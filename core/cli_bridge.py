"""Antigravity CLI Bridge for HarnessISP.

Connects to the local or cloud Antigravity CLI (agy / antigravity).
Provides streaming output, auto-discovery of binary, and safe ISP fallback.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from typing import AsyncGenerator

from core.failsafe_guard import FailsafeGuard


class AntigravityCLIBridge:
    """Interface to communicate with Antigravity CLI."""

    def __init__(self, binary_override: str | None = None) -> None:
        self.binary_path = binary_override or self.find_antigravity_binary()

    @staticmethod
    def find_antigravity_binary() -> str | None:
        """Locate agy or antigravity binary in PATH or default locations."""
        for name in ("antigravity", "agy"):
            path = shutil.which(name)
            if path:
                return path

        # Check default user installations
        candidate = os.path.expanduser("~/.gemini/antigravity-cli/bin/antigravity")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        return None

    def is_installed(self) -> bool:
        """Check whether Antigravity CLI binary exists."""
        return self.binary_path is not None and os.path.exists(self.binary_path)

    async def query_streaming(
        self, prompt: str, context: str | None = None
    ) -> AsyncGenerator[str, None]:
        """Query the CLI or provide specialized deterministic ISP assistance."""
        if not self.is_installed():
            # Specialized local ISP knowledge fallback
            yield "[Motor Antigravity Offline - Modo Determinístico ISP Ativo]\n\n"
            response = self._generate_local_isp_response(prompt)
            for chunk in response.split(" "):
                yield chunk + " "
                await asyncio.sleep(0.01)
            return

        # Real CLI execution if installed
        cmd = [self.binary_path, "run", "--prompt", prompt]
        if context:
            cmd.extend(["--context", context])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            if proc.stdout:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    yield line.decode("utf-8", errors="replace")

            await proc.wait()
        except Exception as e:
            yield f"\n[Erro ao executar Antigravity CLI: {e}]\n"

    def _generate_local_isp_response(self, prompt: str) -> str:
        """Deterministic rule-based response generator for ISP NOC tasks."""
        p_lower = prompt.lower()

        if "bogon" in p_lower or "anti-ddos" in p_lower:
            return (
                "Aqui está a lista de proteção contra pacotes Bogon e Spoofing para MikroTik:\n\n"
                "/ip firewall filter\n"
                "add action=drop chain=input comment=\"Bloquear Bogon IPs\" in-interface-list=WAN src-address-list=BOGON_IPS\n"
                "add action=drop chain=forward comment=\"Bloquear Spoofing RFC1918 na WAN\" in-interface-list=WAN src-address=10.0.0.0/8\n\n"
                "Lembrete: Certifique-se de manter a regra de established,related no topo da chain!"
            )

        if "mikrotik" in p_lower and "validar" in p_lower:
            assessment = FailsafeGuard.audit_mikrotik_script(prompt)
            return (
                f"Resultado da Auditoria Anti-Lockout:\n"
                f"- Nível de Risco: {assessment.level}\n"
                f"- Detalhes: {'; '.join(assessment.reasons)}\n"
                f"- Safe Mode Requerido: {assessment.safe_mode_required}\n"
            )

        if "olt" in p_lower or "onu" in p_lower or "ftth" in p_lower:
            return (
                "Para diagnóstico óptico em OLT Huawei, execute:\n"
                "  display ont optical-info <frame/slot/port> <ont-id>\n\n"
                "Para OLT ZTE:\n"
                "  show pon power attenuation gpon-onu_<f/s/p>:<id>\n\n"
                "Janela operacional recomendada: -8.0 dBm a -27.0 dBm."
            )

        return (
            "Comando de rede recebido e processado. Para segurança em produção, "
            "sempre execute sob Safe Mode (<safe>) ou com commit confirmed."
        )
