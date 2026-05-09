"""Linkify repo-relative paths in AI_PRIORITIES review bullets (extracted from ReportGenerationMixin)."""

from __future__ import annotations

import re
from pathlib import Path

_REVIEW_PATH_LINK = re.compile(
    r"^((?:development_docs|development_tools|ai_development_docs)/[\w./-]+\.(?:md|json))(\s*\(.*)?$"
)


def _href_from_dev_tools_report(path: str) -> str:
    """Return an href relative to generated ``development_tools/*.md`` reports."""
    normalized = path.replace("\\", "/")
    if normalized.startswith("development_tools/"):
        return normalized.removeprefix("development_tools/")
    return f"../{normalized}"


def linkify_review_paths_bullet(text: str) -> str:
    """Turn repo-relative paths in Review for guidance/details lines into markdown links."""
    stripped = text.strip()
    lower = stripped.lower()
    if not (
        lower.startswith("review for guidance:")
        or lower.startswith("review for details:")
    ):
        return text
    colon = stripped.find(":")
    prefix, body = stripped[: colon + 1], stripped[colon + 1 :].strip()
    parts = re.split(r"(\s*,\s*|\s+and\s+)", body)
    out: list[str] = []
    for part in parts:
        if part and re.fullmatch(r"\s*,\s*|\s+and\s+", part, flags=re.IGNORECASE):
            out.append(part)
            continue
        chunk = (part or "").strip()
        m = _REVIEW_PATH_LINK.match(chunk)
        if m:
            path, suffix = m.group(1), m.group(2) or ""
            label = Path(path).name
            href = _href_from_dev_tools_report(path)
            out.append(f"[{label}]({href}){suffix}")
        else:
            out.append(part)
    return f"{prefix} {''.join(out)}".rstrip()
