from django.conf import settings
 
from tools.calculator import calculator
from tools.current_time import current_time
from tools.retrieval_tool import build_retrieval_tool
from tools.memory_tool import build_remember_tool
# from tools.web_search_tool import get_web_search_tool


def build_tools(user, sources_sink: list) -> list:
    """
    Returns the tool list for one user's agent. Kept as a single small function rather than scattering tool construction across the agent factory, so adding/removing a tool is a one-line change here.

    Web search is included only if TAVILY_API_KEY is configured, so the app still runs (just without that capability) in environments that haven't set one up - failing hard at agent-build time over a missing optional integration would be worse than quietly not offering it.
    """
    tools = [
        calculator,
        current_time,
        build_retrieval_tool(user, sources_sink),
        build_remember_tool(user),
    ]
 
    # if settings.TAVILY_API_KEY:
    #     tools.append(get_web_search_tool(max_results=settings.WEB_SEARCH_MAX_RESULTS))
 
    return tools