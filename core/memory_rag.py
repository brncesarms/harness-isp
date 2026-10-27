"""SQLite FTS5 Knowledge Base & Memory Manager (RAG Pattern).

Maintains indexed ISP topology, POPs, BGP peers, and post-incident lessons learned (reflect).
"""

from __future__ import annotations

import datetime
import re
import sqlite3
from pathlib import Path
from typing import Any


class MemoryRAG:
    """SQLite FTS5 storage and search engine for ISP knowledge."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    impact TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                    title,
                    content,
                    category,
                    content=notes,
                    content_rowid=id
                )
            """)
            # Triggers to keep FTS index synced
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                    INSERT INTO notes_fts(rowid, title, content, category)
                    VALUES (new.id, new.title, new.content, new.category);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                    INSERT INTO notes_fts(notes_fts, rowid, title, content, category)
                    VALUES('delete', old.id, old.title, old.content, old.category);
                END;
            """)
            conn.commit()

    def add_lesson(self, title: str, lesson: str, category: str = "incident", impact: str = "medio") -> int:
        """Register a post-incident / post-task lesson learned (arch reflect pattern)."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (category, title, content, impact, created_at) VALUES (?, ?, ?, ?, ?)",
                (category, title, lesson, impact, now),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def add_topology_item(self, pop_name: str, details: str) -> int:
        """Index a POP, router role, or circuit detail."""
        return self.add_lesson(title=f"POP: {pop_name}", lesson=details, category="topology", impact="baixo")

    def sync_markdown_directory(self, wiki_dir: Path) -> int:
        """Scan a markdown wiki directory and index all .md notes into SQLite FTS5."""
        wiki_path = Path(wiki_dir)
        if not wiki_path.exists():
            return 0

        synced = 0
        for md_file in wiki_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                category = md_file.parent.name
                title = md_file.stem.replace("_", " ").title()

                # Basic YAML frontmatter parser
                frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
                impact = "medio"
                body = content

                if frontmatter_match:
                    fm_text, body = frontmatter_match.groups()
                    for line in fm_text.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k, v = k.strip().lower(), v.strip().strip("'\"")
                            if k == "titulo" and v:
                                title = v
                            elif k == "impacto" and v:
                                impact = v
                            elif k == "categoria" and v:
                                category = v

                # Use relative path as distinct title or key
                rel_path = md_file.relative_to(wiki_path).as_posix()
                full_title = f"{title} ({rel_path})"
                self.add_lesson(title=full_title, lesson=body.strip(), category=category, impact=impact)
                synced += 1
            except Exception:
                continue

        return synced

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Perform full-text search using SQLite FTS5."""
        # Replace punctuation (like hyphens) with spaces so terms tokenize correctly
        sanitized = re.sub(r"[^\w\s]", " ", query).strip()
        if not sanitized:
            return []

        # Prepare MATCH query (prefix matching for each word)
        match_query = " ".join(f"{word}*" for word in sanitized.split())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT n.id, n.category, n.title, n.content, n.impact, n.created_at,
                       bm25(notes_fts) as rank
                FROM notes_fts
                JOIN notes n ON n.id = notes_fts.rowid
                WHERE notes_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
