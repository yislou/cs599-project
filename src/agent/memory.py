"""
Conversation Memory — manages multi-turn dialogue history.

Implements a sliding-window memory that keeps the last N turns
of conversation to stay within the LLM context window limit.
"""

from typing import List, Dict


class ConversationMemory:
    """
    Sliding-window conversation memory.

    Maintains a list of messages (user/assistant pairs) and
    trims them to the configured maximum number of turns.
    """

    def __init__(self, max_turns: int = 10):
        """
        Args:
            max_turns: Maximum conversation turns to retain.
                       One turn = one user message + one assistant response.
        """
        self.max_turns = max_turns
        self._messages: List[Dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        """Append a user message to the history."""
        self._messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant (AI) message to the history."""
        self._messages.append({"role": "assistant", "content": content})
        self._trim()

    def _trim(self) -> None:
        """Trim messages to keep only the last max_turns * 2 messages."""
        max_messages = self.max_turns * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

    def get_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return list(self._messages)

    def get_history_text(self) -> str:
        """Get conversation history as a formatted string."""
        if not self._messages:
            return "（这是对话的开始，暂无历史记录）"
        parts = []
        for msg in self._messages[-10:]:  # Last 5 turns max
            role = "用户" if msg["role"] == "user" else "助手"
            parts.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(parts)

    def get_last_user_message(self) -> str:
        """Get the most recent user message."""
        for msg in reversed(self._messages):
            if msg["role"] == "user":
                return msg["content"]
        return ""

    def clear(self) -> None:
        """Clear all conversation history."""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)

    @property
    def turn_count(self) -> int:
        """Number of complete turns (user-assistant pairs)."""
        return len([m for m in self._messages if m["role"] == "user"])
