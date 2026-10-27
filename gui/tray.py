"""System Tray Icon for HarnessISP."""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayManager:
    """Manages the system tray icon and context actions."""

    def __init__(
        self,
        parent: QWidget,
        on_toggle_visible: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.parent = parent
        self.on_toggle_visible = on_toggle_visible
        self.on_quit = on_quit

        self.tray = QSystemTrayIcon(self._generate_icon(), parent)
        self._init_menu()
        self.tray.show()

    def _generate_icon(self) -> QIcon:
        """Draw a minimal programmatic icon if no asset is available."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(6, 182, 212))
        painter.setPen(QColor(14, 165, 233))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()

        return QIcon(pixmap)

    def _init_menu(self) -> None:
        menu = QMenu(self.parent)

        toggle_action = QAction("Exibir/Ocultar Assistente", self.parent)
        toggle_action.triggered.connect(self.on_toggle_visible)
        menu.addAction(toggle_action)

        menu.addSeparator()

        quit_action = QAction("Sair do HarnessISP", self.parent)
        quit_action.triggered.connect(self.on_quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.on_toggle_visible()
