"""FTTH & GPON Automation Engine for HarnessISP.

Supports discovery (autofind), optical diagnostics (dBm thresholds),
and provisioning scripts for Huawei, ZTE, Fiberhome, and Datacom OLTs.
"""

from __future__ import annotations

import re
from typing import Any


class FTTHEngine:
    """Specialized parser and provisioning assistant for GPON OLTs."""

    # Power thresholds (ITU-T G.984 class B+ and C+)
    MIN_RX_DBM = -27.0
    MAX_RX_DBM = -8.0

    @classmethod
    def evaluate_optical_signal(cls, rx_dbm: float, tx_dbm: float | None = None) -> dict[str, Any]:
        """Classify optical health based on standard PON attenuation ranges."""
        if rx_dbm < -30.0:
            status = "FIBRA_ROMPIDA_OU_ATENUACAO_EXTREMA"
            severity = "CRITICAL"
            advice = "Possível rompimento de fibra, conector sujo ou curvatura excessiva."
        elif rx_dbm < cls.MIN_RX_DBM:
            status = "ATENUACAO_ALTA"
            severity = "WARNING"
            advice = "Sinal baixo. Limpar conectores ópticos APC/UPC ou verificar fusões na CTO/CEO."
        elif rx_dbm > cls.MAX_RX_DBM:
            status = "SINAL_SATURADO"
            severity = "WARNING"
            advice = "Sinal muito forte (saturação do receptor óptico). Inserir atenuador óptico."
        else:
            status = "SINAL_NOMINAL"
            severity = "OK"
            advice = "Sinal óptico dentro da janela de operação ideal."

        return {
            "rx_dbm": rx_dbm,
            "tx_dbm": tx_dbm,
            "status": status,
            "severity": severity,
            "advice": advice,
        }

    @classmethod
    def parse_huawei_autofind(cls, raw_output: str) -> list[dict[str, Any]]:
        """Parse 'display ont autofind all' output from Huawei SmartAX OLT."""
        results = []
        # Matches tabular output: 1  0/1/2  4857544312345678 (HWTC-12345678)
        table_pattern = re.compile(
            r"^\s*\d+\s+(\d+/\d+/\d+)\s+([0-9A-Fa-f]{12,16}(?:\s*\([^)]+\))?)",
            re.MULTILINE,
        )
        for match in table_pattern.finditer(raw_output):
            results.append({
                "vendor": "Huawei",
                "fsp": match.group(1).strip(),
                "serial_number": match.group(2).strip(),
            })

        if not results:
            # Matches detailed key-value format: F/S/P : 0/1/2 ... Ont SN : 4857544312345678
            kv_pattern = re.compile(
                r"F/S/P\s*:\s*(\S+).*?Ont SN\s*:\s*([0-9A-Fa-f]+(?:\s*\([^)]+\))?)",
                re.DOTALL | re.IGNORECASE,
            )
            for match in kv_pattern.finditer(raw_output):
                results.append({
                    "vendor": "Huawei",
                    "fsp": match.group(1).strip(),
                    "serial_number": match.group(2).strip(),
                })
        return results

    @classmethod
    def parse_zte_uncfg(cls, raw_output: str) -> list[dict[str, Any]]:
        """Parse 'show gpon onu uncfg' output from ZTE C300/C320 OLT."""
        results = []
        # Matches: gpon-onu_1/1/1:1   ZTEG12345678   ...
        pattern = re.compile(r"(gpon-onu_\d+/\d+/\d+:\d+)\s+([A-Z0-9]{12,16})", re.IGNORECASE)
        for match in pattern.finditer(raw_output):
            onu_id = match.group(1).strip()
            sn = match.group(2).strip()
            results.append({
                "vendor": "ZTE",
                "onu_id": onu_id,
                "serial_number": sn,
            })
        return results

    @classmethod
    def generate_huawei_provision(
        cls, fsp: str, ont_id: int, sn: str, line_profile: str, srv_profile: str, vlan: int
    ) -> str:
        """Generate standard Huawei SmartAX provisioning script."""
        frame, slot, port = fsp.split("/")
        return (
            f"interface gpon {frame}/{slot}\n"
            f" ont add {port} {ont_id} sn-auth {sn} omci ont-lineprofile-name {line_profile} ont-srvprofile-name {srv_profile}\n"
            f"quit\n"
            f"service-port vlan {vlan} gpon {frame}/{slot}/{port} ont {ont_id} gemport 1 multi-service user-vlan {vlan}\n"
        )

    @classmethod
    def generate_zte_provision(
        cls, interface: str, onu_id: int, sn: str, tcont: int, profile: str, vlan: int
    ) -> str:
        """Generate ZTE C300/C320 provisioning script."""
        return (
            f"interface {interface}\n"
            f" onu {onu_id} type {profile} sn {sn}\n"
            f"exit\n"
            f"interface {interface}:{onu_id}\n"
            f" tcont {tcont} profile {profile}\n"
            f" gemport 1 tcont {tcont}\n"
            f" service-port 1 vport 1 user-vlan {vlan} vlan {vlan}\n"
            f"exit\n"
        )
