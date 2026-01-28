#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Dependency Pattern Analyzer
Analyzes dependency patterns, circular dependencies, and risk areas.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
# Note: ensure_ascii is imported but not used in this module

# Load external config on module import
if __name__ != "__main__" and __package__ and "." in __package__:
    from .. import config
else:
    from development_tools import config

config.load_external_config()

logger = get_component_logger("development_tools")


class DependencyPatternAnalyzer:
    """Analyzes dependency patterns, circular dependencies, and risk areas."""

    def analyze_dependency_patterns(
        self, actual_imports: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Analyze dependency patterns for AI consumption."""
        patterns = {
            "core_dependencies": [],
            "communication_dependencies": [],
            "ui_dependencies": [],
            "third_party_dependencies": [],
            "circular_dependencies": [],
            "high_coupling": [],
        }

        # Analyze dependency patterns
        for file_path, data in actual_imports.items():
            local_imports = data["imports"].get("local", [])
            third_party_imports = data["imports"].get("third_party", [])

            # Core dependencies
            if file_path.startswith("core/"):
                patterns["core_dependencies"].append(
                    {
                        "file": file_path,
                        "local_imports": len(local_imports),
                        "third_party_imports": len(third_party_imports),
                        "modules": [imp["module"] for imp in local_imports],
                    }
                )

            # Communication/AI dependencies
            elif file_path.startswith("communication/") or file_path.startswith("ai/"):
                patterns["communication_dependencies"].append(
                    {
                        "file": file_path,
                        "local_imports": len(local_imports),
                        "third_party_imports": len(third_party_imports),
                        "modules": [imp["module"] for imp in local_imports],
                    }
                )

            # UI dependencies
            elif file_path.startswith("ui/"):
                patterns["ui_dependencies"].append(
                    {
                        "file": file_path,
                        "local_imports": len(local_imports),
                        "third_party_imports": len(third_party_imports),
                        "modules": [imp["module"] for imp in local_imports],
                    }
                )

            # High coupling detection
            if len(local_imports) > 5:
                patterns["high_coupling"].append(
                    {
                        "file": file_path,
                        "import_count": len(local_imports),
                        "modules": [imp["module"] for imp in local_imports],
                    }
                )

            # Third-party dependencies
            if third_party_imports:
                patterns["third_party_dependencies"].append(
                    {
                        "file": file_path,
                        "dependencies": [imp["module"] for imp in third_party_imports],
                    }
                )

        # Detect circular dependencies
        patterns["circular_dependencies"] = self.detect_circular_dependencies(
            actual_imports
        )

        return patterns

    def detect_circular_dependencies(
        self, actual_imports: Dict[str, Dict]
    ) -> List[Tuple[str, str]]:
        """Detect potential circular dependencies."""
        circular = []

        for file_path, data in actual_imports.items():
            local_imports = [imp["module"] for imp in data["imports"]["local"]]

            # Check if imported modules also import this module
            for imported_module in local_imports:
                # Convert module name to file path
                module_file = imported_module.replace(".", "/") + ".py"

                if module_file in actual_imports:
                    imported_data = actual_imports[module_file]
                    imported_local = [
                        imp["module"] for imp in imported_data["imports"]["local"]
                    ]

                    # Convert current file to module name
                    current_module = file_path.replace("/", ".").replace(".py", "")

                    if current_module in imported_local:
                        pair = tuple(sorted([file_path, module_file]))
                        if pair not in circular:
                            circular.append(pair)

        return circular

    def detect_risk_areas(
        self, actual_imports: Dict[str, Dict], patterns: Dict[str, Any]
    ) -> str:
        """Detect dependency risk areas dynamically."""
        lines = []

        # High coupling
        high_coupling = patterns.get("high_coupling", [])
        if high_coupling:
            lines.append("### High Coupling")
            for item in sorted(
                high_coupling, key=lambda x: x["import_count"], reverse=True
            )[:5]:
                lines.append(
                    f"- `{item['file']}` -> {item['import_count']} local dependencies (heavy coupling)"
                )
            lines.append("")

        # Third-party risks
        third_party = patterns.get("third_party_dependencies", [])
        if third_party:
            lines.append("### Third-Party Risks")
            third_party_map = {}
            for item in third_party:
                for dep in item["dependencies"]:
                    if dep not in third_party_map:
                        third_party_map[dep] = []
                    third_party_map[dep].append(item["file"])

            for dep, files in sorted(
                third_party_map.items(), key=lambda x: len(x[1]), reverse=True
            )[:5]:
                lines.append(f"- `{files[0]}` -> {dep} ({len(files)} modules use this)")
            lines.append("")

        # Circular dependencies
        circular = patterns.get("circular_dependencies", [])
        if circular:
            lines.append("### Circular Dependencies to Monitor")
            for pair in circular[:5]:
                lines.append(f"- `{pair[0]}` <-> `{pair[1]}`")
            lines.append("")

        return "\n".join(lines) if lines else "*No significant risk areas detected*"

    def find_critical_dependencies(self, actual_imports: Dict[str, Dict]) -> str:
        """Find critical dependencies dynamically."""
        lines = []

        # Entry points
        entry_points = [
            f for f in actual_imports.keys() if "run_" in f or f.endswith("main.py")
        ]
        if entry_points:
            lines.append("### Entry Points")
            for ep in entry_points[:5]:
                deps = self._format_module_dependencies(ep, actual_imports)
                purpose = (
                    "main application entry" if "run_" in ep else "application entry"
                )
                lines.append(f"- `{ep}` -> {deps} ({purpose})")
            lines.append("")

        # Data flow
        data_modules = [
            f
            for f in actual_imports.keys()
            if "user_data" in f or "file_operations" in f
        ]
        if data_modules:
            lines.append("### Data Flow")
            for mod in data_modules[:3]:
                deps = self._format_module_dependencies(mod, actual_imports)
                lines.append(f"- {mod.split('/')[-1]}: {mod} <- {deps}")
            lines.append("")

        # Communication flow
        comm_modules = [
            f for f in actual_imports.keys() if f.startswith("communication/")
        ]
        if comm_modules:
            lines.append("### Communication Flow")
            for mod in comm_modules[:3]:
                deps = self._format_module_dependencies(mod, actual_imports)
                purpose = mod.split("/")[-1].replace(".py", "")
                lines.append(f"- {purpose}: {mod} <- {deps}")
            lines.append("")

        return "\n".join(lines) if lines else "*No critical dependencies detected*"

    def _format_module_dependencies(
        self, file_path: str, actual_imports: Dict[str, Dict], max_deps: int = 5
    ) -> str:
        """Format module dependencies concisely - deduplicated and clean."""
        if file_path not in actual_imports:
            return "unknown"

        data = actual_imports[file_path]

        # Get unique dependencies (deduplicate)
        local_deps = list(
            dict.fromkeys([imp["module"] for imp in data["imports"]["local"]])
        )
        stdlib_deps = list(
            dict.fromkeys(
                [imp["module"] for imp in data["imports"]["standard_library"]]
            )
        )
        third_party_deps = list(
            dict.fromkeys([imp["module"] for imp in data["imports"]["third_party"]])
        )

        parts = []

        # Group dependencies (show top most common)
        if stdlib_deps:
            # Show most common stdlib modules
            stdlib_names = ", ".join(sorted(stdlib_deps)[:4])
            parts.append(f"standard library ({stdlib_names})")

        if third_party_deps:
            # Show most common third-party modules
            third_party_names = ", ".join(sorted(third_party_deps)[:3])
            parts.append(f"third-party ({third_party_names})")

        if local_deps:
            # Extract module names (last part of dotted path) and deduplicate
            local_names = list(dict.fromkeys([d.split(".")[-1] for d in local_deps]))
            # Show most relevant local dependencies
            local_display = ", ".join(local_names[:max_deps])
            if len(local_names) > max_deps:
                local_display += f" (+{len(local_names) - max_deps} more)"
            parts.append(local_display)

        return ", ".join(parts) if parts else "none"

    def generate_dependency_patterns_section(
        self, patterns: Dict[str, Any], actual_imports: Dict[str, Dict]
    ) -> str:
        """Generate dependency patterns section dynamically."""
        lines = []

        # Core -> Communication/AI pattern
        comm_ai_deps = patterns.get("communication_dependencies", [])
        if comm_ai_deps:
            lines.append("### Core -> Communication and AI (most common)")
            lines.append("Communication and AI modules depend on core system modules.")
            for item in comm_ai_deps[:3]:
                core_deps = [m for m in item["modules"] if m.startswith("core.")]
                if core_deps:
                    lines.append(f"- `{item['file']}` -> {', '.join(core_deps[:3])}")
            lines.append("")

        # UI -> Core pattern
        ui_deps = patterns.get("ui_dependencies", [])
        if ui_deps:
            lines.append("### UI -> Core")
            lines.append("UI modules rely on core configuration and data access.")
            for item in ui_deps[:3]:
                core_deps = [m for m in item["modules"] if m.startswith("core.")]
                if core_deps:
                    lines.append(f"- `{item['file']}` -> {', '.join(core_deps[:3])}")
            lines.append("")

        # Communication -> Communication pattern
        if comm_ai_deps:
            lines.append("### Communication -> Communication")
            lines.append(
                "Communication modules compose other communication utilities for complete flows."
            )
            for item in comm_ai_deps[:3]:
                comm_deps = [
                    m
                    for m in item["modules"]
                    if m.startswith("communication.") or m.startswith("ai.")
                ]
                if comm_deps:
                    lines.append(f"- `{item['file']}` -> {', '.join(comm_deps[:3])}")
            lines.append("")

        # Third-party integration
        third_party = patterns.get("third_party_dependencies", [])
        if third_party:
            lines.append("### Third-Party Integration")
            lines.append("External libraries provide channel and UI support.")
            for item in third_party[:5]:
                deps = ", ".join(item["dependencies"][:2])
                lines.append(f"- `{item['file']}` -> {deps}")
            lines.append("")

        return "\n".join(lines) if lines else "*No patterns detected*"

    def generate_quick_reference(
        self, actual_imports: Dict[str, Dict], patterns: Dict[str, Any]
    ) -> str:
        """Generate quick reference section dynamically."""
        lines = []

        lines.append("### Common Patterns")
        lines.append(
            "1. Core system modules expose utilities with minimal dependencies."
        )
        lines.append(
            "2. Communication and AI modules depend on core and peer communication modules."
        )
        lines.append("3. UI modules rely on the UI framework and core services.")
        lines.append("4. Data access modules rely on configuration plus logging.")
        lines.append("")

        lines.append("### Dependency Guidelines")
        lines.append(
            "- Prefer core modules for shared logic instead of duplicating functionality."
        )
        lines.append(
            "- Avoid circular dependencies; break them with interfaces or utility modules."
        )
        lines.append(
            "- Use dependency injection for testability when modules call into services."
        )
        lines.append("- Keep third-party usage wrapped by dedicated modules.")
        lines.append("")

        # Module organization
        lines.append("### Module Organisation")
        directories = {}
        for file_path in actual_imports.keys():
            parts = file_path.split("/")
            if len(parts) > 1:
                top_dir = parts[0]
                if top_dir not in directories:
                    directories[top_dir] = []
                directories[top_dir].append(file_path)

        descriptions = {
            "core": "System utilities (minimal dependencies)",
            "communication": "Channels and message processing (depends on core)",
            "ai": "Chatbot functionality (depends on core)",
            "ui": "User interface (depends on core, limited communication dependencies)",
            "user": "User context (depends on core)",
            "tasks": "Task management (depends on core)",
        }

        for dir_name in sorted(directories.keys()):
            desc = descriptions.get(dir_name, "Module directory")
            lines.append(f"- `{dir_name}/` - {desc}")

        return "\n".join(lines)

    def build_dynamic_decision_trees(self, actual_imports: Dict[str, Dict]) -> str:
        """Build dynamic decision trees based on actual imports."""
        lines = []

        # Core System Decision Tree
        core_modules = [f for f in actual_imports.keys() if f.startswith("core/")]
        if core_modules:
            lines.append("### Need Core System Access?")
            lines.append("Core System Dependencies:")

            # Group by common patterns
            config_modules = [f for f in core_modules if "config" in f]
            logger_modules = [f for f in core_modules if "logger" in f]
            data_modules = [
                f for f in core_modules if "user_data" in f or "file_operations" in f
            ]
            error_modules = [f for f in core_modules if "error" in f]

            if config_modules or logger_modules:
                lines.append("- Configuration and Setup")
                for mod in (config_modules + logger_modules)[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            if data_modules:
                lines.append("- Data Management")
                for mod in data_modules[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            if error_modules:
                lines.append("- Error Handling")
                for mod in error_modules[:2]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")
            lines.append("")

        # AI/Chatbot Decision Tree
        ai_modules = [
            f
            for f in actual_imports.keys()
            if f.startswith("ai/") or (f.startswith("user/") and "context" in f)
        ]
        comm_modules = [
            f for f in actual_imports.keys() if f.startswith("communication/")
        ]
        if ai_modules or comm_modules:
            lines.append("### Need AI or Chatbot Support?")
            lines.append("AI System Dependencies:")

            if ai_modules:
                lines.append("- AI Core")
                for mod in ai_modules[:2]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            command_modules = [
                f for f in comm_modules if "command" in f or "interaction" in f
            ]
            if command_modules:
                lines.append("- Command Processing")
                for mod in command_modules[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            if comm_modules:
                lines.append("- Communication Integration")
                channel_modules = [
                    f for f in comm_modules if "channel" in f or "orchestrator" in f
                ]
                for mod in channel_modules[:2]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")
            lines.append("")

        # Communication Channel Decision Tree
        if comm_modules:
            lines.append("### Need Communication Channel Coverage?")
            lines.append("Communication Dependencies:")

            base_modules = [f for f in comm_modules if "base" in f or "factory" in f]
            if base_modules:
                lines.append("- Channel Infrastructure")
                for mod in base_modules[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            channel_impls = [f for f in comm_modules if "discord" in f or "email" in f]
            if channel_impls:
                lines.append("- Specific Channels")
                for mod in channel_impls[:2]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            flow_modules = [
                f for f in comm_modules if "conversation" in f or "flow" in f
            ]
            if flow_modules:
                lines.append("- Conversation Flow")
                for mod in flow_modules[:2]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")
            lines.append("")

        # UI Decision Tree
        ui_modules = [f for f in actual_imports.keys() if f.startswith("ui/")]
        if ui_modules:
            lines.append("### Need UI Dependencies?")
            lines.append("UI Dependencies:")

            main_ui = [f for f in ui_modules if "ui_app" in f]
            if main_ui:
                lines.append("- Main Application")
                for mod in main_ui[:1]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            dialogs = [f for f in ui_modules if "dialog" in f]
            if dialogs:
                lines.append("- Dialogs")
                for mod in dialogs[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")

            widgets = [f for f in ui_modules if "widget" in f]
            if widgets:
                lines.append("- Widgets")
                for mod in widgets[:3]:
                    deps = self._format_module_dependencies(mod, actual_imports)
                    lines.append(f"  - {mod} <- {deps}")
            lines.append("")

        return (
            "\n".join(lines)
            if lines
            else "*No modules detected - patterns may need updating*"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze dependency patterns")
    parser.add_argument(
        "--circular", action="store_true", help="Detect circular dependencies"
    )
    args = parser.parse_args()

    # This would need actual_imports data - typically called from generate_module_dependencies.py
    print(
        "This tool is typically used as a library. Use generate_module_dependencies.py for full analysis."
    )
