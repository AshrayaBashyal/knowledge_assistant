from pathlib import Path

from django.conf import settings
from langchain_chroma import Chroma

from retrieval.embeddings import get_embeddings


def get_vector_store(user_id: int) -> Chroma:
    """
    Returns a Chroma collection scoped to one user.

    One collection per user (rather than one shared collection filtered
    by a user_id metadata field) is a stronger isolation guarantee: a bug
    in a `where` filter can't leak another user's chunks if their chunks
    are never stored in the same collection to begin with. The trade-off
    is many small collections instead of one big one - fine at the
    small/medium scale ChromaDB targets|--> NOT for pgvector or pinecone
    """
    persist_dir = Path(settings.CHROMA_PERSIST_DIR) / f"user_{user_id}"
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"user_{user_id}_documents",
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )