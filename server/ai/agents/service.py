from langchain.agents import create_agent

from ai.agents.registry import build_tools
from ai.llm.providers import get_chat_model

SYSTEM_PROMPT = (
    "You are a helpful knowledge assistant. Use your available tools to search the user's "
    "uploaded documents or notes, perform arithmetic calculations, check the current time, "
    "or look up up-to-date information on current events. "
    "Only use a tool when absolutely necessary; answer directly for general knowledge questions or greetings. "
    "When using information from the user's personal knowledge base, always reference it "
    "in your answer using its source label format, including the index and the exact document title provided. "
    "For example, write: [Source 1: My_Document_Name.pdf (document)] or [Source 2: Lecture_Notes (note)]."
)


def build_agent(user, sources_sink: list):
    """
    Builds a fresh agent for one request, with tools bound to this user.
    Uses the user's custom model & API key if configured.
    """
    tools = build_tools(user, sources_sink)
    return create_agent(
        model=get_chat_model(user=user),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=True,
    )
