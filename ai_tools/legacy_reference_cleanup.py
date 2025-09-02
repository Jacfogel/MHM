#!/usr/bin/env python3
"""
Legacy Reference Cleanup for MHM

This script identifies and helps clean up legacy references to:
- Old bot/ directory (now communication/)
- Outdated import paths
- Historical references in changelogs and archives
- Other deprecated code paths

Usage:
    python ai_tools/legacy_reference_cleanup.py [--scan] [--clean] [--dry-run]
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegacyReferenceCleanup:
    """Identifies and cleans up legacy references in MHM."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # Legacy patterns to identify
        self.legacy_patterns = {
            'old_bot_directory': [
                r'bot/',
                r'from\s+bot\.',
                r'import\s+bot\.',
                r'bot\.',
            ],
            'old_import_paths': [
                r'from\s+bot\.communication',
                r'from\s+bot\.discord',
                r'from\s+bot\.email',
            ],
            'historical_references': [
                r'bot/communication',
                r'bot/discord',
                r'bot/email',
            ],
            'deprecated_functions': [
                r'bot_',
                r'_bot_',
            ]
        }
        
        # Files that should be preserved (historical context)
        self.preserve_files = {
            'CHANGELOG_DETAIL.md',
            'AI_CHANGELOG.md',
            'archive/',
        }
        
        # Replacement mappings
        self.replacement_mappings = {
            'bot/': 'communication/',
            'from bot.': 'from communication.',
            'import bot.': 'import communication.',
            'bot.': 'communication.',
        }
    
    def scan_for_legacy_references(self) -> Dict[str, List[Tuple[str, str, List[str]]]]:
        """Scan the codebase for legacy references."""
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
                logger.warning(f"Error reading {md_file}: {e}")
        
        return findings
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped from scanning."""
        file_str = str(file_path)
        
        # Skip certain directories
        skip_dirs = ['__pycache__', '.git', '.venv', 'node_modules', 'htmlcov']
        for skip_dir in skip_dirs:
            if skip_dir in file_str:
                return True
        
        # Skip preserved files
        for preserve_pattern in self.preserve_files:
            if preserve_pattern in file_str:
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
        report_lines.append(f"**Generated**: {self.get_current_timestamp()}")
        report_lines.append("**Total Files with Issues**: " + str(sum(len(files) for files in findings.values())))
        report_lines.append("")
        
        for pattern_type, files in findings.items():
            if not files:
                continue
                
            report_lines.append(f"## {pattern_type.replace('_', ' ').title()}")
            report_lines.append(f"**Files Affected**: {len(files)}")
            report_lines.append("")
            
            for file_path, content, matches in files:
                report_lines.append(f"### {file_path}")
                report_lines.append(f"**Issues Found**: {len(matches)}")
                report_lines.append("")
                
                for match in matches:
                    report_lines.append(f"- **Line {match['line']}**: `{match['match']}`")
                    report_lines.append(f"  ```")
                    report_lines.append(f"  {match['line_content']}")
                    report_lines.append(f"  ```")
                    report_lines.append("")
        
        return '\n'.join(report_lines)
    
    def cleanup_legacy_references(self, findings: Dict[str, List[Tuple[str, str, List[str]]]], 
                                 dry_run: bool = True) -> Dict[str, List[str]]:
        """Clean up legacy references in the codebase."""
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
    
    def run(self, scan: bool = True, clean: bool = False, dry_run: bool = True) -> Dict[str, any]:
        """Run the legacy reference cleanup process."""
        results = {}
        
        if scan:
            logger.info("Starting legacy reference scan...")
            findings = self.scan_for_legacy_references()
            
            # Generate report
            report = self.generate_cleanup_report(findings)
            
            # Save report
            report_file = self.project_root / "LEGACY_REFERENCE_REPORT.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Legacy reference report saved: {report_file}")
            
            results['findings'] = findings
            results['report_file'] = str(report_file)
            
            # Print summary
            total_issues = sum(len(files) for files in findings.values())
            print(f"\n🔍 Legacy Reference Scan Complete")
            print(f"   Files with issues: {total_issues}")
            print(f"   Report saved to: {report_file}")
            
            if total_issues > 0:
                for pattern_type, files in findings.items():
                    if files:
                        print(f"   {pattern_type}: {len(files)} files")
        
        if clean and 'findings' in results:
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
    parser = argparse.ArgumentParser(description="Clean up legacy references in MHM")
    parser.add_argument('--scan', action='store_true', default=True,
                       help='Scan for legacy references (default: True)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean up found legacy references')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without making them (default: True)')
    parser.add_argument('--force', action='store_true',
                       help='Force actual changes (overrides --dry-run)')
    
    args = parser.parse_args()
    
    # Handle force flag
    if args.force:
        args.dry_run = False
    
    cleanup = LegacyReferenceCleanup()
    results = cleanup.run(scan=args.scan, clean=args.clean, dry_run=args.dry_run)
    
    if args.clean and not args.dry_run:
        print(f"\n⚠️  Legacy references have been cleaned up!")
        print(f"   Please review the changes and test the system.")
    elif args.clean and args.dry_run:
        print(f"\n💡 To apply the cleanup, run with --force")


if __name__ == "__main__":
    main()
