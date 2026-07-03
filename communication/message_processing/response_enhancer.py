# communication/message_processing/response_enhancer.py

"""AI enhancement for structured command responses."""

from ai.context.assembly import assemble_action_result_messages
from core.config import AI_MAX_RESPONSE_LENGTH
from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

logger = get_component_logger("communication_manager")

EXCLUDED_ENHANCEMENT_INTENTS = {
    "help",
    "commands",
    "examples",
    "checkin_history",
    "checkin_analysis",
    "start_checkin",
    "checkin_status",
    "completion_rate",
    "task_weekly_stats",
    "task_stats",
    "task_analytics",
    "list_tasks",
    "list_task_templates",
    "show_create_hub",
    "create_task",
    "create_task_from_template",
    "complete_task",
    "delete_task",
    "update_task",
    "show_profile",
    "profile_stats",
    "show_schedule",
    "schedule_status",
    "show_analytics",
    "mood_trends",
    "energy_trends",
    "habit_analysis",
    "sleep_analysis",
    "quant_summary",
    "wellness_score",
    "analytics",
    "messages",
    "show_messages",
    "status",
    "create_note",
    "create_quick_note",
    "create_list",
    "create_journal",
    "list_recent_entries",
    "show_entry",
    "append_to_entry",
    "set_entry_body",
    "add_tags_to_entry",
    "remove_tags_from_entry",
    "search_entries",
    "pin_entry",
    "unpin_entry",
    "archive_entry",
    "unarchive_entry",
    "add_list_item",
    "toggle_list_item_done",
    "remove_list_item",
    "set_entry_group",
    "list_entries_by_group",
    "list_pinned_entries",
    "list_inbox_entries",
    "list_entries_by_tag",
    "show_natural_language_defaults",
    "update_natural_language_defaults",
    "connect_google_health",
    "google_health_status",
    "pause_google_health",
    "enable_google_health",
    "delete_google_health_data",
    "sync_google_health",
}


@handle_errors("checking AI enhancement skip", default_return=True)
def _should_skip_ai_enhancement(intent: str) -> bool:
    """Return True when AI must not rewrite a deterministic command response."""
    if intent in EXCLUDED_ENHANCEMENT_INTENTS:
        return True
    skip_keywords = (
        "profile",
        "schedule",
        "analytics",
        "messages",
        "google_health",
        "natural_language",
        "health_data",
    )
    return any(keyword in intent for keyword in skip_keywords)


@handle_errors("enhancing response with AI")
def enhance_response_with_ai(
    user_id: str,
    response: InteractionResponse,
    parsed_command: ParsedCommand,
    *,
    ai_chatbot,
    enable_ai_enhancement: bool,
) -> InteractionResponse:
    """Enhance a structured response with AI contextual information."""
    try:
        if not enable_ai_enhancement:
            return response

        intent = parsed_command.intent or ""
        if _should_skip_ai_enhancement(intent):
            return response

        result_metadata = {
            "action_name": intent,
            "completed": response.completed,
            "handler_message": response.message,
            "rich_data": response.rich_data,
            "suggestions": response.suggestions,
            "error": response.error,
            "source_message": parsed_command.original_message,
        }
        messages = assemble_action_result_messages(
            user_id,
            parsed_command.original_message,
            result_metadata,
        )
        if not messages or len(messages) < 2:
            return response

        system_content = messages[0].get("content", "")
        user_content = messages[1].get("content", parsed_command.original_message)
        context_prompt = (
            f"{system_content}\n\n"
            f"User: {user_content}\n\n"
            "Write one warm, concise user-visible reply that reflects the handler result. "
            "Return ONLY the reply text."
        )

        enhanced_text = ai_chatbot.generate_response(
            context_prompt,
            user_id=user_id,
            timeout=3,
        )

        if enhanced_text and len(enhanced_text) > 10:
            system_indicators = [
                "System response:",
                "Exercise",
                "You are a chatbot",
                "Your job is to",
                "Please enhance",
                "Return ONLY",
                "```python",
                "```json",
                "{'action':",
                '{"action":',
            ]

            has_system_content = any(
                indicator in enhanced_text for indicator in system_indicators
            )

            if not has_system_content:
                if len(enhanced_text) > AI_MAX_RESPONSE_LENGTH:
                    cut = enhanced_text[:AI_MAX_RESPONSE_LENGTH]
                    for mark in (". ", "! ", "? "):
                        idx = cut.rfind(mark)
                        if idx >= 0 and idx > AI_MAX_RESPONSE_LENGTH * 0.6:
                            enhanced_text = cut[: idx + 1]
                            break
                    else:
                        enhanced_text = cut.rstrip() + "..."
                response.message = enhanced_text.strip()
            else:
                logger.debug(
                    "AI enhancement returned system content, keeping original response"
                )

    except Exception as e:
        logger.debug(f"AI enhancement failed: {e}")

    return response
