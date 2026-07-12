from django.utils import timezone

from documents.models import Document
from retrieval.loaders import load_document_text
from retrieval.models import DocumentIndex
from retrieval.splitter import split_into_chunks
from retrieval.vectorstore import get_vector_store


def index_document(document: Document) -> DocumentIndex:
    """
    Runs the full indexing pipeline for one document: load -> split -> embed -> store in the vector store, updating a DocumentIndex row with the outcome either way.

    This runs synchronously (in the request/response cycle) for now,later move this exact function into a Celery task body unchanged - the only difference will be that the HTTP response returns immediately instead of waiting for it to finish.
    """
    index, _ = DocumentIndex.objects.get_or_create(document=document)

    try:
        raw_docs = load_document_text(document)
        chunks = split_into_chunks(document, raw_docs)

        if not chunks:
            raise ValueError("No extractable text found in this document.")

        vector_store = get_vector_store(document.user_id)
        # Clear any previous chunks for this document first, so re-running indexing (e.g. after a fix) doesn't leave duplicate entries.
        vector_store.delete(where={"document_id": document.id})

        ids = [f"doc{document.id}-chunk{i}" for i in range(len(chunks))]
        vector_store.add_documents(chunks, ids=ids)

        index.status = DocumentIndex.Status.INDEXED
        index.chunk_count = len(chunks)
        index.error = ""
        index.indexed_at = timezone.now()
    except Exception as exc:
        index.status = DocumentIndex.Status.FAILED
        index.error = str(exc)
        index.chunk_count = 0
    finally:
        index.save()

    return index