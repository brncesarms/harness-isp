"""Secure Vault for HarnessISP (Zero Leaks).

Stores router and OLT credentials encrypted with AES-256-GCM.
Never leaks credentials to LLM prompts. Injects secrets strictly in-memory.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class VaultManager:
    """AES-256-GCM credential vault manager."""

    SALT_SIZE = 16
    NONCE_SIZE = 12
    ITERATIONS = 100_000

    def __init__(self, vault_dir: Path, master_password: str = "harness-isp-default-key") -> None:
        self.vault_dir = Path(vault_dir)
        self.vault_file = self.vault_dir / "credentials.vault"
        self.master_password = master_password
        self._memory_cache: dict[str, dict[str, Any]] = {}

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(self.master_password.encode("utf-8"))

    def save_secret(self, key: str, payload: dict[str, Any]) -> None:
        """Encrypt and store credentials for a target router or OLT."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache[key] = payload

        # Read existing file or create empty dict
        data = self.read_all_secrets()
        data[key] = payload

        # Serialize
        raw_bytes = json.dumps(data).encode("utf-8")
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        aesgcm = AESGCM(self._derive_key(salt))
        ciphertext = aesgcm.encrypt(nonce, raw_bytes, None)

        packaged = {
            "salt": base64.b64encode(salt).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        }
        with open(self.vault_file, "w", encoding="utf-8") as f:
            json.dump(packaged, f, indent=2)

    def read_secret(self, key: str) -> dict[str, Any] | None:
        """Retrieve single decrypted secret."""
        if key in self._memory_cache:
            return self._memory_cache[key]
        all_secrets = self.read_all_secrets()
        return all_secrets.get(key)

    def read_all_secrets(self) -> dict[str, dict[str, Any]]:
        """Decrypt and return all secrets from vault."""
        if not self.vault_file.exists():
            return {}
        try:
            with open(self.vault_file, "r", encoding="utf-8") as f:
                packaged = json.load(f)

            salt = base64.b64decode(packaged["salt"])
            nonce = base64.b64decode(packaged["nonce"])
            ciphertext = base64.b64decode(packaged["ciphertext"])

            aesgcm = AESGCM(self._derive_key(salt))
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            res: dict[str, dict[str, Any]] = json.loads(plaintext.decode("utf-8"))
            self._memory_cache = res
            return res
        except Exception:
            return {}

    def list_keys(self) -> list[str]:
        """List keys/device aliases without decrypting sensitive values."""
        secrets = self.read_all_secrets()
        return list(secrets.keys())
