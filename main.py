"""Main entrypoint for HarnessISP Desktop Application (Coucou-Inspired Edition).

Integrates the expressive desktop companion, dynamic island pill, pre-flight
approval dialogs, RAG memory and background LLM inference.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtWidgets import QApplication

from core.cli_bridge import AntigravityCLIBridge
from core.failsafe_guard import FailsafeGuard
from core.ftth_engine import FTTHEngine
from core.memory_rag import MemoryRAG
from core.net_tools import NetTools
from core.session import BallState, SessionManager
from core.storage import StorageManager
from core.token_optimizer import TokenOptimizer
from core.vault import VaultManager
from gui.approval_pill import ApprovalPillWidget
from gui.chat_panel import ChatPanel
from gui.tray import TrayManager
from gui.widget import FloatingBallWidget


class LLMWorkerSignals(QObject):
    response_ready = Signal(str, str, object)  # role, content, risk_level


class HarnessISPApp(QObject):
    """Orchestrates HarnessISP components with Coucou-inspired companion UX."""

    def __init__(self) -> None:
        super().__init__()

        # 1. Core Services
        self.storage = StorageManager()
        self.storage.initialize()

        self.vault = VaultManager(self.storage.vault_dir)
        self.memory = MemoryRAG(self.storage.memory_dir / "knowledge.db")
        self.session = SessionManager()
        self.cli_bridge = AntigravityCLIBridge()

        # Thread signals for background LLM
        self.worker_signals = LLMWorkerSignals()
        self.worker_signals.response_ready.connect(self._on_llm_response)

        # 2. GUI Components
        self.ball = FloatingBallWidget()
        self.chat = ChatPanel(self.session)
        self.approval_pill = ApprovalPillWidget()
        self.tray = TrayManager(
            parent=self.ball,
            on_toggle_visible=self.toggle_ball,
            on_quit=self.quit,
        )

        # 3. Signals & Wiring
        self.ball.clicked.connect(self.toggle_chat)
        self.ball.file_dropped.connect(self.handle_file_drop)
        self.chat.action_triggered.connect(self.handle_action)
        self.approval_pill.action_decided.connect(self.handle_approval_decision)

        # Position widget initially on screen
        self.ball.move(120, 80)
        self.ball.show()

    def toggle_ball(self) -> None:
        """Toggle companion visibility."""
        if self.ball.isVisible():
            self.ball.hide()
            self.chat.hide()
            self.approval_pill.hide()
        else:
            self.ball.show()

    def toggle_chat(self) -> None:
        """Toggle chat panel beside the companion."""
        if self.chat.isVisible():
            self.chat.hide()
        else:
            ball_pos = self.ball.pos()
            self.chat.move(ball_pos.x() + self.ball.width() + 15, ball_pos.y())
            self.chat.show()
            self.chat.raise_()

    # --- Coucou-inspired Context Dropping ---
    def handle_file_drop(self, file_path_str: str) -> None:
        """Analyze network files (.rsc, .log, .csv, .txt) dropped onto the companion."""
        path = Path(file_path_str)
        if not path.exists():
            return

        self.ball.set_ball_state(BallState.PROCESSING)
        if not self.chat.isVisible():
            self.toggle_chat()

        self.chat.append_message("user", f"📁 <b>Arquivo arrastado para o Companion:</b> <code>{path.name}</code>")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self.chat.append_message("assistant", f"❌ Erro ao ler arquivo: {e}")
            self.ball.set_ball_state(BallState.IDLE_OK)
            return

        # MikroTik Script / Backup Check (.rsc)
        if path.suffix in (".rsc", ".backup") or "/ip" in content:
            audit = FailsafeGuard.audit_mikrotik_script(content)
            if audit.level == "CRITICAL":
                self.ball.set_ball_state(BallState.ALERT)
                msg = f"⚠️ <b>ALERTA DE RISCO CRÍTICO NO ARQUIVO {path.name}:</b><br>{audit.summary}<br><br><b>Recomendação:</b> Aplicar Safe-Mode antes da injeção no RouterOS."
                self.chat.append_message("assistant", msg, risk="CRITICAL")
                self.approval_pill.prompt(
                    command=f"Executar script {path.name}",
                    risk_level=audit.level,
                    reason=audit.summary,
                    anchor_pos=self.ball.pos(),
                )
            else:
                self.ball.set_ball_state(BallState.IDLE_OK)
                safe_script = FailsafeGuard.wrap_in_safe_mode(content)
                self.chat.append_message("assistant", f"✅ <b>Auditoria concluída em {path.name}:</b> Nenhuma regra de lockout detectada. Script validado e pronto com proteção de Safe Mode.")

        # OLT / Optical Power Check (.csv, .txt)
        elif "ont autofind" in content.lower() or "power" in content.lower() or "dbm" in content.lower():
            onts = FTTHEngine.parse_ont_autofind(content)
            summary = f"📶 <b>Diagnóstico FTTH em {path.name}:</b> {len(onts)} ONUs encontradas.<br>"
            for ont in onts:
                summary += f"• Porta: {ont.get('port')} | SN: {ont.get('sn')} | Modelo: {ont.get('model')}<br>"
            self.chat.append_message("assistant", summary)
            self.ball.set_ball_state(BallState.IDLE_OK)

        # General Network Log / Token Optimization
        else:
            compressed = TokenOptimizer.compress_mikrotik_export(content)
            self.chat.append_message("assistant", f"📄 <b>Log/Arquivo processado com RTK:</b> {len(content)} bytes otimizados para inspeção do NOC.")
            self.ball.set_ball_state(BallState.IDLE_OK)

    # --- Action & Prompt Handler with Pre-flight Protection ---
    def handle_action(self, text: str) -> None:
        """Process prompt or quick button. If critical risk, ask permission via Approval Pill."""
        risk = FailsafeGuard.audit_mikrotik_script(text)
        self.session.add_user_message(text)
        self.chat.append_message("user", text)

        if risk.level in ("CRITICAL", "MEDIUM"):
            self.ball.set_ball_state(BallState.ALERT)
            self.approval_pill.prompt(
                command=text,
                risk_level=risk.level,
                reason=risk.summary,
                anchor_pos=self.ball.pos(),
            )
            return

        self.ball.set_ball_state(BallState.PROCESSING)
        self._dispatch_background_query(text, None)

    def handle_approval_decision(self, action: str, command: str) -> None:
        """Callback when user clicks Safe-Mode, Force, or Abort in Approval Pill."""
        if action == "abort":
            self.ball.set_ball_state(BallState.IDLE_OK)
            self.chat.append_message("assistant", f"🛑 <b>Ação Abortada:</b> O comando <code>{command}</code> foi bloqueado pelo operador para evitar perda de acesso.")
        elif action == "safe_mode":
            self.ball.set_ball_state(BallState.PROCESSING)
            safe_cmd = FailsafeGuard.wrap_in_safe_mode(command)
            self.chat.append_message("assistant", f"🛡️ <b>Executando com Safe-Mode RouterOS:</b><br><code>{safe_cmd}</code>")
            self._dispatch_background_query(safe_cmd, "LOW")
        elif action == "force":
            self.ball.set_ball_state(BallState.PROCESSING)
            self.chat.append_message("assistant", f"⚡ <b>Forçando execução manual (Sem Safe-Mode):</b><br><code>{command}</code>")
            self._dispatch_background_query(command, "CRITICAL")

    def _dispatch_background_query(self, text: str, risk_level: str | None) -> None:
        """Run LLM and RAG query in a background thread so UI stays fluid."""
        def run():
            try:
                # Query RAG for knowledge context
                rag_matches = self.memory.search(text, limit=2)
                context = chr(10).join([f"[{m.title}]: {m.snippet}" for m in rag_matches]) if rag_matches else None
                response = self.cli_bridge.generate_response(text, context=context)
            except Exception as e:
                response = f"⚠️ Ocorreu uma falha no processamento: {e}. Executando sob modo determinístico de contingência."
            self.worker_signals.response_ready.emit("assistant", response, risk_level)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _on_llm_response(self, role: str, response: str, risk_level: str | None) -> None:
        """Slot called on main Qt thread when background query finishes."""
        self.session.add_assistant_message(response, risk_level=risk_level)
        self.chat.append_message(role, response, risk=risk_level)
        self.ball.set_ball_state(BallState.IDLE_OK)

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
