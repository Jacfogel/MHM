#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation ASCII Fixer

Fixes non-ASCII characters in documentation files by replacing them with ASCII equivalents.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation_ascii.py [--dry-run]
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.constants import ASCII_COMPLIANCE_FILES
except ImportError:
    from development_tools import config
    from development_tools.shared.constants import ASCII_COMPLIANCE_FILES

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class DocumentationASCIIFixer:
    """Fixes non-ASCII characters in documentation files."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the documentation ASCII fixer."""
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()

    def fix_ascii(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix non-ASCII characters in documentation files.

        Handles common typographic characters that should be replaced with ASCII equivalents.
        """
        REPLACEMENTS = {
            # Smart quotes (single)
            "\u2018": "'",  # Left single quotation mark
            "\u2019": "'",  # Right single quotation mark
            "\u201a": "'",  # Single low-9 quotation mark
            "\u201b": "'",  # Single high-reversed-9 quotation mark
            # Smart quotes (double)
            "\u201c": '"',  # Left double quotation mark
            "\u201d": '"',  # Right double quotation mark
            "\u201e": '"',  # Double low-9 quotation mark
            "\u201f": '"',  # Double high-reversed-9 quotation mark
            # Dashes and hyphens
            "\u2011": "-",  # Non-breaking hyphen
            "\u2013": "-",  # En dash
            "\u2014": "-",  # Em dash
            "\u2015": "--",  # Horizontal bar
            # Arrows
            "\u2192": "->",  # Right arrow
            "\u2190": "<-",  # Left arrow
            "\u2191": "^",  # Up arrow
            "\u2193": "v",  # Down arrow
            # Ellipsis
            "\u2026": "...",  # Horizontal ellipsis
            # Mathematical symbols
            "\u00d7": "x",  # Multiplication sign (×)
            "\u00b0": "deg",  # Degree symbol (°)
            "\u00b1": "+/-",  # Plus-minus sign (±)
            "\u00f7": "/",  # Division sign (÷)
            # Typographic symbols
            "\u2022": "*",  # Bullet (•)
            "\u2122": "(TM)",  # Trademark symbol (™)
            "\u00ae": "(R)",  # Registered trademark symbol (®)
            "\u00a9": "(C)",  # Copyright symbol (©)
            "\u00a7": "Section ",  # Section sign (§)
            # Common emojis (standard replacements for documentation)
            "\u2705": "[OK]",  # Check mark button
            "\u274c": "[FAIL]",  # Cross mark
            "\u26a0": "[WARNING]",  # Warning sign
            "\U0001f41b": "[BUG]",  # Bug emoji
            "\U0001f4a1": "[IDEA]",  # Light bulb
            "\U0001f4dd": "[NOTE]",  # Memo
            # Spaces (various Unicode spaces -> regular space)
            "\u202f": " ",  # Narrow no-break space
            "\u00a0": " ",  # Non-breaking space
            "\u2009": " ",  # Thin space
            "\u2008": " ",  # Punctuation space
            "\u2007": " ",  # Figure space
            "\u2006": " ",  # Six-per-em space
            "\u2005": " ",  # Four-per-em space
            "\u2004": " ",  # Three-per-em space
            "\u2003": " ",  # Em space
            "\u2002": " ",  # En space
            "\u2001": " ",  # Em quad
            "\u2000": " ",  # En quad
        }

        files_updated = 0
        replacements_made = 0
        errors = 0

        for file_path_str in ASCII_COMPLIANCE_FILES:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
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
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        files_updated += 1
                    else:
                        # In dry-run mode, still count files that would be updated
                        files_updated += 1
                    replacements_made += file_replacements
            except Exception as e:
                errors += 1
                if logger:
                    logger.error(f"Error processing {file_path_str}: {e}")

        return {
            "files_updated": files_updated,
            "replacements_made": replacements_made,
            "errors": errors,
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix non-ASCII characters in documentation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()

    fixer = DocumentationASCIIFixer()
    result = fixer.fix_ascii(dry_run=args.dry_run)

    print(
        f"\nFix ASCII: Updated {result['files_updated']} files, Made {result['replacements_made']} replacements, Errors {result['errors']}"
    )

    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
