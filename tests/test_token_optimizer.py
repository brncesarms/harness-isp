import pytest
from core.token_optimizer import TokenOptimizer


def test_compress_optical_power():
    sample_output = """
    Optical Power details:
    RX optical power: -21.4 dBm
    TX optical power: 2.3 dBm
    RX optical power: -29.8 dBm
    TX optical power: 1.8 dBm
    """
    results = TokenOptimizer.compress_optical_power(sample_output)

    assert len(results) == 2
    assert results[0]["rx_dbm"] == -21.4
    assert results[0]["status"] == "NOMINAL"
    assert results[1]["rx_dbm"] == -29.8
    assert results[1]["status"] == "CRITICAL_LOW"


def test_compress_bgp_summary():
    bgp_output = """
    BGP neighbor is 192.168.10.1, remote AS 65000, external link
      BGP state = Established, up for 2d04h
    BGP neighbor is 10.0.0.2, remote AS 65001, external link
      BGP state = Active
    """
    summary = TokenOptimizer.compress_bgp_summary(bgp_output)

    assert summary["total_peers_detected"] == 2
    assert summary["healthy"] is False
    assert summary["down_peers_count"] == 1
    assert summary["down_peers"][0]["peer"] == "10.0.0.2"


def test_optimize_text():
    long_text = "\n".join(f"line {i}" for i in range(100))
    compressed = TokenOptimizer.optimize_text(long_text, max_lines=20)

    assert "[80 lines compressed by RTK]" in compressed


def test_native_rtk_integration():
    assert TokenOptimizer.has_native_rtk() is True
    out = TokenOptimizer.run_rtk_command(["echo", "hello rtk"])
    assert "hello rtk" in out
