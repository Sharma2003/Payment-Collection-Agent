import os 
import requests
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing import Optional
import re

from chat.graph.state import ExtractedInfo, ConversationState, MAX_PAYMENT_ATTEMPTS, MAX_VERIFICATION_ATTEMPTS, BASE_URL
from chat.utils.llm import _build_llm

load_dotenv()



_llm = None
_extraction_model = None


def _get_extraction_model():
    global _llm, _extraction_model
    if _extraction_model is None:
        _llm = _build_llm()
        _extraction_model = _llm.with_structured_output(ExtractedInfo)
    return _extraction_model


# Information extraction


def extract_information(user_input: str, stage: str) -> ExtractedInfo:
    """
    Use the LLM to extract structured data from free-form user input.
    The stage hint helps the model focus on relevant fields.
    """
    stage_hints = {
        "awaiting_account_id": "Focus on account_id.",
        "awaiting_name": "Focus on full_name.",
        "awaiting_secondary": "Focus on dob, aadhaar_last4, pincode.",
        "awaiting_amount": "Focus on amount.",
        "awaiting_card": "Focus on card_number, cvv, expiry_month, expiry_year, cardholder_name.",
    }
    hint = stage_hints.get(stage, "Extract any relevant payment information.")

    model = _get_extraction_model()
    return model.invoke(
        f"""You are a data extraction assistant for a payment collection system.
Extract ONLY information explicitly stated by the user. Do NOT infer or guess.

{hint}

User message: {user_input}
"""
    )


# API helpers

def api_lookup_account(account_id: str) -> dict:
    """Call /api/lookup-account and return parsed JSON."""
    try:
        r = requests.post(
            f"{BASE_URL}/api/lookup-account",
            json={"account_id": account_id},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return {"error": "account_not_found"}
        return {"error": "api_failure", "status": r.status_code}
    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": "network_error", "detail": str(e)}


def api_process_payment(
    account_id: str,
    amount: float,
    cardholder_name: str,
    card_number: str,
    cvv: str,
    expiry_month: int,
    expiry_year: int,
) -> dict:
    """Call /api/process-payment and return parsed JSON."""
    payload = {
        "account_id": account_id,
        "amount": round(amount, 2),
        "payment_method": {
            "type": "card",
            "card": {
                "cardholder_name": cardholder_name,
                "card_number": card_number,
                "cvv": cvv,
                "expiry_month": expiry_month,
                "expiry_year": expiry_year,
            },
        },
    }
    try:
        r = requests.post(
            f"{BASE_URL}/api/process-payment",
            json=payload,
            timeout=15,
        )
        data = r.json()
        return data
    except requests.exceptions.Timeout:
        return {"success": False, "error_code": "timeout"}
    except Exception as e:
        return {"success": False, "error_code": "network_error", "detail": str(e)}



# Verification logic (deterministic — no LLM involvement)


def verify_identity(state: ConversationState) -> bool:
    """
    Return True only when:
      full_name matches exactly AND at least one secondary factor matches.
    """
    account = state.account_data
    if not account:
        return False

    # Name must match exactly (case-sensitive per spec)
    if state.full_name != account.get("full_name"):
        return False

    # At least one secondary factor
    dob_match = bool(state.dob and state.dob == account.get("dob"))
    aadhaar_match = bool(
        state.aadhaar_last4 and state.aadhaar_last4 == account.get("aadhaar_last4")
    )
    pincode_match = bool(state.pincode and state.pincode == account.get("pincode"))

    return dob_match or aadhaar_match or pincode_match



# Input validation helpers

def _format_rupees(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _validate_card_number(card_number: str) -> bool:
    """Basic length check (Luhn handled server-side)."""
    digits = re.sub(r"\D", "", card_number or "")
    return len(digits) in (15, 16)


def _normalise_expiry_year(year: Optional[int]) -> Optional[int]:
    if year is None:
        return None
    if year < 100:
        return 2000 + year
    return year


def _payment_error_message(error_code: str) -> str:
    messages = {
        "insufficient_balance": (
            "The amount exceeds your outstanding balance. "
            "Please enter a smaller amount."
        ),
        "invalid_amount": (
            "The amount is invalid (must be positive with up to 2 decimal places). "
            "Please re-enter the amount."
        ),
        "invalid_card": (
            "The card number appears to be invalid. "
            "Please double-check and re-enter your card details."
        ),
        "invalid_cvv": (
            "The CVV does not match expected format. "
            "Please re-enter your CVV."
        ),
        "invalid_expiry": (
            "The card expiry date is invalid or the card has expired. "
            "Please check your card and try again."
        ),
        "timeout": (
            "The payment request timed out. Please try again."
        ),
    }
    return messages.get(
        error_code,
        f"Payment failed (error: {error_code}). Please contact support.",
    )


# ---------------------------------------------------------------------------
# State update helper
# ---------------------------------------------------------------------------

def _merge_extracted(state: ConversationState, extracted: ExtractedInfo) -> ConversationState:
    """
    Merge non-None extracted fields into state, preserving already-collected values.
    """
    data = extracted.model_dump(exclude_none=True)
    for key, value in data.items():
        # Only update if field not already set (don't overwrite confirmed data)
        if getattr(state, key, None) is None:
            setattr(state, key, value)
        else:
            # Always update these (user may be correcting themselves)
            if key in ("full_name", "dob", "aadhaar_last4", "pincode",
                       "card_number", "cvv", "expiry_month", "expiry_year",
                       "cardholder_name", "amount"):
                setattr(state, key, value)

    # Normalise expiry year
    if state.expiry_year is not None:
        state.expiry_year = _normalise_expiry_year(state.expiry_year)

    # Normalise account_id: strip spaces, uppercase
    if state.account_id:
        state.account_id = re.sub(r"\s+", "", state.account_id).upper()

    return state


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def node_extract(state: ConversationState) -> ConversationState:
    """Extract structured info from the current user_input and merge into state."""
    if not state.user_input.strip():
        return state

    try:
        extracted = extract_information(state.user_input, state.stage)
        state = _merge_extracted(state, extracted)
    except Exception:
        # Extraction failure is non-fatal; routing will ask the user to repeat
        pass

    return state


def node_handle_account_id(state: ConversationState) -> ConversationState:
    """
    Handles the account-ID stage.
    If we have an account_id, look it up; otherwise ask for it.
    """
    if not state.account_id:
        state.response = (
            "I'd be happy to help you with your payment. "
            "Could you please share your account ID to get started?"
        )
        return state

    # Call the lookup API
    result = api_lookup_account(state.account_id)

    if "error" in result:
        err = result["error"]
        if err == "account_not_found":
            state.account_id = None  # reset so user can retry
            state.response = (
                f"I couldn't find an account with ID '{state.account_id}'. "
                "Please double-check and share the correct account ID."
            )
        else:
            state.response = (
                "I'm having trouble reaching our systems right now. "
                "Please try again in a moment."
            )
        return state

    # Success — store account data (never reveal to user)
    state.account_data = result
    state.balance = result.get("balance")
    state.stage = "awaiting_name"

    # If user already provided their name in the same message, skip asking
    if state.full_name:
        state.stage = "awaiting_secondary"
        state.response = (
            f"Thank you. To verify your identity, could you please provide "
            "your date of birth, the last 4 digits of your Aadhaar, or your pincode?"
        )
    else:
        state.response = (
            "Thank you! I've located your account. "
            "Could you please confirm your full name for verification?"
        )

    return state


def node_handle_verification(state: ConversationState) -> ConversationState:
    """
    Handles the identity verification stages (awaiting_name / awaiting_secondary).
    Enforces retry limit.
    """
    if state.verification_locked:
        state.response = (
            "Your account has been locked after too many failed verification attempts. "
            "Please contact customer support for assistance. "
            "Thank you for calling."
        )
        state.stage = "terminated"
        return state

    # Stage: awaiting_name — check if we have a name yet
    if state.stage == "awaiting_name":
        if not state.full_name:
            state.response = (
                "Could you please share your full name as it appears on your account?"
            )
            return state
        # Name received — move to secondary factor
        state.stage = "awaiting_secondary"
        state.response = (
            "Thank you. For additional verification, could you please provide "
            "one of the following: your date of birth, the last 4 digits of your Aadhaar number, "
            "or your pincode?"
        )
        return state

    # Stage: awaiting_secondary
    has_secondary = state.dob or state.aadhaar_last4 or state.pincode

    if not has_secondary:
        state.response = (
            "Please provide at least one of the following to verify your identity: "
            "your date of birth (in any format), the last 4 digits of your Aadhaar, "
            "or your pincode."
        )
        return state

    # Attempt verification
    state.verification_attempts += 1
    passed = verify_identity(state)

    if passed:
        state.verified = True
        state.stage = "awaiting_amount"
        balance_str = _format_rupees(state.balance)
        state.response = (
            f"Identity verified successfully! ✓\n\n"
            f"Your outstanding balance is {balance_str}. "
            f"How much would you like to pay today? "
            f"(You can pay the full amount or a partial amount.)"
        )
        return state

    # Verification failed
    remaining = MAX_VERIFICATION_ATTEMPTS - state.verification_attempts

    if remaining <= 0:
        state.verification_locked = True
        state.stage = "terminated"
        state.response = (
            "I'm sorry, but I was unable to verify your identity after "
            f"{MAX_VERIFICATION_ATTEMPTS} attempts. "
            "Your account has been temporarily locked for security. "
            "Please contact customer support. Thank you."
        )
        return state

    # Clear incorrect secondary fields so the user can re-enter
    # (keep the name since that might be right and secondary was wrong, or vice-versa)
    name_correct = state.full_name == (state.account_data or {}).get("full_name")
    if not name_correct:
        state.full_name = None
        state.stage = "awaiting_name"
        state.response = (
            f"Verification failed. The name you provided doesn't match our records. "
            f"You have {remaining} attempt(s) remaining. "
            "Could you please re-enter your full name exactly as registered?"
        )
    else:
        state.dob = None
        state.aadhaar_last4 = None
        state.pincode = None
        state.response = (
            f"Verification failed. The secondary details didn't match our records. "
            f"You have {remaining} attempt(s) remaining. "
            "Please try a different verification method: date of birth, "
            "last 4 digits of Aadhaar, or pincode."
        )

    return state


def node_handle_amount(state: ConversationState) -> ConversationState:
    """Handles payment amount collection and validation."""
    if state.amount is None:
        state.response = (
            f"Your outstanding balance is {_format_rupees(state.balance)}. "
            "How much would you like to pay? You can pay the full amount or a partial amount."
        )
        return state

    # Sentinel -1.0 means "full amount"
    if state.amount == -1.0:
        state.amount = state.balance

    # Validate amount
    if state.amount <= 0:
        state.amount = None
        state.response = "The amount must be greater than zero. Please enter a valid amount."
        return state

    if state.amount > state.balance:
        state.amount = None
        state.response = (
            f"The amount exceeds your outstanding balance of {_format_rupees(state.balance)}. "
            "Please enter an amount up to your balance."
        )
        return state

    # Amount looks good — move to card collection
    state.stage = "awaiting_card"
    state.response = (
        f"I'll process a payment of {_format_rupees(state.amount)}. "
        "Please provide your card details:\n"
        "• Card number\n"
        "• Expiry date (month and year)\n"
        "• CVV\n"
        "• Cardholder name (as on card)"
    )
    return state


def node_handle_card(state: ConversationState) -> ConversationState:
    """Handles card detail collection and triggers payment."""
    # Check what we still need
    missing = []
    if not state.card_number:
        missing.append("card number")
    if not state.expiry_month or not state.expiry_year:
        missing.append("expiry date (month and year)")
    if not state.cvv:
        missing.append("CVV")
    if not state.cardholder_name:
        # Default to account holder name if not provided
        state.cardholder_name = (state.account_data or {}).get("full_name")

    if missing:
        missing_str = ", ".join(missing)
        state.response = (
            f"To complete your payment, I still need your {missing_str}. "
            "Please provide the missing details."
        )
        return state

    # Basic card number validation
    card_digits = re.sub(r"\D", "", state.card_number)
    if len(card_digits) not in (15, 16):
        state.card_number = None
        state.response = (
            "The card number doesn't appear to be valid. "
            "Please re-enter your 15 or 16-digit card number."
        )
        return state

    # Process payment
    state.payment_attempts += 1
    result = api_process_payment(
        account_id=state.account_id,
        amount=state.amount,
        cardholder_name=state.cardholder_name,
        card_number=card_digits,
        cvv=state.cvv,
        expiry_month=state.expiry_month,
        expiry_year=state.expiry_year,
    )

    if result.get("success"):
        state.transaction_id = result.get("transaction_id")
        state.stage = "completed"
        state.response = (
            f"Payment successful!\n\n"
            f"Amount paid: {_format_rupees(state.amount)}\n"
            f"Transaction ID: {state.transaction_id}\n\n"
            f"Please keep your transaction ID for reference. "
            f"Is there anything else I can help you with?"
        )
        return state

    # Payment failed
    error_code = result.get("error_code", "unknown")
    user_msg = _payment_error_message(error_code)

    # Retryable errors: let user re-enter card details
    retryable_errors = {"invalid_card", "invalid_cvv", "invalid_expiry", "timeout"}

    if error_code in retryable_errors and state.payment_attempts < MAX_PAYMENT_ATTEMPTS:
        # Clear problematic fields
        if error_code == "invalid_card":
            state.card_number = None
        elif error_code == "invalid_cvv":
            state.cvv = None
        elif error_code == "invalid_expiry":
            state.expiry_month = None
            state.expiry_year = None
        state.response = user_msg
        return state

    if error_code == "insufficient_balance":
        # Non-retryable with current amount — ask for new amount
        state.amount = None
        state.stage = "awaiting_amount"
        state.response = user_msg
        return state

    # Terminal failure
    state.stage = "terminated"
    state.response = (
        f"{user_msg}\n\n"
        "We were unable to process your payment. "
        "Please try again later or contact customer support. "
        "Thank you for your patience."
    )
    return state


def node_handle_completed(state: ConversationState) -> ConversationState:
    """Post-payment wrap-up."""
    state.response = (
        "Your payment has been processed successfully. "
        f"Transaction ID: {state.transaction_id}. "
        "Thank you for using our service. Have a great day!"
    )
    return state


def node_terminated(state: ConversationState) -> ConversationState:
    """Terminal state — session is over."""
    if not state.response:
        state.response = (
            "This session has ended. "
            "Please contact customer support if you need further assistance."
        )
    return state