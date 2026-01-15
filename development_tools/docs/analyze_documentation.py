#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Analyze documentation overlap, duplicates, and placeholder content."""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
    from ..shared.common import (
        ProjectPaths,
        ensure_ascii,
        load_text,
        run_cli,
        summary_block,
    )
    from ..shared.constants import (
        CORRUPTED_ARTIFACT_PATTERNS,
        DEFAULT_DOCS,
        PAIRED_DOCS,
    )
except ImportError:
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config
    from development_tools.shared.common import (
        ProjectPaths,
        ensure_ascii,
        load_text,
        run_cli,
        summary_block,
    )
    from development_tools.shared.constants import (
        CORRUPTED_ARTIFACT_PATTERNS,
        DEFAULT_DOCS,
        PAIRED_DOCS,
    )

# Load external config on module import
config.load_external_config()

# Get configuration
DOC_ANALYSIS_CONFIG = config.get_documentation_analysis_config()


# Build placeholder patterns from config
def _build_placeholder_patterns():
    """Build placeholder regex patterns from config."""
    patterns = []
    placeholder_patterns = DOC_ANALYSIS_CONFIG.get(
        "placeholder_patterns",
        [
            r"TBD",
            r"TODO",
            r"to be filled",
            r"\[insert[^\]]*\]",
        ],
    )
    placeholder_flags = DOC_ANALYSIS_CONFIG.get("placeholder_flags", ["IGNORECASE"])
    flags = 0
    if "IGNORECASE" in placeholder_flags:
        flags |= re.IGNORECASE

    for pattern_str in placeholder_patterns:
        patterns.append(re.compile(pattern_str, flags))
    return tuple(patterns)


PLACEHOLDER_PATTERNS = _build_placeholder_patterns()

# Initialize PATHS (can be overridden in execute)
PATHS = ProjectPaths()

PLACEHOLDER_PATTERNS = (
    re.compile(r"TBD", re.IGNORECASE),
    re.compile(r"TODO"),
    re.compile(r"to be filled", re.IGNORECASE),
    re.compile(r"\[insert[^\]]*\]", re.IGNORECASE),
)


def extract_sections(
    content: str, heading_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """Extract sections from content using configurable heading patterns."""
    if heading_patterns is None:
        heading_patterns = DOC_ANALYSIS_CONFIG.get("heading_patterns", ["## ", "### "])

    sections: Dict[str, str] = {}
    current = "Introduction"
    buffer: List[str] = []
    # Ensure heading_patterns is not None (should be guaranteed by line 76, but type checker needs help)
    assert heading_patterns is not None, "heading_patterns should be set by default"
    for line in content.splitlines():
        matched = False
        for pattern in heading_patterns:
            if line.startswith(pattern):
                sections[current] = "\n".join(buffer).strip()
                current = line[len(pattern) :].strip()
                buffer = []
                matched = True
                break
        if not matched:
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


def analyse_topics(
    docs: Dict[str, str], keyword_map: Optional[Dict[str, List[str]]] = None
) -> Dict[str, List[str]]:
    """Analyze topics in documents using configurable keyword map."""
    if keyword_map is None:
        keyword_map = DOC_ANALYSIS_CONFIG.get(
            "topic_keywords",
            {
                "Setup & Installation": ["install", "setup", "environment", "run"],
                "Development Workflow": [
                    "workflow",
                    "develop",
                    "commit",
                    "merge",
                    "refactor",
                ],
                "Testing": ["test", "pytest", "coverage", "suite"],
                "Architecture": ["architecture", "module", "dependency", "structure"],
                "Troubleshooting": ["error", "issue", "debug", "fail", "failure"],
                "Code Quality": ["quality", "lint", "style", "pattern"],
                "Project Structure": ["directory", "structure", "tree"],
            },
        )

    topics = defaultdict(list)
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
            human_normalised = re.sub(r"\s+", " ", human_content.strip())
            ai_normalised = re.sub(r"\s+", " ", ai_content.strip())
            if human_normalised and human_normalised == ai_normalised:
                duplicates.append(
                    {
                        "section": section,
                        "human_file": human_path,
                        "ai_file": ai_path,
                        "content_length": len(human_content),
                    }
                )
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
            matches.append({"file": name, "matches": sorted(set(hits))})
    return matches


def detect_corrupted_artifacts(docs: Dict[str, str]) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    for name, content in docs.items():
        for idx, line in enumerate(content.splitlines(), 1):
            for label, pattern in CORRUPTED_ARTIFACT_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        {
                            "file": name,
                            "line": idx,
                            "pattern": label,
                            "snippet": line.strip(),
                        }
                    )
                    break
    return issues


def document_profiles(docs: Dict[str, str]) -> List[str]:
    lines: List[str] = []
    for name, content in sorted(docs.items()):
        sections = extract_sections(content)
        preview = ", ".join(sections.keys())
        lines.append(f"{name}: {len(sections)} sections, {len(content)} chars")
        if preview:
            lines.append(f"  Sections: {preview[:120]}")
    return lines


def detect_section_overlaps(docs: Dict[str, str]) -> Dict[str, List[str]]:
    """Detect sections that appear in multiple files (overlap detection).

    Enhanced to provide more actionable insights:
    - Filters out common/expected overlaps (e.g., "Purpose", "Overview")
    - Excludes paired documentation headers (which are required to match)
    - Identifies high-value overlaps (sections with significant content)
    - Provides context about why overlaps might be problematic
    """
    # Import PAIRED_DOCS to exclude paired doc headers
    try:
        from ..shared.constants import PAIRED_DOCS
    except ImportError:
        from development_tools.shared.constants import PAIRED_DOCS

    # Build set of paired doc filenames (both human and AI versions)
    paired_doc_files = set()
    for human_doc, ai_doc in PAIRED_DOCS.items():
        paired_doc_files.add(human_doc)
        paired_doc_files.add(ai_doc)

    section_files: Dict[str, List[str]] = defaultdict(list)
    section_content: Dict[str, Dict[str, str]] = defaultdict(
        dict
    )  # section -> file -> content

    # Common section names that are expected to appear in multiple files (not problematic)
    expected_overlaps = {
        "purpose",
        "overview",
        "introduction",
        "summary",
        "quick start",
        "quick reference",
        "table of contents",
        "contents",
        "navigation",
        "see also",
        "references",
    }

    for filename, content in docs.items():
        sections = extract_sections(content)
        for section_name, section_content_text in sections.items():
            section_files[section_name].append(filename)
            section_content[section_name][filename] = section_content_text

    # Filter overlaps: exclude expected/common overlaps and focus on substantial content
    overlaps = {}
    for section, files in section_files.items():
        if len(files) > 1:
            # Skip if it's an expected/common overlap
            section_lower = section.lower().strip()
            if section_lower in expected_overlaps:
                continue

            # Skip if all files with this section are paired docs (paired docs are required to have matching headers)
            if all(f in paired_doc_files for f in files):
                continue

            # Only include if at least one file has substantial content (more than 50 chars)
            has_substantial_content = any(
                len(section_content[section].get(f, "")) > 50 for f in files
            )
            if has_substantial_content:
                overlaps[section] = files

    return overlaps


def analyze_file_purposes(docs: Dict[str, str]) -> Dict[str, Dict[str, object]]:
    """Analyze the purpose and content of each documentation file."""
    purposes = {}

    for filename, content in docs.items():
        # Extract first few lines to understand purpose
        lines = content.split("\n")[:20]
        header_info = "\n".join(lines)

        # Count sections
        sections = extract_sections(content)

        # Estimate content length
        content_length = len(content)

        purposes[filename] = {
            "header_info": header_info[:200],  # Limit header preview
            "section_count": len(sections),
            "content_length": content_length,
            "sections": list(sections.keys())[:10],  # Limit section list
        }

    return purposes


def generate_consolidation_recommendations(
    docs: Dict[str, str],
) -> List[Dict[str, object]]:
    """Generate recommendations for consolidating documentation files.

    Enhanced to provide more actionable insights:
    - Analyzes content similarity, not just filename keywords
    - Identifies files with high overlap percentage
    - Provides specific consolidation strategies
    - Considers file purposes and audiences
    """
    recommendations = []

    # Analyze file purposes more deeply
    file_purposes = analyze_file_purposes(docs)

    # Group files by purpose keywords (enhanced)
    setup_files = [
        f
        for f in docs.keys()
        if any(
            kw in f.lower()
            for kw in ["setup", "run", "install", "how_to", "getting_started"]
        )
    ]
    if len(setup_files) > 1:
        # Check if files have similar content
        similar_content = _check_content_similarity(docs, setup_files)
        recommendations.append(
            {
                "category": "Setup/Installation",
                "files": setup_files,
                "suggestion": "Consider consolidating into a single SETUP.md or HOW_TO_RUN.md",
                "similarity_score": similar_content,
                "priority": "high" if similar_content > 0.3 else "medium",
            }
        )

    workflow_files = [
        f
        for f in docs.keys()
        if any(
            kw in f.lower() for kw in ["workflow", "development", "guideline", "guide"]
        )
    ]
    if len(workflow_files) > 1:
        similar_content = _check_content_similarity(docs, workflow_files)
        recommendations.append(
            {
                "category": "Development Workflow",
                "files": workflow_files,
                "suggestion": "Consider consolidating into a single DEVELOPMENT_WORKFLOW.md",
                "similarity_score": similar_content,
                "priority": "high" if similar_content > 0.3 else "medium",
            }
        )

    testing_files = [
        f for f in docs.keys() if "test" in f.lower() and "test_" not in f.lower()
    ]
    if len(testing_files) > 1:
        similar_content = _check_content_similarity(docs, testing_files)
        recommendations.append(
            {
                "category": "Testing",
                "files": testing_files,
                "suggestion": "Consider consolidating testing documentation into a single TESTING_GUIDE.md",
                "similarity_score": similar_content,
                "priority": "high" if similar_content > 0.3 else "medium",
            }
        )

    # Check for files with high section overlap
    section_overlaps = detect_section_overlaps(docs)
    high_overlap_files = _identify_high_overlap_files(docs, section_overlaps)
    for file_group in high_overlap_files:
        if len(file_group["files"]) > 1:
            recommendations.append(
                {
                    "category": "High Section Overlap",
                    "files": file_group["files"],
                    "suggestion": f"These files share {file_group['overlap_count']} sections - consider consolidating or clearly differentiating their purposes",
                    "overlap_count": file_group["overlap_count"],
                    "priority": "high" if file_group["overlap_count"] > 5 else "medium",
                }
            )

    return recommendations


def _check_content_similarity(docs: Dict[str, str], file_list: List[str]) -> float:
    """Check content similarity between files (simple word-based similarity)."""
    if len(file_list) < 2:
        return 0.0

    # Extract words from each file
    file_words = {}
    for filename in file_list:
        content = docs.get(filename, "")
        # Simple word extraction (normalize and split)
        words = set(re.findall(r"\b\w+\b", content.lower()))
        file_words[filename] = words

    # Calculate average similarity between all pairs
    similarities = []
    files = list(file_list)
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            words1 = file_words.get(files[i], set())
            words2 = file_words.get(files[j], set())
            if words1 or words2:
                # Jaccard similarity
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)

    return sum(similarities) / len(similarities) if similarities else 0.0


def _identify_high_overlap_files(
    docs: Dict[str, str], section_overlaps: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """Identify groups of files with high section overlap."""
    # Count overlaps per file pair
    file_pair_overlaps = defaultdict(int)
    for section, files in section_overlaps.items():
        # Count overlaps for each pair of files
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pair = tuple(sorted([files[i], files[j]]))
                file_pair_overlaps[pair] += 1

    # Group files with high overlap
    file_groups = defaultdict(set)
    for (file1, file2), count in file_pair_overlaps.items():
        if count >= 3:  # Threshold: 3+ shared sections
            # Try to find existing group or create new
            found_group = False
            for group_key, group_files in file_groups.items():
                if file1 in group_files or file2 in group_files:
                    file_groups[group_key].add(file1)
                    file_groups[group_key].add(file2)
                    found_group = True
                    break
            if not found_group:
                group_key = f"{file1}_{file2}"
                file_groups[group_key] = {file1, file2}

    # Convert to list format
    result = []
    for group_files in file_groups.values():
        if len(group_files) > 1:
            # Count total overlaps for this group
            overlap_count = sum(
                1
                for section, files in section_overlaps.items()
                if len(set(files) & group_files) > 1
            )
            result.append(
                {"files": sorted(list(group_files)), "overlap_count": overlap_count}
            )

    return result


def format_summary(
    docs: Dict[str, str],
    missing: List[str],
    duplicates: List[Dict[str, Any]],
    placeholders: List[Dict[str, Any]],
    artifacts: List[Dict[str, Any]],
    include_overlap: bool = False,
) -> str:
    blocks: List[str] = []
    blocks.append(
        summary_block("Files Analysed", [f"{len(docs)} files", *sorted(docs.keys())])
    )
    if missing:
        blocks.append(summary_block("Missing Files", sorted(missing)))
    topics = analyse_topics(docs)
    if topics:
        topic_lines = []
        for label, files in sorted(topics.items()):
            topic_lines.append(f"{label} ({len(files)} files)")
            topic_lines.extend(f"  - {file}" for file in sorted(files))
        blocks.append(summary_block("Common Topics", topic_lines))
    profiles = document_profiles(docs)
    if profiles:
        blocks.append(summary_block("Document Profiles", profiles))
    if duplicates:
        dup_lines = [
            f"{item['section']} -> {item['human_file']} <-> {item['ai_file']} ({item['content_length']} chars)"
            for item in duplicates
        ]
        blocks.append(summary_block("Verbatim Duplicates", dup_lines))
    if placeholders:
        placeholder_lines = [
            f"{entry['file']}: {', '.join(entry['matches'])}" for entry in placeholders
        ]
        blocks.append(summary_block("Placeholder Content", placeholder_lines))
    if artifacts:
        artifact_lines = [
            f"{entry['file']}:{entry['line']} [{entry['pattern']}] {entry['snippet'][:120]}"
            for entry in artifacts
        ]
        blocks.append(summary_block("Corrupted Artifacts", artifact_lines))

    # Overlap analysis (if requested)
    if include_overlap:
        section_overlaps = detect_section_overlaps(docs)
        if section_overlaps:
            overlap_lines = []
            for section, files in sorted(section_overlaps.items()):
                overlap_lines.append(
                    f"{section} appears in: {', '.join(sorted(files))}"
                )
            blocks.append(summary_block("Section Overlaps", overlap_lines))

        consolidation_recs = generate_consolidation_recommendations(docs)
        if consolidation_recs:
            rec_lines = []
            for rec in consolidation_recs:
                rec_lines.append(f"{rec['category']} ({len(rec['files'])} files):")
                rec_lines.extend(f"  - {file}" for file in sorted(rec["files"]))
                rec_lines.append(f"  → {rec['suggestion']}")
            blocks.append(summary_block("Consolidation Recommendations", rec_lines))

    return "\n".join(blocks)


def execute(
    args: argparse.Namespace,
    project_root: Optional[Path] = None,
    config_path: Optional[str] = None,
):
    """Execute documentation analysis with optional project_root and config_path."""
    # Load config if path provided
    if config_path:
        config.load_external_config(config_path)
        # Reload config after loading external config
        global DOC_ANALYSIS_CONFIG, PLACEHOLDER_PATTERNS
        DOC_ANALYSIS_CONFIG = config.get_documentation_analysis_config()
        PLACEHOLDER_PATTERNS = _build_placeholder_patterns()

    # Use provided project_root or default
    if project_root:
        global PATHS
        PATHS = ProjectPaths(root=project_root)

    targets = args.files or DEFAULT_DOCS
    docs, missing = load_documents(targets)
    duplicates = detect_duplicates(docs)
    placeholders = detect_placeholders(docs)
    artifacts = detect_corrupted_artifacts(docs)

    # Overlap analysis (if requested via --overlap flag)
    include_overlap = getattr(args, "overlap", False)
    summary = format_summary(
        docs,
        missing,
        duplicates,
        placeholders,
        artifacts,
        include_overlap=include_overlap,
    )

    # Calculate total issues
    total_issues = len(missing) + len(duplicates) + len(placeholders) + len(artifacts)

    # Build details dict
    details = {
        "documents": sorted(docs.keys()),
        "missing": sorted(missing),
        "duplicates": duplicates,
        "placeholders": placeholders,
        "artifacts": artifacts,
    }

    # Add overlap data to details if requested (always include keys, even if empty, to indicate analysis ran)
    if include_overlap:
        section_overlaps = detect_section_overlaps(docs)
        consolidation_recs = generate_consolidation_recommendations(docs)
        file_purposes = analyze_file_purposes(docs)
        details["section_overlaps"] = section_overlaps if section_overlaps else {}
        details["consolidation_recommendations"] = (
            consolidation_recs if consolidation_recs else []
        )
        details["file_purposes"] = file_purposes if file_purposes else {}

    # Return standard format
    payload = {
        "summary": {
            "total_issues": total_issues,
            "files_affected": 0,  # Not file-based
        },
        "details": details,
    }

    exit_code = 0
    if duplicates or placeholders or artifacts:
        exit_code = 1
    return exit_code, ensure_ascii(summary), payload


def main() -> int:
    argument_spec = [
        (
            ("--files",),
            {
                "nargs": "+",
                "metavar": "REL_PATH",
                "help": "Specific documentation files to analyze (relative to project root).",
            },
        ),
        (
            ("--overlap",),
            {
                "action": "store_true",
                "help": "Include overlap analysis (section overlaps and consolidation recommendations).",
            },
        ),
    ]
    return run_cli(
        execute,
        description="Analyze documentation overlap and quality.",
        arguments=argument_spec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
