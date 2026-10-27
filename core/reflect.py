"""Reflection and Atomic Note Generator for HarnessISP (Archimedes Reflect Pattern).

Creates standardized Markdown notes with YAML frontmatter in wiki/notes/
and automatically synchronizes with SQLite FTS5 RAG.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

from core.memory_rag import MemoryRAG
from core.storage import StorageManager


def slugify(text: str) -> str:
    """Create a URL/filename-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text).strip("_")


def get_next_note_id(notes_dir: Path) -> int:
    """Find the next sequential note number in wiki/notes."""
    notes_dir.mkdir(parents=True, exist_ok=True)
    existing = list(notes_dir.glob("nota_*.md"))
    if not existing:
        return 1

    max_id = 0
    for file in existing:
        match = re.match(r"nota_(\d{4})_", file.name)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id + 1


def create_reflection_note(
    task: str,
    lesson: str,
    category: str = "incidentes",
    impact: str = "alto",
    wiki_dir: Path | None = None,
) -> Path:
    """Generate an atomic note, save to wiki/notes and sync with FTS5."""
    storage = StorageManager()
    base_wiki = wiki_dir or (Path(__file__).parent.parent / "wiki")
    notes_dir = base_wiki / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    note_num = get_next_note_id(notes_dir)
    note_id = f"NOTA-{note_num:04d}"
    slug = slugify(task)[:50]
    filename = f"nota_{note_num:04d}_{slug}.md"
    note_path = notes_dir / filename

    today = datetime.date.today().isoformat()
    content = f"""---
id: {note_id}
titulo: 'Reflexão: {task}'
data: '{today}'
categoria: {category}
impacto: {impact}
tags:
  - reflexao
  - noc
  - isp
  - post-mortem
---

# 🧠 {note_id}: {task}

## 🎯 Contexto da Tarefa / Incidente
{task}

## 💡 Lição Aprendida (Pilar Invariante)
{lesson}

## 📋 Regra de Ação para o Harness / NOC
Auditar e validar preventivamente via FailsafeGuard e RTK antes de aplicação em produção.
"""

    note_path.write_text(content, encoding="utf-8")

    # Ingest directly into SQLite FTS5 RAG
    db_path = storage.memory_dir / "knowledge.db"
    rag = MemoryRAG(db_path)
    rag.add_lesson(
        title=f"{note_id}: {task}",
        lesson=lesson,
        category=category,
        impact=impact,
    )

    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description="HarnessISP Reflection Engine")
    parser.add_argument("--task", required=True, help="Task description or incident title")
    parser.add_argument("--lesson", required=True, help="Lesson learned or invariant rule")
    parser.add_argument("--category", default="incidentes", help="Note category")
    parser.add_argument("--impact", default="alto", choices=["baixo", "medio", "alto", "critico"], help="Impact level")

    args = parser.parse_args()
    note_path = create_reflection_note(args.task, args.lesson, args.category, args.impact)
    print(f"✨ Lição indexada com sucesso em: {note_path}")


if __name__ == "__main__":
    main()
