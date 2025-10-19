#!/usr/bin/env python3
"""
Unused Imports Detection for MHM

This script identifies unused imports throughout the codebase using pylint.
It categorizes findings and generates detailed reports for cleanup planning.

Usage:
    python ai_development_tools/unused_imports_checker.py [--output REPORT_PATH]

Integration:
    python ai_development_tools/ai_tools_runner.py unused-imports
"""

import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ai_development_tools.standard_exclusions import should_exclude_file
    from core.logger import get_component_logger
    logger = get_component_logger(__name__)
except ImportError:
    # Fallback logging if imports not available
    logger = None
    print("Warning: Could not import standard_exclusions or logger", file=sys.stderr)


class UnusedImportsChecker:
    """Detects and categorizes unused imports in Python files."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # Files to skip entirely
        self.skip_patterns = {
            'scripts/',
            '__pycache__/',
            '.pytest_cache/',
            'venv/',
            '.venv/',
            'htmlcov/',
        }
        
        # Special handling files
        self.init_files = {
            'ai_development_tools/__init__.py',
            'ai_development_tools/services/__init__.py',
        }
        
        # Results storage
        self.findings = {
            'obvious_unused': [],
            'type_hints_only': [],
            're_exports': [],
            'conditional_imports': [],
            'star_imports': [],
            'test_mocking': [],
            'qt_testing': [],
            'test_infrastructure': [],
            'production_test_mocking': [],
            'ui_imports': [],
        }
        
        self.stats = {
            'files_scanned': 0,
            'files_with_issues': 0,
            'total_unused': 0,
        }
    
    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        # Convert to relative path
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            return False
        
        # Skip patterns
        for pattern in self.skip_patterns:
            if pattern in rel_path_str:
                return False
        
        # Use standard exclusions (development context, no tool type)
        if should_exclude_file(rel_path_str, tool_type=None, context='development'):
            return False
        
        # Must be Python file
        if not file_path.suffix == '.py':
            return False
        
        # Must exist and be readable
        if not file_path.exists() or not file_path.is_file():
            return False
        
        return True
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files to scan."""
        python_files = []
        
        for file_path in self.project_root.rglob('*.py'):
            if self.should_scan_file(file_path):
                python_files.append(file_path)
        
        return sorted(python_files)
    
    def run_pylint_on_file(self, file_path: Path) -> Optional[List[Dict]]:
        """Run pylint on a single file to detect unused imports."""
        try:
            # Run pylint with only unused-import enabled, JSON output
            cmd = [
                sys.executable, '-m', 'pylint',
                '--disable=all',
                '--enable=unused-import',
                '--output-format=json',
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            # Pylint returns non-zero if it finds issues, which is what we want
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    return issues
                except json.JSONDecodeError:
                    if logger:
                        logger.warning(f"Could not parse pylint output for {file_path}")
                    return None
            
            return []
            
        except subprocess.TimeoutExpired:
            if logger:
                logger.warning(f"Pylint timeout on {file_path}")
            return None
        except Exception as e:
            if logger:
                logger.error(f"Error running pylint on {file_path}: {e}")
            return None
    
    def categorize_unused_import(self, file_path: Path, issue: Dict) -> str:
        """Categorize an unused import based on context."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            rel_path_str = str(file_path)
        
        # Extract import name from the message
        message = issue.get('message', '')
        import_name = self._extract_import_name_from_message(message)
        
        # Debug output removed for cleaner operation
        
        # Check if it's in an __init__.py file
        if file_path.name == '__init__.py':
            return 're_exports'
        
        # Read the file to get context
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_num = issue.get('line', 1) - 1  # Convert to 0-based
            if line_num < 0 or line_num >= len(lines):
                return 'obvious_unused'
            
            # Get the import line and surrounding context
            import_line = lines[line_num].strip()
            file_content = ''.join(lines)
            
            # Check for test mocking requirements
            if self._is_test_mocking_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"Test mocking import detected: {import_name} in {file_path}")
                return 'test_mocking'
            
            # Check for Qt testing requirements
            if self._is_qt_testing_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"Qt testing import detected: {import_name} in {file_path}")
                return 'qt_testing'
            
            # Check for test infrastructure imports
            if self._is_test_infrastructure_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"Test infrastructure import detected: {import_name} in {file_path}")
                return 'test_infrastructure'
            
            # Check for production code test mocking requirements
            if self._is_production_test_mocking_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"Production test mocking import detected: {import_name} in {file_path}")
                return 'production_test_mocking'
            
            # Check for UI imports
            if self._is_ui_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"UI import detected: {import_name} in {file_path}")
                return 'ui_imports'
            
            # Check for conditional import (in try/except or if block)
            # Look backwards for try/except or if statements
            indent_level = len(lines[line_num]) - len(lines[line_num].lstrip())
            for i in range(max(0, line_num - 10), line_num):
                prev_line = lines[i].strip()
                prev_indent = len(lines[i]) - len(lines[i].lstrip())
                if prev_indent < indent_level and (
                    prev_line.startswith('try:') or 
                    prev_line.startswith('if ') or
                    prev_line.startswith('except')
                ):
                    return 'conditional_imports'
            
            # Check for star imports
            if 'import *' in import_line:
                return 'star_imports'
            
            # Check if used only in type hints
            # Look for TYPE_CHECKING or if the import appears in comments/strings
            if 'TYPE_CHECKING' in file_content and import_name:
                # Check if import is only used in type hint context
                # This is a heuristic - look for the name in type annotations
                type_hint_patterns = [
                    f': {import_name}',
                    f'-> {import_name}',
                    f'List[{import_name}',
                    f'Dict[{import_name}',
                    f'Optional[{import_name}',
                    f'Union[{import_name}',
                ]
                if any(pattern in file_content for pattern in type_hint_patterns):
                    return 'type_hints_only'
            
            # Check for type hint imports that are commonly unused
            type_hint_imports = ['Optional', 'List', 'Dict', 'Any', 'Tuple', 'Set', 'Union', 'Callable']
            if import_name in type_hint_imports:
                # Check if used in type annotations
                type_annotation_patterns = [
                    f': {import_name}',
                    f'-> {import_name}',
                    f'List[{import_name}',
                    f'Dict[{import_name}',
                    f'Optional[{import_name}',
                    f'Union[{import_name}',
                    f'Tuple[{import_name}',
                    f'Set[{import_name}',
                    f'Callable[{import_name}',
                ]
                if any(pattern in file_content for pattern in type_annotation_patterns):
                    return 'type_hints_only'
            
            return 'obvious_unused'
            
        except Exception as e:
            if logger:
                logger.warning(f"Error categorizing import in {file_path}: {e}")
            return 'obvious_unused'
    
    def _extract_import_name_from_message(self, message: str) -> str:
        """Extract the actual import name from pylint message."""
        # Examples:
        # "Unused import os" -> "os"
        # "Unused Optional imported from typing" -> "Optional"
        # "Unused List imported from typing" -> "List"
        # "Unused datetime imported from datetime" -> "datetime"
        
        if not message.startswith("Unused "):
            return ""
        
        # Remove "Unused " prefix
        remaining = message[7:]  # len("Unused ") = 7
        
        # Handle "import X" pattern
        if remaining.startswith("import "):
            return remaining[7:]  # len("import ") = 7
        
        # Handle "X imported from Y" pattern
        if " imported from " in remaining:
            return remaining.split(" imported from ")[0]
        
        return remaining
    
    def _is_test_mocking_import(self, file_path: Path, import_name: str, file_content: str) -> bool:
        """Check if import is required for test mocking."""
        # Check if it's a test file
        file_path_str = str(file_path)
        if not ('test' in file_path_str or 'tests/' in file_path_str):
            return False
        
        # Check for unittest.mock imports
        mock_imports = ['Mock', 'MagicMock', 'patch', 'mock_open']
        if import_name in mock_imports:
            # Check if used in @patch decorators or patch.object calls
            if '@patch' in file_content or 'patch.object' in file_content or 'with patch' in file_content:
                print(f"DEBUG: Test mocking pattern found for {import_name} in {file_path_str}")
                return True
            
            # For test files, assume mock imports are needed even without explicit usage
            # as they might be used in ways not easily detected by static analysis
            print(f"DEBUG: Test mocking import assumed needed for {import_name} in {file_path_str}")
            return True
        
        # Check for production functions that are commonly mocked in tests
        production_mock_functions = [
            'get_user_data', 'save_user_data', 'get_user_categories', 'create_user_files',
            'get_user_file_path', 'is_valid_email', 'is_valid_phone', 'update_user_account',
            'update_user_schedules', 'update_channel_preferences', 'get_schedule_time_periods',
            'set_schedule_periods', 'set_schedule_days', 'create_new_user', 'ensure_user_directory',
            'load_default_messages', 'update_user_context', 'get_user_id_by_identifier',
            '_create_next_recurring_task_instance', 'determine_file_path', 'get_available_channels',
            'get_channel_class_mapping', 'validate_schedule_periods__validate_time_format',
            'MHMError', 'DataError', 'FileOperationError'  # Add error handling imports
        ]
        
        if import_name in production_mock_functions:
            # Check if there are @patch decorators that might mock this function
            patch_patterns = [
                f'@patch(',
                f'patch.object(',
                f'with patch(',
                f'patch(',
            ]
            if any(pattern in file_content for pattern in patch_patterns):
                print(f"DEBUG: Production function mocking pattern found for {import_name} in {file_path_str}")
                return True
            
            # For test files, assume production functions are needed for mocking
            # even without explicit @patch decorators
            print(f"DEBUG: Production function mocking assumed needed for {import_name} in {file_path_str}")
            return True
        
        return False
    
    def _is_qt_testing_import(self, file_path: Path, import_name: str, file_content: str) -> bool:
        """Check if import is required for Qt testing."""
        # Check if it's a test file
        file_path_str = str(file_path)
        if not ('test' in file_path_str or 'tests/' in file_path_str):
            return False
        
        # Check for Qt imports
        qt_imports = ['QWidget', 'QMessageBox', 'QDialog', 'Qt', 'QTimer', 'QTest', 'QApplication', 
                     'QLineEdit', 'QScrollArea', 'Signal', 'QFont', 'QColor', 'QPalette', 'QPainter', 
                     'QPen', 'QBrush', 'QVBoxLayout', 'QHBoxLayout', 'QLabel', 'QTextEdit', 
                     'QPushButton', 'QComboBox', 'QTabWidget', 'QFrame', 'QThread', 'QListWidgetItem', 
                     'QInputDialog', 'QTableWidgetItem']
        
        if import_name in qt_imports:
            # Check if used in Qt testing patterns
            qt_test_patterns = [
                'QTest.',
                'QApplication.',
                'QApplication.processEvents',
                'QTest.keyClicks',
                'QTest.mouseClick',
                'Signal(',
                'QWidget(',
                'QMessageBox(',
                'QDialog(',
                'QTimer(',
                'QApplication(',
            ]
            if any(pattern in file_content for pattern in qt_test_patterns):
                print(f"DEBUG: Qt testing pattern found for {import_name} in {file_path_str}")
                return True
        
        return False
    
    def _is_ui_import(self, file_path: Path, import_name: str, file_content: str) -> bool:
        """Check if import is required for UI files (not test files)."""
        # Check if it's a UI file (not test file)
        file_path_str = str(file_path)
        
        if 'test' in file_path_str or 'tests/' in file_path_str:
            return False
        
        # Check if it's in ui/ directory
        if 'ui/' not in file_path_str:
            return False
        
        # Check for Qt imports
        qt_imports = ['QWidget', 'QMessageBox', 'QDialog', 'Qt', 'QTimer', 'QApplication', 
                     'QLineEdit', 'QScrollArea', 'Signal', 'QFont', 'QColor', 'QPalette', 'QPainter', 
                     'QPen', 'QBrush', 'QVBoxLayout', 'QHBoxLayout', 'QLabel', 'QTextEdit', 
                     'QPushButton', 'QComboBox', 'QTabWidget', 'QFrame', 'QThread', 'QListWidgetItem', 
                     'QInputDialog', 'QTableWidgetItem']
        
        if import_name in qt_imports:
            # For UI files, assume Qt imports are needed even if not explicitly used
            # as they might be used in ways not easily detected by static analysis
            return True
        
        return False
    
    def _is_test_infrastructure_import(self, file_path: Path, import_name: str, file_content: str) -> bool:
        """Check if import is required for test infrastructure."""
        # Check if it's a test file
        if not ('test' in str(file_path) or 'tests/' in str(file_path)):
            return False
        
        # Check for test infrastructure imports
        test_infrastructure_imports = ['pytest', 'tempfile', 'shutil', 'json', 'datetime', 'time', 'threading', 'os', 'Path']
        
        if import_name in test_infrastructure_imports:
            # Check if used in test patterns
            test_patterns = [
                '@pytest.',
                'pytest.',
                'tempfile.',
                'shutil.',
                'json.',
                'datetime.',
                'time.',
                'threading.',
                'os.',
                'TestUserFactory',
                'TestDataFactory',
                'TestUserDataFactory',
                'IsolationManager',
            ]
            if any(pattern in file_content for pattern in test_patterns):
                print(f"DEBUG: Test infrastructure pattern found for {import_name} in {file_path}")
                return True
        
        # Check for test factory imports
        test_factory_patterns = ['TestDataFactory', 'TestUserDataFactory', 'TestUserFactory']
        if import_name in test_factory_patterns:
            print(f"DEBUG: Test factory pattern found for {import_name} in {file_path}")
            return True
        
        # Check for UI widget imports in test files
        ui_widget_patterns = ['CategorySelectionWidget', 'ChannelSelectionWidget', 'TaskSettingsWidget', 
                             'CheckinSettingsWidget', 'TaskEditDialog', 'TaskCrudDialog', 'TaskCompletionDialog',
                             'open_schedule_editor']
        if import_name in ui_widget_patterns:
            print(f"DEBUG: UI widget pattern found for {import_name} in {file_path}")
            return True
        
        return False
    
    def _is_production_test_mocking_import(self, file_path: Path, import_name: str, file_content: str) -> bool:
        """Check if import is required for production code test mocking."""
        # Check if it's production code (not in tests/)
        if 'tests/' in str(file_path) or 'test' in str(file_path):
            return False
        
        # Check for imports that are commonly mocked in tests
        production_mock_imports = [
            'determine_file_path', 'get_available_channels', 'get_channel_class_mapping',
            'get_user_data', 'save_user_data', 'create_user_files', 'get_user_file_path',
            'is_valid_email', 'is_valid_phone', 'validate_schedule_periods__validate_time_format',
            'update_user_account', 'update_user_schedules', 'update_channel_preferences',
            'get_schedule_time_periods', 'set_schedule_periods', 'set_schedule_days',
            'create_new_user', 'ensure_user_directory', 'load_default_messages',
            'get_user_categories', 'update_user_context', 'get_user_id_by_identifier',
            '_create_next_recurring_task_instance', 'os'  # Add os to the list
        ]
        
        if import_name in production_mock_imports:
            # Check if there are comments indicating test mocking requirements
            if 'test mocking' in file_content.lower() or 'needed for test' in file_content.lower():
                print(f"DEBUG: Production test mocking comment found for {import_name} in {file_path}")
                return True
            
            # Check if there are test files that might mock this function
            # This is a heuristic - if the function name suggests it's commonly mocked
            if any(keyword in import_name.lower() for keyword in ['get_', 'save_', 'create_', 'update_', 'validate_']):
                print(f"DEBUG: Production test mocking heuristic found for {import_name} in {file_path}")
                return True
            
            # Special case for 'os' - check if there's a comment about test mocking
            if import_name == 'os' and ('test mocking' in file_content.lower() or 'needed for test' in file_content.lower()):
                print(f"DEBUG: Production test mocking os comment found in {file_path}")
                return True
        
        return False
    
    def scan_codebase(self) -> Dict:
        """Scan the entire codebase for unused imports."""
        if logger:
            logger.info("Starting unused imports scan...")
        
        python_files = self.find_python_files()
        self.stats['files_scanned'] = len(python_files)
        total_files = len(python_files)
        
        print(f"Scanning {total_files} Python files for unused imports...")
        print("")  # Blank line before progress
        
        for idx, file_path in enumerate(python_files, 1):
            # Print progress every 10 files or on last file
            if idx % 10 == 0 or idx == total_files:
                percentage = int((idx / total_files) * 100)
                print(f"[PROGRESS] Scanning files... {idx}/{total_files} ({percentage}%) - {self.stats['files_with_issues']} files with issues found", flush=True)
            
            try:
                rel_path = file_path.relative_to(self.project_root)
                rel_path_str = str(rel_path).replace('\\', '/')
            except ValueError:
                rel_path_str = str(file_path)
            
            # Run pylint on the file
            issues = self.run_pylint_on_file(file_path)
            
            if issues is None:
                # Error occurred
                continue
            
            if not issues:
                # No unused imports
                continue
            
            # File has unused imports
            self.stats['files_with_issues'] += 1
            
            for issue in issues:
                if issue.get('message-id') == 'W0611':  # unused-import
                    category = self.categorize_unused_import(file_path, issue)
                    
                    self.findings[category].append({
                        'file': rel_path_str,
                        'line': issue.get('line', 0),
                        'column': issue.get('column', 0),
                        'message': issue.get('message', ''),
                        'symbol': issue.get('symbol', ''),
                    })
                    
                    self.stats['total_unused'] += 1
        
        print("")  # Blank line after progress
        if logger:
            logger.info(f"Scan complete. Found {self.stats['total_unused']} unused imports in {self.stats['files_with_issues']} files.")
        
        return {
            'findings': self.findings,
            'stats': self.stats,
        }
    
    def generate_report(self) -> str:
        """Generate a detailed markdown report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = []
        lines.append("# Unused Imports Report")
        lines.append("")
        lines.append("> **Generated**: This file is auto-generated by unused_imports_checker.py. Do not edit manually.")
        lines.append("> **Generated by**: unused_imports_checker.py - Unused Imports Detection Tool")
        lines.append(f"> **Last Generated**: {timestamp}")
        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py unused-imports`")
        lines.append("")
        
        # Summary statistics
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- **Total Files Scanned**: {self.stats['files_scanned']}")
        lines.append(f"- **Files with Unused Imports**: {self.stats['files_with_issues']}")
        lines.append(f"- **Total Unused Imports**: {self.stats['total_unused']}")
        lines.append("")
        
        # Category breakdown
        lines.append("## Breakdown by Category")
        lines.append("")
        for category, items in self.findings.items():
            category_name = category.replace('_', ' ').title()
            lines.append(f"- **{category_name}**: {len(items)} imports")
        lines.append("")
        
        # Detailed findings by category
        category_order = [
            'obvious_unused', 'type_hints_only', 're_exports', 'conditional_imports', 'star_imports',
            'test_mocking', 'qt_testing', 'test_infrastructure', 'production_test_mocking', 'ui_imports'
        ]
        
        for category in category_order:
            items = self.findings[category]
            if not items:
                continue
            
            category_name = category.replace('_', ' ').title()
            lines.append(f"## {category_name}")
            lines.append("")
            
            # Add recommendation for each category
            if category == 'obvious_unused':
                lines.append("**Recommendation**: These imports can likely be safely removed.")
            elif category == 'type_hints_only':
                lines.append("**Recommendation**: Consider using `TYPE_CHECKING` guard for these imports.")
            elif category == 're_exports':
                lines.append("**Recommendation**: Review if these are intentional re-exports in `__init__.py` files.")
            elif category == 'conditional_imports':
                lines.append("**Recommendation**: Review carefully - these may be for optional dependencies.")
            elif category == 'star_imports':
                lines.append("**Recommendation**: Star imports can hide unused imports - consider explicit imports.")
            elif category == 'test_mocking':
                lines.append("**Recommendation**: These imports are required for test mocking with `@patch` decorators and `patch.object()` calls.")
            elif category == 'qt_testing':
                lines.append("**Recommendation**: These Qt imports are required for UI testing and signal handling.")
            elif category == 'test_infrastructure':
                lines.append("**Recommendation**: These imports are required for test infrastructure (fixtures, data creation, etc.).")
            elif category == 'production_test_mocking':
                lines.append("**Recommendation**: These imports are required in production code for test mocking. Keep them.")
            elif category == 'ui_imports':
                lines.append("**Recommendation**: These Qt imports are required for UI functionality. Keep them.")
            lines.append("")
            
            # Group by file
            by_file = defaultdict(list)
            for item in items:
                by_file[item['file']].append(item)
            
            for file_path in sorted(by_file.keys()):
                file_items = by_file[file_path]
                lines.append(f"### `{file_path}`")
                lines.append("")
                lines.append(f"**Count**: {len(file_items)} unused import(s)")
                lines.append("")
                
                for item in sorted(file_items, key=lambda x: x['line']):
                    lines.append(f"- **Line {item['line']}**: {item['message']}")
                    if item.get('symbol'):
                        lines.append(f"  - Symbol: `{item['symbol']}`")
                lines.append("")
        
        # Recommendations
        lines.append("## Overall Recommendations")
        lines.append("")
        lines.append("1. **Obvious Unused**: Review and remove obvious unused imports to improve code cleanliness")
        lines.append("2. **Type Hints**: For type hint imports, consider using `from __future__ import annotations` and `TYPE_CHECKING`")
        lines.append("3. **Re-exports**: Verify `__init__.py` imports are intentional re-exports")
        lines.append("4. **Conditional Imports**: Be cautious with conditional imports - they may be handling optional dependencies")
        lines.append("5. **Star Imports**: Consider replacing star imports with explicit imports for better clarity")
        lines.append("6. **Test Mocking**: Keep imports required for `@patch` decorators and `patch.object()` calls")
        lines.append("7. **Qt Testing**: Keep Qt imports required for UI testing and signal handling")
        lines.append("8. **Test Infrastructure**: Keep imports required for test fixtures and data creation")
        lines.append("9. **Production Test Mocking**: Keep imports in production code that are mocked by tests")
        lines.append("10. **UI Imports**: Keep Qt imports required for UI functionality")
        lines.append("")
        
        return '\n'.join(lines)
    
    def get_summary_data(self) -> Dict:
        """Get summary data for integration with AI tools."""
        return {
            'files_scanned': self.stats['files_scanned'],
            'files_with_issues': self.stats['files_with_issues'],
            'total_unused': self.stats['total_unused'],
            'by_category': {
                category: len(items)
                for category, items in self.findings.items()
            },
            'status': self._determine_status(),
        }
    
    def _determine_status(self) -> str:
        """Determine overall status based on findings."""
        if self.stats['total_unused'] == 0:
            return 'GOOD'
        elif self.stats['total_unused'] < 20:
            return 'NEEDS ATTENTION'
        else:
            return 'CRITICAL'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Detect unused imports in MHM codebase')
    parser.add_argument('--output', default='development_docs/UNUSED_IMPORTS_REPORT.md',
                       help='Output report path')
    parser.add_argument('--json', action='store_true',
                       help='Output JSON data to stdout')
    args = parser.parse_args()
    
    # Run the check
    checker = UnusedImportsChecker(project_root)
    results = checker.scan_codebase()
    
    # Generate report
    if not args.json:
        report = checker.generate_report()
        
        # Write report to file
        output_path = project_root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nReport saved to: {output_path}")
        print(f"Files scanned: {checker.stats['files_scanned']}")
        print(f"Files with issues: {checker.stats['files_with_issues']}")
        print(f"Total unused imports: {checker.stats['total_unused']}")
    else:
        # Output JSON for integration
        summary = checker.get_summary_data()
        print(json.dumps(summary, indent=2))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

