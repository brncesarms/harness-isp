"""Floating Desktop Sentinela Widget (NOC HUD & Dynamic Island) in PySide6.

Professional sentry HUD designed specifically for ISP network operations centers (NOC)
and telecom engineers. Provides live network status, anti-lockout feedback,
and instant script/log pre-flight auditing via drag & drop.
"""

from __future__ import annotations

import math
from pathlib import Path
import time

from PySide6.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from core.session import BallState


class FloatingBallWidget(QWidget):
    """Professional NOC Sentinela HUD with Compact Radar Badge and Dynamic Island modes."""

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
        self.setMouseTracking(True)

        # Presentation Mode: 'ball' (Compact Sentinela Badge) or 'pill' (Dynamic Island)
        self.mode = "ball"

        # Dimensions
        self._ball_size = 84
        self._pill_width = 340
        self._pill_height = 46

        self.resize(self._ball_size + 20, self._ball_size + 20)

        # State and Positioning
        self.ball_state = BallState.IDLE_OK
        self.drag_position = QPoint()
        self.is_dragging = False
        self.last_mouse_pos = QPoint()
        self.is_drag_hovered = False

        # NOC Telemetry & Pulse Animation
        self.pulse_phase = 0.0
        self.telemetry_summary = "🟢 BGP: 4 Up  |  ⚡ 12ms  |  📶 -19.4 dBm"

        # Animation Loop (~30 FPS)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._tick_animations)
        self.animation_timer.start(33)

    # --- Public API ---

    def set_ball_state(self, state: BallState) -> None:
        """Update operational state and refresh HUD visual indicators."""
        self.ball_state = state
        self.update()

    def set_telemetry(self, text: str) -> None:
        """Update live telemetry banner shown in Dynamic Island mode."""
        self.telemetry_summary = text
        self.update()

    def toggle_mode(self) -> None:
        """Switch between Compact Sentinela Badge and Dynamic Island Telemetry Bar."""
        if self.mode == "ball":
            self.mode = "pill"
            self.resize(self._pill_width, self._pill_height)
        else:
            self.mode = "ball"
            self.resize(self._ball_size + 20, self._ball_size + 20)
        self.update()

    # --- Internal Animation ---

    def _tick_animations(self) -> None:
        self.pulse_phase = (self.pulse_phase + 0.08) % (2.0 * math.pi)
        self.update()

    # --- Mouse & Drag Interactivity ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.last_mouse_pos = event.globalPosition().toPoint()
            self.is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.last_mouse_pos
            if delta.manhattanLength() > 4:
                self.is_dragging = True
            if self.is_dragging:
                new_pos = current_pos - self.drag_position
                self._clamp_to_screen(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                self.clicked.emit()
            self.is_dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle_mode()
            self.double_clicked.emit()
            event.accept()

    def _clamp_to_screen(self, pos: QPoint) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.left(), min(pos.x(), geom.right() - self.width()))
            y = max(geom.top(), min(pos.y(), geom.bottom() - self.height()))
            self.move(x, y)
        else:
            self.move(pos)

    # --- Context Dropping (File Drop Ingestion) ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.is_drag_hovered = True
            self.update()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.is_drag_hovered = False
        self.update()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self.is_drag_hovered = False
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                file_path = url.toLocalFile()
                if file_path:
                    self.file_dropped.emit(file_path)
                    break
            event.acceptProposedAction()
        self.update()

    # --- Painting Engine ---

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.mode == "ball":
            self._paint_sentinela_badge(painter)
        else:
            self._paint_dynamic_island(painter)

    def _get_status_colors(self) -> tuple[QColor, QColor, QColor]:
        """Returns (primary_color, glow_color, bg_accent)."""
        if self.ball_state == BallState.ALERT:
            return (
                QColor(239, 68, 68),       # Crimson
                QColor(239, 68, 68, 90),
                QColor(127, 29, 29, 140),
            )
        elif self.ball_state == BallState.PROCESSING:
            return (
                QColor(6, 182, 212),       # Cyan
                QColor(6, 182, 212, 90),
                QColor(14, 116, 144, 140),
            )
        else:
            return (
                QColor(16, 185, 129),      # Emerald
                QColor(16, 185, 129, 80),
                QColor(6, 78, 59, 140),
            )

    def _paint_sentinela_badge(self, painter: QPainter) -> None:
        """Render high-tech circular NOC Sentinela Radar Badge."""
        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0
        r = float(self._ball_size) / 2.0

        primary_col, glow_col, bg_accent = self._get_status_colors()

        if self.is_drag_hovered:
            primary_col = QColor(56, 189, 248)  # Sky blue highlight on drag hover
            glow_col = QColor(56, 189, 248, 140)

        # 1. Outer Status Breathing Glow
        pulse_alpha = int(40 + 25 * math.sin(self.pulse_phase))
        outer_glow_color = QColor(glow_col.red(), glow_col.green(), glow_col.blue(), pulse_alpha)
        painter.setBrush(QBrush(outer_glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r + 7.0, r + 7.0)

        # 2. Main Dark-Glass Disc
        bg_grad = QRadialGradient(cx, cy - r * 0.3, r * 1.2)
        bg_grad.setColorAt(0.0, QColor(24, 32, 47, 248))
        bg_grad.setColorAt(0.7, QColor(15, 20, 31, 252))
        bg_grad.setColorAt(1.0, QColor(10, 14, 23, 255))
        painter.setBrush(QBrush(bg_grad))

        # Border Pen with Pulse
        border_width = 2.4 if self.is_drag_hovered else 1.8
        painter.setPen(QPen(primary_col, border_width))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # 3. Subtle Inner Radar Rings
        radar_pen = QPen(QColor(51, 65, 85, 70), 1.0, Qt.DotLine)
        painter.setPen(radar_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r * 0.65, r * 0.65)
        painter.drawEllipse(QPointF(cx, cy), r * 0.35, r * 0.35)

        # Crosshairs / Axis marks
        cross_pen = QPen(QColor(51, 65, 85, 50), 1.0)
        painter.setPen(cross_pen)
        painter.drawLine(QPointF(cx - r * 0.85, cy), QPointF(cx + r * 0.85, cy))
        painter.drawLine(QPointF(cx, cy - r * 0.85), QPointF(cx, cy + r * 0.85))

        # 4. Center ISP Network Nodes Graphic
        if self.is_drag_hovered:
            # Drop Prompt
            painter.setPen(QColor(56, 189, 248))
            font = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(cx - r, cy - 14, r * 2, 28),
                Qt.AlignCenter,
                "DROP\n.RSC",
            )
        else:
            self._paint_network_nodes(painter, cx, cy, primary_col)

        # 5. Top-Right Status Badge Pill / Indicator
        badge_cx = cx + r * 0.70
        badge_cy = cy - r * 0.70
        painter.setBrush(QBrush(primary_col))
        painter.setPen(QPen(QColor(15, 23, 42), 1.5))

        if self.ball_state == BallState.ALERT:
            # Red Alert Indicator (!)
            painter.drawEllipse(QPointF(badge_cx, badge_cy), 8.0, 8.0)
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Segoe UI", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(badge_cx - 8, badge_cy - 8, 16, 16),
                Qt.AlignCenter,
                "!",
            )
        elif self.ball_state == BallState.PROCESSING:
            # Sync pulse dot
            p_r = 6.0 + 1.5 * math.sin(self.pulse_phase * 2.0)
            painter.drawEllipse(QPointF(badge_cx, badge_cy), p_r, p_r)
        else:
            # Green steady dot
            painter.drawEllipse(QPointF(badge_cx, badge_cy), 5.5, 5.5)

    def _paint_network_nodes(self, painter: QPainter, cx: float, cy: float, accent: QColor) -> None:
        """Render clean, sharp telecom network topology glyph in center."""
        painter.save()

        # Nodes positions (Central Router + 3 Edge Nodes)
        center_pt = QPointF(cx, cy)
        p1 = QPointF(cx, cy - 16.0)
        p2 = QPointF(cx - 14.0, cy + 10.0)
        p3 = QPointF(cx + 14.0, cy + 10.0)

        # Links (interconnection lines)
        link_pen = QPen(QColor(100, 116, 139, 190), 1.8)
        painter.setPen(link_pen)
        painter.drawLine(center_pt, p1)
        painter.drawLine(center_pt, p2)
        painter.drawLine(center_pt, p3)

        # Peripheral Nodes
        painter.setPen(QPen(accent, 1.2))
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        for pt in (p1, p2, p3):
            painter.drawEllipse(pt, 4.0, 4.0)

        # Center Master Node (Core Router with accent glow)
        painter.setBrush(QBrush(accent))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2))
        painter.drawEllipse(center_pt, 6.0, 6.0)

        painter.restore()

    def _paint_dynamic_island(self, painter: QPainter) -> None:
        """Render horizontal dark-glass dynamic island telemetry bar."""
        rect = self.rect().adjusted(2, 2, -2, -2)

        primary_col, glow_col, _ = self._get_status_colors()

        # Background Pill
        pill_grad = QLinearGradient(0, 0, self.width(), 0)
        pill_grad.setColorAt(0.0, QColor(15, 23, 42, 248))
        pill_grad.setColorAt(1.0, QColor(11, 14, 20, 248))

        painter.setBrush(QBrush(pill_grad))
        border_width = 2.0 if self.is_drag_hovered else 1.4
        border_col = QColor(56, 189, 248) if self.is_drag_hovered else primary_col
        painter.setPen(QPen(border_col, border_width))
        painter.drawRoundedRect(rect, 22, 22)

        # Left NOC Status Beacon
        beacon_cx = 24.0
        beacon_cy = self.height() / 2.0
        beacon_r = 7.0 + (1.2 * math.sin(self.pulse_phase) if self.ball_state != BallState.IDLE_OK else 0.0)

        painter.setBrush(QBrush(primary_col))
        painter.setPen(QPen(QColor(15, 23, 42), 1.5))
        painter.drawEllipse(QPointF(beacon_cx, beacon_cy), beacon_r, beacon_r)

        # Center Content: Live Telemetry or Drop Notification
        painter.setPen(QColor(226, 232, 240))
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)

        text_to_show = (
            "📥 Solte o arquivo (.rsc / .log) para auditoria pré-flight"
            if self.is_drag_hovered
            else self.telemetry_summary
        )

        painter.drawText(
            QRect(44, 0, self.width() - 50, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            text_to_show,
        )
