"""Strip quoted history from an email reply so only the new text remains."""

from __future__ import annotations

import re

from core.error_handling import handle_errors

_REPLY_CUT_RE = re.compile(
    r"^(On .+ wrote:\s*|-----Original Message-----|_{5,}\s*|Begin forwarded message:)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_OUTLOOK_HEADER_RE = re.compile(
    r"(?im)^From: .+\n(?:.*\n){0,3}?Sent: .+",
)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"[ \t]+")
_BLANK_RE = re.compile(r"\n{3,}")


@handle_errors("converting HTML email to plain text", default_return="")
def html_to_plain_text(html_text: str) -> str:
    """Turn an HTML email part into plain text while keeping line breaks."""
    if not html_text:
        return ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", html_text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?i)</div>", "\n", text)
    text = re.sub(r"(?i)</tr>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = _TAG_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text)
    text = _BLANK_RE.sub("\n\n", text)
    return text.strip()


@handle_errors("stripping quoted email reply", default_return="")
def strip_quoted_reply(body: str) -> str:
    """Return the new reply text, without the quoted original or a standard signature."""
    if not body or not isinstance(body, str):
        return ""

    text = body.replace("\r\n", "\n").replace("\r", "\n")
    signature_at = text.find("\n-- \n")
    if signature_at != -1:
        text = text[:signature_at]
    elif text.startswith("-- \n"):
        return ""

    cut_at = None
    header_match = _REPLY_CUT_RE.search(text)
    if header_match:
        cut_at = header_match.start()
    outlook_match = _OUTLOOK_HEADER_RE.search(text)
    if outlook_match and (cut_at is None or outlook_match.start() < cut_at):
        cut_at = outlook_match.start()
    if cut_at is not None:
        text = text[:cut_at]

    kept_lines = [
        line for line in text.split("\n") if not line.strip().startswith(">")
    ]
    cleaned = "\n".join(kept_lines).strip()
    return _BLANK_RE.sub("\n\n", cleaned).strip()
