import logging
import os
from pathlib import Path

from django.conf import settings
from langchain_core.embeddings import Embeddings

from apps.retrieval.services.embeddings import get_embeddings

logger = logging.getLogger("retrieval.vectorstore")


class NamespacedVectorStoreWrapper:
    """
    Lightweight proxy around any VectorStore that ensures `namespace`
    is explicitly delivered on every add, query, and delete operation.
    This protects against version differences across vectorstore libraries.
    """

    def __init__(self, store, namespace: str):
        self._store = store
        self.namespace = namespace

    def add_documents(self, documents, ids=None, **kwargs):
        kwargs.setdefault("namespace", self.namespace)
        return self._store.add_documents(documents, ids=ids, **kwargs)

    def delete(self, ids=None, delete_all=None, **kwargs):
        kwargs.setdefault("namespace", self.namespace)
        try:
            return self._store.delete(ids=ids, delete_all=delete_all, **kwargs)
        except TypeError:
            # Fallback if the underlying vectorstore doesn't take namespace in delete()
            return self._store.delete(ids=ids, delete_all=delete_all)

    def similarity_search(self, query: str, k: int = 4, **kwargs):
        kwargs.setdefault("namespace", self.namespace)
        return self._store.similarity_search(query, k=k, **kwargs)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        kwargs.setdefault("namespace", self.namespace)
        return self._store.similarity_search_with_score(query, k=k, **kwargs)

    def as_retriever(self, **kwargs):
        search_kwargs = kwargs.setdefault("search_kwargs", {})
        search_kwargs.setdefault("namespace", self.namespace)
        return self._store.as_retriever(**kwargs)

    def __getattr__(self, name):
        return getattr(self._store, name)


def _init_pinecone(user_id: int, emb: Embeddings, api_key: str, index_name: str):
    """
    Initializes a Pinecone Serverless vector store with auto-index creation and user namespace scoping.
    """
    try:
        from pinecone import Pinecone, ServerlessSpec
        from langchain_pinecone import PineconeVectorStore
    except ImportError:
        logger.warning(
            "Pinecone packages not installed ('pinecone' or 'langchain-pinecone'). "
            "Falling back to local Chroma storage."
        )
        return None

    try:
        pc = Pinecone(api_key=api_key)

        # In modern Pinecone, check if index exists. If not, auto-create it on the free Serverless tier
        if not pc.has_index(index_name):
            # Probe embedding dimension dynamically
            try:
                probe_dim = len(emb.embed_query("probe"))
            except Exception:
                probe_dim = 768  # Standard for Gemini text-embedding-004

            logger.info(
                f"Pinecone index '{index_name}' does not exist. "
                f"Auto-creating serverless index in AWS us-east-1 with dimension {probe_dim}..."
            )
            pc.create_index(
                name=index_name,
                dimension=probe_dim,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        index = pc.Index(index_name)
        raw_store = PineconeVectorStore(
            index=index,
            embedding=emb,
            namespace=f"user_{user_id}",
        )
        return NamespacedVectorStoreWrapper(raw_store, namespace=f"user_{user_id}")
    except Exception as exc:
        logger.exception(
            f"Failed to initialize Pinecone vector store: {exc}. "
            "Falling back to local Chroma."
        )
        return None


def _init_qdrant(user_id: int, emb: Embeddings, url: str, api_key: str, collection: str):
    """
    Initializes a Qdrant Cloud vector store (Permanent Free 1GB Cluster).
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        logger.warning(
            "Qdrant packages not installed ('qdrant-client' or 'langchain-qdrant'). "
            "Falling back to local Chroma."
        )
        return None

    try:
        client = QdrantClient(url=url, api_key=api_key)
        user_collection = f"{collection}_user_{user_id}"

        if not client.collection_exists(user_collection):
            try:
                probe_dim = len(emb.embed_query("probe"))
            except Exception:
                probe_dim = 768

            client.create_collection(
                collection_name=user_collection,
                vectors_config=VectorParams(size=probe_dim, distance=Distance.COSINE),
            )

        raw_store = QdrantVectorStore(
            client=client,
            collection_name=user_collection,
            embedding=emb,
        )
        return raw_store
    except Exception as exc:
        logger.exception(
            f"Failed to initialize Qdrant vector store: {exc}. "
            "Falling back to local Chroma."
        )
        return None


def _init_chroma(user_id: int, emb: Embeddings):
    """
    Default local / in-container Chroma vector store.
    """
    from langchain_chroma import Chroma

    persist_dir = Path(settings.CHROMA_PERSIST_DIR) / f"user_{user_id}"
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"user_{user_id}_documents",
        embedding_function=emb,
        persist_directory=str(persist_dir),
    )


def get_vector_store(user_id: int, embeddings: Embeddings | None = None):
    """
    Returns an indexed VectorStore collection scoped to one user.

    Supports:
    1. Pinecone (Serverless Cloud Vector DB - AWS us-east-1 free tier):
       Uses user-level namespaces (f"user_{user_id}") with auto-index creation.
    2. Qdrant Cloud (Permanent Free 1GB cluster):
       Uses user-level collections with auto-collection creation.
    3. Chroma (Local / SQLite / Persistent):
       Zero-configuration default fallback for local dev or when cloud vector DBs are unset.
    """
    emb = embeddings or get_embeddings()

    provider = os.getenv("VECTOR_STORE_PROVIDER", "").strip().lower()

    # 1. Pinecone
    pinecone_key = os.getenv("PINECONE_API_KEY", "").strip()
    pinecone_index = os.getenv("PINECONE_INDEX_NAME", "knowledge-assistant").strip()
    if provider == "pinecone" or (not provider and pinecone_key):
        store = _init_pinecone(user_id, emb, pinecone_key, pinecone_index)
        if store is not None:
            return store

    # 2. Qdrant Cloud
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_key = os.getenv("QDRANT_API_KEY", "").strip()
    qdrant_coll = os.getenv("QDRANT_COLLECTION_NAME", "knowledge_assistant").strip()
    if provider == "qdrant" or (not provider and qdrant_url and qdrant_key):
        store = _init_qdrant(user_id, emb, qdrant_url, qdrant_key, qdrant_coll)
        if store is not None:
            return store

    # 3. Local Chroma fallback
    return _init_chroma(user_id, emb)
