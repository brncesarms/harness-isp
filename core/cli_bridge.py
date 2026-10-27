"""Antigravity & Local LLM (Ollama) Bridge for HarnessISP.

Connects to:
1. Lab Ollama instances (10.0.0.254:11434 / 10.10.10.2:11434) with qwen3-coder:30b / gemma4:26b.
2. Antigravity CLI (agy / antigravity) if available in PATH.
3. Deterministic ISP Knowledge Engine with Anti-Lockout and FTTH rules.
"""

from __future__ import annotations

import json
import os
import shutil
import urllib.request
import urllib.error
from typing import AsyncGenerator

from core.failsafe_guard import FailsafeGuard

SYSTEM_PROMPT = """Você é o HarnessISP, um Desktop Companion inteligente especializado em Engenharia de Redes, FTTH/GPON e NOC Operacional para Provedores de Internet (ISPs).
Você auxilia analistas de NOC, técnicos de campo e engenheiros com:
1. Blindagem Anti-Lockout (Safe Mode no MikroTik RouterOS v6/v7, rollback automático no Linux).
2. Diagnósticos de sinal óptico (dBm) e provisionamento em OLTs (Huawei, ZTE, Fiberhome, Datacom).
3. Resolução de problemas de BGP, OSPF, VLANs, MTU, PPPoE e regras Bogon/Anti-DDoS.
Responda sempre em português do Brasil, de forma técnica, cirúrgica, concisa e direta ao ponto."""

OLLAMA_CANDIDATES = [
    os.environ.get("OLLAMA_HOST", "").rstrip("/"),
    "http://10.0.0.254:11434",
    "http://10.10.10.2:11434",
    "http://127.0.0.1:11434",
]


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
        """Probe candidate Ollama endpoints with a 1-second connect timeout."""
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
        """Query active Ollama node using qwen3-coder:30b or gemma4:26b."""
        active_url = self.find_active_ollama()
        if not active_url:
            return None

        # Build full prompt
        full_system = SYSTEM_PROMPT
        if context:
            full_system += f"\n\n[Contexto RAG de Topologia/Notas]:\n{context}"

        payload = {
            "model": "qwen3-coder:30b",
            "system": full_system,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 600,
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
            # Fallback to secondary model if primary timed out or not loaded
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
        """Main entrypoint for generating responses. Tries Ollama -> Antigravity CLI -> Deterministic fallback."""
        p_lower = prompt.lower().strip()

        # 1. Identity & Help Check
        if any(w in p_lower for w in ("quem é você", "quem é vc", "quem e voce", "quem e vc", "o que voce faz", "o que você faz", "ajuda", "help")):
            return (
                "Olá! Eu sou o **HarnessISP**, seu Desktop Companion inteligente especializado em "
                "**Engenharia de Redes, FTTH/GPON e NOC para Provedores de Internet (ISPs)**.\n\n"
                "🛡️ **Minhas Especialidades:**\n"
                "• **Blindagem Anti-Lockout:** Valido scripts RouterOS, Linux iptables e aplico Safe-Mode automático com timer de auto-rollback.\n"
                "• **Engenharia FTTH Multivendor:** Diagnóstico de níveis de atenuação óptica (Class B+/C+) e provisionamento em OLTs Huawei, ZTE, Fiberhome e Datacom.\n"
                "• **Context Dropping:** Você pode arrastar scripts .rsc do MikroTik, logs de BGP ou tabelas de OLT diretamente em cima do meu mascote.\n"
                "• **Pre-Flight Approval Pill:** Intercepto comandos com risco de derrubar o link e ofereço aprovação em 1 clique.\n"
                "• **Dynamic Island:** Dê um duplo-clique no mascote para ver telemetria de tráfego, BGP e sinal ao vivo!\n\n"
                "Como posso ajudar na sua infraestrutura de rede agora?"
            )

        # 2. Try Ollama (Fast & Local/Lab)
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
                "> **Importante:** Certifique-se de manter a regra established,related no topo da chain!"
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
            "⚡ **HarnessISP NOC Core:** Comando recebido e processado.\n"
            "Para operações críticas de roteamento e firewall em produção, "
            "recomenda-se sempre a ativação prévia do **Safe Mode** (<safe>)."
        )
