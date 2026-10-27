"""Google Antigravity CLI Bridge for HarnessISP.

Connects strictly to the official Google Antigravity CLI (agy) and Google Cloud
Gemini models (Gemini 3.8 Flash / Pro) with AGENTS.md governance.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import AsyncGenerator

from core.failsafe_guard import FailsafeGuard


def get_situational_context() -> str:
    """Reads AGENTS.md and gathers runtime host telemetry in an agnostic way."""
    current_host = socket.gethostname()
    repo_root = Path(__file__).resolve().parent.parent
    agents_md_path = repo_root / "AGENTS.md"

    agents_content = ""
    if agents_md_path.exists():
        try:
            agents_content = agents_md_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    telemetry = (
        f"• Host de Execução: {current_host}\n"
        f"• Motor de Cognição: Google Antigravity CLI (agy) com Google Gemini\n"
        f"• Diretório do Projeto: {repo_root}"
    )

    return (
        f"=== CONTRATO DE GOVERNANÇA (AGENTS.md) ===\n"
        f"{agents_content}\n"
        f"===========================================\n\n"
        f"=== TELEMETRIA DE AMBIENTE ===\n"
        f"{telemetry}\n"
        f"==============================\n"
    )


class AntigravityCLIBridge:
    """Direct interface to the official Google Antigravity CLI (agy)."""

    def __init__(self, binary_override: str | None = None) -> None:
        self.binary_path = binary_override or self.find_antigravity_binary()

    @staticmethod
    def find_antigravity_binary() -> str | None:
        for name in ("agy", "antigravity"):
            path = shutil.which(name)
            if path:
                return path

        candidates = [
            os.path.expanduser("~/.local/bin/agy"),
            os.path.expanduser("~/.gemini/antigravity-cli/bin/antigravity"),
            "/usr/local/bin/agy",
            "/usr/bin/agy",
        ]
        for candidate in candidates:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None

    def is_installed(self) -> bool:
        return self.binary_path is not None and os.path.exists(self.binary_path)

    def query_google_gemini(self, prompt: str, context: str | None = None) -> str | None:
        """Query Google Gemini models directly via Antigravity CLI (agy -p)."""
        bin_path = self.find_antigravity_binary()
        if not bin_path:
            return None

        repo_root = str(Path(__file__).resolve().parent.parent)
        env = dict(os.environ)
        env["PATH"] = f"{os.path.expanduser('~/.local/bin')}:{env.get('PATH', '')}"

        full_prompt = prompt
        if context:
            full_prompt = f"[Contexto de Topologia/Notas]:\n{context}\n\nPergunta:\n{prompt}"

        cmd = [bin_path, "-p", full_prompt]

        try:
            res = subprocess.run(
                cmd,
                cwd=repo_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            return None

        return None

    def generate_response(self, prompt: str, context: str | None = None) -> str:
        """Main entrypoint. Invokes Google Antigravity CLI or deterministic rule engine."""
        p_lower = prompt.lower().strip()

        # 1. Location & Identity Check (Universal & Agnostic)
        location_triggers = ("onde você está", "onde vc esta", "onde você roda", "onde vc roda", "onde voce esta", "onde esta", "onde está", "qual seu host", "qual o seu host")
        identity_triggers = ("quem é você", "quem é vc", "quem e voce", "quem e vc", "o que voce faz", "o que você faz", "ajuda", "help", "agents.md")

        if any(trig in p_lower for trig in location_triggers):
            current_host = socket.gethostname()
            return (
                f"📍 **Consciência Situacional do HarnessISP:**\n\n"
                f"• **Host Local:** `{current_host}` (Desktop Companion via PySide6)\n"
                f"• **Motor de IA Oficial:** Google Antigravity CLI (`agy`) com modelos **Google Gemini** (Nuvem)\n"
                f"• **Contrato de Governança:** Apontado para o **`AGENTS.md`** canônico do repositório\n"
                f"• **Ambiente:** Engenharia de Redes & NOC para ISPs\n\n"
                f"> Operando sob as diretrizes de blindagem anti-lockout, cofre seguro e cognição em nuvem Google Gemini."
            )

        if any(trig in p_lower for trig in identity_triggers):
            current_host = socket.gethostname()
            return (
                f"Olá! Eu sou o **HarnessISP**, assistente companion oficial operando com a **Google Antigravity CLI (`agy`)** "
                f"sob as regras do **`AGENTS.md`** no host `{current_host}`.\n\n"
                f"🛡️ **Pilares de Atuação:**\n"
                f"• **Google Gemini Engine:** Cognição avançada em nuvem para engenharia de telecomunicações.\n"
                f"• **Blindagem Anti-Lockout:** Safe Mode inegociável em roteadores MikroTik e servidores Linux.\n"
                f"• **Automação FTTH Multivendor:** Diagnósticos de sinal óptico (dBm) e perfis OLT (Huawei, ZTE, Fiberhome, Datacom).\n"
                f"• **Terminal Nativo no Clique:** Dê um clique no mascote para abrir a sessão interativa da `agy` no seu terminal!\n\n"
                f"Como posso ajudar na sua infraestrutura de rede hoje?"
            )

        # 2. Invoke Google Antigravity CLI (Primary Engine)
        gemini_resp = self.query_google_gemini(prompt, context)
        if gemini_resp:
            return gemini_resp

        # 3. Deterministic Local ISP Fallback (Offline safety only)
        return self._generate_local_isp_response(prompt)

    def _generate_local_isp_response(self, prompt: str) -> str:
        """Deterministic rule-based response generator for ISP NOC tasks."""
        p_lower = prompt.lower()

        if "bogon" in p_lower or "anti-ddos" in p_lower or "spoofing" in p_lower:
            return (
                "🛡️ **Regras de Proteção Bogon & Anti-Spoofing (MikroTik RouterOS):**\n\n"
                "```routeros\n"
                "/ip firewall filter\n"
                "add action=drop chain=input comment=\"Drop Bogon IPs na WAN\" in-interface-list=WAN src-address-list=BOGON_IPS\n"
                "add action=drop chain=forward comment=\"Drop Spoofing RFC1918 na WAN\" in-interface-list=WAN src-address=10.0.0.0/8\n"
                "```\n"
                "> **Importante:** Certifique-se de manter a regra `established,related` no topo da chain!"
            )

        if "mikrotik" in p_lower and ("validar" in p_lower or "script" in p_lower):
            assessment = FailsafeGuard.audit_mikrotik_script(prompt)
            return (
                f"🔍 **Auditoria Anti-Lockout MikroTik:**\n"
                f"• **Nível de Risco:** {assessment.level}\n"
                f"• **Motivo:** {'; '.join(assessment.reasons) if assessment.reasons else 'Nenhum risco detectado'}\n"
                f"• **Safe Mode Requerido:** {'Sim' if assessment.safe_mode_required else 'Não'}"
            )

        if "olt" in p_lower or "onu" in p_lower or "ftth" in p_lower or "sinal" in p_lower:
            return (
                "📶 **Comandos de Telemetria Óptica Multivendor:**\n\n"
                "• **Huawei:** `display ont optical-info <frame/slot/port> <ont-id>`\n"
                "• **ZTE:** `show pon power attenuation gpon-onu_<f/s/p>:<id>`\n"
                "• **Fiberhome:** `show onu optical-power <port> <onu-id>`\n\n"
                "> **Janela Operacional Recomendada:** -8.0 dBm a -27.0 dBm (Alarme Crítico: < -28.0 dBm)."
            )

        return (
            "⚡ **HarnessISP NOC Core:** Comando processado sob governança do `AGENTS.md`.\n"
            "Para operações críticas de roteamento e firewall em produção, "
            "recomenda-se sempre a ativação prévia do **Safe Mode** (`<safe>`)."
        )
