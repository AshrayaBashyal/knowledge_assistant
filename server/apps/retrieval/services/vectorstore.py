from pathlib import Path

from django.conf import settings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from apps.retrieval.services.embeddings import get_embeddings


def get_vector_store(user_id: int, embeddings: Embeddings | None = None) -> Chroma:
    """
    Returns a Chroma collection scoped to one user.

    One collection per user (rather than one shared collection filtered
    by a user_id metadata field) is a stronger isolation guarantee: a bug
    in a `where` filter can't leak another user's chunks if their chunks
    are never stored in the same collection to begin with. The trade-off
    is many small collections instead of one big one - fine at the
    small/medium scale ChromaDB targets.

    `embeddings` is optional - pass an already-constructed instance if
    the caller also needs to embed something directly (e.g.
    retriever.py embedding the query itself for manual similarity
    ranking), so the underlying model only gets loaded once per call
    instead of twice. Defaults to building a fresh one, unchanged from
    before, for every other caller that doesn't need this.
    """
    persist_dir = Path(settings.CHROMA_PERSIST_DIR) / f"user_{user_id}"
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"user_{user_id}_documents",
        embedding_function=embeddings or get_embeddings(),
        persist_directory=str(persist_dir),
    )