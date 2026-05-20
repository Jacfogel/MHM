"""
Import boundary policy tests for the ai/ package.

Documents intentional cross-layer imports and guards modules that must stay isolated.
"""

import ast
from pathlib import Path

import pytest

AI_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent / "ai"
FALLBACK_PACKAGE_DIR = AI_PACKAGE_DIR / "fallback_responses"
CONVERSATIONAL_CONTEXT_DIR = AI_PACKAGE_DIR / "conversational_context"

FORBIDDEN_COMMUNICATION_PREFIXES = (
    "communication.",
    "communication/",
)

FORBIDDEN_CHANNEL_PREFIXES = (
    "discord",
    "email",
)


def _collect_imports_from_file(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _violations_for_dir(
    package_dir: Path,
    forbidden_prefixes: tuple[str, ...],
) -> list[str]:
    violations: list[str] = []
    for py_file in package_dir.glob("*.py"):
        for module_name in _collect_imports_from_file(py_file):
            lower = module_name.lower()
            if any(
                lower.startswith(prefix) or prefix in lower
                for prefix in forbidden_prefixes
            ):
                violations.append(f"{py_file.name}: {module_name}")
    return violations


@pytest.mark.unit
@pytest.mark.ai
class TestAiImportBoundaries:
    """Enforce documented import boundaries under ai/."""

    def test_fallback_package_does_not_import_communication_or_channels(self):
        violations = _violations_for_dir(
            FALLBACK_PACKAGE_DIR,
            FORBIDDEN_COMMUNICATION_PREFIXES + FORBIDDEN_CHANNEL_PREFIXES,
        )
        assert not violations, (
            "Fallback package must stay AI-layer only; forbidden imports:\n"
            + "\n".join(violations)
        )

    def test_conversational_context_does_not_import_communication_or_channels(self):
        violations = _violations_for_dir(
            CONVERSATIONAL_CONTEXT_DIR,
            FORBIDDEN_COMMUNICATION_PREFIXES + FORBIDDEN_CHANNEL_PREFIXES,
        )
        assert not violations, (
            "conversational_context must not import communication adapters:\n"
            + "\n".join(violations)
        )

    def test_command_registry_may_import_command_parser(self):
        """Documented adapter: ai -> communication for intent names only."""
        registry_file = AI_PACKAGE_DIR / "command_registry.py"
        imports = _collect_imports_from_file(registry_file)
        assert any(
            mod.startswith("communication.message_processing.command_parser")
            for mod in imports
        ), "command_registry should import command_parser for live intent names"

    def test_command_registry_is_only_ai_module_importing_communication_parser(self):
        """Other ai/*.py files should not reach into communication.message_processing."""
        violations: list[str] = []
        for py_file in AI_PACKAGE_DIR.glob("*.py"):
            if py_file.name == "command_registry.py":
                continue
            for module_name in _collect_imports_from_file(py_file):
                if module_name.startswith("communication."):
                    violations.append(f"{py_file.name}: {module_name}")
        assert not violations, (
            "Only command_registry may import communication from ai/*.py:\n"
            + "\n".join(violations)
        )
