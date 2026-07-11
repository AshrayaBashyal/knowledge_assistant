import os
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings() -> Embeddings:
    """
    Factory method to initialize and return the embedding model.
    
    This acts as a retrieval-side equivalent to llm/providers.get_chat_model(). 
    By centralizing the initialization, it allows for easy switching to a hosted 
    API later without needing to refactor multiple files. Imports are kept 
    inside the function to prevent the slow loading of PyTorch and 
    sentence-transformers dependencies unless this specific function is called.
    """
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name=model_name)
