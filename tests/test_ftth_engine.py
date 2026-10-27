import pytest
from core.ftth_engine import FTTHEngine


def test_optical_signal_evaluation():
    nominal = FTTHEngine.evaluate_optical_signal(-19.5, 2.1)
    assert nominal["severity"] == "OK"

    critical_low = FTTHEngine.evaluate_optical_signal(-32.0, 1.5)
    assert critical_low["severity"] == "CRITICAL"
    assert "FIBRA_ROMPIDA" in critical_low["status"]

    saturated = FTTHEngine.evaluate_optical_signal(-6.0, 2.5)
    assert saturated["severity"] == "WARNING"
    assert saturated["status"] == "SINAL_SATURADO"


def test_parse_huawei_autofind():
    raw_huawei = """
    -------------------------------------------------------------------------
     Number  F/S/P   Ont SN                  Password
    -------------------------------------------------------------------------
     1       0/1/2   4857544312345678 (HWTC-12345678)
    -------------------------------------------------------------------------
    """
    found = FTTHEngine.parse_huawei_autofind(raw_huawei)
    assert len(found) == 1
    assert found[0]["fsp"] == "0/1/2"
    assert "4857544312345678" in found[0]["serial_number"]


def test_generate_huawei_provision():
    script = FTTHEngine.generate_huawei_provision(
        fsp="0/1/2", ont_id=5, sn="HWTC12345678", line_profile="LINE_1G", srv_profile="SRV_PPPOE", vlan=100
    )
    assert "interface gpon 0/1" in script
    assert "ont add 2 5 sn-auth HWTC12345678" in script
    assert "service-port vlan 100" in script
