"""Tests for analyze_duplicate_functions supporting tool."""

import shutil
import uuid
from pathlib import Path

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
