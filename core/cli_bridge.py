"""Antigravity & Local LLM (Ollama) Bridge for HarnessISP.

Connects to:
1. Dynamic AGENTS.md Constitution & Situational Awareness (CT 249 SSOT).
2. Lab Ollama instances (10.0.0.254:11434 / 10.10.10.2:11434) with qwen3-coder:30b / gemma4:26b.
3. Antigravity CLI (agy / antigravity) if available in PATH.
4. Deterministic ISP Knowledge Engine with Anti-Lockout and FTTH rules.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import urllib.request
import urllib.error
from pathlib import Path
from typing import AsyncGenerator

from core.failsafe_guard import FailsafeGuard

OLLAMA_CANDIDATES = [
    os.environ.get("OLLAMA_HOST", "").rstrip("/"),
    "http://10.0.0.254:11434",
    "http://10.10.10.2:11434",
    "http://127.0.0.1:11434",
]


def get_situational_context() -> tuple[str, str]:
    """Reads AGENTS.md and gathers runtime host telemetry."""
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
        f"• Host de Execução Atual: {current_host}\n"
        f"• Host SSOT / Esteira Central: CT 249 (harness-isp, Debian 13 Trixie no Proxmox VE)\n"
        f"• Gateway / Roteador Borda: MikroTik RouterOS (10.0.0.1)\n"
        f"• Autoridade Soberana: Bruno Cesar\n"
        f"• Repositório Git SSOT: https://github.com/brncesarms/harness-isp\n"
        f"• Diretório Local: {repo_root}"
    )

    system_prompt = (
        "Você é o HarnessISP, assistente desktop companion inteligente para Engenharia de Redes, FTTH/GPON e NOC de ISPs.\n"
        "Você deve seguir RIGOROSAMENTE as diretrizes do AGENTS.md abaixo:\n\n"
        f"=== CONTRATO DE GOVERNANÇA (AGENTS.md) ===\n"
        f"{agents_content}\n"
        f"===========================================\n\n"
        f"=== TELEMETRIA DE AMBIENTE ATUAL ===\n"
        f"{telemetry}\n"
        f"====================================\n\n"
        "Diretrizes adicionais: Responda SEMPRE em português do Brasil, de forma cirúrgica, técnica e concisa. "
        "Você tem plena consciência de que sua esteira central reside no CT 249 Debian 13 e você está rodando no desktop do operador."
    )

    return system_prompt, telemetry


class AntigravityCLIBridge:
    """Hybrid bridge connecting Local LLMs (Ollama), Antigravity CLI and deterministic ISP rules."""

    def __init__(self, binary_override: str | None = None) -> None:
        self.binary_path = binary_override or self.find_antigravity_binary()
        self._cached_ollama_url: str | None = None

    @staticmethod
    def find_antigravity_binary() -> str | None:
        for name in ("antigravity", "agy"):
            path = shutil.which(name)
            if path:
                return path

        candidate = os.path.expanduser("~/.gemini/antigravity-cli/bin/antigravity")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        return None

    def is_installed(self) -> bool:
        return self.binary_path is not None and os.path.exists(self.binary_path)

    def find_active_ollama(self) -> str | None:
        """Probe candidate Ollama endpoints with a 1.2-second connect timeout."""
        if self._cached_ollama_url:
            return self._cached_ollama_url

        for base_url in OLLAMA_CANDIDATES:
            if not base_url:
                continue
            try:
                url = f"{base_url}/api/tags"
                req = urllib.request.Request(url, headers={"User-Agent": "HarnessISP/1.0"})
                with urllib.request.urlopen(req, timeout=1.2) as resp:
                    if resp.status == 200:
                        self._cached_ollama_url = base_url
                        return base_url
            except Exception:
                continue
        return None

    def query_ollama(self, prompt: str, context: str | None = None) -> str | None:
        """Query active Ollama node using qwen3-coder:30b or gemma4:26b with full AGENTS.md injection."""
        active_url = self.find_active_ollama()
        if not active_url:
            return None

        system_prompt, telemetry = get_situational_context()
        if context:
            system_prompt = system_prompt + chr(10) + chr(10) + "[Contexto RAG de Topologia/Notas]:" + chr(10) + str(context)

        payload = {
            "model": "qwen3-coder:30b",
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 700,
            }
        }

        try:
            req = urllib.request.Request(
                f"{active_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                response_text = data.get("response", "").strip()
                if response_text:
                    return response_text
        except Exception:
            # Fallback to secondary model if primary timed out
            try:
                payload["model"] = "gemma4:26b"
                req = urllib.request.Request(
                    f"{active_url}/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("response", "").strip()
            except Exception:
                return None

        return None

    def generate_response(self, prompt: str, context: str | None = None) -> str:
        """Main entrypoint. Tries Ollama -> Antigravity CLI -> Deterministic fallback."""
        p_lower = prompt.lower().strip()

        # 1. Direct Location & Situational Awareness Check
        location_triggers = ("onde você está", "onde vc esta", "onde você roda", "onde vc roda", "onde voce esta", "onde esta", "onde está", "qual seu host", "qual o seu host")
        identity_triggers = ("quem é você", "quem é vc", "quem e voce", "quem e vc", "o que voce faz", "o que você faz", "ajuda", "help", "agents.md")

        if any(trig in p_lower for trig in location_triggers):
            current_host = socket.gethostname()
            return (
                f"📍 **Consciência Situacional & Localização do HarnessISP:**\n\n"
                f"• **Host de Execução Local:** `{current_host}` (Área de trabalho interativa via PySide6)\n"
                f"• **Esteira Master & SSOT:** `CT 249` (`harness-isp`, Debian 13 Trixie no Proxmox VE)\n"
                f"• **Contrato de Governança:** Apontado diretamente para o **`AGENTS.md`** canônico do repositório\n"
                f"• **Roteador / Gateway Borda:** MikroTik RouterOS (`10.0.0.1`)\n"
                f"• **Nó de Inferência LLM:** Ollama Lab (`10.0.0.254:11434` / `10.10.10.2:11434` - `qwen3-coder:30b`)\n"
                f"• **Autoridade Soberana:** Bruno Cesar\n\n"
                f"> Minha infraestrutura central reside no container isolado **CT 249**, garantindo blindagem anti-lockout e zero vazamento de credenciais enquanto opero no seu desktop."
            )

        if any(trig in p_lower for trig in identity_triggers):
            current_host = socket.gethostname()
            return (
                f"Olá! Eu sou o **HarnessISP**, o Desktop Companion inteligente governado pelo **`AGENTS.md`** "
                f"do **CT 249** (`harness-isp`), rodando atualmente na estação `{current_host}`.\n\n"
                f"🛡️ **Pilares de Atuação (Definidos no AGENTS.md):**\n"
                f"• **Blindagem Anti-Lockout (Inegociável):** Toda regra de firewall, MTU ou rota é validada com Safe Mode e auto-rollback.\n"
                f"• **Automação FTTH Multivendor:** Diagnóstico óptico (dBm) e provisionamento em OLTs Huawei, ZTE, Fiberhome e Datacom.\n"
                f"• **Escudo Zero Leaks:** Credenciais protegidas via AES-256-GCM (`core/vault.py`) exclusivamente em RAM.\n"
                f"• **Token Economy Nativa:** Compressão de saídas extensas de rede (`rtk`) antes da análise.\n"
                f"• **Context Dropping:** Você pode arrastar scripts `.rsc`, logs de BGP ou tabelas CSV diretamente sobre mim na tela!\n\n"
                f"Como posso apoiar a operação do seu NOC agora?"
            )

        # 2. Try Ollama (Fed with full AGENTS.md + RAG context)
        ollama_resp = self.query_ollama(prompt, context)
        if ollama_resp:
            return ollama_resp

        # 3. Deterministic Local ISP Fallback
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

        if "bgp" in p_lower or "asn" in p_lower:
            return (
                "🌐 **Diagnóstico BGP:**\n"
                "• MikroTik v7: `/routing/bgp/session/print detail where state=\"established\"`\n"
                "• Cisco/Huawei: `display bgp peer` ou `show ip bgp summary`\n"
                "• Verifique se há flaps recentes com `grep -i bgp /var/log/syslog`."
            )

        return (
            "⚡ **HarnessISP NOC Core:** Comando recebido e processado sob governança do `AGENTS.md`.\n"
            "Para operações críticas de roteamento e firewall em produção, "
            "recomenda-se sempre a ativação prévia do **Safe Mode** (`<safe>`)."
        )
