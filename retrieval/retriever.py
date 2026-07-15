from langchain_core.documents import Document as LCDocument

from retrieval.vectorstore import get_vector_store


def retrieve_relevant_chunks(user, query: str, k: int = 4) -> list[LCDocument]:
    """
    Returns up to k chunks most similar to `query`, scoped to the given user's own indexed documents. Returns an empty list (rather than raising) if the user has no collection yet - "no documents indexed" is a normal state, not an error.
    """
    vector_store = get_vector_store(user.id)
    try:
        return vector_store.similarity_search(query, k=k)
    except Exception:
        return []