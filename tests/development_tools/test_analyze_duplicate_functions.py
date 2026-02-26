"""Tests for analyze_duplicate_functions supporting tool."""

import shutil
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.fixture
def dupes_module():
    """Load analyze_duplicate_functions module with dev tools loader."""
    return load_development_tools_module("functions.analyze_duplicate_functions")


@pytest.mark.unit
def test_tokenize_name_splits_snake_and_camel_case(dupes_module):
    """_tokenize_name should split snake_case, camelCase, and digits."""
    assert dupes_module._tokenize_name("get_user2_id") == [
        "get",
        "user",
        "2",
        "id",
    ]
    assert dupes_module._tokenize_name("HTTPServerError") == [
        "http",
        "server",
        "error",
    ]


@pytest.mark.unit
def test_function_has_exclude_comment_detects_marker(dupes_module):
    """Exclude comment should be detected within a few lines of the function."""
    content = "# duplicate_functions_exclude: thin wrapper\n\ndef foo():\n    return 1\n"
    node = dupes_module.ast.parse(content).body[0]
    assert dupes_module._function_has_exclude_comment(content, node) is True

    no_marker = "def bar():\n    return 2\n"
    node = dupes_module.ast.parse(no_marker).body[0]
    assert dupes_module._function_has_exclude_comment(no_marker, node) is False


@pytest.mark.unit
def test_build_candidate_pairs_respects_stop_tokens_and_group_size(dupes_module):
    """Candidate pairing should skip stop tokens and oversized token groups."""
    record = dupes_module.FunctionRecord
    records = [
        record(
            name="alpha",
            full_name="alpha",
            class_name=None,
            file_path="a.py",
            line=1,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("shared",),
        ),
        record(
            name="alpha",
            full_name="alpha",
            class_name=None,
            file_path="b.py",
            line=2,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("shared",),
        ),
        record(
            name="alpha",
            full_name="alpha",
            class_name=None,
            file_path="c.py",
            line=3,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("shared",),
        ),
    ]

    pairs, skipped, capped = dupes_module._build_candidate_pairs(
        records,
        stop_tokens=set(),
        max_token_group_size=2,
        max_candidate_pairs=10,
    )

    assert pairs == set()
    assert skipped.get("shared") == 3
    assert capped is False


@pytest.mark.unit
def test_deduplicate_records_collapses_same_function(dupes_module):
    """_deduplicate_records should collapse identical (file, line, full_name)."""
    temp_root = Path(__file__).parent.parent / "data" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = temp_root / f"tmp_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        file_path = temp_path / "a.py"
        record = dupes_module.FunctionRecord
        r1 = record(
            name="alpha",
            full_name="alpha",
            class_name=None,
            file_path=str(file_path),
            line=10,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("alpha",),
        )
        r2 = record(
            name="alpha",
            full_name="alpha",
            class_name=None,
            file_path=str(file_path.resolve()),
            line=10,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("alpha",),
        )

        deduped = dupes_module._deduplicate_records([r1, r2], project_root=temp_path)
        assert len(deduped) == 1
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.mark.unit
def test_compute_similarity_applies_weights(dupes_module):
    """_compute_similarity should weight name/args/locals/imports scores."""
    record = dupes_module.FunctionRecord
    a = record(
        name="get_user",
        full_name="get_user",
        class_name=None,
        file_path="a.py",
        line=1,
        args=("user_id",),
        locals_used=("result",),
        imports_used=("core",),
        name_tokens=("get", "user"),
    )
    b = record(
        name="get_user",
        full_name="get_user",
        class_name=None,
        file_path="b.py",
        line=2,
        args=("user_id",),
        locals_used=("result",),
        imports_used=("core",),
        name_tokens=("get", "user"),
    )

    overall, scores = dupes_module._compute_similarity(
        a,
        b,
        weights={"name": 1.0, "args": 0.0, "locals": 0.0, "imports": 0.0},
    )
    assert overall == 1.0
    assert scores["name"] == 1.0


@pytest.mark.unit
def test_group_pairs_respects_max_groups(dupes_module):
    """_group_pairs should sort by max similarity and honor max_groups."""
    pair_results = [
        {
            "overall_similarity": 0.95,
            "name_similarity": 1.0,
            "args_similarity": 1.0,
            "locals_similarity": 1.0,
            "imports_similarity": 0.8,
            "a": {
                "name": "a1",
                "full_name": "a1",
                "class": None,
                "file": "a.py",
                "line": 1,
                "args": [],
            },
            "b": {
                "name": "a2",
                "full_name": "a2",
                "class": None,
                "file": "a.py",
                "line": 2,
                "args": [],
            },
        },
        {
            "overall_similarity": 0.70,
            "name_similarity": 0.8,
            "args_similarity": 0.6,
            "locals_similarity": 0.7,
            "imports_similarity": 0.7,
            "a": {
                "name": "b1",
                "full_name": "b1",
                "class": None,
                "file": "b.py",
                "line": 10,
                "args": [],
            },
            "b": {
                "name": "b2",
                "full_name": "b2",
                "class": None,
                "file": "b.py",
                "line": 11,
                "args": [],
            },
        },
    ]

    groups = dupes_module._group_pairs(pair_results, max_groups=1)
    assert len(groups) == 1
    assert groups[0]["similarity_range"]["max"] == 0.95
    assert len(groups[0]["pair_examples"]) == 1


@pytest.mark.unit
def test_normalize_path_falls_back_when_project_root_fails(dupes_module):
    """_normalize_path should return a normalized path even if config fails."""
    with patch.object(dupes_module.config, "get_project_root", side_effect=RuntimeError("boom")):
        normalized = dupes_module._normalize_path(r"a\b\c.py")
    assert normalized == "a/b/c.py"


@pytest.mark.unit
def test_main_json_output_path(dupes_module):
    """main should print JSON when --json is passed."""
    fake_result = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {"total_functions": 0, "top_pairs": []},
    }
    with (
        patch.object(dupes_module, "_gather_function_records", return_value=([], {})),
        patch.object(dupes_module, "_analyze_duplicates", return_value=fake_result),
        patch("sys.argv", ["analyze_duplicate_functions.py", "--json"]),
        patch("builtins.print") as mock_print,
    ):
        exit_code = dupes_module.main()

    assert exit_code == 0
    mock_print.assert_called_once()
    printed = mock_print.call_args.args[0]
    assert '"total_issues": 0' in printed


@pytest.mark.unit
def test_main_non_json_no_duplicate_groups_message(dupes_module):
    """main should render the no-groups message in human-readable mode."""
    fake_result = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "total_functions": 2,
            "records_deduplicated": 0,
            "groups_filtered_single_function": 0,
            "groups_capped": False,
            "max_groups": 25,
            "top_pairs": [],
        },
    }
    with (
        patch.object(dupes_module, "_gather_function_records", return_value=([], {})),
        patch.object(dupes_module, "_analyze_duplicates", return_value=fake_result),
        patch("sys.argv", ["analyze_duplicate_functions.py"]),
        patch("builtins.print") as mock_print,
    ):
        exit_code = dupes_module.main()

    assert exit_code == 0
    output_lines = [str(call.args[0]) for call in mock_print.call_args_list if call.args]
    assert any("No duplicate groups detected." in line for line in output_lines)
