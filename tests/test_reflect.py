import pytest
from core.reflect import create_reflection_note


def test_create_reflection_note(tmp_path):
    wiki_dir = tmp_path / "wiki"
    note_path = create_reflection_note(
        task="Flap de BGP no PTT Fortaleza",
        lesson="Timeout de BGP configurado muito agressivo (10s). Ajustado para 30s.",
        category="incidentes",
        impact="critico",
        wiki_dir=wiki_dir,
    )

    assert note_path.exists()
    content = note_path.read_text(encoding="utf-8")
    assert "NOTA-0001" in content
    assert "Flap de BGP no PTT Fortaleza" in content
    assert "critico" in content
