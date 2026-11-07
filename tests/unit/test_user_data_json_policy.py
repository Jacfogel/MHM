"""Prevent stream JSON access from bypassing approved storage boundaries.

The conservative rule checks all product json.load/dump calls, avoiding fragile
guesses about variable names or paths. Non-user files have exact call exceptions.
json.loads/dumps (in-memory/wire serialization) are intentionally outside scope.
"""

import pytest

from tests.test_helpers.source_policy import (
    PROJECT_ROOT,
    json_violations,
    product_sources,
)

pytestmark = [pytest.mark.unit, pytest.mark.user]

JSON_ALLOWED_FILES = {
    "core/file_operations.py": "Shared validated/atomic JSON persistence primitives.",
    "core/file_locking.py": "Shared locked JSON persistence primitives.",
    "storage/user_data_read.py": "Canonical user-data reads.",
    "storage/user_data_write.py": "Canonical user-data writes.",
    "storage/user_data_registry.py": "Canonical user-data registry.",
    "storage/user_item_storage.py": "Canonical task/notebook item persistence.",
    "storage/user_data_index.py": "Canonical user index rebuild and lookup storage.",
    "storage/user_data_summaries.py": "Storage-owned validated per-user summary reads.",
    "storage/user_data_presets.py": "Storage-owned shared user preset resource loading.",
    "storage/service_flag_storage.py": "Low-level service flag persistence.",
}

# Exact path + qualified owner + API. New functions in these files are not exempt.
JSON_ALLOWED_CALLS = {
    (
        "core/error_handling.py",
        "FileNotFoundRecovery.recover",
        "json.dump",
    ): "Low-level missing-file recovery creates the caller's default JSON payload.",
    (
        "core/error_handling.py",
        "JSONDecodeRecovery.recover",
        "json.dump",
    ): "Low-level corrupt-file recovery replaces the caller's default JSON payload.",
    (
        "core/backup_manager.py",
        "BackupManager._create_backup__create_directory_payload",
        "json.dump",
    ): "Writes backup manifest, not per-user feature data.",
    (
        "core/backup_manager.py",
        "BackupManager._get_backup_info",
        "json.load",
    ): "Reads backup manifest metadata.",
    (
        "core/backup_manager.py",
        "BackupManager._validate_backup__validate_directory_backup",
        "json.load",
    ): "Validates backup manifest metadata.",
    (
        "core/backup_manager.py",
        "_validate_system_state__validate_user_index",
        "json.load",
    ): "Read-only locked system index validation; does not load per-user documents.",
    (
        "core/auto_cleanup.py",
        "get_last_cleanup_timestamp",
        "json.load",
    ): "Reads global cleanup tracker.",
    (
        "core/auto_cleanup.py",
        "update_cleanup_timestamp",
        "json.dump",
    ): "Writes global cleanup tracker.",
    (
        "core/natural_language_defaults.py",
        "_load_builtin_defaults_dict",
        "json.load",
    ): "Reads shipped phrase defaults; per-user overrides use storage helpers.",
    (
        "core/tags.py",
        "_load_default_tags_from_resources",
        "json.load",
    ): "Reads shipped default tags.",
    (
        "messages/message_data_manager.py",
        "load_default_messages",
        "json.load",
    ): "Reads shipped default messages; user messages use storage helpers.",
    (
        "ui/request_actions.py",
        "_poll_response_file",
        "json.load",
    ): "Reads transient service response IPC file.",
    (
        "ui/request_actions.py",
        "create_test_message_request",
        "json.dump",
    ): "Writes transient service request IPC file.",
    (
        "ui/request_actions.py",
        "create_checkin_prompt_request",
        "json.dump",
    ): "Writes transient service request IPC file.",
    (
        "ui/request_actions.py",
        "create_task_reminder_request",
        "json.dump",
    ): "Writes transient service request IPC file.",
}


def test_product_json_stream_access_uses_approved_storage():
    violations = [
        v
        for path, source in product_sources()
        for v in json_violations(source, path, JSON_ALLOWED_FILES, JSON_ALLOWED_CALLS)
    ]
    assert not violations, "\n".join(violations)


@pytest.mark.parametrize(
    "source",
    [
        "import json\njson.load(handle)",
        "import json as codec\ncodec.dump(data, handle)",
        "from json import load as read\nread(handle)",
        "from json import dump\ndump(data, handle)",
    ],
)
def test_scanner_rejects_direct_and_aliased_stream_access(source):
    assert json_violations(
        source, "tasks/example.py", JSON_ALLOWED_FILES, JSON_ALLOWED_CALLS
    )


def test_non_user_exception_cannot_exempt_other_functions_or_operations():
    path = "messages/message_data_manager.py"
    source = "import json\ndef load_default_messages():\n    json.load(handle)\ndef load_user_messages():\n    json.load(handle)\ndef save():\n    json.dump(data, handle)"
    violations = json_violations(source, path, JSON_ALLOWED_FILES, JSON_ALLOWED_CALLS)
    assert len(violations) == 2
    assert "load_user_messages" in violations[0]
    assert "save" in violations[1]


def test_storage_allowlist_is_exact_and_requires_a_reason():
    source = "import json\njson.load(handle)"
    assert not json_violations(
        source, "storage/user_item_storage.py", JSON_ALLOWED_FILES, {}
    )
    assert json_violations(source, "tasks/user_item_storage.py", JSON_ALLOWED_FILES, {})
    assert json_violations(
        source, "storage/user_item_storage.py", {"storage/user_item_storage.py": ""}, {}
    )


def test_json_strings_comments_and_in_memory_serialization_are_allowed():
    source = "import json\ntext = 'json.load(file)' # json.dump(data, file)\njson.loads(text)\njson.dumps(data)"
    assert not json_violations(source, "tasks/example.py", {}, {})


def test_documented_exceptions_exist_and_are_still_used():
    for path, reason in JSON_ALLOWED_FILES.items():
        assert reason and (PROJECT_ROOT / path).is_file(), path
    for (path, owner, api), reason in JSON_ALLOWED_CALLS.items():
        assert reason
        source = (PROJECT_ROOT / path).read_text(encoding="utf-8-sig")
        # Without its own exception the exact call must be reported. This catches
        # stale exceptions and avoids quietly retaining broad historical lists.
        remaining = dict(JSON_ALLOWED_CALLS)
        del remaining[(path, owner, api)]
        assert any(
            f"{api} in {owner};" in message
            for message in json_violations(source, path, JSON_ALLOWED_FILES, remaining)
        ), (path, owner, api)
