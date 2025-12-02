#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Address Fixer

Adds file addresses to documentation files that don't have them.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation_addresses.py [--dry-run]
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
    from ..shared.standard_exclusions import ALL_GENERATED_FILES
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class DocumentationAddressFixer:
    """Fixes missing file addresses in documentation files."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the documentation address fixer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
    
    def fix_add_addresses(self, dry_run: bool = False) -> Dict[str, any]:
        """Add file addresses to documentation files that don't have them."""
        updated = 0
        skipped = 0
        errors = 0
        
        files_to_process = []
        for ext in ['*.md', '*.mdc']:
            files_to_process.extend(self.project_root.rglob(ext))
        
        ignore_dirs = {'venv', '.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache', 'coverage_html', 'archive'}
        generated_files = set(ALL_GENERATED_FILES)
        
        filtered_files = []
        for file_path in files_to_process:
            parts = file_path.parts
            if any(ignore in parts for ignore in ignore_dirs):
                continue
            try:
                rel_path = file_path.relative_to(self.project_root)
                rel_path_str = str(rel_path).replace('\\', '/')
                if rel_path_str in generated_files:
                    continue
                
                # Skip .cursor/ directory files (plans, rules, etc.) - they have their own metadata format
                if '.cursor' in parts:
                    continue
                
                if 'tests' in rel_path.parts:
                    tests_index = rel_path.parts.index('tests')
                    if tests_index < len(rel_path.parts) - 2:
                        continue
            except ValueError:
                continue
            filtered_files.append(file_path)
        
        for file_path in filtered_files:
            try:
                rel_path = str(file_path.relative_to(self.project_root)).replace('\\', '/')
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_address = bool(re.search(r'^>\s*\*\*File\*\*:\s*`', content[:2000], re.MULTILINE))
                if has_address:
                    skipped += 1
                    continue
                
                if not dry_run:
                    if file_path.suffix == '.md':
                        if content.startswith('@'):
                            first_newline = content.find('\n')
                            if first_newline > 0:
                                new_content = content[:first_newline+1] + f'\n> **File**: `{rel_path}`\n' + content[first_newline+1:]
                            else:
                                new_content = f'> **File**: `{rel_path}`\n\n' + content
                        else:
                            title_match = re.match(r'^(#+\s+[^\n]+)\n+', content)
                            if title_match:
                                title_end = title_match.end()
                                new_content = content[:title_end] + f'\n> **File**: `{rel_path}`\n' + content[title_end:]
                            else:
                                new_content = f'> **File**: `{rel_path}`\n\n' + content
                    else:
                        if content.startswith('---'):
                            frontmatter_end = content.find('---', 3)
                            if frontmatter_end > 0:
                                frontmatter = content[3:frontmatter_end].strip()
                                new_frontmatter = frontmatter + f'\nfile: "{rel_path}"'
                                new_content = '---\n' + new_frontmatter + '\n---' + content[frontmatter_end+3:]
                            else:
                                new_content = f'<!-- File: {rel_path} -->\n\n' + content
                        else:
                            new_content = f'<!-- File: {rel_path} -->\n\n' + content
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                
                updated += 1
            except Exception as e:
                errors += 1
                if logger:
                    logger.error(f"Error processing {file_path}: {e}")
        
        return {'updated': updated, 'skipped': skipped, 'errors': errors}


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add file addresses to documentation files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    fixer = DocumentationAddressFixer()
    result = fixer.fix_add_addresses(dry_run=args.dry_run)
    
    print(f"\nAdd Addresses: Updated {result['updated']}, Skipped {result['skipped']}, Errors {result['errors']}")
    
    return 0 if result['errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

