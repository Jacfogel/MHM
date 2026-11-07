"""Enforce canonical product time APIs, including scanner/exception behavior."""

import pytest

from tests.test_helpers.source_policy import product_sources, time_violations

pytestmark = [pytest.mark.unit, pytest.mark.user]

TIME_ALLOWED_FILES = {
    "core/time_utilities.py": "Canonical implementation owns clock, formatting, and parsing APIs.",
}


def test_product_uses_canonical_time_helpers():
    violations = [
        v
        for path, source in product_sources()
        for v in time_violations(source, path, TIME_ALLOWED_FILES)
    ]
    assert not violations, "\n".join(violations)


@pytest.mark.parametrize(
    "source",
    [
        "from datetime import datetime as Clock\nClock.now()",
        "import datetime as clock\nclock.datetime.now()",
        "value.strftime('%Y')",
        "from time import strptime as parse\nparse(text, '%Y')",
        "datetime.strptime(text, '%Y')",
    ],
)
def test_scanner_rejects_direct_time_calls(source):
    assert time_violations(source, "tasks/example.py", TIME_ALLOWED_FILES)


def test_time_exception_is_exact_and_requires_a_reason():
    source = "datetime.now()"
    assert not time_violations(source, "core/time_utilities.py", TIME_ALLOWED_FILES)
    assert time_violations(source, "core/time_utilities_extra.py", TIME_ALLOWED_FILES)
    assert time_violations(
        source, "core/time_utilities.py", {"core/time_utilities.py": ""}
    )


def test_scanner_ignores_comments_strings_and_canonical_calls():
    source = "# datetime.now()\ntext = 'value.strftime()'\nnow_datetime_full()\nformat_timestamp(value, fmt)"
    assert not time_violations(source, "tasks/example.py", TIME_ALLOWED_FILES)


def test_source_discovery_covers_nested_product_and_entry_points_only(tmp_path):
    paths = [
        "core/nested/example.py",
        "tasks/example.py",
        "run_mhm.py",
        "tests/example.py",
        "development_tools/example.py",
        "run_tests.py",
        "core/__pycache__/generated.py",
    ]
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass", encoding="utf-8")
    assert {path for path, _ in product_sources(tmp_path)} == {
        "core/nested/example.py",
        "tasks/example.py",
        "run_mhm.py",
    }
