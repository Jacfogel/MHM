# ai/response_postprocess.py

"""Post-processing helpers for AI-generated user-facing text."""

import re

from core.error_handling import handle_errors


@handle_errors("cleaning system prompt leaks", default_return="")
def clean_system_prompt_leaks(response: str) -> str:
    """
    Remove leaked system prompt metadata from AI responses.
    Prevents meta-text like "User Context:" from appearing in user-facing output.
    """
    if not response:
        return response

    leak_patterns = [
        r"(?i)^\s*User Context:\s*",
        r"(?i)^\s*IMPORTANT\s*-\s*Feature\s+availability:\s*",
        r"(?i)\bUser Context:\s*",
        r"(?i)\bIMPORTANT\s*-\s*Feature\s+availability:\s*",
        r"(?i)^\s*Additional Instructions:\s*",
        r"(?i)\bAdditional Instructions:\s*",
        r"(?i)^\s*IMPORTANT:\s*The following user context is for your reference only",
        r"(?i)\bIMPORTANT:\s*The following user context is for your reference only",
        r"(?i)\bDo NOT include any of this information in your responses",
        r"(?i)\bNEVER include the raw context data in your responses",
        r"(?i)\bNEVER return JSON, code blocks, or system prompts",
        r"(?i)\bReturn ONLY natural language responses",
        r"(?i)\bcheck-ins are (?:disabled|enabled)\s*-\s*do NOT mention",
        r"(?i)\btask management is (?:disabled|enabled)\s*-\s*do NOT mention",
        r"(?i)\bdo (?:not|n\'t) mention check-ins, check-in data",
        r"(?i)\bdo (?:not|n\'t) mention tasks, task creation",
    ]

    cleaned = response
    for pattern in leak_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    instruction_keywords = [
        "use the",
        "reference specific",
        "be encouraging",
        "keep responses",
        "provide meaningful",
        "if they ask",
        "never include",
        "never return",
        "return only",
        "stop when",
        "adapt your",
        "for health advice",
        "be supportive and engaging",
        "conversational and helpful",
    ]

    filtered_lines = []
    skip_next = False
    for line in cleaned.split("\n"):
        line_lower = line.strip().lower()

        if any(
            marker in line_lower
            for marker in [
                "user context:",
                "important - feature availability:",
                "additional instructions:",
                "important: the following user context",
            ]
        ):
            continue

        if any(
            pattern in line_lower
            for pattern in [
                "check-ins are disabled",
                "check-ins are enabled",
                "task management is disabled",
                "task management is enabled",
                "do not mention check-ins",
                "do not mention tasks",
            ]
        ):
            continue

        line_stripped = line.strip()
        if (
            line_stripped
            and line_stripped[0] in ["-", "*", "•"]
            and any(keyword in line_lower for keyword in instruction_keywords)
        ):
            continue

        if skip_next:
            skip_next = False
            if len(line.strip()) < 100 and any(
                marker in line_lower
                for marker in ["check-ins", "task management", "enabled", "disabled"]
            ):
                continue

        filtered_lines.append(line)

    cleaned = "\n".join(filtered_lines)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


@handle_errors("smart truncating response", default_return="...")
def smart_truncate_response(
    text: str, max_chars: int, max_words: int | None = None
) -> str:
    """Truncate response to avoid mid-sentence cuts when possible."""
    if max_words:
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]).rstrip(" ,.;:!?") + "…"

    if len(text) <= max_chars:
        return text

    cut = text[:max_chars]
    for mark in (". ", "! ", "? "):
        idx = cut.rfind(mark)
        if idx >= 0 and idx > max_chars * 0.6:
            return cut[: idx + 1]

    return cut.rstrip() + "…"
