from chat.graph.state import ConversationState
from chat.graph.node import node_extract, node_handle_account_id, node_handle_amount, node_handle_card, node_handle_completed, node_handle_verification, node_terminated
from chat.graph.edges import route_state
from langgraph.checkpoint.memory import MemorySaver

from chat.graph.state import ConversationState
from langgraph.graph import StateGraph, END, START


def _build_graph():
    graph = StateGraph(ConversationState)
    # Nodes
    graph.add_node("extract", node_extract)
    graph.add_node("handle_account_id", node_handle_account_id)
    graph.add_node("handle_verification", node_handle_verification)
    graph.add_node("handle_amount", node_handle_amount)
    graph.add_node("handle_card", node_handle_card)
    graph.add_node("handle_completed", node_handle_completed)
    graph.add_node("terminated", node_terminated)

    # Entry: always extract first
    graph.set_entry_point("extract")

    # After extraction, route based on stage
    graph.add_conditional_edges(
        "extract",
        route_state,
        {
            "handle_account_id": "handle_account_id",
            "handle_verification": "handle_verification",
            "handle_amount": "handle_amount",
            "handle_card": "handle_card",
            "handle_completed": "handle_completed",
            "terminated": "terminated",
        },
    )

    # All handler nodes terminate the graph turn
    for node in (
        "handle_account_id",
        "handle_verification",
        "handle_amount",
        "handle_card",
        "handle_completed",
        "terminated",
    ):
        graph.add_edge(node, END)

    return graph.compile(checkpointer=MemorySaver())
