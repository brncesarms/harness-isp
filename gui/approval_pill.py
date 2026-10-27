"""Coucou-inspired Quick Approval Pill for High-Risk Network Commands.

Presents an unobtrusive floating approval pill directly beneath or attached to
the desktop companion, allowing 1-click authorization with Safe-Mode, Force,
or Abort options.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ApprovalPillWidget(QWidget):
    """Floating dynamic pill for instant HITL approval of network commands."""

    # action: 'safe_mode' | 'force' | 'abort'
    action_decided = Signal(str, str)  # action, command

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.current_command = ""

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)

        # Rounded Container Frame
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.95);
                border: 2px solid #ef4444;
                border-radius: 12px;
            }
        """)
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 10, 12, 10)
        frame_layout.setSpacing(8)

        # Header with Risk Tag
        header_layout = QHBoxLayout()
        self.title_label = QLabel("⚠️ <b>AUTORIZAÇÃO PRÉ-FLIGHT DE COMANDO</b>")
        self.title_label.setStyleSheet("color: #f87171; font-size: 11px;")

        self.risk_tag = QLabel("RISCO CRÍTICO")
        self.risk_tag.setStyleSheet("""
            background-color: #7f1d1d;
            color: #fca5a5;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.risk_tag)
        frame_layout.addLayout(header_layout)

        # Command Preview Snippet
        self.cmd_label = QLabel("")
        self.cmd_label.setStyleSheet("""
            background-color: #0b0e14;
            color: #38bdf8;
            padding: 6px 10px;
            border-radius: 6px;
            font-family: 'Fira Code', 'JetBrains Mono', monospace;
            font-size: 11px;
        """)
        self.cmd_label.setWordWrap(True)
        frame_layout.addWidget(self.cmd_label)

        # Risk Description
        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.desc_label.setWordWrap(True)
        frame_layout.addWidget(self.desc_label)

        # Action Buttons (Coucou Style: Safe Mode / Force / Abort)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_safe = QPushButton("🛡️ Safe-Mode (Enter)")
        self.btn_safe.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                color: #a7f3d0;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #047857;
                color: #ffffff;
            }
        """)
        self.btn_safe.clicked.connect(lambda: self._choose("safe_mode"))

        self.btn_force = QPushButton("⚡ Forçar")
        self.btn_force.setStyleSheet("""
            QPushButton {
                background-color: #78350f;
                color: #fde68a;
                border: 1px solid #f59e0b;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #b45309;
                color: #ffffff;
            }
        """)
        self.btn_force.clicked.connect(lambda: self._choose("force"))

        self.btn_abort = QPushButton("❌ Abortar (Esc)")
        self.btn_abort.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.btn_abort.clicked.connect(lambda: self._choose("abort"))

        btn_layout.addWidget(self.btn_safe)
        btn_layout.addWidget(self.btn_force)
        btn_layout.addWidget(self.btn_abort)
        frame_layout.addLayout(btn_layout)

        outer_layout.addWidget(self.frame)
        self.setFixedWidth(380)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key_Return), self, lambda: self._choose("safe_mode"))
        QShortcut(QKeySequence(Qt.Key_Enter), self, lambda: self._choose("safe_mode"))
        QShortcut(QKeySequence(Qt.Key_Escape), self, lambda: self._choose("abort"))

    def prompt(
        self,
        command: str,
        risk_level: str,
        reason: str,
        anchor_pos: QPoint | None = None,
    ) -> None:
        """Display the pill configured for the given command and risk."""
        self.current_command = command
        display_cmd = command if len(command) <= 55 else command[:52] + "..."
        self.cmd_label.setText(display_cmd)
        self.desc_label.setText(reason)

        if risk_level.upper() == "CRITICAL":
            tag_text = "RISCO CRÍTICO"
        elif risk_level.upper() == "MEDIUM":
            tag_text = "RISCO MÉDIO"
        else:
            tag_text = f"RISCO {risk_level.upper()}"
        self.risk_tag.setText(tag_text)

        if risk_level.upper() == "CRITICAL":
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.96);
                    border: 2px solid #ef4444;
                    border-radius: 12px;
                }
            """)
        else:
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.96);
                    border: 2px solid #f59e0b;
                    border-radius: 12px;
                }
            """)

        if anchor_pos:
            self.move(anchor_pos.x() - 140, anchor_pos.y() + 85)

        self.show()
        self.raise_()

    def _choose(self, action: str) -> None:
        cmd = self.current_command
        self.hide()
        self.action_decided.emit(action, cmd)
