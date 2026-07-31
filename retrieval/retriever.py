import logging
import time

from langchain_core.documents import Document as LCDocument

from retrieval.vectorstore import get_vector_store

logger = logging.getLogger("retrieval.retriever")

def retrieve_relevant_chunks(user, query: str, k: int = 4) -> list[LCDocument]:
    """
    Returns up to k chunks most similar to `query`, scoped to the given user's own indexed documents. Returns an empty list (rather than raising) if the user has no collection yet - "no documents indexed" is a normal state, not an error.
    """
    started_at = time.monotonic()
    vector_store = get_vector_store(user.id)

    try:
        results = vector_store.similarity_search(query, k=k)
        logger.info(
            "retrieval_query",
            extra={
                "user_id": user.id,
                "query_length": len(query),
                "k": k,
                "result_count": len(results),
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )
        return results

    except Exception:
        # Query text itself isn't logged (may contain sensitive content the user typed) - length and outcome are enough to see this happening/how often, without putting arbitrary user input in logs.
        logger.exception(
            "retrieval_query_failed",
            extra={
                "user_id": user.id,
                "query_length": len(query),
                "k": k,
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )
        return []