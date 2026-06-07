from chat.graph.graph import _build_graph
from chat.graph.state import ConversationState
from uuid import uuid4

graph = _build_graph()

class Agent:

    def __init__(self):
        self.state = ConversationState()
        self.thread_id = str(uuid4())

    def next(self, user_input: str):

        self.state.user_input = user_input

        result = graph.invoke(
            self.state,
            config={
                "configurable": {
                    "thread_id": self.thread_id
                }
            }
        )

        self.state = ConversationState(**result)

        return {
            "message": self.state.response
        }