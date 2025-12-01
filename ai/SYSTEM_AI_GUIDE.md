# AI System Documentation

> **File**: `ai/SYSTEM_AI_GUIDE.md`
> **Audience**: Developers and AI collaborators working on MHM's AI system
> **Purpose**: Explain how the AI subsystem is structured, how it behaves at runtime, and how to extend it safely
> **Style**: Technical, concise, system-level (hybrid of conceptual and concrete details)
> **Last Updated**: 2025-11-01

## 1. Overview

The MHM AI subsystem is responsible for generating context-aware, safety-aligned responses and for helping interpret user messages (for example, parsing commands) across all channels.

It is designed to:

- Centralize AI-specific logic (so channels can be added/removed without duplicating behavior)
- Use local models via LM Studio when available, with clear fallbacks
- Build rich user context (history, mood, schedules, preferences) in a safe, controlled way
- Apply strict prompt, logging, and error-handling rules
- Support both rule-based and AI-enhanced parsing without making AI a single point of failure

This guide focuses on the AI implementation layer. For overall system design, see section 2. "Directory Overview" in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 2. High-Level Architecture

### 2.1. Core components

The AI subsystem lives primarily under `ai/` and collaborates with `user/` and `core/`:

- `ai/chatbot.py`  
  - Main AI chatbot logic (modes, LM Studio calls, caching, fallbacks).
- `ai/prompt_manager.py`  
  - Loads and manages the system prompt and prompt templates.
- `ai/cache_manager.py`  
  - Response and context caching with TTL and LRU cleanup.
- `ai/context_builder.py`  
  - Builds AI-ready context from user data and recent responses.
- `ai/conversation_history.py`  
  - Persists and retrieves per-user conversational history.
- `ai/lm_studio_manager.py`  
  - Detects LM Studio status and model readiness.
- `communication/message_processing/command_parser.py`  
  - Enhanced command parser combining rule-based and AI parsing.

Supporting modules:

- `user/context_manager.py`  
  - Aggregates user profile, preferences, recent activity, insights, and schedules into an AI context structure.
- `core/response_tracking.py`  
  - Stores and retrieves recent responses and check-ins for use in context.
- `core/config.py`  
  - AI- and LM-Studio-related configuration (URLs, timeouts, thresholds).
- `core/error_handling.py` and `core/logger.py`  
  - Centralized error handling and logging for all AI components.

### 2.2. Request / response flow (simplified)

At a high level:

1. A message arrives from a channel (e.g., Discord, Email).
2. The communication layer may call the enhanced command parser (`EnhancedCommandParser.parse`) to interpret commands.
3. When a free-form AI reply is needed, code calls into `AIChatBotSingleton.generate_response` or `generate_contextual_response`.
4. The chatbot:
   - Detects mode (chat vs command).
   - Optionally builds context via `ContextBuilder` and `UserContextManager`.
   - Builds a prompt via `PromptManager`.
   - Calls LM Studio (if available) with timeouts and error handling.
   - Applies safety and cleaning rules.
   - Caches appropriate responses via `ResponseCache`.
5. The final response goes back through the communication layer to the user.

---

## 3. Entry Points and Modes

### 3.1. Main runtime entry points

The core public entry points in `ai/chatbot.py` are:

- `generate_response(user_prompt, timeout=None, user_id=None, mode=None)`  
  - Core synchronous generation function used by other helpers.  
  - Decorated with `@handle_errors("generating AI response", default_return="I'm having trouble generating a response right now. Please try again in a moment.")`.
- `async_generate_response(user_prompt, user_id=None)`  
  - Thin async wrapper that runs `generate_response` on an executor.
- `generate_contextual_response(user_id, user_prompt, timeout=None)`  
  - Builds rich context for the user first, then calls into `generate_response`.
- Higher-level helpers in communication or parsing modules call these functions; avoid calling LM Studio directly from elsewhere.

All of these are accessed via a singleton instance; use `get_ai_chatbot()` rather than instantiating the chatbot class directly.

### 3.2. Modes

The AI subsystem distinguishes between two primary modes internally:

- **Chat mode** (`mode="chat"`)  
  - General wellness/support/QA conversation.
  - No caching for responses to allow natural variation.
- **Command mode** (`mode="command"`)  
  - Structured responses used for parsing and integration with `EnhancedCommandParser`.
  - Caching is enabled when safe, and responses may be cleaned or parsed as JSON/structured output.

`AIChatBotSingleton._detect_mode(user_prompt)` applies a combination of keyword heuristics and simple patterns (for example, phrases like "create a task", "remind me to...", "update my schedule") to choose a mode when one is not explicitly provided.

When you add new high-level capabilities, prefer:

- Keeping **mode detection rules** in `ai/chatbot.py`, and
- Introducing **explicit mode override** where higher-level code already knows the correct mode (for example, command parsing).

### 3.3. Command parsing integration

The enhanced command parser in `communication/message_processing/command_parser.py` uses two layers:

1. **Rule-based parsing**  
   - Regex patterns for common intents (`create_task`, `update_task`, `edit_schedule_period`, etc.).
   - If a high-confidence match is found (above `AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD` in `core/config.py`), it returns a structured `ParsedCommand` without calling AI.

2. **AI-enhanced parsing**  
   - When the rule-based layer is not confident enough, `EnhancedCommandParser._ai_enhanced_parse` calls:
     ```python
     ai_response = self.ai_chatbot.generate_response(
         message,
         mode="command",
         user_id=user_id,
         timeout=AI_COMMAND_PARSING_TIMEOUT,
     )
     ```
   - The AI is expected to return either:
     - A key-value style response, or
     - JSON with `intent` and `details`, which the parser then normalizes into a `ParsedCommand`.

Confidence scores for AI parsing rely on thresholds from `core/config.py`:
- `AI_AI_PARSING_BASE_CONFIDENCE`
- `AI_AI_PARSING_PARTIAL_CONFIDENCE`
- `AI_AI_ENHANCED_CONFIDENCE_THRESHOLD`

Do not hard-code these thresholds in new code; use the values from `core/config.py` and, where necessary, refer to section 9. "Configuration" in this guide.

---

## 4. Context and Conversation State

### 4.1. Context builder and user context manager

Two layers collaborate to assemble context:

- `user/context_manager.py` (`UserContextManager`)  
  - Manages user profile, preferences, schedules, check-ins, and derived insights.
  - Uses `get_user_data`, `get_recent_checkins`, and schedule utilities to build a structured `ai_context` dictionary.
  - Key fields include:
    - `preferred_name`
    - `active_categories`
    - `messaging_service`
    - `active_schedules`
    - Recent activity and mood trends
- `ai/context_builder.py` (`ContextBuilder`)  
  - Wraps the above plus response tracking and conversation history.
  - Decorated with `@handle_errors("building user context", default_return=ContextData())`.
  - Produces a `ContextData` object with:
    - Structured data (for internal use) and
    - A concise, human-readable summary string used in prompts.

If context cannot be built (for example, missing data, file corruption), the builder falls back to a safe default (for example, treating the user as "New user") rather than failing the entire AI request.

### 4.2. Conversation history and recent activity

Conversation history lives through:

- `ai/conversation_history.py`  
  - Handles storage and retrieval of messages per user.
  - Limits the number of entries used in prompts to keep context manageable (most recent interactions only).
- `core/response_tracking.py`  
  - Provides `get_recent_responses`, `get_recent_checkins`, and related helpers.
  - Stores user interactions in JSON files under user-specific directories.
  - Decorated with `@handle_errors` to avoid crashes when log files are missing or corrupted.

`ContextBuilder` uses these sources to include:

- A short summary of recent check-ins (for example, average mood over recent days).
- A compact representation of recent conversation topics when available.

When you add new forms of tracked data, prefer:

1. Extending `response_tracking.py` (or related tracking utilities).
2. Updating `UserContextManager` and `ContextBuilder` to integrate the new signals.
3. Keeping the context summary short and stable to avoid prompt bloat.

---

## 5. Prompting and Model Interaction

### 5.1. Prompt manager

The prompt layer in `ai/prompt_manager.py` is responsible for:

- Loading the **system prompt** from `AI_SYSTEM_PROMPT_PATH` (by default `resources/assistant_system_prompt.txt`).
- Respecting `AI_USE_CUSTOM_PROMPT` from `core/config.py` to enable/disable custom system prompts.
- Providing `PromptTemplate` structures for different prompt types (for example, chat, command parsing).

The system prompt encodes:

- Safety rules (no self-harm assistance, no medical or legal advice beyond permitted scope, etc.).
- Tone and style (supportive, concise, non-judgmental).
- Rules about using context and avoiding vague references.
- How to respond when context is missing or incomplete.

When you adjust behavior, prefer editing the system prompt file and `PromptTemplate` definitions rather than hardcoding new rules in multiple places.

### 5.2. LM Studio integration

`ai/chatbot.py` delegates model interaction to LM Studio via HTTP:

- Uses LM Studio configuration from `core/config.py`:
  - `LM_STUDIO_BASE_URL`
  - `LM_STUDIO_API_KEY`
  - `LM_STUDIO_MODEL`
  - `AI_API_CALL_TIMEOUT` and related timeouts.
- `ai/lm_studio_manager.py` provides helpers to:
  - Check whether LM Studio is running.
  - Ensure the configured model is loaded.
  - Optionally auto-start LM Studio and auto-load the model based on:
    - `LM_STUDIO_AUTO_START`
    - `LM_STUDIO_AUTO_LOAD_MODEL`
    - `LM_STUDIO_STARTUP_TIMEOUT`
    - `LM_STUDIO_MODEL_LOAD_TIMEOUT`

`AIChatBotSingleton`:

- Tests LM Studio connectivity at initialization (`_test_lm_studio_connection`).
- Uses `lm_studio_available` flags to decide whether to call the model or fall back to local responses.
- Applies timeouts to each request so a hung LM Studio instance does not block the whole app.

Do not bypass these helpers or call LM Studio directly from other modules.

---

## 6. Caching and Performance

### 6.1. Response and context caches

`ai/cache_manager.py` provides:

- `ResponseCache`:
  - Caches AI responses keyed by prompt, user_id, and prompt type.
  - Uses TTL and LRU cleanup to control memory usage.
  - Controlled by:
    - `AI_CACHE_RESPONSES`
    - `AI_RESPONSE_CACHE_TTL`
- `ContextCache`:
  - Caches built context to avoid recomputing expensive summaries on every request.
  - Controlled by:
    - `CONTEXT_CACHE_TTL`

`AIChatBotSingleton.generate_response`:

- Skips cache for pure chat responses and certain fallback messages to allow variation.
- Uses cache only when the key is valid (for example, non-empty prompt and mode).
- Cleans cached command responses (for example, extracting just the relevant JSON or key-value segment).

### 6.2. Locks and concurrency

To avoid concurrent generation conflicts, the chatbot uses:

- A global `_generation_lock` to guard certain shared operations.
- Per-user locks (`_locks_by_user`) backed by `threading.Lock`:
  - Allows concurrent requests across users.
  - Serializes requests per user to avoid interleaving conversation state or exceeding model capacity.

When adding new concurrent behavior around AI calls, reuse these locks instead of adding new global synchronization primitives.

---

## 7. Configuration and Feature Flags

All AI-related configuration lives in `core/config.py`. Key values include:

- **LM Studio / model parameters**
  - `LM_STUDIO_BASE_URL`
  - `LM_STUDIO_API_KEY`
  - `LM_STUDIO_MODEL`
  - `LM_STUDIO_AUTO_START`
  - `LM_STUDIO_AUTO_LOAD_MODEL`
  - `LM_STUDIO_STARTUP_TIMEOUT`
  - `LM_STUDIO_MODEL_LOAD_TIMEOUT`

- **AI behavior and performance**
  - `AI_TIMEOUT_SECONDS`
  - `AI_BATCH_SIZE`
  - `AI_CUDA_WARMUP`
  - `AI_CONNECTION_TEST_TIMEOUT`
  - `AI_API_CALL_TIMEOUT`

- **Caching**
  - `AI_CACHE_RESPONSES`
  - `AI_RESPONSE_CACHE_TTL`
  - `CONTEXT_CACHE_TTL`

- **Parsing thresholds and timeouts**
  - `AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD`
  - `AI_AI_ENHANCED_CONFIDENCE_THRESHOLD`
  - `AI_AI_PARSING_BASE_CONFIDENCE`
  - `AI_AI_PARSING_PARTIAL_CONFIDENCE`
  - `AI_COMMAND_PARSING_TIMEOUT`

When changing AI behavior:

1. Prefer updating these config values (or their environment variables) rather than hardcoding new constants.
2. If you add new AI-related config, ensure it is:
   - Validated in `core/config.py`, and
   - Documented in section 9. "Configuration" of this guide or the main configuration docs.

---

## 8. Error Handling and Fallbacks

AI components rely heavily on the centralized error handling system:

- Most public methods in the AI stack are decorated with `@handle_errors`, for example:
  - `_detect_mode`
  - `generate_response`
  - `build_user_context`
  - Cache operations
  - Command parsing

For detailed patterns, see:

- Section 2. "Architecture Overview" and section 4. "Error Categories and Severity" in [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).
- [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) for AI-facing routing rules and constraints.

### 8.1. Typical AI-specific fallbacks

Common fallback behaviors include:

- If LM Studio is not available or model calls repeatedly fail:
  - Use a local, simple fallback response (for example, supportive generic messages) via `_get_contextual_fallback`.
  - Log the failure to the AI component logger and, where appropriate, to user-activity logs.
- If context building fails:
  - Log the failure.
  - Use a minimal "New user" context string and continue with generation rather than failing the entire request.
- If caching operations fail:
  - Log and continue without caching instead of blocking.

When extending behavior:

- Do not raise new exceptions at the edges of the AI subsystem without routing them through `handle_errors`.
- Prefer adding new, specific error messages and recovery actions in `core/error_handling.py` rather than catching everything locally and swallowing errors silently.

---

## 9. Testing and Troubleshooting

### 9.1. Automated tests

The AI subsystem is covered both by general tests and AI-specific functionality tests.

- For overall testing strategy and layout, see:
  - Section 1. "Purpose and Scope" and section 3. "Fixtures, Utilities, and Safety" in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).
- For AI-specific functional tests, see:
  - [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md) for behavior-focused AI test flows.
  - [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md) and [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md) for channel-specific manual checks.

These guides describe how to:

- Run automated AI functionality tests (for example, via `tests/ai/run_ai_functionality_tests.py`).
- Validate mode detection behavior.
- Confirm that prompts, context, and fallbacks behave as expected.
- Check that error handling and logging work correctly for AI failures.

### 9.2. Logs and debugging

AI-related logs are routed to component loggers named:

- `ai` / `ai_chatbot`
- `ai_context`
- `ai_cache`
- `ai_prompt`
- `user_activity` (for response tracking)

For logging details, see:

- Section 2. "Logging Architecture" and section 4. "Component Log Files and Layout" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).
- [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md) for AI-specific logging rules and patterns.

When debugging:

1. Check the AI component logs for mode detection, prompt building, and LM Studio call issues.
2. Check `user_activity` logs and response tracking files for context/history problems.
3. Use configuration validation helpers in `core/config.py` to detect misconfiguration (for example, invalid URLs or timeouts).

### 9.3. Common troubleshooting steps

If AI responses stop working or degrade:

- Verify LM Studio is running and the configured model is loaded.
- Check timeouts (`AI_API_CALL_TIMEOUT`, `AI_TIMEOUT_SECONDS`, `AI_COMMAND_PARSING_TIMEOUT`) for values that are too low or too high.
- Inspect AI logs for repeated errors or timeouts.
- Confirm that the system prompt file exists at `AI_SYSTEM_PROMPT_PATH` and is readable.
- Run AI functionality tests to see whether failures are localized (for example, only parsing) or global (LM Studio down).

---

## 10. Module Map (Short Reference)

For quick navigation when working on the AI subsystem:

- `ai/chatbot.py`  
  - Main AI entry points, modes, LM Studio calls, caching, and concurrency.
- `ai/context_builder.py`  
  - Assembles AI context from user data, recent activity, and conversation history.
- `user/context_manager.py`  
  - Manages user profile, preferences, schedules, and insights; produces a structured AI context object.
- `core/response_tracking.py`  
  - Stores and retrieves user responses, check-ins, and interactions.
- `ai/prompt_manager.py`  
  - System prompt and prompt templates; safety and style rules.
- `ai/cache_manager.py`  
  - Response and context caches (TTL and LRU).
- `ai/conversation_history.py`  
  - Conversation history persistence; limits history passed into prompts.
- `ai/lm_studio_manager.py`  
  - LM Studio status checks, model readiness, and auto-start behavior.
- `communication/message_processing/command_parser.py`  
  - Enhanced command parser using both rule-based and AI-assisted parsing.
- `core/config.py`  
  - AI configuration values, thresholds, and validation logic.
