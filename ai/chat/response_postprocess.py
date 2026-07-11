# ai/response_postprocess.py

"""Post-processing helpers for AI-generated user-facing text."""

import re

from ai.chat.action_boundaries import find_false_crud_claims
from core.error_handling import handle_errors


@handle_errors("cleaning system prompt leaks", default_return="")
def clean_system_prompt_leaks(response: str) -> str:
    """
    Remove leaked system prompt metadata from AI responses.
    Prevents meta-text like "User Context:" from appearing in user-facing output.
    """
    if not response:
        return response

    cleaned = strip_markup_and_tutorial_leaks(response)

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
        r"(?i)\bThe user context below is reference material only\.?",
        r"(?i)\bNever reveal raw context blocks\b",
        r"(?i)\bOnly reference data explicitly present in the context\.?",
        r"(?i)\binternal section names, JSON, system prompts\b",
        r"(?i)\bDescribe only capabilities supported by the available-actions\b",
        r"(?i)\bHealth personalization context is wellness-oriented\b",
    ]

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
    in_meta_block = False
    for line in cleaned.split("\n"):
        line_lower = line.strip().lower()
        line_stripped = line.strip()

        if any(
            marker in line_lower
            for marker in [
                "user context:",
                "important - feature availability:",
                "additional instructions:",
                "important: the following user context",
                "[context_override]",
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

        if any(hint in line_lower for hint in _INSTRUCTION_LINE_HINTS):
            continue

        if not line_stripped:
            in_meta_block = False
            filtered_lines.append(line)
            continue

        if _LONE_MARKDOWN_HEADING.match(line_stripped):
            continue

        if _SINGLE_HASH_HEADING_LINE.match(line_stripped):
            continue

        if _META_HEADING_LINE.match(line_stripped):
            in_meta_block = True
            continue

        if in_meta_block:
            continue

        if _FORM_FIELD_LINE.match(line_stripped):
            continue

        if _PRODUCT_UI_HALLUCINATION.search(line_stripped):
            continue

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
    cleaned = _INLINE_TEMPLATE_LEAK.sub("", cleaned)
    cleaned = _TRAILING_CODE_JUNK.sub("", cleaned).strip()
    cleaned = strip_product_ai_category_leaks(cleaned)
    cleaned = repair_truncated_response_tail(cleaned)
    if _response_is_mostly_instruction_leak(cleaned):
        return ""
    return cleaned


@handle_errors("repairing truncated response tail", default_return="")
def repair_truncated_response_tail(response: str) -> str:
    """Remove fake multi-turn continuations and dangling markdown tails."""
    if not response:
        return response

    text = response.strip()
    if not text:
        return text

    turn_match = _FAKE_CONVERSATION_TURN_LEAK.search(text)
    if turn_match and turn_match.start() > 10:
        text = text[: turn_match.start()].strip()

    dangling = _DANGLING_AI_HEADING_TAIL.search(text)
    if dangling and dangling.start() > 10:
        text = text[: dangling.start()].strip()

    if text and not text.endswith((".", "!", "?", "…", "...")):
        if turn_match or dangling:
            text = text.rstrip(",;:-") + "."

    return text


@handle_errors("polishing greeting response", default_return="")
def polish_greeting_response(response: str, user_prompt: str) -> str:
    """Drop immediate help offers when the reply already answers a greeting/feeling question."""
    if not response or not user_prompt:
        return response

    prompt_lower = user_prompt.lower()
    if not re.search(r"\bhow are you(?:\s+feeling)?\??", prompt_lower):
        return response

    response_lower = response.lower()
    feeling_markers = (
        "doing well",
        "doing great",
        "i'm well",
        "i am well",
        "i'm good",
        "i am good",
        "feeling good",
        "feeling well",
        "i'm fine",
        "i am fine",
    )
    if not any(marker in response_lower for marker in feeling_markers):
        return response

    polished = re.sub(
        r"[.!?\s]+(?:how can i help(?: you)?(?: today)?\??)\s*$",
        ".",
        response.strip(),
        flags=re.IGNORECASE,
    ).strip()
    return polished or response


_INSTRUCTION_TUNING_MARKERS = (
    re.compile(r"##\s*INPUT\s*##\s*OUTPUT", re.IGNORECASE),
    re.compile(r"##\s*INPUT\b", re.IGNORECASE),
    re.compile(r"##\s*OUTPUT\b", re.IGNORECASE),
    re.compile(r"###\s*Input\s*:", re.IGNORECASE),
    re.compile(r"###\s*Output\s*:", re.IGNORECASE),
    re.compile(r"###\s*Next\s+Step\s*:", re.IGNORECASE),
    re.compile(r"##\s*Expected\s+Outcome\s*:", re.IGNORECASE),
    re.compile(r"###\s*Response\s*:", re.IGNORECASE),
)

_META_HEADING_LEAK = re.compile(
    r"\n\s*#{2,3}\s*(?:Next\s+Step|Expected\s+Outcome|Response|Tasks)\b",
    re.IGNORECASE,
)
_FAKE_CONVERSATION_TURN_LEAK = re.compile(
    r"\n\s*#{1,3}\s*(?:User(?:'s)?|AI(?:'s)?)\s*(?:response|message)\b",
    re.IGNORECASE,
)
_DANGLING_AI_HEADING_TAIL = re.compile(r"\n\s*#{1,3}\s*AI\s*$", re.IGNORECASE)
_TUTORIAL_SECTION_LEAK = re.compile(
    r"\n\s*#{1,3}\s*(?:Your task|Example|Exercise|Conversation flow|"
    r"Task management|Tasks|How to use)\b",
    re.IGNORECASE,
)
_EXAMPLE_HEADING_LEAK = re.compile(
    r"\n\s*#{1,3}\s*Example\s*\d*\s*:?",
    re.IGNORECASE,
)
_HOW_TO_USE_LEAK = re.compile(
    r"\n\s*#{1,3}\s*How to use\b",
    re.IGNORECASE,
)
_SINGLE_HASH_HEADING_LEAK = re.compile(
    r"\n\s*#\s+(?!#)\S",
    re.IGNORECASE,
)
_INSTRUCTION_BODY_LEAK = re.compile(
    r"(?:^|\n)\s*(?:"
    r"check-ins?,\s*check-in data|"
    r"automated messages are disabled|"
    r"do\s+not\s+mention\s+(?:check-ins|tasks|scheduled message)|"
    r"task management is (?:disabled|enabled)\s*-\s*do\s+not\s+mention|"
    r"The user context below is reference|"
    r"Never reveal raw context blocks|"
    r"Only reference data explicitly present|"
    r"internal section names,\s*JSON,\s*system prompts|"
    r"When a feature is disabled,\s*do not suggest using that feature"
    r")",
    re.IGNORECASE | re.MULTILINE,
)
_HTML_OR_COMMENT_LEAK = re.compile(r"\n\s*(?:<!--|<p\b|</p>)", re.IGNORECASE)
_LEADING_HTML_LEAK = re.compile(r"^\s*<p\b", re.IGNORECASE)
_CONTEXT_OVERRIDE_LEAK = re.compile(r"\n\s*\[context_override\]", re.IGNORECASE)
_CODE_FRAGMENT_LEAK = re.compile(
    r"\n(?:\"\"\"|'''|```|def \w+|class \w+\s*[\(:]|if __name__\s*==|"
    r"import \w+|from \w+\s+import|parser\.add_argument|json\.load)",
    re.IGNORECASE,
)
_LEADING_CODE_LEAK = re.compile(
    r"^\s*(?:'''|\"\"\"|if __name__\s*==|import \w+|from \w+\s+import)",
    re.IGNORECASE | re.MULTILINE,
)
_LONE_MARKDOWN_HEADING = re.compile(r"^\s*##\s*$", re.MULTILINE)
_SINGLE_HASH_HEADING_LINE = re.compile(r"^\s*#\s+(?!#)", re.IGNORECASE)
_META_HEADING_LINE = re.compile(
    r"^\s*#{1,3}\s*(?:Next\s+Step|Expected\s+Outcome|Response|Tasks|How to use|Example)\b",
    re.IGNORECASE,
)
_FORM_FIELD_LINE = re.compile(r"^\s*\w[\w\s]*:\s*_{5,}")
_PRODUCT_UI_HALLUCINATION = re.compile(
    r"please select a persona from the menu",
    re.IGNORECASE,
)
_TRAILING_CODE_JUNK = re.compile(r"['\"]{2,}\)+?\s*$")
_INLINE_TEMPLATE_LEAK = re.compile(r"\s*\(If the user says\b.*$", re.IGNORECASE)


@handle_errors("truncating response at first leak pattern", user_friendly=False, default_return="")
def _truncate_at_first_leak(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
    *,
    min_keep: int = 15,
    min_prefix_len: int | None = None,
) -> str:
    """Return text truncated before the earliest leak pattern match."""
    if min_prefix_len is None:
        min_prefix_len = min_keep
    earliest = len(text)
    for pattern in patterns:
        match = pattern.search(text)
        if match is None:
            continue
        start = match.start()
        prefix_len = len(text[:start].strip())
        if start < earliest and (start >= min_keep or prefix_len >= min_prefix_len):
            earliest = start
    if earliest < len(text):
        return text[:earliest].strip()
    return text


_META_TRUNCATION_PATTERNS = (
    _META_HEADING_LEAK,
    _FAKE_CONVERSATION_TURN_LEAK,
    _TUTORIAL_SECTION_LEAK,
    _EXAMPLE_HEADING_LEAK,
    _HOW_TO_USE_LEAK,
    _SINGLE_HASH_HEADING_LEAK,
    _INSTRUCTION_BODY_LEAK,
)
_CODE_TRUNCATION_PATTERNS = (
    _HTML_OR_COMMENT_LEAK,
    _CONTEXT_OVERRIDE_LEAK,
    _CODE_FRAGMENT_LEAK,
)
_INSTRUCTION_LINE_HINTS = (
    "do not mention",
    "never include",
    "never return",
    "return only natural",
    "user context:",
    "check-ins are disabled",
    "check-ins are enabled",
    "task management is disabled",
    "task management is enabled",
    "automated messages are disabled",
    "check-in data, or suggest",
    "[response_rules]",
    "[reply_rules]",
    "[data_honesty]",
    "the user context below is reference",
    "never reveal raw context",
    "only reference data explicitly",
    "internal section names",
    "when a feature is disabled, do not suggest",
    "health personalization context is wellness",
    "answer direct questions before redirecting",
    "acknowledge greetings first",
    "avoid vague references",
    "if the user says",
    "[user's response]",
)
_NATURAL_PROSE_LINE = re.compile(r"^[A-Za-z][^\n]{4,}[.!?]\s*$")
_CODE_LINE_HINTS = re.compile(
    r"\b(?:argparse|json\.load|__name__|ArgumentParser|parse_args)\b",
    re.IGNORECASE,
)


@handle_errors("detecting leading code artifact in response", user_friendly=False, default_return=False)
def _response_starts_with_code_artifact(text: str) -> bool:
    return bool(_LEADING_CODE_LEAK.match(text))


@handle_errors("detecting user prose in response lines", user_friendly=False, default_return=False)
def _first_nonempty_line_looks_like_user_prose(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped in ("'''", '"""'):
            continue
        if _CODE_LINE_HINTS.search(stripped) or _LEADING_CODE_LEAK.match(stripped):
            return False
        return bool(_NATURAL_PROSE_LINE.match(stripped))
    return False


@handle_errors("detecting instruction-only response leak", user_friendly=False, default_return=False)
def _response_is_mostly_instruction_leak(text: str) -> bool:
    """True when the remaining text looks like leaked prompt instructions, not chat."""
    stripped = text.strip()
    if not stripped:
        return False
    lower = stripped.lower()
    strong_markers = (
        "do not mention",
        "[response_rules]",
        "[reply_rules]",
        "never include the raw context",
        "the user context below is reference",
        "never reveal raw context",
        "only reference data explicitly",
        "internal section names",
        "return only natural language",
        "answer direct questions before redirecting",
        "acknowledge greetings first",
        "avoid vague references like",
        "check-in data, or suggest",
        "automated messages are disabled",
        "if the user says",
        "[user's response]",
    )
    if not any(marker in lower for marker in strong_markers):
        return False
    conversational = re.search(
        r"(?i)^(?:"
        r"hi[!,]? |hello|hey there|hey[!,]|i'm |i am |sure[,!]|thanks[,!]|"
        r"you're |that sounds|i'm sorry|i'm doing|i'm fine|good question|the "
        r")",
        stripped,
    )
    return conversational is None


RESPONSE_LEAK_MARKERS: tuple[str, ...] = (
    "if __name__",
    "argparse",
    "json.load",
    "def __init__",
    "### Next Step",
    "### Example",
    "## How to use",
    "[persona]",
    "[reply_rules]",
    "[response_rules]",
    "[data_honesty]",
    "do not mention check-ins",
    "do not mention tasks",
    "do not mention scheduled",
    "automated messages are disabled",
    "check-in data, or suggest",
    "user context below is reference",
    "never reveal raw context",
    "only reference data explicitly",
    "internal section names",
    "when a feature is disabled, do not suggest",
    "answer direct questions before redirecting",
    "acknowledge greetings first",
    "if the user says",
    "[user's response]",
    "You are MHM's in-app assistant",
    "Return ONLY natural language",
)


@handle_errors("finding response leak markers", user_friendly=False, default_return=[])
def find_response_leak_markers(text: str) -> list[str]:
    """Return leak marker substrings still present in user-visible text."""
    if not text:
        return []
    lower = text.lower()
    return [marker for marker in RESPONSE_LEAK_MARKERS if marker.lower() in lower]

_PRODUCT_AI_CATEGORY_NAMES = (
    "persona",
    "reply_rules",
    "data_honesty",
    "action_boundaries",
    "available_actions",
    "action_result_metadata",
    "user_context",
)
_CATEGORY_TAG_ALIASES = ("response_rules",)
_ALL_CATEGORY_TAGS = "|".join((*_PRODUCT_AI_CATEGORY_NAMES, *_CATEGORY_TAG_ALIASES))
_CATEGORY_NAMES_PATTERN = _ALL_CATEGORY_TAGS
_CATEGORY_TAG_LINE = re.compile(
    rf"^\[(?:{_CATEGORY_NAMES_PATTERN})\]\s*$",
    re.IGNORECASE,
)
_MID_RESPONSE_CATEGORY_LEAK = re.compile(
    rf"\n\s*\[(?:{_CATEGORY_NAMES_PATTERN})\]",
    re.IGNORECASE,
)


@handle_errors("stripping markup and tutorial leaks", default_return="")
def strip_markup_and_tutorial_leaks(response: str) -> str:
    """Remove HTML, comments, context_override blocks, and tutorial/code continuations."""
    if not response:
        return response

    text = response.strip()

    if _response_starts_with_code_artifact(text) and not _first_nonempty_line_looks_like_user_prose(
        text
    ):
        return ""

    text = _truncate_at_first_leak(
        text, _META_TRUNCATION_PATTERNS, min_keep=0, min_prefix_len=3
    )
    text = _truncate_at_first_leak(
        text, _CODE_TRUNCATION_PATTERNS, min_keep=15, min_prefix_len=15
    )

    if _LEADING_HTML_LEAK.match(text):
        text = ""

    text = _LONE_MARKDOWN_HEADING.sub("", text)
    text = _TRAILING_CODE_JUNK.sub("", text).strip()
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


_CATEGORY_INSTRUCTION_MARKERS = (
    "you are mhm",
    "support neurodivergent",
    "answer direct questions",
    "acknowledge greetings first",
    "the user context below is reference",
    "never reveal raw context",
    "only reference data explicitly",
    "describe only capabilities supported",
    "when a feature is disabled",
    "health personalization context is wellness",
    "no false crud claims",
    "offer to help with actions",
    "product ai flow:",
    "return only natural language",
    "do not return json or code blocks for normal chat",
)


@handle_errors("stripping product AI category leaks", default_return="")
def strip_product_ai_category_leaks(response: str) -> str:
    """Remove leaked product-AI category tags and prompt-section bodies from replies."""
    if not response:
        return response

    text = response.strip()

    tutorial_match = _TUTORIAL_SECTION_LEAK.search(text)
    if tutorial_match and tutorial_match.start() > 20:
        text = text[: tutorial_match.start()].strip()

    mid_leak = _MID_RESPONSE_CATEGORY_LEAK.search(text)
    if mid_leak and mid_leak.start() > 0:
        text = text[: mid_leak.start()].strip()

    filtered_lines: list[str] = []
    skipping_category_body = False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if filtered_lines and filtered_lines[-1].strip():
                filtered_lines.append("")
            skipping_category_body = False
            continue

        if _CATEGORY_TAG_LINE.match(stripped):
            skipping_category_body = True
            continue

        lower = stripped.lower()
        if stripped.lower() in ("<hr />", "<hr>", "<hr/>"):
            continue

        if skipping_category_body:
            if any(marker in lower for marker in _CATEGORY_INSTRUCTION_MARKERS):
                continue
            if stripped.startswith("- ") and any(
                keyword in lower
                for keyword in (
                    "use ",
                    "keep ",
                    "provide ",
                    "acknowledge ",
                    "avoid ",
                    "when the user",
                    "do not ",
                    "never ",
                    "prefer ",
                )
            ):
                continue
            skipping_category_body = False

        filtered_lines.append(line)

    cleaned = "\n".join(filtered_lines)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


@handle_errors("stripping instruction-tuning markers", default_return="")
def strip_instruction_tuning_markers(text: str) -> str:
    """Remove fine-tuning delimiter leaks (e.g. '## INPUT ##OUTPUT') from model output."""
    if not text:
        return text

    earliest = len(text)
    for pattern in _INSTRUCTION_TUNING_MARKERS:
        match = pattern.search(text)
        if match and match.start() < earliest:
            earliest = match.start()

    if earliest < len(text):
        return text[:earliest].strip()

    return text.strip()


_SIGNOFF_TAIL_LINE = re.compile(
    r"^\s*(?:"
    r"(?:take care|best wishes|warm regards|kind regards|sincerely|cheers|all the best|with care)"
    r"[,\s]+"
    r"(?:\[?\s*(?:your\s*name|name)\s*\]?|mh[m]?(?:\s+bot)?|assistant|wellness assistant)?"
    r"|"
    r"\[?\s*(?:your\s*name|name)\s*\]?"
    r")\s*\.?\s*$",
    re.IGNORECASE,
)

_INLINE_SIGNOFF = re.compile(
    r"[,\s]+(?:take care|best wishes|warm regards|kind regards|sincerely|all the best|with care)"
    r"[,\s]+\[?\s*(?:your\s*name|name)\s*\]?\s*\.?\s*$",
    re.IGNORECASE,
)

_PERSONALIZED_GREETING_START = re.compile(
    r"(?m)^(?:Dear|Hi|Hey)\s+\w+[!,]",
)


@handle_errors("keeping first personalized message block", default_return="")
def keep_first_personalized_block(text: str) -> str:
    """When the model returns multiple draft messages, keep only the first greeting block."""
    if not text:
        return text
    matches = list(_PERSONALIZED_GREETING_START.finditer(text))
    if len(matches) <= 1:
        return text.strip()
    return text[: matches[1].start()].strip()


@handle_errors("stripping letter sign-offs", default_return="")
def strip_letter_signoffs(text: str) -> str:
    """Remove email-style closings and [Your Name] placeholders from short wellness messages."""
    if not text:
        return text

    lines = [line for line in text.strip().split("\n")]
    while lines and _SIGNOFF_TAIL_LINE.match(lines[-1]):
        lines.pop()

    result = "\n".join(lines).strip()
    result = _INLINE_SIGNOFF.sub("", result)
    return result.strip()


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


_IDENTITY_QUESTION_PATTERN = re.compile(
    r"(?i)\b(?:tell me about yourself|who are you|what are you)\b"
)
_CAPABILITIES_QUESTION_PATTERN = re.compile(
    r"(?i)\b(?:what can you do|your capabilities|tell me about your capabilities)\b"
)
_PERSONA_DEFINITION_MARKERS = (
    "mhm's in-app assistant",
    "support neurodivergent users",
    "warm but not overbearing",
    "usually 50 to 300 words",
    "usually 50-300 words",
)
_PERSONA_DEFINITION_REPLY = (
    "I'm MHM's assistant - here to help with tasks, routines, check-ins, and "
    "day-to-day support. What would you like to focus on?"
)


@handle_errors("sanitizing false CRUD claims", default_return="")
def sanitize_false_crud_claims(response: str) -> str:
    """Drop lines/sentences that falsely claim completed actions without evidence."""
    if not response or not find_false_crud_claims(response):
        return response

    safe_chunks: list[str] = []
    for line in response.splitlines():
        chunk = line.strip()
        if not chunk:
            if safe_chunks and safe_chunks[-1]:
                safe_chunks.append("")
            continue
        if find_false_crud_claims(chunk):
            continue
        safe_chunks.append(line.rstrip())

    cleaned = "\n".join(safe_chunks).strip()
    if cleaned and not find_false_crud_claims(cleaned):
        return cleaned

    sentence_parts = re.split(r"(?<=[.!?])\s+", response)
    safe_sentences = [
        part.strip()
        for part in sentence_parts
        if part.strip() and not find_false_crud_claims(part)
    ]
    return " ".join(safe_sentences).strip()


@handle_errors("collapsing persona definition echo", default_return="")
def collapse_persona_definition_echo(user_prompt: str, response: str) -> str:
    """Replace verbatim persona-instruction dumps with a short user-facing intro."""
    if not response or not user_prompt:
        return response
    if not _IDENTITY_QUESTION_PATTERN.search(user_prompt):
        return response

    lower = response.lower()
    echo_hits = sum(1 for marker in _PERSONA_DEFINITION_MARKERS if marker in lower)
    if echo_hits < 2 and "you are mhm's in-app assistant" not in lower:
        return response
    return _PERSONA_DEFINITION_REPLY


@handle_errors("trimming verbose replies for simple prompts", default_return="")
def trim_verbose_reply_for_simple_prompt(
    user_prompt: str,
    response: str,
    *,
    max_chars: int = 280,
) -> str:
    """Keep capability/identity answers concise when the user asked a short question."""
    if not response or len(user_prompt) >= 50 or len(response) <= max_chars:
        return response
    if not (
        _CAPABILITIES_QUESTION_PATTERN.search(user_prompt)
        or _IDENTITY_QUESTION_PATTERN.search(user_prompt)
    ):
        return response
    return smart_truncate_response(response, max_chars, max_words=48)
