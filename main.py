"""Main entrypoint for HarnessISP Desktop Application.

Initializes storage, session manager, GUI widget and tray.
"""

from __future__ import annotations

import asyncio
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.cli_bridge import AntigravityCLIBridge
from core.failsafe_guard import FailsafeGuard
from core.memory_rag import MemoryRAG
from core.net_tools import NetTools
from core.session import BallState, SessionManager
from core.storage import StorageManager
from core.vault import VaultManager
from gui.chat_panel import ChatPanel
from gui.tray import TrayManager
from gui.widget import FloatingBallWidget


class HarnessISPApp:
    """Orchestrates HarnessISP components."""

    def __init__(self) -> None:
        # 1. Core Services
        self.storage = StorageManager()
        self.storage.initialize()

        self.vault = VaultManager(self.storage.vault_dir)
        self.memory = MemoryRAG(self.storage.memory_dir / "knowledge.db")
        self.session = SessionManager()
        self.cli_bridge = AntigravityCLIBridge()

        # 2. GUI Components
        self.ball = FloatingBallWidget()
        self.chat = ChatPanel(self.session)
        self.tray = TrayManager(
            parent=self.ball,
            on_toggle_visible=self.toggle_ball,
            on_quit=self.quit,
        )

        # 3. Signals & Wiring
        self.ball.clicked.connect(self.toggle_chat)
        self.chat.action_triggered.connect(self.handle_action)

        # Position widget initially on screen
        self.ball.move(100, 100)
        self.ball.show()

    def toggle_ball(self) -> None:
        """Toggle sphere visibility."""
        if self.ball.isVisible():
            self.ball.hide()
            self.chat.hide()
        else:
            self.ball.show()

    def toggle_chat(self) -> None:
        """Toggle chat panel beside the ball."""
        if self.chat.isVisible():
            self.chat.hide()
        else:
            # Place chat window next to the sphere
            ball_pos = self.ball.pos()
            self.chat.move(ball_pos.x() + self.ball.width() + 10, ball_pos.y())
            self.chat.show()
            self.chat.raise_()

    def handle_action(self, text: str) -> None:
        """Process incoming user prompt or NOC quick action."""
        # 1. Audit for lockout risks first (Pre-flight check)
        risk = FailsafeGuard.audit_mikrotik_script(text)
        risk_level = risk.level if risk.level != "LOW" else None

        self.session.add_user_message(text)
        self.chat.append_message("user", text)
        self.ball.set_ball_state(BallState.PROCESSING)

        # 2. Asynchronous execution simulation/query
        QTimer.singleShot(500, lambda: self._complete_action(text, risk_level))

    def _complete_action(self, text: str, risk_level: str | None) -> None:
        # Generate response using local ISP rules or Antigravity CLI
        response = self.cli_bridge._generate_local_isp_response(text)
        self.session.add_assistant_message(response, risk_level=risk_level)
        self.chat.append_message("assistant", response, risk=risk_level)
        self.ball.set_ball_state(BallState.ALERT if risk_level == "CRITICAL" else BallState.IDLE_OK)

    def quit(self) -> None:
        QApplication.instance().quit()


def main() -> None:
    # Linux Wayland/X11 safety
    if "WAYLAND_DISPLAY" in os.environ and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("HarnessISP")
    app.setQuitOnLastWindowClosed(False)

    harness = HarnessISPApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
