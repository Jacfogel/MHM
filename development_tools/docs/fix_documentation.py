#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Fix Tool

Fixes common documentation issues:
- Adds file addresses to documentation files
- Fixes non-ASCII characters
- Numbers H2 and H3 headings
- Converts file paths to markdown links

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation.py [--add-addresses] [--fix-ascii] [--number-headings] [--convert-links] [--all] [--dry-run]
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.constants import (
        DEFAULT_DOCS, ASCII_COMPLIANCE_FILES,
        STANDARD_LIBRARY_MODULES, THIRD_PARTY_LIBRARIES,
        COMMON_FUNCTION_NAMES, COMMON_CLASS_NAMES, COMMON_VARIABLE_NAMES,
        COMMON_CODE_PATTERNS, IGNORED_PATH_PATTERNS,
        COMMAND_PATTERNS, TEMPLATE_PATTERNS
    )
    from ..shared.standard_exclusions import ALL_GENERATED_FILES, should_exclude_file
    from .analyze_documentation_sync import DocumentationSyncChecker
except ImportError:
    from development_tools import config
    from development_tools.shared.constants import (
        DEFAULT_DOCS, ASCII_COMPLIANCE_FILES,
        STANDARD_LIBRARY_MODULES, THIRD_PARTY_LIBRARIES,
        COMMON_FUNCTION_NAMES, COMMON_CLASS_NAMES, COMMON_VARIABLE_NAMES,
        COMMON_CODE_PATTERNS, IGNORED_PATH_PATTERNS,
        COMMAND_PATTERNS, TEMPLATE_PATTERNS
    )
    from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES, should_exclude_file
    from development_tools.docs.analyze_documentation_sync import DocumentationSyncChecker

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


# ============================================================================
# Heading Numbering Functions (integrated from scripts/number_documentation_headings.py)
# ============================================================================

def _parse_headings(content: str) -> List[Tuple[int, int, str, str, bool]]:
    """Parse markdown content and extract heading information."""
    lines = content.split('\n')
    headings = []
    in_code_block = False
    code_block_delimiter = None
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code_block:
                if stripped == code_block_delimiter or len(stripped) == 3:
                    in_code_block = False
                    code_block_delimiter = None
            else:
                in_code_block = True
                code_block_delimiter = stripped
            continue
        
        if in_code_block:
            continue
        
        match = re.match(r'^(#{2,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((i, level, line, heading_text, False))
    
    return headings

def _extract_numbered_prefix(text: str) -> Tuple[Optional[int], Optional[int], str]:
    """Extract number prefix from heading if present."""
    match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', text)
    if match:
        number_str = match.group(1)
        parts = number_str.split('.')
        main_number = int(parts[0])
        if len(parts) >= 2:
            sub_number = int(parts[1])
            return main_number, sub_number, match.group(2)
        else:
            return main_number, None, match.group(2)
    
    match = re.match(r'^(\d+(?:\.\d+)+)\s+(.+)$', text)
    if match:
        number_str = match.group(1)
        parts = number_str.split('.')
        if len(parts) >= 2:
            main_number = int(parts[0])
            sub_number = int(parts[1])
            return main_number, sub_number, match.group(2)
    
    match = re.match(r'^(\d+)\s+(.+)$', text)
    if match:
        main_number = int(match.group(1))
        return main_number, None, match.group(2)
    
    return None, None, text

def _is_changelog_file(file_path: Path) -> bool:
    """Determine if a file is a changelog, plan, or TODO file."""
    filename = file_path.name
    skip_patterns = [r'CHANGELOG', r'PLANS', r'^TODO\.md$']
    for pattern in skip_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False

def _remove_emojis_from_text(text: str) -> str:
    """Remove emojis and common Unicode symbols from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()

def _should_convert_to_bold(heading_text: str) -> bool:
    """Determine if a heading should be converted to bold text instead of numbered."""
    clean_text = _remove_emojis_from_text(heading_text)
    clean_text = re.sub(r'\*\*', '', clean_text).strip()
    if re.match(r'^Q:\s*', clean_text, re.IGNORECASE):
        return True
    if re.match(r'^Step\s+\d+:', clean_text, re.IGNORECASE):
        return True
    return False

def _has_standard_numbering_format(heading_text: str) -> bool:
    """Check if a heading uses the standard numbering format (with trailing period)."""
    if re.match(r'^\d+(?:\.\d+)*\.\s+', heading_text):
        return True
    if re.match(r'^\d+(?:\.\d+)+\s+', heading_text):
        return False
    if re.match(r'^\d+\s+', heading_text):
        return False
    return True

def _strip_content_number(text: str) -> str:
    """Strip content numbers (like "1. ", "2. ") from the start of text."""
    match = re.match(r'^(\d+)\.\s+(.+)$', text)
    if match:
        number = match.group(1)
        rest = match.group(2)
        if '.' not in number and len(number) <= 2:
            return rest
    return text

def _should_skip_numbering(heading_text: str, is_changelog: bool = False) -> bool:
    """Determine if a heading should not be numbered."""
    clean_text = _remove_emojis_from_text(heading_text)
    skip_patterns = [r'^Quick Reference', r'^Overview$', r'^Introduction$']
    for pattern in skip_patterns:
        if re.match(pattern, clean_text, re.IGNORECASE):
            return True
    if is_changelog:
        date_pattern = r'^\d{4}-\d{2}-\d{2}'
        if re.match(date_pattern, clean_text):
            return True
    return False

def _number_headings(content: str, file_path: Optional[Path] = None, start_at_zero: bool = False, create_updates: bool = True) -> Tuple[str, List[str]]:
    """Number H2 and H3 headings in markdown content."""
    is_changelog = file_path is not None and _is_changelog_file(file_path)
    if is_changelog:
        return content, []
    
    lines = content.split('\n')
    headings = _parse_headings(content)
    issues = []
    h2_counter = None
    h3_counters = {}
    updates = {}
    current_h2_number = None
    start_at_zero_detected = None
    
    # First pass: detect starting number
    for line_num, level, original_line, heading_text, in_code_block in headings:
        if in_code_block or _should_skip_numbering(heading_text, is_changelog):
            continue
        if level == 2:
            h2_num, h3_num, _ = _extract_numbered_prefix(heading_text)
            if h2_num is not None and h3_num is None:
                if start_at_zero_detected is None:
                    start_at_zero_detected = (h2_num == 0)
                break
    
    if start_at_zero_detected is not None:
        start_at_zero = start_at_zero_detected
        h2_counter = 0 if start_at_zero else 1
    else:
        h2_counter = 0 if start_at_zero else 1
    
    # Second pass: number headings
    for line_num, level, original_line, heading_text, in_code_block in headings:
        if in_code_block:
            continue
        
        if _should_convert_to_bold(heading_text):
            clean_text = heading_text.strip()
            clean_text = re.sub(r'\*\*', '', clean_text).strip()
            clean_text = f"**{clean_text}**"
            updates[line_num] = clean_text
            continue
        
        if _should_skip_numbering(heading_text, is_changelog):
            if create_updates:
                clean_heading = _remove_emojis_from_text(heading_text)
                if clean_heading != heading_text:
                    updates[line_num] = f"{'#' * level} {clean_heading}"
            continue
        
        if level == 2:
            if h2_counter not in h3_counters:
                h3_counters[h2_counter] = 0 if start_at_zero else 1
            current_h2_number = h2_counter
            h2_num, h3_num, text_without_num = _extract_numbered_prefix(heading_text)
            
            if h2_num is not None and h3_num is None:
                needs_format_fix = not _has_standard_numbering_format(heading_text)
                if h2_num != h2_counter:
                    issues.append(f"Line {line_num}: H2 heading number {h2_num} is out of order. Expected {h2_counter}.")
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"## {h2_counter}. {clean_heading}"
                    current_h2_number = h2_counter
                    h2_counter += 1
                elif needs_format_fix:
                    issues.append(f"Line {line_num}: H2 heading uses non-standard numbering format.")
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"## {h2_num}. {clean_heading}"
                    current_h2_number = h2_counter
                    h2_counter += 1
                else:
                    current_h2_number = h2_counter
                    h2_counter += 1
            else:
                if create_updates:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    updates[line_num] = f"## {h2_counter}. {clean_heading}"
                else:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    issues.append(f"Line {line_num}: H2 heading missing number. Expected: '## {h2_counter}. {clean_heading}'")
                current_h2_number = h2_counter
                h2_counter += 1
        
        elif level == 3:
            if current_h2_number is None:
                issues.append(f"Line {line_num}: H3 heading found before any H2 heading.")
                continue
            
            if current_h2_number not in h3_counters:
                h3_counters[current_h2_number] = 0 if start_at_zero else 1
            h3_counter = h3_counters[current_h2_number]
            h2_num, h3_num, text_without_num = _extract_numbered_prefix(heading_text)
            
            if h2_num is not None and h3_num is None:
                heading_text = text_without_num
                h2_num, h3_num, text_without_num = None, None, heading_text
            
            if h2_num is not None and h3_num is not None:
                needs_format_fix = not _has_standard_numbering_format(heading_text)
                if h2_num != current_h2_number:
                    issues.append(f"Line {line_num}: H3 heading H2 number mismatch.")
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                    h3_counters[current_h2_number] += 1
                elif h3_num != h3_counter:
                    issues.append(f"Line {line_num}: H3 heading number {h3_num} is out of order. Expected {h3_counter}.")
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                    h3_counters[current_h2_number] = h3_counter + 1
                elif needs_format_fix:
                    issues.append(f"Line {line_num}: H3 heading uses non-standard numbering format.")
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"### {current_h2_number}.{h3_num}. {clean_heading}"
                    h3_counters[current_h2_number] += 1
                else:
                    h3_counters[current_h2_number] += 1
            else:
                if create_updates:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    updates[line_num] = f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                else:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    issues.append(f"Line {line_num}: H3 heading missing number. Expected: '### {current_h2_number}.{h3_counter}. {clean_heading}'")
                h3_counters[current_h2_number] += 1
    
    if updates:
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in updates:
                new_lines.append(updates[i])
            else:
                new_lines.append(line)
        return '\n'.join(new_lines), issues
    
    return content, issues


# ============================================================================
# Link Conversion Functions (integrated from scripts/utilities/convert_paths_to_links.py)
# ============================================================================

# Helper functions are now provided by DocumentationSyncChecker
# The fixer uses self.checker methods for consistency


# ============================================================================
# DocumentationFixer Class
# ============================================================================

class DocumentationFixer:
    """Fixes common documentation issues."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the documentation fixer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        
        # Create a DocumentationSyncChecker instance to reuse its analysis logic
        self.checker = DocumentationSyncChecker(project_root=str(self.project_root))
    
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
                
                # Skip .cursor/rules/*.mdc files - they have their own metadata format
                if '.cursor' in parts and 'rules' in parts and file_path.suffix == '.mdc':
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
                logger.error(f"Error processing {file_path}: {e}")
        
        return {'updated': updated, 'skipped': skipped, 'errors': errors}
    
    def fix_ascii(self, dry_run: bool = False) -> Dict[str, any]:
        """Fix non-ASCII characters in documentation files.
        
        Handles common typographic characters that should be replaced with ASCII equivalents.
        """
        REPLACEMENTS = {
            # Smart quotes (single)
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u201A': "'",  # Single low-9 quotation mark
            '\u201B': "'",  # Single high-reversed-9 quotation mark
            # Smart quotes (double)
            '\u201C': '"',  # Left double quotation mark
            '\u201D': '"',  # Right double quotation mark
            '\u201E': '"',  # Double low-9 quotation mark
            '\u201F': '"',  # Double high-reversed-9 quotation mark
            # Dashes and hyphens
            '\u2011': '-',  # Non-breaking hyphen
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2015': '--',  # Horizontal bar
            # Arrows
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2191': '^',  # Up arrow
            '\u2193': 'v',  # Down arrow
            # Ellipsis
            '\u2026': '...',  # Horizontal ellipsis
            # Common emojis (standard replacements for documentation)
            '\u2705': '[OK]',  # Check mark button
            '\u274C': '[FAIL]',  # Cross mark
            '\u26A0': '[WARNING]',  # Warning sign
            '\U0001F41B': '[BUG]',  # Bug emoji
            '\U0001F4A1': '[IDEA]',  # Light bulb
            '\U0001F4DD': '[NOTE]',  # Memo
            # Spaces (various Unicode spaces -> regular space)
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
        
        files_updated = 0
        replacements_made = 0
        errors = 0
        
        for file_path_str in ASCII_COMPLIANCE_FILES:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_replacements = 0
                
                for non_ascii, ascii_replacement in REPLACEMENTS.items():
                    if non_ascii in content:
                        count = content.count(non_ascii)
                        content = content.replace(non_ascii, ascii_replacement)
                        file_replacements += count
                
                if content != original_content:
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        files_updated += 1
                    else:
                        # In dry-run mode, still count files that would be updated
                        files_updated += 1
                    replacements_made += file_replacements
            except Exception as e:
                errors += 1
                logger.error(f"Error processing {file_path_str}: {e}")
        
        return {'files_updated': files_updated, 'replacements_made': replacements_made, 'errors': errors}
    
    def fix_number_headings(self, dry_run: bool = False, start_at_zero: bool = False) -> Dict[str, any]:
        """Number H2 and H3 headings in documentation files."""
        files_updated = 0
        issues_fixed = 0
        errors = 0
        
        for file_path_str in DEFAULT_DOCS:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue
            
            if 'CHANGELOG' in file_path_str or 'PLANS' in file_path_str or file_path.name == 'TODO.md':
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content, issues = _number_headings(content, file_path=file_path, start_at_zero=start_at_zero, create_updates=not dry_run)
                
                if new_content != content and not dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    files_updated += 1
                    issues_fixed += len(issues)
                elif issues:
                    issues_fixed += len(issues)
            except Exception as e:
                errors += 1
                logger.error(f"Error processing {file_path_str}: {e}")
        
        return {'files_updated': files_updated, 'issues_fixed': issues_fixed, 'errors': errors}
    
    
    def _is_generated_file(self, file_path: Path) -> bool:
        """Check if a file is generated (should not be edited). Uses analysis checker logic."""
        return self.checker._is_generated_file(file_path)
    
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
                    is_metadata_section = self.checker._is_metadata_section(lines, line_num)
                    
                    if self.checker._is_in_code_block(lines, line_num):
                        breakdown['skipped_code_block'] += 1
                        new_lines.append(line)
                        continue
                    
                    if self.checker._is_in_example_context(line, lines, line_num):
                        breakdown['skipped_example_context'] += 1
                        new_lines.append(line)
                        continue
                    
                    pattern = r'`([a-zA-Z_][a-zA-Z0-9_/\\]*\.md)`'
                    
                    def replace_path(match):
                        path = match.group(1).replace('\\', '/')
                        
                        # Use analysis checker's methods for consistency
                        if self.checker._is_already_link(line, path):
                            breakdown['skipped_already_link'] += 1
                            return match.group(0)
                        
                        if self.checker._is_file_metadata_line(line):
                            return match.group(0)
                        
                        if not self.checker._should_convert_path_to_link(path, line, line_num, lines, file_path):
                            if path == file_path.name:
                                breakdown['skipped_self_reference'] += 1
                            return match.group(0)
                        
                        if not self.checker._is_valid_file_path_for_link(path, file_path):
                            breakdown['skipped_invalid_path'] += 1
                            return match.group(0)
                        
                        # Check if target file is generated (don't link to generated files)
                        target_path = self.project_root / path
                        if target_path.exists() and self.checker._is_generated_file(target_path):
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
    
    parser = argparse.ArgumentParser(description='Fix documentation issues')
    parser.add_argument('--add-addresses', action='store_true', help='Add file addresses to documentation files')
    parser.add_argument('--fix-ascii', action='store_true', help='Fix non-ASCII characters in documentation')
    parser.add_argument('--number-headings', action='store_true', help='Number H2 and H3 headings in documentation')
    parser.add_argument('--convert-links', action='store_true', help='Convert file paths to markdown links')
    parser.add_argument('--all', action='store_true', help='Apply all fix operations')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    fixer = DocumentationFixer()
    results = {}
    
    if args.add_addresses or args.all:
        result = fixer.fix_add_addresses(dry_run=args.dry_run)
        results['add_addresses'] = result
        print(f"\nAdd Addresses: Updated {result['updated']}, Skipped {result['skipped']}, Errors {result['errors']}")
    
    if args.fix_ascii or args.all:
        result = fixer.fix_ascii(dry_run=args.dry_run)
        results['fix_ascii'] = result
        print(f"\nFix ASCII: Updated {result['files_updated']} files, Made {result['replacements_made']} replacements, Errors {result['errors']}")
    
    if args.number_headings or args.all:
        result = fixer.fix_number_headings(dry_run=args.dry_run)
        results['number_headings'] = result
        print(f"\nNumber Headings: Updated {result['files_updated']} files, Fixed {result['issues_fixed']} issues, Errors {result['errors']}")
    
    if args.convert_links or args.all:
        result = fixer.fix_convert_links(dry_run=args.dry_run)
        results['convert_links'] = result
        print(f"\nConvert Links: Updated {result['files_updated']} files, Made {result['changes_made']} changes, Errors {result['errors']}")
    
    if not (args.add_addresses or args.fix_ascii or args.number_headings or args.convert_links or args.all):
        parser.print_help()
        return 1
    
    total_errors = sum(r.get('errors', 0) for r in results.values())
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
