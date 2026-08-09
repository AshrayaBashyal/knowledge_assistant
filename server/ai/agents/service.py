from langchain.agents import create_agent

from ai.agents.registry import build_tools
from ai.llm.providers import get_chat_model


# SYSTEM_PROMPT = (
#     "You are a helpful knowledge assistant. You have tools available: "
#     "use search_my_knowledge when the question might be answered by the "
#     "user's own uploaded documents or notes, use calculator for "
#     "arithmetic instead of computing it yourself, use current_time if "
#     "the date/time is relevant, and use tavily_search for questions "
#     "about current events or anything needing up-to-date information "
#     "beyond your training data. Don't use a tool when you don't need "
#     "one - answer directly for general knowledge questions. When you "
#     "use information returned by search_my_knowledge, reference it in "
#     "your answer using its [Source N] label so the user knows which "
#     "document or note it came from."
# )

SYSTEM_PROMPT = (
    "You are a helpful knowledge assistant. Use your available tools to search the user's "
    "uploaded documents or notes, perform arithmetic calculations, check the current time, "
    "or look up up-to-date information on current events. "
    "Only use a tool when absolutely necessary; answer directly for general knowledge questions or greetings. "
    "When using information from the user's personal knowledge base, always reference it "
    "in your answer using its [Source N(document/note/memory_name(source_type))] label."
)



def build_agent(user, sources_sink: list):
    """
    Builds a fresh agent for one request, with tools bound to this user.
    
    Building an agent is cheap/fast because it only configures memory and code references and not perform any network calls, database queries, or heavy file read/write operations (I/O). Making a new one  per request cleanly isolates user data without extra tracking.
    
    We don't use LangGraph's checkpointer or thread history here even though create_agent supports persisting conversation state itself. Postgres is our single source of truth for chat history, so we pass the full log on every call to avoid data to drift out of sync.

    Should only switch to LangGraph's native checkpointer memory if, we plan to build complex, multi-step state machines.
    """
    tools = build_tools(user, sources_sink)
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=True
    )
