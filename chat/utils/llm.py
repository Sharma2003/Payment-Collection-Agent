from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

def _build_llm():
    """Build the LLM client. Falls back gracefully if env vars missing."""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        return init_chat_model("groq:qwen/qwen3-32b")
    except Exception:
        return init_chat_model("groq:llama3-8b-8192")