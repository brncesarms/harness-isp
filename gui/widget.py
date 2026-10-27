"""Floating Desktop Companion Widget (Coucou-Inspired Mascot & Dynamic Island) in PySide6.

Faithfully inspired by Louis-CFM/coucou:
1. Authentic Mochi Anatomy: Soft pearlescent squircle with large forehead, lower-third face placement,
   rosy pastel cheeks set outward, and subtle state tinting without harsh halos.
2. Coucou Signature Shoulder Badges:
   - IDLE_OK: Sleek emerald dot with black rim.
   - PROCESSING: Purple pill badge with animated jumping dots (...) and lavender belly tint.
   - ALERT: Crimson badge with exclamation mark (!) and warning belly tint.
3. Expressive Eye Dynamics & Real-Time Cursor Gaze:
   - PILL: Attentive companion eyes in lower third tracking the user's cursor across screens.
   - HAPPY: Joyous curved arcs (^ ^) upon finishing tasks or swallowing context.
   - WIDE: Wide-open pupils during network alerts.
   - SPIRAL: Spinning Archimedean spirals when rapidly poked (Dizzy state).
   - CLOSED: Peaceful sleeping eyes when idle for extended periods.
4. Interactive Mechanics:
   - Poke & Dizzy: Playful squash response on click; becomes dizzy with spiral eyes if clicked repeatedly.
   - Context Dropping (Mailbox Slot Morph): Mouth slot opens at top when dragging network configs;
     swallows and chews happily on drop.
   - Happy Jump: Elastic celebration leap on task completion.
5. Dynamic Island Pill: Smooth toggle to horizontal dark-glass status HUD with mini-Mochi avatar.
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
    """Build Coucou's signature superellipse (squircle) path with exponent 2.0/2.7."""
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

        # Dimensions: Coucou aspect ratio rx=1.15 * R, ry=0.88 * R
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
        self.dots_phase = 0.0
        self.tilt_angle = 0.0
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.jump_offset_y = 0.0
        self.jump_velocity = 0.0
        self.blush_intensity = 0.7   # Rosy cheeks
        self.slot_open = 0.0         # Mailbox swallow morph
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

        # Periodic Blink Timer (cadence 3.5s - 5s)
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
        elif state == BallState.IDLE_OK and old_state in (BallState.PROCESSING, BallState.ALERT):
            # Task finished: Celebrate with Coucou Happy Jump!
            self.happy_jump()
        elif state == BallState.PROCESSING:
            self.eye_shape_override = None
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
        """Coucou-signature happy celebration leap."""
        self.jump_velocity = -7.5
        self.eye_shape_override = EyeShape.HAPPY
        self.blush_intensity = 1.0
        QTimer.singleShot(1600, self._reset_override)
        self.update()

    def _reset_override(self) -> None:
        if not self.is_dizzy and not self.is_chewing:
            self.eye_shape_override = None
            self.blush_intensity = 0.7
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
        self.dots_phase = (self.dots_phase + 0.15) % (2.0 * math.pi)

        # 2. Dizzy Recovery Timer
        if self.is_dizzy:
            self.spiral_phase = (self.spiral_phase + 0.35) % (2.0 * math.pi)
            self.tilt_angle = math.sin(self.spiral_phase * 1.5) * 8.0
            if now > self.dizzy_until:
                self.is_dizzy = False
                self.tilt_angle = 0.0
                self.eye_shape_override = None
                self.blush_intensity = 0.7
        else:
            self.tilt_angle = 0.0

        # 3. Chew Animation (after swallowing network context)
        if self.is_chewing:
            self.chew_timer += 0.2
            self.squash_y = 1.0 + math.sin(self.chew_timer * 4.0) * 0.06
            self.squash_x = 1.0 - math.sin(self.chew_timer * 4.0) * 0.04
            if self.chew_timer >= 2.5:
                self.is_chewing = False
                self.squash_x = 1.0
                self.squash_y = 1.0
                self.eye_shape_override = None
                self.blush_intensity = 0.7

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
        self.slot_open += (target_slot - self.slot_open) * 0.22

        # 6. Real-time Cursor Gaze Tracking (Coucou Gaze Engine)
        if not self.is_dizzy and not self.is_sleeping and not self.is_chewing:
            if self.is_drag_hovered:
                # Eagerly look up at the incoming dropped file
                self.target_look_x = 0.0
                self.target_look_y = -0.85
            elif self.ball_state == BallState.PROCESSING:
                # Thinking scan motion
                self.target_look_x = math.sin(self.idle_angle * 1.8) * 0.55
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
            self.blush_intensity = 1.0
            self.poke_history.clear()
        else:
            # Single poke reaction: squash and cute blink
            self.squash_y = 0.88
            self.squash_x = 1.10
            self.blush_intensity = 1.0
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
        """Render true Coucou Mochi: Authentic superellipse, pearlescent gradient, lower-third face."""
        width = self.width()
        height = self.height()

        center_x = width / 2.0
        idle_float = math.sin(self.idle_angle) * 2.2
        center_y = (height / 2.0) + idle_float + self.jump_offset_y

        # Proportions: Coucou Mochi has rx = 1.15 * R, ry = 0.88 * R
        base_r = (self._ball_size / 2.0)
        rx = (base_r * 1.15) * self.squash_x
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

        # 1. Soft Floor Shadow (clean and soft, diminishes when jumping)
        shadow_alpha = int(max(0, 75 - abs(self.jump_offset_y) * 3.5))
        if shadow_alpha > 0:
            shadow_rect = QRectF(center_x - rx * 0.72, center_y + ry + 3, rx * 1.44, 10)
            shadow_grad = QRadialGradient(center_x, center_y + ry + 8, rx * 0.72)
            shadow_grad.setColorAt(0.0, QColor(0, 0, 0, shadow_alpha))
            shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(shadow_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(shadow_rect)

        # 2. Mochi Anatomical Superellipse Body Path
        body_path = _build_mochi_path(center_x, center_y, rx, ry)

        # 3. Coucou Body Base: Soft Pearlescent Cream / White Gradient
        body_grad = QLinearGradient(center_x, center_y - ry, center_x, center_y + ry)
        body_grad.setColorAt(0.0, QColor(254, 254, 255))
        body_grad.setColorAt(0.65, QColor(244, 244, 248))
        body_grad.setColorAt(1.0, QColor(218, 220, 228))
        painter.setBrush(QBrush(body_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(body_path)

        # 4. Subtle State Tint on the lower belly (Coucou belly tint)
        tint_color, tint_alpha = self._get_belly_tint()
        if tint_alpha > 0:
            tint_grad = QLinearGradient(center_x, center_y + ry, center_x, center_y)
            tint_grad.setColorAt(0.0, QColor(tint_color.red(), tint_color.green(), tint_color.blue(), tint_alpha))
            tint_grad.setColorAt(1.0, QColor(tint_color.red(), tint_color.green(), tint_color.blue(), 0))
            painter.save()
            painter.setClipPath(body_path)
            painter.setBrush(QBrush(tint_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(body_path)
            painter.restore()

        # 5. Top Specular Shine (Soft diffuse highlight)
        shine_grad = QRadialGradient(center_x - rx * 0.2, center_y - ry * 0.45, rx * 0.8)
        shine_grad.setColorAt(0.0, QColor(255, 255, 255, 175))
        shine_grad.setColorAt(0.8, QColor(255, 255, 255, 0))
        painter.save()
        painter.setClipPath(body_path)
        painter.setBrush(QBrush(shine_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x - rx * 0.2, center_y - ry * 0.4), rx * 0.7, ry * 0.35)
        painter.restore()

        # 6. Mailbox Slot Morph (Opens during file drag)
        if self.slot_open > 0.02:
            self._paint_mailbox_slot(painter, body_path, center_x, center_y, rx, ry)

        # 7. Rosy Pastel Cheeks (Coucou Blush: Set outward, above eye level!)
        self._paint_blush(painter, center_x, center_y, rx, ry)

        # 8. Expressive Mochi Eyes (Coucou: Positioned in the lower-third!)
        self._paint_eyes(painter, center_x, center_y, rx, ry)

        # 9. Coucou Signature Shoulder Badge (Status Dot or Thinking Pill)
        self._paint_shoulder_badge(painter, center_x, center_y, rx, ry)

        # 10. Sleeping Zzz particles
        if self.is_sleeping:
            self._paint_sleeping_indicators(painter, center_x, center_y, rx, ry)

        painter.restore()

    def _get_belly_tint(self) -> tuple[QColor, int]:
        """Subtle belly tint matching Coucou's state glows without covering the character."""
        if self.ball_state == BallState.IDLE_OK:
            return QColor(16, 185, 129), 35
        elif self.ball_state == BallState.PROCESSING:
            pulse = int(50 + 25 * math.sin(self.pulse_phase))
            return QColor(139, 92, 246), pulse
        else:  # ALERT
            pulse = int(70 + 35 * math.sin(self.pulse_phase * 1.5))
            return QColor(239, 68, 68), pulse

    def _paint_shoulder_badge(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render Coucou's iconic status badge on the upper-left shoulder."""
        bx = cx - rx * 0.74
        by = cy - ry * 0.65

        if self.ball_state == BallState.PROCESSING:
            # Coucou Thinking Pill: Purple pill with 3 animated white dots (...)
            pill_w = 34.0
            pill_h = 18.0
            pill_rect = QRectF(bx - pill_w / 2.0, by - pill_h / 2.0, pill_w, pill_h)

            # Black border
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(pill_rect.adjusted(-2, -2, 2, 2), (pill_h + 4) / 2.0, (pill_h + 4) / 2.0)

            # Purple fill
            painter.setBrush(QBrush(QColor(139, 92, 246)))
            painter.drawRoundedRect(pill_rect, pill_h / 2.0, pill_h / 2.0)

            # 3 Animated jumping dots
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            dot_spacing = 7.5
            for i in range(3):
                phase_offset = self.dots_phase - (i * 0.8)
                jump = max(0.0, math.sin(phase_offset)) * 2.2
                dx = (i - 1) * dot_spacing
                painter.drawEllipse(QPointF(bx + dx, by - jump), 2.2, 2.2)

        elif self.ball_state == BallState.ALERT:
            # Coucou Alert Badge: Red circle with white exclamation mark (!)
            radius = 11.0
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(bx, by), radius + 2, radius + 2)

            pulse_col = QColor(239, 68, 68)
            painter.setBrush(QBrush(pulse_col))
            painter.drawEllipse(QPointF(bx, by), radius, radius)

            # White Exclamation Mark
            painter.setPen(QPen(QColor(255, 255, 255), 2.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(bx, by - 4.5), QPointF(bx, by + 1.0))
            painter.drawPoint(QPointF(bx, by + 4.5))

        else:
            # Coucou Normal/Finished Dot: Crisp Emerald circle with dark outline
            radius = 8.5
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(bx, by), radius + 2, radius + 2)

            painter.setBrush(QBrush(QColor(16, 185, 129)))
            painter.drawEllipse(QPointF(bx, by), radius, radius)

    def _paint_blush(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render Coucou's soft rosy pastel blush ovals placed outward and above eyes."""
        alpha = int(clamp(self.blush_intensity * 210.0, 40.0, 240.0))
        blush_color = QColor(249, 183, 198, alpha)
        painter.setBrush(QBrush(blush_color))
        painter.setPen(Qt.NoPen)

        blush_rx = rx * 0.18
        blush_ry = ry * 0.10
        blush_y = cy + ry * 0.16  # Above eye level!
        blush_spacing = rx * 0.60

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
        slot_w = rx * 1.35 * self.slot_open
        slot_h = ry * 0.32 * self.slot_open
        slot_x = cx - slot_w / 2.0
        slot_y = cy - ry * 0.94 + (ry * 0.10 * self.slot_open)

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

        # Top Rim Highlight (1pt white line)
        rim_alpha = int(160 * self.slot_open)
        painter.setPen(QPen(QColor(255, 255, 255, rim_alpha), 1.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(slot_x + 6, slot_y + 0.5), QPointF(slot_x + slot_w - 6, slot_y + 0.5))

        painter.restore()

    def _paint_eyes(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render Coucou's signature eyes placed in the lower-third with cursor tracking."""
        shape = self.eye_shape_override or EyeShape.PILL
        ink_color = QColor(24, 24, 28)

        # Coucou Eye Positioning: Lower-third of body!
        eye_y = cy + ry * 0.38
        eye_spacing = rx * 0.36
        base_w = 9.5
        base_h = 14.5

        for side in (-1.0, 1.0):
            eye_cx = cx + (side * eye_spacing)
            eye_cy = eye_y

            # Dynamic gaze offset applied to pupils/eyes
            look_offset_x = self.eye_look_x * 2.5
            look_offset_y = self.eye_look_y * 2.2
            eye_cx += look_offset_x
            eye_cy += look_offset_y

            painter.save()

            if shape == EyeShape.HAPPY:
                # Coucou Happy: Joyous thick curved arcs (^ ^) exactly like char_state_finished.png
                arc_path = QPainterPath()
                arc_w = base_w * 1.5
                arc_h = base_h * 0.8
                arc_path.moveTo(eye_cx - arc_w / 2.0, eye_cy + arc_h * 0.15)
                arc_path.quadTo(eye_cx, eye_cy - arc_h * 0.65, eye_cx + arc_w / 2.0, eye_cy + arc_h * 0.15)
                pen = QPen(ink_color, 3.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(arc_path)

            elif shape == EyeShape.WIDE:
                # Coucou Wide: Big round attentive eyes
                wide_w = base_w * 1.4
                wide_h = base_h * 1.2
                painter.setBrush(QBrush(ink_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(eye_cx, eye_cy), wide_w / 2.0, wide_h / 2.0)
                # Catchlight
                painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
                painter.drawEllipse(QPointF(eye_cx + 1.2, eye_cy - 2.0), 1.8, 1.8)

            elif shape == EyeShape.SPIRAL:
                # Coucou Dizzy: Spinning Archimedean spiral matching dizzy.png
                spiral_path = QPainterPath()
                steps = 26
                for s in range(steps):
                    a = (s / steps) * 4.2 * math.pi
                    r = (s / steps) * (base_w * 0.85)
                    ang = a + self.spiral_phase * side
                    px = eye_cx + math.cos(ang) * r
                    py = eye_cy + math.sin(ang) * r
                    if s == 0:
                        spiral_path.moveTo(px, py)
                    else:
                        spiral_path.lineTo(px, py)
                pen = QPen(ink_color, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(spiral_path)

            elif shape == EyeShape.CLOSED:
                # Sleeping peaceful downward curves
                close_path = QPainterPath()
                arc_w = base_w * 1.3
                arc_h = base_h * 0.65
                close_path.moveTo(eye_cx - arc_w / 2.0, eye_cy - arc_h * 0.1)
                close_path.quadTo(eye_cx, eye_cy + arc_h * 0.5, eye_cx + arc_w / 2.0, eye_cy - arc_h * 0.1)
                pen = QPen(ink_color, 2.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(close_path)

            else:  # EyeShape.PILL (Authentic Coucou Mochi Pill Eye)
                effective_h = max(2.5, base_h * (1.0 - self.blink_factor))
                eye_rect = QRectF(eye_cx - base_w / 2.0, eye_cy - effective_h / 2.0, base_w, effective_h)
                painter.setBrush(QBrush(ink_color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(eye_rect, base_w / 2.0, base_w / 2.0)

            painter.restore()

    def _paint_sleeping_indicators(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float) -> None:
        """Render floating 'Zzz' particles when asleep."""
        painter.save()
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184, 180))

        # Floating offset based on idle angle
        float_y = math.sin(self.idle_angle) * 3.0
        painter.drawText(int(cx + rx * 0.7), int(cy - ry * 0.4 + float_y), "z")
        painter.drawText(int(cx + rx * 0.95), int(cy - ry * 0.7 + float_y * 1.3), "Z")
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
        mini_rx = 13.5
        mini_ry = 10.5

        mini_path = _build_mochi_path(mini_cx, mini_cy, mini_rx, mini_ry, n_points=36)
        mini_grad = QLinearGradient(mini_cx, mini_cy - mini_ry, mini_cx, mini_cy + mini_ry)
        mini_grad.setColorAt(0.0, QColor(254, 254, 255))
        mini_grad.setColorAt(1.0, QColor(218, 220, 228))
        painter.setBrush(QBrush(mini_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(mini_path)

        # Mini Rosy Cheeks
        painter.setBrush(QBrush(QColor(249, 183, 198, 210)))
        painter.drawEllipse(QPointF(mini_cx - 7.5, mini_cy + 1.2), 2.4, 1.5)
        painter.drawEllipse(QPointF(mini_cx + 7.5, mini_cy + 1.2), 2.4, 1.5)

        # Mini Eye Dots (Lower third!)
        painter.setBrush(QBrush(QColor(24, 24, 28)))
        look_dx = self.eye_look_x * 1.2
        painter.drawEllipse(QPointF(mini_cx - 4.5 + look_dx, mini_cy + 3.0), 1.8, 2.5)
        painter.drawEllipse(QPointF(mini_cx + 4.5 + look_dx, mini_cy + 3.0), 1.8, 2.5)

        # Mini Shoulder Dot
        painter.setBrush(QBrush(QColor(16, 185, 129)))
        painter.drawEllipse(QPointF(mini_cx - mini_rx * 0.7, mini_cy - mini_ry * 0.6), 2.2, 2.2)

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
