#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Legacy Reference Fixer (Portable)

This script fixes legacy references in codebases. It uses analysis results from
analyze_legacy_references.py to perform cleanup operations. Configuration is loaded
from external config file (development_tools_config.json) if available, making this
tool portable across different projects.

Usage:
    python legacy/fix_legacy_references.py [--scan] [--clean] [--dry-run] [--find ITEM] [--verify ITEM]

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
    from .analyze_legacy_references import LegacyReferenceAnalyzer
    from .generate_legacy_reference_report import LegacyReferenceReportGenerator
else:
    from development_tools import config
    from development_tools.legacy.analyze_legacy_references import LegacyReferenceAnalyzer
    from development_tools.legacy.generate_legacy_reference_report import LegacyReferenceReportGenerator

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, 'load_external_config'):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")

class LegacyReferenceFixer:
    """Fixes legacy references in codebases (portable across projects)."""
    
    def __init__(self, project_root: str = ".", replacement_mappings: Dict[str, str] = None):
        """
        Initialize legacy reference fixer.
        
        Args:
            project_root: Root directory of the project
            replacement_mappings: Optional dict mapping old patterns to new patterns.
                                  If None, loads from config or uses generic defaults.
        """
        self.project_root = Path(project_root).resolve()
        
        # Load legacy configuration from external config
        legacy_config = config.get_external_value('legacy_cleanup', {})
        
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
    

    def cleanup_legacy_references(self, findings: Dict[str, List[Tuple[str, str, List[Dict[str, Any]]]]], 
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
    
    def run(self, scan: bool = True, clean: bool = False, dry_run: bool = True) -> Dict[str, Any]:
        """
        Run the legacy reference cleanup process.
        
        Uses LegacyReferenceAnalyzer for analysis and LegacyReferenceReportGenerator for reports.
        
        Args:
            scan: Whether to scan for legacy references
            clean: Whether to clean up found references
            dry_run: Whether to preview changes without applying them
            
        Returns:
            Dictionary with results
        """
        results = {}
        
        if scan:
            if logger:
                logger.info("Starting legacy reference scan...")
            
            # Use analyzer for scanning
            analyzer = LegacyReferenceAnalyzer(project_root=str(self.project_root))
            findings = analyzer.scan_for_legacy_references()
            
            # Generate report using report generator
            report_generator = LegacyReferenceReportGenerator(project_root=str(self.project_root))
            report = report_generator.generate_cleanup_report(findings)
            
            # Save report
            report_file = report_generator.save_report(report)
            
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
                print(f"\nCleanup Preview (Dry Run)")
                print(f"   Files that would be updated: {len(cleanup_results['files_would_update'])}")
                print(f"   Total changes: {len(cleanup_results['changes'])}")
            else:
                print(f"\nCleanup Complete")
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
    
    # Handle --find and --verify by delegating to analyzer
    if args.find or args.verify:
        analyzer = LegacyReferenceAnalyzer()
        
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
    
    # Handle force flag
    if args.force:
        args.dry_run = False
    
    # Use fixer for cleanup operations
    fixer = LegacyReferenceFixer()
    results = fixer.run(scan=args.scan, clean=args.clean, dry_run=args.dry_run)
    
    if args.clean and not args.dry_run:
        print(f"\nLegacy references have been cleaned up!")
        print(f"   Please review the changes and test the system.")
    elif args.clean and args.dry_run:
        print(f"\nTo apply the cleanup, run with --force")


if __name__ == "__main__":
    main()
