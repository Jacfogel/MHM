#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Link Conversion Fixer

Converts file path references to markdown links in documentation.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation_links.py [--dry-run]
"""

import re
import sys
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.constants import DEFAULT_DOCS
    from ..shared.standard_exclusions import ALL_GENERATED_FILES
    from .analyze_unconverted_links import UnconvertedLinkAnalyzer
except ImportError:
    from development_tools import config
    from development_tools.shared.constants import DEFAULT_DOCS
    from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES
    from development_tools.docs.analyze_unconverted_links import UnconvertedLinkAnalyzer

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class DocumentationLinkFixer:
    """Fixes unconverted file path references in documentation files."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the documentation link fixer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        
        # Create link analyzer instance to reuse helper methods
        self.link_analyzer = UnconvertedLinkAnalyzer(project_root=str(self.project_root))
    
    def _is_generated_file(self, file_path: Path) -> bool:
        """Check if a file is generated (should not be edited). Uses link analyzer logic."""
        return self.link_analyzer._is_generated_file(file_path)
    
    def fix_convert_links(self, dry_run: bool = False) -> Dict[str, any]:
        """
        Convert file path references to markdown links in documentation.
        
        In metadata sections (H1 heading + lines starting with >), only links each
        unique file once to avoid repetitive links. In body content, multiple links
        to the same file are allowed.
        
        Only processes non-generated .md files.
        """
        files_updated = 0
        changes_made = 0
        errors = 0
        breakdown = {
            'files_processed': 0,
            'files_skipped_generated': 0,
            'files_skipped_not_found': 0,
            'conversions_by_file': {},
            'metadata_dedup_count': 0,
            'skipped_code_block': 0,
            'skipped_example_context': 0,
            'skipped_invalid_path': 0,
            'skipped_already_link': 0,
            'skipped_self_reference': 0,
        }
        
        for file_path_str in DEFAULT_DOCS:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                breakdown['files_skipped_not_found'] += 1
                continue
            
            # Skip generated files
            if self._is_generated_file(file_path):
                breakdown['files_skipped_generated'] += 1
                continue
            
            breakdown['files_processed'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                new_lines = []
                modified = False
                file_conversions = []
                
                # Track which files have been linked in metadata section
                metadata_linked_files = set()
                
                for line_num, line in enumerate(lines):
                    original_line = line
                    is_metadata_section = self.link_analyzer._is_metadata_section(lines, line_num)
                    
                    if self.link_analyzer._is_in_code_block(lines, line_num):
                        breakdown['skipped_code_block'] += 1
                        new_lines.append(line)
                        continue
                    
                    if self.link_analyzer._is_in_example_context(line, lines, line_num):
                        breakdown['skipped_example_context'] += 1
                        new_lines.append(line)
                        continue
                    
                    pattern = r'`([a-zA-Z_][a-zA-Z0-9_/\\]*\.md)`'
                    
                    def replace_path(match):
                        path = match.group(1).replace('\\', '/')
                        
                        # Use link analyzer's methods for consistency
                        if self.link_analyzer._is_already_link(line, path):
                            breakdown['skipped_already_link'] += 1
                            return match.group(0)
                        
                        if self.link_analyzer._is_file_metadata_line(line):
                            return match.group(0)
                        
                        if not self.link_analyzer._should_convert_path_to_link(path, line, line_num, lines, file_path):
                            if path == file_path.name:
                                breakdown['skipped_self_reference'] += 1
                            return match.group(0)
                        
                        if not self.link_analyzer._is_valid_file_path_for_link(path, file_path):
                            breakdown['skipped_invalid_path'] += 1
                            return match.group(0)
                        
                        # Check if target file is generated (don't link to generated files)
                        target_path = self.project_root / path
                        if target_path.exists() and self.link_analyzer._is_generated_file(target_path):
                            breakdown['skipped_invalid_path'] += 1
                            return match.group(0)
                        
                        # In metadata section, only link each unique file once
                        if is_metadata_section:
                            if path in metadata_linked_files:
                                breakdown['metadata_dedup_count'] += 1
                                return match.group(0)
                            metadata_linked_files.add(path)
                        
                        path_obj = Path(path)
                        filename = path_obj.name
                        file_conversions.append(f"Line {line_num + 1}: `{path}` -> [{filename}]({path})")
                        return f'[{filename}]({path})'
                    
                    new_line = re.sub(pattern, replace_path, line)
                    if new_line != original_line:
                        modified = True
                        changes_made += 1
                    new_lines.append(new_line)
                
                if file_conversions:
                    breakdown['conversions_by_file'][file_path_str] = file_conversions
                
                if modified and not dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    files_updated += 1
            except Exception as e:
                errors += 1
                if logger:
                    logger.error(f"Error processing {file_path_str}: {e}")
        
        result = {
            'files_updated': files_updated,
            'changes_made': changes_made,
            'errors': errors,
            'breakdown': breakdown
        }
        
        if dry_run:
            # Print detailed breakdown in dry-run mode
            print(f"\nLink Conversion Breakdown:")
            print(f"  Files processed: {breakdown['files_processed']}")
            print(f"  Files skipped (generated): {breakdown['files_skipped_generated']}")
            print(f"  Files skipped (not found): {breakdown['files_skipped_not_found']}")
            print(f"  Total conversions: {changes_made}")
            print(f"  Metadata deduplications: {breakdown['metadata_dedup_count']}")
            print(f"  Skipped (code block): {breakdown['skipped_code_block']}")
            print(f"  Skipped (example context): {breakdown['skipped_example_context']}")
            print(f"  Skipped (invalid path): {breakdown['skipped_invalid_path']}")
            print(f"  Skipped (already link): {breakdown['skipped_already_link']}")
            print(f"  Skipped (self reference): {breakdown['skipped_self_reference']}")
            if breakdown['conversions_by_file']:
                print(f"\n  Conversions by file:")
                for file_str, conversions in list(breakdown['conversions_by_file'].items())[:10]:
                    print(f"    {file_str}: {len(conversions)} conversions")
                    for conv in conversions[:3]:
                        print(f"      {conv}")
                    if len(conversions) > 3:
                        print(f"      ... and {len(conversions) - 3} more")
                if len(breakdown['conversions_by_file']) > 10:
                    print(f"    ... and {len(breakdown['conversions_by_file']) - 10} more files")
        
        return result


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert file paths to markdown links in documentation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    fixer = DocumentationLinkFixer()
    result = fixer.fix_convert_links(dry_run=args.dry_run)
    
    print(f"\nConvert Links: Updated {result['files_updated']} files, Made {result['changes_made']} changes, Errors {result['errors']}")
    
    return 0 if result['errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

