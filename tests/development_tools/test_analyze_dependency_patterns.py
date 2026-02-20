"""Tests for imports/analyze_dependency_patterns.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


dep_patterns_module = load_development_tools_module("imports.analyze_dependency_patterns")
DependencyPatternAnalyzer = dep_patterns_module.DependencyPatternAnalyzer


def _build_imports_payload(local_modules=None, third_party_modules=None, stdlib_modules=None):
    local_modules = local_modules or []
    third_party_modules = third_party_modules or []
    stdlib_modules = stdlib_modules or []
    return {
        "imports": {
            "local": [{"module": module} for module in local_modules],
            "third_party": [{"module": module} for module in third_party_modules],
            "standard_library": [{"module": module} for module in stdlib_modules],
        }
    }


@pytest.mark.unit
def test_analyze_dependency_patterns_categorizes_and_flags_high_coupling():
    """Analyzer should split dependencies by area and detect high coupling."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "core/config.py": _build_imports_payload(
            local_modules=["core.logger", "core.errors", "core.paths"],
            third_party_modules=["pydantic"],
        ),
        "communication/discord_bot.py": _build_imports_payload(
            local_modules=["core.config", "core.service", "ai.chatbot", "communication.router", "communication.webhook", "communication.events"],
            third_party_modules=["discord"],
        ),
        "ui/main_window.py": _build_imports_payload(
            local_modules=["core.config", "core.user_data", "ui.dialogs"],
            third_party_modules=["PySide6"],
        ),
    }

    patterns = analyzer.analyze_dependency_patterns(actual_imports)

    assert len(patterns["core_dependencies"]) == 1
    assert len(patterns["communication_dependencies"]) == 1
    assert len(patterns["ui_dependencies"]) == 1
    assert any(item["file"] == "communication/discord_bot.py" for item in patterns["high_coupling"])
    assert any(item["file"] == "ui/main_window.py" for item in patterns["third_party_dependencies"])


@pytest.mark.unit
def test_detect_circular_dependencies_returns_unique_pairs():
    """Circular dependency detector should return normalized unique pairs."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "core/a.py": _build_imports_payload(local_modules=["core.b"]),
        "core/b.py": _build_imports_payload(local_modules=["core.a"]),
        "core/c.py": _build_imports_payload(local_modules=["core.b"]),
    }

    circular = analyzer.detect_circular_dependencies(actual_imports)

    assert ("core/a.py", "core/b.py") in circular
    assert len(circular) == 1


@pytest.mark.unit
def test_detect_risk_areas_contains_expected_sections():
    """Risk area output should include coupling, third-party, and circular sections when present."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "core/a.py": _build_imports_payload(
            local_modules=[
                "core.b",
                "core.c",
                "core.d",
                "core.e",
                "core.f",
                "core.g",
            ],
            third_party_modules=["numpy"],
        ),
        "core/b.py": _build_imports_payload(local_modules=["core.a"]),
    }
    patterns = analyzer.analyze_dependency_patterns(actual_imports)

    text = analyzer.detect_risk_areas(actual_imports, patterns)

    assert "High Coupling" in text
    assert "Third-Party Risks" in text
    assert "Circular Dependencies to Monitor" in text


@pytest.mark.unit
def test_format_module_dependencies_deduplicates_and_limits():
    """Dependency formatter should deduplicate and cap local dependency display."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "core/sample.py": _build_imports_payload(
            local_modules=[
                "core.user_data",
                "core.user_data",
                "core.logger",
                "communication.router",
                "tasks.manager",
                "ui.dialog",
                "ai.chatbot",
            ],
            third_party_modules=["pydantic", "pydantic"],
            stdlib_modules=["json", "json", "pathlib"],
        )
    }

    rendered = analyzer._format_module_dependencies("core/sample.py", actual_imports, max_deps=3)

    assert "standard library (" in rendered
    assert "third-party (" in rendered
    assert "+3 more" in rendered
