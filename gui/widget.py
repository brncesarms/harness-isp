"""Floating Desktop Companion Widget (Coucou-Inspired Mascot & Dynamic Island) in PySide6.

Faithfully inspired by Louis-CFM/coucou:
1. Mochi Anatomical Superellipse: Soft squircle body with pearl-matte gradient and reactive NOC state tints.
2. Expressive Eye Engine: Reactive pill eyes, natural cursor gaze tracking, blinking, and dynamic expressions:
   - PILL: Classical attentive companion tracking the user's cursor across screens.
   - HAPPY: Joyous curved arcs (^ ^) upon completing tasks or being petted.
   - WIDE: Wide-open pupils during network alerts or surprises.
   - SPIRAL: Dizzy spinning eyes when rapidly poked.
   - CLOSED: Gentle sleeping eyes when idle for extended periods.
3. Interactive Mechanics:
   - Poke & Dizzy: Playful squash response on click; becomes dizzy with spiral eyes if clicked repeatedly.
   - Context Dropping (Mailbox Slot Morph): Mouth slot opens when dragging network configs (.rsc, .log);
     swallows and chews happily on drop.
   - Happy Jump: Elastic celebration leap on task completion.
4. Dynamic Island Pill: Smooth toggle to horizontal dark-glass status HUD with mini-Mochi avatar.
"""

from __future__ import annotations

from enum import Enum
import math
from pathlib import Path
import time

from PySide6.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
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


class EyeShape(str, Enum):
    """Expressive eye forms inspired by Coucou's BotEngine."""
    PILL = "pill"
    HAPPY = "happy"
    WIDE = "wide"
    SPIRAL = "spiral"
    CLOSED = "closed"


def _build_mochi_path(cx: float, cy: float, rx: float, ry: float, n_points: int = 72) -> QPainterPath:
    """Build Coucou's signature superellipse (squircle) path with exponent ~2.0/2.7."""
    path = QPainterPath()
    exp_n = 2.0 / 2.7
    for i in range(n_points + 1):
        a = (i / n_points) * (2.0 * math.pi)
        ca = math.cos(a)
        sa = math.sin(a)
        px = rx * (math.pow(ca, exp_n) if ca >= 0 else -math.pow(-ca, exp_n))
        py = ry * (math.pow(sa, exp_n) if sa >= 0 else -math.pow(-sa, exp_n))
        pt = QPointF(cx + px, cy + py)
        if i == 0:
            path.moveTo(pt)
        else:
            path.lineTo(pt)
    path.closeSubpath()
    return path


class FloatingBallWidget(QWidget):
    """Living Coucou-inspired Mochi companion with expressive physics and dynamic island HUD."""

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

        # Presentation Mode: 'ball' (Coucou Mochi Mascot) or 'pill' (Dynamic Island)
        self.mode = "ball"

        # Dimensions: Coucou aspect ratio rx=1.14 * R, ry=0.88 * R
        self._ball_size = 90
        self._pill_width = 320
        self._pill_height = 48

        self.resize(self._ball_size + 36, self._ball_size + 36)

        # State and Physical Feedback
        self.ball_state = BallState.IDLE_OK
        self.drag_position = QPoint()
        self.is_dragging = False
        self.drag_velocity = QPoint()
        self.last_mouse_pos = QPoint()
        self.is_drag_hovered = False

        # Mascot Expressions & Facial Dynamics
        self.eye_shape_override: EyeShape | None = None
        self.blink_factor = 0.0      # 0.0 = open, 1.0 = fully shut
        self.eye_look_x = 0.0        # -1.0 to 1.0 (Cursor tracking gaze)
        self.eye_look_y = 0.0        # -1.0 to 1.0
        self.target_look_x = 0.0
        self.target_look_y = 0.0

        # Coucou Anatomy & Animations
        self.idle_angle = 0.0
        self.pulse_phase = 0.0
        self.spiral_phase = 0.0
        self.tilt_angle = 0.0
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.jump_offset_y = 0.0
        self.jump_velocity = 0.0
        self.blush_intensity = 0.4   # 0.0 to 1.0 (blush glow)
        self.slot_open = 0.0         # 0.0 to 1.0 (mailbox swallow morph)
        self.is_chewing = False
        self.chew_timer = 0.0

        # Poking and Dizzy State Machine
        self.poke_history: list[float] = []
        self.is_dizzy = False
        self.dizzy_until = 0.0

        # Sleep and Inactivity Tracking
        self.last_interaction_time = time.monotonic()
        self.is_sleeping = False
        self.sleep_timeout_seconds = 180.0

        # Telemetry Banner for Dynamic Island Pill
        self.telemetry_summary = "🟢 BGP: 4 Up  |  ⚡ 12ms  |  📶 -19.4 dBm"

        # Animation Loop (~30 FPS)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._tick_animations)
        self.animation_timer.start(33)

        # Periodic Blink Timer (natural cadence 3.5s - 5s)
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start(3800)

    # --- Public API & State Modifiers ---

    def set_ball_state(self, state: BallState) -> None:
        """Update visual state and reactive emotions."""
        old_state = self.ball_state
        self.ball_state = state
        self.last_interaction_time = time.monotonic()
        self.is_sleeping = False

        if state == BallState.ALERT:
            self.eye_shape_override = EyeShape.WIDE
            self.blush_intensity = 0.1
        elif state == BallState.IDLE_OK and old_state in (BallState.PROCESSING, BallState.ALERT):
            # Task finished: Celebrate with Coucou Happy Jump!
            self.happy_jump()
        elif state == BallState.PROCESSING:
            self.eye_shape_override = None
            self.blush_intensity = 0.5
        else:
            self.eye_shape_override = None

        self.update()

    def set_telemetry(self, text: str) -> None:
        """Update live telemetry banner shown in Dynamic Island mode."""
        self.telemetry_summary = text
        self.update()

    def toggle_mode(self) -> None:
        """Smoothly switch between Coucou Mascot Squircle and Dynamic Island Pill."""
        if self.mode == "ball":
            self.mode = "pill"
            self.resize(self._pill_width, self._pill_height)
        else:
            self.mode = "ball"
            self.resize(self._ball_size + 36, self._ball_size + 36)
        self.update()

    def happy_jump(self) -> None:
        """Coucou-signature happy jump with celebration eyes and blush."""
        self.jump_velocity = -7.5
        self.eye_shape_override = EyeShape.HAPPY
        self.blush_intensity = 0.95
        QTimer.singleShot(1600, self._reset_override)
        self.update()

    def _reset_override(self) -> None:
        if not self.is_dizzy and not self.is_chewing:
            self.eye_shape_override = None
        self.update()

    # --- Internal Animation Engine ---

    def _trigger_blink(self) -> None:
        """Natural eye blinking."""
        if self.ball_state == BallState.ALERT or self.is_sleeping or self.is_dizzy:
            return
        self.blink_factor = 1.0
        QTimer.singleShot(110, self._finish_blink)
        self.update()

    def _finish_blink(self) -> None:
        self.blink_factor = 0.0
        self.update()

    def _tick_animations(self) -> None:
        now = time.monotonic()

        # 1. Idle Breathing and Subtle Floating
        self.idle_angle = (self.idle_angle + 0.05) % (2.0 * math.pi)
        self.pulse_phase = (self.pulse_phase + 0.09) % (2.0 * math.pi)

        # 2. Dizzy Recovery Timer
        if self.is_dizzy:
            self.spiral_phase = (self.spiral_phase + 0.35) % (2.0 * math.pi)
            self.tilt_angle = math.sin(self.spiral_phase * 1.5) * 8.0
            if now > self.dizzy_until:
                self.is_dizzy = False
                self.tilt_angle = 0.0
                self.eye_shape_override = None
                self.blush_intensity = 0.4
        else:
            self.tilt_angle = 0.0

        # 3. Chew Animation (after swallowing network context)
        if self.is_chewing:
            self.chew_timer += 0.2
            self.squash_y = 1.0 + math.sin(self.chew_timer * 4.0) * 0.07
            self.squash_x = 1.0 - math.sin(self.chew_timer * 4.0) * 0.04
            if self.chew_timer >= 2.5:
                self.is_chewing = False
                self.squash_x = 1.0
                self.squash_y = 1.0
                self.eye_shape_override = None
                self.blush_intensity = 0.4

        # 4. Happy Jump Physics
        if abs(self.jump_velocity) > 0.1 or abs(self.jump_offset_y) > 0.1:
            self.jump_offset_y += self.jump_velocity
            self.jump_velocity += 0.8  # Gravity
            if self.jump_offset_y >= 0.0:
                self.jump_offset_y = 0.0
                self.jump_velocity = 0.0
                # Elastic landing squash
                self.squash_y = 0.92
                self.squash_x = 1.08

        # Smooth relaxation of squashes back to neutral
        self.squash_x += (1.0 - self.squash_x) * 0.15
        self.squash_y += (1.0 - self.squash_y) * 0.15

        # 5. Mailbox Slot Morph (Opens when file hovered)
        target_slot = 1.0 if self.is_drag_hovered else 0.0
        self.slot_open += (target_slot - self.slot_open) * 0.2

        # 6. Real-time Cursor Gaze Tracking (Coucou Gaze Engine)
        if not self.is_dizzy and not self.is_sleeping and not self.is_chewing:
            if self.is_drag_hovered:
                # Eagerly look up at the incoming dropped file
                self.target_look_x = 0.0
                self.target_look_y = -0.85
            elif self.ball_state == BallState.PROCESSING:
                # Thinking scan motion
                self.target_look_x = math.sin(self.idle_angle * 1.8) * 0.65
                self.target_look_y = 0.0
            else:
                # Track user's actual mouse cursor on screen
                try:
                    cursor_pos = QCursor.pos()
                    center_global = self.mapToGlobal(QPoint(int(self.width() / 2), int(self.height() / 2)))
                    dx = cursor_pos.x() - center_global.x()
                    dy = cursor_pos.y() - center_global.y()
                    self.target_look_x = math.tanh(dx / 260.0)
                    self.target_look_y = math.tanh(dy / 200.0)

                    # Reset sleep timer if user is actively moving mouse near Mochi
                    if math.hypot(dx, dy) < 300:
                        self.last_interaction_time = now
                        if self.is_sleeping:
                            self.is_sleeping = False
                            self.eye_shape_override = None
                            self.happy_jump()
                except Exception:
                    self.target_look_x = math.sin(self.idle_angle * 0.5) * 0.2
                    self.target_look_y = math.cos(self.idle_angle * 0.5) * 0.1

            # Smooth gaze interpolation (lerp)
            self.eye_look_x += (self.target_look_x - self.eye_look_x) * 0.22
            self.eye_look_y += (self.target_look_y - self.eye_look_y) * 0.22

        # 7. Inactivity Sleeping Check
        if not self.is_sleeping and not self.is_dizzy and self.ball_state == BallState.IDLE_OK:
            if (now - self.last_interaction_time) > self.sleep_timeout_seconds:
                self.is_sleeping = True
                self.eye_shape_override = EyeShape.CLOSED

        self.update()

    # --- Mouse & Interaction Handlers ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.last_interaction_time = time.monotonic()
            if self.is_sleeping:
                self.is_sleeping = False
                self.eye_shape_override = None

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
                self._handle_poke()
                self.clicked.emit()
            self.update()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle_mode()
            self.double_clicked.emit()
            event.accept()

    def _handle_poke(self) -> None:
        """Coucou signature poke reaction: Squash, blush, and dizzy if rapid."""
        now = time.monotonic()
        self.poke_history.append(now)
        self.poke_history = [t for t in self.poke_history if now - t < 1.4]

        # 3 rapid pokes -> Dizzy state
        if len(self.poke_history) >= 3:
            self.is_dizzy = True
            self.dizzy_until = now + 2.4
            self.eye_shape_override = EyeShape.SPIRAL
            self.blush_intensity = 0.95
            self.poke_history.clear()
        else:
            # Single poke reaction: squash and cute blink
            self.squash_y = 0.88
            self.squash_x = 1.10
            self.blush_intensity = min(1.0, self.blush_intensity + 0.3)
            self._trigger_blink()

    # --- Drag & Drop Context Dropping (Coucou Mailbox Morph) ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.is_drag_hovered = True
            self.last_interaction_time = time.monotonic()
            self.is_sleeping = False
            self.update()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.is_drag_hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent) -> None:
        self.is_drag_hovered = False
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                # Swallows and chews happily
                self.is_chewing = True
                self.chew_timer = 0.0
                self.eye_shape_override = EyeShape.HAPPY
                self.blush_intensity = 1.0
                self.file_dropped.emit(str(Path(path).resolve()))

        self.update()
        event.acceptProposedAction()

    # --- Paint Engine ---

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.mode == "ball":
            self._paint_coucou_mascot(painter)
        else:
            self._paint_dynamic_island(painter)

    def _paint_coucou_mascot(self, painter: QPainter) -> None:
        """Render Coucou's Mochi: Pearlescent squircle, state glow, cheeks and expressive eyes."""
        width = self.width()
        height = self.height()

        center_x = width / 2.0
        idle_float = math.sin(self.idle_angle) * 2.2
        center_y = (height / 2.0) + idle_float + self.jump_offset_y

        # Proportions: Coucou Mochi has rx = 1.14 * R, ry = 0.88 * R
        base_r = (self._ball_size / 2.0)
        rx = (base_r * 1.14) * self.squash_x
        ry = (base_r * 0.88) * self.squash_y

        # Dynamic inertia stretch during drag
        if self.is_dragging:
            rx += min(10.0, abs(self.drag_velocity.x()) * 0.35)
            ry += min(10.0, abs(self.drag_velocity.y()) * 0.35)

        painter.save()

        # Handle tilt rotation (e.g. during dizzy state)
        if abs(self.tilt_angle) > 0.1:
            painter.translate(center_x, center_y)
            painter.rotate(self.tilt_angle)
            painter.translate(-center_x, -center_y)

        # 1. Soft Floor Shadow (diminishes when jumping)
        shadow_alpha = int(max(0, 50 - abs(self.jump_offset_y) * 2.5))
        if shadow_alpha > 0:
            shadow_rect = QRectF(center_x - rx * 0.75, height - 12, rx * 1.5, 8)
            painter.setBrush(QBrush(QColor(0, 0, 0, shadow_alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(shadow_rect)

        # 2. Status Halo / Outer Ambient Glow
        halo_color = self._get_halo_color()
        halo_grad = QRadialGradient(center_x, center_y, max(rx, ry) + 12)
        halo_grad.setColorAt(0.68, halo_color)
        halo_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(halo_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), rx + 10, ry + 10)

        # 3. Mochi Anatomical Superellipse Body Path
        body_path = _build_mochi_path(center_x, center_y, rx, ry)

        # 4. Coucou Body Base: Velvety Pearl Off-White Gradient
        # Top: #F1F2F5, Bottom: #CBD0D8
        body_grad = QLinearGradient(center_x, center_y - ry, center_x, center_y + ry)
        body_grad.setColorAt(0.0, QColor(241, 242, 245))
        body_grad.setColorAt(1.0, QColor(203, 208, 216))
        painter.setBrush(QBrush(body_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1.0))
        painter.drawPath(body_path)

        # 5. State Tint Lighting from Base (Coucou State Tinting)
        tint_color, tint_opacity = self._get_state_tint()
        if tint_opacity > 0.01:
            tint_grad = QLinearGradient(center_x, center_y + ry, center_x, center_y - ry * 0.3)
            tint_grad.setColorAt(0.0, QColor(tint_color.red(), tint_color.green(), tint_color.blue(), int(255 * tint_opacity)))
            tint_grad.setColorAt(1.0, QColor(tint_color.red(), tint_color.green(), tint_color.blue(), 0))
            painter.save()
            painter.setClipPath(body_path)
            painter.setBrush(QBrush(tint_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(body_path)
            painter.restore()

        # 6. Upper Specular Shine (Glossy Mochi Highlight)
        shine_grad = QRadialGradient(center_x - rx * 0.25, center_y - ry * 0.5, rx * 0.8)
        shine_grad.setColorAt(0.0, QColor(255, 255, 255, 160))
        shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.save()
        painter.setClipPath(body_path)
        painter.setBrush(QBrush(shine_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x - rx * 0.25, center_y - ry * 0.45), rx * 0.7, ry * 0.35)
        painter.restore()

        # 7. Mailbox Slot Morph (Opens during file drag)
        if self.slot_open > 0.02:
            self._paint_mailbox_slot(painter, body_path, center_x, center_y, rx, ry)

        # 8. Rosy Cheeks (Blush)
        self._paint_blush(painter, center_x, center_y, rx, ry)

        # 9. Expressive Mochi Eyes
        self._paint_eyes(painter, center_x, center_y, rx, ry)

        # 10. Sleeping Zzz particles
        if self.is_sleeping:
            self._paint_sleeping_indicators(painter, center_x, center_y, rx, ry)

        painter.restore()

    def _get_halo_color(self) -> QColor:
        if self.ball_state == BallState.IDLE_OK:
            alpha = 140 if not self.is_drag_hovered else 220
            return QColor(6, 182, 212, alpha)
        elif self.ball_state == BallState.PROCESSING:
            pulse = int(140 + 70 * math.sin(self.pulse_phase))
            return QColor(59, 130, 246, pulse)
        else:  # ALERT
            pulse = int(160 + 90 * math.sin(self.pulse_phase * 1.5))
            return QColor(239, 68, 68, pulse)

    def _get_state_tint(self) -> tuple[QColor, float]:
        if self.ball_state == BallState.IDLE_OK:
            return QColor(16, 185, 129), 0.28
        elif self.ball_state == BallState.PROCESSING:
            pulse = 0.35 + 0.15 * math.sin(self.pulse_phase)
            return QColor(59, 130, 246), pulse
        else:  # ALERT
            pulse = 0.50 + 0.25 * math.sin(self.pulse_phase * 1.5)
            return QColor(239, 68, 68), pulse

    def _paint_blush(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render soft rosy blush ovals."""
        alpha = int(clamp(self.blush_intensity * 180.0, 20.0, 220.0))
        blush_color = QColor(255, 120, 150, alpha)
        painter.setBrush(QBrush(blush_color))
        painter.setPen(Qt.NoPen)

        blush_rx = rx * 0.18
        blush_ry = ry * 0.11
        blush_y = cy + ry * 0.18
        blush_spacing = rx * 0.54

        painter.drawEllipse(QPointF(cx - blush_spacing, blush_y), blush_rx, blush_ry)
        painter.drawEllipse(QPointF(cx + blush_spacing, blush_y), blush_rx, blush_ry)

    def _paint_mailbox_slot(
        self,
        painter: QPainter,
        body_path: QPainterPath,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
    ) -> None:
        """Render Coucou's mailbox slot cutout inside the squircle face."""
        slot_w = rx * 1.40 * self.slot_open
        slot_h = ry * 0.34 * self.slot_open
        slot_x = cx - slot_w / 2.0
        slot_y = cy - ry * 0.92 + (ry * 0.10 * self.slot_open)

        painter.save()
        painter.setClipPath(body_path)

        # Slot Cavity
        slot_rect = QRectF(slot_x, slot_y, slot_w, slot_h)
        slot_grad = QLinearGradient(slot_x, slot_y, slot_x, slot_y + slot_h)
        slot_grad.setColorAt(0.0, QColor(7, 8, 10))
        slot_grad.setColorAt(1.0, QColor(20, 24, 33))
        painter.setBrush(QBrush(slot_grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(slot_rect, slot_h / 2.0, slot_h / 2.0)

        # Top Rim Highlight (1pt white 60% line)
        rim_alpha = int(160 * self.slot_open)
        painter.setPen(QPen(QColor(255, 255, 255, rim_alpha), 1.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(slot_x + 6, slot_y + 0.5), QPointF(slot_x + slot_w - 6, slot_y + 0.5))

        painter.restore()

    def _paint_eyes(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render Coucou's lively eyes with cursor tracking and expressions."""
        shape = self.eye_shape_override or EyeShape.PILL
        ink_color = QColor(20, 26, 36)

        # Eye Positioning (Coucou eye spacing ~0.37 * R)
        eye_y = cy - ry * 0.08
        eye_spacing = rx * 0.37
        base_w = 7.5
        base_h = 12.0

        for side in (-1.0, 1.0):
            eye_cx = cx + (side * eye_spacing)
            eye_cy = eye_y

            # Inverted gaze offset applied to pupils/eyes
            look_offset_x = self.eye_look_x * 2.8
            look_offset_y = self.eye_look_y * 2.5
            eye_cx += look_offset_x
            eye_cy += look_offset_y

            painter.save()

            if shape == EyeShape.HAPPY:
                # Upward curving joyous arcs (^ ^)
                arc_path = QPainterPath()
                arc_w = base_w * 1.3
                arc_h = base_h * 0.9
                arc_path.moveTo(eye_cx - arc_w / 2.0, eye_cy + arc_h * 0.2)
                arc_path.quadTo(eye_cx, eye_cy - arc_h * 0.6, eye_cx + arc_w / 2.0, eye_cy + arc_h * 0.2)
                pen = QPen(ink_color, 2.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(arc_path)

            elif shape == EyeShape.WIDE:
                # Wide attentive eyes with large round pupil
                wide_w = base_w * 1.3
                wide_h = base_h * 1.2
                painter.setBrush(QBrush(ink_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(eye_cx, eye_cy), wide_w / 2.0, wide_h / 2.0)
                # Catchlight
                painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
                painter.drawEllipse(QPointF(eye_cx + 1.2, eye_cy - 2.0), 1.8, 1.8)

            elif shape == EyeShape.SPIRAL:
                # Coucou Dizzy Spiral (spinning Archimedean spiral)
                spiral_path = QPainterPath()
                steps = 24
                for s in range(steps):
                    a = (s / steps) * 4.0 * math.pi
                    r = (s / steps) * (base_w * 0.8)
                    ang = a + self.spiral_phase * side
                    px = eye_cx + math.cos(ang) * r
                    py = eye_cy + math.sin(ang) * r
                    if s == 0:
                        spiral_path.moveTo(px, py)
                    else:
                        spiral_path.lineTo(px, py)
                pen = QPen(ink_color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(spiral_path)

            elif shape == EyeShape.CLOSED:
                # Sleeping peaceful closed arcs
                close_path = QPainterPath()
                arc_w = base_w * 1.3
                arc_h = base_h * 0.7
                close_path.moveTo(eye_cx - arc_w / 2.0, eye_cy - arc_h * 0.1)
                close_path.quadTo(eye_cx, eye_cy + arc_h * 0.5, eye_cx + arc_w / 2.0, eye_cy - arc_h * 0.1)
                pen = QPen(ink_color, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(close_path)

            else:  # EyeShape.PILL (Default Coucou Mochi Eye)
                # Modulated by blink_factor
                effective_h = max(2.0, base_h * (1.0 - self.blink_factor))
                eye_rect = QRectF(eye_cx - base_w / 2.0, eye_cy - effective_h / 2.0, base_w, effective_h)
                painter.setBrush(QBrush(ink_color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(eye_rect, base_w / 2.0, base_w / 2.0)

                # Catchlight sparkle (only visible when eyes open)
                if self.blink_factor < 0.4:
                    sparkle_x = eye_cx + 1.2
                    sparkle_y = eye_cy - effective_h * 0.22
                    painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
                    painter.drawEllipse(QPointF(sparkle_x, sparkle_y), 1.5, 1.8)

            painter.restore()

    def _paint_sleeping_indicators(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render floating 'Zzz' particles when asleep."""
        painter.save()
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184, 180))

        # Floating offset based on idle angle
        float_y = math.sin(self.idle_angle) * 3.0
        painter.drawText(int(cx + rx * 0.7), int(cy - ry * 0.6 + float_y), "z")
        painter.drawText(int(cx + rx * 0.95), int(cy - ry * 0.9 + float_y * 1.3), "Z")
        painter.restore()

    # --- Dynamic Island Mode Painting ---

    def _paint_dynamic_island(self, painter: QPainter) -> None:
        """Render horizontal dark-glass dynamic island pill."""
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Glass Background Pill
        pill_grad = QLinearGradient(0, 0, self.width(), 0)
        pill_grad.setColorAt(0.0, QColor(15, 23, 42, 245))
        pill_grad.setColorAt(1.0, QColor(11, 14, 20, 245))

        border_color = QColor(6, 182, 212) if self.ball_state == BallState.IDLE_OK else QColor(239, 68, 68)
        painter.setBrush(QBrush(pill_grad))
        painter.setPen(QPen(border_color, 1.5))
        painter.drawRoundedRect(rect, 22, 22)

        # Mini Coucou Mochi Avatar on Left
        mini_cx = 26.0
        mini_cy = self.height() / 2.0
        mini_rx = 13.0
        mini_ry = 10.0

        mini_path = _build_mochi_path(mini_cx, mini_cy, mini_rx, mini_ry, n_points=36)
        mini_grad = QLinearGradient(mini_cx, mini_cy - mini_ry, mini_cx, mini_cy + mini_ry)
        mini_grad.setColorAt(0.0, QColor(241, 242, 245))
        mini_grad.setColorAt(1.0, QColor(203, 208, 216))
        painter.setBrush(QBrush(mini_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(mini_path)

        # Mini Rosy Cheeks
        painter.setBrush(QBrush(QColor(255, 120, 150, 160)))
        painter.drawEllipse(QPointF(mini_cx - 6.5, mini_cy + 2.0), 2.2, 1.5)
        painter.drawEllipse(QPointF(mini_cx + 6.5, mini_cy + 2.0), 2.2, 1.5)

        # Mini Eye Dots
        painter.setBrush(QBrush(QColor(20, 26, 36)))
        look_dx = self.eye_look_x * 1.5
        painter.drawEllipse(QPointF(mini_cx - 4.0 + look_dx, mini_cy - 1.0), 1.8, 2.5)
        painter.drawEllipse(QPointF(mini_cx + 4.0 + look_dx, mini_cy - 1.0), 1.8, 2.5)

        # NOC Live Telemetry Summary
        painter.setPen(QColor(226, 232, 240))
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRect(52, 0, self.width() - 60, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            self.telemetry_summary,
        )


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))
