"""Main entrypoint for HarnessISP Desktop Application (Coucou-Inspired Edition).

Integrates the expressive desktop companion, dynamic island pill, pre-flight
approval dialogs, and native system terminal launch on click.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtWidgets import QApplication

from core.failsafe_guard import FailsafeGuard
from core.ftth_engine import FTTHEngine
from core.memory_rag import MemoryRAG
from core.session import BallState, SessionManager
from core.storage import StorageManager
from core.token_optimizer import TokenOptimizer
from core.vault import VaultManager
from gui.approval_pill import ApprovalPillWidget
from gui.tray import TrayManager
from gui.widget import FloatingBallWidget


def launch_native_terminal(project_dir: Path) -> None:
    """Launches the user's default system terminal with the interactive HarnessISP shell."""
    cwd = str(project_dir)
    script_cmd = f"cd {cwd} && source .venv/bin/activate 2>/dev/null; python3 cli.py chat || bash"

    term = os.environ.get("TERMINAL")
    candidates: list[list[str]] = []
    if term:
        candidates.append([term, "-e", "bash", "-c", script_cmd])

    candidates.extend([
        ["xdg-terminal-exec", "bash", "-c", script_cmd],
        ["kitty", "--directory", cwd, "bash", "-c", script_cmd],
        ["foot", "-D", cwd, "bash", "-c", script_cmd],
        ["ghostty", f"--working-directory={cwd}", "-e", "bash", "-c", script_cmd],
        ["alacritty", "--working-directory", cwd, "-e", "bash", "-c", script_cmd],
        ["x-terminal-emulator", "-e", "bash", "-c", script_cmd],
        ["gnome-terminal", f"--working-directory={cwd}", "--", "bash", "-c", script_cmd],
        ["konsole", "--workdir", cwd, "-e", "bash", "-c", script_cmd],
        ["xfce4-terminal", f"--working-directory={cwd}", "-e", "bash", "-c", script_cmd],
    ])

    for cmd in candidates:
        bin_name = cmd[0]
        if shutil.which(bin_name):
            try:
                subprocess.Popen(cmd, cwd=cwd, start_new_session=True)
                return
            except Exception:
                continue

    # Fallback to direct bash
    try:
        subprocess.Popen(["bash", "-c", script_cmd], cwd=cwd, start_new_session=True)
    except Exception:
        pass


class HarnessISPApp(QObject):
    """Orchestrates HarnessISP Desktop Companion with native terminal integration."""

    def __init__(self) -> None:
        super().__init__()

        # 1. Core Services
        self.storage = StorageManager()
        self.storage.initialize()
        self.project_dir = Path(__file__).resolve().parent

        self.vault = VaultManager(self.storage.vault_dir)
        self.memory = MemoryRAG(self.storage.memory_dir / "knowledge.db")
        self.session = SessionManager()

        # 2. GUI Components (Companion Sphere + Pre-flight Approval Pill)
        self.ball = FloatingBallWidget()
        self.approval_pill = ApprovalPillWidget()
        self.tray = TrayManager(
            parent=self.ball,
            on_toggle_visible=self.toggle_ball,
            on_quit=self.quit,
        )

        # 3. Wiring: Click opens the DEFAULT SYSTEM TERMINAL
        self.ball.clicked.connect(self.open_terminal)
        self.ball.file_dropped.connect(self.handle_file_drop)
        self.approval_pill.action_decided.connect(self.handle_approval_decision)

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
        """Launch native system terminal (Kitty/Ghostty/Foot/XDG) on companion click."""
        self.ball.set_ball_state(BallState.PROCESSING)
        launch_native_terminal(self.project_dir)
        QTimer.singleShot(1500, lambda: self.ball.set_ball_state(BallState.IDLE_OK))

    # --- Coucou-inspired Context Dropping ---
    def handle_file_drop(self, file_path_str: str) -> None:
        """Analyze network files (.rsc, .log, .csv, .txt) dropped onto the companion."""
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
                    command=f"Executar script {path.name}",
                    risk_level=audit.level,
                    reason=audit.summary,
                    anchor_pos=self.ball.pos(),
                )
            else:
                self.ball.set_ball_state(BallState.IDLE_OK)
                # Opens native terminal with the validated safe script
                safe_script = FailsafeGuard.wrap_in_safe_mode(content)
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
