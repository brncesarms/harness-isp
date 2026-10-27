"""Session and State Manager for HarnessISP.

Tracks multi-turn conversations, ball status states, and active diagnostic contexts.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class BallState(str, Enum):
    IDLE_OK = "idle_ok"            # Green / Cyan - Stable
    PROCESSING = "processing"      # Pulsing Yellow - Executing/Streaming
    ALERT = "alert"                # Red / Orange - Packet loss, high risk lockout


class ChatMessage(BaseModel):
    role: str                      # "user", "assistant", "system"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    risk_level: str | None = None  # "LOW", "MEDIUM", "CRITICAL"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionManager:
    """Maintains active conversation history and system status."""

    def __init__(self) -> None:
        self.ball_state: BallState = BallState.IDLE_OK
        self.history: list[ChatMessage] = []
        self._add_system_intro()

    def _add_system_intro(self) -> None:
        self.history.append(
            ChatMessage(
                role="system",
                content=(
                    "HarnessISP inicializado. Motor Antigravity pronto para diagnósticos de ISP "
                    "(MikroTik, Huawei, Cisco, Datacom, OLTs e Linux Fail-Safe ativado)."
                ),
            )
        )

    def add_user_message(self, content: str) -> ChatMessage:
        msg = ChatMessage(role="user", content=content)
        self.history.append(msg)
        self.set_state(BallState.PROCESSING)
        return msg

    def add_assistant_message(
        self, content: str, risk_level: str | None = None, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        msg = ChatMessage(
            role="assistant",
            content=content,
            risk_level=risk_level,
            metadata=metadata or {},
        )
        self.history.append(msg)
        if risk_level == "CRITICAL":
            self.set_state(BallState.ALERT)
        else:
            self.set_state(BallState.IDLE_OK)
        return msg

    def set_state(self, state: BallState) -> None:
        self.ball_state = state

    def clear(self) -> None:
        self.history.clear()
        self._add_system_intro()
        self.set_state(BallState.IDLE_OK)
