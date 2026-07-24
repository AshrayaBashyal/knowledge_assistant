from langchain_core.tools import tool

from memory.models import Memory


def build_remember_tool(user):
    """
    Builds a memory-writing tool bound to one user, mirroring build_retrieval_tool's pattern (a fresh closure per request rather than a global tool, since which user's memory to write to is request-scoped).

    Saving just creates a Memory row - indexing into the shared vector collection happens automatically via a post_save signal (in retrieval/signals.py), the same way Note works. This tool doesn't need to know retrieval exists at all.
    """

    @tool
    def remember_fact(fact: str) -> str:
        """Save a fact or preference about the user that should be recalled in future conversations - e.g. a stated preference, dietary restriction, profession, or recurring detail. Do not use this for one-off details only relevant to the current message."""
        memory = Memory.objects.create(user=user, content=fact)
        return f"Remembered: {memory.content}"

    return remember_fact