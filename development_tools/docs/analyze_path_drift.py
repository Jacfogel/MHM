#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Path Drift Analyzer

This script checks for path drift between code and documentation. It scans the
codebase for file paths and imports, then compares them with paths referenced
in documentation files. Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python docs/analyze_path_drift.py
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != '__main__' and __package__ and '.' in __package__:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
    from ..shared.constants import (
        COMMAND_PATTERNS, COMMON_CLASS_NAMES, COMMON_CODE_PATTERNS,
        COMMON_FUNCTION_NAMES, COMMON_VARIABLE_NAMES, IGNORED_PATH_PATTERNS,
        STANDARD_LIBRARY_MODULES, TEMPLATE_PATTERNS, THIRD_PARTY_LIBRARIES,
        CORE_MODULES
    )
else:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools.shared.constants import (
        COMMAND_PATTERNS, COMMON_CLASS_NAMES, COMMON_CODE_PATTERNS,
        COMMON_FUNCTION_NAMES, COMMON_VARIABLE_NAMES, IGNORED_PATH_PATTERNS,
        STANDARD_LIBRARY_MODULES, TEMPLATE_PATTERNS, THIRD_PARTY_LIBRARIES,
        CORE_MODULES
    )

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, 'load_external_config'):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")


class PathDriftAnalyzer:
    """Analyzes path drift between code and documentation."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None, use_cache: bool = True):
        """
        Initialize path drift analyzer.
        
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
        
        # Caching - use standardized storage
        from development_tools.shared.mtime_cache import MtimeFileCache
        # cache_file parameter kept for backward compatibility but not used (standardized storage always used)
        cache_file = self.project_root / "development_tools" / "docs" / ".path_drift_cache.json"
        self.cache = MtimeFileCache(cache_file, self.project_root, use_cache=use_cache,
                                    tool_name='analyze_path_drift', domain='docs')
    
    def _setup_enhanced_filters(self):
        """Setup enhanced filtering patterns to reduce false positives."""
        # Use centralized constants from shared.constants
        self.stdlib_modules = STANDARD_LIBRARY_MODULES
        self.third_party_libs = set(THIRD_PARTY_LIBRARIES)
        self.function_names = set(COMMON_FUNCTION_NAMES)
        self.class_names = set(COMMON_CLASS_NAMES)
        self.variable_names = set(COMMON_VARIABLE_NAMES)
        self.code_patterns = set(COMMON_CODE_PATTERNS)
        self.ignored_paths = set(IGNORED_PATH_PATTERNS)
        self.command_patterns = set(COMMAND_PATTERNS)
        self.template_patterns = set(TEMPLATE_PATTERNS)
    
    def _should_skip_path_drift_check(self, doc_file: str) -> bool:
        """Check if a file should be skipped from path drift checking.
        
        Skips:
        - Files with "PLAN" in the name (historical context files)
        - Files in .cursor/plans/ directory
        - Files in archive directories
        - Test fixture files (intentional test data, not real documentation issues)
        
        Note: Example sections within files are excluded via _is_in_example_context(),
        not by excluding entire files.
        """
        doc_file_lower = doc_file.lower()
        doc_file_path = Path(doc_file)
        
        # Skip files with "PLAN" in the name (historical context)
        if 'plan' in doc_file_lower:
            return True
        
        # Skip .cursor/ directory files (plans, rules, etc.)
        if '.cursor' in doc_file_path.parts:
            return True
        
        # Skip archive directories
        if 'archive' in doc_file_path.parts:
            return True
        
        # Skip test fixture files (intentional test data, not real documentation issues)
        # These are in tests/fixtures/ or tests/fixtures/development_tools_demo/
        if 'tests' in doc_file_path.parts and 'fixtures' in doc_file_path.parts:
            return True
        
        return False
    
    def _should_skip_path(self, path: str, doc_file: str) -> bool:
        """Enhanced path filtering to reduce false positives."""
        # Skip URLs and anchors
        if path.startswith(('http', '#', 'mailto')):
            return True
        
        # Skip Python __future__ feature names (not modules)
        if path == 'annotations' or path == '__future__':
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
        
        # Skip code blocks and method calls
        if '(' in path and ')' in path:
            return True
        
        # Skip paths that look like method calls or function calls
        if '.' in path and any(char in path for char in ['(', ')', '=', ' ']):
            return True
        
        # Skip paths that contain Python keywords or operators
        # Check for whole-word matches only (not substrings)
        python_keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
        # Use word boundaries to avoid false positives (e.g., "in" in "nonexistent")
        import re
        for keyword in python_keywords:
            # Match whole word only, not as substring
            if re.search(r'\b' + re.escape(keyword) + r'\b', path):
                return True
        
        # Skip paths that look like code snippets (contain newlines or are very long)
        if '\n' in path or len(path) > 200:
            return True
        
        # Skip paths that contain Python operators
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
        5. Example phrases: "for example", "for instance", "e.g.", etc.
        
        This method implements the example marking standards defined in DOCUMENTATION_GUIDE.md section 2.6.
        Uses the same logic as fix_documentation.py for consistency.
        """
        line_stripped = line.strip()
        line_lower = line.lower()
        
        # Standard 4: Check if line contains "archive" or "archived" (for archived file references)
        if 'archive' in line_lower or 'archived' in line_lower:
            return True
        
        # Check for [ARCHIVED] marker (similar to [EXAMPLE])
        if '[archived]' in line_lower:
            return True
        
        # Standard 5: Check for example phrases in the current line
        example_phrases = ['for example', 'for instance', 'e.g.,', 'e.g.', 'example:', 'examples:']
        for phrase in example_phrases:
            if phrase in line_lower:
                return True
        
        # Standard 1: Check for example markers at the start of the line
        # These are the official markers per documentation standards
        example_markers = [
            r'^\[OK\]', r'^\[AVOID\]', r'^\[GOOD\]', r'^\[BAD\]', r'^\[EXAMPLE\]',
        ]
        for marker in example_markers:
            if re.match(marker, line_stripped, re.IGNORECASE):
                return True
        
        # Standard 1 & 5 (continued): Check previous lines (up to 10 lines back) for example markers and phrases
        # This catches cases where [AVOID] or [OK] or [EXAMPLE] or [ARCHIVED] is on a previous line (per standard)
        for i in range(max(0, line_num - 10), line_num):
            prev_line = lines[i].strip()
            prev_line_lower = prev_line.lower()
            # Check for archive references in previous lines too
            if 'archive' in prev_line_lower or 'archived' in prev_line_lower:
                if line_num - i <= 10:  # Within 10 lines of archive reference (extended for [ARCHIVED] sections)
                    return True
            # Check for [ARCHIVED] marker in previous lines
            if '[archived]' in prev_line_lower:
                if line_num - i <= 10:  # Within 10 lines of [ARCHIVED] marker
                    return True
            # Check for example phrases in previous lines
            for phrase in example_phrases:
                if phrase in prev_line_lower:
                    if line_num - i <= 3:  # Within 3 lines of example phrase
                        return True
            # Check for example markers in previous lines
            for marker in example_markers:
                if re.match(marker, prev_line, re.IGNORECASE):
                    # If we found a marker, check if current line is part of the example
                    # (list item, continuation, or within same section)
                    if line_stripped.startswith(('-', '*', '1.', '2.', '3.', '  ')) or \
                       line_num - i <= 10:  # Within 10 lines of the marker (extended for [EXAMPLE] sections)
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
    
    def _is_valid_module_reference(self, path: str, code_paths: Set[str]) -> bool:
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
        # Ensure enhanced filters are set up (needed by filtering methods)
        if not hasattr(self, 'stdlib_modules'):
            self._setup_enhanced_filters()
        
        doc_paths = defaultdict(list)
        
        for md_file in self.project_root.rglob("*.md"):
            # Skip files that should be excluded
            # Check path relative to project root to avoid matching parent directory exclusions
            rel_path = str(md_file.relative_to(self.project_root))
            if should_exclude_file(rel_path, 'documentation'):
                continue
                
            if md_file.name.startswith('.'):
                continue
            
            # Skip historical changelog files - they contain accurate historical references
            if 'CHANGELOG_DETAIL.md' in str(md_file) or 'AI_CHANGELOG.md' in str(md_file):
                continue
            
            # Check cache first
            cached_paths = self.cache.get_cached(md_file)
            if cached_paths is not None:
                if cached_paths:
                    rel_path = str(md_file.relative_to(self.project_root))
                    doc_paths[rel_path] = cached_paths
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
                
                # Cache results for this file
                rel_path = str(md_file.relative_to(self.project_root))
                file_paths = doc_paths.get(rel_path, [])
                self.cache.cache_results(md_file, file_paths)
                                
            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {md_file}: {e}")
                # Cache empty result for files with errors
                self.cache.cache_results(md_file, [])
        
        # Save cache
        self.cache.save_cache()
        
        return doc_paths
    
    def check_path_drift(self) -> Dict[str, List[str]]:
        """
        Check for path drift between code and documentation.
        
        Returns:
            Dictionary mapping file paths to lists of issues
        """
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
            # Skip files that shouldn't be checked for path drift
            if self._should_skip_path_drift_check(doc_file):
                continue
            
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
    
    def run_analysis(self) -> Dict[str, Any]:
        """
        Run path drift analysis and return results in standard format.
        
        Returns:
            Dictionary with standard format: 'summary', 'files', and 'details' keys
        """
        drift_issues = self.check_path_drift()
        
        # Convert to structured format
        files = {}
        total_issues = 0
        for doc_file, issues in drift_issues.items():
            issue_count = len(issues)
            files[doc_file] = issue_count
            total_issues += issue_count
        
        # Return standard format
        return {
            'summary': {
                'total_issues': total_issues,
                'files_affected': len(files)
            },
            'files': files,
            'details': {
                'detailed_issues': dict(drift_issues)  # Keep detailed issues for reference
            }
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check for path drift between code and documentation")
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    analyzer = PathDriftAnalyzer()
    structured_results = analyzer.run_analysis()
    
    if args.json:
        import json
        print(json.dumps(structured_results, indent=2))
        return 0
    
    # Print results in human-readable format
    # run_analysis() always returns standard format with 'summary', 'files', and 'details' keys
    summary = structured_results.get('summary', {})
    total_issues = summary.get('total_issues', 0)
    files = structured_results.get('files', {})
    details = structured_results.get('details', {})
    results = details.get('detailed_issues', {})
    
    if results:
        print(f"\nPath Drift Issues:")
        print(f"   Total files with issues: {len(results)}")
        print(f"   Total issues found: {total_issues}")
        print(f"   Top files with most issues:")
        sorted_files = sorted(files.items(), key=lambda x: x[1], reverse=True)
        for doc_file, issue_count in sorted_files[:5]:
            print(f"     {doc_file}: {issue_count} issues")
    else:
        print("\nNo path drift issues found!")
    
    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())

