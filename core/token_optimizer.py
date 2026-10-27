"""Token Economy Hook & Deterministic Summarizer (RTK Pattern).

Parses verbose router, ping, traceroute, and OLT outputs to condense
information before passing to the LLM, reducing token consumption and noise.
"""

from __future__ import annotations

import re
from typing import Any

import jc


class TokenOptimizer:
    """Compresses verbose network CLI diagnostic outputs."""

    @staticmethod
    def compress_ping(raw_output: str) -> dict[str, Any]:
        """Summarize ping results into sent/received/loss/rtt."""
        try:
            parsed = jc.parse("ping", raw_output)
            return {
                "destination": parsed.get("destination"),
                "packets_transmitted": parsed.get("packets_transmitted"),
                "packets_received": parsed.get("packets_received"),
                "packet_loss_percent": parsed.get("packet_loss_percent"),
                "round_trip_ms": {
                    "min": parsed.get("round_trip_ms_min"),
                    "avg": parsed.get("round_trip_ms_avg"),
                    "max": parsed.get("round_trip_ms_max"),
                    "stddev": parsed.get("round_trip_ms_stddev"),
                },
            }
        except Exception:
            return {"raw_summary": raw_output.strip().splitlines()[-2:]}

    @staticmethod
    def compress_traceroute(raw_output: str) -> list[dict[str, Any]]:
        """Summarize traceroute to hop numbers, hosts and latencies."""
        try:
            parsed = jc.parse("traceroute", raw_output)
            hops = []
            for hop in parsed.get("hops", []):
                hops.append({
                    "hop": hop.get("hop"),
                    "ip": hop.get("ip"),
                    "host": hop.get("host"),
                    "avg_ms": hop.get("avg_ms") or hop.get("rtt"),
                })
            return hops
        except Exception:
            return [{"line": line.strip()} for line in raw_output.splitlines() if line.strip()][:15]

    @staticmethod
    def compress_bgp_summary(raw_output: str) -> dict[str, Any]:
        """Summarize BGP peers: total peers, up/established, down, prefixes."""
        peers = []
        down_peers = []

        # Split into blocks by BGP neighbor or iterate
        # Matches patterns like: BGP neighbor is 10.0.0.2 ... BGP state = Active
        blocks = re.split(r"(?:BGP neighbor is|peer:)", raw_output, flags=re.IGNORECASE)
        for block in blocks:
            ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", block)
            if ip_match:
                ip = ip_match.group(1)
                peers.append(ip)
                # Check if state in this block is down/idle/active
                is_down = bool(re.search(r"(?:state\s*=\s*|status\s*[:=]\s*)(?:idle|active|down|connect)", block, re.IGNORECASE))
                if is_down:
                    down_peers.append({"peer": ip, "detail": block.strip().splitlines()[0]})

        if not peers:
            # Fallback for single line tabular MikroTik / FRR
            for line in raw_output.splitlines():
                ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                if ip_match:
                    ip = ip_match.group(1)
                    peers.append(ip)
                    if any(k in line.lower() for k in ("idle", "active", "down", "connect")):
                        down_peers.append({"peer": ip, "detail": line.strip()})

        return {
            "total_peers_detected": len(peers),
            "healthy": len(down_peers) == 0,
            "down_peers_count": len(down_peers),
            "down_peers": down_peers,
            "summary_snippet": [l.strip() for l in raw_output.splitlines() if l.strip()][:10],
        }

    @staticmethod
    def compress_optical_power(raw_output: str) -> list[dict[str, Any]]:
        """Extract RX and TX power and flag attenuation anomalies."""
        results = []
        # Match patterns like: RX: -21.4 dBm or RX Power: -19.2dBm
        rx_matches = re.finditer(r"(?:rx|receive)[\s\w]*[:=]\s*(-?\d+\.?\d*)\s*(?:dbm)?", raw_output, re.IGNORECASE)
        tx_matches = re.finditer(r"(?:tx|transmit)[\s\w]*[:=]\s*(-?\d+\.?\d*)\s*(?:dbm)?", raw_output, re.IGNORECASE)

        rx_values = [float(m.group(1)) for m in rx_matches]
        tx_values = [float(m.group(1)) for m in tx_matches]

        for i, rx in enumerate(rx_values):
            tx = tx_values[i] if i < len(tx_values) else None
            # Standard GPON acceptable window: -8 dBm to -27 dBm
            status = "CRITICAL_LOW" if rx < -27.0 else ("CRITICAL_HIGH" if rx > -8.0 else "NOMINAL")
            results.append({
                "index": i + 1,
                "rx_dbm": rx,
                "tx_dbm": tx,
                "status": status,
            })
        return results

    @classmethod
    def optimize_text(cls, text: str, max_lines: int = 50) -> str:
        """Generic fallback token compressor: truncates middle with marker."""
        lines = text.splitlines()
        if len(lines) <= max_lines:
            return text
        head = lines[: max_lines // 2]
        tail = lines[- (max_lines // 2) :]
        omitted = len(lines) - len(head) - len(tail)
        return "\n".join(head) + f"\n... [{omitted} lines compressed by RTK] ...\n" + "\n".join(tail)
