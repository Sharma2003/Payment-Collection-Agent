from typing import Optional
from pydantic import BaseModel, Field

BASE_URL = (
    "https://se-payment-verification-api.service.external.usea2.aws.prodigaltech.com"
)

MAX_VERIFICATION_ATTEMPTS = 3
MAX_PAYMENT_ATTEMPTS = 2

class ConversationState(BaseModel):

    user_input: str = ""

    # Account
    account_id: Optional[str] = None
    account_data: Optional[dict] = None          

    # Identity (collected from user)
    full_name: Optional[str] = None
    dob: Optional[str] = None                   
    aadhaar_last4: Optional[str] = None
    pincode: Optional[str] = None

    # Verification
    verified: bool = False
    verification_attempts: int = 0
    verification_locked: bool = False

    # Payment intent
    balance: Optional[float] = None
    amount: Optional[float] = None

    # Card details
    cardholder_name: Optional[str] = None
    card_number: Optional[str] = None
    cvv: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None

    # Outcome
    transaction_id: Optional[str] = None
    payment_attempts: int = 0

    # Current pipeline stage (drives routing decisions)
    stage: str = "awaiting_account_id"

    # The reply to send back to the user this turn
    response: str = ""


# ---------------------------------------------------------------------------
# Structured extraction schema (LLM → typed output)
# ---------------------------------------------------------------------------

class ExtractedInfo(BaseModel):
    """
    Fields the LLM should extract from a single user message.
    All fields are Optional; only fill what is clearly present.
    """

    account_id: Optional[str] = Field(
        default=None,
        description="Account identifier like ACC1001. Normalise to uppercase, remove spaces.",
    )
    full_name: Optional[str] = Field(
        default=None,
        description=(
            "Full legal name exactly as stated by the user. "
            "Do not infer or guess; preserve original casing."
        ),
    )
    dob: Optional[str] = Field(
        default=None,
        description=(
            "Date of birth normalised to YYYY-MM-DD. "
            "Handle variants like '14th May 1990', '14-05-1990', 'May 14, 90'."
        ),
    )
    aadhaar_last4: Optional[str] = Field(
        default=None,
        description="Last 4 digits of Aadhaar card as a 4-character string.",
    )
    pincode: Optional[str] = Field(
        default=None,
        description="6-digit postal pincode as a string.",
    )
    amount: Optional[float] = Field(
        default=None,
        description=(
            "Payment amount in rupees as a float. "
            "Interpret 'full amount' or 'total' as -1.0 (sentinel for full balance). "
            "Interpret 'thousand' as 1000, 'five hundred' as 500, etc."
        ),
    )
    cardholder_name: Optional[str] = Field(
        default=None,
        description="Name on the card, exactly as stated.",
    )
    card_number: Optional[str] = Field(
        default=None,
        description="16-digit card number; strip spaces and dashes.",
    )
    cvv: Optional[str] = Field(
        default=None,
        description="Card CVV (3 or 4 digits) as a string.",
    )
    expiry_month: Optional[int] = Field(
        default=None,
        description=(
            "Card expiry month as integer 1-12. "
            "Interpret 'December' as 12, '12/27' month part as 12, etc."
        ),
    )
    expiry_year: Optional[int] = Field(
        default=None,
        description=(
            "Card expiry year as 4-digit integer. "
            "Interpret '27' or '2027' both as 2027."
        ),
    )
