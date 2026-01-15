#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Heading Numbering Fixer

Numbers H2 and H3 headings in documentation files.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation_headings.py [--dry-run] [--start-at-zero]
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.constants import DEFAULT_DOCS
except ImportError:
    from development_tools import config
    from development_tools.shared.constants import DEFAULT_DOCS

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


# ============================================================================
# Heading Numbering Helper Functions
# ============================================================================


def _parse_headings(content: str) -> List[Tuple[int, int, str, str, bool]]:
    """Parse markdown content and extract heading information."""
    lines = content.split("\n")
    headings = []
    in_code_block = False
    code_block_delimiter = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
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

        match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((i, level, line, heading_text, False))

    return headings


def _extract_numbered_prefix(text: str) -> Tuple[Optional[int], Optional[int], str]:
    """Extract number prefix from heading if present."""
    match = re.match(r"^(\d+(?:\.\d+)*)\.\s+(.+)$", text)
    if match:
        number_str = match.group(1)
        parts = number_str.split(".")
        main_number = int(parts[0])
        if len(parts) >= 2:
            sub_number = int(parts[1])
            return main_number, sub_number, match.group(2)
        else:
            return main_number, None, match.group(2)

    match = re.match(r"^(\d+(?:\.\d+)+)\s+(.+)$", text)
    if match:
        number_str = match.group(1)
        parts = number_str.split(".")
        if len(parts) >= 2:
            main_number = int(parts[0])
            sub_number = int(parts[1])
            return main_number, sub_number, match.group(2)

    match = re.match(r"^(\d+)\s+(.+)$", text)
    if match:
        main_number = int(match.group(1))
        return main_number, None, match.group(2)

    return None, None, text


def _is_changelog_file(file_path: Path) -> bool:
    """Determine if a file is a changelog, plan, or TODO file."""
    filename = file_path.name
    skip_patterns = [r"CHANGELOG", r"PLANS", r"^TODO\.md$"]
    for pattern in skip_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False


def _remove_emojis_from_text(text: str) -> str:
    """Remove emojis and common Unicode symbols from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002702-\U000027b0"  # dingbats
        "\U000024c2-\U0001f251"  # enclosed characters
        "\U0001f900-\U0001f9ff"  # supplemental symbols
        "\U0001fa00-\U0001fa6f"  # chess symbols
        "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
        "\U00002600-\U000026ff"  # miscellaneous symbols
        "\U00002700-\U000027bf"  # dingbats
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def _should_convert_to_bold(heading_text: str) -> bool:
    """Determine if a heading should be converted to bold text instead of numbered."""
    clean_text = _remove_emojis_from_text(heading_text)
    clean_text = re.sub(r"\*\*", "", clean_text).strip()
    if re.match(r"^Q:\s*", clean_text, re.IGNORECASE):
        return True
    if re.match(r"^Step\s+\d+:", clean_text, re.IGNORECASE):
        return True
    return False


def _has_standard_numbering_format(heading_text: str) -> bool:
    """Check if a heading uses the standard numbering format (with trailing period)."""
    if re.match(r"^\d+(?:\.\d+)*\.\s+", heading_text):
        return True
    if re.match(r"^\d+(?:\.\d+)+\s+", heading_text):
        return False
    if re.match(r"^\d+\s+", heading_text):
        return False
    return True


def _strip_content_number(text: str) -> str:
    """Strip content numbers (like "1. ", "2. ") from the start of text."""
    match = re.match(r"^(\d+)\.\s+(.+)$", text)
    if match:
        number = match.group(1)
        rest = match.group(2)
        if "." not in number and len(number) <= 2:
            return rest
    return text


def _should_skip_numbering(heading_text: str, is_changelog: bool = False) -> bool:
    """Determine if a heading should not be numbered."""
    clean_text = _remove_emojis_from_text(heading_text)
    skip_patterns = [r"^Quick Reference", r"^Overview$", r"^Introduction$"]
    for pattern in skip_patterns:
        if re.match(pattern, clean_text, re.IGNORECASE):
            return True
    if is_changelog:
        date_pattern = r"^\d{4}-\d{2}-\d{2}"
        if re.match(date_pattern, clean_text):
            return True
    return False


def _number_headings(
    content: str,
    file_path: Optional[Path] = None,
    start_at_zero: bool = False,
    create_updates: bool = True,
) -> Tuple[str, List[str]]:
    """Number H2 and H3 headings in markdown content."""
    is_changelog = file_path is not None and _is_changelog_file(file_path)
    if is_changelog:
        return content, []

    lines = content.split("\n")
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
                    start_at_zero_detected = h2_num == 0
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
            clean_text = re.sub(r"\*\*", "", clean_text).strip()
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
                    issues.append(
                        f"Line {line_num}: H2 heading number {h2_num} is out of order. Expected {h2_counter}."
                    )
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = f"## {h2_counter}. {clean_heading}"
                    current_h2_number = h2_counter
                    h2_counter += 1
                elif needs_format_fix:
                    issues.append(
                        f"Line {line_num}: H2 heading uses non-standard numbering format."
                    )
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
                    issues.append(
                        f"Line {line_num}: H2 heading missing number. Expected: '## {h2_counter}. {clean_heading}'"
                    )
                current_h2_number = h2_counter
                h2_counter += 1

        elif level == 3:
            if current_h2_number is None:
                issues.append(
                    f"Line {line_num}: H3 heading found before any H2 heading."
                )
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
                        updates[line_num] = (
                            f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                        )
                    h3_counters[current_h2_number] += 1
                elif h3_num != h3_counter:
                    issues.append(
                        f"Line {line_num}: H3 heading number {h3_num} is out of order. Expected {h3_counter}."
                    )
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = (
                            f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                        )
                    h3_counters[current_h2_number] = h3_counter + 1
                elif needs_format_fix:
                    issues.append(
                        f"Line {line_num}: H3 heading uses non-standard numbering format."
                    )
                    if create_updates:
                        clean_heading = _remove_emojis_from_text(text_without_num)
                        updates[line_num] = (
                            f"### {current_h2_number}.{h3_num}. {clean_heading}"
                        )
                    h3_counters[current_h2_number] += 1
                else:
                    h3_counters[current_h2_number] += 1
            else:
                if create_updates:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    updates[line_num] = (
                        f"### {current_h2_number}.{h3_counter}. {clean_heading}"
                    )
                else:
                    text_no_content_num = _strip_content_number(heading_text)
                    clean_heading = _remove_emojis_from_text(text_no_content_num)
                    issues.append(
                        f"Line {line_num}: H3 heading missing number. Expected: '### {current_h2_number}.{h3_counter}. {clean_heading}'"
                    )
                h3_counters[current_h2_number] += 1

    if updates:
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in updates:
                new_lines.append(updates[i])
            else:
                new_lines.append(line)
        return "\n".join(new_lines), issues

    return content, issues


# ============================================================================
# DocumentationHeadingFixer Class
# ============================================================================


class DocumentationHeadingFixer:
    """Fixes heading numbering in documentation files."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the documentation heading fixer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()

    def fix_number_headings(
        self, dry_run: bool = False, start_at_zero: bool = False
    ) -> Dict[str, any]:
        """Number H2 and H3 headings in documentation files."""
        files_updated = 0
        issues_fixed = 0
        errors = 0

        for file_path_str in DEFAULT_DOCS:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue

            if (
                "CHANGELOG" in file_path_str
                or "PLANS" in file_path_str
                or file_path.name == "TODO.md"
            ):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content, issues = _number_headings(
                    content,
                    file_path=file_path,
                    start_at_zero=start_at_zero,
                    create_updates=not dry_run,
                )

                if new_content != content and not dry_run:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    files_updated += 1
                    issues_fixed += len(issues)
                elif issues:
                    issues_fixed += len(issues)
            except Exception as e:
                errors += 1
                if logger:
                    logger.error(f"Error processing {file_path_str}: {e}")

        return {
            "files_updated": files_updated,
            "issues_fixed": issues_fixed,
            "errors": errors,
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Number H2 and H3 headings in documentation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--start-at-zero", action="store_true", help="Start numbering at 0 instead of 1"
    )

    args = parser.parse_args()

    fixer = DocumentationHeadingFixer()
    result = fixer.fix_number_headings(
        dry_run=args.dry_run, start_at_zero=args.start_at_zero
    )

    print(
        f"\nNumber Headings: Updated {result['files_updated']} files, Fixed {result['issues_fixed']} issues, Errors {result['errors']}"
    )

    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
