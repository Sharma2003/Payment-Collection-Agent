from typing import Literal
from chat.graph.state import ConversationState

def route_state(
    state: ConversationState,
) -> Literal[
    "handle_account_id",
    "handle_verification",
    "handle_amount",
    "handle_card",
    "handle_completed",
    "terminated",
]:
    stage = state.stage

    if stage == "terminated":
        return "terminated"
    if stage == "completed":
        return "handle_completed"
    if stage in ("awaiting_name", "awaiting_secondary"):
        return "handle_verification"
    if stage == "awaiting_amount":
        return "handle_amount"
    if stage == "awaiting_card":
        return "handle_card"
    # Default / awaiting_account_id
    return "handle_account_id"