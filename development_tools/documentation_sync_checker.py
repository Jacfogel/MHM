#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Synchronization Checker

This script helps identify and fix documentation synchronization issues:
- Flags outdated documentation paths during refactors
- Checks for paired AI/human documentation consistency
- Identifies path drift between code and documentation
- Generates directory trees for documentation

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python development_tools/documentation_sync_checker.py [--check] [--fix] [--generate-trees]
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from . import config
    from .services.standard_exclusions import should_exclude_file
    from .services.constants import (
        COMMAND_PATTERNS, COMMON_CLASS_NAMES, COMMON_CODE_PATTERNS,
        COMMON_FUNCTION_NAMES, COMMON_VARIABLE_NAMES, DEFAULT_DOCS, IGNORED_PATH_PATTERNS,
        PAIRED_DOCS, STANDARD_LIBRARY_MODULES, TEMPLATE_PATTERNS, THIRD_PARTY_LIBRARIES,
        CORE_MODULES
    )
except ImportError:
    from development_tools import config
    from development_tools.services.standard_exclusions import should_exclude_file
    from development_tools.services.constants import (
        COMMAND_PATTERNS, COMMON_CLASS_NAMES, COMMON_CODE_PATTERNS,
        COMMON_FUNCTION_NAMES, COMMON_VARIABLE_NAMES, DEFAULT_DOCS, IGNORED_PATH_PATTERNS,
        PAIRED_DOCS, STANDARD_LIBRARY_MODULES, TEMPLATE_PATTERNS, THIRD_PARTY_LIBRARIES,
        CORE_MODULES
    )

logger = get_component_logger("development_tools")

class DocumentationSyncChecker:
    """Checks and maintains documentation synchronization."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None):
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
        
        # Common path patterns that might drift - improved precision
        self.path_patterns = [
            # Only match backtick code that looks like file paths (not code blocks)
            # Use negative lookahead to avoid matching .md within .mdc or other extensions
            r'`([a-zA-Z_][a-zA-Z0-9_/]*\.py)`',
            r'`([a-zA-Z_][a-zA-Z0-9_/]*\.md)(?![a-zA-Z0-9])`',  # .md not followed by alphanumeric
            # Markdown links
            r'\[([^\]]+)\]\(([^)]+)\)',
            # Python imports - but only in non-code contexts
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ]
        
        # Directories to scan for code references - load from config
        # Use CORE_MODULES from constants (which loads from config) or fall back to scan_directories
        if CORE_MODULES:
            self.code_dirs = list(CORE_MODULES)
        else:
            # Fall back to scan_directories from config
            scan_dirs = config.get_scan_directories()
            self.code_dirs = scan_dirs if scan_dirs else ['core']  # Generic default
        
        # Get paths config for output directories
        paths_config = config.get_paths_config()
        self.docs_dir = paths_config.get('development_docs_dir', 'development_docs')
        
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
            # Skip files that should be excluded
            if should_exclude_file(str(md_file), 'documentation'):
                continue
                
            if md_file.name.startswith('.'):
                continue
            
            # Skip historical changelog files - they contain accurate historical references
            if 'CHANGELOG_DETAIL.md' in str(md_file) or 'AI_CHANGELOG.md' in str(md_file):
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract all path references with context awareness
                lines = content.split('\n')
                in_code_block = False
                
                for line_num, line in enumerate(lines):
                    # Track code block state
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    
                    # Skip extraction if we're inside a code block
                    if in_code_block:
                        continue
                    
                    # Check if this line is in an example context
                    if self._is_in_example_context(line, lines, line_num):
                        continue
                    
                    # Extract paths from this line
                    for pattern in self.path_patterns:
                        matches = re.findall(pattern, line)
                        for match in matches:
                            if isinstance(match, tuple):
                                # Handle regex groups (e.g., markdown links [text](url))
                                # For markdown links, check if URL part has valid path
                                if len(match) >= 2:
                                    link_text = match[0] if match[0] else ''
                                    url_part = match[1] if match[1] else ''
                                    
                                    # Skip if URL part is a valid file reference (has full path or exists)
                                    if url_part and not url_part.startswith(('http', '#')):
                                        # Check if URL part is a valid file reference
                                        source_dir = md_file.parent
                                        if self._is_valid_file_reference(url_part, source_dir):
                                            # URL part is valid, skip link text even if it looks like a file path
                                            # Only process the URL part
                                            if not self._is_likely_code_snippet(url_part, line):
                                                if not self._is_section_header_or_link_text(url_part, line):
                                                    doc_paths[str(md_file.relative_to(self.project_root))].append(url_part)
                                            continue
                                    
                                    # URL part not valid or not a file path, process link text if it looks like a file path
                                    if link_text and not link_text.startswith(('http', '#')):
                                        if link_text.endswith(('.py', '.md')) or '/' in link_text or '\\' in link_text:
                                            if not self._is_likely_code_snippet(link_text, line):
                                                if not self._is_section_header_or_link_text(link_text, line):
                                                    doc_paths[str(md_file.relative_to(self.project_root))].append(link_text)
                                else:
                                    # Single group match, process normally
                                    for idx, group in enumerate(match):
                                        if group and not group.startswith(('http', '#')):
                                            if not self._is_likely_code_snippet(group, line):
                                                if not self._is_section_header_or_link_text(group, line):
                                                    doc_paths[str(md_file.relative_to(self.project_root))].append(group)
                            else:
                                if match and not match.startswith(('http', '#')):
                                    # Additional context filtering
                                    if not self._is_likely_code_snippet(match, line):
                                        # Skip section headers and common markdown link text
                                        if not self._is_section_header_or_link_text(match, line):
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
        
        # Enhanced filtering patterns for false positives
        self._setup_enhanced_filters()
        
        # Files that document legacy patterns (expected to reference old paths)
        # Use normalized paths (forward slashes) for comparison
        legacy_documentation_files = {
            'development_docs/LEGACY_REFERENCE_REPORT.md',
            'development_docs\\LEGACY_REFERENCE_REPORT.md',  # Windows path
            'development_docs/CHANGELOG_DETAIL.md',  # May contain historical references
            'development_docs\\CHANGELOG_DETAIL.md',  # Windows path
            'ai_development_docs/AI_CHANGELOG.md',
            'ai_development_docs\\AI_CHANGELOG.md',  # Windows path
        }
        
        # Check if documented paths exist
        for doc_file, paths in doc_paths.items():
            # Get the directory of the source file for relative path resolution
            source_dir = self.project_root / doc_file
            if source_dir.is_file():
                source_dir = source_dir.parent
            
            # Skip legacy documentation files - they intentionally reference old paths
            # Normalize path for comparison (handle both / and \)
            normalized_doc_file = doc_file.replace('\\', '/')
            if normalized_doc_file in legacy_documentation_files or doc_file in legacy_documentation_files:
                continue
            
            for path in paths:
                # Apply enhanced filtering
                if self._should_skip_path(path, doc_file):
                    continue
                
                # Check if it's a markdown file reference
                if path.endswith('.md') or path.endswith('.py'):
                    if self._is_valid_file_reference(path, source_dir):
                        continue
                    else:
                        drift_issues[doc_file].append(f"Missing file: {path}")
                else:
                    # Check if it's a Python module reference
                    if self._is_valid_module_reference(path, code_paths):
                        continue
                    else:
                        drift_issues[doc_file].append(f"Potentially outdated module: {path}")
                    
        return drift_issues
    
    def _setup_enhanced_filters(self):
        """Setup enhanced filtering patterns to reduce false positives."""
        # Use centralized constants from services.constants
        self.stdlib_modules = STANDARD_LIBRARY_MODULES
        self.third_party_libs = set(THIRD_PARTY_LIBRARIES)
        self.function_names = set(COMMON_FUNCTION_NAMES)
        self.class_names = set(COMMON_CLASS_NAMES)
        self.variable_names = set(COMMON_VARIABLE_NAMES)
        self.code_patterns = set(COMMON_CODE_PATTERNS)
        self.ignored_paths = set(IGNORED_PATH_PATTERNS)
        self.command_patterns = set(COMMAND_PATTERNS)
        self.template_patterns = set(TEMPLATE_PATTERNS)
        # Note: ALTERNATIVE_DIRECTORIES removed - we now require full paths to avoid ambiguity
    
    def _should_skip_path(self, path: str, doc_file: str) -> bool:
        """Enhanced path filtering to reduce false positives."""
        # Skip URLs and anchors
        if path.startswith(('http', '#', 'mailto')):
            return True
        
        # Skip external website references and markdown section headers
        if path in self.ignored_paths:
            return True
        
        # Skip standard library modules
        if path in self.stdlib_modules:
            return True
        
        # Skip third-party libraries
        if path in self.third_party_libs:
            return True
        
        # Skip function names
        if path in self.function_names:
            return True
        
        # Skip class names
        if path in self.class_names:
            return True
        
        # Skip variable names and common words
        if path in self.variable_names:
            return True
        
        # Skip common code patterns
        if path in self.code_patterns:
            return True
        
        # Skip single words that are clearly not files
        if len(path.split('.')) == 1 and path.isalpha() and len(path) < 10:
            return True
        
        # Skip Python import patterns that are clearly not files
        if '.' in path and not path.endswith(('.py', '.md')):
            # Check if it's a valid Python module pattern
            parts = path.split('.')
            if all(part.isidentifier() for part in parts):
                # This looks like a Python module, not a file
                return True
        
        # Skip command references
        if any(path.startswith(cmd) for cmd in self.command_patterns):
            return True
        
        # Skip template patterns
        if any(pattern in path for pattern in self.template_patterns):
            return True
        
        # Skip glob patterns
        if '*' in path or '?' in path:
            return True
        
        # Skip incomplete patterns
        if path.endswith('_') or path.startswith('_'):
            return True
        
        # NEW: Skip code blocks and method calls
        if '(' in path and ')' in path:
            return True
        
        # NEW: Skip paths that look like method calls or function calls
        if '.' in path and any(char in path for char in ['(', ')', '=', ' ']):
            return True
        
        # NEW: Skip paths that contain Python keywords or operators
        python_keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
        if any(keyword in path for keyword in python_keywords):
            return True
        
        # NEW: Skip paths that look like code snippets (contain newlines or are very long)
        if '\n' in path or len(path) > 200:
            return True
        
        # NEW: Skip paths that contain Python operators
        if any(op in path for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=', '//=', '**=', '&=', '|=', '^=', '<<=', '>>=']):
            return True
        
        return False
    
    def _is_likely_code_snippet(self, path: str, line: str) -> bool:
        """Check if a path looks like it's part of a code snippet rather than a file reference."""
        # Skip if it contains method calls
        if '(' in path and ')' in path:
            return True
        
        # Skip if it contains Python operators
        if any(op in path for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=', '//=', '**=']):
            return True
        
        # Skip if it contains Python keywords
        python_keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda']
        if any(keyword in path for keyword in python_keywords):
            return True
        
        # Skip if the line looks like code (contains indentation and Python syntax)
        if line.strip().startswith(('    ', '\t')) and any(char in line for char in ['(', ')', '=', ':', 'def', 'class', 'import', 'from']):
            return True
        
        # Skip if it's very long (likely a code snippet)
        if len(path) > 100:
            return True
        
        # Skip if it contains newlines (definitely a code snippet)
        if '\n' in path:
            return True
        
        return False
    
    def _is_section_header_or_link_text(self, path: str, line: str) -> bool:
        """Check if a path is actually a markdown section header or link text that shouldn't be treated as a file path."""
        # Common section header patterns (title case, multiple words, no file extension)
        if not path.endswith(('.py', '.md', '.json', '.txt', '.yaml', '.yml', '.toml', '.ini', '.cfg')):
            # Check if it looks like a section header (title case, spaces, common words)
            if ' ' in path and path[0].isupper():
                # Common section header words
                section_words = [
                    'overview', 'summary', 'introduction', 'background', 'context',
                    'recommendations', 'suggestions', 'guidelines', 'best practices',
                    'implementation', 'status', 'progress', 'analysis', 'review',
                    'findings', 'conclusion', 'next steps', 'action items', 'todo',
                    'issues', 'problems', 'solutions', 'approach', 'strategy',
                    'architecture', 'design', 'structure', 'organization', 'layout'
                ]
                path_lower = path.lower()
                # If it contains section header words and doesn't look like a file path
                if any(word in path_lower for word in section_words):
                    # Check if it's in a markdown link pointing to an anchor
                    if re.search(rf'\[{re.escape(path)}\]\(#', line):
                        return True
                    # Check if it's in a numbered list with markdown links
                    if re.search(rf'^\d+\.\s*\[{re.escape(path)}\]\(#', line):
                        return True
        
        # Skip if it's clearly a section header in a table of contents
        if re.search(rf'^\d+\.\s*\[{re.escape(path)}\]\(#', line):
            return True
        
        # Skip if it's in a markdown link that points to an anchor (not a file)
        if re.search(rf'\[{re.escape(path)}\]\(#[^)]+\)', line):
            return True
        
        return False
    
    def _is_in_example_context(self, line: str, lines: List[str], line_num: int) -> bool:
        """
        Check if a line is in an example context based on documentation standards.
        
        Examples must be marked using one of these standards:
        1. Example markers: [OK], [AVOID], [GOOD], [BAD], [EXAMPLE] at start of section
        2. Example headings: "Examples:", "Example Usage:", "Example Code:" headings
        3. Code blocks: Automatically excluded (handled separately)
        4. Archive references: Lines containing "archive" or "archived" (for archived file references)
        
        This method implements the example marking standards defined in DOCUMENTATION_GUIDE.md section 2.6.
        """
        line_stripped = line.strip()
        line_lower = line.lower()
        
        # Standard 4: Check if line contains "archive" or "archived" (for archived file references)
        if 'archive' in line_lower or 'archived' in line_lower:
            return True
        
        # Standard 1: Check for example markers at the start of the line
        # These are the official markers per documentation standards
        example_markers = [
            r'^\[OK\]', r'^\[AVOID\]', r'^\[GOOD\]', r'^\[BAD\]', r'^\[EXAMPLE\]',
        ]
        for marker in example_markers:
            if re.match(marker, line_stripped, re.IGNORECASE):
                return True
        
        # Standard 1 (continued): Check previous lines (up to 5 lines back) for example markers
        # This catches cases where [AVOID] or [OK] is on a previous line (per standard)
        for i in range(max(0, line_num - 5), line_num):
            prev_line = lines[i].strip()
            prev_line_lower = prev_line.lower()
            # Check for archive references in previous lines too
            if 'archive' in prev_line_lower or 'archived' in prev_line_lower:
                if line_num - i <= 3:  # Within 3 lines of archive reference
                    return True
            for marker in example_markers:
                if re.match(marker, prev_line, re.IGNORECASE):
                    # If we found a marker, check if current line is part of the example
                    # (list item, continuation, or within same section)
                    if line_stripped.startswith(('-', '*', '1.', '2.', '3.', '  ')) or \
                       line_num - i <= 3:  # Within 3 lines of the marker
                        return True
        
        # Standard 2: Check if we're in an "Examples" section by looking backwards for section headers
        # Look back up to 20 lines for section headers (per standard)
        for i in range(max(0, line_num - 20), line_num):
            prev_line = lines[i].strip()
            # Check for "Examples:" or "Example Usage:" or "Example Code:" headings (per standard)
            if re.match(r'^#+\s+(Examples?|Example\s+Usage|Example\s+Code)', prev_line, re.IGNORECASE):
                return True
            # Check for bold "Examples:" or "Example Usage:" text
            if re.match(r'^\*\*(Examples?|Example\s+Usage)\*\*', prev_line, re.IGNORECASE):
                return True
        
        # Note: Code blocks are handled separately in scan_documentation_paths() by checking in_code_block
        # This is Standard 3 and doesn't need to be checked here
        
        return False
    
    def _is_valid_file_reference(self, path: str, source_dir: Path) -> bool:
        """Check if a file reference is valid."""
        # Skip obvious glob patterns
        if path.startswith('*') or path.endswith('*') or '/*' in path:
            return True
        
        # Skip command references
        if path.startswith('python ') or path.startswith('pip ') or path.startswith('git '):
            return True
        
        # Skip template patterns
        if '{' in path and '}' in path:
            return True
        
        # Skip test template patterns
        if path.startswith('test_<') or path.endswith('>.py'):
            return True
        
        # Check if the file exists
        file_path = self.project_root / path
        if file_path.exists():
            return True
        
        # If checking for .md file, also check if .mdc file exists (avoid false positives)
        if path.endswith('.md'):
            mdc_path = path[:-2] + 'c'  # Replace .md with .mdc
            mdc_file = self.project_root / mdc_path
            if mdc_file.exists():
                return True  # Valid reference to .mdc file, not a missing .md file
        
        # Check relative paths (both ../ paths and same-directory paths)
        # First check if it's a relative path starting with ../
        if path.startswith('../'):
            relative_path = source_dir / path
            if relative_path.exists():
                return True
            
            # Also check for .mdc variant in relative paths
            if path.endswith('.md'):
                mdc_path = path[:-2] + 'c'
                mdc_relative = source_dir / mdc_path
                if mdc_relative.exists():
                    return True
        else:
            # For paths without ../, check relative to source file's directory
            # This handles same-directory references (e.g., config.py in development_tools/)
            relative_path = source_dir / path
            if relative_path.exists():
                return True
            
            # Also check for .mdc variant
            if path.endswith('.md'):
                mdc_path = path[:-2] + 'c'
                mdc_relative = source_dir / mdc_path
                if mdc_relative.exists():
                    return True
        
        return False
    
    def _is_valid_module_reference(self, path: str, code_paths: set) -> bool:
        """Check if a module reference is valid."""
        # Skip if it's a standard library module
        if path in self.stdlib_modules:
            return True
        
        # Skip if it's a third-party library
        if path in self.third_party_libs:
            return True
        
        # Skip if it's a function name
        if path in self.function_names:
            return True
        
        # Skip if it's a class name
        if path in self.class_names:
            return True
        
        # Skip if it's a variable name
        if path in self.variable_names:
            return True
        
        # Skip if it's a common code pattern
        if path in self.code_patterns:
            return True
        
        # Skip valid package-level exports (e.g., CommunicationManager from communication package)
        # These are valid even if not directly importable via static analysis
        valid_package_exports = {
            'CommunicationManager',  # Exported via __getattr__ in communication/__init__.py
        }
        if path in valid_package_exports:
            return True
        
        # Check if this path exists in the codebase
        normalized_path = path.replace('.', '/').replace('\\', '/')
        for code_path in code_paths:
            if normalized_path in code_path or code_path in normalized_path:
                return True
        
        return False
    
    def generate_directory_tree(self, output_file: Optional[str] = None) -> str:
        """Generate a directory tree for documentation with placeholders for certain directories."""
        import subprocess
        
        # Use provided output_file or default from config
        if output_file is None:
            output_file = f"{self.docs_dir}/DIRECTORY_TREE.md"
        
        # Run tree command
        result = subprocess.run(['tree', '/F', '/A'], capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            if logger:
                logger.error("Error running tree command")
            return ""
        
        lines = result.stdout.split('\n')
        
        # Import constants from services
        from development_tools.services.standard_exclusions import DOC_SYNC_PLACEHOLDERS
        placeholders = DOC_SYNC_PLACEHOLDERS
        
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
            f"> **File**: `{output_file}`",
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
    
    def check_ascii_compliance(self) -> Dict[str, List[str]]:
        """Check for non-ASCII characters in documentation files."""
        ascii_issues = defaultdict(list)
        
        # Import constants from services.constants
        from development_tools.services.constants import ASCII_COMPLIANCE_FILES
        files_to_check = list(ASCII_COMPLIANCE_FILES)
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for non-ASCII characters
                non_ascii_chars = []
                for i, char in enumerate(content):
                    if ord(char) > 127:  # Non-ASCII character
                        non_ascii_chars.append({
                            'char': char,
                            'position': i,
                            'codepoint': ord(char)
                        })
                
                if non_ascii_chars:
                    # Group by character type for better reporting
                    char_types = {}
                    for char_info in non_ascii_chars:
                        char = char_info['char']
                        if char not in char_types:
                            char_types[char] = []
                        char_types[char].append(char_info['position'])
                    
                    for char, positions in char_types.items():
                        ascii_issues[file_path].append(
                            f"Non-ASCII character '{char}' (U+{ord(char):04X}) at positions: {positions[:5]}{'...' if len(positions) > 5 else ''}"
                        )
                        
            except Exception as e:
                ascii_issues[file_path].append(f"Error reading file: {e}")
        
        return ascii_issues

    def check_heading_numbering(self) -> Dict[str, List[str]]:
        """Check that H2 and H3 headings are numbered consecutively starting at 1 (or 0)."""
        numbering_issues = defaultdict(list)
        
        # Import constants from services.constants
        from development_tools.services.constants import DEFAULT_DOCS
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
                numbering_issues[file_path].append(f"Error reading file: {e}")
        
        return numbering_issues

    def run_checks(self) -> Dict[str, any]:
        """Run all documentation synchronization checks."""
        if logger:
            logger.info("Running documentation synchronization checks...")
        
        results = {
            'paired_docs': self.check_paired_documentation(),
            'path_drift': self.check_path_drift(),
            'ascii_compliance': self.check_ascii_compliance(),
            'heading_numbering': self.check_heading_numbering(),
            'summary': {}
        }
        
        # Generate summary
        total_issues = sum(len(issues) for issues in results['paired_docs'].values())
        total_issues += sum(len(issues) for issues in results['path_drift'].values())
        total_issues += sum(len(issues) for issues in results['ascii_compliance'].values())
        total_issues += sum(len(issues) for issues in results['heading_numbering'].values())
        
        results['summary'] = {
            'total_issues': total_issues,
            'paired_doc_issues': len(results['paired_docs']),
            'path_drift_issues': len(results['path_drift']),
            'ascii_compliance_issues': len(results['ascii_compliance']),
            'heading_numbering_issues': len(results['heading_numbering']),
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
        print(f"   ASCII Compliance Issues: {summary['ascii_compliance_issues']}")
        print(f"   Heading Numbering Issues: {summary['heading_numbering_issues']}")
        
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
        
        # ASCII Compliance Issues
        if results['ascii_compliance']:
            print(f"\nASCII COMPLIANCE ISSUES:")
            print(f"   Total files with non-ASCII characters: {len(results['ascii_compliance'])}")
            print(f"   Total issues found: {sum(len(issues) for issues in results['ascii_compliance'].values())}")
            print(f"   Files with non-ASCII characters:")
            for doc_file, issues in results['ascii_compliance'].items():
                print(f"     {doc_file}: {len(issues)} issues")
                for issue in issues[:3]:  # Show first 3 issues per file
                    # Clean Unicode characters that cause encoding issues
                    clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                    print(f"       - {clean_issue}")
                if len(issues) > 3:
                    print(f"       ... and {len(issues) - 3} more issues")
        
        # Heading Numbering Issues
        if results['heading_numbering']:
            print(f"\nHEADING NUMBERING ISSUES:")
            print(f"   Total files with numbering issues: {len(results['heading_numbering'])}")
            print(f"   Total issues found: {sum(len(issues) for issues in results['heading_numbering'].values())}")
            print(f"   Files with numbering issues:")
            for doc_file, issues in results['heading_numbering'].items():
                print(f"     {doc_file}: {len(issues)} issues")
                for issue in issues[:5]:  # Show first 5 issues per file
                    # Clean Unicode characters that cause encoding issues
                    clean_issue = issue.encode('ascii', 'ignore').decode('ascii')
                    print(f"       - {clean_issue}")
                if len(issues) > 5:
                    print(f"       ... and {len(issues) - 5} more issues")
        
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
