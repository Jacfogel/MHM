"""Policy tests for test-suite safety and consistency."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PROJECT_ROOT / "tests"
CATEGORY_MARKERS = {"unit", "integration", "behavior", "ui"}
TEMPFILE_CALLS_REQUIRING_DIR = {
    "mkdtemp",
    "mkstemp",
    "NamedTemporaryFile",
    "TemporaryDirectory",
}
DATETIME_NOW_ALLOWED_FILES = {
    "tests/conftest.py",
    "tests/conftest_hooks.py",
    "tests/test_helpers/test_support/conftest_hooks.py",
    "tests/development_tools/conftest.py",
    "tests/development_tools/test_changelog_trim_tooling.py",
    "tests/development_tools/test_supporting_tools.py",
    "tests/behavior/test_interaction_handlers_coverage_expansion.py",
}
PRODUCTION_LOG_REFERENCE_ALLOWED_FILES = {
    "tests/conftest.py",
    "tests/core/test_file_auditor.py",
    "tests/unit/test_logger_unit.py",
    "tests/unit/test_logging_components.py",
    "tests/behavior/test_observability_logging.py",
    "tests/behavior/test_core_service_coverage_expansion.py",
    "tests/ai/run_ai_functionality_tests.py",
}
REAL_USER_PATH_ALLOWED_FILES = {
    "tests/conftest.py",
    "tests/core/test_file_auditor.py",
    "tests/unit/debug_file_paths.py",
    "tests/behavior/test_scheduler_coverage_expansion.py",
    "tests/unit/test_config.py",
}
NO_PARALLEL_REASON_ALLOWED_FILES = {
    "tests/behavior/test_account_management_real_behavior.py",
    "tests/behavior/test_account_handler_behavior.py",
    "tests/behavior/test_backup_manager_behavior.py",
    "tests/behavior/test_checkin_handler_behavior.py",
    "tests/behavior/test_discord_bot_behavior.py",
    "tests/behavior/test_discord_checkin_retry_behavior.py",
    "tests/behavior/test_message_behavior.py",
    "tests/behavior/test_user_data_flow_architecture.py",
    "tests/behavior/test_utilities_demo.py",
    "tests/integration/test_account_lifecycle.py",
    "tests/integration/test_user_creation.py",
    "tests/ui/test_ui_app_qt_main.py",
    "tests/unit/test_user_data_manager.py",
    "tests/unit/test_user_management.py",
}


def _iter_test_python_files():
    for path in TESTS_ROOT.rglob("*.py"):
        normalized = path.as_posix()
        if "/tests/data/" in normalized or "/tests/fixtures/" in normalized:
            continue
        if normalized.endswith("/__init__.py"):
            continue
        yield path


def _extract_category_markers(decorators: list[ast.expr]) -> set[str]:
    markers: set[str] = set()
    for dec in decorators:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if not isinstance(target, ast.Attribute):
            continue

        # Handles @pytest.mark.unit and @mark.unit
        if target.attr in CATEGORY_MARKERS and isinstance(target.value, ast.Attribute):
            if target.value.attr == "mark":
                markers.add(target.attr)
                continue

        # Handles edge forms like @unit (rare, but safe to support)
        if target.attr in CATEGORY_MARKERS and isinstance(target.value, ast.Name):
            if target.value.id == "mark":
                markers.add(target.attr)
                continue

    return markers


def _is_pytest_fixture(decorators: list[ast.expr]) -> bool:
    for dec in decorators:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute):
            if target.attr == "fixture":
                return True
        elif isinstance(target, ast.Name) and target.id == "fixture":
            return True
    return False


def _extract_markers_from_pytestmark_value(node: ast.AST) -> set[str]:
    markers: set[str] = set()
    if isinstance(node, ast.List):
        for elt in node.elts:
            markers |= _extract_markers_from_pytestmark_value(elt)
        return markers
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        if node.attr in CATEGORY_MARKERS and isinstance(node.value, ast.Attribute):
            if node.value.attr == "mark":
                markers.add(node.attr)
    return markers


def _module_category_markers(tree: ast.Module) -> set[str]:
    markers: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "pytestmark":
                    markers |= _extract_markers_from_pytestmark_value(node.value)
    return markers


def _find_tempfile_policy_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    violations: list[str] = []

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return violations

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != "tempfile":
            continue
        if node.func.attr not in TEMPFILE_CALLS_REQUIRING_DIR:
            continue

        has_dir_kw = any(
            kw.arg == "dir" and not isinstance(kw.value, ast.Constant)
            or (
                kw.arg == "dir"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is not None
            )
            for kw in node.keywords
        )
        if not has_dir_kw:
            violations.append(
                f"{rel}:{node.lineno} uses tempfile.{node.func.attr} without dir= under tests/data"
            )

    # Explicitly guard against root-level temporary directory patterns.
    if not rel.endswith("tests/unit/test_test_policy_guards.py"):
        root_tmp_markers = [".tmp_devtools_unit", ".tmp_devtools_pyfiles", "Path(\".tmp", "Path('.tmp"]
        for marker in root_tmp_markers:
            if marker in text:
                violations.append(f"{rel} references root temp path marker: {marker}")

    return violations


def _lineno_to_line_map(text: str) -> dict[int, str]:
    return {i + 1: line for i, line in enumerate(text.splitlines())}


def _contains_datetime_now_call(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "now":
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "datetime":
            lines.append(node.lineno)
    return sorted(set(lines))


def _collect_production_log_reference_lines(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    logs_path_re = re.compile(r"(^|[\\/])logs([\\/]|$)")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        write_like = False
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            # open(path, mode) where mode writes.
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                if isinstance(node.args[1].value, str) and any(
                    m in node.args[1].value for m in ("w", "a", "x")
                ):
                    write_like = True
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    if isinstance(kw.value.value, str) and any(
                        m in kw.value.value for m in ("w", "a", "x")
                    ):
                        write_like = True

        if isinstance(node.func, ast.Attribute):
            if node.func.attr in {"write_text", "write_bytes", "touch", "mkdir", "makedirs"}:
                write_like = True

        if not write_like:
            continue

        candidate_strings: list[str] = []
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                candidate_strings.append(arg.value)
        for kw in node.keywords:
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                candidate_strings.append(kw.value.value)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Constant) and isinstance(node.func.value.value, str):
                candidate_strings.append(node.func.value.value)

        for value in candidate_strings:
            if not logs_path_re.search(value):
                continue
            if "tests/logs/" in value or "tests\\logs\\" in value:
                continue
            lines.append(node.lineno)
            break
    return sorted(set(lines))


def _collect_real_user_path_lines(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    risky_env_vars = {"APPDATA", "USERPROFILE", "HOME", "HOMEPATH", "HOMEDRIVE"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Path.home()
            if (
                node.func.attr == "home"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "Path"
            ):
                lines.append(node.lineno)
            # os.path.expanduser(...)
            if (
                node.func.attr == "expanduser"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "path"
            ):
                lines.append(node.lineno)
            # os.getenv("APPDATA") / os.environ.get("APPDATA")
            if node.func.attr == "get" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    if first.value in risky_env_vars:
                        lines.append(node.lineno)

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if "data/users" in value and "tests/data/users" not in value:
                # Exempt policy-file literal references.
                if value.startswith("Real user path policy violations found"):
                    continue
                lines.append(node.lineno)

    return sorted(set(lines))


def _collect_no_parallel_missing_reason_lines(path: Path, text: str, tree: ast.AST) -> list[int]:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if rel in NO_PARALLEL_REASON_ALLOWED_FILES:
        return []

    line_map = _lineno_to_line_map(text)
    violations: list[int] = []

    def has_reason(line_no: int) -> bool:
        same = line_map.get(line_no, "")
        if "#" in same:
            return True
        prev = line_map.get(line_no - 1, "").strip().lower()
        return bool(prev.startswith("#") and ("parallel" in prev or "shared" in prev or "resource" in prev))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for dec in node.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute):
                if target.attr == "no_parallel" and isinstance(target.value, ast.Attribute):
                    if target.value.attr == "mark" and not has_reason(dec.lineno):
                        violations.append(dec.lineno)

    return sorted(set(violations))


@pytest.mark.unit
def test_tempfile_writes_are_scoped_to_tests_data():
    """Policy: tempfile-based writes in tests must be scoped under tests/data via dir=."""
    violations: list[str] = []
    for path in _iter_test_python_files():
        violations.extend(_find_tempfile_policy_violations(path))

    assert not violations, "Tempfile policy violations found:\n" + "\n".join(sorted(violations))


@pytest.mark.unit
def test_pytest_tests_have_required_category_marker():
    """Policy: each pytest test function/method must include at least one category marker."""
    violations: list[str] = []

    for path in _iter_test_python_files():
        normalized = path.as_posix()
        if normalized.endswith("/conftest.py"):
            continue
        if "/tests/ai/" in normalized:
            continue
        if normalized.endswith("/run_ai_functionality_tests.py"):
            continue
        if normalized.endswith("/test_ai_functionality_manual.py"):
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
        except SyntaxError:
            continue

        rel = path.relative_to(PROJECT_ROOT).as_posix()
        module_markers = _module_category_markers(tree)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _is_pytest_fixture(node.decorator_list):
                    continue
                if node.name.startswith("test_"):
                    markers = module_markers | _extract_category_markers(node.decorator_list)
                    if not markers:
                        violations.append(f"{rel}:{node.lineno} {node.name} missing category marker")
            elif isinstance(node, ast.ClassDef):
                class_markers = module_markers | _extract_category_markers(node.decorator_list)
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name.startswith("test_"):
                        if _is_pytest_fixture(member.decorator_list):
                            continue
                        markers = class_markers | _extract_category_markers(member.decorator_list)
                        if not markers:
                            violations.append(
                                f"{rel}:{member.lineno} {node.name}.{member.name} missing category marker"
                            )

    assert not violations, "Category marker policy violations found:\n" + "\n".join(sorted(violations))


@pytest.mark.unit
def test_no_datetime_now_in_tests():
    """Policy: tests should not call datetime.now() directly."""
    violations: list[str] = []
    for path in _iter_test_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in DATETIME_NOW_ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for line_no in _contains_datetime_now_call(tree):
            violations.append(f"{rel}:{line_no} uses datetime.now(); use canonical time utilities/patch points")

    assert not violations, "datetime.now() policy violations found:\n" + "\n".join(sorted(violations))


@pytest.mark.unit
def test_no_production_logs_in_tests():
    """Policy: tests should not reference production logs/ paths."""
    violations: list[str] = []
    for path in _iter_test_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel == "tests/unit/test_test_policy_guards.py":
            continue
        if rel in PRODUCTION_LOG_REFERENCE_ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for line_no in _collect_production_log_reference_lines(tree):
            violations.append(f"{rel}:{line_no} references production logs path; use tests/logs only")

    assert not violations, "Production log reference policy violations found:\n" + "\n".join(sorted(violations))


@pytest.mark.unit
def test_no_real_user_path_usage_in_tests():
    """Policy: tests should not touch APPDATA/home dirs or direct data/users paths."""
    violations: list[str] = []
    for path in _iter_test_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel == "tests/unit/test_test_policy_guards.py":
            continue
        if rel in REAL_USER_PATH_ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for line_no in _collect_real_user_path_lines(tree):
            violations.append(f"{rel}:{line_no} references real-user path pattern")

    assert not violations, "Real user path policy violations found:\n" + "\n".join(sorted(violations))


@pytest.mark.unit
def test_no_parallel_marker_requires_reason():
    """Policy: every @pytest.mark.no_parallel should include an inline or preceding reason comment."""
    violations: list[str] = []
    for path in _iter_test_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for line_no in _collect_no_parallel_missing_reason_lines(path, text, tree):
            violations.append(f"{rel}:{line_no} @pytest.mark.no_parallel missing reason comment")

    assert not violations, "no_parallel reason policy violations found:\n" + "\n".join(sorted(violations))
