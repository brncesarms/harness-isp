import os
import pytest

# Ensure headless offscreen for test runner
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from core.session import SessionManager
from gui.widget import FloatingBallWidget
from gui.chat_panel import ChatPanel


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


def test_chat_panel_instantiation(qapp):
    session = SessionManager()
    panel = ChatPanel(session)
    assert panel.windowTitle() == "HarnessISP - Painel NOC"

    # Simulate sending message
    panel.append_message("user", "ping 1.1.1.1")
    panel.append_message("assistant", "Ping OK", risk="LOW")
