"""
Embedding generator — uses DeepSeek Embedding API to generate vector embeddings.

DeepSeek's embedding endpoint is OpenAI-compatible, so we use
the OpenAI embeddings client pointed at the DeepSeek base URL.
"""

from typing import List

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.config import config


def create_embeddings() -> Embeddings:
    """
    Create an embeddings client using DeepSeek API.

    Returns:
        OpenAIEmbeddings instance configured for DeepSeek.
    """
    return OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
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
