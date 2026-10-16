"""Parallel workers must delete the test accounts they create."""

import shutil
from pathlib import Path

import pytest

from tests.test_helpers.test_support.conftest_user_data import (
    _clear_user_store,
    _remove_new_user_dirs,
)

pytestmark = [pytest.mark.unit, pytest.mark.user]


def _probe(name: str) -> Path:
    root = Path("tests/data/tmp") / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def test_clear_user_store_removes_accounts_and_index():
    root = _probe("user_store_cleanup_clear")
    account = root / "users" / "abc" / "account.json"
    account.parent.mkdir(parents=True)
    account.write_text("{}", encoding="utf-8")
    (root / "user_index.json").write_text("{}", encoding="utf-8")
    (root / "notes.txt").write_text("keep", encoding="utf-8")
    try:
        _clear_user_store(root)
        assert not account.exists()
        assert not (root / "user_index.json").exists()
        assert (root / "notes.txt").read_text(encoding="utf-8") == "keep"
        assert (root / "users").is_dir()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_clear_user_store_leaves_real_data_tree_alone():
    root = Path("data/_cleanup_guard_probe")
    account = root / "users" / "keep" / "account.json"
    account.parent.mkdir(parents=True)
    account.write_text("{}", encoding="utf-8")
    try:
        _clear_user_store(root)
        assert account.is_file()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_remove_new_user_dirs_keeps_fixture_users():
    root = _probe("user_store_cleanup_new")
    existing = root / "users" / "from-fixture"
    created = root / "users" / "from-this-test"
    existing.mkdir(parents=True)
    created.mkdir()
    try:
        _remove_new_user_dirs(root, {"from-fixture"})
        assert existing.is_dir()
        assert not created.exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
