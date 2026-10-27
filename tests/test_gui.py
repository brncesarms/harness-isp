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
from gui.widget import FloatingBallWidget
from gui.approval_pill import ApprovalPillWidget
from main import launch_native_terminal


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_sentinela_widget_instantiation(qapp):
    widget = FloatingBallWidget()
    assert widget.width() > 0
    assert widget.height() > 0
    assert widget.mode == "ball"

    # Test mode toggle (Dynamic Island pill)
    widget.toggle_mode()
    assert widget.mode == "pill"
    assert widget.width() == 340

    widget.toggle_mode()
    assert widget.mode == "ball"


def test_sentinela_states_and_telemetry(qapp):
    widget = FloatingBallWidget()
    widget.set_ball_state(BallState.PROCESSING)
    assert widget.ball_state == BallState.PROCESSING

    widget.set_ball_state(BallState.ALERT)
    assert widget.ball_state == BallState.ALERT

    widget.set_ball_state(BallState.IDLE_OK)
    assert widget.ball_state == BallState.IDLE_OK

    widget.set_telemetry("🟢 BGP: 6 Up | ⚡ 5ms | 🛡️ Safe-Mode")
    assert "BGP: 6 Up" in widget.telemetry_summary


def test_sentinela_context_dropping(qapp, tmp_path):
    widget = FloatingBallWidget()
    test_file = tmp_path / "mikrotik_test.rsc"
    test_file.write_text("/ip address print")

    received_drops = []
    widget.file_dropped.connect(lambda p: received_drops.append(p))

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
    widget.dropEvent(drop_event)

    assert len(received_drops) == 1
    assert Path(received_drops[0]).resolve() == test_file.resolve()


def test_sentinela_signals(qapp):
    widget = FloatingBallWidget()
    clicked = []
    widget.clicked.connect(lambda: clicked.append(True))

    assert len(clicked) == 0


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
