from langchain.agents import create_agent

from agents.registry import build_tools
from llm.providers import get_chat_model


SYSTEM_PROMPT = (
    "You are a helpful knowledge assistant. You have tools available: "
    "use search_my_documents when the question might be answered by the "
    "user's own uploaded documents, use calculator for arithmetic instead "
    "of computing it yourself, and use current_time if the date/time is "
    "relevant. Don't use a tool when you don't need one - answer directly "
    "for general knowledge questions. When you use information returned "
    "by search_my_documents, reference it in your answer using its "
    "[Source N] label so the user knows which document it came from."
)
 


def build_agent(user, sources_sink: list):
    """
    Builds a fresh agent for one request, with tools bound to this user.
    
    Building an agent is cheap/fast because it only configures memory and code references and not perform any network calls, database queries, or heavy file read/write operations (I/O). Making a new one  per request cleanly isolates user data without extra tracking.
    
    We don't use LangGraph's checkpointer or thread history here even though create_agent supports persisting conversation state itself. Postgres is our single source of truth for chat history, so we pass the full log on every call to avoid data to drift out of sink.

    Should only switch to LangGraph's native checkpointer memory if, we plan to build complex, multi-step state machines.
    """
    tools = build_tools(user, sources_sink)
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
