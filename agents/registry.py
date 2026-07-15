from tools.calculator import calculator
from tools.current_time import current_time
from tools.retrieval_tool import build_retrieval_tool


def build_tools(user, sources_sink: list) -> list:
    """
    Returns the tool list for one user's agent. Kept as a single small
    function rather than scattering tool construction across the agent
    factory, so adding/removing a tool is a one-line change here.
    """
    return [
        calculator,
        current_time,
        build_retrieval_tool(user, sources_sink),
    ]