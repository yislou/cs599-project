# Architecture Spec — Agentic RAG 智能知识库助手

> **版本**: v1.0  
> **日期**: 2026-06-07

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  ┌──────────────┐  ┌──────────────────────────────────┐    │
│  │   Sidebar     │  │        Chat Area                 │    │
│  │  - Upload     │  │  - Message History              │    │
│  │  - Status     │  │  - Agent Thinking (expand)      │    │
│  │  - Manage     │  │  - Source Citations              │    │
│  └──────────────┘  └──────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Agent Layer (LangGraph)                    │
│  ┌──────────┐     ┌───────────────┐    ┌──────────────┐    │
│  │  Agent   │────▶│  Tool Router  │───▶│  Tool Node   │    │
│  │  Node    │◀────│               │    │  (Execute)   │    │
│  │ (LLM)    │     └───────────────┘    └──────────────┘    │
│  └──────────┘                                              │
│      │                                                     │
│      ▼                                                     │
│  ┌──────────────────────────────────────────┐              │
│  │           Conversation Memory            │              │
│  │     (Sliding Window, Last N Turns)       │              │
│  └──────────────────────────────────────────┘              │
├─────────────────────────────────────────────────────────────┤
│                     RAG Layer                               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │  Loader  │─▶│  Embedder    │─▶│  Vector Store     │    │
│  │(PyPDF,   │  │(DeepSeek)    │  │  (ChromaDB)       │    │
│  │ Docx2txt)│  │              │  │                   │    │
│  └──────────┘  └──────────────┘  └───────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure                            │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │  Config  │  │  DeepSeek    │  │  Docker           │    │
│  │(.env)    │  │  API Client  │  │  Container         │    │
│  └──────────┘  └──────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 2. Agent 交互流程 (ReAct Pattern)

```
用户: "这份报告的核心结论是什么？"
         │
         ▼
    ┌─────────┐
    │  Agent  │ ── Think: 需要检索文档内容
    │  Node   │    Action: search_knowledge_base("核心结论 报告")
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Tool   │ ── 执行语义检索
    │  Node   │    → 返回 Top-4 相关片段
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Agent  │ ── Think: 已获得足够上下文
    │  Node   │    → 基于检索结果生成回答
    └────┬────┘
         │
         ▼
      最终回答:
      "报告的核心结论是...（来源：annual_report_2025.pdf）"
```

## 3. 数据流设计

### 3.1 文档摄入流 (Ingestion Pipeline)

```
文件上传 → 格式检测 → 文档加载 → 递归分块 → Embedding → ChromaDB 持久化
                                                                    │
                                              向量索引 + 元数据(source, page, score)
```

### 3.2 问答流 (Query Pipeline)

```
用户提问 → Agent Node (LLM) → 决策 → Tool Call (检索)
                                    ↓
                               ChromaDB 相似度搜索
                                    ↓
                              Top-K 相关片段返回
                                    ↓
                              Agent Node (LLM) → 综合推理
                                    ↓
                              生成回答 + 引用来源
                                    ↓
                              存入 Conversation Memory
```

## 4. 组件规格

### 4.1 Config 模块 (`src/config.py`)
- **职责**: 环境变量加载、全局配置管理
- **输入**: .env 文件
- **输出**: Config 单例对象
- **关键配置**: DEEPSEEK_API_KEY, LLM_MODEL, CHUNK_SIZE

### 4.2 Loader 模块 (`src/rag/loader.py`)
- **职责**: 多格式文档加载 + 递归分块
- **支持格式**: PDF (PyPDF), TXT/MD (TextLoader), DOCX (Docx2txt)
- **分块策略**: RecursiveCharacterTextSplitter, chunk_size=1000, overlap=200
- **分隔符优先级**: `\n\n` > `\n` > `。` > `.` > ` `

### 4.3 Embedder 模块 (`src/rag/embedder.py`)
- **职责**: 文本向量化
- **实现**: DeepSeek Embedding API (OpenAI 兼容)
- **模型**: text-embedding-3-small (1536 维)

### 4.4 Vector Store 模块 (`src/rag/vector_store.py`)
- **职责**: 向量存储与检索 CRUD
- **实现**: ChromaDB (持久化)
- **Collection**: knowledge_base
- **检索**: 余弦相似度 Top-K

### 4.5 Agent Core 模块 (`src/agent/core.py`)
- **职责**: LangGraph ReAct Agent 编排
- **节点**: agent (LLM+Tools), tools (ToolNode)
- **路由**: 条件边 (有 tool_calls → tools, 无 → END)
- **LLM**: DeepSeek Chat (via langchain-openai)

### 4.6 Tools 模块 (`src/agent/tools.py`)
- **职责**: Agent 可调用工具定义
- **工具**: search_knowledge_base, list_documents, get_context

### 4.7 Memory 模块 (`src/agent/memory.py`)
- **职责**: 对话历史管理
- **策略**: 滑动窗口 (最近 10 轮)
- **存储**: Streamlit session_state

## 5. 技术选型理由

| 技术 | 理由 |
|------|------|
| LangGraph | 提供显式状态图，比 LangChain AgentExecutor 更可控、更可观测 |
| ChromaDB | 嵌入式数据库，零运维开销，适合 MVP |
| Streamlit | 最快的 Python UI 框架，原生支持聊天组件 |
| DeepSeek | OpenAI 兼容 API，性价比高，国内访问稳定 |
| RecursiveCharacterTextSplitter | 支持多级分隔符，中文友好 |
