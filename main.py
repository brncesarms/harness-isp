"""Main entrypoint for HarnessISP Desktop Companion (Coucou Architecture).

Acts as a living desktop companion and pre-flight HUD on the workstation,
launching the user's native terminal directly into the canonical CT 249
HarnessISP workspace running the Google Antigravity CLI (agy).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtWidgets import QApplication

from core.failsafe_guard import FailsafeGuard
from core.session import BallState, SessionManager
from core.storage import StorageManager
from gui.approval_pill import ApprovalPillWidget
from gui.tray import TrayManager
from gui.widget import FloatingBallWidget


def launch_native_terminal(project_dir: Path | None = None) -> None:
    """Launches default terminal directly into CT 249 /home/brn/harness-isp with agy CLI."""
    current_host = socket.gethostname()

    # Remote workstation -> SSH directly into CT 249
    if current_host != "harness-isp":
        target_cmd = "ssh -t harness-isp 'cd /home/brn/harness-isp && export PATH=$HOME/.local/bin:$PATH && agy'"
    else:
        target_cmd = "cd /home/brn/harness-isp && export PATH=$HOME/.local/bin:$PATH && agy"

    term = os.environ.get("TERMINAL")
    candidates: list[list[str]] = []
    if term:
        candidates.append([term, "-e", "bash", "-c", target_cmd])

    candidates.extend([
        ["xdg-terminal-exec", "bash", "-c", target_cmd],
        ["kitty", "bash", "-c", target_cmd],
        ["foot", "bash", "-c", target_cmd],
        ["ghostty", "-e", "bash", "-c", target_cmd],
        ["alacritty", "-e", "bash", "-c", target_cmd],
        ["x-terminal-emulator", "-e", "bash", "-c", target_cmd],
        ["gnome-terminal", "--", "bash", "-c", target_cmd],
    ])

    for cmd in candidates:
        bin_name = cmd[0]
        if shutil.which(bin_name):
            try:
                subprocess.Popen(cmd, start_new_session=True)
                return
            except Exception:
                continue

    try:
        subprocess.Popen(["bash", "-c", target_cmd], start_new_session=True)
    except Exception:
        pass


class HarnessISPApp(QObject):
    """Orchestrates HarnessISP Desktop Companion with direct CT 249 agy terminal launch."""

    def __init__(self) -> None:
        super().__init__()

        # 1. Core Services
        self.storage = StorageManager()
        self.storage.initialize()
        self.project_dir = Path(__file__).resolve().parent
        self.session = SessionManager()

        # 2. GUI Components (Companion Sphere + Pre-flight Approval Pill)
        self.ball = FloatingBallWidget()
        self.approval_pill = ApprovalPillWidget()
        self.tray = TrayManager(
            parent=self.ball,
            on_toggle_visible=self.toggle_ball,
            on_quit=self.quit,
        )

        # 3. Wiring: Click launches Kitty directly into CT 249 agy
        self.ball.clicked.connect(self.open_terminal)
        self.ball.file_dropped.connect(self.handle_file_drop)
        self.approval_pill.action_decided.connect(self.handle_approval_decision)

        # Telemetry Pill: Highlights canonical SSOT on CT 249
        self.ball.set_telemetry("⚡ CT 249: agy online  |  🛡️ Safe Mode ON  |  MikroTik 10.0.0.1")

        # Position widget initially on screen
        self.ball.move(120, 80)
        self.ball.show()

    def toggle_ball(self) -> None:
        """Toggle companion visibility."""
        if self.ball.isVisible():
            self.ball.hide()
            self.approval_pill.hide()
        else:
            self.ball.show()

    def open_terminal(self) -> None:
        """Launch terminal connected via SSH into CT 249 running agy."""
        self.ball.set_ball_state(BallState.PROCESSING)
        launch_native_terminal(self.project_dir)
        QTimer.singleShot(1500, lambda: self.ball.set_ball_state(BallState.IDLE_OK))

    # --- Coucou-inspired Context Dropping ---
    def handle_file_drop(self, file_path_str: str) -> None:
        """Analyze network files (.rsc, .log, .csv) dropped onto the companion."""
        path = Path(file_path_str)
        if not path.exists():
            return

        self.ball.set_ball_state(BallState.PROCESSING)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            self.ball.set_ball_state(BallState.ALERT)
            return

        # MikroTik Script / Backup Check (.rsc)
        if path.suffix in (".rsc", ".backup") or "/ip" in content:
            audit = FailsafeGuard.audit_mikrotik_script(content)
            if audit.level == "CRITICAL":
                self.ball.set_ball_state(BallState.ALERT)
                self.approval_pill.prompt(
                    command=f"Auditar e executar script {path.name} no CT 249",
                    risk_level=audit.level,
                    reason=audit.summary,
                    anchor_pos=self.ball.pos(),
                )
            else:
                self.ball.set_ball_state(BallState.IDLE_OK)
                self.open_terminal()
        else:
            self.ball.set_ball_state(BallState.IDLE_OK)
            self.open_terminal()

    def handle_approval_decision(self, action: str, command: str) -> None:
        """Callback when user clicks Safe-Mode, Force, or Abort in Approval Pill."""
        if action == "abort":
            self.ball.set_ball_state(BallState.IDLE_OK)
        elif action in ("safe_mode", "force"):
            self.ball.set_ball_state(BallState.PROCESSING)
            self.open_terminal()
            QTimer.singleShot(1500, lambda: self.ball.set_ball_state(BallState.IDLE_OK))

    def quit(self) -> None:
        QApplication.instance().quit()


def main() -> None:
    if "WAYLAND_DISPLAY" in os.environ and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("HarnessISP")
    app.setQuitOnLastWindowClosed(False)

    harness = HarnessISPApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
