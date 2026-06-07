"""
Agent Core — LangGraph ReAct Agent implementation.

构建一个具有工具调用能力的 ReAct Agent：
1. 用户输入 → Agent 节点（LLM 推理）
2. 如果需要调用工具 → Tool 节点（执行工具）
3. 工具返回结果 → Agent 节点继续推理
4. 不需要工具时 → 生成最终回答 → END

Uses LangGraph StateGraph for the control flow.
"""

from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.config import config
from src.agent.tools import ALL_TOOLS


# ─── State Definition ────────────────────────────────────────────

class AgentState(TypedDict):
    """The state that flows through the LangGraph agent."""
    messages: Annotated[List[BaseMessage], add_messages]


# ─── LLM & Agent Graph ───────────────────────────────────────────

def create_llm() -> ChatOpenAI:
    """
    Create the DeepSeek chat LLM instance.

    DeepSeek API is OpenAI-compatible, so we use ChatOpenAI
    with the base_url pointed at DeepSeek.

    Returns:
        ChatOpenAI instance configured for DeepSeek.
    """
    return ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        temperature=0.3,  # Lower temperature for factual accuracy
        streaming=True,
    )


def create_agent() -> StateGraph:
    """
    Build the ReAct Agent StateGraph.

    Returns:
        A compiled StateGraph ready for invocation.

    Graph structure:
        agent (LLM + tools) → tools (execute) → agent → ... → END
    """
    llm = create_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # System prompt that guides the Agent behavior
    SYSTEM_PROMPT = """你是一个智能知识库助手，能够基于用户上传的文档回答问题。

你的工作方式：
1. **理解问题**：仔细理解用户的问题
2. **检索信息**：使用 search_knowledge_base 工具在知识库中查找相关内容
3. **综合分析**：基于检索到的文档内容进行分析和推理
4. **给出答案**：用清晰、准确的中文回答用户，并引用来源

重要规则：
- 回答问题时必须先检索知识库（使用 search_knowledge_base）
- 如果用户询问知识库中有哪些文档，使用 list_documents 工具
- 如果检索结果为空，诚实告诉用户没有找到相关信息
- 答案要基于文档内容，不要编造信息
- 引用来源时注明文档名称
- 如果用户的问题是闲聊或无关心话题，可以简短回应
- 始终使用中文回复
"""

    def agent_node(state: AgentState) -> dict:
        """Agent reasoning node — calls LLM with tools."""
        messages = state["messages"]

        # Prepend system prompt if it's the first message
        if not any(
            isinstance(m, (AIMessage,)) and hasattr(m, "tool_calls") is False
            for m in messages
        ):
            full_messages = [HumanMessage(content=SYSTEM_PROMPT)] + messages
        else:
            full_messages = messages

        response = llm_with_tools.invoke(full_messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        """Router: decide whether to call tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "__end__"

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))

    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# ─── Global agent instance ───────────────────────────────────────

_agent = None


def get_agent() -> StateGraph:
    """Get or create the global compiled agent graph."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def run_agent(
    user_message: str,
    chat_history: List[BaseMessage] = None,
) -> dict:
    """
    Run the agent with a user message and optional chat history.

    Args:
        user_message: The user's input text.
        chat_history: Previous conversation messages (optional).

    Returns:
        The final agent state containing all messages and the response.
    """
    agent = get_agent()
    messages = list(chat_history) if chat_history else []
    messages.append(HumanMessage(content=user_message))

    result = agent.invoke({"messages": messages})
    return result
