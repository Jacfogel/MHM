#!/usr/bin/env python3
"""
Documentation Synchronization Checker for MHM

This script helps identify and fix documentation synchronization issues:
- Flags outdated documentation paths during refactors
- Checks for paired AI/human documentation consistency
- Identifies path drift between code and documentation
- Generates directory trees for documentation

Usage:
    python ai_tools/documentation_sync_checker.py [--check] [--fix] [--generate-trees]
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.logger import get_component_logger
    logger = get_component_logger(__name__)
except ImportError:
    # Fallback logging if core.logger not available
    logger = None

class DocumentationSyncChecker:
    """Checks and maintains documentation synchronization."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.paired_docs = {
            'DEVELOPMENT_WORKFLOW.md': 'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
            'ARCHITECTURE.md': 'ai_development_docs/AI_ARCHITECTURE.md',
            'DOCUMENTATION_GUIDE.md': 'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
            'development_docs/CHANGELOG_DETAIL.md': 'ai_development_docs/AI_CHANGELOG.md',
        }
        
        # Common path patterns that might drift
        self.path_patterns = [
            r'`([^`]+\.py)`',
            r'`([^`]+\.md)`',
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ]
        
        # Directories to scan for code references
        self.code_dirs = ['core', 'communication', 'ui', 'tasks', 'user', 'ai']
        
    def scan_codebase_paths(self) -> Set[str]:
        """Scan codebase for all file paths and imports."""
        paths = set()
        
        for code_dir in self.code_dirs:
            code_path = self.project_root / code_dir
            if code_path.exists():
                for py_file in code_path.rglob("*.py"):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extract import statements
                        import_pattern = r'^(?:from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import|import\s+([a-zA-Z_][a-zA-Z0-9_.]*))'
                        for line in content.split('\n'):
                            match = re.match(import_pattern, line.strip())
                            if match:
                                module = match.group(1) or match.group(2)
                                if module and not module.startswith(('os', 'sys', 'pathlib', 'typing')):
                                    paths.add(module)
                                    
                    except Exception as e:
                        if logger:
                            logger.warning(f"Error reading {py_file}: {e}")
                        
        return paths
    
    def scan_documentation_paths(self) -> Dict[str, List[str]]:
        """Scan documentation files for path references."""
        doc_paths = defaultdict(list)
        
        for md_file in self.project_root.rglob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract all path references
                for pattern in self.path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle regex groups
                            for group in match:
                                if group and not group.startswith(('http', '#')):
                                    doc_paths[str(md_file.relative_to(self.project_root))].append(group)
                        else:
                            if match and not match.startswith(('http', '#')):
                                doc_paths[str(md_file.relative_to(self.project_root))].append(match)
                                
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {md_file}: {e}")
                
        return doc_paths
    
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
    
    def check_path_drift(self) -> Dict[str, List[str]]:
        """Check for path drift between code and documentation."""
        code_paths = self.scan_codebase_paths()
        doc_paths = self.scan_documentation_paths()
        
        drift_issues = defaultdict(list)
        
        # Check if documented paths exist in codebase
        for doc_file, paths in doc_paths.items():
            for path in paths:
                # Normalize path for comparison
                normalized_path = path.replace('.', '/').replace('\\', '/')
                
                # Check if this path exists in the codebase
                path_exists = False
                for code_path in code_paths:
                    if normalized_path in code_path or code_path in normalized_path:
                        path_exists = True
                        break
                        
                if not path_exists and not path.startswith(('http', '#', 'mailto')):
                    drift_issues[doc_file].append(f"Potentially outdated path: {path}")
                    
        return drift_issues
    
    def generate_directory_tree(self, output_file: str = "development_docs/DIRECTORY_TREE.md") -> str:
        """Generate a directory tree for documentation with placeholders for certain directories."""
        import subprocess
        
        # Run tree command
        result = subprocess.run(['tree', '/F', '/A'], capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            if logger:
                logger.error("Error running tree command")
            return ""
        
        lines = result.stdout.split('\n')
        
        # Define placeholders
        placeholders = {
            '__pycache__': '    (Python cache files)',
            '.pytest_cache': '    (pytest cache files)',
            '.venv': '    (virtual environment files)',
            'backups': '    (backup files)',
            'htmlcov': '    (HTML coverage reports)',
            'archive': '    (archived files)'
        }
        
        # Process lines
        processed_lines = []
        skip_until_next_dir = False
        
        for i, line in enumerate(lines):
            if skip_until_next_dir:
                # Skip ALL content until we hit the next root-level directory
                # Look for lines that start with +--- (root level directories)
                if line.strip() and line.startswith('+---'):
                    # Found next directory at same level, stop skipping
                    skip_until_next_dir = False
                    # Now process this line normally (fall through to the else clause)
                else:
                    # Skip this line completely (don't add it, even if it's a nested placeholder)
                    continue
            
            # Check if this line contains a directory we want to replace
            should_replace = False
            replacement = None
            
            for key, placeholder in placeholders.items():
                if key in line and ('+---' in line or '\\---' in line):
                    should_replace = True
                    replacement = placeholder
                    break
            
            if should_replace:
                # Add the directory line
                processed_lines.append(line)
                # Add the placeholder
                processed_lines.append(replacement)
                skip_until_next_dir = True
            else:
                processed_lines.append(line)
        
        # Create the final content
        header = [
            "# Project Directory Tree",
            "",
            "> **Generated**: This file is auto-generated. Do not edit manually.",
            ""
        ]
        
        footer = [
            "",
            "---",
            "",
            "*Generated by documentation_sync_checker.py*"
        ]
        
        final_content = header + processed_lines + footer
        
        # Write to file
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_content))
            
        if logger:
            logger.info(f"Directory tree generated: {output_path}")
        return str(output_path)
    
    def run_checks(self) -> Dict[str, any]:
        """Run all documentation synchronization checks."""
        if logger:
            logger.info("Running documentation synchronization checks...")
        
        results = {
            'paired_docs': self.check_paired_documentation(),
            'path_drift': self.check_path_drift(),
            'summary': {}
        }
        
        # Generate summary
        total_issues = sum(len(issues) for issues in results['paired_docs'].values())
        total_issues += sum(len(issues) for issues in results['path_drift'].values())
        
        results['summary'] = {
            'total_issues': total_issues,
            'paired_doc_issues': len(results['paired_docs']),
            'path_drift_issues': len(results['path_drift']),
            'status': 'PASS' if total_issues == 0 else 'FAIL'
        }
        
        return results
    
    def print_report(self, results: Dict[str, any]):
        """Print a formatted report of the results."""
        # Remove headers - they'll be added by the consolidated report
        
        # Limit output to avoid Unicode issues
        max_issues_per_file = 5
        
        # Summary
        summary = results['summary']
        print(f"\nSUMMARY:")
        print(f"   Status: {summary['status']}")
        print(f"   Total Issues: {summary['total_issues']}")
        print(f"   Paired Doc Issues: {summary['paired_doc_issues']}")
        print(f"   Path Drift Issues: {summary['path_drift_issues']}")
        
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
        
        # Path Drift Issues (summary only)
        if results['path_drift']:
            print(f"\nPATH DRIFT ISSUES:")
            print(f"   Total files with issues: {len(results['path_drift'])}")
            print(f"   Total issues found: {sum(len(issues) for issues in results['path_drift'].values())}")
            print(f"   Top files with most issues:")
            sorted_files = sorted(results['path_drift'].items(), key=lambda x: len(x[1]), reverse=True)
            for doc_file, issues in sorted_files[:5]:
                print(f"     {doc_file}: {len(issues)} issues")
        
        if summary['total_issues'] == 0:
            print(f"\nAll documentation synchronization checks passed!")
        else:
            print(f"\nFound {summary['total_issues']} documentation synchronization issues.")
            print("   Consider running with --fix to attempt automatic fixes.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check documentation synchronization")
    parser.add_argument('--check', action='store_true', help='Run all checks')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--generate-trees', action='store_true', help='Generate directory trees')
    parser.add_argument('--output', default='development_docs/DIRECTORY_TREE.md', help='Output file for directory tree')
    
    args = parser.parse_args()
    
    checker = DocumentationSyncChecker()
    
    if args.generate_trees:
        output_file = checker.generate_directory_tree(args.output)
        print(f"Directory tree generated: {output_file}")
        return
    
    if args.check or not any([args.fix, args.generate_trees]):
        results = checker.run_checks()
        checker.print_report(results)
        
        if args.fix:
            if logger:
                logger.info("Auto-fix functionality not yet implemented")
                logger.info("Please review the issues above and fix them manually")


if __name__ == "__main__":
    main()
