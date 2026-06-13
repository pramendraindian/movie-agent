"""In-memory conversation context for multi-turn agentic movie chat."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    last_intent: str = ""
    last_movies: list[dict] = field(default_factory=list)
    last_query: str = ""
    last_entities: dict[str, Any] = field(default_factory=dict)

    def add_turn(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]

    def history_text(self, max_turns: int = 6) -> str:
        recent = self.messages[-max_turns:]
        return "\n".join(f"{m['role']}: {m['content']}" for m in recent)


class ContextManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def get_or_create(self, session_id: str | None = None) -> SessionContext:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        new_id = session_id or str(uuid.uuid4())
        ctx = SessionContext(session_id=new_id)
        self._sessions[new_id] = ctx
        return ctx

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
