#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Heading Numbering Analyzer

This script checks that H2 and H3 headings are numbered consecutively starting
at 1 (or 0). Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python docs/analyze_heading_numbering.py
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
else:
    from development_tools import config

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, 'load_external_config'):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")


class HeadingNumberingAnalyzer:
    """Analyzes documentation files for heading numbering compliance."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None, use_cache: bool = True):
        """
        Initialize heading numbering analyzer.
        
        Args:
            project_root: Root directory of the project
            config_path: Optional path to external config file
            use_cache: Whether to use mtime-based caching for file analysis
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
        
        # Caching - use shared utility
        from development_tools.shared.mtime_cache import MtimeFileCache
        cache_file = self.project_root / "development_tools" / "docs" / ".heading_numbering_cache.json"
        self.cache = MtimeFileCache(cache_file, self.project_root, use_cache=use_cache)
    
    def check_heading_numbering(self) -> Dict[str, List[str]]:
        """
        Check that H2 and H3 headings are numbered consecutively starting at 1 (or 0).
        
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        numbering_issues = defaultdict(list)
        
        # Import constants from shared.constants
        from development_tools.shared.constants import DEFAULT_DOCS
        files_to_check = list(DEFAULT_DOCS)
        
        def is_changelog_file(filepath: str) -> bool:
            """Check if a file is a changelog, plan, or TODO file (should be skipped from numbering checks)."""
            # Match changelogs, plans, and TODO files
            skip_patterns = [
                r'CHANGELOG',
                r'PLANS',
                r'TODO\.md$',
            ]
            for pattern in skip_patterns:
                if re.search(pattern, filepath, re.IGNORECASE):
                    return True
            return False
        
        for file_path in files_to_check:
            # Skip changelog files - they have their own structure
            if is_changelog_file(file_path):
                continue
                
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            # Check cache first
            cached_issues = self.cache.get_cached(full_path)
            if cached_issues is not None:
                if cached_issues:
                    numbering_issues[file_path] = cached_issues
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                h2_counter = None  # Track expected H2 number
                h3_counters = {}  # Track H3 counters per H2 section
                current_h2_number = None
                start_at_zero = False  # Track if numbering starts at 0
                
                # Headings that should not be numbered
                skip_patterns = [
                    r'^Quick Reference',
                    r'^Overview$',
                    r'^Introduction$',
                ]
                
                in_quick_reference = False
                
                for line_num, line in enumerate(lines, 1):
                    # Match H2 headings
                    h2_match = re.match(r'^##\s+(.+)$', line)
                    if h2_match:
                        heading_text = h2_match.group(1).strip()
                        
                        # Check if this is a Quick Reference section
                        if any(re.match(pattern, heading_text, re.IGNORECASE) 
                               for pattern in skip_patterns):
                            in_quick_reference = True
                            continue
                        else:
                            in_quick_reference = False
                        
                        # Check if Q&A or Step headings (should be converted to bold, not numbered)
                        clean_heading = re.sub(r'\*\*', '', heading_text).strip()
                        if re.match(r'^Q:\s*', clean_heading, re.IGNORECASE):
                            numbering_issues[file_path].append(
                                f"Line {line_num}: Q&A heading should be converted to bold text instead of being a heading. "
                                f"Found: '## {heading_text}', expected: '**{clean_heading}**'"
                            )
                            continue
                        
                        if re.match(r'^Step\s+\d+:', clean_heading, re.IGNORECASE):
                            numbering_issues[file_path].append(
                                f"Line {line_num}: Step heading should be converted to bold text instead of being a heading. "
                                f"Found: '## {heading_text}', expected: '**{clean_heading}**'"
                            )
                            continue
                        
                        # Extract number if present (handle multiple patterns)
                        # Standard format: "2.1. Title" (with trailing period and space)
                        num_match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', heading_text)
                        non_standard_format = None
                        
                        if not num_match:
                            # Try pattern without trailing period: "2.1 Title" (non-standard)
                            num_match = re.match(r'^(\d+(?:\.\d+)+)\s+(.+)$', heading_text)
                            if num_match:
                                non_standard_format = "missing_period"
                        if not num_match:
                            # Try single number: "2 Title" (non-standard)
                            num_match = re.match(r'^(\d+)\s+(.+)$', heading_text)
                            if num_match:
                                non_standard_format = "missing_period"
                        
                        if num_match:
                            # Flag non-standard formats
                            if non_standard_format:
                                number_str = num_match.group(1)
                                text_part = num_match.group(2)
                                numbering_issues[file_path].append(
                                    f"Line {line_num}: H2 heading uses non-standard numbering format. "
                                    f"Found: '## {heading_text}', expected: '## {number_str}. {text_part}'"
                                )
                            
                            # Already numbered
                            number_str = num_match.group(1)
                            main_number = int(number_str.split('.')[0])
                            
                            if h2_counter is None:
                                # First numbered H2 - determine if starting at 0 or 1
                                h2_counter = main_number + 1  # Increment for next heading
                                start_at_zero = (main_number == 0)
                                current_h2_number = main_number
                            else:
                                # Check if consecutive (h2_counter already represents the next expected number)
                                expected = h2_counter
                                if main_number != expected:
                                    numbering_issues[file_path].append(
                                        f"Line {line_num}: H2 heading number {main_number} is out of order. "
                                        f"Expected {expected}. Heading: {heading_text}"
                                    )
                                    # Use expected number for H3 checks (as numbering script would fix it)
                                    current_h2_number = expected
                                    h2_counter = expected + 1  # Increment for next heading
                                else:
                                    # Number is correct
                                    current_h2_number = main_number
                                    h2_counter = main_number + 1  # Increment for next heading
                            
                            # Initialize H3 counter for this section
                            if current_h2_number not in h3_counters:
                                h3_counters[current_h2_number] = 0 if start_at_zero else 1
                        else:
                            # Not numbered
                            if h2_counter is None:
                                h2_counter = 1  # Default start at 1
                                start_at_zero = False
                            else:
                                numbering_issues[file_path].append(
                                    f"Line {line_num}: H2 heading missing number. "
                                    f"Expected: '## {h2_counter}. {heading_text}'"
                                )
                                h2_counter += 1
                            
                            current_h2_number = h2_counter - 1
                            h3_counters[current_h2_number] = 0 if start_at_zero else 1
                    
                    # Match H3 headings
                    h3_match = re.match(r'^###\s+(.+)$', line)
                    if h3_match:
                        heading_text = h3_match.group(1).strip()
                        
                        # Skip if in Quick Reference section
                        if in_quick_reference:
                            continue
                        
                        # Check if Q&A or Step headings (should be converted to bold, not numbered)
                        clean_heading = re.sub(r'\*\*', '', heading_text).strip()
                        if re.match(r'^Q:\s*', clean_heading, re.IGNORECASE):
                            numbering_issues[file_path].append(
                                f"Line {line_num}: Q&A heading should be converted to bold text instead of being a heading. "
                                f"Found: '### {heading_text}', expected: '**{clean_heading}**'"
                            )
                            continue
                        
                        if re.match(r'^Step\s+\d+:', clean_heading, re.IGNORECASE):
                            numbering_issues[file_path].append(
                                f"Line {line_num}: Step heading should be converted to bold text instead of being a heading. "
                                f"Found: '### {heading_text}', expected: '**{clean_heading}**'"
                            )
                            continue
                        
                        if current_h2_number is None:
                            numbering_issues[file_path].append(
                                f"Line {line_num}: H3 heading found before any numbered H2. "
                                f"Heading: {heading_text}"
                            )
                            continue
                        
                        # Extract number if present (handle multiple patterns)
                        # Standard format: "2.1. Title" (with trailing period and space)
                        num_match = re.match(r'^(\d+(?:\.\d+)+)\.\s+(.+)$', heading_text)
                        non_standard_format = None
                        
                        if not num_match:
                            # Try pattern without trailing period: "2.1 Title" (non-standard)
                            num_match = re.match(r'^(\d+(?:\.\d+)+)\s+(.+)$', heading_text)
                            if num_match:
                                non_standard_format = "missing_period"
                        
                        if num_match:
                            # Flag non-standard formats
                            if non_standard_format:
                                number_str = num_match.group(1)
                                text_part = num_match.group(2)
                                numbering_issues[file_path].append(
                                    f"Line {line_num}: H3 heading uses non-standard numbering format. "
                                    f"Found: '### {heading_text}', expected: '### {current_h2_number}.{number_str.split('.')[1]}. {text_part}'"
                                )
                            
                            # Already numbered - check pattern
                            number_str = num_match.group(1)
                            parts = number_str.split('.')
                            h2_num = int(parts[0])
                            h3_num = int(parts[1]) if len(parts) > 1 else None
                            
                            if h2_num != current_h2_number:
                                numbering_issues[file_path].append(
                                    f"Line {line_num}: H3 heading H2 number mismatch. "
                                    f"Found {h2_num}, expected {current_h2_number}. Heading: {heading_text}"
                                )
                            
                            if h3_num is not None:
                                expected_h3 = h3_counters.get(current_h2_number, 0 if start_at_zero else 1)
                                if h3_num != expected_h3:
                                    numbering_issues[file_path].append(
                                        f"Line {line_num}: H3 heading number {h3_num} is out of order. "
                                        f"Expected {expected_h3}. Heading: {heading_text}"
                                    )
                                    # Use expected number for next H3 (as numbering script would fix it)
                                    h3_counters[current_h2_number] = expected_h3 + 1
                                else:
                                    # Number is correct
                                    h3_counters[current_h2_number] = h3_num + 1
                        else:
                            # Not numbered
                            expected_h3 = h3_counters.get(current_h2_number, 0 if start_at_zero else 1)
                            numbering_issues[file_path].append(
                                f"Line {line_num}: H3 heading missing number. "
                                f"Expected: '### {current_h2_number}.{expected_h3}. {heading_text}'"
                            )
                            h3_counters[current_h2_number] = expected_h3 + 1
                            
            except Exception as e:
                file_issues = [f"Error reading file: {e}"]
                self.cache.cache_results(full_path, file_issues)
                numbering_issues[file_path] = file_issues
            else:
                # Cache results for this file
                file_issues = numbering_issues.get(file_path, [])
                self.cache.cache_results(full_path, file_issues)
        
        # Save cache
        self.cache.save_cache()
        
        return numbering_issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check heading numbering in documentation files")
    
    args = parser.parse_args()
    
    analyzer = HeadingNumberingAnalyzer()
    results = analyzer.check_heading_numbering()
    
    # Print results
    if results:
        print(f"\nHeading Numbering Issues:")
        print(f"   Total files with numbering issues: {len(results)}")
        print(f"   Total issues found: {sum(len(issues) for issues in results.values())}")
        print(f"   Files with numbering issues:")
        for doc_file, issues in results.items():
            print(f"     {doc_file}: {len(issues)} issues")
            for issue in issues[:5]:  # Show first 5 issues per file
                # Clean Unicode characters that cause encoding issues
                clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                print(f"       - {clean_issue}")
            if len(issues) > 5:
                print(f"       ... and {len(issues) - 5} more issues")
    else:
        print("\nAll documentation files have correct heading numbering!")
    
    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())

