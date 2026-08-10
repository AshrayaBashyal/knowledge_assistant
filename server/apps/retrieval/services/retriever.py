import logging
import time

from langchain_core.documents import Document as LCDocument
from langsmith import traceable

from apps.retrieval.services.embeddings import get_embeddings
from apps.retrieval.similarity_algorithm import top_k_by_similarity
from apps.retrieval.services.vectorstore import get_vector_store

logger = logging.getLogger("retrieval.retriever")


@traceable(run_type="retriever", name="cosine_similarity_retrieval")
def retrieve_relevant_chunks(user, query: str, k: int = 4) -> list[LCDocument]:
    """
    Returns up to k chunks most similar to `query`, scoped to the given
    user's own indexed documents. Returns an empty list (rather than
    raising) if the user has no collection yet - "no documents indexed"
    is a normal state, not an error.

    Ranking is computed manually (retrieval/similarity.py's cosine
    similarity + heap-based top-k) rather than delegating to Chroma's
    internal ANN search - Chroma is still used purely as storage here
    (fetching raw vectors via .get()), not for the similarity ranking
    itself.

    Trade-off worth naming: the previous version called
    vector_store.as_retriever().invoke(query), which is a LangChain
    Runnable and therefore automatically traced by LangSmith (Milestone
    13) - VectorStoreRetriever IS a Runnable subclass, but a plain
    Python function computing similarity by hand is not, so it would be
    invisible in traces without help. The @traceable decorator above
    (from the langsmith package directly, not something LangChain wraps
    automatically) manually re-creates that same "retriever" span so
    this function keeps showing up correctly in traces despite no
    longer going through a Runnable at all.
    """
    started_at = time.monotonic()

    try:
        # Constructed once, reused for both the vector store's internal
        # setup and embedding the query directly below - avoids loading
        # the underlying model twice for what was previously a single
        # get_vector_store() call that handled embedding internally.
        embeddings = get_embeddings()
        vector_store = get_vector_store(user.id, embeddings=embeddings)

        # Chroma as storage only: fetch every stored vector for this
        # user's collection, embeddings included.
        stored = vector_store.get(include=["embeddings", "documents", "metadatas"])
        query_vector = embeddings.embed_query(query)

        candidates = [
            (stored_id, vector)
            for stored_id, vector in zip(stored["ids"], stored["embeddings"])
        ]
        ranked = top_k_by_similarity(query_vector, candidates, k=k)

        # top_k_by_similarity only returns (id, score) pairs - look the
        # actual text/metadata back up by id to build real LCDocuments,
        # since ranking and content are deliberately separate concerns.
        by_id = {
            stored_id: (doc, meta)
            for stored_id, doc, meta in zip(
                stored["ids"], stored["documents"], stored["metadatas"]
            )
        }
        results = [
            LCDocument(page_content=by_id[stored_id][0], metadata=by_id[stored_id][1])
            for stored_id, _score in ranked
        ]

        logger.info(
            "retrieval_query",
            extra={
                "user_id": user.id,
                "query_length": len(query),
                "k": k,
                "candidate_count": len(candidates),
                "result_count": len(results),
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )
        return results
    except Exception:
        # Query text itself isn't logged (may contain sensitive content
        # the user typed) - length and outcome are enough to see this
        # happening/how often, without putting arbitrary user input in
        # logs.
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