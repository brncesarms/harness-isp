"""Anti-Lockout and Fail-Safe Guard (Zero Lockouts).

Protects network engineers from losing access to routers (MikroTik, Huawei, Cisco, Datacom)
and Linux distributions during network/firewall configuration.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class RiskAssessment(NamedTuple):
    level: str  # "LOW", "MEDIUM", "CRITICAL"
    reasons: list[str]
    safe_mode_required: bool
    suggested_rollback: str | None


class FailsafeGuard:
    """Detects suicidal network rules and enforces safe mode and rollbacks."""

    # Suicidal firewall patterns (matches action=drop and chain=input regardless of order)
    RE_INPUT_DROP = re.compile(r"(?=.*chain\s*=\s*input)(?=.*action\s*=\s*drop)", re.IGNORECASE)
    RE_ESTABLISHED_ACCEPT = re.compile(r"connection-state\s*=\s*(?:established|related)", re.IGNORECASE)
    RE_MGMT_PORT = re.compile(r"(?:22|8291|443|8728|2222)", re.IGNORECASE)

    # Interface/management disabling patterns
    RE_DISABLE_MGMT = re.compile(r"/interface\s+(?:disable|set\s+.*disabled\s*=\s*yes)\s+(?:ether1|bridge|mgmt|lan)", re.IGNORECASE)
    RE_MTU_CHANGE = re.compile(r"mtu\s*=\s*\d+", re.IGNORECASE)

    # Linux patterns
    RE_LINUX_IPTABLES_FLUSH = re.compile(r"iptables\s+(-F|-X|--flush|--delete-chain)", re.IGNORECASE)
    RE_LINUX_IPTABLES_DROP = re.compile(r"iptables\s+-P\s+(INPUT|FORWARD)\s+DROP", re.IGNORECASE)
    RE_NETPLAN_APPLY = re.compile(r"netplan\s+apply", re.IGNORECASE)

    @classmethod
    def audit_mikrotik_script(cls, script: str) -> RiskAssessment:
        """Analyze MikroTik RouterOS script for lockout risks."""
        reasons = []
        safe_mode = False
        level = "LOW"

        # Check for input drop without established/related
        has_input_drop = bool(cls.RE_INPUT_DROP.search(script))
        has_established = bool(cls.RE_ESTABLISHED_ACCEPT.search(script))

        if has_input_drop and not has_established:
            level = "CRITICAL"
            reasons.append("Regra 'action=drop' detectada na chain 'input' SEM regra anterior de 'established,related' permitida. Risco Imediato de Perda de Acesso!")
            safe_mode = True

        if cls.RE_DISABLE_MGMT.search(script):
            level = "CRITICAL"
            reasons.append("Comando detectado desativando interface primária/bridge de gerência (ether1/bridge/lan).")
            safe_mode = True

        if cls.RE_MTU_CHANGE.search(script):
            if level != "CRITICAL":
                level = "MEDIUM"
            reasons.append("Alteração de MTU identificada. Risco de queda transitória ou flap de OSPF/BGP/MPLS.")
            safe_mode = True

        if "/routing/bgp" in script or "/ip/route" in script or "gateway=" in script:
            if level == "LOW":
                level = "MEDIUM"
            reasons.append("Alteração em tabelas de rotas ou sessões BGP.")
            safe_mode = True

        rollback = None
        if safe_mode:
            rollback = "Use obrigatoriamente <safe> mode no MikroTik (Ctrl+X no terminal) ou execute via script com auto-rollback."

        return RiskAssessment(
            level=level,
            reasons=reasons or ["Operação segura. Nenhuma regra de lockout identificada."],
            safe_mode_required=safe_mode,
            suggested_rollback=rollback,
        )

    @classmethod
    def audit_linux_script(cls, script: str) -> RiskAssessment:
        """Analyze Linux bash/network script for lockout risks."""
        reasons = []
        level = "LOW"
        safe_mode = False

        if cls.RE_LINUX_IPTABLES_FLUSH.search(script) or cls.RE_LINUX_IPTABLES_DROP.search(script):
            level = "CRITICAL"
            reasons.append("Iptables flush ou política padrão DROP detectada sem garantia de keepalive SSH. Risco crítico de bloqueio total!")
            safe_mode = True

        if cls.RE_NETPLAN_APPLY.search(script):
            if level != "CRITICAL":
                level = "MEDIUM"
            reasons.append("Uso de 'netplan apply' direto detectado. Recomendado usar 'netplan try' com timeout automático.")
            safe_mode = True

        if "sshd_config" in script:
            reasons.append("Alteração de sshd_config. Mandatório rodar 'sshd -t' antes do restart e manter terminal aberto.")
            if level != "CRITICAL":
                level = "MEDIUM"

        rollback = None
        if safe_mode:
            rollback = (
                "Execute com timer de auto-reversão temporizada em background:\n"
                "  iptables-save > /tmp/iptables.bak\n"
                "  (sleep 60 && iptables-restore < /tmp/iptables.bak) &\n"
                "  TIMER_PID=$!\n"
                "  # aplique as regras aqui\n"
                "  # se a conexão continuar ativa, execute: kill $TIMER_PID\n"
            )

        return RiskAssessment(
            level=level,
            reasons=reasons or ["Script Linux seguro."],
            safe_mode_required=safe_mode,
            suggested_rollback=rollback,
        )

    @classmethod
    def wrap_with_safe_mode(cls, script: str, vendor: str = "mikrotik") -> str:
        """Inject safe mode instructions or wrappers around commands."""
        vendor_lower = vendor.lower()
        if "mikrotik" in vendor_lower:
            header = "# --- [HARNESS-ISP SAFE MODE ENFORCED] ---\n"
            header += "# Pressione Ctrl+X no WinBox/Terminal para ativar o Safe Mode antes de colar.\n"
            return header + script
        if "cisco" in vendor_lower or "huawei" in vendor_lower or "datacom" in vendor_lower:
            header = "# --- [HARNESS-ISP COMMIT CONFIRMED ENFORCED] ---\n"
            header += "# commit confirmed 5\n"
            return header + script
        return script
