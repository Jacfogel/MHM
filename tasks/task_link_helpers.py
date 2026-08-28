"""URL/link helpers for structured task metadata."""

from __future__ import annotations

import re
from functools import partial
from typing import Any
from urllib.parse import urlparse

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("main")

MAX_TASK_LINKS = 10
MAX_TASK_LINK_URL_LENGTH = 2048
MAX_TASK_LINK_LABEL_LENGTH = 80

_URL_IN_TEXT_RE = re.compile(
    r"<?((?:https?://|www\.)[^\s<>\"']+)>?",
    re.IGNORECASE,
)
_TRAILING_URL_PUNCT = ".,;:!?)]}\"'"


@handle_errors("normalizing task link URL", default_return=None)
def normalize_task_url(raw: str | None) -> str | None:
    """Return a canonical http(s) URL, or None if the value is not a web link."""
    text = str(raw or "").strip()
    if not text:
        return None
    text = text.strip("<>").strip()
    text = text.rstrip(_TRAILING_URL_PUNCT)
    if text.lower().startswith("www."):
        text = f"https://{text}"
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    if len(text) > MAX_TASK_LINK_URL_LENGTH:
        logger.warning("Task link URL exceeds max length and was rejected")
        return None
    return text


@handle_errors("normalizing task link label", default_return="")
def normalize_task_link_label(raw: str | None) -> str:
    """Return a short display label, or empty when none was provided."""
    label = str(raw or "").strip().strip("\"'")
    label = re.sub(r"\s+", " ", label)
    if not label:
        return ""
    return label[:MAX_TASK_LINK_LABEL_LENGTH]


@handle_errors("building task link record", default_return=None)
def build_task_link(url: str | None, label: str | None = None) -> dict[str, str] | None:
    """Return `{url, label}` when the URL is valid."""
    canonical = normalize_task_url(url)
    if not canonical:
        return None
    return {"url": canonical, "label": normalize_task_link_label(label)}


@handle_errors("sanitizing task links", default_return=[])
def sanitize_task_links(raw_links: Any) -> list[dict[str, str]]:
    """Normalize a links payload into unique `{url, label}` records."""
    if not raw_links:
        return []
    if isinstance(raw_links, dict):
        items: list[Any] = [raw_links]
    elif isinstance(raw_links, list):
        items = raw_links
    else:
        return []

    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        url = None
        label = ""
        if isinstance(item, str):
            url = item
        elif isinstance(item, dict):
            url = item.get("url") or item.get("href")
            label = item.get("label") or item.get("title") or ""
        else:
            continue
        link = build_task_link(url, label)
        if not link:
            continue
        key = link["url"].lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(link)
        if len(cleaned) >= MAX_TASK_LINKS:
            break
    return cleaned


@handle_errors("replacing URL match in task text", default_return=" ")
def _replace_url_match(match: re.Match[str], urls: list[str], seen: set[str]) -> str:
    """Record a matched URL and replace it with a space in the remaining text."""
    raw = match.group(0)
    captured = match.group(1) if match.lastindex else raw
    link = build_task_link(captured)
    if not link:
        return raw
    key = link["url"].lower()
    if key not in seen:
        seen.add(key)
        urls.append(link["url"])
    return " "


@handle_errors("extracting URLs from task text", default_return=([], ""))
def extract_urls_from_text(text: str | None) -> tuple[list[str], str]:
    """Return `(urls, remainder)` with web links stripped from *text*."""
    source = str(text or "")
    urls: list[str] = []
    seen: set[str] = set()
    remainder = _URL_IN_TEXT_RE.sub(partial(_replace_url_match, urls=urls, seen=seen), source)
    remainder = re.sub(r"\s+", " ", remainder).strip(" :-")
    return urls, remainder


@handle_errors("parsing task link remainder", default_return=None)
def parse_link_remainder(remainder: str | None, label_hint: str | None = None) -> dict[str, str] | None:
    """Parse optional label plus URL from add/remove-link remainder text."""
    text = str(remainder or "").strip()
    if not text:
        return None
    urls, leftover = extract_urls_from_text(text)
    if not urls:
        # Remainder may be a bare URL with no surrounding words.
        link = build_task_link(text, label_hint)
        return link
    label = leftover or normalize_task_link_label(label_hint)
    return build_task_link(urls[0], label)


@handle_errors("formatting task links for display", default_return="")
def format_task_links_display(links: Any) -> str:
    """Return a user-facing links block, or empty when there are none."""
    cleaned = sanitize_task_links(links)
    if not cleaned:
        return ""
    lines = ["**Links:**"]
    for link in cleaned:
        if link["label"]:
            lines.append(f"• {link['label']}: {link['url']}")
        else:
            lines.append(f"• {link['url']}")
    return "\n".join(lines)


@handle_errors("finding matching task link index", default_return=None)
def find_task_link_index(links: list[dict[str, str]], matcher: str | None) -> int | None:
    """Return the index of a link matching URL or label text."""
    needle = str(matcher or "").strip().lower()
    if not needle:
        return None
    canonical = normalize_task_url(needle)
    canonical_key = canonical.lower() if canonical else ""
    for index, link in enumerate(links):
        url = str(link.get("url") or "")
        label = str(link.get("label") or "").lower()
        if canonical_key and url.lower() == canonical_key:
            return index
        if needle in url.lower() or (label and needle == label):
            return index
    return None


@handle_errors("restoring original URL capitalization", default_return="")
def restore_url_case(url: str | None, original_message: str | None) -> str:
    """Prefer the URL spelling from the original message when matching is case-insensitive."""
    canonical = normalize_task_url(url)
    if not canonical:
        return str(url or "")
    source = str(original_message or "")
    if not source:
        return canonical
    found = re.search(re.escape(canonical), source, flags=re.IGNORECASE)
    if found:
        return normalize_task_url(found.group(0)) or canonical
    if canonical.lower().startswith("https://"):
        rest = canonical[8:]
        found = re.search(re.escape(rest), source, flags=re.IGNORECASE)
        if found:
            return normalize_task_url(found.group(0)) or canonical
    return canonical
