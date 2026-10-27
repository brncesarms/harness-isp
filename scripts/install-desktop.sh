#!/usr/bin/env bash
# HarnessISP - Desktop Sentinela & XDG Installer
# Registra o HUD Sentinela no menu de aplicativos do Linux (Hyprland, Omarchy, GNOME, etc.)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

echo "⚡ Instalando HarnessISP Desktop Sentinela (NOC HUD)..."

# 1. Garante ambiente virtual com uv
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "📦 Criando venv e instalando dependências com uv..."
    (cd "$SCRIPT_DIR" && uv venv && uv pip install -r requirements.txt)
fi

# 2. Instalação do arquivo .desktop
mkdir -p "$APPS_DIR"
cp "$SCRIPT_DIR/desktop/harness-isp.desktop" "$APPS_DIR/harness-isp.desktop"
sed -i "s|\$HOME|$HOME|g" "$APPS_DIR/harness-isp.desktop"

# Atualiza cache de aplicativos se a ferramenta existir
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

echo "✅ Atalho de aplicativo instalado em: $APPS_DIR/harness-isp.desktop"

# 3. Instalação opcional do serviço systemd de usuário
mkdir -p "$SYSTEMD_USER_DIR"
cp "$SCRIPT_DIR/systemd/harness-isp-companion.service" "$SYSTEMD_USER_DIR/harness-isp-companion.service"

if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    echo "ℹ️  Para iniciar automaticamente no login do desktop:"
    echo "   systemctl --user enable --now harness-isp-companion.service"
fi

echo "✨ Concluído com sucesso! Você já pode abrir o 'HarnessISP Sentinela' pelo seu menu de aplicativos ou via 'uv run python3 main.py'."
