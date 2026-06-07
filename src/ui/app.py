"""
Streamlit UI — 聊天界面与文档管理。

Provides:
- Chat interface with message history
- Sidebar for document upload and management
- Agent thinking process visualization (tool calls)
- System status display
"""

import os
import tempfile
from pathlib import Path
from typing import List

import streamlit as st
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from src.config import config
from src.rag.loader import process_document
from src.rag.vector_store import (
    add_documents,
    list_indexed_documents,
    get_document_count,
    delete_document,
    clear_store,
)
from src.agent.core import get_agent, run_agent
from src.agent.memory import ConversationMemory


# ─── Page Configuration ──────────────────────────────────────────

def setup_page():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Agentic RAG Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(config.STREAMLIT_TITLE)
    st.caption("基于 DeepSeek + LangGraph + ChromaDB 的智能知识库问答系统")


# ─── Session State Initialization ─────────────────────────────────

def init_session():
    """Initialize Streamlit session state variables."""
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory(
            max_turns=config.MAX_HISTORY_TURNS
        )
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


# ─── Sidebar: Document Management ─────────────────────────────────

def render_sidebar():
    """Render the sidebar with document upload and management UI."""
    with st.sidebar:
        st.header("📁 知识库管理")

        # ── Upload Section ──
        st.subheader("上传文档")
        uploaded_files = st.file_uploader(
            "支持 PDF, TXT, MD, DOCX 格式",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            key="doc_uploader",
        )

        if uploaded_files:
            if st.button("🚀 导入知识库", type="primary", use_container_width=True):
                with st.spinner("正在处理文档..."):
                    success_count = 0
                    for file in uploaded_files:
                        try:
                            # Save to temp file and process
                            suffix = Path(file.name).suffix
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=suffix
                            ) as tmp:
                                tmp.write(file.getvalue())
                                tmp_path = tmp.name

                            chunks = process_document(tmp_path)
                            if chunks:
                                count = add_documents(chunks)
                                success_count += 1
                                st.toast(f"✅ {file.name} — {count} 个片段已索引")

                            # Cleanup
                            os.unlink(tmp_path)
                        except Exception as e:
                            st.toast(f"❌ {file.name} — 处理失败: {e}")

                    if success_count > 0:
                        st.success(f"成功导入 {success_count}/{len(uploaded_files)} 个文档")
                        st.rerun()

        st.divider()

        # ── Knowledge Base Status ──
        st.subheader("📊 知识库状态")
        doc_count = get_document_count()
        sources = list_indexed_documents()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("片段数", doc_count)
        with col2:
            st.metric("文档数", len(sources))

        if sources:
            st.write("**已索引文档：**")
            for source in sources:
                cols = st.columns([4, 1])
                with cols[0]:
                    st.text(f"📄 {source}")
                with cols[1]:
                    if st.button("🗑️", key=f"del_{source}", help=f"删除 {source}"):
                        count = delete_document(source)
                        st.toast(f"已删除 {source} 的 {count} 个片段")
                        st.rerun()

        if doc_count > 0:
            if st.button("⚠️ 清空知识库", use_container_width=True):
                clear_store()
                st.toast("知识库已清空")
                st.rerun()

        st.divider()

        # ── System Info ──
        st.subheader("⚙️ 系统信息")
        st.caption(f"LLM: {config.LLM_MODEL}")
        st.caption(f"Embedding: {config.EMBEDDING_MODEL}")
        st.caption(f"Chunk: {config.CHUNK_SIZE}/{config.CHUNK_OVERLAP}")
        st.caption(f"History: {config.MAX_HISTORY_TURNS} turns")


# ─── Main Chat Area ───────────────────────────────────────────────

def render_chat():
    """Render the chat interface in the main area."""
    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("请输入你的问题..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.memory.add_user_message(prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        # Run agent
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    # Build message history for agent
                    history_messages = []
                    for msg in st.session_state.chat_messages[:-1]:
                        if msg["role"] == "user":
                            history_messages.append(HumanMessage(content=msg["content"]))
                        else:
                            history_messages.append(AIMessage(content=msg["content"]))

                    # Invoke agent
                    result = run_agent(prompt, history_messages)

                    # Extract agent response and tool calls
                    response_text = ""
                    tool_calls_made = []

                    for m in result["messages"]:
                        if isinstance(m, AIMessage):
                            if hasattr(m, "tool_calls") and m.tool_calls:
                                for tc in m.tool_calls:
                                    tool_calls_made.append({
                                        "name": tc.get("name", "unknown"),
                                        "args": tc.get("args", {}),
                                    })
                            if m.content:
                                response_text += m.content

                    # Display tool calls in expandable section
                    if tool_calls_made:
                        with st.expander("🔍 Agent 思考过程", expanded=False):
                            for tc in tool_calls_made:
                                st.caption(f"🔧 调用工具: **{tc['name']}**")
                                args_str = str(tc.get("args", {}))
                                if len(args_str) > 200:
                                    args_str = args_str[:200] + "..."
                                st.code(args_str, language="json")

                    # Display final answer
                    if response_text:
                        st.markdown(response_text)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": response_text,
                        })
                        st.session_state.memory.add_assistant_message(response_text)
                    else:
                        st.warning("Agent 未生成回复，请重试。")

                except Exception as e:
                    error_msg = f"⚠️ 发生错误: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })


def render_app():
    """Main app entry — called from main.py."""
    setup_page()
    init_session()
    render_sidebar()
    render_chat()
