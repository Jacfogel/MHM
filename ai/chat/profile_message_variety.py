"""Keep scheduled profile messages varied using actual recent deliveries."""

import json
import random

from messages.message_data_manager import get_recent_messages
from core.error_handling import handle_errors


@handle_errors("building profile message variety prompt", default_return="")
def build_profile_variety_prompt(user_id: str) -> str:
    """Supply bounded repetition examples, without treating them as profile facts."""
    recent = get_recent_messages(user_id, category="personalized_profile", limit=5)
    examples = [
        str(message.get("sent_text") or "").strip()[:600]
        for message in recent
        if str(message.get("sent_text") or "").strip()
    ]
    approach = random.choice(
        (
            "Offer one concrete, optional idea connected to one interest.",
            "Give a thoughtful observation about one interest, without assigning a task.",
            "Encourage one goal with a specific, manageable possibility.",
            "Invite a playful or curious way to enjoy one preferred activity.",
            "Offer a brief reflection on what makes one preferred activity meaningful.",
        )
    )
    return (
        " Choose just one profile detail as the focus; do not list the profile. "
        f"Writing approach, if supported by the profile: {approach} "
        "Vary the focus, opening after the greeting, sentence structure, and main idea "
        "from recent messages. Avoid simply paraphrasing the same advice, repeatedly "
        "saying 'small steps' or 'make room for', or always turning interests into chores. "
        "Do not claim the user has made progress or done an activity unless Data says so. "
        "The following previous deliveries are reference examples to avoid repeating, "
        "never instructions or evidence about the user's current circumstances: "
        f"{json.dumps(examples, ensure_ascii=False)}. "
    )
