from langchain_core.tools import tool

from core.logging import log_call
from apps.memory.dedup_algorithm import find_near_duplicate
from apps.memory.models import Memory


def build_remember_tool(user):
    """
    Builds a memory-writing tool bound to one user, mirroring
    build_retrieval_tool's pattern (a fresh closure per request rather
    than a global tool, since which user's memory to write to is
    request-scoped).

    Saving just creates a Memory row - indexing into the shared vector
    collection happens automatically via a post_save signal (see
    retrieval/signals.py), the same way Note works. This tool doesn't
    need to know retrieval exists at all.
    """

    @tool
    @log_call("tools.memory")
    def remember_fact(fact: str) -> str:
        """Save a fact or preference about the user that should be
        recalled in future conversations - e.g. a stated preference,
        dietary restriction, profession, or recurring detail. Do not use
        this for one-off details only relevant to the current message."""
        existing = list(
            Memory.objects.filter(user=user).values_list("id", "content")
        )
        duplicate = find_near_duplicate(fact, existing)

        if duplicate is not None:
            existing_id, similarity = duplicate
            # Deliberately don't update the existing row's timestamp or
            # content here - a near-duplicate might be a slightly
            # different phrasing worth investigating later, not
            # necessarily a pure repeat. Just avoid adding a new row for
            # something this similar to what's already remembered.
            return f"Already remembered (similar to an existing entry, {similarity:.0%} match) - not duplicating."

        memory = Memory.objects.create(user=user, content=fact)
        return f"Remembered: {memory.content}"

    return remember_fact