import logging
import time

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from retrieval.content import get_source_type
from retrieval.loaders import load_content_text
from retrieval.models import ContentIndex
from retrieval.splitter import split_into_chunks
from retrieval.vectorstore import get_vector_store

logger = logging.getLogger("retrieval.indexing")


def index_content(obj) -> ContentIndex:
    """
    Runs the full i ndexing pipeline for one piece of content (a Document or a Note): load -> split -> embed -> store, updating a ContentIndex row with the outcome either way.
    
    Generic over content type via Django's contenttypes framework - this is what lets one retriever/tool search documents and notes together, ranked by relevance, instead of the agent guessing which of several separate tools to call.

    Runs as the body of a Celery task (in tasks/retrieval_tasks.py) - this function's own logic is unchanged from when it ran synchronously, only its caller changed.
    """

    content_type = ContentType.objects.get_for_model(obj)
    index, _ = ContentIndex.objects.get_or_create(
        content_type=content_type, object_id=obj.pk
    )

    started_at = time.monotonic()
    source_type = get_source_type(obj)

    try:
        raw_docs = load_content_text(obj)
        chunks = split_into_chunks(obj, raw_docs)

        if not chunks:
            raise ValueError("No extractable text found in this content.")

        vector_store = get_vector_store(obj.user_id)

        # Clear any previous chunks for this document first, so re-running indexing (e.g. after a fix) doesn't leave duplicate entries.
        # vector_store.delete(where={"document_id": document.id})

        # Delete by reconstructed ids, not a `where` metadata filter.`where` happens to work with Chroma (it forwards **kwargs to theunderlying collection), but that's not part of LangChain'sportable VectorStore interface - a different backend might notsupport it. Chunk ids are deterministic (doc{id}-chunk{i}), so the exact ids a previous run created can always be reconstructedand deleted directly with `ids=`, which every VectorStoreimplementation supports.

        # We delete up to max(previous count, new count), not justrange(len(chunks)): if this re-index produced *fewer* chunks than before, chunks beyond the new count would otherwise be orphaned in the vector store forever.

        previous_chunk_count = max(index.chunk_count, len(chunks))
        if previous_chunk_count > 0:
            stale_ids = [f"{source_type}{obj.pk}-chunk{i}" for i in range(previous_chunk_count)]
            vector_store.delete(ids=stale_ids)

        ids = [f"{source_type}{obj.pk}-chunk{i}" for i in range(len(chunks))]
        vector_store.add_documents(chunks, ids=ids)

        index.status = ContentIndex.Status.INDEXED
        index.chunk_count = len(chunks)
        index.error = ""
        index.indexed_at = timezone.now()
 
        logger.info(
            "indexing_completed",
            extra={
                "source_type": source_type,
                "object_id": obj.pk,
                "user_id": obj.user_id,
                "chunk_count": len(chunks),
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )

    except Exception as exc:
        index.status = ContentIndex.Status.FAILED
        index.error = str(exc)
        index.chunk_count = 0

        logger.exception(
            "indexing_failed",
            extra={
                "source_type": source_type,
                "object_id": obj.pk,
                "user_id": obj.user_id,
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )
    finally:
        index.save()

    return index