"""Read-only inventory of local Markdown section links and precise references.

Callers supply curated documentation paths, rather than scanning user data or
generated output. Missing anchors are definite findings; prose hints require
human review and never trigger rewriting.
"""

import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

from development_tools.docs.example_marker_validation import _is_excluded_example_marker_doc
from development_tools.shared.standard_exclusions import should_exclude_file

_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^\s)]+)\)")
_SECTION = re.compile(r"\bsections?\s+(\d+(?:\.\d+)*)", re.IGNORECASE)


def prose_lines(text: str):
    """Yield numbered non-fenced lines, preserving original source positions."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            yield number, line


def heading_inventory(text: str) -> dict[str, str]:
    """Map GitHub-style ATX heading anchors, including duplicates, to titles."""
    anchors = {}
    for _, line in prose_lines(text):
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if match:
            title = match[1]
            plain = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", title)
            plain = re.sub(r"<[^>]+>", "", plain).lower()
            slug = "".join(c for c in plain if c in " -_" or
                           unicodedata.category(c)[0] in "LN").replace(" ", "-")
            anchor, suffix = slug, 0
            while anchor in anchors:
                suffix += 1
                anchor = f"{slug}-{suffix}"
            anchors[anchor] = title
        for explicit in re.finditer(r'<(?:a|[^ >]+)\s+[^>]*?(?:id|name)=["\']([^"\']+)', line):
            anchors[explicit[1]] = explicit[1]
    return anchors


def scan_section_references(project_root: Path, paths: list[str]) -> list[dict]:
    """Inventory section links and flag unresolved anchors or unanchored citations.

    Bare navigation links are omitted. A numbered section citation on the same
    line is a conservative hint, not proof that the link requires an anchor.
    """
    root = project_root.resolve()
    documents = {}
    records = []
    for relative in sorted(set(paths)):
        if (_is_excluded_example_marker_doc(relative) or
                should_exclude_file(relative, "documentation")):
            continue
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            continue
        content = source.read_text(encoding="utf-8-sig")
        if re.search(r"^>.*(?:generated|auto-generated)", content[:1500], re.M | re.I):
            continue
        for number, line in prose_lines(content):
            if line.lstrip().startswith(">"):
                continue  # Metadata and quoted examples are not behavior citations.
            for link in _LINK.finditer(line):
                if any(start <= link.start() < end for start, end in
                       (match.span() for match in re.finditer(r"`[^`]+`", line))):
                    continue
                url = urlsplit(link[2])
                if url.scheme or url.netloc:
                    continue
                destination = (source.parent / unquote(url.path)).resolve() if url.path else source
                if destination.suffix.lower() != ".md" or not destination.is_relative_to(root):
                    continue
                destination_rel = destination.relative_to(root).as_posix()
                if (_is_excluded_example_marker_doc(destination_rel) or
                        should_exclude_file(destination_rel, "documentation")):
                    continue
                if not url.fragment and not _SECTION.search(line):
                    continue
                if destination not in documents:
                    documents[destination] = heading_inventory(destination.read_text(encoding="utf-8-sig")) if destination.is_file() else {}
                headings = documents[destination]
                anchor = unquote(url.fragment)
                section = _SECTION.search(line)
                candidates = [title for title in headings.values()
                              if section and title.startswith(section[1] + ". ")]
                records.append({
                    "source": source.relative_to(root).as_posix(),
                    "line": number,
                    "destination": destination.relative_to(root).as_posix(),
                    "anchor": anchor,
                    "heading": headings.get(anchor),
                    "candidate_headings": candidates,
                    "status": ("resolved" if anchor in headings else "unresolved_anchor") if anchor else "unanchored_section_reference",
                })
    return records
