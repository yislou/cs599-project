# 🤖 Agentic RAG — 智能知识库助手

> **CS599 期末大作业 — 方向一: Agentic AI 原生开发**
>
> 基于 DeepSeek + LangGraph + ChromaDB 构建的智能知识库问答系统

[![tag](https://img.shields.io/badge/version-v0.1-blue)](https://github.com/yislou/cs599-project/releases/tag/v0.1)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 项目简介

Agentic RAG 智能知识库助手是一款基于**检索增强生成 (RAG)** 与 **AI Agent** 技术的智能问答系统。

- 📄 **上传文档** → 自动分块 → 向量化存储
- 🔍 **语义检索** → Agent 多步推理 → 精准回答
- 🧠 **多轮对话** → 上下文记忆 → 自然追问
- 📎 **来源引用** → 每一条答案都可追溯

### 核心闭环

```
[文档上传] → [Chunking] → [Embedding] → [Vector Store]
                                                ↓
[用户提问] → [Agent ReAct] → [检索工具] → [推理回答]
                                                ↓
                              [多轮记忆] ← [存入历史]
```

---

## 🏗 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **LLM** | DeepSeek Chat API | 性价比高的国产大模型 |
| **Embedding** | DeepSeek Embedding | 1536 维文本向量化 |
| **Agent 框架** | LangGraph | ReAct 模式，显式状态图 |
| **向量数据库** | ChromaDB | 嵌入式，零运维 |
| **UI** | Streamlit | 快速构建聊天界面 |
| **文档解析** | PyPDF + python-docx | 多格式支持 |
| **容器化** | Docker | 一键部署 |

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- DeepSeek API Key ([获取地址](https://platform.deepseek.com/))

### 1. 克隆仓库

```bash
git clone https://github.com/yislou/cs599-project.git
cd cs599-project
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动应用

```bash
streamlit run src/main.py
```

浏览器访问 `http://localhost:8501` 即可使用。

### 5. Docker 部署（可选）

```bash
docker compose up -d
```

---

## 📁 项目结构

```
cs599-project/
├── README.md                    # 本文件
├── LICENSE                      # MIT
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── .gitignore
├── docker-compose.yml           # Docker 编排
├── Dockerfile
├── specs/                       # SDD 规格文档
│   ├── product_spec.md          # 产品规格书
│   ├── architecture_spec.md     # 架构规格书
│   └── api_spec.md              # API/Tool 规格书
├── src/
│   ├── main.py                  # Streamlit 入口
│   ├── config.py                # 配置管理
│   ├── agent/                   # Agent 核心
│   │   ├── core.py              # LangGraph ReAct Agent
│   │   ├── tools.py             # Tool 定义 (3 tools)
│   │   └── memory.py            # 对话记忆
│   ├── rag/                     # RAG 模块
│   │   ├── loader.py            # 文档加载 & 分块
│   │   ├── embedder.py          # DeepSeek Embedding
│   │   └── vector_store.py      # ChromaDB 操作
│   └── ui/
│       └── app.py               # Streamlit UI
├── data/                        # 上传文档 (gitignored)
└── tests/
    └── test_basic.py            # 基础测试
```

---

## 🎯 核心技术要素

| 要素 | 实现 |
|------|------|
| ✅ **SDD 规格驱动开发** | Product/Architecture/API 三份 Spec |
| ✅ **工具使用 / Function Calling** | 3 个自定义 Agent Tool |
| ✅ **记忆机制** | 对话滑动窗口 + ChromaDB 向量持久化 |
| ✅ **状态管理与多步推理** | LangGraph ReAct Agent |
| ✅ **可观测性** | Agent 思考链可视化 |

---

## 📝 使用示例

1. 打开应用后，在侧边栏上传 PDF/TXT/MD/DOCX 文档
2. 点击「导入知识库」按钮
3. 在聊天框输入问题，如：
   - "总结这份文档的核心内容"
   - "文档中提到了哪些关键数据？"
   - "刚才说的 X 具体是什么意思？"（多轮追问）
4. 查看 Agent 思考过程（展开 🔍 面板）
5. 回答中自动标注来源

---

## 📄 许可

MIT License — 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration
- [ChromaDB](https://github.com/chroma-core/chroma) — Vector database
- [DeepSeek](https://www.deepseek.com/) — LLM & Embedding API
- [Streamlit](https://streamlit.io/) — UI framework
