"""NOC Chat Panel with Quick Action Buttons and Risk Diff Display."""

from __future__ import annotations

import re
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.session import SessionManager
from gui.styles import NOC_STYLESHEET


def _format_markdown_to_html(text: str) -> str:
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code style='background-color:#1e293b;color:#f8fafc;padding:2px 4px;border-radius:3px;font-family:monospace;'>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*([^\*]+)\*\*", r"<b>\1</b>", text)
    # Line breaks
    text = text.replace(chr(10), "<br>")
    return text


class ChatPanel(QWidget):
    """Side panel displaying NOC chat history and quick action buttons."""

    action_triggered = Signal(str)

    def __init__(self, session: SessionManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setStyleSheet(NOC_STYLESHEET)
        self.setWindowTitle("HarnessISP - Painel NOC")
        self.resize(500, 620)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with Risk / Safe Mode Indicator
        header_layout = QHBoxLayout()
        title_label = QLabel("⚡ <b>HarnessISP NOC Core</b>")
        self.safe_badge = QLabel("🛡️ Safe Mode Ativo")
        self.safe_badge.setObjectName("risk_low")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.safe_badge)
        layout.addLayout(header_layout)

        # Quick Action NOC Buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)

        actions = [
            ("🔍 MTR / Ping", "ping 8.8.8.8"),
            ("🌐 BGP / ASN", "consultar bgp asn"),
            ("📶 Sinal OLT", "diagnosticar sinal optico olt"),
            ("🛡️ Bogon / DDoS", "gerar regras bogon anti-ddos"),
        ]

        for label, cmd in actions:
            btn = QPushButton(label)
            btn.setObjectName("action_btn")
            btn.clicked.connect(lambda checked=False, c=cmd: self.action_triggered.emit(c))
            quick_layout.addWidget(btn)

        layout.addLayout(quick_layout)

        # Chat / Log Display Area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Pergunte ao assistente, cole saídas de CLI ou comandos...")
        self.input_field.returnPressed.connect(self._handle_send)

        send_btn = QPushButton("Enviar")
        send_btn.clicked.connect(self._handle_send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

        self.refresh_display()

    def _handle_send(self) -> None:
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.action_triggered.emit(text)

    def append_message(self, role: str, content: str, risk: str | None = None) -> None:
        color = "#38bdf8" if role == "user" else "#34d399"
        header = f"<b style='color:{color};'>[{role.upper()}]</b>"
        if risk == "CRITICAL":
            header += " <span style='background:#7f1d1d;color:#fca5a5;padding:2px 4px;border-radius:3px;'>⚠️ RISCO CRÍTICO DE LOCKOUT</span>"

        formatted = _format_markdown_to_html(content)
        self.chat_display.append(f"{header}<br>{formatted}<br>")

        # Auto-scroll to bottom
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def refresh_display(self) -> None:
        self.chat_display.clear()
        for msg in self.session.history:
            self.append_message(msg.role, msg.content, msg.risk_level)
