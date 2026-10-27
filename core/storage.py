"""Workspace and Storage Manager for HarnessISP.

Manages data persistence, workspace directory structure, configuration,
and pre-change backups.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("harness_isp.storage")

DEFAULT_WORKSPACE_DIRNAME = "HarnessISP_Data"


class StorageManager:
    """Handles workspace persistence, directory creation and configuration."""

    def __init__(self, workspace_path: str | Path | None = None) -> None:
        if workspace_path:
            self.root = Path(workspace_path).expanduser().resolve()
        else:
            self.root = self._detect_default_workspace()

        self.memory_dir = self.root / "memory"
        self.wiki_dir = self.root / "wiki"
        self.backups_dir = self.root / "backups"
        self.scripts_dir = self.root / "scripts"
        self.logs_dir = self.root / "logs"
        self.vault_dir = self.root / "vault"
        self.config_file = self.root / "config.yaml"

    def _detect_default_workspace(self) -> Path:
        """Resolve default workspace based on user home."""
        home = Path.home()
        return (home / DEFAULT_WORKSPACE_DIRNAME).resolve()

    def initialize(self) -> None:
        """Create necessary workspace folders and baseline config if missing."""
        for folder in (self.memory_dir, self.wiki_dir, self.backups_dir, self.scripts_dir, self.logs_dir, self.vault_dir):
            folder.mkdir(parents=True, exist_ok=True)

        if not self.config_file.exists():
            default_config: dict[str, Any] = {
                "version": "1.0.0",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "network": {
                    "primary_asn": None,
                    "default_vendor": "mikrotik",
                    "safe_mode_enforced": True,
                },
                "gui": {
                    "theme": "dark_noc",
                    "stay_on_top": True,
                    "ball_color_mode": "status_reactive",
                },
            }
            self.save_config(default_config)

    def load_config(self) -> dict[str, Any]:
        """Load YAML configuration from workspace."""
        if not self.config_file.exists():
            self.initialize()
        with open(self.config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def save_config(self, data: dict[str, Any]) -> None:
        """Save YAML configuration to workspace."""
        self.root.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def create_backup(self, device_id: str, content: str, extension: str = "rsc") -> Path:
        """Store a pre-change configuration backup timestamped."""
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in device_id)
        backup_file = self.backups_dir / f"{sanitized_id}_{ts}.{extension}"
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(content)
        return backup_file

    def save_script(self, filename: str, content: str) -> Path:
        """Persist generated network script to scripts directory."""
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        target = self.scripts_dir / filename
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return target

    def log_incident(self, title: str, details: dict[str, Any]) -> Path:
        """Append an incident/action record to logs."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"incident_{ts}.json"
        payload = {
            "title": title,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **details,
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return log_file
