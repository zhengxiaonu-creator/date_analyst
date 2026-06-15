"""对话历史管理模块 — 支持上限截断。"""

from __future__ import annotations

from typing import List

from .constants import MAX_CONVERSATION_HISTORY


class ConversationManager:
    """管理 LLM 对话历史，自动限制消息数量。"""

    def __init__(self, max_messages: int = MAX_CONVERSATION_HISTORY):
        self.max_messages = max_messages
        self._messages: List[dict] = []

    def append(self, role: str, content: str) -> None:
        """追加一条消息。"""
        self._messages.append({"role": role, "content": content})
        self._trim()

    def get_history(self) -> List[dict]:
        """返回对话历史副本。"""
        return list(self._messages)

    def set_history(self, messages: List[dict] | None) -> None:
        """替换对话历史。"""
        self._messages = list(messages or [])
        self._trim()

    def clear(self) -> None:
        """清空对话历史。"""
        self._messages.clear()

    def _trim(self) -> None:
        """超出上限时，截掉最早的消息。"""
        while len(self._messages) > self.max_messages:
            self._messages.pop(0)
