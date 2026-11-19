"""International phone normalization shared by SMS adapters and delivery."""

import re

# error_handling_exclude: pure type-checked normalization; no I/O or mutation.
def normalize_phone(value: str) -> str | None:
    """Accept an international number with optional display punctuation."""
    if not isinstance(value, str):
        return None
    number = re.sub(r"[\s().-]", "", value)
    return number if re.fullmatch(r"\+[1-9][0-9]{7,14}", number) else None

