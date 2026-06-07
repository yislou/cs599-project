# API Spec — Agentic RAG 智能知识库助手

> **版本**: v1.0  
> **日期**: 2026-06-07

---

## 1. Agent Tool API

Agent 通过 Function Calling 机制调用以下工具。每个工具都有明确的名称、描述和参数 schema。

### 1.1 search_knowledge_base

**描述**: 在知识库中执行语义搜索，返回最相关的文档片段。

**参数**:
```json
{
  "name": "search_knowledge_base",
  "description": "在知识库中语义搜索相关文档片段。当用户询问任何需要查找信息的问题时使用此工具。",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "搜索查询 — 用自然语言描述你需要查找的内容"
      }
    },
    "required": ["query"]
  }
}
```

**返回值**:
```json
{
  "type": "string",
  "format": "格式化文本，包含来源、相关度、内容片段"
}
```

**示例返回值**:
```
[1] 来源: annual_report.pdf | 相关度: 0.8567
2025年公司营收达到120亿元，同比增长15%...

[2] 来源: q3_summary.txt | 相关度: 0.7834
第三季度核心业务收入为35亿元...
```

---

### 1.2 list_documents

**描述**: 列出知识库中所有已索引的文档清单。

**参数**:
```json
{
  "name": "list_documents",
  "description": "列出知识库中所有已索引的文档。当用户询问"有哪些文档"或需要了解知识库包含什么内容时使用。",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

**返回值**:
```json
{
  "type": "string",
  "format": "知识库统计信息 + 文档列表"
}
```

**示例返回值**:
```
知识库共 42 个片段，来自 3 个文档：
  - annual_report_2025.pdf
  - technical_whitepaper.docx
  - meeting_notes.md
```

---

### 1.3 get_context

**描述**: 获取与问题相关的完整上下文片段，用于深度分析。

**参数**:
```json
{
  "name": "get_context",
  "description": "获取与问题相关的最相关上下文，用于回答用户问题。",
  "parameters": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "用户的问题"
      }
    },
    "required": ["question"]
  }
}
```

**返回值**:
```json
{
  "type": "string",
  "format": "带来源标注的完整上下文片段"
}
```

---

## 2. Internal API (RAG Module)

以下接口为内部 Python API，供 Agent Tools 和 UI 层调用。

### 2.1 Vector Store API (`src/rag/vector_store.py`)

```python
# 添加文档到向量存储
add_documents(documents: List[Document]) -> int
# 返回: 添加的文档片段数

# 语义相似度搜索
similarity_search(query: str, k: int = 4) -> List[Document]
# 返回: 带 score 元数据的 Document 列表

# 列出已索引文档
list_indexed_documents() -> List[str]
# 返回: 去重排序的源文件名列表

# 获取文档总数
get_document_count() -> int

# 删除指定文档
delete_document(source_name: str) -> int
# 返回: 删除的片段数

# 清空知识库
clear_store() -> None
```

### 2.2 Loader API (`src/rag/loader.py`)

```python
# 加载单文档 (自动检测格式)
load_document(file_path: str) -> List[Document]

# 文档分块
chunk_documents(documents: List[Document], chunk_size?, chunk_overlap?) -> List[Document]

# 完整处理流程: 加载 + 分块
process_document(file_path: str) -> List[Document]
```

### 2.3 Embedder API (`src/rag/embedder.py`)

```python
# 创建嵌入实例
create_embeddings() -> Embeddings

# 单文本嵌入
embed_query(text: str) -> List[float]

# 批量嵌入
embed_documents(texts: List[str]) -> List[List[float]]
```

### 2.4 Agent API (`src/agent/core.py`)

```python
# 创建/获取编译好的 Agent
get_agent() -> StateGraph

# 执行 Agent (同步)
run_agent(user_message: str, chat_history: List[BaseMessage]?) -> dict
# 返回: {"messages": [..., AIMessage(content="回答")]}
```

## 3. Message Format (Agent State)

Agent 内部使用 LangChain 标准消息格式：

```python
# 用户消息
HumanMessage(content="这份报告的核心结论是什么？")

# AI 消息 (含工具调用)
AIMessage(
    content="",
    tool_calls=[{
        "name": "search_knowledge_base",
        "args": {"query": "核心结论 报告"},
        "id": "call_xxx"
    }]
)

# 工具返回
ToolMessage(content="[1] 来源: report.pdf...", tool_call_id="call_xxx")

# AI 最终回复
AIMessage(content="报告的核心结论是：2025年营收增长15%...（来源：report.pdf）")
```

## 4. Environment Variables

| 变量 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `DEEPSEEK_API_KEY` | string | ✅ | — | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | string | ❌ | `https://api.deepseek.com` | API 基础 URL |
| `LLM_MODEL` | string | ❌ | `deepseek-chat` | 对话模型 |
| `EMBEDDING_MODEL` | string | ❌ | `text-embedding-3-small` | 嵌入模型 |
| `CHUNK_SIZE` | int | ❌ | `1000` | 文档分块大小 |
| `CHUNK_OVERLAP` | int | ❌ | `200` | 分块重叠大小 |
| `MAX_HISTORY_TURNS` | int | ❌ | `10` | 最大对话轮数 |
| `TOP_K_RETRIEVAL` | int | ❌ | `4` | 检索返回数 |
