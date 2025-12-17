#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Legacy Reference Analyzer (Portable)

This script analyzes codebases for legacy references. It identifies legacy patterns
but does not generate reports or perform fixes. Configuration is loaded from external
config file (development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python legacy/analyze_legacy_references.py [--find ITEM] [--verify ITEM]
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != '__main__' and __package__ and '.' in __package__:
    from .. import config
else:
    from development_tools import config

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, 'load_external_config'):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")


class LegacyReferenceAnalyzer:
    """Analyzes codebase for legacy references (portable across projects)."""
    
    def __init__(self, project_root: str = ".", legacy_tokens: Dict[str, List[str]] = None):
        """
        Initialize legacy reference analyzer.
        
        Args:
            project_root: Root directory of the project
            legacy_tokens: Optional dict of legacy pattern categories and their regex patterns.
                          If None, loads from config or uses generic defaults.
        """
        self.project_root = Path(project_root).resolve()
        
        # Load legacy configuration from external config
        legacy_config = config.get_external_value('legacy_cleanup', {})
        
        # Legacy patterns to identify (from config or provided, with generic defaults)
        if legacy_tokens is not None:
            self.legacy_patterns = legacy_tokens
        else:
            # Load from config or use generic defaults
            config_patterns = legacy_config.get('legacy_patterns', {})
            if config_patterns:
                # Convert string patterns to regex patterns (if they're strings)
                self.legacy_patterns = {}
                for category, patterns in config_patterns.items():
                    self.legacy_patterns[category] = [p if isinstance(p, str) else str(p) for p in patterns]
            else:
                # Generic defaults (projects should provide their own via config)
                self.legacy_patterns = {
                    'legacy_compatibility_markers': [
                        r'# LEGACY COMPATIBILITY:',
                        r'# LEGACY:',
                    ],
                }
        
        # Files that should be preserved (historical context)
        from development_tools.shared.standard_exclusions import LEGACY_PRESERVE_FILES
        self.preserve_files = set(LEGACY_PRESERVE_FILES)
        
        # File extensions to skip entirely
        skip_exts = legacy_config.get('skip_extensions', ['.md', '.txt', '.json', '.log'])
        self.skip_extensions = set(skip_exts) if isinstance(skip_exts, list) else skip_exts
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped from scanning."""
        # Get relative path from project root for exclusion checking
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            # File is outside project root, use absolute path
            rel_path_str = str(file_path).replace('\\', '/')
        
        # Skip the analyzer's own file to avoid false positives
        if 'analyze_legacy_references.py' in rel_path_str:
            return True
        
        # Skip test fixtures directory (intentional legacy patterns for testing)
        # Only skip if the file is in the main project's tests/fixtures directory
        # Don't skip if it's in a demo/test project (different project_root) - tests need to scan those
        try:
            main_project_root = Path('.').resolve()
            is_main_project = str(self.project_root.resolve()) == str(main_project_root)
        except (OSError, ValueError):
            # If we can't resolve paths, assume it's not the main project
            is_main_project = False
        
        if is_main_project and ('tests/fixtures/' in rel_path_str or 'tests\\fixtures\\' in rel_path_str):
            return True
        
        # Check for INTENTIONAL LEGACY marker at the top of the file
        # Only apply this check for files in the main project (not demo/test projects)
        # Demo/test projects need their legacy_code.py to be scanned for testing
        if is_main_project:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 10 lines to check for marker
                    first_lines = ''.join(f.readlines()[:10])
                    if 'INTENTIONAL LEGACY' in first_lines or '# INTENTIONAL LEGACY:' in first_lines:
                        # Only skip if it's in tests/fixtures directory or is a test file
                        if ('tests/fixtures/' in rel_path_str or 'tests\\fixtures\\' in rel_path_str or
                            'test_' in file_path.name or rel_path_str.startswith('tests/')):
                            return True
            except (IOError, UnicodeDecodeError):
                # If we can't read the file, skip it
                pass
        
        # Skip generated files
        from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES
        if rel_path_str in ALL_GENERATED_FILES:
            return True
        
        # Skip certain directories (check relative path, not absolute)
        from development_tools.shared.standard_exclusions import STANDARD_EXCLUSION_PATTERNS
        skip_dirs = [pattern.rstrip('/') for pattern in STANDARD_EXCLUSION_PATTERNS if not pattern.startswith('*')]
        for skip_dir in skip_dirs:
            path_parts = rel_path_str.split('/')
            skip_parts = skip_dir.split('/')
            if len(path_parts) >= len(skip_parts):
                if path_parts[:len(skip_parts)] == skip_parts:
                    return True
        
        # Skip preserved files
        for preserve_pattern in self.preserve_files:
            if preserve_pattern.endswith('/'):
                if preserve_pattern in rel_path_str or f'/{preserve_pattern}' in rel_path_str:
                    return True
            elif preserve_pattern == '.cursor/plans':
                if '.cursor/plans' in rel_path_str or '.cursor\\plans' in rel_path_str:
                    return True
            elif preserve_pattern.startswith('_') or preserve_pattern.endswith('_'):
                if preserve_pattern in file_path.name:
                    return True
            elif preserve_pattern in rel_path_str:
                return True
        
        # Skip certain file extensions
        if file_path.suffix.lower() in self.skip_extensions:
            return True
        
        return False
    
    def analyze_file_content(self, file_path: Path, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze file content for legacy patterns."""
        findings = defaultdict(list)
        
        for pattern_type, patterns in self.legacy_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()
                    
                    findings[pattern_type].append({
                        'pattern': pattern,
                        'match': match.group(0),
                        'line': line_num,
                        'line_content': line_content,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        return findings
    
    def scan_for_legacy_references(self) -> Dict[str, List[Tuple[str, str, List[Dict[str, Any]]]]]:
        """Scan the codebase for legacy references."""
        if logger:
            logger.info("Scanning for legacy references...")
        
        findings = defaultdict(list)
        
        # Scan Python files
        for py_file in self.project_root.rglob("*.py"):
            if self.should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_findings = self.analyze_file_content(py_file, content)
                for pattern_type, matches in file_findings.items():
                    if matches:
                        findings[pattern_type].append((str(py_file.relative_to(self.project_root)), content, matches))
                        
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {py_file}: {e}")
        
        # Scan Markdown files
        for md_file in self.project_root.rglob("*.md"):
            if self.should_skip_file(md_file):
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_findings = self.analyze_file_content(md_file, content)
                for pattern_type, matches in file_findings.items():
                    if matches:
                        findings[pattern_type].append((str(md_file.relative_to(self.project_root)), content, matches))
                        
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {md_file}: {e}")
        
        return findings
    
    def find_all_references(self, item_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find all references to a specific legacy item (function, class, module, etc.).
        
        Args:
            item_name: Name of the legacy item to search for
            
        Returns:
            Dictionary mapping file paths to lists of reference details
        """
        if logger:
            logger.info(f"Searching for all references to '{item_name}'...")
        
        references = defaultdict(list)
        
        # Patterns to search for
        search_patterns = [
            # Direct imports
            rf'from\s+[\w.]+?\s+import\s+{re.escape(item_name)}\b',
            rf'import\s+{re.escape(item_name)}\b',
            # Class and function definitions
            rf'\bclass\s+{re.escape(item_name)}\b',
            rf'\bdef\s+{re.escape(item_name)}\s*\(',
            # Usage patterns
            rf'\b{re.escape(item_name)}\s*\(',
            rf'\b{re.escape(item_name)}\s*\.',
            rf'\.{re.escape(item_name)}\b',
            # String references (in comments, docstrings, etc.)
            rf'["\']{re.escape(item_name)}["\']',
            rf'`{re.escape(item_name)}`',
        ]
        
        # Scan Python files
        for py_file in self.project_root.rglob("*.py"):
            if self.should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    content = ''.join(lines)
                    
                file_refs = []
                # Collect all matches first, then deduplicate overlapping ones
                all_matches = []
                for line_num, line in enumerate(lines, 1):
                    for pattern in search_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            all_matches.append({
                                'line': line_num,
                                'line_content': line.strip(),
                                'match': match.group(0),
                                'pattern': pattern,
                                'start': match.start(),
                                'end': match.end(),
                                'context': self._get_context(lines, line_num)
                            })
                
                # Deduplicate: remove matches that overlap on the same line
                seen_lines = {}
                for match in all_matches:
                    line_num = match['line']
                    start = match['start']
                    end = match['end']
                    
                    if line_num not in seen_lines:
                        seen_lines[line_num] = []
                    
                    should_add = True
                    to_remove = []
                    for i, existing in enumerate(seen_lines[line_num]):
                        if start == existing['start'] and end == existing['end']:
                            should_add = False
                            break
                        elif not (end <= existing['start'] or start >= existing['end']):
                            new_length = end - start
                            existing_length = existing['end'] - existing['start']
                            if new_length > existing_length:
                                to_remove.append(i)
                            else:
                                should_add = False
                                break
                    
                    for i in reversed(to_remove):
                        seen_lines[line_num].pop(i)
                    
                    if should_add:
                        seen_lines[line_num].append(match)
                
                # Flatten results and remove internal keys
                for line_matches in seen_lines.values():
                    for match in line_matches:
                        match.pop('start', None)
                        match.pop('end', None)
                        file_refs.append(match)
                
                if file_refs:
                    references[str(py_file.relative_to(self.project_root))] = file_refs
                    
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {py_file}: {e}")
        
        # Scan Markdown files
        for md_file in self.project_root.rglob("*.md"):
            if self.should_skip_file(md_file):
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                file_refs = []
                for line_num, line in enumerate(lines, 1):
                    if item_name.lower() in line.lower():
                        file_refs.append({
                            'line': line_num,
                            'line_content': line.strip(),
                            'match': item_name,
                            'pattern': 'text_search',
                            'context': self._get_context(lines, line_num)
                        })
                
                if file_refs:
                    references[str(md_file.relative_to(self.project_root))] = file_refs
                    
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {md_file}: {e}")
        
        return dict(references)
    
    def _get_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> str:
        """Get context around a line for better reference understanding."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        context = lines[start:end]
        return ''.join(context)
    
    def verify_removal_readiness(self, item_name: str) -> Dict[str, Any]:
        """
        Verify that a legacy item is ready for removal.
        
        Checks:
        - No active code references
        - No test dependencies (or tests updated)
        - Documentation references identified
        - Configuration references checked
        
        Args:
            item_name: Name of the legacy item to verify
            
        Returns:
            Dictionary with verification results and recommendations
        """
        if logger:
            logger.info(f"Verifying removal readiness for '{item_name}'...")
        
        references = self.find_all_references(item_name)
        
        # Categorize references
        active_code = []
        test_files = []
        documentation = []
        config_files = []
        archive_files = []
        
        for file_path, refs in references.items():
            file_path_lower = file_path.lower()
            
            if 'archive' in file_path_lower:
                archive_files.append((file_path, refs))
            elif file_path_lower.endswith('.md'):
                documentation.append((file_path, refs))
            elif 'test' in file_path_lower or file_path.startswith('tests/'):
                test_files.append((file_path, refs))
            elif 'config' in file_path_lower or file_path.endswith(('.json', '.yaml', '.yml', '.ini', '.toml')):
                config_files.append((file_path, refs))
            else:
                active_code.append((file_path, refs))
        
        # Determine readiness
        ready_for_removal = (
            len(active_code) == 0 and
            len(config_files) == 0
        )
        
        # Generate recommendations
        recommendations = []
        if active_code:
            recommendations.append(f"[ERROR] {len(active_code)} active code file(s) still reference '{item_name}' - must update before removal")
        if test_files:
            recommendations.append(f"[WARNING] {len(test_files)} test file(s) reference '{item_name}' - update tests or remove if testing legacy behavior")
        if config_files:
            recommendations.append(f"[ERROR] {len(config_files)} configuration file(s) reference '{item_name}' - must update before removal")
        if documentation:
            recommendations.append(f"[INFO] {len(documentation)} documentation file(s) reference '{item_name}' - update for clarity (except archive)")
        if archive_files:
            recommendations.append(f"[INFO] {len(archive_files)} archive file(s) reference '{item_name}' - can leave for historical context")
        
        if ready_for_removal:
            recommendations.append("[OK] Ready for removal - no active code or configuration references found")
        
        return {
            'item_name': item_name,
            'ready_for_removal': ready_for_removal,
            'references': references,
            'categorized': {
                'active_code': active_code,
                'test_files': test_files,
                'documentation': documentation,
                'config_files': config_files,
                'archive_files': archive_files
            },
            'counts': {
                'total_files': len(references),
                'active_code': len(active_code),
                'test_files': len(test_files),
                'documentation': len(documentation),
                'config_files': len(config_files),
                'archive_files': len(archive_files)
            },
            'recommendations': recommendations
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze codebase for legacy references")
    parser.add_argument('--find', type=str, metavar='ITEM',
                       help='Find all references to a specific legacy item (function, class, module, etc.)')
    parser.add_argument('--verify', type=str, metavar='ITEM',
                       help='Verify that a legacy item is ready for removal')
    
    args = parser.parse_args()
    
    analyzer = LegacyReferenceAnalyzer()
    
    # Handle --find command
    if args.find:
        references = analyzer.find_all_references(args.find)
        
        print(f"\nReferences to '{args.find}':")
        print(f"   Total files: {len(references)}")
        
        if references:
            for file_path, refs in sorted(references.items()):
                print(f"\n   {file_path} ({len(refs)} reference(s)):")
                for ref in refs[:5]:  # Show first 5 references per file
                    print(f"      Line {ref['line']}: {ref['line_content'][:80]}")
                if len(refs) > 5:
                    print(f"      ... and {len(refs) - 5} more")
        else:
            print("   No references found - item may be safe to remove")
        
        return
    
    # Handle --verify command
    if args.verify:
        verification = analyzer.verify_removal_readiness(args.verify)
        
        print(f"\nRemoval Readiness Verification for '{args.verify}':")
        print(f"   Status: {'READY' if verification['ready_for_removal'] else 'NOT READY'}")
        print(f"\n   Reference Summary:")
        print(f"      Total files: {verification['counts']['total_files']}")
        print(f"      Active code: {verification['counts']['active_code']}")
        print(f"      Test files: {verification['counts']['test_files']}")
        print(f"      Documentation: {verification['counts']['documentation']}")
        print(f"      Config files: {verification['counts']['config_files']}")
        print(f"      Archive files: {verification['counts']['archive_files']}")
        
        print(f"\n   Recommendations:")
        for rec in verification['recommendations']:
            rec_clean = rec.replace('❌', '[ERROR]').replace('⚠️', '[WARNING]').replace('ℹ️', '[INFO]').replace('✅', '[OK]')
            print(f"      {rec_clean}")
        
        if verification['counts']['active_code'] > 0:
            print(f"\n   Active Code Files (must update):")
            for file_path, refs in verification['categorized']['active_code']:
                print(f"      - {file_path} ({len(refs)} reference(s))")
        
        if verification['counts']['test_files'] > 0:
            print(f"\n   Test Files (update or remove):")
            for file_path, refs in verification['categorized']['test_files']:
                print(f"      - {file_path} ({len(refs)} reference(s))")
        
        return
    
    # Default: scan for legacy references
    findings = analyzer.scan_for_legacy_references()
    
    # Print summary
    total_issues = sum(len(files) for files in findings.values())
    print(f"\nLegacy Reference Analysis Complete")
    print(f"   Files with issues: {total_issues}")
    
    if total_issues > 0:
        for pattern_type, files in findings.items():
            if files:
                print(f"   {pattern_type}: {len(files)} files")


if __name__ == "__main__":
    main()

