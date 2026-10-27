import pytest
from core.vault import VaultManager


def test_vault_encryption_decryption(tmp_path):
    vault = VaultManager(vault_dir=tmp_path, master_password="super-secret-pass")

    secret_payload = {
        "host": "10.0.0.1",
        "user": "admin",
        "password": "RouterPassword123!",
        "type": "mikrotik",
    }

    vault.save_secret("core-borda-01", secret_payload)

    # Validate file is created
    assert (tmp_path / "credentials.vault").exists()

    # Create new instance to test cold-read from disk
    vault_reader = VaultManager(vault_dir=tmp_path, master_password="super-secret-pass")
    retrieved = vault_reader.read_secret("core-borda-01")

    assert retrieved is not None
    assert retrieved["password"] == "RouterPassword123!"
    assert retrieved["host"] == "10.0.0.1"
    assert "core-borda-01" in vault_reader.list_keys()


def test_vault_wrong_password(tmp_path):
    vault = VaultManager(vault_dir=tmp_path, master_password="correct-pass")
    vault.save_secret("olt-huawei-01", {"snmp": "public123"})

    bad_vault = VaultManager(vault_dir=tmp_path, master_password="wrong-password")
    assert bad_vault.read_secret("olt-huawei-01") is None
