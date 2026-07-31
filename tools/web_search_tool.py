from langchain_tavily import TavilySearch


def get_web_search_tool(max_results: int = 3) -> TavilySearch:
    """
    Factory for the web search tool, mirroring get_chat_model()/ get_embeddings(). TavilySearch reads TAVILY_API_KEY from the environment itself, the same way ChatGroq reads GROQ_API_KEY, so this stays a one-line wrapper rather than plumbing the key through manually.

    Unlike the other tools in this package, this one isn't wrapped with
    @log_call: TavilySearch is a full BaseTool subclass (implements
    _run/_arun internally) with no plain function to decorate the way
    calculator/current_time/search_my_knowledge/remember_fact have -
    confirmed by inspecting the class directly rather than assuming.
    Tool-call logging for this one comes from the generic per-tool-call
    logging in chat/views.py's _stream_chat_response instead, which
    covers every tool uniformly regardless of how it's implemented, just
    with coarser timing than the other tools' own instrumentation.
    """
    return TavilySearch(max_results=max_results)