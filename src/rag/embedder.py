"""
Embedding generator — uses local sentence-transformers model for vector embeddings.

Since DeepSeek does not provide an Embedding API, we use a local model
(BAAI/bge-small-zh-v1.5) which supports Chinese-English bilingual text.
No extra API key needed — runs entirely on CPU.
"""

import os

# Set HF mirror and SSL before any huggingface imports
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
if "HF_HUB_DISABLE_SSL_VERIFY" not in os.environ:
    os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"

from typing import List

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import config


def create_embeddings() -> Embeddings:
    """
    Create a local HuggingFace embeddings instance.

    Uses BAAI/bge-small-zh-v1.5 — a lightweight Chinese-English
    bilingual model (512 dims, ~100MB download).

    Returns:
        HuggingFaceEmbeddings instance.
    """
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# Singleton embeddings instance
_embeddings: Embeddings = None


def get_embeddings() -> Embeddings:
    """Get or create the global embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = create_embeddings()
    return _embeddings


def embed_query(text: str) -> List[float]:
    """
    Generate embedding vector for a single query text.

    Args:
        text: Query string.

    Returns:
        Embedding vector as list of floats.
    """
    return get_embeddings().embed_query(text)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generate embedding vectors for multiple documents.

    Args:
        texts: List of document strings.

    Returns:
        List of embedding vectors.
    """
    return get_embeddings().embed_documents(texts)
