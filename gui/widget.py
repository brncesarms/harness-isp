"""Floating Desktop Companion Widget (Interactive Mascot & Dynamic Island) in PySide6.

Inspired by Louis-CFM/coucou:
1. Expressive Network Mascot with reactive eyes and dynamic status halo.
2. Drag-and-drop Context Dropping for network files (.rsc, .log, .csv, .txt).
3. Dynamic Island / Pill Mode toggle for unobtrusive live NOC telemetry.
"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import (
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
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
    """Coucou-inspired NOC companion with expressive facial animations, drag-and-drop, and dynamic island."""

    clicked = Signal()
    double_clicked = Signal()
    file_dropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        # Presentation Mode: 'ball' or 'pill'
        self.mode = "ball"

        # Dimensions
        self._ball_size = 80
        self._pill_width = 320
        self._pill_height = 46

        self.resize(self._ball_size + 24, self._ball_size + 24)

        # State and physics
        self.ball_state = BallState.IDLE_OK
        self.drag_position = QPoint()
        self.is_dragging = False
        self.drag_velocity = QPoint()
        self.last_mouse_pos = QPoint()
        self.is_drag_hovered = False

        # Mascot Facial Animation State
        self.blink_state = 0.0  # 0.0 = fully open, 1.0 = fully closed
        self.eye_look_x = 0.0   # -1.0 to 1.0
        self.eye_look_y = 0.0   # -1.0 to 1.0
        self.scan_phase = 0.0

        # Telemetry Text for Pill Mode
        self.telemetry_summary = "🟢 BGP: 4 Up  |  ⚡ 12ms  |  📶 -19.4 dBm"

        # Idle float animation (~30 FPS)
        self.idle_angle = 0.0
        self.pulse_phase = 0.0
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._update_idle)
        self.idle_timer.start(33)

        # Periodic Blink Timer
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start(3500)

    def set_ball_state(self, state: BallState) -> None:
        """Update visual state colors and eyes."""
        self.ball_state = state
        self.update()

    def set_telemetry(self, text: str) -> None:
        """Update live telemetry banner shown in Pill Mode."""
        self.telemetry_summary = text
        self.update()

    def toggle_mode(self) -> None:
        """Switch smoothly between Mascot Ball and Dynamic Island Pill."""
        if self.mode == "ball":
            self.mode = "pill"
            self.resize(self._pill_width, self._pill_height)
        else:
            self.mode = "ball"
            self.resize(self._ball_size + 24, self._ball_size + 24)
        self.update()

    def _trigger_blink(self) -> None:
        """Animate natural eye blinking."""
        if self.ball_state == BallState.ALERT:
            return  # In alert, eyes stay wide open
        self.blink_state = 1.0
        QTimer.singleShot(120, self._finish_blink)
        self.update()

    def _finish_blink(self) -> None:
        self.blink_state = 0.0
        self.update()

    def _update_idle(self) -> None:
        """Tick animations for floating, scanning and halos."""
        self.idle_angle = (self.idle_angle + 0.05) % (2 * math.pi)
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)

        if self.ball_state == BallState.PROCESSING:
            self.scan_phase = (self.scan_phase + 0.15) % (2 * math.pi)
            self.eye_look_x = math.sin(self.scan_phase) * 0.7
            self.eye_look_y = 0.0
        elif self.is_drag_hovered:
            self.eye_look_x = 0.0
            self.eye_look_y = -0.8  # Look up eagerly at the incoming dropped file
        else:
            # Subtle natural gaze
            self.eye_look_x = math.sin(self.idle_angle * 0.5) * 0.2
            self.eye_look_y = math.cos(self.idle_angle * 0.5) * 0.1

        self.update()

    # --- Drag & Drop Context Dropping ---
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.is_drag_hovered = True
            self.update()

    def dragLeaveEvent(self, event) -> None:
        self.is_drag_hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent) -> None:
        self.is_drag_hovered = False
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.file_dropped.emit(str(Path(path).resolve()))
        self.update()
        event.acceptProposedAction()

    # --- Mouse Events ---
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
            self.move(current_pos - self.drag_position)
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_velocity = QPoint(0, 0)
            delta = (event.globalPosition().toPoint() - (self.pos() + self.drag_position)).manhattanLength()
            if delta < 10:
                self.clicked.emit()
            self.update()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle_mode()
            self.double_clicked.emit()
            event.accept()

    # --- Paint Engine ---
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.mode == "ball":
            self._paint_ball_mascot(painter)
        else:
            self._paint_dynamic_island(painter)

    def _paint_ball_mascot(self, painter: QPainter) -> None:
        center_x = self.width() / 2.0
        idle_y = math.sin(self.idle_angle) * 2.0
        center_y = (self.height() / 2.0) + idle_y
        radius = (self._ball_size / 2.0)

        # Elastic distortion on drag
        stretch_x = min(14.0, abs(self.drag_velocity.x()) * 0.4) if self.is_dragging else 0.0
        stretch_y = min(14.0, abs(self.drag_velocity.y()) * 0.4) if self.is_dragging else 0.0
        rx = radius + stretch_x
        ry = radius + stretch_y

        # Colors by State
        if self.ball_state == BallState.IDLE_OK:
            halo_color = QColor(6, 182, 212, 170) if not self.is_drag_hovered else QColor(56, 189, 248, 240)
            core_top = QColor(14, 165, 233)
            core_bottom = QColor(3, 105, 161)
        elif self.ball_state == BallState.PROCESSING:
            pulse = int(120 + 80 * math.sin(self.pulse_phase))
            halo_color = QColor(234, 179, 8, pulse)
            core_top = QColor(250, 204, 21)
            core_bottom = QColor(161, 98, 7)
        else:  # ALERT
            pulse = int(140 + 100 * math.sin(self.pulse_phase))
            halo_color = QColor(239, 68, 68, pulse)
            core_top = QColor(248, 113, 113)
            core_bottom = QColor(185, 28, 28)

        # 1. Outer Glow / Halo
        glow_grad = QRadialGradient(center_x, center_y, max(rx, ry) + 9)
        glow_grad.setColorAt(0.7, halo_color)
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(rx + 7), int(ry + 7))

        # 2. Main Sphere Body
        core_grad = QLinearGradient(center_x - rx, center_y - ry, center_x + rx, center_y + ry)
        core_grad.setColorAt(0.0, core_top)
        core_grad.setColorAt(1.0, core_bottom)
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(halo_color, 1.5))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(rx), int(ry))

        # 3. Inner Specular Highlight (Coucou glossy shine)
        highlight_grad = QLinearGradient(center_x, center_y - ry + 4, center_x, center_y)
        highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 190))
        highlight_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPoint(int(center_x), int(center_y - ry * 0.45)),
            int(rx * 0.45),
            int(ry * 0.22),
        )

        # 4. Expressive Mascot Eyes (Coucou Mochi Style)
        eye_y = center_y - 2
        eye_spacing = rx * 0.38
        eye_w = 7.0
        eye_h = 10.0 if self.ball_state != BallState.ALERT else 13.0

        for eye_x in (center_x - eye_spacing, center_x + eye_spacing):
            if self.blink_state > 0.5:
                # Blinked eye: a cute curved line
                painter.setPen(QPen(QColor(15, 23, 42), 2.0))
                painter.drawLine(int(eye_x - 4), int(eye_y), int(eye_x + 4), int(eye_y))
            else:
                # Sclera / Eye Capsule
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(
                    QPoint(int(eye_x), int(eye_y)),
                    int(eye_w),
                    int(eye_h),
                )

                # Pupil (Moves with gaze)
                pupil_offset_x = self.eye_look_x * 2.5
                pupil_offset_y = self.eye_look_y * 2.5
                pupil_x = eye_x + pupil_offset_x
                pupil_y = eye_y + pupil_offset_y

                pupil_color = QColor(15, 23, 42)
                painter.setBrush(QBrush(pupil_color))
                painter.drawEllipse(QPoint(int(pupil_x), int(pupil_y)), 3, 4)

                # Pupil catchlight (Sparkle)
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QPoint(int(pupil_x - 1), int(pupil_y - 1)), 1, 1)

    def _paint_dynamic_island(self, painter: QPainter) -> None:
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Background Pill Shape
        pill_grad = QLinearGradient(0, 0, self.width(), 0)
        pill_grad.setColorAt(0.0, QColor(15, 23, 42, 245))
        pill_grad.setColorAt(1.0, QColor(11, 14, 20, 245))

        border_color = QColor(6, 182, 212) if self.ball_state == BallState.IDLE_OK else QColor(239, 68, 68)
        painter.setBrush(QBrush(pill_grad))
        painter.setPen(QPen(border_color, 1.5))
        painter.drawRoundedRect(rect, 20, 20)

        # Mini Mascot Avatar on the Left
        mini_cx = 24
        mini_cy = self.height() / 2.0
        mini_r = 12

        avatar_grad = QLinearGradient(mini_cx - mini_r, mini_cy - mini_r, mini_cx + mini_r, mini_cy + mini_r)
        avatar_grad.setColorAt(0.0, QColor(14, 165, 233))
        avatar_grad.setColorAt(1.0, QColor(3, 105, 161))
        painter.setBrush(QBrush(avatar_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(mini_cx), int(mini_cy)), mini_r, mini_r)

        # Mini Eye Dots
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPoint(int(mini_cx - 3), int(mini_cy)), 2, 3)
        painter.drawEllipse(QPoint(int(mini_cx + 3), int(mini_cy)), 2, 3)

        # Live NOC Telemetry Text
        painter.setPen(QColor(226, 232, 240))
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRect(44, 0, self.width() - 50, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            self.telemetry_summary,
        )
