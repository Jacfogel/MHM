"""§3.19.1 merge contract tests for sharded Ruff/Bandit JSON (V5)."""

from __future__ import annotations

import pytest

from development_tools.shared.sharded_static_analysis import (
    merge_bandit_raw_payloads,
    merge_pyright_json_payloads,
    merge_ruff_check_json_lists,
    pyright_diagnostic_identity,
    ruff_diagnostic_identity,
)


@pytest.mark.unit
def test_merge_ruff_dedupes_same_file_code_location() -> None:
    a = {"filename": "pkg/a.py", "code": "F401", "location": {"row": 1, "column": 0}}
    shard1 = [a]
    shard2 = [dict(a)]
    merged = merge_ruff_check_json_lists([shard1, shard2])
    assert len(merged) == 1
    assert ruff_diagnostic_identity(merged[0]) == ("pkg/a.py", "F401", 1, 0)


@pytest.mark.unit
def test_merge_ruff_keeps_distinct_locations() -> None:
    i1 = {"filename": "x.py", "code": "E", "location": {"row": 1, "column": 1}}
    i2 = {"filename": "x.py", "code": "E", "location": {"row": 2, "column": 1}}
    merged = merge_ruff_check_json_lists([[i1], [i2]])
    assert len(merged) == 2
    keys = {ruff_diagnostic_identity(x) for x in merged}
    assert ("x.py", "E", 1, 1) in keys
    assert ("x.py", "E", 2, 1) in keys


@pytest.mark.unit
def test_merge_ruff_normalizes_backslashes_in_filename() -> None:
    i1 = {"filename": "pkg\\a.py", "code": "F401", "location": {"row": 3, "column": 0}}
    i2 = {"filename": "pkg/a.py", "code": "F401", "location": {"row": 3, "column": 0}}
    merged = merge_ruff_check_json_lists([[i1], [i2]])
    assert len(merged) == 1


@pytest.mark.unit
def test_merge_bandit_dedupes_and_sorts() -> None:
    p1 = {
        "results": [
            {
                "filename": "a.py",
                "line_number": 2,
                "test_id": "B101",
                "issue_severity": "HIGH",
            },
        ]
    }
    p2 = {
        "results": [
            {
                "filename": "a.py",
                "line_number": 2,
                "test_id": "B101",
                "issue_severity": "HIGH",
            },
            {
                "filename": "b.py",
                "line_number": 1,
                "test_id": "B102",
                "issue_severity": "MEDIUM",
            },
        ]
    }
    out = merge_bandit_raw_payloads([p1, p2])
    assert list(out.keys()) == ["results"]
    assert len(out["results"]) == 2
    assert out["results"][0]["filename"] == "a.py"
    assert out["results"][1]["filename"] == "b.py"


@pytest.mark.unit
def test_merge_bandit_empty_payloads() -> None:
    assert merge_bandit_raw_payloads([]) == {"results": []}


@pytest.mark.unit
def test_merge_pyright_dedupes_same_diagnostic() -> None:
    d = {
        "file": "a.py",
        "severity": "error",
        "message": "m",
        "range": {
            "start": {"line": 1, "character": 0},
            "end": {"line": 1, "character": 1},
        },
        "rule": "R",
    }
    p1 = {
        "version": "1",
        "summary": {"errorCount": 1, "warningCount": 0, "informationCount": 0},
        "generalDiagnostics": [d],
    }
    p2 = {
        "version": "1",
        "summary": {"errorCount": 1, "warningCount": 0, "informationCount": 0},
        "generalDiagnostics": [dict(d)],
    }
    merged = merge_pyright_json_payloads([p1, p2])
    assert len(merged["generalDiagnostics"]) == 1
    assert merged["summary"]["errorCount"] == 1
    assert pyright_diagnostic_identity(merged["generalDiagnostics"][0]) == (
        "a.py",
        1,
        0,
        "error",
        "R",
        "m",
    )


@pytest.mark.unit
def test_merge_pyright_empty_payloads() -> None:
    out = merge_pyright_json_payloads([])
    assert out["generalDiagnostics"] == []
