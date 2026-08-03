import os

from langchain_groq import ChatGroq


def get_chat_model(*, streaming: bool = True) -> ChatGroq:
    """Factory for the chat model used across the app."""
    
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.7")),
        api_key=os.getenv("GROQ_API_KEY"),
        streaming=streaming,
    )