# ai/fallback_responses.py

"""Fallback response generation when LM Studio or AI API calls are unavailable."""

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.response_tracking import get_recent_responses

logger = get_component_logger("ai")


class FallbackResponses:
    """Template and data-aware fallback text; does not call LM Studio."""

    @handle_errors(
        "getting contextual fallback",
        default_return="I'd like to help with that! How can I assist you today?",
    )
    def contextual(self, user_prompt: str, user_id: str | None = None) -> str:
        """
        Provide contextually aware fallback responses based on user data and prompt analysis.
        Analyzes user's check-in data when available for meaningful responses.
        """
        prompt_lower = user_prompt.lower()

        context_result = get_user_data(user_id, "context")
        user_context = context_result.get("context") if context_result else {}

        user_name = ""
        if user_id and user_context:
            user_name = user_context.get("preferred_name", "").strip()

        name_prefix = f"{user_name}, " if user_name else ""

        recent_data = None
        if user_id:
            recent_data = get_recent_responses(user_id, limit=10)

            if recent_data:
                breakfast_count = sum(
                    1 for entry in recent_data if entry.get("ate_breakfast") is True
                )
                total_entries = len(recent_data)
                breakfast_rate = (
                    (breakfast_count / total_entries) * 100 if total_entries > 0 else 0
                )

                moods = [
                    entry.get("mood")
                    for entry in recent_data
                    if entry.get("mood") is not None
                ]
                avg_mood = sum(moods) / len(moods) if moods else None

                energies = [
                    entry.get("energy")
                    for entry in recent_data
                    if entry.get("energy") is not None
                ]
                avg_energy = sum(energies) / len(energies) if energies else None

                if any(word in prompt_lower for word in ["breakfast", "eat", "ate"]):
                    if breakfast_rate >= 80:
                        return (
                            f"{name_prefix}Great news! You've been eating breakfast {breakfast_rate:.0f}% of the time in your recent check-ins. "
                            f"That's a really healthy habit to maintain!"
                        )
                    if breakfast_rate >= 50:
                        return (
                            f"{name_prefix}You've been eating breakfast {breakfast_rate:.0f}% of the time recently. "
                            f"Breakfast can really help with energy and focus throughout the day!"
                        )
                    return (
                        f"{name_prefix}I notice you've been eating breakfast {breakfast_rate:.0f}% of the time in your recent check-ins. "
                        f"Starting the day with a good breakfast can help with energy and mood!"
                    )

                if (
                    any(
                        word in prompt_lower
                        for word in ["mood", "feeling", "how have i been", "lately"]
                    )
                    and avg_mood
                    and avg_energy
                ):
                    if avg_mood >= 4 and avg_energy >= 4:
                        return (
                            f"{name_prefix}Looking at your recent check-ins, you've been doing really well! "
                            f"Your average mood has been {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                            f"Keep up those positive patterns!"
                        )
                    if avg_mood <= 2 or avg_energy <= 2:
                        return (
                            f"{name_prefix}I've noticed from your recent check-ins that things might be challenging lately. "
                            f"Your average mood is {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                            f"Remember that tough periods are temporary, and it's okay to take things one step at a time."
                        )
                    return (
                        f"{name_prefix}Based on your recent check-ins, you're doing okay! "
                        f"Your average mood is {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                        f"Small improvements each day add up to big changes over time."
                    )

                if any(
                    word in prompt_lower
                    for word in [
                        "how am i",
                        "how have i been",
                        "doing lately",
                        "progress",
                    ]
                ):
                    insights = []
                    if breakfast_rate >= 70:
                        insights.append("great breakfast habits")
                    if avg_mood and avg_mood >= 3.5:
                        insights.append("generally positive mood")
                    if avg_energy and avg_energy >= 3:
                        insights.append("decent energy levels")

                    if insights:
                        return f"{name_prefix}You're doing well in several areas: {', '.join(insights)}. Keep up the good work!"
                    return f"{name_prefix}There's room for improvement, but that's normal! Every small step counts."

                if any(
                    word in prompt_lower
                    for word in ["how many", "times", "count", "frequency"]
                ):
                    if "breakfast" in prompt_lower:
                        return f"{name_prefix}You ate breakfast {breakfast_count}/{total_entries} times ({breakfast_rate:.0f}%)."
                    if "mood" in prompt_lower:
                        if avg_mood is not None:
                            return f"{name_prefix}Your average mood was {avg_mood:.1f}/5 - {'positive' if avg_mood >= 4 else 'neutral' if avg_mood >= 3 else 'challenging'}."
                        return f"{name_prefix}I don't have enough mood data to calculate an average yet."
                    if "energy" in prompt_lower:
                        if avg_energy is not None:
                            return f"{name_prefix}Your average energy was {avg_energy:.1f}/5 - {'high' if avg_energy >= 4 else 'moderate' if avg_energy >= 3 else 'low'}."
                        return f"{name_prefix}I don't have enough energy data to calculate an average yet."

        if any(
            word in prompt_lower
            for word in [
                "connection",
                "connection error",
                "network",
                "api error",
                "timeout",
            ]
        ):
            return (
                f"{name_prefix}I'm having some technical difficulties right now. "
                f"Could you please try again in a moment? If the issue persists, "
                f"we can troubleshoot together. What were you trying to do?"
            )

        is_new_user = not user_context or (user_id and not recent_data)

        context_requiring_prompts = [
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

        if any(phrase in prompt_lower for phrase in context_requiring_prompts) and is_new_user:
            return (
                f"{name_prefix}I don't have enough information about how you're doing today, but we can figure it out together! "
                f"How about you tell me about your day so far? How are you feeling right now? "
                f"Once you start using check-ins, I'll be able to give you more specific insights!"
            )

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
                f"What small thing might help you feel a bit better?"
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
                f"Sometimes just taking one tiny step is enough."
            )

        health_keywords = ["sleep", "exercise", "diet", "energy", "tired", "nutrition"]
        if any(keyword in prompt_lower for keyword in health_keywords):
            return (
                f"{name_prefix}Taking care of your physical health is so important for overall wellbeing. "
                f"Small, consistent changes often make the biggest difference. What aspect of your health "
                f"would you like to focus on improving?"
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
                f"What's one small thing you could do right now?"
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
                f"even 2 minutes of progress is real progress. What's one small step you could take today?"
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
                f"Is there someone you could reach out to today?"
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
                f"How are you doing today? What's on your mind?"
            )

        thanks_keywords = ["thank", "appreciate", "grateful", "helpful"]
        if any(keyword in prompt_lower for keyword in thanks_keywords):
            return (
                f"{name_prefix}You're very welcome! I'm glad I could help. "
                f"Remember that seeking support and taking care of yourself shows real strength. "
                f"Keep up the great work!"
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
                f"Would you like to talk about what's happening, or would it help to focus on just getting through the next few minutes?"
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
                f"You don't have to face this alone. What would be most helpful right now?"
            )

        if is_new_user:
            return (
                f"{name_prefix}I'm here to listen and support you! "
                f"Since we're just getting started, I'd love to learn more about you. "
                f"How are you feeling right now? What's on your mind? "
                f"Tell me a bit about how your day is going, and I'll do my best to help!"
            )
        return (
            f"{name_prefix}I'm here to listen and support you. "
            f"How are you feeling right now? What's on your mind?"
        )

    @handle_errors(
        "getting fallback personalized message",
        default_return="Wishing you a wonderful day! Remember that every small step toward your wellbeing matters.",
    )
    def personalized(self, user_id: str) -> str:
        """Provide fallback personalized messages when AI model is not available."""
        recent_data = get_recent_responses(user_id, limit=5)
        context_result = get_user_data(user_id, "context")
        user_context = context_result.get("context")
        user_name = user_context.get("preferred_name", "") if user_context else ""
        name_prefix = f"{user_name}, " if user_name else ""

        if recent_data:
            latest_entry = recent_data[0]
            mood = latest_entry.get("mood", None)
            energy = latest_entry.get("energy", None)

            if mood and energy:
                if mood >= 4 and energy >= 4:
                    return (
                        f"{name_prefix}You're doing great! Your recent check-ins show positive energy and mood. "
                        f"Keep up those healthy habits and celebrate your progress!"
                    )
                if mood <= 2 or energy <= 2:
                    return (
                        f"{name_prefix}I noticed things might be challenging for you lately. "
                        f"Remember that tough days are temporary, and it's okay to take things one step at a time. "
                        f"Consider reaching out for support if you need it."
                    )
                return (
                    f"{name_prefix}You're making steady progress! Focus on the small things that "
                    f"make you feel good and energized. Every positive step counts."
                )

        return (
            f"{name_prefix}Hope you're having a good day! Remember to take care of yourself "
            f"and celebrate the small wins along the way."
        )

    @handle_errors("personalizing fallback with profile name", default_return="")
    def personalize_with_profile_name(
        self, fallback_response: str, context_summary: list[str], profile: dict
    ) -> str:
        """Inject preferred name into greeting-based fallback responses when available."""
        if not context_summary:
            return fallback_response

        user_name = profile.get("preferred_name", "")
        if user_name and user_name not in fallback_response:
            fallback_response = fallback_response.replace("Hello!", f"Hello {user_name}!")
            fallback_response = fallback_response.replace("Hi!", f"Hi {user_name}!")
        return fallback_response


_fallback_responses: FallbackResponses | None = None


@handle_errors("getting fallback responses helper")
def get_fallback_responses() -> FallbackResponses:
    """Return the shared fallback responses helper."""
    global _fallback_responses
    if _fallback_responses is None:
        _fallback_responses = FallbackResponses()
    return _fallback_responses
