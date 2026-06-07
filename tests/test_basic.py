"""
Basic integration tests for the Agentic RAG system.

Tests cover:
- Config loading
- Document chunking
- Embedding generation
- Vector store CRUD
- Agent graph compilation
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_loading():
    """Test that config module loads without error."""
    from src.config import Config
    assert Config.PROJECT_ROOT.exists()
    assert Config.CHUNK_SIZE > 0
    assert Config.CHUNK_OVERLAP > 0
    print("[PASS]  Config loading passed")


def test_document_chunking():
    """Test chunking of a text document."""
    from src.rag.loader import chunk_documents, load_document
    from langchain_core.documents import Document

    # Create a test document
    docs = [Document(
        page_content="第一段内容。\n\n第二段内容。\n\n第三段内容。",
        metadata={"source": "test.txt"}
    )]
    chunks = chunk_documents(docs, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "source" in chunk.metadata
    print(f"[PASS]  Document chunking passed ({len(chunks)} chunks)")


def test_vector_store_operations():
    """Test ChromaDB basic CRUD operations (requires API key)."""
    from src.config import config

    if not config.DEEPSEEK_API_KEY:
        print("[SKIP]   Skipping vector store test (no API key)")
        return

    from src.rag.vector_store import (
        get_vector_store,
        add_documents,
        similarity_search,
        list_indexed_documents,
        get_document_count,
        clear_store,
    )
    from langchain_core.documents import Document

    # Clean up first
    clear_store()

    # Add test documents
    docs = [
        Document(
            page_content="人工智能是计算机科学的一个分支，旨在创建能够模拟人类智能的系统。",
            metadata={"source": "ai_intro.txt"}
        ),
        Document(
            page_content="机器学习是人工智能的子领域，通过数据和算法让计算机从经验中学习。",
            metadata={"source": "ai_intro.txt"}
        ),
        Document(
            page_content="Python是一种广泛使用的高级编程语言，以其简洁易读的语法而闻名。",
            metadata={"source": "python_intro.txt"}
        ),
    ]

    count = add_documents(docs)
    assert count == 3
    print(f"[PASS]  Added {count} documents to vector store")

    # List documents
    sources = list_indexed_documents()
    assert len(sources) == 2
    assert "ai_intro.txt" in sources
    print(f"[PASS]  Listed {len(sources)} source documents")

    # Search
    results = similarity_search("什么是人工智能", k=2)
    assert len(results) == 2
    assert "score" in results[0].metadata
    print(f"[PASS]  Similarity search returned {len(results)} results")

    # Cleanup
    clear_store()
    assert get_document_count() == 0
    print("[PASS] Vector store cleared successfully")


def test_agent_compilation():
    """Test that the agent graph compiles without error."""
    from src.config import config

    if not config.DEEPSEEK_API_KEY:
        print("[SKIP]   Skipping agent test (no API key)")
        return

    from src.agent.core import create_agent

    agent = create_agent()
    assert agent is not None
    print("[PASS]  Agent graph compiled successfully")


if __name__ == "__main__":
    print("=" * 50)
    print("Agentic RAG System — Integration Tests")
    print("=" * 50)

    tests = [
        ("Config Loading", test_config_loading),
        ("Document Chunking", test_document_chunking),
        ("Vector Store Operations", test_vector_store_operations),
        ("Agent Compilation", test_agent_compilation),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_fn in tests:
        try:
            print(f"\n>  {name}")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL]  {name} FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"{'=' * 50}")
