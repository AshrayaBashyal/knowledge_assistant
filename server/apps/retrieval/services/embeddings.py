import os
import random
from django.conf import settings
from langchain_core.embeddings import Embeddings


def get_embeddings() -> Embeddings:
    """
    Factory method to initialize and return the embedding model.
    
    Supports:
    1. Google Gemini Embeddings (models/gemini-embedding-001):
       Ideal for cloud deployment (Render free tier, Vercel). Consumes 0 MB of RAM,
       avoids heavy PyTorch dependencies, and uses the free Google AI Studio tier.
    2. Local HuggingFace sentence-transformers:
       Used when EMBEDDING_PROVIDER="huggingface" or running locally offline.
    """
    provider = (
        os.getenv("EMBEDDING_PROVIDER") or settings.EMBEDDING_PROVIDER
    ).strip().lower()

    if provider not in {"gemini", "huggingface"}:
        raise ValueError(
            "EMBEDDING_PROVIDER must be either 'gemini' or 'huggingface'."
        )

    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_keys_raw = os.getenv("GEMINI_API_KEYS", "").strip()
        if api_keys_raw:
            api_keys = [
                key.strip()
                for key in api_keys_raw.split(",")
                if key.strip() and not key.strip().lower().startswith("your_")
            ]
            selected_key = random.choice(api_keys) if api_keys else None
        else:
            selected_key = os.getenv("GEMINI_API_KEY", "").strip()

        if selected_key and selected_key.lower().startswith("your_"):
            selected_key = None
        if not selected_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embeddings.")

        embedding_model = settings.GEMINI_EMBEDDING_MODEL
        return GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=selected_key,
            output_dimensionality=768,
        )

    # HuggingFace fallback (local)
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = getattr(
        settings, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    return HuggingFaceEmbeddings(model_name=model_name)
