#!/usr/bin/env python3
"""
Domain Mapping Infrastructure

Maps source code directories to test directories and pytest markers for test-file coverage caching.
This enables selective test execution: when source files in a domain change, only test files
covering that domain are re-run.

Usage:
    from development_tools.tests.domain_mapper import DomainMapper

    mapper = DomainMapper(project_root)
    source_domain = mapper.get_source_domain('core/service.py')
    test_domains = mapper.get_test_domains_for_source('core/service.py')
    markers = mapper.get_markers_for_source('core/service.py')
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from core.logger import get_component_logger

    logger = get_component_logger("development_tools")
except ImportError:
    logger = None


class DomainMapper:
    """
    Maps source code domains to test domains and pytest markers.

    This enables test-file coverage caching by identifying which tests cover which source domains.
    """

    # Source domain to test domain mapping
    # Maps source directory -> (test directories, pytest markers)
    SOURCE_TO_TEST_MAPPING: Dict[str, Tuple[List[str], List[str]]] = {
        "core": (["tests/core/", "tests/unit/"], ["unit", "critical"]),
        "communication": (["tests/communication/"], ["communication", "integration"]),
        "ui": (["tests/ui/"], ["ui"]),
        "tasks": ([], ["tasks"]),  # No dedicated test directory, uses markers only
        "ai": (["tests/ai/"], ["ai"]),
        "user": ([], ["user_management"]),
        "notebook": ([], ["notebook"]),
        "development_tools": (["tests/development_tools/"], []),
    }

    # Cross-domain coverage dependencies:
    # if a source domain changes, domains in this list should also be revalidated.
    DOMAIN_DEPENDENCIES: Dict[str, List[str]] = {
        "core": ["communication", "ui", "tasks", "ai", "user", "notebook"],
        "communication": ["ui", "tasks", "ai", "user"],
        "tasks": ["communication", "ui"],
        "user": ["communication", "ui", "ai"],
        "ai": ["communication", "ui"],
        "ui": [],
        "notebook": ["communication", "ui"],
        "development_tools": [],
    }

    def __init__(self, project_root: Path):
        """
        Initialize domain mapper.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.test_root = self.project_root / "tests"

        # Cache for parsed markers from test files
        self._marker_cache: Dict[Path, Set[str]] = {}

        # Build reverse mapping: source file -> domains/markers
        self._source_domain_cache: Dict[str, str] = {}
        self._test_domain_cache: Dict[str, List[str]] = {}
        self._marker_cache_for_source: Dict[str, Set[str]] = {}

    def get_source_domain(self, source_file: str) -> Optional[str]:
        """
        Get the source domain for a source file.

        Args:
            source_file: Relative path to source file (e.g., 'core/service.py')

        Returns:
            Source domain name (e.g., 'core') or None if not mapped
        """
        if source_file in self._source_domain_cache:
            return self._source_domain_cache[source_file]

        # Extract directory from file path
        source_path = Path(source_file)
        if len(source_path.parts) > 0:
            domain = source_path.parts[0]
            if domain in self.SOURCE_TO_TEST_MAPPING:
                self._source_domain_cache[source_file] = domain
                return domain

        # Check if it's in a known source directory
        for domain in self.SOURCE_TO_TEST_MAPPING.keys():
            if source_file.startswith(f"{domain}/"):
                self._source_domain_cache[source_file] = domain
                return domain

        return None

    def get_test_domains_for_source(self, source_file: str) -> List[str]:
        """
        Get test directories that cover a source file.

        Args:
            source_file: Relative path to source file (e.g., 'core/service.py')

        Returns:
            List of test directory paths (e.g., ['tests/core/', 'tests/unit/'])
        """
        if source_file in self._test_domain_cache:
            return self._test_domain_cache[source_file]

        source_domain = self.get_source_domain(source_file)
        if source_domain and source_domain in self.SOURCE_TO_TEST_MAPPING:
            test_dirs, _ = self.SOURCE_TO_TEST_MAPPING[source_domain]
            self._test_domain_cache[source_file] = test_dirs
            return test_dirs

        return []

    def get_markers_for_source(self, source_file: str) -> Set[str]:
        """
        Get pytest markers that cover a source file.

        Args:
            source_file: Relative path to source file (e.g., 'core/service.py')

        Returns:
            Set of pytest marker names (e.g., {'unit', 'critical'})
        """
        if source_file in self._marker_cache_for_source:
            return self._marker_cache_for_source[source_file]

        source_domain = self.get_source_domain(source_file)
        if source_domain and source_domain in self.SOURCE_TO_TEST_MAPPING:
            _, markers = self.SOURCE_TO_TEST_MAPPING[source_domain]
            marker_set = set(markers)
            self._marker_cache_for_source[source_file] = marker_set
            return marker_set

        return set()

    def parse_markers_from_test_file(self, test_file: Path) -> Set[str]:
        """
        Parse pytest markers from a test file.

        Args:
            test_file: Path to test file

        Returns:
            Set of marker names found in the file
        """
        if test_file in self._marker_cache:
            return self._marker_cache[test_file]

        markers = set()

        if not test_file.exists():
            self._marker_cache[test_file] = markers
            return markers

        try:
            content = test_file.read_text(encoding="utf-8")

            # Parse using AST for accurate marker detection
            try:
                tree = ast.parse(content, filename=str(test_file))

                # Find all decorators with @pytest.mark.*
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(
                        node, ast.ClassDef
                    ):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                if (
                                    isinstance(decorator.value, ast.Attribute)
                                    and decorator.value.attr == "mark"
                                    and isinstance(decorator.value.value, ast.Name)
                                    and decorator.value.value.id == "pytest"
                                ):
                                    # Found @pytest.mark.<marker>
                                    markers.add(decorator.attr)
                            elif isinstance(decorator, ast.Call):
                                # Handle @pytest.mark.<marker>() or @pytest.mark.parametrize(...)
                                if isinstance(decorator.func, ast.Attribute):
                                    if (
                                        isinstance(decorator.func.value, ast.Attribute)
                                        and decorator.func.value.attr == "mark"
                                        and isinstance(
                                            decorator.func.value.value, ast.Name
                                        )
                                        and decorator.func.value.value.id == "pytest"
                                    ):
                                        markers.add(decorator.func.attr)
            except SyntaxError:
                # Fallback to regex if AST parsing fails
                if logger:
                    logger.debug(
                        f"AST parsing failed for {test_file}, using regex fallback"
                    )
                # Regex pattern for @pytest.mark.<marker>
                pattern = r"@pytest\.mark\.(\w+)"
                matches = re.findall(pattern, content)
                markers.update(matches)

        except Exception as e:
            if logger:
                logger.debug(f"Failed to parse markers from {test_file}: {e}")

        self._marker_cache[test_file] = markers
        return markers

    def get_test_files_for_source(self, source_file: str) -> List[Path]:
        """
        Get test files that potentially cover a source file.

        Args:
            source_file: Relative path to source file (e.g., 'core/service.py')

        Returns:
            List of test file paths
        """
        test_files = []

        # Get test directories for this source domain
        test_dirs = self.get_test_domains_for_source(source_file)
        for test_dir in test_dirs:
            test_dir_path = self.project_root / test_dir
            if test_dir_path.exists():
                # Find all test files in this directory
                for test_file in test_dir_path.rglob("test_*.py"):
                    test_files.append(test_file)

        # Also find test files with matching markers
        markers = self.get_markers_for_source(source_file)
        if markers:
            # Search all test files for these markers
            for test_file in self.test_root.rglob("test_*.py"):
                file_markers = self.parse_markers_from_test_file(test_file)
                if markers.intersection(file_markers):
                    if test_file not in test_files:
                        test_files.append(test_file)

        return test_files

    def get_changed_domains(self, changed_files: List[str]) -> Set[str]:
        """
        Get set of domains that have changed files.

        Args:
            changed_files: List of relative paths to changed source files

        Returns:
            Set of domain names that have changes
        """
        changed_domains = set()
        for file_path in changed_files:
            domain = self.get_source_domain(file_path)
            if domain:
                changed_domains.add(domain)
        return self.expand_domains_with_dependencies(changed_domains)

    def expand_domains_with_dependencies(self, domains: Set[str]) -> Set[str]:
        """
        Expand domains to include transitive cross-domain dependencies.

        Args:
            domains: Initial changed domains

        Returns:
            Expanded domain set including dependent domains
        """
        expanded = set(domains)
        queue = list(domains)

        while queue:
            domain = queue.pop(0)
            for dependent_domain in self.DOMAIN_DEPENDENCIES.get(domain, []):
                if dependent_domain not in expanded:
                    expanded.add(dependent_domain)
                    queue.append(dependent_domain)

        return expanded

    def get_pytest_marker_filter(self, domains: Set[str]) -> Optional[str]:
        """
        Get pytest marker filter expression for given domains.

        Args:
            domains: Set of domain names

        Returns:
            Pytest marker filter expression (e.g., 'communication or tasks') or None
        """
        if not domains:
            return None

        # Collect all markers for these domains
        all_markers = set()
        for domain in domains:
            if domain in self.SOURCE_TO_TEST_MAPPING:
                _, markers = self.SOURCE_TO_TEST_MAPPING[domain]
                all_markers.update(markers)

        if not all_markers:
            return None

        # Create OR expression: 'marker1 or marker2 or marker3'
        return " or ".join(sorted(all_markers))

    def get_test_directories_for_domains(self, domains: Set[str]) -> List[str]:
        """
        Get test directories for given domains.

        Args:
            domains: Set of domain names

        Returns:
            List of test directory paths
        """
        test_dirs = set()
        for domain in domains:
            if domain in self.SOURCE_TO_TEST_MAPPING:
                dirs, _ = self.SOURCE_TO_TEST_MAPPING[domain]
                test_dirs.update(dirs)
        return sorted(test_dirs)

    def infer_domains_from_test_path(self, test_file: Path) -> Set[str]:
        """
        Infer test domains from file path/name when markers are missing.

        Args:
            test_file: Path to test file

        Returns:
            Set of inferred domain names
        """
        path_lower = test_file.as_posix().lower()
        inferred = set()

        keyword_map = {
            "development_tools": [
                "development_tools",
                "dev_tools",
                "audit",
                "coverage",
                "verification",
                "status",
            ],
            "communication": [
                "communication",
                "discord",
                "email",
                "webhook",
                "channel",
                "command",
                "interaction",
                "router",
            ],
            "ai": ["ai", "chatbot", "prompt", "context", "llm"],
            "tasks": ["task"],
            "ui": ["ui", "dialog", "widget", "qt", "pyside"],
            "user": ["user", "profile", "account", "preferences"],
            "notebook": ["notebook", "note", "journal", "list"],
            "core": [
                "core",
                "service",
                "scheduler",
                "config",
                "logger",
                "logging",
                "observability",
                "error",
                "backup",
                "file",
                "cleanup",
                "checkin",
                "analytics",
                "response",
            ],
        }

        for domain, keywords in keyword_map.items():
            if any(keyword in path_lower for keyword in keywords):
                inferred.add(domain)

        return inferred
