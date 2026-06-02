"""Tests for shared test user factory helpers."""

import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.user
@pytest.mark.file_io
def test_user_index_updates_preserve_concurrent_entries(test_path_factory):
    """Parallel test-user creation should not drop user_index entries."""
    test_data_dir = test_path_factory

    def update_entry(index: int) -> None:
        TestUserFactory.create_basic_user__update_index(
            test_data_dir,
            f"concurrent_user_{index}",
            f"actual-user-{index}",
            discord_user_id=f"discord-{index}",
            email=f"user-{index}@example.com",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(update_entry, range(20)))

    with open(os.path.join(test_data_dir, "user_index.json"), encoding="utf-8") as file_obj:
        user_index = json.load(file_obj)

    for index in range(20):
        assert user_index[f"concurrent_user_{index}"] == f"actual-user-{index}"
        assert user_index[f"discord:discord-{index}"] == f"actual-user-{index}"
        assert user_index[f"email:user-{index}@example.com"] == f"actual-user-{index}"
