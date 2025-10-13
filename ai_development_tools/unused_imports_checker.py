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
            file_content = ''.join(lines)
            import_name = issue.get('symbol', '')
            
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
            
            return 'obvious_unused'
            
        except Exception as e:
            if logger:
                logger.warning(f"Error categorizing import in {file_path}: {e}")
            return 'obvious_unused'
    
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
        for category in ['obvious_unused', 'type_hints_only', 're_exports', 'conditional_imports', 'star_imports']:
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
        lines.append("1. Review and remove obvious unused imports to improve code cleanliness")
        lines.append("2. For type hint imports, consider using `from __future__ import annotations` and `TYPE_CHECKING`")
        lines.append("3. Verify `__init__.py` imports are intentional re-exports")
        lines.append("4. Be cautious with conditional imports - they may be handling optional dependencies")
        lines.append("5. Consider replacing star imports with explicit imports for better clarity")
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

