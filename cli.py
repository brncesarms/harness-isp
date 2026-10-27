#!/usr/bin/env python3
"""Unified CLI for HarnessISP.

Deterministic single-line interface for tests, wiki reflection, RAG sync, and audits.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from core.memory_rag import MemoryRAG
from core.reflect import create_reflection_note
from core.storage import StorageManager
from core.token_optimizer import TokenOptimizer


def cmd_status() -> None:
    storage = StorageManager()
    storage.initialize()
    has_rtk = TokenOptimizer.has_native_rtk()
    wiki_notes = list((Path(__file__).parent / "wiki").rglob("*.md"))

    print("⚡ HarnessISP — Status Operacional")
    print(f"  • Workspace: {storage.root}")
    print(f"  • RTK Nativo (Rust): {'✅ ATIVO (/usr/bin/rtk)' if has_rtk else '⚠️ INATIVO'}")
    print(f"  • Base Wiki (SSOT): {len(wiki_notes)} notas em {Path(__file__).parent / 'wiki'}")
    print(f"  • Memória SQLite FTS5: {storage.memory_dir / 'knowledge.db'}")


def cmd_sync_wiki() -> None:
    storage = StorageManager()
    storage.initialize()
    rag = MemoryRAG(storage.memory_dir / "knowledge.db")
    wiki_path = Path(__file__).parent / "wiki"
    synced = rag.sync_markdown_directory(wiki_path)
    print(f"✨ Wiki sincronizada: {synced} notas indexadas no SQLite FTS5.")


def cmd_audit() -> None:
    repo_root = Path(__file__).parent
    print("🔍 Executando auditoria completa do HarnessISP...\n")

    # 1. Gitleaks
    print("1. Escudo Zero-Leaks (Gitleaks):")
    res_git = subprocess.run(["gitleaks", "detect", f"--source={repo_root}", "--no-git"], capture_output=True, text=True, check=False)
    if res_git.returncode == 0:
        print("   ✅ Zero leaks detectados!")
    else:
        print(f"   ❌ ALERTA DE VAZAMENTO:\n{res_git.stdout or res_git.stderr}")

    # 2. Lychee
    print("\n2. Integridade de Links (Lychee):")
    res_lychee = subprocess.run(["lychee", "--offline", str(repo_root / "wiki")], capture_output=True, text=True, check=False)
    if res_lychee.returncode == 0:
        print("   ✅ Todos os links internos estão íntegros!")
    else:
        print(f"   ⚠️ Links quebrados detectados:\n{res_lychee.stdout or res_lychee.stderr}")

    # 3. Testes via RTK
    print("\n3. Suíte de Testes Automatizados (RTK Pytest):")
    env = dict(sys.modules["os"].environ)
    env["PATH"] = f"{repo_root / '.venv' / 'bin'}:{env.get('PATH', '')}"
    res_test = subprocess.run(["rtk", "pytest", "-v"], cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
    output = (res_test.stdout or res_test.stderr).strip()
    print(f"   {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="HarnessISP Universal CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Status
    subparsers.add_parser("status", help="Exibir status operacional do sistema")

    # Sync Wiki
    subparsers.add_parser("sync-wiki", help="Sincronizar arquivos Markdown da Wiki com SQLite FTS5")

    # Audit
    subparsers.add_parser("audit", help="Auditoria completa de segurança, links e testes")

    # Reflect
    reflect_p = subparsers.add_parser("reflect", help="Registrar lição aprendida / post-mortem")
    reflect_p.add_argument("--task", required=True, help="Título da tarefa ou incidente")
    reflect_p.add_argument("--lesson", required=True, help="Lição aprendida / invariante")
    reflect_p.add_argument("--category", default="incidentes", help="Categoria da nota")
    reflect_p.add_argument("--impact", default="alto", choices=["baixo", "medio", "alto", "critico"])

    # GUI
    subparsers.add_parser("gui", help="Inicializar a esfera flutuante desktop")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "sync-wiki":
        cmd_sync_wiki()
    elif args.command == "audit":
        cmd_audit()
    elif args.command == "reflect":
        note = create_reflection_note(args.task, args.lesson, args.category, args.impact)
        print(f"✨ Lição indexada com sucesso em: {note}")
    elif args.command == "gui":
        from main import main as run_gui
        run_gui()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
