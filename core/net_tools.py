"""Deterministic Network Diagnostic Utilities for HarnessISP (Tool-First).

Runs local ICMP ping, traceroute, DNS lookups, and RDAP queries asynchronously.
"""

from __future__ import annotations

import asyncio
import shutil
import socket
from typing import Any

from core.token_optimizer import TokenOptimizer


class NetTools:
    """Runs deterministic local network checks before querying AI."""

    @staticmethod
    async def async_ping(host: str, count: int = 4) -> dict[str, Any]:
        """Execute system ping asynchronously and summarize output."""
        ping_bin = shutil.which("ping")
        if not ping_bin:
            return {"error": "Utilitário ping não encontrado no sistema."}

        cmd = [ping_bin, "-c", str(count), "-W", "2", host]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            raw = stdout.decode("utf-8", errors="replace")
            summary = TokenOptimizer.compress_ping(raw)
            summary["exit_code"] = proc.returncode
            return summary
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def async_dns_lookup(domain: str) -> dict[str, Any]:
        """Resolve IP addresses for domain/hostname."""
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.getaddrinfo(domain, None, proto=socket.IPPROTO_TCP)
            ips = list({info[4][0] for info in addr_info})
            return {"domain": domain, "ips": ips, "status": "RESOLVED"}
        except Exception as e:
            return {"domain": domain, "error": str(e), "status": "FAILED"}

    @staticmethod
    async def async_traceroute(host: str, max_hops: int = 15) -> dict[str, Any]:
        """Run traceroute asynchronously and summarize."""
        traceroute_bin = shutil.which("traceroute") or shutil.which("tracepath")
        if not traceroute_bin:
            return {"error": "Traceroute/tracepath não instalado."}

        cmd = [traceroute_bin, "-m", str(max_hops), host]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            raw = stdout.decode("utf-8", errors="replace")
            hops = TokenOptimizer.compress_traceroute(raw)
            return {"destination": host, "hops": hops}
        except Exception as e:
            return {"error": str(e)}
