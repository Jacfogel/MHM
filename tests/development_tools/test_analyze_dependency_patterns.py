"""Tests for imports/analyze_dependency_patterns.py."""

import sys
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


@pytest.mark.unit
def test_main_logs_library_usage_guidance(monkeypatch):
    """Standalone entrypoint should log usage guidance and exit cleanly."""
    messages = []

    monkeypatch.setattr(sys, "argv", ["analyze_dependency_patterns.py"])
    monkeypatch.setattr(
        dep_patterns_module.logger,
        "info",
        lambda message: messages.append(message),
    )

    exit_code = dep_patterns_module.main()

    assert exit_code == 0
    assert messages == [
        "This tool is typically used as a library. Use generate_module_dependencies.py for full analysis."
    ]


@pytest.mark.unit
def test_find_critical_dependencies_renders_entry_data_and_communication_sections():
    """Critical dependency rendering should include discovered section headers."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "run_mhm.py": _build_imports_payload(local_modules=["core.config"]),
        "core/user_data_handlers.py": _build_imports_payload(local_modules=["core.file_operations"]),
        "communication/message_processing/interaction_manager.py": _build_imports_payload(
            local_modules=["communication.core.channel_orchestrator", "core.logger"]
        ),
    }
    rendered = analyzer.find_critical_dependencies(actual_imports)
    assert "Entry Points" in rendered
    assert "Data Flow" in rendered
    assert "Communication Flow" in rendered


@pytest.mark.unit
def test_generate_dependency_patterns_section_renders_dynamic_sections():
    """Dependency pattern section should include major relationship headings."""
    analyzer = DependencyPatternAnalyzer()
    patterns = {
        "communication_dependencies": [
            {
                "file": "communication/message_processing/interaction_manager.py",
                "modules": ["core.config", "communication.core.router", "ai.chatbot"],
            }
        ],
        "ui_dependencies": [
            {"file": "ui/main.py", "modules": ["core.config", "ui.widgets"]}
        ],
        "third_party_dependencies": [
            {"file": "ui/main.py", "dependencies": ["PySide6", "pydantic"]}
        ],
    }
    rendered = analyzer.generate_dependency_patterns_section(patterns, {})
    assert "Core -> Communication and AI" in rendered
    assert "UI -> Core" in rendered
    assert "Communication -> Communication" in rendered
    assert "Third-Party Integration" in rendered


@pytest.mark.unit
def test_generate_quick_reference_and_decision_tree_outputs():
    """Quick reference and decision trees should render when imports are present."""
    analyzer = DependencyPatternAnalyzer()
    actual_imports = {
        "core/config.py": _build_imports_payload(stdlib_modules=["json"]),
        "core/logger.py": _build_imports_payload(stdlib_modules=["logging"]),
        "core/user_data_handlers.py": _build_imports_payload(local_modules=["core.config"]),
        "communication/core/channel_orchestrator.py": _build_imports_payload(local_modules=["core.logger"]),
        "communication/message_processing/conversation_flow_manager.py": _build_imports_payload(
            local_modules=["communication.core.channel_orchestrator"]
        ),
        "ai/chatbot.py": _build_imports_payload(local_modules=["core.config"]),
        "ui/ui_app_qt.py": _build_imports_payload(local_modules=["core.config"]),
        "ui/dialogs/account_dialog.py": _build_imports_payload(local_modules=["ui/ui_app_qt"]),
        "ui/widgets/tag_widget.py": _build_imports_payload(local_modules=["ui/ui_app_qt"]),
    }

    quick_ref = analyzer.generate_quick_reference(actual_imports, {})
    trees = analyzer.build_dynamic_decision_trees(actual_imports)

    assert "Dependency Guidelines" in quick_ref
    assert "`core/` - " in quick_ref
    assert "Need Core System Access?" in trees
    assert "Need AI or Chatbot Support?" in trees
    assert "Need Communication Channel Coverage?" in trees
    assert "Need UI Dependencies?" in trees
