"""Floating Desktop Widget (Interactive Sphere) in PySide6.

Implements spring-bounce physics, elastic drag deformation, idle hover animation,
and dynamic LED status halo.
"""

from __future__ import annotations

import math
from typing import Callable

from PySide6.QtCore import (
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    QTimeLine,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from core.session import BallState


class FloatingBallWidget(QWidget):
    """Floating desktop sphere with elastic drag and state-reactive halo."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._size = 80
        self.resize(self._size + 20, self._size + 20)

        # State and physics
        self.ball_state = BallState.IDLE_OK
        self.drag_position = QPoint()
        self.is_dragging = False
        self.drag_velocity = QPoint()
        self.last_mouse_pos = QPoint()

        # Idle float animation
        self.idle_angle = 0.0
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._update_idle)
        self.idle_timer.start(33)  # ~30 FPS

        # Pulse animation for processing/alert
        self.pulse_phase = 0.0

    def set_ball_state(self, state: BallState) -> None:
        """Update visual state colors."""
        self.ball_state = state
        self.update()

    def _update_idle(self) -> None:
        """Subtle hover vibration and halo pulse."""
        self.idle_angle = (self.idle_angle + 0.05) % (2 * math.pi)
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.last_mouse_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.last_mouse_pos
            self.drag_velocity = delta
            self.last_mouse_pos = current_pos

            # Move window
            self.move(current_pos - self.drag_position)
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            was_dragging = self.is_dragging
            self.is_dragging = False
            self.drag_velocity = QPoint(0, 0)

            # Detect click (no major displacement)
            delta = (event.globalPosition().toPoint() - (self.pos() + self.drag_position)).manhattanLength()
            if delta < 10:
                self.clicked.emit()

            self.update()
            event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2.0
        # Subtle idle bobbing: +/- 2 pixels
        idle_y = math.sin(self.idle_angle) * 2.0
        center_y = (self.height() / 2.0) + idle_y

        radius = (self._size / 2.0)

        # Elastic distortion during drag
        stretch_x = 0.0
        stretch_y = 0.0
        if self.is_dragging:
            stretch_x = min(15.0, abs(self.drag_velocity.x()) * 0.4)
            stretch_y = min(15.0, abs(self.drag_velocity.y()) * 0.4)

        rx = radius + stretch_x
        ry = radius + stretch_y

        # Halo color based on state
        if self.ball_state == BallState.IDLE_OK:
            halo_color = QColor(6, 182, 212, 160)     # Neon Cyan
            core_top = QColor(14, 165, 233)
            core_bottom = QColor(3, 105, 161)
        elif self.ball_state == BallState.PROCESSING:
            pulse = int(100 + 80 * math.sin(self.pulse_phase))
            halo_color = QColor(234, 179, 8, pulse)    # Pulsing Yellow
            core_top = QColor(250, 204, 21)
            core_bottom = QColor(161, 98, 7)
        else:  # ALERT
            pulse = int(120 + 100 * math.sin(self.pulse_phase))
            halo_color = QColor(239, 68, 68, pulse)    # Alert Red
            core_top = QColor(248, 113, 113)
            core_bottom = QColor(185, 28, 28)

        # 1. Outer Glow / Halo
        glow_grad = QRadialGradient(center_x, center_y, max(rx, ry) + 8)
        glow_grad.setColorAt(0.7, halo_color)
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(rx + 6), int(ry + 6))

        # 2. Main Sphere with 3D gradient
        core_grad = QLinearGradient(center_x - rx, center_y - ry, center_x + rx, center_y + ry)
        core_grad.setColorAt(0.0, core_top)
        core_grad.setColorAt(1.0, core_bottom)
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(halo_color, 1.5))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(rx), int(ry))

        # 3. Inner Specular Highlight (Light reflection)
        highlight_grad = QLinearGradient(center_x, center_y - ry + 4, center_x, center_y)
        highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        highlight_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPoint(int(center_x), int(center_y - ry * 0.4)),
            int(rx * 0.5),
            int(ry * 0.25),
        )
