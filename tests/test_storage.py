import pytest
from core.storage import StorageManager


def test_storage_initialization_and_backups(tmp_path):
    storage = StorageManager(workspace_path=tmp_path)
    storage.initialize()

    assert (tmp_path / "config.yaml").exists()
    assert (tmp_path / "memory").is_dir()
    assert (tmp_path / "backups").is_dir()
    assert (tmp_path / "vault").is_dir()

    # Test backup creation
    backup_file = storage.create_backup("ccr-borda-01", "/export compact\n# sample config")
    assert backup_file.exists()
    assert "ccr-borda-01" in backup_file.name

    # Test config update
    cfg = storage.load_config()
    cfg["network"]["primary_asn"] = 65000
    storage.save_config(cfg)

    reloaded = storage.load_config()
    assert reloaded["network"]["primary_asn"] == 65000
