import pytest
from core.memory_rag import MemoryRAG


def test_sqlite_fts5_rag(tmp_path):
    db_file = tmp_path / "test_memory.db"
    rag = MemoryRAG(db_file)

    # Insert items
    rag.add_lesson(
        title="Queda de BGP com PTT São Paulo",
        lesson="Queda ocorreu devido a estouro do max-prefix configurado em 1000 rotas. Aumentado para 2000.",
        category="bgp_incident",
        impact="alto",
    )

    rag.add_topology_item(
        pop_name="POP Central - Datacenter",
        details="Roteador CCR2116 conectando OLT Huawei MA5800 via enlace 10G SFP+ na VLAN 200.",
    )

    # Search query
    res = rag.search("max-prefix")
    assert len(res) >= 1
    assert "PTT São Paulo" in res[0]["title"]

    res_pop = rag.search("CCR2116")
    assert len(res_pop) >= 1
    assert "POP Central" in res_pop[0]["title"]
