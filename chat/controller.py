from uuid import uuid4

from fastapi import APIRouter, HTTPException

from chat.schemas import ChatRequest
from chat.graph.graph import _build_graph

graph = _build_graph()

router = APIRouter(
    prefix="/chat",
    tags=["Payment Agent"]
)


@router.post("/start")
async def start_chat():
    """
    Start a new conversation.
    Creates a fresh thread_id that LangGraph
    will use for state persistence.
    """

    thread_id = str(uuid4())

    try:

        result = await graph.ainvoke(
            {
                "user_input": ""
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        return {
            "thread_id": thread_id,
            "message": result.get(
                "response",
                "Welcome! Please provide your account ID."
            ),
            "stage": result.get("stage")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/message")
async def next_message(
    request: ChatRequest
):
    """
    Continue an existing conversation.
    """

    try:

        result = await graph.ainvoke(
            {
                "user_input": request.message
            },
            config={
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
        )

        return {
            "thread_id": request.thread_id,
            "message": result.get("response"),
            "stage": result.get("stage"),
            "verified": result.get("verified"),
            "transaction_id": result.get(
                "transaction_id"
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )