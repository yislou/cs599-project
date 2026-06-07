"""
Vector store — ChromaDB wrapper for document indexing and semantic search.

Provides CRUD operations on the persistent vector store,
serving as the long-term memory for the RAG system.
"""

import os
from typing import List, Optional

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import config
from src.rag.embedder import get_embeddings


# Collection name for our knowledge base
COLLECTION_NAME = "knowledge_base"


def _get_persist_dir() -> str:
    """Ensure the ChromaDB persistence directory exists."""
    persist_dir = config.CHROMA_PERSIST_DIR
    os.makedirs(persist_dir, exist_ok=True)
    return persist_dir


def get_vector_store() -> Chroma:
    """
    Get or create the Chroma vector store.

    Returns:
        Chroma vector store instance connected to the persisted collection.
    """
    persist_dir = _get_persist_dir()
    embeddings = get_embeddings()

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )


def add_documents(documents: List[Document]) -> int:
    """
    Add documents to the vector store.

    Args:
        documents: List of Document objects with content and metadata.

    Returns:
        Number of document IDs added.

    Raises:
        ValueError: If documents list is empty.
    """
    if not documents:
        raise ValueError("Cannot add empty document list to vector store.")

    store = get_vector_store()
    ids = store.add_documents(documents)
    return len(ids)


def similarity_search(
    query: str,
    k: int = None,
) -> List[Document]:
    """
    Perform semantic similarity search over the knowledge base.

    Args:
        query: Search query string.
        k: Number of top results to return (default from config).

    Returns:
        List of Document objects ranked by relevance, with similarity scores.
    """
    k = k or config.TOP_K_RETRIEVAL
    store = get_vector_store()
    results = store.similarity_search_with_score(query, k=k)
    docs = []
    for doc, score in results:
        doc.metadata["score"] = round(float(score), 4)
        docs.append(doc)
    return docs


def list_indexed_documents() -> List[str]:
    """
    List all unique source documents currently indexed.

    Returns:
        Sorted list of unique source filenames.
    """
    store = get_vector_store()
    try:
        results = store.get()
        if not results or not results["metadatas"]:
            return []
        sources = set()
        for meta in results["metadatas"]:
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(sources)
    except Exception:
        return []


def get_document_count() -> int:
    """Get the total number of chunks in the vector store."""
    store = get_vector_store()
    try:
        collection = store._collection
        return collection.count()
    except Exception:
        return 0


def clear_store() -> None:
    """Delete all documents from the vector store (use with caution)."""
    store = get_vector_store()
    try:
        # Delete all documents in the collection
        results = store.get()
        if results and results["ids"]:
            store.delete(ids=results["ids"])
    except Exception:
        pass


def delete_document(source_name: str) -> int:
    """
    Delete all chunks belonging to a specific source document.

    Args:
        source_name: The source filename to delete.

    Returns:
        Number of chunks deleted.
    """
    store = get_vector_store()
    try:
        results = store.get(where={"source": source_name})
        if results and results["ids"]:
            store.delete(ids=results["ids"])
            return len(results["ids"])
    except Exception:
        pass
    return 0
