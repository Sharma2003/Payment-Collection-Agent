# DESIGN DOCUMENT

## Payment Collection Agent

### Author

Tejash Sharma

---

# 1. System Objective

The objective of the system is to automate debt collection conversations while ensuring:

* Secure identity verification
* Reliable payment processing
* Robust error handling
* Context-aware multi-turn interactions

The agent must guide users through the entire payment collection workflow with minimal friction.

---

# 2. Design Principles

The system was designed around five core principles:

1. Context Preservation
2. Structured Information Extraction
3. Tool-Based Execution
4. Failure Resilience
5. Separation of Concerns

---

# 3. System Architecture

```text
User
 │
 ▼
FastAPI Gateway
 │
 ▼
LangGraph Workflow
 │
 ├── Extraction Layer
 │
 ├── Business Logic Layer
 │
 ├── Tool Layer
 │
 ├── State Layer
 │
 └── Response Layer
```

---

# 4. State Management

A centralized ConversationState object stores:

```python
account_id
full_name
dob
aadhaar_last4
pincode

verified
verification_attempts

balance
amount

cardholder_name
card_number
cvv
expiry_month
expiry_year

transaction_id
stage
response
```

This allows the agent to maintain context across multiple conversation turns.

---

# 5. Workflow Design

## Step 1: Information Extraction

The user message is processed using structured output extraction.

Example:

```text
My account id is ACC1001
```

Extracted:

```json
{
  "account_id": "ACC1001"
}
```

---

## Step 2: Account Lookup

The Account Lookup Tool retrieves:

```text
Customer Name
DOB
Aadhaar Last 4 Digits
Pincode
Outstanding Balance
```

---

## Step 3: Identity Verification

Verification succeeds when:

```text
Full Name Match

AND

(
DOB Match
OR
Aadhaar Match
OR
Pincode Match
)
```

This provides a balance between security and usability.

---

## Step 4: Payment Collection

The user specifies:

```text
Full Payment
or
Partial Payment
```

Validation checks:

* Amount > 0
* Amount <= Outstanding Balance

---

## Step 5: Card Validation

The system validates:

* Card Number
* CVV
* Expiry Date

before payment submission.

---

## Step 6: Payment Processing

The Payment Tool executes the transaction.

Upon success:

```text
Remaining Balance =
Current Balance - Payment Amount
```

A transaction ID is returned.

---

# 6. Tool Calling Strategy

Three primary tools are used:

### Account Lookup Tool

Purpose:

```text
Retrieve customer account information
```

---

### Payment Processing Tool

Purpose:

```text
Execute payment transactions
```

---

### Balance Calculation Tool

Purpose:

```text
Calculate remaining outstanding balance
```

---

# 7. Failure Handling Strategy

The agent implements multiple failure recovery paths.

## Verification Failures

Maximum Attempts:

```text
3
```

After exceeding the limit:

```text
Session Terminated
```

---

## Payment Failures

Maximum Attempts:

```text
2
```

Supported failure scenarios:

* Invalid card
* Invalid CVV
* Invalid expiry date
* API timeout
* Processing failure

---

## Account Lookup Failures

Supported scenarios:

* Account not found
* Service unavailable
* Timeout

---

# 8. Evaluation Strategy

The agent was evaluated using automated test suites covering:

### Account Lookup

* Valid account
* Invalid account

### Verification

* DOB verification
* Aadhaar verification
* Pincode verification
* Verification failure paths

### Context Management

* Multi-turn conversations
* Out-of-order information collection

### Payment Processing

* Full payment
* Partial payment
* Invalid payment amounts

---

# 9. Trade-Offs

### Chosen

* LangGraph for workflow orchestration
* Typed state management using Pydantic
* FastAPI for deployment

### Deferred

* Redis checkpointing
* Human escalation workflow
* Fraud scoring

These can be added in future iterations.

---

# 10. Conclusion

The proposed architecture provides a scalable, maintainable, and production-oriented payment collection agent capable of handling multi-turn conversations, tool integrations, structured outputs, and robust failure management while maintaining clear separation between workflow orchestration, business logic, and external service interactions.
