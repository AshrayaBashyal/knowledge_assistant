from langchain.tools import tool
from retrieval.retriever import retrieve_relevant_chunks


def build_retrieval_tool(user, sources_sink: list, k: int = 4):
    """
    Creates a user-scoped document search tool for a single request.

    Since LangChain tools are usually stateless, this factory closes over `user` to isolate data and ensure the LLM can only search this specific user's files.

    It returns a plain text string to the model (per tool-calling contract), but appends the raw chunk objects to `sources_sink`. This side effect lets the caller recover structured metadata (like titles) for UI citations afterward.
    """

    @tool
    def search_my_documents(query: str) -> str:
        """Search the user's uploaded documents for information relevant to `query`. Use this when the question might be answered by the user's own uploaded files, not general knowledge."""

        chunks = retrieve_relevant_chunks(user, query, k=k)
        if not chunks:
            return "No relevant documents found in the user's collection."
 
        sources_sink.extend(chunks)
 
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            title = chunk.metadata.get("document_title", "unknown")
            parts.append(f"[Source {i}: {title}]\n{chunk.page_content}")
        return "\n\n".join(parts)
 
    return search_my_documents