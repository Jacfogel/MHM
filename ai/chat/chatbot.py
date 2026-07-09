# ai/chatbot.py

"""
ai/chatbot.py

A separate module to handle AI chatbot logic for any platform
(Discord, Email, etc.). This keeps AI-specific code in one place,
so we can phase in or out different messaging services without duplicating logic.
"""

import os
import asyncio
import threading
import collections
import uuid
from core.logger import get_component_logger
from core.config import (
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL,
    AI_TIMEOUT_SECONDS,
    AI_CACHE_RESPONSES,
    AI_SYSTEM_PROMPT_PATH,
    AI_USE_CUSTOM_PROMPT,
    AI_PERSONALIZED_MESSAGE_TIMEOUT,
    AI_CONTEXTUAL_RESPONSE_TIMEOUT,
    AI_QUICK_RESPONSE_TIMEOUT,
    AI_MAX_RESPONSE_LENGTH,
    AI_MAX_RESPONSE_WORDS,
    AI_MAX_RESPONSE_TOKENS,
    AI_CHAT_TEMPERATURE,
    AI_COMMAND_TEMPERATURE,
    AI_CLARIFICATION_TEMPERATURE,
)
from core.response_tracking import store_chat_interaction
from user.context_manager import user_context_manager
from ai.context.chatbot_context import build_chatbot_context_dict
from ai.prompts.manager import get_prompt_manager
from ai.client.cache_manager import get_response_cache
from ai.prompts.command_interpreter import get_command_interpreter
from ai.fallback import get_fallback_responses
from ai.chat.interaction_types import AIInteractionType, interaction_type_for_mode
from ai.chat.response_generator import get_response_generator
from ai.client.lm_studio_client import call_lm_studio_api, test_lm_studio_connection
from ai.chat.response_postprocess import (
    clean_system_prompt_leaks,
    smart_truncate_response,
    strip_instruction_tuning_markers,
    strip_letter_signoffs,
    keep_first_personalized_block,
)
from core.error_handling import handle_errors


ai_logger = get_component_logger("ai")
logger = ai_logger

# Global prompt manager instance
prompt_manager = get_prompt_manager()


class AIChatBotSingleton:
    """
    A Singleton container for LM Studio API client.
    """

    _instance = None

    # not_duplicate: singleton_new_methods
    @handle_errors("creating AI chatbot instance", default_return=None)
    def __new__(cls):
        """Create a new instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @handle_errors("initializing AI chatbot", default_return=None)
    # not_duplicate: unrelated_singleton_constructors
    def __init__(self):
        """Initialize the object."""
        if self._initialized:
            return
        logger.info("Initializing shared AIChatBot with LM Studio API (singleton).")
        self.lm_studio_available = False
        self.response_cache = get_response_cache()
        self._generation_lock = threading.Lock()  # Prevent concurrent generations
        self._locks_by_user = collections.defaultdict(
            threading.Lock
        )  # Per-user locks for better concurrency

        # Test LM Studio connection
        self._refresh_lm_studio_availability()

        # If connection failed, check LM Studio status
        if not self.lm_studio_available:
            try:
                from ai.client.lm_studio_manager import is_lm_studio_ready

                if is_lm_studio_ready():
                    logger.info("LM Studio is now ready - retrying connection")
                    self._refresh_lm_studio_availability()
                else:
                    logger.warning("LM Studio not ready - AI features will be limited")
            except Exception as e:
                logger.warning(f"LM Studio status check error: {e}")

        self._initialized = True

    @handle_errors("making cache key inputs", default_return=("", "", ""))
    def _make_cache_key_inputs(self, mode: str, user_prompt: str, user_id: str | None):
        """
        Create consistent cache key inputs with validation.

        Returns:
            tuple: (user_prompt, user_id, mode)
        """
        # Validate mode
        if not mode or not isinstance(mode, str):
            logger.error(f"Invalid mode: {mode}")
            return "", "", ""

        if not mode.strip():
            logger.error("Empty mode provided")
            return "", "", ""

        # Validate user_prompt
        if not user_prompt or not isinstance(user_prompt, str):
            logger.error(f"Invalid user_prompt: {user_prompt}")
            return "", "", ""

        if not user_prompt.strip():
            logger.error("Empty user_prompt provided")
            return "", "", ""

        # Validate user_id if provided
        if user_id is not None and not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return "", "", ""
        """Create consistent cache key inputs using prompt_type parameter."""
        # Always use the raw prompt; pass mode as prompt_type into the cache
        return user_prompt, user_id, mode

    @handle_errors("testing LM Studio connection", default_return=None)
    def _test_lm_studio_connection(self):
        """Test connection to LM Studio (delegates to ai.client.lm_studio_client)."""
        self._refresh_lm_studio_availability()

    @handle_errors("refreshing LM Studio availability", default_return=None)
    def _refresh_lm_studio_availability(self):
        """Update lm_studio_available from a live connection test."""
        self.lm_studio_available = test_lm_studio_connection()
        if os.getenv("MHM_TESTING") == "1" and self.lm_studio_available:
            ai_logger.info("LM Studio connection assumed available for tests")

    @handle_errors("calling LM Studio API", default_return=None)
    def _call_lm_studio_api(
        self,
        messages: list,
        max_tokens: int = 100,
        temperature: float = 0.2,
        timeout: int | None = None,
        *,
        stop: list[str] | None = None,
    ) -> str | None:
        """Make an API call to LM Studio (delegates to ai.client.lm_studio_client)."""
        return call_lm_studio_api(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            stop=stop,
        )

    @handle_errors(
        "mapping response mode to interaction type",
        default_return=AIInteractionType.CONVERSATIONAL,
    )
    def _interaction_type_for_mode(self, mode: str | None) -> AIInteractionType:
        """Map response mode to interaction type for structured logging."""
        return interaction_type_for_mode(mode)

    @handle_errors(
        "optimizing prompt",
        default_return=[
            {
                "role": "system",
                "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
            },
            {"role": "user", "content": "Hello"},
        ],
    )
    def _optimize_prompt(self, user_prompt: str, context: str | None = None) -> list:
        """Create optimized messages array for LM Studio API."""
        system_message = {
            "role": "system",
            "content": prompt_manager.get_prompt("wellness"),
        }

        if (
            context and len(context) < 200
        ):  # Only include context if it's reasonable size
            user_content = f"Context: {context}\n\nQuestion: {user_prompt}"
        else:
            user_content = user_prompt

        user_message = {"role": "user", "content": user_content}

        return [system_message, user_message]

    # not_duplicate: generate_response_pair
    @handle_errors(
        "generating AI response",
        default_return="I'm having trouble generating a response right now. Please try again in a moment.",
    )
    def generate_response(
        self,
        user_prompt: str,
        timeout: int | None = None,
        user_id: str | None = None,
        mode: str | None = None,
    ) -> str:
        """
        Generate a basic AI response from user_prompt, using LM Studio API.
        Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
        """
        if not self._is_valid_timeout(timeout):
            logger.error(f"Invalid timeout parameter: {timeout} (expected int)")
            return "I'm having trouble generating a response. Please check your input and try again."

        timeout = (
            timeout
            if timeout is not None
            else self._get_adaptive_timeout(AI_TIMEOUT_SECONDS)
        )
        mode = self._normalize_response_mode(mode, user_prompt)

        prompt_for_key, uid_for_key, ptype = self._make_cache_key_inputs(
            mode, user_prompt, user_id
        )

        # Check if inputs are valid - if cache key inputs are empty, inputs were invalid
        if not prompt_for_key or not prompt_for_key.strip():
            logger.error(
                f"Invalid inputs provided to generate_response: mode={mode}, user_prompt={user_prompt}, user_id={user_id}"
            )
            return "I'm having trouble generating a response. Please check your input and try again."

        cached_response = self._get_cached_non_chat_response(
            mode, prompt_for_key, uid_for_key, ptype, user_prompt, user_id
        )
        if cached_response:
            return cached_response

        if not self._ensure_lm_studio_available():
            return self._fallback_response_for_unavailable_lm(
                user_prompt, user_id, mode
            )

        # Use per-user locks for better concurrency
        lock = self._locks_by_user[user_id or "__anon__"]
        lock_acquired = lock.acquire(blocking=True, timeout=3)
        if not lock_acquired:
            logger.warning("API is busy, using enhanced contextual fallback")
            ai_logger.warning(
                "AI response using fallback - API busy",
                user_id=user_id,
                mode=mode,
                interaction_type=AIInteractionType.FALLBACK.value,
                prompt_length=len(user_prompt),
            )
            response = get_fallback_responses().contextual(user_prompt, user_id)
            # Don't cache fallback responses to allow variation
            return response

        messages, max_tokens, temperature = self._build_response_generation_request(
            mode, user_prompt, user_id
        )

        logger.debug(
            f"AIChatBot generating response via LM Studio for prompt: {user_prompt[:60]} in mode {mode}..."
        )

        try:
            stop_sequences = (
                ["## INPUT", "## OUTPUT", "### Input:", "### Output:"]
                if mode == "personalized"
                else None
            )
            # Call LM Studio API with adaptive timeout
            result = self._call_lm_studio_api(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stop=stop_sequences,
            )

            if result:
                response = self._post_process_generated_response(mode, result)
                if (
                    mode in ("chat", "personalized")
                    and len((response or "").strip()) < 3
                ):
                    response = get_fallback_responses().contextual(
                        user_prompt, user_id
                    )
                self._cache_response_if_needed(
                    mode, prompt_for_key, uid_for_key, ptype, response
                )
                self._store_chat_mode_interaction(
                    mode, user_id, user_prompt, response, context_used=True
                )

                ai_logger.info(
                    "AI response generated successfully",
                    user_id=user_id,
                    mode=mode,
                    interaction_type=self._interaction_type_for_mode(mode).value,
                    prompt_length=len(user_prompt),
                    response_length=len(response),
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response
            else:
                # API failed, use contextual fallback
                response = get_fallback_responses().contextual(user_prompt, user_id)
                # Don't cache fallback responses to allow variation

                self._store_chat_mode_interaction(
                    mode, user_id, user_prompt, response, context_used=False
                )

                ai_logger.error(
                    "AI response generation failed - using fallback",
                    user_id=user_id,
                    mode=mode,
                    interaction_type=AIInteractionType.FALLBACK.value,
                    prompt_length=len(user_prompt),
                )
                return response
        finally:
            # Always release the lock
            if lock_acquired:
                lock.release()

    @handle_errors("validating response timeout", default_return=False)
    def _is_valid_timeout(self, timeout: int | None) -> bool:
        """Validate timeout input type for response generation."""
        return timeout is None or isinstance(timeout, int)

    @handle_errors("normalizing response mode", default_return="chat")
    def _normalize_response_mode(self, mode: str | None, user_prompt: str) -> str:
        """Normalize generation mode to supported values."""
        if mode == "personalized":
            return "personalized"
        resolved_mode = (
            mode if mode is not None else get_command_interpreter().detect_mode(user_prompt)
        )
        if resolved_mode is None:
            return "chat"
        resolved_mode = resolved_mode.lower()
        if resolved_mode == "personalized":
            return "personalized"
        if resolved_mode != "chat" and not resolved_mode.startswith("command"):
            return "chat"
        return resolved_mode

    @handle_errors("getting cached non-chat response", default_return=None)
    def _get_cached_non_chat_response(
        self,
        mode: str,
        prompt_for_key: str,
        uid_for_key: str | None,
        ptype: str,
        user_prompt: str,
        user_id: str | None,
    ) -> str | None:
        """Return cached response for non-chat modes when eligible."""
        if mode == "chat":
            return None

        cached_response = self.response_cache.get(
            prompt_for_key, uid_for_key, prompt_type=ptype
        )
        if not cached_response or cached_response.startswith(
            "I'm here to listen and support you"
        ):
            return None

        if mode == "command":
            cleaned_response = get_command_interpreter().extract_command_from_response(
                cached_response
            )
            ai_logger.debug(
                "AI response served from cache (cleaned)",
                user_id=user_id,
                mode=mode,
                prompt_length=len(user_prompt),
            )
            return cleaned_response

        ai_logger.debug(
            "AI response served from cache",
            user_id=user_id,
            mode=mode,
            prompt_length=len(user_prompt),
        )
        return cached_response

    @handle_errors("ensuring LM Studio availability", default_return=False)
    def _ensure_lm_studio_available(self) -> bool:
        """Ensure LM Studio availability by retrying connection if needed."""
        if not self.lm_studio_available:
            self._test_lm_studio_connection()
        return self.lm_studio_available

    @handle_errors(
        "getting fallback response for unavailable LM Studio",
        default_return="I'm having trouble generating a response right now. Please try again in a moment.",
    )
    def _fallback_response_for_unavailable_lm(
        self, user_prompt: str, user_id: str | None, mode: str
    ) -> str:
        """Return contextual fallback when LM Studio is unavailable."""
        response = get_fallback_responses().contextual(user_prompt, user_id)
        ai_logger.warning(
            "AI response using fallback - LM Studio unavailable",
            user_id=user_id,
            mode=mode,
            interaction_type=AIInteractionType.FALLBACK.value,
            prompt_length=len(user_prompt),
        )
        return response

    @handle_errors(
        "building response generation request",
        default_return=([], AI_MAX_RESPONSE_TOKENS, AI_CHAT_TEMPERATURE),
    )
    def _build_response_generation_request(
        self, mode: str, user_prompt: str, user_id: str | None
    ) -> tuple[list, int, float]:
        """Build messages and generation parameters based on response mode."""
        if mode == "command":
            return (
                get_command_interpreter().create_command_parsing_prompt(user_prompt),
                60,
                AI_COMMAND_TEMPERATURE,
            )
        if mode == "command_with_clarification":
            return (
                get_command_interpreter().create_command_parsing_prompt(
                    user_prompt, clarification=True
                ),
                120,
                AI_CLARIFICATION_TEMPERATURE,
            )
        if mode == "personalized":
            from ai.fallback import data_access
            from ai.fallback.profile_helpers import name_prefix_from_context

            context_result = (
                data_access.get_user_data(user_id, "context") if user_id else {}
            )
            user_context = (context_result or {}).get("context") or {}
            name_prefix = name_prefix_from_context(user_context).strip().rstrip(",")

            system_content = (
                "You are a supportive wellness assistant writing a brief scheduled wellness message. "
                "Write 2-4 complete sentences (under 100 words) using only the wellness data in the request. "
                "Be warm and specific. End with a finished supportive sentence. "
                "Do not add a letter-style sign-off or signature — no 'Best wishes', 'Take care', "
                "or placeholder names like [Your Name]; you already greet the user at the start. "
                "Return only the message text — no INPUT/OUTPUT markers, labels, or second replies."
            )
            if name_prefix:
                system_content += f" Address the user as {name_prefix}."
            return (
                [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_prompt},
                ],
                150,
                0.7,
            )

        template = prompt_manager.get_prompt_template("wellness")
        template_max_tokens = template.max_tokens if template and template.max_tokens else 0
        max_tokens = max(template_max_tokens, AI_MAX_RESPONSE_TOKENS)
        temperature = (
            template.temperature
            if template and template.temperature is not None
            else AI_CHAT_TEMPERATURE
        )
        messages = get_response_generator().create_comprehensive_context_prompt(
            user_id, user_prompt
        )
        return messages, max_tokens, temperature

    @handle_errors("post-processing generated response", default_return="")
    def _post_process_generated_response(self, mode: str, result: str) -> str:
        """Post-process model output into final user-visible response."""
        response = result.strip()
        response = strip_instruction_tuning_markers(response)
        response = clean_system_prompt_leaks(response)
        if mode == "command":
            response = get_command_interpreter().extract_command_from_response(response)
        if mode == "personalized":
            response = strip_letter_signoffs(response)
            response = keep_first_personalized_block(response)
            return smart_truncate_response(
                response, AI_MAX_RESPONSE_LENGTH, max_words=100
            )
        return smart_truncate_response(
            response, AI_MAX_RESPONSE_LENGTH, AI_MAX_RESPONSE_WORDS
        )

    @handle_errors("caching response when needed", default_return=None)
    def _cache_response_if_needed(
        self,
        mode: str,
        prompt_for_key: str,
        uid_for_key: str | None,
        ptype: str,
        response: str,
    ) -> None:
        """Cache successful non-chat responses."""
        if mode != "chat":
            self.response_cache.set(
                prompt_for_key, response, uid_for_key, prompt_type=ptype
            )

    @handle_errors("storing chat mode interaction", default_return=None)
    def _store_chat_mode_interaction(
        self,
        mode: str,
        user_id: str | None,
        user_prompt: str,
        response: str,
        *,
        context_used: bool,
    ) -> None:
        """Persist chat interactions for conversation context."""
        if mode == "chat" and user_id:
            store_chat_interaction(user_id, user_prompt, response, context_used=context_used)

    @handle_errors("generating async AI response")
    async def async_generate_response(
        self, user_prompt: str, user_id: str | None = None
    ) -> str:
        """
        Async variant if you need to integrate with an async context.
        """
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.generate_response, user_prompt, AI_TIMEOUT_SECONDS, user_id
        )

    @handle_errors("checking AI availability", default_return=False)
    def is_ai_available(self) -> bool:
        """
        Check if the AI model is available and functional.
        """
        return self.lm_studio_available

    @handle_errors("reloading system prompt", default_return=None)
    def reload_system_prompt(self):
        """
        Reload the system prompt from file (useful for development and testing).
        """
        prompt_manager.reload_custom_prompt()
        logger.info("System prompt reloaded via AI chatbot")

    @handle_errors(
        "testing system prompt integration", user_friendly=False, default_return={}
    )
    def test_system_prompt_integration(self) -> dict:
        """
        Test the system prompt integration and return status information.
        """
        test_results = {
            "custom_prompt_enabled": AI_USE_CUSTOM_PROMPT,
            "prompt_file_exists": os.path.exists(AI_SYSTEM_PROMPT_PATH),
            "custom_prompt_loaded": prompt_manager.has_custom_prompt(),
            "prompt_length": prompt_manager.custom_prompt_length(),
            "fallback_prompts_available": len(prompt_manager.fallback_prompt_keys())
            > 0,
        }

        # Test each prompt type
        for prompt_type in ["wellness", "command", "neurodivergent_support"]:
            try:
                prompt = prompt_manager.get_prompt(prompt_type)
                test_results[f"{prompt_type}_prompt_works"] = True
                test_results[f"{prompt_type}_prompt_length"] = len(prompt)
            except Exception as e:
                test_results[f"{prompt_type}_prompt_works"] = False
                test_results[f"{prompt_type}_prompt_error"] = str(e)

        return test_results

    @handle_errors("getting AI status", default_return={})
    def get_ai_status(self) -> dict:
        """
        Get detailed status information about the AI system.
        """
        return {
            "lm_studio_available": self.lm_studio_available,
            "lm_studio_base_url": LM_STUDIO_BASE_URL,
            "lm_studio_model": LM_STUDIO_MODEL,
            "ai_functional": self.lm_studio_available,
            "fallback_mode": not self.lm_studio_available,
            "cache_enabled": AI_CACHE_RESPONSES,
            "cache_size": len(self.response_cache.cache),
            "timeout_seconds": AI_TIMEOUT_SECONDS,
            # System prompt information
            "custom_prompt_enabled": AI_USE_CUSTOM_PROMPT,
            "custom_prompt_path": AI_SYSTEM_PROMPT_PATH,
            "custom_prompt_loaded": prompt_manager.has_custom_prompt(),
            "prompt_length": prompt_manager.custom_prompt_length(),
            "prompt_file_exists": os.path.exists(AI_SYSTEM_PROMPT_PATH),
        }

    @handle_errors(
        "generating personalized message",
        default_return="Wishing you a wonderful day! Remember that every small step toward your wellbeing matters.",
    )
    def generate_personalized_message(
        self,
        user_id: str,
        timeout: int | None = None,
        *,
        prompt_prefix: str | None = None,
        skip_cache: bool = False,
    ) -> str:
        """
        Generate a personalized message by examining the user's recent responses
        (check-in data). Uses longer timeout since this is not real-time.

        When skip_cache is True (admin test sends), bypass the response cache and
        ask the model for fresh wording so back-to-back tests are not identical.
        """
        if timeout is None:
            timeout = AI_PERSONALIZED_MESSAGE_TIMEOUT

        if not self.lm_studio_available:
            return get_fallback_responses().personalized(user_id)

        from core.health_context_builder import build_personalized_wellness_context

        user_summary = build_personalized_wellness_context(user_id)[:400]

        instruction = (
            "Create a brief, encouraging message based on the wellness data below. "
            "When 'Primary source — wearable wellness' is present, base the message on "
            "recovery and activity patterns only; do not mention check-ins or hopelessness. "
            "Use coarse recovery language only (no exact hours, step counts, heart rate, or device names). "
            f"Data: {user_summary}. "
            "Keep it supportive, personal, and under 100 words. "
            "Do not end with a sign-off or signature (no 'Best wishes', 'Take care', or [Your Name])."
        )
        if prompt_prefix:
            instruction = f"{prompt_prefix} {instruction}"
        if skip_cache:
            instruction += (
                f" Use fresh wording distinct from any prior message "
                f"(variation: {uuid.uuid4().hex[:8]})."
            )
        prompt = instruction

        if not skip_cache:
            cached_response = self.response_cache.get(
                prompt, user_id, prompt_type="personalized"
            )
            if cached_response:
                return cached_response

        response = self.generate_response(
            prompt, timeout=timeout, user_id=user_id, mode="personalized"
        )

        if not skip_cache:
            self.response_cache.set(
                prompt,
                response,
                user_id,
                prompt_type="personalized",
                metadata={"mode": "personalized"},
            )

        return response

    @handle_errors(
        "generating quick response",
        default_return="I'm having trouble responding right now. Please try again in a moment.",
    )
    def generate_quick_response(
        self, user_prompt: str, user_id: str | None = None
    ) -> str:
        """
        Generate a quick response for real-time chat (Discord, etc.).
        Uses shorter timeout optimized for responsiveness.
        """
        # Use shorter timeout for real-time interactions
        return self.generate_response(
            user_prompt, timeout=AI_QUICK_RESPONSE_TIMEOUT, user_id=user_id
        )

    # not_duplicate: generate_response_pair
    @handle_errors(
        "generating contextual response",
        default_return="I'm having trouble generating a contextual response right now. Please try again in a moment.",
    )
    def generate_contextual_response(
        self, user_id: str, user_prompt: str, timeout: int | None = None
    ) -> str:
        """
        Generate a context-aware response using comprehensive user data.
        Integrates with existing UserContext and UserPreferences systems.
        """
        if timeout is None:
            timeout = AI_CONTEXTUAL_RESPONSE_TIMEOUT

        # Envelope-backed context dict; overlay in-memory session exchanges.
        context = build_chatbot_context_dict(
            user_id, include_conversation_history=True
        )
        session_history = user_context_manager.conversation_history.get(user_id, [])[
            -5:
        ]
        if session_history:
            context["conversation_history"] = session_history
        profile, context_summary, context_str = self._build_contextual_summary(context)

        if not self.lm_studio_available:
            # Use enhanced contextual fallback with user information and data analysis
            fallback_response = get_fallback_responses().contextual(user_prompt, user_id)

            # Enhance fallback with context if available
            fallback_response = get_fallback_responses().personalize_with_profile_name(
                fallback_response, context_summary, profile
            )
            self._record_contextual_interaction(
                user_id, user_prompt, fallback_response, context_used=True
            )
            return fallback_response

        # Create comprehensive context-aware messages for LM Studio with all user data
        messages = get_response_generator().create_comprehensive_context_prompt(
            user_id, user_prompt
        )

        if not self._is_data_analysis_question(user_prompt):
            cached_response = self.response_cache.get(
                user_prompt, user_id, prompt_type="contextual"
            )
            if cached_response:
                self._record_contextual_interaction(
                    user_id, user_prompt, cached_response, context_used=True
                )
                return cached_response

        # Generate AI response with context
        # Use per-user locks for better concurrency
        lock = self._locks_by_user[user_id or "__anon__"]
        lock_acquired = lock.acquire(blocking=True, timeout=5)
        if not lock_acquired:
            logger.warning("API is busy, using enhanced contextual fallback")
            fallback_response = get_fallback_responses().contextual(user_prompt, user_id)
            self._record_contextual_interaction(
                user_id, user_prompt, fallback_response, context_used=False
            )
            return fallback_response

        logger.debug(
            f"Generating contextual response for user {user_id} with context: {context_str[:60]}..."
        )

        try:
            # Call LM Studio API with context
            result = self._call_lm_studio_api(
                messages=messages,
                max_tokens=80,  # Shorter responses for faster generation
                temperature=0.2,  # Lower temperature for focused responses
                timeout=timeout,
            )

            if result:
                response = result.strip()
                # Clean any leaked system prompt metadata
                response = clean_system_prompt_leaks(response)
                # Ensure response acknowledges the user by name if available
                user_name = profile.get("preferred_name", "")
                if user_name and user_name.lower() not in response.lower():
                    # Prepend name if not already included
                    response = f"{user_name}, {response}"
            else:
                response = get_fallback_responses().contextual(user_prompt, user_id)
                logger.info("Using contextual fallback response")

            # Cache the final response for contextual prompts
            self.response_cache.set(
                user_prompt,
                response,
                user_id,
                prompt_type="contextual",
                metadata={"mode": "contextual"},
            )

            # Single call to record the interaction
            self._record_contextual_interaction(
                user_id, user_prompt, response, context_used=True
            )

            return response
        finally:
            # Always release the lock
            if lock_acquired:
                lock.release()

    @handle_errors(
        "building contextual summary",
        default_return=({}, [], "New user"),
    )
    def _build_contextual_summary(self, context: dict) -> tuple[dict, list[str], str]:
        """Build a concise context summary used for logging and fallback personalization."""
        context_summary = []
        profile = context.get("user_profile", {})

        if profile.get("preferred_name"):
            context_summary.append(f"User's name is {profile['preferred_name']}")
        if profile.get("active_categories"):
            categories = profile["active_categories"][:2]
            context_summary.append(f"Interested in: {', '.join(categories)}")

        recent_activity = context.get("recent_activity", {})
        if recent_activity.get("recent_responses_count", 0) > 2:
            context_summary.append(
                f"Active user with {recent_activity['recent_responses_count']} recent check-ins"
            )

        mood_trends = context.get("mood_trends", {})
        if mood_trends.get("average_mood") is not None:
            avg_mood = mood_trends["average_mood"]
            context_summary.append(f"Recent mood: {avg_mood:.1f}/5")

        context_str = ". ".join(context_summary) if context_summary else "New user"
        return profile, context_summary, context_str

    @handle_errors("detecting contextual data analysis question", default_return=False)
    def _is_data_analysis_question(self, user_prompt: str) -> bool:
        """Detect prompts that should bypass contextual cache for fresh data."""
        data_analysis_keywords = [
            "how often",
            "how many",
            "check",
            "frequency",
            "times",
            "average",
            "lately",
            "recent",
        ]
        prompt_lower = user_prompt.lower()
        return any(keyword in prompt_lower for keyword in data_analysis_keywords)

    @handle_errors("recording contextual interaction", default_return=None)
    def _record_contextual_interaction(
        self, user_id: str, user_prompt: str, response: str, *, context_used: bool
    ) -> None:
        """Persist contextual response and conversation history."""
        store_chat_interaction(user_id, user_prompt, response, context_used=context_used)
        user_context_manager.add_conversation_exchange(user_id, user_prompt, response)

    @handle_errors("detecting resource constraints", default_return=False)
    def _detect_resource_constraints(self) -> bool:
        """Detect if system is resource-constrained."""
        import psutil

        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Consider system constrained if:
        # - Memory usage > 90%
        # - Available memory < 2 GB
        # - CPU usage > 80%
        is_constrained = (
            memory.percent > 90
            or memory.available < (2 * 1024**3)  # 2 GB
            or cpu_percent > 80
        )

        if is_constrained:
            logger.warning(
                f"System resource constraints detected: Memory {memory.percent}%, CPU {cpu_percent}%, Available RAM {memory.available / (1024**3):.1f}GB"
            )

        return is_constrained

    @handle_errors("cleaning system prompt leaks", default_return="")
    def _clean_system_prompt_leaks(self, response: str) -> str:
        """Remove leaked system prompt metadata (delegates to ai.chat.response_postprocess)."""
        return clean_system_prompt_leaks(response)

    @handle_errors("smart truncating response", default_return="...")
    def _smart_truncate_response(
        self, text: str, max_chars: int, max_words: int | None = None
    ) -> str:
        """Smartly truncate response (delegates to ai.chat.response_postprocess)."""
        return smart_truncate_response(text, max_chars, max_words)

    @handle_errors("getting adaptive timeout", default_return=15)
    def _get_adaptive_timeout(self, base_timeout: int) -> int:
        """Get adaptive timeout based on system resources."""
        if self._detect_resource_constraints():
            # Increase timeout for resource-constrained systems
            return min(base_timeout * 2, 60)  # Cap at 60 seconds
        return base_timeout


@handle_errors("getting AI chatbot instance")
def get_ai_chatbot():
    """
    Return the shared AIChatBot instance.
    """
    return AIChatBotSingleton()
