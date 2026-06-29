"""
Fernet encryption for Google Health OAuth tokens at rest.

When ``GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY`` is set, ``access_token`` and
``refresh_token`` are encrypted before write and decrypted after read.
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("google_health")

_TOKEN_FIELDS = ("access_token", "refresh_token")


def _encryption_key() -> str:
    from core.config import GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY

    return (GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY or "").strip()


def is_token_encryption_enabled() -> bool:
    """Return True when a Fernet key is configured."""
    return bool(_encryption_key())


@handle_errors("validating Google Health token encryption key", default_return=False)
def is_valid_fernet_key(key: str) -> bool:
    """Return True when ``key`` is a valid Fernet key string."""
    if not key or not isinstance(key, str):
        return False
    try:
        from cryptography.fernet import Fernet

        Fernet(key.encode("utf-8"))
        return True
    except Exception:
        return False


@handle_errors("building Fernet cipher", default_return=None)
def _fernet():
    key = _encryption_key()
    if not key:
        return None
    from cryptography.fernet import Fernet

    return Fernet(key.encode("utf-8"))


@handle_errors("encrypting token value", default_return="")
def encrypt_token_value(plaintext: str) -> str:
    """Encrypt a token for storage; return plaintext unchanged when encryption is off."""
    if not plaintext:
        return ""
    cipher = _fernet()
    if cipher is None:
        return plaintext
    return cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")


@handle_errors("decrypting token value", default_return=None)
def decrypt_token_value(ciphertext: str) -> str | None:
    """Decrypt a stored token value; return None on failure."""
    if not ciphertext:
        return ""
    cipher = _fernet()
    if cipher is None:
        return None
    from cryptography.fernet import InvalidToken

    try:
        return cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


@handle_errors("preparing Google Health auth for storage", default_return=None)
def prepare_auth_for_storage(data: dict[str, Any]) -> dict[str, Any] | None:
    """Encrypt sensitive token fields before persisting to disk."""
    if not isinstance(data, dict):
        return None

    payload = dict(data)
    if not is_token_encryption_enabled():
        payload["tokens_encrypted"] = False
        return payload

    payload["tokens_encrypted"] = True
    for field in _TOKEN_FIELDS:
        value = payload.get(field) or ""
        if value:
            payload[field] = encrypt_token_value(value)
    return payload


@handle_errors("preparing Google Health auth for use", default_return=None)
def prepare_auth_for_use(data: dict[str, Any]) -> dict[str, Any] | None:
    """Decrypt token fields after loading from disk for runtime use."""
    if not isinstance(data, dict):
        return None

    if not data.get("tokens_encrypted"):
        return dict(data)

    if not is_token_encryption_enabled():
        logger.error(
            "Google Health auth tokens are encrypted on disk but "
            "GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY is not configured"
        )
        cleared = dict(data)
        cleared["access_token"] = ""
        cleared["refresh_token"] = ""
        return cleared

    payload = dict(data)
    for field in _TOKEN_FIELDS:
        value = payload.get(field) or ""
        if not value:
            continue
        decrypted = decrypt_token_value(value)
        if decrypted is None:
            logger.error(
                "Failed to decrypt Google Health auth tokens — "
                "check GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY"
            )
            payload["access_token"] = ""
            payload["refresh_token"] = ""
            return payload
        payload[field] = decrypted
    return payload
