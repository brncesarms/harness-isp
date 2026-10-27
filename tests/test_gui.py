import os
from pathlib import Path
import pytest

# Ensure headless offscreen for test runner
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QPoint, QMimeData, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from core.session import BallState, SessionManager
from gui.widget import FloatingBallWidget
from gui.chat_panel import ChatPanel
from gui.approval_pill import ApprovalPillWidget


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

    ball.set_telemetry("🟢 BGP: 6 Up | ⚡ 5ms")
    assert "BGP: 6 Up" in ball.telemetry_summary


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


def test_chat_panel_instantiation(qapp):
    session = SessionManager()
    panel = ChatPanel(session)
    assert panel.windowTitle() == "HarnessISP - Painel NOC"

    panel.append_message("user", "ping 1.1.1.1")
    panel.append_message("assistant", "Ping OK", risk="LOW")
