# ai/fallback_responses/conversational.py

"""Keyword-based conversational fallback (no check-in analytics).

MAINTENANCE: This module is intentionally a small keyword cascade for when LM
Studio is unavailable. Do not add check-in analytics or new data-aware paths here
(use checkin_summary.py / personalized.py / coordinator.py). Avoid growing the
keyword lists; prefer new FallbackCategory handlers in coordinator.py instead.
"""

from ai.fallback.categories import FallbackCategory
from core.error_handling import handle_errors

CONTEXT_REQUIRING_PROMPTS = [
    "how am i",
    "how are you",
    "how am i doing",
    "how have i been",
    "doing lately",
    "progress",
    "my mood",
    "my energy",
    "my check-ins",
    "check-in data",
    "how many times",
    "how often",
    "my habits",
    "my patterns",
    "my trends",
]

TECHNICAL_KEYWORDS = [
    "connection",
    "connection error",
    "network",
    "api error",
    "timeout",
]


@handle_errors("building technical-unavailable fallback", default_return=None)
def try_technical_unavailable(
    prompt_lower: str, name_prefix: str
) -> tuple[str, FallbackCategory] | None:
    if any(word in prompt_lower for word in TECHNICAL_KEYWORDS):
        return (
            f"{name_prefix}I'm having some technical difficulties right now. "
            f"Could you please try again in a moment? If the issue persists, "
            f"we can troubleshoot together. What were you trying to do?",
            FallbackCategory.TECHNICAL_UNAVAILABLE,
        )
    return None


@handle_errors("building new-user fallback", default_return=None)
def try_new_user_no_context(
    prompt_lower: str, name_prefix: str, is_new_user: bool
) -> tuple[str, FallbackCategory] | None:
    if any(phrase in prompt_lower for phrase in CONTEXT_REQUIRING_PROMPTS) and is_new_user:
        return (
            f"{name_prefix}I don't have enough information about how you're doing today, but we can figure it out together! "
            f"How about you tell me about your day so far? How are you feeling right now? "
            f"Once you start using check-ins, I'll be able to give you more specific insights!",
            FallbackCategory.NEW_USER_NO_CONTEXT,
        )
    return None


@handle_errors("building conversational support fallback", default_return=None)
def try_conversational_support(
    prompt_lower: str, name_prefix: str, user_name: str
) -> tuple[str, FallbackCategory] | None:
    """Keyword-based general support (no check-in calculations)."""
    work_fatigue_keywords = [
        "off work",
        "don't feel like",
        "tired",
        "exhausted",
        "no energy",
        "can't motivate",
        "don't want to",
    ]
    if any(keyword in prompt_lower for keyword in work_fatigue_keywords):
        return (
            f"{name_prefix}I understand you're feeling unmotivated. "
            f"That's a common experience, especially after work. "
            f"What small thing might help you feel a bit better?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    mood_keywords = [
        "depressed",
        "anxious",
        "sad",
        "worried",
        "stressed",
        "overwhelmed",
        "down",
        "hopeless",
    ]
    if any(keyword in prompt_lower for keyword in mood_keywords):
        return (
            f"{name_prefix}It sounds like you're going through a difficult time. "
            f"Remember that your feelings are valid, and it's okay to not be okay. "
            f"What small thing could help you feel a bit better right now? "
            f"Sometimes just taking one tiny step is enough.",
            FallbackCategory.GENERAL_SUPPORT,
        )

    health_keywords = ["sleep", "exercise", "diet", "energy", "tired", "nutrition"]
    if any(keyword in prompt_lower for keyword in health_keywords):
        return (
            f"{name_prefix}Taking care of your physical health is so important for overall wellbeing. "
            f"Small, consistent changes often make the biggest difference. What aspect of your health "
            f"would you like to focus on improving?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    focus_keywords = [
        "focus",
        "concentrate",
        "distracted",
        "procrastinate",
        "forget",
        "remember",
        "task",
        "overwhelm",
    ]
    if any(keyword in prompt_lower for keyword in focus_keywords):
        return (
            f"{name_prefix}Tasks can feel overwhelming when focus is challenging. "
            f"Try breaking things into tiny steps - even 5 minutes of progress counts. "
            f"What's one small thing you could do right now?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    goal_keywords = [
        "motivation",
        "goal",
        "habit",
        "change",
        "improve",
        "better",
        "start",
        "begin",
    ]
    if any(keyword in prompt_lower for keyword in goal_keywords):
        return (
            f"{name_prefix}It's wonderful that you're thinking about positive changes! "
            f"Big goals can feel overwhelming. Try starting with something tiny - "
            f"even 2 minutes of progress is real progress. What's one small step you could take today?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    social_keywords = [
        "lonely",
        "friends",
        "family",
        "relationship",
        "social",
        "isolated",
    ]
    if any(keyword in prompt_lower for keyword in social_keywords):
        return (
            f"{name_prefix}Connections with others are such an important part of wellbeing. "
            f"Even small social interactions can make a meaningful difference. "
            f"Is there someone you could reach out to today?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    greeting_keywords = [
        "hello",
        "hi",
        "hey",
        "how are you",
        "good morning",
        "good evening",
    ]
    if any(keyword in prompt_lower for keyword in greeting_keywords):
        return (
            f"Hello{', ' + user_name if user_name else ''}! I'm here to offer support and encouragement. "
            f"How are you doing today? What's on your mind?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    thanks_keywords = ["thank", "appreciate", "grateful", "helpful"]
    if any(keyword in prompt_lower for keyword in thanks_keywords):
        return (
            f"{name_prefix}You're very welcome! I'm glad I could help. "
            f"Remember that seeking support and taking care of yourself shows real strength. "
            f"Keep up the great work!",
            FallbackCategory.GENERAL_SUPPORT,
        )

    distress_keywords = [
        "breakdown",
        "overwhelmed",
        "struggling",
        "difficult",
        "hard",
        "tough",
        "stress",
        "anxiety",
        "depression",
        "sad",
        "upset",
        "worried",
        "scared",
        "frustrated",
        "angry",
    ]
    if any(keyword in prompt_lower for keyword in distress_keywords):
        return (
            f"{name_prefix}I can hear that you're going through a really tough time right now. "
            f"I'm here with you, and it's okay to feel overwhelmed. "
            f"Would you like to talk about what's happening, or would it help to focus on just getting through the next few minutes?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    support_keywords = [
        "help",
        "support",
        "listen",
        "talk",
        "feel",
        "emotion",
        "mood",
        "crisis",
    ]
    if any(keyword in prompt_lower for keyword in support_keywords):
        return (
            f"{name_prefix}I'm here to listen and support you through whatever you're experiencing. "
            f"You don't have to face this alone. What would be most helpful right now?",
            FallbackCategory.GENERAL_SUPPORT,
        )

    return None


@handle_errors(
    "building default contextual fallback",
    default_return=(
        "I'm here to listen and support you. How are you feeling right now?",
        FallbackCategory.GENERAL_SUPPORT,
    ),
)
def default_contextual_response(
    name_prefix: str, is_new_user: bool
) -> tuple[str, FallbackCategory]:
    """Last-resort supportive fallback when no keyword or check-in path matched."""
    if is_new_user:
        return (
            f"{name_prefix}I'm here to listen and support you! "
            f"Since we're just getting started, I'd love to learn more about you. "
            f"How are you feeling right now? What's on your mind? "
            f"Tell me a bit about how your day is going, and I'll do my best to help!",
            FallbackCategory.NEW_USER_NO_CONTEXT,
        )
    return (
        f"{name_prefix}I'm here to listen and support you. "
        f"How are you feeling right now? What's on your mind?",
        FallbackCategory.GENERAL_SUPPORT,
    )
