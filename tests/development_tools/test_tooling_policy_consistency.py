"""Policy tests for CLI aliases, scanner exclusions, and command-doc parity."""

from __future__ import annotations

import ast
import inspect
import os
import time
import re
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


FLAG_PATTERN = re.compile(r"""['"](--[a-z0-9][a-z0-9-]*)['"]""", re.IGNORECASE)
GLOB_DISCOVERY_PATTERN = re.compile(
    r"""\.(?:rglob|glob)\(\s*['"]\*\.(?:py|md)['"]\s*\)""",
    re.IGNORECASE,
)
OS_WALK_PATTERN = re.compile(r"""\bos\.walk\(""")


def _extract_flags(text: str) -> set[str]:
    return set(FLAG_PATTERN.findall(text))


def _build_command_flag_inventory(cli_module) -> dict[str, set[str]]:
    inventory: dict[str, set[str]] = {}
    for command_name, registration in cli_module.COMMAND_REGISTRY.items():
        inventory[command_name] = _extract_flags(inspect.getsource(registration.handler))
    return inventory


def _build_runner_flag_inventory(project_root: Path) -> set[str]:
    runner_path = project_root / "development_tools" / "run_development_tools.py"
    return _extract_flags(runner_path.read_text(encoding="utf-8", errors="replace"))


def _attribute_chain_name(node: ast.AST) -> str:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _ast_is_scanner_candidate(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = _attribute_chain_name(node.func)
        if target.endswith(".rglob") or target.endswith(".glob"):
            return True
        if target == "os.walk":
            return True
        if target.endswith(".iter_python_sources") or target == "iter_python_sources":
            return True
    return False


def _is_scanner_candidate(relative_path: str, text: str) -> bool:
    if relative_path.endswith("__init__.py"):
        return False
    # Cleanup utility traverses files but is not an analyzer policy target.
    if relative_path == "development_tools/shared/fix_project_cleanup.py":
        return False
    if relative_path.startswith("development_tools/reports/") and "analyze_" not in relative_path:
        return False
    try:
        return _ast_is_scanner_candidate(ast.parse(text))
    except SyntaxError:
        # Fallback to conservative regex heuristics for malformed sources.
        return bool(
            GLOB_DISCOVERY_PATTERN.search(text)
            or OS_WALK_PATTERN.search(text)
            or "iter_python_sources(" in text
        )


def _extract_documented_commands(doc_path: Path) -> set[str]:
    command_name_pattern = re.compile(r"^[a-z][a-z0-9-]*$")
    commands: set[str] = set()
    in_command_h2 = False
    for line in doc_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            # Keep command parity scoped to the "Running the Tool Suite" section.
            in_command_h2 = stripped.startswith("## 2.")
            continue
        if not in_command_h2:
            continue
        if not stripped.startswith("- `"):
            continue
        match = re.match(r"- `([^`]+)`", stripped)
        if not match:
            continue
        token = match.group(1).split()[0]
        if command_name_pattern.match(token):
            commands.add(token)
    return commands


def _collect_non_compliant_scanners(project_root: Path) -> list[str]:
    from development_tools.shared.standard_exclusions import should_exclude_file

    explicitly_scanner_enforced = {
        "development_tools/functions/generate_function_registry.py",
        "development_tools/functions/fix_function_docstrings.py",
        "development_tools/docs/fix_version_sync.py",
        "development_tools/static_checks/check_channel_loggers.py",
    }

    non_compliant: list[str] = []
    for py_file in sorted((project_root / "development_tools").rglob("*.py")):
        rel = py_file.relative_to(project_root).as_posix()
        if should_exclude_file(rel, tool_type="analysis", context="development"):
            continue
        base_name = py_file.name
        enforced = base_name.startswith("analyze_") or rel in explicitly_scanner_enforced
        if not enforced:
            continue
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if not _is_scanner_candidate(rel, text):
            continue
        uses_exclusions = (
            "should_exclude_file(" in text
            or "standard_exclusions.should_exclude_file(" in text
            or "iter_python_sources(" in text
        )
        if not uses_exclusions:
            non_compliant.append(rel)
    return non_compliant


@pytest.mark.unit
def test_cli_alias_policy_rules():
    cli_module = load_development_tools_module("shared.cli_interface")
    command_flags = _build_command_flag_inventory(cli_module)
    global_flags = _build_runner_flag_inventory(Path(__file__).resolve().parents[2])

    assert "--full" in command_flags["audit"]
    assert "full-audit" in command_flags
    assert "--full" in command_flags["cleanup"]
    assert "--all" in command_flags["cleanup"]
    assert "--all" in command_flags["doc-fix"]
    assert "--full" in command_flags["doc-fix"]
    assert "--clear-cache" in global_flags
    assert "--cache-clear" in global_flags


@pytest.mark.unit
def test_scanner_exclusion_policy_consistency():
    project_root = Path(__file__).resolve().parents[2]
    non_compliant = _collect_non_compliant_scanners(project_root)

    assert not non_compliant, (
        "Scanner-like file discovery found without exclusion filtering: "
        + ", ".join(non_compliant)
    )


@pytest.mark.unit
def test_command_doc_parity_policy():
    project_root = Path(__file__).resolve().parents[2]
    cli_module = load_development_tools_module("shared.cli_interface")
    active_commands = set(cli_module.COMMAND_REGISTRY.keys())

    ai_doc_commands = _extract_documented_commands(
        project_root / "development_tools" / "AI_DEVELOPMENT_TOOLS_GUIDE.md"
    )
    human_doc_commands = _extract_documented_commands(
        project_root / "development_tools" / "DEVELOPMENT_TOOLS_GUIDE.md"
    )
    documented_commands = ai_doc_commands | human_doc_commands

    aliases_not_required_in_docs = {"clean-up"}
    expected_documented = active_commands - aliases_not_required_in_docs

    missing_from_docs = sorted(expected_documented - documented_commands)
    assert not missing_from_docs, (
        "Active commands missing from docs command sections: "
        + ", ".join(missing_from_docs)
    )
    stale_in_docs = sorted(documented_commands - expected_documented)
    assert not stale_in_docs, (
        "Docs list stale/removed commands in command sections: "
        + ", ".join(stale_in_docs)
    )


@pytest.mark.unit
def test_command_group_parity_policy():
    cli_module = load_development_tools_module("shared.cli_interface")
    metadata_module = load_development_tools_module("shared.tool_metadata")

    active_commands = set(cli_module.COMMAND_REGISTRY.keys())
    grouped_commands: set[str] = set()
    for group in metadata_module.get_command_groups().values():
        grouped_commands.update(group.get("commands", []))

    unknown_grouped = sorted(grouped_commands - active_commands)
    assert not unknown_grouped, (
        "Command groups include unknown commands: " + ", ".join(unknown_grouped)
    )

    aliases_not_required_in_groups = {"full-audit", "clean-up"}
    expected_grouped = active_commands - aliases_not_required_in_groups
    missing_from_groups = sorted(expected_grouped - grouped_commands)
    assert not missing_from_groups, (
        "Active non-alias commands missing from command groups: "
        + ", ".join(missing_from_groups)
    )


@pytest.mark.unit
def test_tooling_policy_runtime_budget():
    project_root = Path(__file__).resolve().parents[2]
    cli_module = load_development_tools_module("shared.cli_interface")
    metadata_module = load_development_tools_module("shared.tool_metadata")

    max_seconds = float(os.getenv("MHM_TOOLING_POLICY_MAX_SECONDS", "12.0"))

    started = time.perf_counter()
    _build_command_flag_inventory(cli_module)
    _build_runner_flag_inventory(project_root)
    _extract_documented_commands(
        project_root / "development_tools" / "AI_DEVELOPMENT_TOOLS_GUIDE.md"
    )
    _extract_documented_commands(
        project_root / "development_tools" / "DEVELOPMENT_TOOLS_GUIDE.md"
    )
    _collect_non_compliant_scanners(project_root)
    metadata_module.get_command_groups()
    elapsed = time.perf_counter() - started

    assert elapsed <= max_seconds, (
        f"Tooling policy checks are too slow: {elapsed:.2f}s > {max_seconds:.2f}s "
        "(override with MHM_TOOLING_POLICY_MAX_SECONDS if needed)."
    )
