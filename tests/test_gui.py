import os
from pathlib import Path
import time
import pytest

# Ensure headless offscreen for test runner
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QPointF, QPoint, QMimeData, QUrl, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from core.session import BallState, SessionManager
from gui.widget import FloatingBallWidget, EyeShape
from gui.approval_pill import ApprovalPillWidget
from main import launch_native_terminal


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_floating_ball_widget_instantiation(qapp):
    ball = FloatingBallWidget()
    assert ball.width() > 0
    assert ball.height() > 0
    assert ball.mode == "ball"

    # Test mode toggle (Coucou Dynamic Island)
    ball.toggle_mode()
    assert ball.mode == "pill"
    assert ball.width() == 320

    ball.toggle_mode()
    assert ball.mode == "ball"


def test_floating_ball_states_and_telemetry(qapp):
    ball = FloatingBallWidget()
    ball.set_ball_state(BallState.PROCESSING)
    assert ball.ball_state == BallState.PROCESSING

    ball.set_ball_state(BallState.ALERT)
    assert ball.ball_state == BallState.ALERT
    assert ball.eye_shape_override == EyeShape.WIDE

    # Finishing task or resolving alert triggers happy celebration
    ball.set_ball_state(BallState.IDLE_OK)
    assert ball.ball_state == BallState.IDLE_OK
    assert ball.eye_shape_override == EyeShape.HAPPY

    ball.set_telemetry("🟢 BGP: 6 Up | ⚡ 5ms")
    assert "BGP: 6 Up" in ball.telemetry_summary


def test_coucou_mochi_poking_and_dizzy(qapp):
    ball = FloatingBallWidget()
    assert not ball.is_dizzy

    # Single poke
    ball._handle_poke()
    assert len(ball.poke_history) == 1
    assert not ball.is_dizzy

    # Rapid second and third pokes
    ball._handle_poke()
    ball._handle_poke()
    assert ball.is_dizzy
    assert ball.eye_shape_override == EyeShape.SPIRAL
    assert ball.blush_intensity >= 0.9


def test_coucou_mochi_happy_jump(qapp):
    ball = FloatingBallWidget()
    ball.happy_jump()
    assert ball.jump_velocity < 0
    assert ball.eye_shape_override == EyeShape.HAPPY
    assert ball.blush_intensity > 0.8


def test_coucou_mochi_context_dropping(qapp, tmp_path):
    ball = FloatingBallWidget()
    test_file = tmp_path / "mikrotik_test.rsc"
    test_file.write_text("/ip address print")

    received_drops = []
    ball.file_dropped.connect(lambda p: received_drops.append(p))

    # Simulate drop event
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(str(test_file))])
    drop_event = QDropEvent(
        QPointF(40.0, 40.0),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    ball.dropEvent(drop_event)

    assert len(received_drops) == 1
    assert Path(received_drops[0]).resolve() == test_file.resolve()
    assert ball.is_chewing
    assert ball.eye_shape_override == EyeShape.HAPPY


def test_approval_pill_widget(qapp):
    pill = ApprovalPillWidget()
    assert pill.width() == 380

    received_actions = []
    pill.action_decided.connect(lambda action, cmd: received_actions.append((action, cmd)))

    # Test prompt configuration
    pill.prompt(
        command="/ip firewall filter add chain=input action=drop",
        risk_level="CRITICAL",
        reason="Bloqueia porta de gerência SSH",
        anchor_pos=QPoint(100, 100),
    )
    assert pill.current_command == "/ip firewall filter add chain=input action=drop"
    assert pill.risk_tag.text() == "RISCO CRÍTICO"

    # Test safe mode decision
    pill._choose("safe_mode")
    assert len(received_actions) == 1
    assert received_actions[0][0] == "safe_mode"


def test_launch_native_terminal_mock(monkeypatch, tmp_path):
    # Test that launch_native_terminal doesn't crash
    called = []
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: called.append(args))
    launch_native_terminal(tmp_path)
    assert len(called) > 0
