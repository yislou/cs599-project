"""
Document loader — loads and chunks documents for ingestion into the vector store.

Supported formats: PDF, TXT, MD, DOCX
Uses recursive character splitting with configurable chunk size and overlap.
"""

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import config


# Supported file extensions and their loaders
SUPPORTED_EXTENSIONS = {
    ".pdf": "pypdf",
    ".txt": "text",
    ".md": "text",
    ".docx": "docx",
}


def _load_pdf(file_path: str) -> List[Document]:
    """Load a PDF document using PyPDF loader."""
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    return loader.load()


def _load_text(file_path: str) -> List[Document]:
    """Load a plain text or markdown document."""
    from langchain_community.document_loaders import TextLoader
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()


def _load_docx(file_path: str) -> List[Document]:
    """Load a DOCX document."""
    from langchain_community.document_loaders import Docx2txtLoader
    loader = Docx2txtLoader(file_path)
    return loader.load()


LOADER_MAP = {
    ".pdf": _load_pdf,
    ".txt": _load_text,
    ".md": _load_text,
    ".docx": _load_docx,
}


def load_document(file_path: str) -> List[Document]:
    """
    Load a single document based on its file extension.

    Args:
        file_path: Absolute path to the document.

    Returns:
        List of Document objects (pages/sections).

    Raises:
        ValueError: If the file format is unsupported.
    """
    ext = Path(file_path).suffix.lower()
    if ext not in LOADER_MAP:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported: {list(SUPPORTED_EXTENSIONS.keys())}"
        )
    return LOADER_MAP[ext](file_path)


def chunk_documents(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """
    Split documents into smaller chunks for embedding.

    Args:
        documents: List of Document objects to split.
        chunk_size: Maximum token count per chunk (default from config).
        chunk_overlap: Overlap tokens between chunks (default from config).

    Returns:
        List of chunked Document objects.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.split_documents(documents)


def process_document(file_path: str) -> List[Document]:
    """
    Full pipeline: load a document and chunk it.

    Args:
        file_path: Absolute path to the document.

    Returns:
        List of chunked Document objects ready for embedding.
    """
    docs = load_document(file_path)
    chunks = chunk_documents(docs)

    # Add source filename as metadata for citation
    filename = Path(file_path).name
    for chunk in chunks:
        if "source" not in chunk.metadata:
            chunk.metadata["source"] = filename

    return chunks
