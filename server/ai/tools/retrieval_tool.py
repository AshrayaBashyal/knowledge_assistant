from langchain_core.tools import tool

from core.logging import log_call
from apps.retrieval.services.retriever import retrieve_relevant_chunks


def build_retrieval_tool(user, sources_sink: list, k: int = 4):
    """
    Builds a knowledge-search tool bound to one user's documents AND notes together - they share one vector collection (see retrieval/vectorstore.py) - so a single search ranks both by relevance, rather than the agent having to guess which of two separate tools to call.

    Since LangChain tools are usually stateless, this factory closes over `user` to isolate data and ensure the LLM can only search this specific user's files.

    It returns a plain text string to the model (per tool-calling contract), but appends the raw chunk objects to `sources_sink`. This side effect lets the caller recover structured metadata (like titles) for UI citations afterward.

    `sources_sink` is a list the caller passes in and this tool appends retrieved chunks to as a side effect, since the tool's return value to the model is just a text string (the LLM tool-calling contract), which loses structured metadata like title/source_type - sources_sink is how the caller recovers that afterward to show citations.
    """

    @tool
    @log_call("tools.retrieval")
    def search_my_knowledge(query: str) -> str:
        """Search the user's uploaded documents, notes, and remembered facts/preferences for information relevant to `query`. Use this when the question might be answered by the user's own content, not general knowledge."""

        chunks = retrieve_relevant_chunks(user, query, k=k)
        if not chunks:
            return "No relevant content found in the user's documents or notes."
 
        sources_sink.extend(chunks)
 
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            title = chunk.metadata.get("title", "unknown")
            source_type = chunk.metadata.get("source_type", "content")
            parts.append(f"[Source {i}: {title} ({source_type})]\n{chunk.page_content}")
        return "\n\n".join(parts)
 
    return search_my_knowledge