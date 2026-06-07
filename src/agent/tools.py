"""
Agent Tools — Function Calling 工具定义。

Defines the tools that the Agent can invoke to interact with
the knowledge base. Each tool is a callable function wrapped
with LangChain's @tool decorator for use in the ReAct agent.
"""

from typing import List, Optional

from langchain_core.tools import tool
from langchain_core.documents import Document

from src.rag.vector_store import (
    similarity_search,
    list_indexed_documents,
    get_document_count,
)


@tool
def search_knowledge_base(query: str) -> str:
    """
    在知识库中语义搜索相关文档片段。

    当用户询问任何需要查找信息的问题时使用此工具。
    返回最相关的文档片段及其来源和相似度分数。

    Args:
        query: 搜索查询 — 用自然语言描述你需要查找的内容。
    """
    results: List[Document] = similarity_search(query, k=4)
    if not results:
        return "知识库中没有找到相关信息。请先上传文档。"
    parts = []
    for i, doc in enumerate(results, 1):
        score = doc.metadata.get("score", "N/A")
        source = doc.metadata.get("source", "未知来源")
        content = doc.page_content[:500]  # Truncate for display
        parts.append(
            f"[{i}] 来源: {source} | 相关度: {score}\n{content}\n"
        )
    return "\n".join(parts)


@tool
def list_documents() -> str:
    """
    列出知识库中所有已索引的文档。

    当用户询问"有哪些文档"或需要了解知识库包含什么内容时使用。
    """
    sources = list_indexed_documents()
    count = get_document_count()
    if not sources:
        return "知识库为空，尚未索引任何文档。"
    lines = [f"知识库共 {count} 个片段，来自 {len(sources)} 个文档："]
    for s in sources:
        lines.append(f"  - {s}")
    return "\n".join(lines)


@tool
def get_context(question: str) -> str:
    """
    获取与问题相关的最相关上下文，用于回答用户问题。

    此工具合并了检索和上下文提取，Agent 应优先使用
    search_knowledge_base 进行检索，然后使用本工具获取完整上下文。

    Args:
        question: 用户的问题。
    """
    results = similarity_search(question, k=5)
    if not results:
        return "未找到相关上下文。"
    parts = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "未知")
        parts.append(f"--- 片段 {i} (来源: {source}) ---\n{doc.page_content}")
    return "\n\n".join(parts)


# All available tools
ALL_TOOLS = [
    search_knowledge_base,
    list_documents,
    get_context,
]
