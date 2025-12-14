#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Synchronization Checker

This script checks for paired AI/human documentation consistency.
Other documentation checks have been decomposed into separate tools:
- Path drift: analyze_path_drift.py
- ASCII compliance: analyze_ascii_compliance.py
- Heading numbering: analyze_heading_numbering.py
- Missing addresses: analyze_missing_addresses.py
- Unconverted links: analyze_unconverted_links.py
- Directory trees: generate_directory_tree.py

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/analyze_documentation_sync.py [--check]
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != '__main__' and __package__ and '.' in __package__:
    from .. import config
    from ..shared.constants import PAIRED_DOCS
else:
    from development_tools import config
    from development_tools.shared.constants import PAIRED_DOCS

logger = get_component_logger("development_tools")


class DocumentationSyncChecker:
    """Checks for paired AI/human documentation consistency."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize documentation sync checker.
        
        Args:
            project_root: Root directory of the project
            config_path: Optional path to external config file
        """
        # Load external config if provided
        if config_path:
            config.load_external_config(config_path)
        else:
            config.load_external_config()
        
        # Use provided project_root or get from config
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        
        # Load paired docs from constants (which loads from config)
        self.paired_docs = dict(PAIRED_DOCS)
    
    def check_paired_documentation(self) -> Dict[str, List[str]]:
        """Check for inconsistencies in paired AI/human documentation."""
        issues = defaultdict(list)
        
        for human_doc, ai_doc in self.paired_docs.items():
            human_path = self.project_root / human_doc
            ai_path = self.project_root / ai_doc
            
            if not human_path.exists():
                issues['missing_human_docs'].append(human_doc)
            if not ai_path.exists():
                issues['missing_ai_docs'].append(ai_doc)
                
            if human_path.exists() and ai_path.exists():
                # Check for content synchronization issues
                try:
                    with open(human_path, 'r', encoding='utf-8') as f:
                        human_content = f.read()
                    with open(ai_path, 'r', encoding='utf-8') as f:
                        ai_content = f.read()
                        
                    # Simple content comparison (could be enhanced)
                    human_sections = set(re.findall(r'^##\s+(.+)$', human_content, re.MULTILINE))
                    ai_sections = set(re.findall(r'^##\s+(.+)$', ai_content, re.MULTILINE))
                    
                    missing_in_ai = human_sections - ai_sections
                    missing_in_human = ai_sections - human_sections
                    
                    if missing_in_ai:
                        issues['content_sync'].append(f"{human_doc} has sections missing in {ai_doc}: {missing_in_ai}")
                    if missing_in_human:
                        issues['content_sync'].append(f"{ai_doc} has sections missing in {human_doc}: {missing_in_human}")
                        
                except Exception as e:
                    issues['read_errors'].append(f"Error reading {human_doc} or {ai_doc}: {e}")
                    
        return issues
    
    def run_checks(self) -> Dict[str, any]:
        """
        Run paired documentation synchronization checks and return results in standard format.
        
        Note: Other documentation checks (path drift, ASCII compliance, etc.)
        have been decomposed into separate tools. This method only checks
        paired documentation consistency.
        
        Returns:
            Dictionary with standard format: 'summary', and 'details' keys
        """
        if logger:
            logger.info("Running paired documentation synchronization checks...")
        
        paired_docs = self.check_paired_documentation()
        
        # Generate summary
        total_issues = sum(len(issues) for issues in paired_docs.values())
        status = 'PASS' if total_issues == 0 else 'FAIL'
        
        # Return standard format
        return {
            'summary': {
            'total_issues': total_issues,
                'files_affected': 0,  # Not file-based
                'status': status
            },
            'details': {
            'paired_doc_issues': total_issues,
                'paired_docs': paired_docs
            }
        }
    
    def print_report(self, results: Dict[str, any]):
        """Print a formatted report of the results."""
        summary = results['summary']
        print(f"\nSUMMARY:")
        print(f"   Status: {summary['status']}")
        print(f"   Total Issues: {summary['total_issues']}")
        print(f"   Paired Doc Issues: {summary['paired_doc_issues']}")
        
        # Paired Documentation Issues
        if results['paired_docs']:
            print(f"\nPAIRED DOCUMENTATION ISSUES:")
            for issue_type, issues in results['paired_docs'].items():
                if issues:
                    print(f"   {issue_type}:")
                    for issue in issues:
                        # Clean Unicode characters that cause encoding issues
                        clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                        print(f"     - {clean_issue}")
        
        if summary['total_issues'] == 0:
            print(f"\nAll paired documentation synchronization checks passed!")
        else:
            print(f"\nFound {summary['total_issues']} paired documentation synchronization issues.")


def main():
    """Main entry point."""
    import json
    parser = argparse.ArgumentParser(description="Check paired documentation synchronization")
    parser.add_argument('--check', action='store_true', help='Run paired documentation checks (default: always runs)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON in standard format')
    
    args = parser.parse_args()
    
    checker = DocumentationSyncChecker()
    
    # Always run checks by default (this is an analysis tool)
    # The --check flag is maintained for backward compatibility but has no effect
    results = checker.run_checks()
    
    if args.json:
        # Output JSON in standard format
        print(json.dumps(results, indent=2))
    else:
        # Convert to old format for print_report compatibility
        legacy_results = {
            'summary': {
                'total_issues': results['summary']['total_issues'],
                'paired_doc_issues': results['details']['paired_doc_issues'],
                'status': results['summary']['status']
            },
            'paired_docs': results['details']['paired_docs']
        }
        checker.print_report(legacy_results)


if __name__ == "__main__":
    main()
