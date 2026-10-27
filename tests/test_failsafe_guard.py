import pytest
from core.failsafe_guard import FailsafeGuard


def test_suicidal_firewall_detection():
    suicidal_script = """
    /ip firewall filter
    add action=drop chain=input comment="Bloquear tudo"
    """
    assessment = FailsafeGuard.audit_mikrotik_script(suicidal_script)

    assert assessment.level == "CRITICAL"
    assert assessment.safe_mode_required is True
    assert any("established" in r for r in assessment.reasons)


def test_safe_firewall_script():
    safe_script = """
    /ip firewall filter
    add action=accept chain=input connection-state=established,related
    add action=accept chain=input dst-port=22 protocol=tcp
    add action=drop chain=input
    """
    assessment = FailsafeGuard.audit_mikrotik_script(safe_script)

    assert assessment.level == "LOW"
    assert assessment.safe_mode_required is False


def test_linux_failsafe_iptables():
    dangerous_linux = "iptables -F && iptables -P INPUT DROP"
    assessment = FailsafeGuard.audit_linux_script(dangerous_linux)

    assert assessment.level == "CRITICAL"
    assert assessment.safe_mode_required is True
    assert assessment.suggested_rollback is not None
    assert "sleep 60" in assessment.suggested_rollback
