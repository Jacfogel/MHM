#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Module Import Analyzer
Extracts and analyzes imports from Python files.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != "__main__" and __package__ and "." in __package__:
    from .. import config
    from ..shared.common import ensure_ascii
else:
    from development_tools import config
    from development_tools.shared.common import ensure_ascii

from development_tools.shared.constants import (
    is_local_module as _is_local_module,
    is_standard_library_module as _is_stdlib_module,
)

# Load external config on module import
config.load_external_config()

logger = get_component_logger("development_tools")


class ModuleImportAnalyzer:
    """Analyzes imports from Python files."""

    def __init__(
        self,
        project_root: Optional[str] = None,
        local_prefixes: Optional[Tuple[str, ...]] = None,
    ):
        """Initialize the module import analyzer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        self.local_prefixes = local_prefixes
        try:
            from development_tools.shared.mtime_cache import MtimeFileCache

            self.cache = MtimeFileCache(
                project_root=self.project_root,
                use_cache=True,
                tool_name="analyze_module_imports",
                domain="imports",
                tool_paths=[Path(__file__)],
            )
        except Exception:
            self.cache = None

    def extract_imports_from_file(self, file_path: str) -> Dict[str, List[Dict]]:
        """Extract all imports from a Python file with detailed information."""
        # Note: Exclusion logic is handled in scan_all_python_files() before calling this function.
        # This function processes any file passed to it (including test fixtures and files in tests/),
        # so we don't apply exclusions here. This allows tests to pass file paths directly.

        # Normalize path to handle both string and Path objects, and Windows/Unix path separators
        from pathlib import Path

        file_path_obj = Path(file_path)
        # Resolve the path (handles relative paths, symlinks, etc.)
        # This is safe even if the file doesn't exist yet - resolve() just normalizes the path
        try:
            file_path = str(file_path_obj.resolve())
        except (OSError, RuntimeError):
            # If resolve fails (e.g., broken symlink), use the path as-is
            file_path = str(file_path_obj)

        imports = {"standard_library": [], "third_party": [], "local": []}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        import_info = {
                            "module": module_name,
                            "as_name": alias.asname,
                            "imported_items": [
                                module_name
                            ],  # For direct imports, the module itself
                        }

                        if self.is_standard_library(module_name):
                            imports["standard_library"].append(import_info)
                        elif self.is_local_import(module_name):
                            imports["local"].append(import_info)
                        else:
                            imports["third_party"].append(import_info)

                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module
                    if module_name:
                        # Extract specific imported items
                        imported_items = []
                        for alias in node.names:
                            if alias.name == "*":
                                imported_items.append("*")
                            else:
                                imported_items.append(alias.name)

                        import_info = {
                            "module": module_name,
                            "as_name": None,  # ImportFrom doesn't have module-level aliases
                            "imported_items": imported_items,
                        }

                        if self.is_standard_library(module_name):
                            imports["standard_library"].append(import_info)
                        elif self.is_local_import(module_name):
                            imports["local"].append(import_info)
                        else:
                            imports["third_party"].append(import_info)

        except Exception as e:
            # Only log errors for non-excluded files (excluded files are skipped above)
            logger.error(ensure_ascii(f"Error parsing {file_path}: {e}"))

        return imports

    def is_standard_library(self, module_name: str) -> bool:
        """Check if a module is part of the Python standard library."""
        return _is_stdlib_module(module_name)

    def is_local_import(self, module_name: str) -> bool:
        """
        Check if a module is a local import (part of our project).

        Args:
            module_name: The module name to check

        Returns:
            True if the module is local, False otherwise.
        """
        if self.local_prefixes is not None:
            # Use provided prefixes
            if not module_name:
                return False
            base = module_name.split(".", 1)[0]
            return base in self.local_prefixes
        # Use default from constants (which loads from config)
        return _is_local_module(module_name)

    def format_import_details(self, import_info: Dict) -> str:
        """Format import information for display - handles both list and set formats."""
        module = import_info["module"]
        imported_items = import_info.get("imported_items", [])

        # Handle both list and set formats
        if isinstance(imported_items, set):
            imported_items = sorted(list(imported_items))
        elif not isinstance(imported_items, list):
            imported_items = [imported_items] if imported_items else []

        if imported_items == [module] or "*" in imported_items or not imported_items:
            # Direct import or wildcard import or no specific items
            return module
        else:
            # Specific items imported - deduplicate and sort
            unique_items = sorted(
                list(dict.fromkeys(imported_items))
            )  # Preserve order while deduplicating
            items_str = ", ".join(unique_items)
            return ensure_ascii(f"{module} ({items_str})")

    def scan_all_python_files(self) -> Dict[str, Dict]:
        """Scan all Python files in the project and extract import information."""
        results = {}

        # Import exclusion utilities (import at module level for testability)
        from ..shared import standard_exclusions

        # Directories to scan from configuration
        scan_dirs = config.get_scan_directories()

        for scan_dir in scan_dirs:
            dir_path = self.project_root / scan_dir
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                # Use production context exclusions to match audit behavior
                if standard_exclusions.should_exclude_file(
                    str(py_file), "analysis", "production"
                ):
                    continue

                relative_path = py_file.relative_to(self.project_root)
                file_key = str(relative_path).replace("\\", "/")

                if self.cache:
                    cached = self.cache.get_cached(py_file)
                    if cached is not None:
                        results[file_key] = cached
                        continue

                imports = self.extract_imports_from_file(str(py_file))

                file_result = {
                    "imports": imports,
                    "total_imports": sum(
                        len(imp_list) for imp_list in imports.values()
                    ),
                }
                results[file_key] = file_result
                if self.cache:
                    self.cache.cache_results(py_file, file_result)

        # Also scan root directory for .py files
        for py_file in self.project_root.glob("*.py"):
            if py_file.name not in [
                "generate_function_registry.py",
                "generate_module_dependencies.py",
            ]:
                # Use production context exclusions to match audit behavior
                if standard_exclusions.should_exclude_file(
                    str(py_file), "analysis", "production"
                ):
                    continue

                file_key = py_file.name

                if self.cache:
                    cached = self.cache.get_cached(py_file)
                    if cached is not None:
                        results[file_key] = cached
                        continue

                imports = self.extract_imports_from_file(str(py_file))

                file_result = {
                    "imports": imports,
                    "total_imports": sum(
                        len(imp_list) for imp_list in imports.values()
                    ),
                }
                results[file_key] = file_result
                if self.cache:
                    self.cache.cache_results(py_file, file_result)

        if self.cache:
            self.cache.save_cache()

        return results

    def find_usage_of_module(
        self, target_module: str, all_modules: Dict[str, Dict]
    ) -> List[str]:
        """Find all modules that use the target module."""
        users = []
        for file_path, data in all_modules.items():
            if target_module in data["imports"]["local"]:
                users.append(file_path)
        return sorted(users)

    def find_reverse_dependencies(
        self, target_module: str, all_modules: Dict[str, Dict]
    ) -> List[str]:
        """Find all modules that import the target module."""
        users = []

        # Convert file path to module name (e.g., 'core/config.py' -> 'core.config')
        module_name = target_module.replace("/", ".").replace(".py", "")

        for file_path, data in all_modules.items():
            # Check local imports for the target module
            for import_info in data["imports"]["local"]:
                if import_info["module"] == module_name:
                    users.append(file_path)
                    break

        return sorted(users)

    def analyze_dependency_changes(
        self, file_path: str, data: Dict, existing_content: str
    ) -> Dict:
        """Analyze if dependencies have changed since last generation."""
        changes = {"added": [], "removed": [], "unchanged": True}

        # Extract current dependencies from the new structure
        current_deps = set()
        for import_info in data["imports"]["local"]:
            current_deps.add(import_info["module"])

        # Extract existing dependencies from content
        existing_deps = set()
        if existing_content:
            section_start = existing_content.find(ensure_ascii(f"#### `{file_path}`"))
            if section_start != -1:
                next_section = existing_content.find("#### `", section_start + 1)
                if next_section == -1:
                    section_end = len(existing_content)
                else:
                    section_end = next_section

                section_content = existing_content[section_start:section_end]

                # Extract dependencies from the section
                for line in section_content.split("\n"):
                    if line.strip().startswith("- `") and line.strip().endswith("`"):
                        dep = line.strip()[3:-1]  # Remove '- `' and '`'
                        if "." in dep:  # Only count local dependencies
                            # Extract module name from formatted string (e.g., "core.error_handling (func1, func2)" -> "core.error_handling")
                            module_name = dep.split(" (")[0]
                            existing_deps.add(module_name)

        # Calculate changes
        added = current_deps - existing_deps
        removed = existing_deps - current_deps

        if added or removed:
            changes["unchanged"] = False
            changes["added"] = sorted(added)
            changes["removed"] = sorted(removed)

        return changes

    def infer_module_purpose(
        self, file_path: str, data: Dict, all_modules: Dict[str, Dict]
    ) -> str:
        """Infer a more detailed purpose based on dependencies and usage patterns."""
        # Extract local dependencies from the new structure
        local_deps = [import_info["module"] for import_info in data["imports"]["local"]]
        reverse_deps = self.find_reverse_dependencies(file_path, all_modules)

        # Analyze dependency patterns
        core_deps = [d for d in local_deps if d.startswith("core.")]
        bot_deps = [d for d in local_deps if d.startswith("bot.")]
        ui_deps = [d for d in local_deps if d.startswith("ui.")]
        test_deps = [d for d in local_deps if "test" in d]

        # Infer purpose based on patterns
        if file_path.startswith("communication/") or file_path.startswith("ai/"):
            if "ai_chatbot" in file_path:
                return "AI chatbot implementation using LM Studio API"
            elif "base_channel" in file_path:
                return "Abstract base class for communication channels"
            elif "channel_factory" in file_path:
                return "Factory for creating communication channels"
            elif "channel_registry" in file_path:
                return "Registry for all available communication channels"
            elif "communication_manager" in file_path:
                return "Manages communication across all channels"
            elif "conversation_manager" in file_path:
                return "Manages conversation flows and check-ins"
            elif "discord_bot" in file_path:
                return "Discord bot implementation"
            elif "email_bot" in file_path:
                return "Email bot implementation"
            elif "user_context_manager" in file_path:
                return "Manages user context for AI conversations"
            else:
                return ensure_ascii(
                    f"Communication channel implementation for {file_path.split('/')[-1].replace('.py', '')}"
                )

        elif file_path.startswith("core/"):
            if "config" in file_path:
                return "Configuration management and validation"
            elif "error_handling" in file_path:
                return "Centralized error handling and recovery"
            elif "file_operations" in file_path:
                return "File operations and data management"
            elif "logger" in file_path:
                return "Logging system configuration and management"
            elif "message_management" in file_path:
                return "Message management and storage"
            elif "response_tracking" in file_path:
                return "Tracks user responses and interactions"
            elif "schedule_management" in file_path:
                return "Schedule management and time period handling"
            elif "scheduler" in file_path:
                return "Task scheduling and job management"
            elif "service" in file_path:
                return "Main service orchestration and management"
            elif "service_utilities" in file_path:
                return "Utility functions for service operations"
            elif "ui_management" in file_path:
                return "UI management and widget utilities"
            elif "user_data" in file_path:
                if "handlers" in file_path:
                    return "User data handlers with caching and validation"
                elif "manager" in file_path:
                    return "Enhanced user data management with references"
                elif "validation" in file_path:
                    return "User data validation and integrity checks"
            elif "user_data_handlers" in file_path:
                return "Centralized user data access and management"
            elif "validation" in file_path:
                return "Data validation utilities"
            elif "auto_cleanup" in file_path:
                return "Automatic cache cleanup and maintenance"
            elif "backup_manager" in file_path:
                return "Manages automatic backups and rollback operations"
            elif "checkin_analytics" in file_path:
                return "Analyzes check-in data and provides insights"
            else:
                return ensure_ascii(
                    f"Core system module for {file_path.split('/')[-1].replace('.py', '')}"
                )

        elif file_path.startswith("ui/"):
            if "dialogs" in file_path:
                return ensure_ascii(
                    f"Dialog component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}"
                )
            elif "widgets" in file_path:
                return ensure_ascii(
                    f"UI widget component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}"
                )
            elif "generated" in file_path:
                return ensure_ascii(
                    f"Auto-generated UI component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}"
                )
            elif "ui_app" in file_path:
                return "Main UI application (PyQt6)"
            else:
                return ensure_ascii(
                    f"User interface component for {file_path.split('/')[-1].replace('.py', '')}"
                )

        elif file_path.startswith("tests/"):
            if "behavior" in file_path:
                return ensure_ascii(
                    f"Behavior tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}"
                )
            elif "integration" in file_path:
                return ensure_ascii(
                    f"Integration tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}"
                )
            elif "unit" in file_path:
                return ensure_ascii(
                    f"Unit tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}"
                )
            elif "ui" in file_path:
                return ensure_ascii(
                    f"UI tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}"
                )
            else:
                return ensure_ascii(
                    f"Test file for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}"
                )

        elif file_path.startswith("user/"):
            if "user_context" in file_path:
                return "User context management"
            elif "user_preferences" in file_path:
                return "User preferences management"
            else:
                return ensure_ascii(
                    f"User data module for {file_path.split('/')[-1].replace('.py', '')}"
                )

        elif file_path.startswith("tasks/"):
            return "Task management and scheduling"

        elif file_path.endswith("run_tests.py") or "test" in file_path.lower():
            return "Test runner for the application"
        elif any(main_file in file_path for main_file in ["run_", "main.py"]):
            return "Main entry point for the application"

        # Fallback based on dependency patterns
        if len(core_deps) > len(local_deps) * 0.7:
            return f"Core system module with heavy core dependencies"
        elif len(bot_deps) > 0:
            return f"Bot-related module with communication dependencies"
        elif len(ui_deps) > 0:
            return f"UI-related module with interface dependencies"
        elif len(test_deps) > 0:
            return ensure_ascii(f"Test-related module")
        else:
            return ensure_ascii(f"Module for {file_path}")


def extract_imports_from_file(file_path: str) -> Dict[str, List[Dict]]:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().extract_imports_from_file(file_path)


def find_reverse_dependencies(
    target_module: str, all_modules: Dict[str, Dict]
) -> List[str]:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().find_reverse_dependencies(target_module, all_modules)


def analyze_dependency_changes(
    file_path: str, data: Dict, existing_content: str
) -> Dict:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().analyze_dependency_changes(
        file_path, data, existing_content
    )


def infer_module_purpose(
    file_path: str, data: Dict, all_modules: Dict[str, Dict]
) -> str:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().infer_module_purpose(file_path, data, all_modules)


def format_import_details(import_info: Dict) -> str:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().format_import_details(import_info)


def scan_all_python_files() -> Dict[str, Dict]:
    """Module-level helper for tests and callers."""
    return ModuleImportAnalyzer().scan_all_python_files()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze module imports")
    parser.add_argument("--file", type=str, help="Analyze a specific file")
    parser.add_argument("--scan", action="store_true", help="Scan all Python files")
    args = parser.parse_args()

    analyzer = ModuleImportAnalyzer()

    if args.file:
        imports = analyzer.extract_imports_from_file(args.file)
        print(f"Imports from {args.file}:")
        print(f"  Standard library: {len(imports['standard_library'])}")
        print(f"  Third-party: {len(imports['third_party'])}")
        print(f"  Local: {len(imports['local'])}")
    elif args.scan:
        results = analyzer.scan_all_python_files()
        print(f"Scanned {len(results)} files")
        total_imports = sum(data["total_imports"] for data in results.values())
        print(f"Total imports: {total_imports}")
    else:
        parser.print_help()
