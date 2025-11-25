#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: mhm-specific

"""Analyze documentation overlap, duplicates, and placeholder content."""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from .services.common import ProjectPaths, ensure_ascii, load_text, run_cli, summary_block
    from .services.constants import CORRUPTED_ARTIFACT_PATTERNS, DEFAULT_DOCS, PAIRED_DOCS
except ImportError:
    from services.common import ProjectPaths, ensure_ascii, load_text, run_cli, summary_block
    from services.constants import CORRUPTED_ARTIFACT_PATTERNS, DEFAULT_DOCS, PAIRED_DOCS

PATHS = ProjectPaths()

PLACEHOLDER_PATTERNS = (
    re.compile(r'TBD', re.IGNORECASE),
    re.compile(r'TODO'),
    re.compile(r'to be filled', re.IGNORECASE),
    re.compile(r'\[insert[^\]]*\]', re.IGNORECASE),
)


def extract_sections(content: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current = 'Introduction'
    buffer: List[str] = []
    for line in content.splitlines():
        if line.startswith('## '):
            sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip()
            buffer = []
        elif line.startswith('### '):
            sections[current] = "\n".join(buffer).strip()
            current = line[4:].strip()
            buffer = []
        else:
            buffer.append(line)
    sections[current] = "\n".join(buffer).strip()
    return sections

def load_documents(paths: Sequence[str]) -> Tuple[Dict[str, str], List[str]]:
    docs: Dict[str, str] = {}
    missing: List[str] = []
    for rel in paths:
        absolute = (PATHS.root / rel).resolve()
        if not absolute.exists():
            missing.append(rel)
            continue
        docs[rel] = load_text(absolute)
    return docs, missing


def analyse_topics(docs: Dict[str, str]) -> Dict[str, List[str]]:
    topics = defaultdict(list)
    keyword_map = {
        'Setup & Installation': ['install', 'setup', 'environment', 'run'],
        'Development Workflow': ['workflow', 'develop', 'commit', 'merge', 'refactor'],
        'Testing': ['test', 'pytest', 'coverage', 'suite'],
        'Architecture': ['architecture', 'module', 'dependency', 'structure'],
        'Troubleshooting': ['error', 'issue', 'debug', 'fail', 'failure'],
        'Code Quality': ['quality', 'lint', 'style', 'pattern'],
        'Project Structure': ['directory', 'structure', 'tree'],
    }
    for name, content in docs.items():
        lower = content.lower()
        for label, keywords in keyword_map.items():
            if any(keyword in lower for keyword in keywords):
                topics[label].append(name)
    return dict(topics)


def detect_duplicates(docs: Dict[str, str]) -> List[Dict[str, object]]:
    duplicates: List[Dict[str, object]] = []
    for human_path, ai_path in PAIRED_DOCS.items():
        human_text = docs.get(human_path)
        ai_text = docs.get(ai_path)
        if not human_text or not ai_text:
            continue
        human_sections = extract_sections(human_text)
        ai_sections = extract_sections(ai_text)
        for section, human_content in human_sections.items():
            ai_content = ai_sections.get(section)
            if not ai_content:
                continue
            human_normalised = re.sub(r'\s+', ' ', human_content.strip())
            ai_normalised = re.sub(r'\s+', ' ', ai_content.strip())
            if human_normalised and human_normalised == ai_normalised:
                duplicates.append({
                    'section': section,
                    'human_file': human_path,
                    'ai_file': ai_path,
                    'content_length': len(human_content),
                })
    return duplicates


def detect_placeholders(docs: Dict[str, str]) -> List[Dict[str, object]]:
    matches: List[Dict[str, object]] = []
    for name, content in docs.items():
        hits = []
        for pattern in PLACEHOLDER_PATTERNS:
            found = pattern.findall(content)
            if found:
                hits.extend(found)
        if hits:
            matches.append({'file': name, 'matches': sorted(set(hits))})
    return matches


def detect_corrupted_artifacts(docs: Dict[str, str]) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    for name, content in docs.items():
        for idx, line in enumerate(content.splitlines(), 1):
            for label, pattern in CORRUPTED_ARTIFACT_PATTERNS:
                if pattern.search(line):
                    issues.append({
                        'file': name,
                        'line': idx,
                        'pattern': label,
                        'snippet': line.strip(),
                    })
                    break
    return issues


def document_profiles(docs: Dict[str, str]) -> List[str]:
    lines: List[str] = []
    for name, content in sorted(docs.items()):
        sections = extract_sections(content)
        preview = ', '.join(sections.keys())
        lines.append(f"{name}: {len(sections)} sections, {len(content)} chars")
        if preview:
            lines.append(f"  Sections: {preview[:120]}")
    return lines


def format_summary(
    docs: Dict[str, str],
    missing: List[str],
    duplicates: List[Dict[str, object]],
    placeholders: List[Dict[str, object]],
    artifacts: List[Dict[str, object]],
) -> str:
    blocks: List[str] = []
    blocks.append(summary_block('Files Analysed', [f"{len(docs)} files", *sorted(docs.keys())]))
    if missing:
        blocks.append(summary_block('Missing Files', sorted(missing)))
    topics = analyse_topics(docs)
    if topics:
        topic_lines = []
        for label, files in sorted(topics.items()):
            topic_lines.append(f"{label} ({len(files)} files)")
            topic_lines.extend(f"  - {file}" for file in sorted(files))
        blocks.append(summary_block('Common Topics', topic_lines))
    profiles = document_profiles(docs)
    if profiles:
        blocks.append(summary_block('Document Profiles', profiles))
    if duplicates:
        dup_lines = [
            f"{item['section']} -> {item['human_file']} <-> {item['ai_file']} ({item['content_length']} chars)"
            for item in duplicates
        ]
        blocks.append(summary_block('Verbatim Duplicates', dup_lines))
    if placeholders:
        placeholder_lines = [f"{entry['file']}: {', '.join(entry['matches'])}" for entry in placeholders]
        blocks.append(summary_block('Placeholder Content', placeholder_lines))
    if artifacts:
        artifact_lines = [
            f"{entry['file']}:{entry['line']} [{entry['pattern']}] {entry['snippet'][:120]}"
            for entry in artifacts
        ]
        blocks.append(summary_block('Corrupted Artifacts', artifact_lines))
    return "\n".join(blocks)



def execute(args: argparse.Namespace):
    targets = args.files or DEFAULT_DOCS
    docs, missing = load_documents(targets)
    duplicates = detect_duplicates(docs)
    placeholders = detect_placeholders(docs)
    artifacts = detect_corrupted_artifacts(docs)
    summary = format_summary(docs, missing, duplicates, placeholders, artifacts)
    payload = {
        'documents': sorted(docs.keys()),
        'missing': sorted(missing),
        'duplicates': duplicates,
        'placeholders': placeholders,
        'artifacts': artifacts,
    }
    exit_code = 0
    if duplicates or placeholders or artifacts:
        exit_code = 1
    return exit_code, ensure_ascii(summary), payload


def main() -> int:
    argument_spec = [(
        ('--files',),
        {
            'nargs': '+',
            'metavar': 'REL_PATH',
            'help': 'Specific documentation files to analyze (relative to project root).',
        },
    )]
    return run_cli(execute, description='Analyze documentation overlap and quality.', arguments=argument_spec)


if __name__ == '__main__':
    raise SystemExit(main())
