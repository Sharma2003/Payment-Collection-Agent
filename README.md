# Payment Collection Agent

## Overview

This project implements an AI-powered Payment Collection Agent using LangGraph. The agent guides customers through a payment collection workflow by verifying identity, collecting payment information, processing payments, and handling failures gracefully.

The system supports:

* Multi-turn conversations
* Context persistence across interactions
* Structured information extraction
* Account verification
* Payment processing
* Failure handling and retry mechanisms
* Tool-based API integrations

---

## Problem Statement

Develop an intelligent payment collection agent that can:

1. Verify customer identity using account information.
2. Retrieve outstanding balance information.
3. Collect payment amounts.
4. Collect and validate card details.
5. Process payments through external APIs.
6. Maintain conversational context across multiple turns.
7. Handle failures and retries gracefully.

---

## Architecture

```text
User
 │
 ▼
LangGraph Workflow
 │
 ├── Extraction Node
 │
 ├── Account Lookup Tool
 │
 ├── Verification Node
 │
 ├── Amount Collection Node
 │
 ├── Card Collection Node
 │
 ├── Payment Processing Tool
 │
 └── Completion Node
```

---

## Project Structure

```text
Payment-Collection-Agent/
│
├── chat/
│   ├── controller.py
│   ├── Agent.py
|   ├── schemas.py
│   │
│   └── graph/
│       ├── graph.py
│       ├── nodes.py
│       ├── edges.py
│       └── state.py
│
├── evaluation/
│   ├── test_lookup.py
│   ├── test_verification.py
│   ├── test_context.py
│   ├── test_payment.py
│   └── run_all_tests.py
│
├── README.md
├── DESIGN.md
└── requirements.txt
```

---

## Key Features

### Multi-Turn Context Management

The agent maintains conversation state across turns using LangGraph state management and checkpointing.

Example:

```text
User: ACC1001
Agent: Please provide your full name.

User: Nithin Jain
Agent: Please provide your DOB.

User: 1990-05-14
Agent: Identity verified.
```

---

### Structured Output Extraction

The agent uses Pydantic schemas and LLM-based structured extraction to identify:

* Account IDs
* Full Names
* Date of Birth
* Aadhaar Last 4 Digits
* Pincodes
* Payment Amounts
* Card Details

---

### Tool Calling

The workflow integrates external tools:

#### Account Lookup Tool

Retrieves customer account information.

#### Payment Processing Tool

Processes card payments.

#### Balance Calculation Tool

Calculates remaining outstanding balance after successful payment.

---

### Failure Handling

Implemented safeguards include:

* Invalid account handling
* Verification retry limits
* Payment retry limits
* Invalid card validation
* Invalid CVV validation
* Expired card detection
* API timeout handling
* Session termination after repeated failures

---

## Running the Application

### Install Dependencies

```bash
uv sync
```

---

### Start FastAPI Server

```bash
uv run uvicorn main:app --reload
```

---

### API Documentation

```text
http://localhost:8000/docs
```

---

## Running Evaluation Tests

```bash
python -m evaluation.run_all_tests
```

Example Output:

```text
======================================================================
PAYMENT COLLECTION AGENT - EVALUATION REPORT
======================================================================
[PASS]   Account Lookup
[PASS]   Verification
[PASS]   Context Management
[PASS]   Payment Processing

======================================================================
SUMMARY
======================================================================
Total Test Suites : 4
Passed            : 4
Failed            : 0
Success Rate      : 100%
======================================================================
```

---

## Technologies Used

* Python
* LangGraph
* LangChain
* FastAPI
* Pydantic
* Gemini
* UV
* Requests

---

## Future Improvements

* Redis-backed checkpointing
* LangSmith observability
* Fraud detection checks
* Human handoff workflow
* Additional payment methods
* Production monitoring and analytics

---
