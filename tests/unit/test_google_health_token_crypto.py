"""Unit tests for Google Health OAuth token encryption at rest."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from core.config import get_user_data_dir
from integrations.google_health.data_handlers import load_auth, save_auth
from integrations.google_health.token_crypto import (
    decrypt_token_value,
    encrypt_token_value,
    is_valid_fernet_key,
    prepare_auth_for_storage,
    prepare_auth_for_use,
)
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

TEST_KEY = Fernet.generate_key().decode()


@pytest.mark.unit
@pytest.mark.core
def test_is_valid_fernet_key_accepts_generated_key():
    assert is_valid_fernet_key(TEST_KEY) is True
    assert is_valid_fernet_key("not-a-valid-key") is False


@pytest.mark.unit
@pytest.mark.core
def test_encrypt_decrypt_round_trip():
    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": TEST_KEY}):
        encrypted = encrypt_token_value("secret-access-token")
        assert encrypted != "secret-access-token"
        assert decrypt_token_value(encrypted) == "secret-access-token"


@pytest.mark.unit
@pytest.mark.core
def test_prepare_auth_for_use_requires_key_when_encrypted():
    encrypted = Fernet(TEST_KEY.encode()).encrypt(b"refresh").decode()
    stored = {
        "schema_version": 2,
        "updated_at": "2026-06-28 12:00:00",
        "access_token": encrypted,
        "refresh_token": encrypted,
        "tokens_encrypted": True,
    }
    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": ""}):
        result = prepare_auth_for_use(stored)
    assert result is not None
    assert result["access_token"] == ""
    assert result["refresh_token"] == ""


@pytest.mark.unit
@pytest.mark.user
def test_save_auth_encrypts_tokens_on_disk(test_data_dir):
    user_id = "health-crypto-user-001"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    auth = {
        "schema_version": 2,
        "updated_at": "2026-06-28 12:00:00",
        "access_token": "plain-access",
        "refresh_token": "plain-refresh",
        "expires_at": "2099-01-01 00:00:00",
    }

    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": TEST_KEY}):
        assert save_auth(user_id, auth) is True
        loaded = load_auth(user_id)

    assert loaded is not None
    assert loaded["access_token"] == "plain-access"
    assert loaded["refresh_token"] == "plain-refresh"
    assert loaded["tokens_encrypted"] is True

    auth_path = Path(get_user_data_dir(user_id)) / "health" / "google_health_auth.json"
    raw = json.loads(auth_path.read_text(encoding="utf-8"))
    assert raw["tokens_encrypted"] is True
    assert raw["access_token"] != "plain-access"
    assert raw["refresh_token"] != "plain-refresh"


@pytest.mark.unit
@pytest.mark.user
def test_legacy_plaintext_auth_still_loads(test_data_dir):
    user_id = "health-crypto-user-002"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    auth = {
        "schema_version": 2,
        "updated_at": "2026-06-28 12:00:00",
        "access_token": "legacy-access",
        "refresh_token": "legacy-refresh",
        "tokens_encrypted": False,
    }

    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": ""}):
        assert save_auth(user_id, auth) is True
        loaded = load_auth(user_id)

    assert loaded["access_token"] == "legacy-access"
    assert loaded["refresh_token"] == "legacy-refresh"


@pytest.mark.unit
@pytest.mark.user
def test_plaintext_migrates_to_encrypted_on_save(test_data_dir):
    user_id = "health-crypto-user-003"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": ""}):
        save_auth(
            user_id,
            {
                "schema_version": 2,
                "updated_at": "2026-06-28 12:00:00",
                "access_token": "migrate-access",
                "refresh_token": "migrate-refresh",
            },
        )

    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": TEST_KEY}):
        save_auth(
            user_id,
            {
                "schema_version": 2,
                "updated_at": "2026-06-28 13:00:00",
                "access_token": "migrate-access",
                "refresh_token": "migrate-refresh",
            },
        )
        loaded = load_auth(user_id)

    assert loaded["access_token"] == "migrate-access"
    auth_path = Path(get_user_data_dir(user_id)) / "health" / "google_health_auth.json"
    raw = json.loads(auth_path.read_text(encoding="utf-8"))
    assert raw["tokens_encrypted"] is True
    assert raw["access_token"] != "migrate-access"


@pytest.mark.unit
@pytest.mark.core
def test_prepare_auth_for_storage_without_key_keeps_plaintext():
    data = {
        "access_token": "plain",
        "refresh_token": "plain",
    }
    with patch.dict(os.environ, {"GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY": ""}):
        result = prepare_auth_for_storage(data)
    assert result["tokens_encrypted"] is False
    assert result["access_token"] == "plain"
