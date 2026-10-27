"""Main entrypoint for HarnessISP Desktop Sentinela (NOC HUD).

Acts as a living desktop sentry and pre-flight HUD on the workstation,
launching the user's native terminal running the official Google Antigravity CLI (agy).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path


try:
    from PySide6.QtCore import QObject, QPoint, QTimer, Signal
    from PySide6.QtWidgets import QApplication

    from core.failsafe_guard import FailsafeGuard
    from core.session import BallState, SessionManager
    from core.storage import StorageManager
    from gui.approval_pill import ApprovalPillWidget
    from gui.tray import TrayManager
    from gui.widget import FloatingBallWidget
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    QObject = object  # type: ignore


def check_display_environment() -> None:
    """Check if graphical display server is available before loading Qt."""
    print("\n⚡ HarnessISP Desktop Sentinela (NOC HUD)")
    print("━" * 60)
    print("⚠️  Nenhum servidor gráfico detectado (ambiente headless / SSH).")
    print("ℹ️  O HUD Sentinela foi concebido para rodar no seu Desktop físico (Omarchy / Hyprland).")
    print("\n👉 Para interagir com o agente neste terminal:")
    print("   python3 cli.py chat")
    print("   ou")
    print("   agy\n")
    sys.exit(0)


def launch_native_terminal(project_dir: Path | None = None) -> None:
    """Launches default terminal directly into the agy CLI session."""
    cwd = str(project_dir or Path(__file__).resolve().parent)
    current_host = socket.gethostname()
    default_remote = "harness-isp" if current_host not in ("harness-isp",) else None
    remote_host = os.environ.get("HARNESS_REMOTE_HOST", default_remote)

    if remote_host:
        target_cmd = f"ssh -t {remote_host} 'cd ~/harness-isp && agy'"
    else:
        target_cmd = f"cd {cwd} && agy"

    term = os.environ.get("TERMINAL")
    candidates: list[list[str]] = []
    if term:
        candidates.append([term, "-e", "bash", "-c", target_cmd])

    candidates.extend([
        ["xdg-terminal-exec", "bash", "-c", target_cmd],
        ["kitty", "--directory", cwd, "bash", "-c", target_cmd],
        ["foot", "-D", cwd, "bash", "-c", target_cmd],
        ["ghostty", f"--working-directory={cwd}", "-e", "bash", "-c", target_cmd],
        ["alacritty", "--working-directory", cwd, "-e", "bash", "-c", target_cmd],
        ["x-terminal-emulator", "-e", "bash", "-c", target_cmd],
        ["gnome-terminal", f"--working-directory={cwd}", "--", "bash", "-c", target_cmd],
        ["konsole", "--workdir", cwd, "-e", "bash", "-c", target_cmd],
    ])

    for cmd in candidates:
        bin_name = cmd[0]
        if shutil.which(bin_name):
            try:
                subprocess.Popen(cmd, cwd=cwd, start_new_session=True)
                return
            except Exception:
                continue

    try:
        subprocess.Popen(["bash", "-c", target_cmd], cwd=cwd, start_new_session=True)
    except Exception:
        pass


class HarnessISPApp(QObject):
    """Orchestrates HarnessISP Desktop Companion with direct agy terminal launch."""

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

        # 3. Wiring: Click launches default system terminal running agy
        self.ball.clicked.connect(self.open_terminal)
        self.ball.file_dropped.connect(self.handle_file_drop)
        self.approval_pill.action_decided.connect(self.handle_approval_decision)

        # Telemetry Pill: Live NOC Status
        self.ball.set_telemetry("⚡ HarnessISP: agy online  |  🛡️ Safe Mode ON  |  NOC Ready")

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
        """Launch system terminal running Google Antigravity CLI."""
        self.ball.set_ball_state(BallState.PROCESSING)
        launch_native_terminal(self.project_dir)
        QTimer.singleShot(1500, lambda: self.ball.set_ball_state(BallState.IDLE_OK))

    # --- Context Dropping (NOC Script & Log Ingestion) ---
    def handle_file_drop(self, file_path_str: str) -> None:
        """Analyze network files (.rsc, .log, .csv) dropped onto the sentinela."""
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
                    command=f"Auditar e executar script {path.name}",
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
    has_display = bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"))
    if not HAS_GUI or not has_display:
        check_display_environment()

    if "WAYLAND_DISPLAY" in os.environ and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("HarnessISP")
    app.setQuitOnLastWindowClosed(False)

    harness = HarnessISPApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
