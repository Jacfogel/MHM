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
def test_get_intentional_group_id_extracts_id_or_empty(dupes_module):
    """_get_intentional_group_id should return group id after colon, or '' when marker has no colon."""
    content = "# not_duplicate: format_message\n\ndef format_message():\n    pass\n"
    node = dupes_module.ast.parse(content).body[0]
    assert dupes_module._get_intentional_group_id(content, node) == "format_message"

    content_no_colon = "# not_duplicate\n\ndef clear():\n    pass\n"
    node = dupes_module.ast.parse(content_no_colon).body[0]
    assert dupes_module._get_intentional_group_id(content_no_colon, node) == ""

    no_marker = "def bar():\n    return 2\n"
    node = dupes_module.ast.parse(no_marker).body[0]
    assert dupes_module._get_intentional_group_id(no_marker, node) is None


@pytest.mark.unit
def test_analyze_duplicates_filters_pairs_only_when_both_same_intentional_group(dupes_module):
    """Pairs are omitted only when both functions have the same intentional_group_id."""
    record = dupes_module.FunctionRecord
    gid = "format_message"
    records = [
        record(
            name="format_message",
            full_name="MessageFormatter.format_message",
            class_name="MessageFormatter",
            file_path="message_formatter.py",
            line=1,
            args=("message",),
            locals_used=(),
            imports_used=(),
            name_tokens=("format", "message"),
            intentional_group_id=gid,
        ),
        record(
            name="format_message",
            full_name="TextMessageFormatter.format_message",
            class_name="TextMessageFormatter",
            file_path="message_formatter.py",
            line=2,
            args=("message",),
            locals_used=(),
            imports_used=(),
            name_tokens=("format", "message"),
            intentional_group_id=gid,
        ),
    ]
    config = {
        "weights": {"name": 1.0, "args": 0.0, "locals": 0.0, "imports": 0.0},
        "min_name_similarity": 0.5,
        "min_overall_similarity": 0.5,
        "max_pairs": 50,
        "max_groups": 25,
        "max_candidate_pairs": 20000,
        "max_token_group_size": 200,
        "stop_name_tokens": [],
    }
    with patch.object(dupes_module.config, "get_project_root", return_value="/proj"):
        result = dupes_module._analyze_duplicates(records, config, cache_stats={})
    details = result.get("details", {})
    assert details.get("pairs_filtered_intentional") == 1
    assert len(details.get("duplicate_groups", [])) == 0
    assert details.get("pairs_reported") == 0


@pytest.mark.unit
def test_analyze_duplicates_reports_pair_when_only_one_has_intentional_group(dupes_module):
    """If only one function has intentional_group_id, the pair is still reported (future duplicate)."""
    record = dupes_module.FunctionRecord
    records = [
        record(
            name="format_message",
            full_name="MessageFormatter.format_message",
            class_name="MessageFormatter",
            file_path="message_formatter.py",
            line=1,
            args=("message",),
            locals_used=(),
            imports_used=(),
            name_tokens=("format", "message"),
            intentional_group_id="format_message",
        ),
        record(
            name="format_message",
            full_name="TextMessageFormatter.format_message",
            class_name="TextMessageFormatter",
            file_path="message_formatter.py",
            line=2,
            args=("message",),
            locals_used=(),
            imports_used=(),
            name_tokens=("format", "message"),
            intentional_group_id=None,
        ),
    ]
    config = {
        "weights": {"name": 1.0, "args": 0.0, "locals": 0.0, "imports": 0.0},
        "min_name_similarity": 0.5,
        "min_overall_similarity": 0.5,
        "max_pairs": 50,
        "max_groups": 25,
        "max_candidate_pairs": 20000,
        "max_token_group_size": 200,
        "stop_name_tokens": [],
    }
    with patch.object(dupes_module.config, "get_project_root", return_value="/proj"):
        result = dupes_module._analyze_duplicates(records, config, cache_stats={})
    details = result.get("details", {})
    assert details.get("pairs_filtered_intentional", 0) == 0
    assert details.get("pairs_reported") == 1


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


# --- Body/structural similarity tests ---


@pytest.mark.unit
def test_body_node_sequence_returns_top_level_stmt_types(dupes_module):
    """_body_node_sequence should return AST node type names for function body statements."""
    code = "def foo():\n    x = 1\n    if x:\n        return x\n    return None\n"
    tree = dupes_module.ast.parse(code)
    func = tree.body[0]
    seq = dupes_module._body_node_sequence(func)
    assert isinstance(seq, tuple)
    assert "Assign" in seq
    assert "If" in seq
    assert "Return" in seq


@pytest.mark.unit
def test_build_body_candidate_pairs_same_file_capped(dupes_module):
    """_build_body_candidate_pairs with same_file scope should cap at max_pairs."""
    record = dupes_module.FunctionRecord
    records = [
        record(
            name="a",
            full_name="a",
            class_name=None,
            file_path="f.py",
            line=i,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("a",),
            body_node_sequence=("Assign", "Return"),
        )
        for i in range(1, 11)
    ]
    pairs = dupes_module._build_body_candidate_pairs(
        records, scope="same_file", max_pairs=3
    )
    assert len(pairs) == 3


@pytest.mark.unit
def test_compute_similarity_includes_body_when_present(dupes_module):
    """_compute_similarity should include body_similarity in scores when both records have body."""
    record = dupes_module.FunctionRecord
    seq = ("Assign", "If", "Return")
    a = record(
        name="validate_user",
        full_name="validate_user",
        class_name=None,
        file_path="a.py",
        line=1,
        args=(),
        locals_used=(),
        imports_used=(),
        name_tokens=("validate", "user"),
        body_node_sequence=seq,
    )
    b = record(
        name="check_user_input",
        full_name="check_user_input",
        class_name=None,
        file_path="b.py",
        line=2,
        args=(),
        locals_used=(),
        imports_used=(),
        name_tokens=("check", "user", "input"),
        body_node_sequence=seq,
    )
    weights = {"name": 0.0, "args": 0.0, "locals": 0.0, "imports": 0.0, "body": 1.0}
    overall, scores = dupes_module._compute_similarity(a, b, weights)
    assert "body" in scores
    assert scores["body"] == 1.0
    assert overall == 1.0


@pytest.mark.unit
def test_main_passes_consider_body_similarity_to_gather(dupes_module):
    """main should call _gather_function_records with consider_body_similarity=True when --consider-body-similarity."""
    def gather_return(*args, **kwargs):
        return ([], {"total_files": 0, "cached_files": 0, "scanned_files": 0})

    with (
        patch.object(dupes_module, "_gather_function_records", side_effect=gather_return) as mock_gather,
        patch.object(dupes_module, "_analyze_duplicates", return_value={"summary": {}, "details": {}}),
        patch("sys.argv", ["script", "--json", "--consider-body-similarity"]),
        patch("builtins.print"),
    ):
        dupes_module.main()
    mock_gather.assert_called_once()
    assert mock_gather.call_args.kwargs.get("consider_body_similarity") is True


@pytest.mark.unit
def test_analyze_duplicates_body_details_when_enabled(dupes_module):
    """_analyze_duplicates should set consider_body_similarity_used and body_candidate_pairs_considered when enabled."""
    record = dupes_module.FunctionRecord
    seq = ("Return",)
    records = [
        record(
            name="foo",
            full_name="foo",
            class_name=None,
            file_path="f.py",
            line=1,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("foo",),
            body_node_sequence=seq,
        ),
        record(
            name="bar",
            full_name="bar",
            class_name=None,
            file_path="f.py",
            line=2,
            args=(),
            locals_used=(),
            imports_used=(),
            name_tokens=("bar",),
            body_node_sequence=seq,
        ),
    ]
    config = {
        "weights": {"name": 0.0, "args": 0.0, "locals": 0.0, "imports": 0.0, "body": 1.0},
        "min_name_similarity": 0.0,
        "min_overall_similarity": 0.5,
        "max_pairs": 50,
        "max_groups": 25,
        "max_candidate_pairs": 20000,
        "max_token_group_size": 200,
        "stop_name_tokens": [],
        "consider_body_similarity": True,
        "max_body_candidate_pairs": 5000,
        "body_similarity_scope": "same_file",
    }
    with patch.object(dupes_module.config, "get_project_root", return_value="/proj"):
        result = dupes_module._analyze_duplicates(records, config, cache_stats={})
    details = result.get("details", {})
    assert details.get("consider_body_similarity_used") is True
    assert "body_candidate_pairs_considered" in details
    assert details["body_candidate_pairs_considered"] == 1
    top_pairs = details.get("top_pairs", [])
    if top_pairs:
        assert "body_similarity" in top_pairs[0]


@pytest.mark.unit
def test_analyze_duplicates_body_for_near_miss_rescues_on_body(dupes_module):
    """With body_for_near_miss_only, pairs below min_name but >= body_similarity_min_name_threshold can be rescued by body similarity."""
    record = dupes_module.FunctionRecord
    seq = ("Assign", "Return")
    records = [
        record(
            name="get_user_id",
            full_name="get_user_id",
            class_name=None,
            file_path="a.py",
            line=1,
            args=("x",),
            locals_used=(),
            imports_used=(),
            name_tokens=("get", "user", "id"),
            body_node_sequence=seq,
        ),
        record(
            name="get_user_name",
            full_name="get_user_name",
            class_name=None,
            file_path="b.py",
            line=2,
            args=("x",),
            locals_used=(),
            imports_used=(),
            name_tokens=("get", "user", "name"),
            body_node_sequence=seq,
        ),
    ]
    config = {
        "weights": {"name": 0.3, "args": 0.2, "locals": 0.0, "imports": 0.0, "body": 0.5},
        "min_name_similarity": 0.9,
        "min_overall_similarity": 0.5,
        "max_pairs": 50,
        "max_groups": 25,
        "max_candidate_pairs": 20000,
        "max_token_group_size": 200,
        "stop_name_tokens": ["get"],
        "consider_body_similarity": False,
        "body_for_near_miss_only": True,
        "body_similarity_min_name_threshold": 0.2,
        "max_body_candidate_pairs": 5000,
        "body_similarity_scope": "same_file",
    }
    with patch.object(dupes_module.config, "get_project_root", return_value="/proj"):
        result = dupes_module._analyze_duplicates(records, config, cache_stats={})
    details = result.get("details", {})
    assert details.get("body_for_near_miss_only") is True
    assert details.get("body_similarity_min_name_threshold") == 0.2
    top_pairs = details.get("top_pairs", [])
    assert len(top_pairs) >= 1
    assert "body_similarity" in top_pairs[0]
