#!/usr/bin/env python3
# TOOL_TIER: core

"""
Legacy Reference Cleanup Tool (Portable)

This script identifies and helps clean up legacy references. It is configurable
via development_tools_config.json to work with any project's legacy patterns.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python legacy/fix_legacy_references.py [--scan] [--clean] [--dry-run]

LEGACY CODE STANDARDS COMPLIANCE:
This tool is part of the mandatory legacy code management system. When adding new
legacy patterns, follow these requirements:
1. Add specific patterns (not broad matches like "bot" or "legacy")
2. Include replacement mappings for automated cleanup
3. Test patterns to ensure they don't create false positives
4. Document new patterns in this file's docstring
5. Update the tool when new legacy code is identified
6. Configure patterns via development_tools_config.json for portability
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
# Check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
if __name__ != '__main__' and __package__ and '.' in __package__:
    # Running as part of a package, use relative imports
    from . import config
else:
    # Running directly or not as a package, use absolute imports
    from development_tools import config

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, 'load_external_config'):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")

class LegacyReferenceCleanup:
    """Identifies and cleans up legacy references (portable across projects)."""
    
    def __init__(self, project_root: str = ".", legacy_tokens: Dict[str, List[str]] = None, 
                 replacement_mappings: Dict[str, str] = None, log_locations: List[str] = None):
        """
        Initialize legacy reference cleanup.
        
        Args:
            project_root: Root directory of the project
            legacy_tokens: Optional dict of legacy pattern categories and their regex patterns.
                          If None, loads from config or uses generic defaults.
            replacement_mappings: Optional dict mapping old patterns to new patterns.
                                  If None, loads from config or uses generic defaults.
            log_locations: Optional list of log file/directory paths to scan.
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
        # Import constants from services (which loads from config)
        from development_tools.shared.standard_exclusions import LEGACY_PRESERVE_FILES
        self.preserve_files = set(LEGACY_PRESERVE_FILES)
        
        # File extensions to skip entirely
        skip_exts = legacy_config.get('skip_extensions', ['.md', '.txt', '.json', '.log'])
        self.skip_extensions = set(skip_exts) if isinstance(skip_exts, list) else skip_exts
        
        # Replacement mappings (from config or provided, with generic defaults)
        if replacement_mappings is not None:
            self.replacement_mappings = replacement_mappings
        else:
            # Load from config or use generic defaults
            config_replacements = legacy_config.get('replacement_mappings', {})
            if config_replacements:
                self.replacement_mappings = config_replacements
            else:
                # Generic defaults (projects should provide their own via config)
                self.replacement_mappings = {}
        
        # Log locations to scan (from config or provided, with generic defaults)
        if log_locations is not None:
            self.log_locations = log_locations
        else:
            # Load from config or use generic defaults
            config_log_locations = legacy_config.get('log_locations', [])
            if config_log_locations:
                self.log_locations = config_log_locations
            else:
                # Generic defaults
                self.log_locations = ['logs/', '*.log']
    
    def scan_for_legacy_references(self) -> Dict[str, List[Tuple[str, str, List[str]]]]:
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
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped from scanning."""
        # Get relative path from project root for exclusion checking
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            # File is outside project root, use absolute path
            rel_path_str = str(file_path).replace('\\', '/')
        
        # Skip the checker's own file to avoid false positives
        # The checker defines legacy patterns, so it will match its own pattern definitions
        if 'fix_legacy_references.py' in rel_path_str:
            return True
        
        # Skip generated files
        from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES
        if rel_path_str in ALL_GENERATED_FILES:
            return True
        
        # Skip certain directories (check relative path, not absolute)
        # Import constants from services
        from development_tools.shared.standard_exclusions import STANDARD_EXCLUSION_PATTERNS
        skip_dirs = [pattern.rstrip('/') for pattern in STANDARD_EXCLUSION_PATTERNS if not pattern.startswith('*')]
        for skip_dir in skip_dirs:
            # Check if the pattern matches the relative path
            # Use path segments to avoid false matches (e.g., "tests" matching "test_something")
            path_parts = rel_path_str.split('/')
            skip_parts = skip_dir.split('/')
            # Check if skip pattern matches at the start of the path
            if len(path_parts) >= len(skip_parts):
                if path_parts[:len(skip_parts)] == skip_parts:
                    return True
        
        # Skip preserved files
        for preserve_pattern in self.preserve_files:
            # Handle directory patterns (archive/, logs/)
            if preserve_pattern.endswith('/'):
                # Match if pattern appears anywhere in path (archive/ or /archive/ or archive/something/)
                if preserve_pattern in rel_path_str or f'/{preserve_pattern}' in rel_path_str:
                    return True
            # Handle .cursor/plans directory (no trailing slash in config)
            elif preserve_pattern == '.cursor/plans':
                if '.cursor/plans' in rel_path_str or '.cursor\\plans' in rel_path_str:
                    return True
            # Handle file name patterns (_PLAN - matches files with _PLAN in name)
            elif preserve_pattern.startswith('_') or preserve_pattern.endswith('_'):
                if preserve_pattern in file_path.name:
                    return True
            # Handle exact file matches (CHANGELOG_DETAIL.md, AI_CHANGELOG.md)
            elif preserve_pattern in rel_path_str:
                return True
        
        # Skip certain file extensions
        if file_path.suffix.lower() in self.skip_extensions:
            return True
        
        return False
    
    def analyze_file_content(self, file_path: Path, content: str) -> Dict[str, List[str]]:
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
    
    def generate_cleanup_report(self, findings: Dict[str, List[Tuple[str, str, List[str]]]]) -> str:
        """Generate a report of all legacy references found."""
        report_lines = []

        report_lines.append("# Legacy Reference Cleanup Report")
        report_lines.append("")
        report_lines.append("> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`")
        report_lines.append(f"> **Generated**: {self.get_current_timestamp()}")

        affected_files = {file_path for files in findings.values() for file_path, _, _ in files}
        report_lines.append(f"**Total Files with Issues**: {len(affected_files)}")

        total_markers = sum(len(matches) for files in findings.values() for _, _, matches in files)
        report_lines.append(f"**Legacy Compatibility Markers Detected**: {total_markers}")
        report_lines.append("")

        if affected_files:
            report_lines.append("## Summary")
            report_lines.append("- Scan mode only: no automated fixes were applied.")

            legacy_entries = findings.get('legacy_compatibility_markers', [])
            if legacy_entries:
                legacy_marker_count = sum(len(matches) for _, _, matches in legacy_entries)
                report_lines.append(f"- Legacy compatibility markers remain in {len(legacy_entries)} file(s) ({legacy_marker_count} total markers).")
                enabled_fields_files = {file_path for file_path, _, matches in legacy_entries if any('enabled_fields' in (match['line_content'] or '') for match in matches)}
                if enabled_fields_files:
                    report_lines.append(f"- {len(enabled_fields_files)} file(s) still reference `enabled_fields`; confirm any clients still produce that payload.")
                preference_files = {file_path for file_path, _, matches in legacy_entries if any('Preference' in (match['line_content'] or '') for match in matches)}
                if preference_files:
                    report_lines.append(f"- {len(preference_files)} file(s) rely on legacy preference delegation paths; decide whether to modernise or retire them.")
            report_lines.append("")

        report_lines.append("## Recommended Follow-Up")
        report_lines.append("1. Confirm whether legacy `enabled_fields` payloads are still produced; if not, plan removal and data migration.")
        report_lines.append("2. Add regression tests covering analytics handler flows and user data migrations before deleting markers.")
        report_lines.append("3. Track the cleanup effort and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.")
        report_lines.append("")

        for pattern_type in sorted(findings.keys()):
            files = findings[pattern_type]
            if not files:
                continue

            report_lines.append(f"## {pattern_type.replace('_', ' ').title()}")
            report_lines.append(f"**Files Affected**: {len(files)}")
            report_lines.append("")

            for file_path, content, matches in sorted(files, key=lambda item: item[0]):
                report_lines.append(f"### {file_path}")
                report_lines.append(f"**Issues Found**: {len(matches)}")
                report_lines.append("")

                for match in sorted(matches, key=lambda m: m['line']):
                    report_lines.append(f"- **Line {match['line']}**: `{match['match']}`")
                    report_lines.append(f"  ```")
                    report_lines.append(f"  {match['line_content']}")
                    report_lines.append(f"  ```")
                    report_lines.append("")

        return '\n'.join(report_lines)

    def cleanup_legacy_references(self, findings: Dict[str, List[Tuple[str, str, List[str]]]], 
                                 dry_run: bool = True) -> Dict[str, List[str]]:
        """Clean up legacy references in the codebase."""
        if logger:
            logger.info(f"Cleaning up legacy references (dry_run={dry_run})...")
        
        cleanup_results = defaultdict(list)
        
        for pattern_type, files in findings.items():
            for file_path, content, matches in files:
                file_path_obj = self.project_root / file_path
                
                if not file_path_obj.exists():
                    continue
                
                # Sort matches by position (reverse order to avoid offset issues)
                sorted_matches = sorted(matches, key=lambda x: x['start'], reverse=True)
                
                updated_content = content
                changes_made = []
                
                for match in sorted_matches:
                    original_text = match['match']
                    replacement_text = self.get_replacement(original_text)
                    
                    if replacement_text != original_text:
                        # Replace the text
                        start = match['start']
                        end = match['end']
                        updated_content = updated_content[:start] + replacement_text + updated_content[end:]
                        
                        changes_made.append(f"Line {match['line']}: '{original_text}' → '{replacement_text}'")
                
                if changes_made:
                    if not dry_run:
                        try:
                            with open(file_path_obj, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            cleanup_results['files_updated'].append(f"{file_path} ({len(changes_made)} changes)")
                        except Exception as e:
                            cleanup_results['errors'].append(f"Error updating {file_path}: {e}")
                    else:
                        cleanup_results['files_would_update'].append(f"{file_path} ({len(changes_made)} changes)")
                    
                    cleanup_results['changes'].extend(changes_made)
        
        return cleanup_results
    
    def get_replacement(self, original_text: str) -> str:
        """Get the replacement text for a legacy reference."""
        for old_pattern, new_pattern in self.replacement_mappings.items():
            if old_pattern in original_text:
                return original_text.replace(old_pattern, new_pattern)
        return original_text
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def find_all_references(self, item_name: str) -> Dict[str, List[Dict[str, any]]]:
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
                # Keep the longest match when overlaps occur, or first match if same length
                seen_lines = {}
                for match in all_matches:
                    line_num = match['line']
                    start = match['start']
                    end = match['end']
                    
                    if line_num not in seen_lines:
                        seen_lines[line_num] = []
                    
                    # Check if this match overlaps with any existing match on this line
                    should_add = True
                    to_remove = []
                    for i, existing in enumerate(seen_lines[line_num]):
                        # Exact position match - skip duplicate (same pattern or different)
                        if start == existing['start'] and end == existing['end']:
                            should_add = False
                            break
                        # Check if ranges overlap (not disjoint)
                        elif not (end <= existing['start'] or start >= existing['end']):
                            # Overlaps found - decide which to keep
                            new_length = end - start
                            existing_length = existing['end'] - existing['start']
                            if new_length > existing_length:
                                # New match is longer - mark existing for removal
                                to_remove.append(i)
                            else:
                                # Existing is longer or same - skip adding this match
                                should_add = False
                                break
                    
                    # Remove marked items (in reverse order to maintain indices)
                    for i in reversed(to_remove):
                        seen_lines[line_num].pop(i)
                    
                    if should_add:
                        seen_lines[line_num].append(match)
                
                # Flatten results and remove internal keys
                for line_matches in seen_lines.values():
                    for match in line_matches:
                        # Remove internal deduplication keys
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
    
    def verify_removal_readiness(self, item_name: str) -> Dict[str, any]:
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
    
    def run(self, scan: bool = True, clean: bool = False, dry_run: bool = True) -> Dict[str, any]:
        """Run the legacy reference cleanup process."""
        results = {}
        
        if scan:
            if logger:
                logger.info("Starting legacy reference scan...")
            findings = self.scan_for_legacy_references()
            
            # Generate report
            report = self.generate_cleanup_report(findings)
            
            # Save report
            report_file = self.project_root / "development_docs" / "LEGACY_REFERENCE_REPORT.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            if logger:
                logger.info(f"Legacy reference report saved: {report_file}")
            
            results['findings'] = findings
            results['report_file'] = str(report_file)
            
            # Print summary
            total_issues = sum(len(files) for files in findings.values())
            print(f"\nLegacy Reference Scan Complete")
            print(f"   Files with issues: {total_issues}")
            print(f"   Report saved to: {report_file}")
            
            if total_issues > 0:
                for pattern_type, files in findings.items():
                    if files:
                        print(f"   {pattern_type}: {len(files)} files")
        
        if clean and 'findings' in results:
            if logger:
                logger.info("Starting cleanup process...")
            cleanup_results = self.cleanup_legacy_references(results['findings'], dry_run)
            
            results['cleanup'] = cleanup_results
            
            # Print cleanup summary
            if dry_run:
                print(f"\n🧹 Cleanup Preview (Dry Run)")
                print(f"   Files that would be updated: {len(cleanup_results['files_would_update'])}")
                print(f"   Total changes: {len(cleanup_results['changes'])}")
            else:
                print(f"\n✅ Cleanup Complete")
                print(f"   Files updated: {len(cleanup_results['files_updated'])}")
                print(f"   Total changes: {len(cleanup_results['changes'])}")
                
                if cleanup_results['errors']:
                    print(f"   Errors: {len(cleanup_results['errors'])}")
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Clean up legacy references in codebase")
    parser.add_argument('--scan', action='store_true', default=True,
                       help='Scan for legacy references (default: True)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean up found legacy references')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without making them (default: True)')
    parser.add_argument('--force', action='store_true',
                       help='Force actual changes (overrides --dry-run)')
    parser.add_argument('--find', type=str, metavar='ITEM',
                       help='Find all references to a specific legacy item (function, class, module, etc.)')
    parser.add_argument('--verify', type=str, metavar='ITEM',
                       help='Verify that a legacy item is ready for removal')
    
    args = parser.parse_args()
    
    cleanup = LegacyReferenceCleanup()
    
    # Handle --find command
    if args.find:
        references = cleanup.find_all_references(args.find)
        
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
        verification = cleanup.verify_removal_readiness(args.verify)
        
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
            # Remove emojis for Windows compatibility
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
    
    # Handle force flag
    if args.force:
        args.dry_run = False
    
    results = cleanup.run(scan=args.scan, clean=args.clean, dry_run=args.dry_run)
    
    if args.clean and not args.dry_run:
        print(f"\n⚠️  Legacy references have been cleaned up!")
        print(f"   Please review the changes and test the system.")
    elif args.clean and args.dry_run:
        print(f"\n💡 To apply the cleanup, run with --force")


if __name__ == "__main__":
    main()
