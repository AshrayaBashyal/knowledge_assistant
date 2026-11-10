import os
import random
from django.conf import settings
from langchain_core.embeddings import Embeddings


def get_embeddings() -> Embeddings:
    """
    Factory method to initialize and return the embedding model.
    
    Supports:
    1. Google Gemini Embeddings (models/text-embedding-004):
       Ideal for cloud deployment (Render free tier, Vercel). Consumes 0 MB of RAM,
       avoids heavy PyTorch dependencies, and uses the free Google AI Studio tier.
    2. Local HuggingFace sentence-transformers:
       Used when EMBEDDING_PROVIDER="huggingface" or running locally offline.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()

    # Default to Gemini if EMBEDDING_PROVIDER is "gemini", or if a Gemini key is present and not explicitly set to huggingface
    gemini_key_exists = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS"))
    use_gemini = provider == "gemini" or (provider != "huggingface" and gemini_key_exists)

    if use_gemini:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_keys_raw = os.getenv("GEMINI_API_KEYS", "").strip()
        if api_keys_raw:
            api_keys = [k.strip() for k in api_keys_raw.split(",") if k.strip()]
            selected_key = random.choice(api_keys) if api_keys else None
        else:
            selected_key = os.getenv("GEMINI_API_KEY")

        if not selected_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embeddings.")

        embedding_model = os.getenv(
            "GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"
        )
        return GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=selected_key,
        )

    # HuggingFace fallback (local)
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = getattr(
        settings, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    return HuggingFaceEmbeddings(model_name=model_name)
