#!/usr/bin/env bash
# HarnessISP TUI Mascot & Banner
# Renderizado no terminal na inicialização do agy CLI e no Antigravity

""":"
exec python3 "$0" "$@"
"""

import os
import socket
import sys
from pathlib import Path


def render_mascot_tui() -> None:
    # ANSI 256 / TrueColor codes
    c_cyan = "\033[38;2;64;224;208m"
    c_emerald = "\033[38;2;46;204;113m"
    c_pink = "\033[38;2;255;105;180m"
    c_gold = "\033[38;2;241;196;15m"
    c_bold = "\033[1m"
    c_reset = "\033[0m"
    c_dim = "\033[2m"

    host = socket.gethostname()
    safe_mode = "ATIVO" if os.environ.get("SAFE_MODE", "1") == "1" else "INATIVO"

    banner = f"""
{c_emerald}{c_bold}       ╭────────────────────────────────────────╮{c_reset}
{c_emerald}{c_bold}       │{c_reset}         ╭────────────────────╮         {c_emerald}{c_bold}│{c_reset}    ⚡ {c_bold}HarnessISP — Coucou Companion (TUI){c_reset}
{c_emerald}{c_bold}       │{c_reset}       ╭╯                      ╰╮       {c_emerald}{c_bold}│{c_reset}    🛡️  Safe Mode: {c_emerald}{safe_mode}{c_reset} | Host: {c_gold}{host}{c_reset}
{c_emerald}{c_bold}       │{c_reset}      ╭╯   {c_cyan}●{c_reset}              {c_cyan}●{c_reset}   ╰╮      {c_emerald}{c_bold}│{c_reset}    🌐 FTTH Multivendor & BGP Ready
{c_emerald}{c_bold}       │{c_reset}      │   {c_pink}✿{c_reset}      ╰──╯      {c_pink}✿{c_reset}   │      {c_emerald}{c_bold}│{c_reset}    🤖 Google Antigravity CLI (agy)
{c_emerald}{c_bold}       │{c_reset}       ╰╮                      ╭╯       {c_emerald}{c_bold}│{c_reset}
{c_emerald}{c_bold}       │{c_reset}         ╰────────────────────╯         {c_emerald}{c_bold}│{c_reset}    {c_dim}"Pronto para proteger o seu NOC contra lockouts!"{c_reset}
{c_emerald}{c_bold}       ╰────────────────────────────────────────╯{c_reset}
"""
    print(banner)


if __name__ == "__main__":
    render_mascot_tui()
