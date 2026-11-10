import logging
import time

from langchain_core.documents import Document as LCDocument
from langsmith import traceable

from apps.retrieval.services.embeddings import get_embeddings
from apps.retrieval.services.vectorstore import get_vector_store

logger = logging.getLogger("retrieval.retriever")


@traceable(run_type="retriever", name="vector_similarity_retrieval")
def retrieve_relevant_chunks(user, query: str, k: int = 4) -> list[LCDocument]:
    """
    Returns up to k chunks most similar to `query`, scoped to the given
    user's own indexed documents. Returns an empty list (rather than
    raising) if the user has no collection yet - "no documents indexed"
    is a normal state, not an error.

    Uses the vector database's native Approximate Nearest Neighbor (ANN / HNSW)
    search algorithm, which executes directly inside the optimized vector index
    rather than loading all stored vectors into Python memory for a linear scan.
    """
    started_at = time.monotonic()

    try:
        embeddings = get_embeddings()
        vector_store = get_vector_store(user.id, embeddings=embeddings)

        # Vector store's native indexed similarity search
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
