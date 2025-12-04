#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
ASCII Compliance Analyzer

This script checks for non-ASCII characters in documentation files.
Reports ALL non-ASCII characters found. Characters that can be auto-fixed
are marked with their suggested replacement. Configuration is loaded from
external config file (development_tools_config.json) if available, making
this tool portable across different projects.

Usage:
    python docs/analyze_ascii_compliance.py
"""

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


class ASCIIComplianceAnalyzer:
    """Analyzes documentation files for ASCII compliance."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None, use_cache: bool = True):
        """
        Initialize ASCII compliance analyzer.
        
        Args:
            project_root: Root directory of the project
            config_path: Optional path to external config file
            use_cache: Whether to use mtime-based caching for file results
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
        
        # Caching - use standardized storage
        from development_tools.shared.mtime_cache import MtimeFileCache
        cache_file = self.project_root / "development_tools" / "docs" / ".ascii_compliance_cache.json"  # Legacy fallback
        self.cache = MtimeFileCache(cache_file, self.project_root, use_cache=use_cache, 
                                    tool_name='analyze_ascii_compliance', domain='docs')
    
    def check_ascii_compliance(self) -> Dict[str, List[str]]:
        """
        Check for non-ASCII characters in documentation files.
        
        Reports ALL non-ASCII characters found. Characters that can be auto-fixed
        are marked with their suggested replacement.
        
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        ascii_issues = defaultdict(list)
        
        # Import constants from shared.constants
        from development_tools.shared.constants import ASCII_COMPLIANCE_FILES
        
        # Known replacements (characters that can be auto-fixed)
        KNOWN_REPLACEMENTS = {
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u201A': "'",  # Single low-9 quotation mark
            '\u201B': "'",  # Single high-reversed-9 quotation mark
            '\u201C': '"',  # Left double quotation mark
            '\u201D': '"',  # Right double quotation mark
            '\u201E': '"',  # Double low-9 quotation mark
            '\u201F': '"',  # Double high-reversed-9 quotation mark
            '\u2011': '-',  # Non-breaking hyphen
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2015': '--',  # Horizontal bar
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2191': '^',  # Up arrow
            '\u2193': 'v',  # Down arrow
            '\u2026': '...',  # Horizontal ellipsis
            # Common emojis (standard replacements for documentation)
            '\u2705': '[OK]',  # Check mark button
            '\u274C': '[FAIL]',  # Cross mark
            '\u26A0': '[WARNING]',  # Warning sign
            '\U0001F41B': '[BUG]',  # Bug emoji
            '\U0001F4A1': '[IDEA]',  # Light bulb
            '\U0001F4DD': '[NOTE]',  # Memo
            '\u202F': ' ',  # Narrow no-break space
            '\u00A0': ' ',  # Non-breaking space
            '\u2009': ' ',  # Thin space
            '\u2008': ' ',  # Punctuation space
            '\u2007': ' ',  # Figure space
            '\u2006': ' ',  # Six-per-em space
            '\u2005': ' ',  # Four-per-em space
            '\u2004': ' ',  # Three-per-em space
            '\u2003': ' ',  # Em space
            '\u2002': ' ',  # En space
            '\u2001': ' ',  # Em quad
            '\u2000': ' ',  # En quad
        }
        
        files_to_check = list(ASCII_COMPLIANCE_FILES)
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            # Check cache first
            cached_issues = self.cache.get_cached(full_path)
            if cached_issues is not None:
                if cached_issues:
                    ascii_issues[file_path] = cached_issues
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find ALL non-ASCII characters
                non_ascii_chars = {}
                for i, char in enumerate(content):
                    if ord(char) > 127:  # Non-ASCII
                        if char not in non_ascii_chars:
                            non_ascii_chars[char] = 0
                        non_ascii_chars[char] += 1
                
                file_issues = []
                if non_ascii_chars:
                    # Report all non-ASCII characters
                    for char, count in sorted(non_ascii_chars.items()):
                        if char in KNOWN_REPLACEMENTS:
                            file_issues.append(
                                f"Non-ASCII character '{char}' (U+{ord(char):04X}): {count} instance(s) found (auto-fixable: '{KNOWN_REPLACEMENTS[char]}')"
                            )
                        else:
                            file_issues.append(
                                f"Non-ASCII character '{char}' (U+{ord(char):04X}): {count} instance(s) found (manual review needed)"
                            )
                
                # Cache results
                self.cache.cache_results(full_path, file_issues)
                if file_issues:
                    ascii_issues[file_path] = file_issues
                        
            except Exception as e:
                file_issues = [f"Error reading file: {e}"]
                self.cache.cache_results(full_path, file_issues)
                ascii_issues[file_path] = file_issues
        
        # Save cache
        self.cache.save_cache()
        
        return ascii_issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check for non-ASCII characters in documentation files")
    
    args = parser.parse_args()
    
    analyzer = ASCIIComplianceAnalyzer()
    results = analyzer.check_ascii_compliance()
    
    # Print results
    if results:
        print(f"\nASCII Compliance Issues:")
        print(f"   Total files with non-ASCII characters: {len(results)}")
        print(f"   Total issues found: {sum(len(issues) for issues in results.values())}")
        print(f"   Files with non-ASCII characters:")
        for doc_file, issues in results.items():
            print(f"     {doc_file}: {len(issues)} issues")
            for issue in issues[:3]:  # Show first 3 issues per file
                # Clean Unicode characters that cause encoding issues
                clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                print(f"       - {clean_issue}")
            if len(issues) > 3:
                print(f"       ... and {len(issues) - 3} more issues")
    else:
        print("\nAll documentation files are ASCII compliant!")
    
    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())

