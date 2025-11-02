# AI System Documentation

> **Purpose**: Comprehensive documentation for the MHM AI system architecture, components, and behavior  
> **Last Updated**: 2025-11-01

## Overview

The MHM AI system provides intelligent, context-aware responses for mental health support. It uses LM Studio (local language model) via HTTP API and includes sophisticated context management, response caching, and fallback mechanisms.

## Architecture

### Core Components

1. **`ai/chatbot.py`** - Main AI chatbot logic and LM Studio integration
2. **`ai/prompt_manager.py`** - Manages AI prompts and templates
3. **`ai/cache_manager.py`** - Response and context caching
4. **`user/context_manager.py`** - Builds comprehensive user context
5. **`ai/lm_studio_manager.py`** - LM Studio connection management

### Singleton Pattern

The AI system uses a **Singleton pattern** for the chatbot instance:

```python
from ai.chatbot import get_ai_chatbot

chatbot = get_ai_chatbot()  # Returns shared AIChatBotSingleton instance
```

This ensures a single instance across the application, with shared connection state and caching.

## Main Entry Points

### 1. `generate_response()`

Basic AI response generation without full context.

**Signature:**
```python
def generate_response(
    user_prompt: str,
    timeout: Optional[int] = None,
    user_id: Optional[str] = None,
    mode: Optional[str] = None,
) -> str
```

**Behavior:**
- Auto-detects mode if not provided (`chat`, `command`, `command_with_clarification`)
- Checks cache for non-chat modes
- Uses LM Studio API if available, falls back to contextual fallback if unavailable
- Uses per-user locks to prevent concurrent generation conflicts
- Post-processes command responses to extract structured format
- Applies smart truncation and conversational enhancement

**Example:**
```python
response = chatbot.generate_response("How are you?", user_id="user123")
```

### 2. `generate_contextual_response()`

Context-aware response generation with full user data.

**Signature:**
```python
def generate_contextual_response(
    user_id: str,
    user_prompt: str,
    timeout: Optional[int] = None,
) -> str
```

**Behavior:**
- Builds comprehensive user context (profile, check-ins, tasks, schedules, messages)
- Formats context in natural language (not structured JSON)
- Uses longer timeout (`AI_CONTEXTUAL_RESPONSE_TIMEOUT`)
- Includes conversation history automatically
- Falls back gracefully when context unavailable

**Example:**
```python
response = chatbot.generate_contextual_response("user123", "How am I doing today?")
```

### 3. `generate_personalized_message()`

Generates personalized messages based on recent check-in data (for automated messages).

**Signature:**
```python
def generate_personalized_message(
    user_id: str,
    timeout: Optional[int] = None,
) -> str
```

## Mode Detection

The AI system automatically detects the appropriate mode based on user input:

### Mode Types

1. **`chat`** - General conversation, wellness support
2. **`command`** - Explicit command requests (e.g., "add task buy groceries")
3. **`command_with_clarification`** - Ambiguous requests needing clarification

### Detection Logic (`_detect_mode()`)

**Command Mode Triggers:**
- Explicit command keywords: "add task", "create task", "list tasks", etc.
- Direct action verbs: "complete", "delete", "update", "show"

**Clarification Mode Triggers:**
- Very short prompts (≤3 words)
- Minimal commands without details ("add task", "create")
- Question requests with clarification phrases ("can you", "could you")
- Natural language task requests ("I need to buy groceries")

**Chat Mode:**
- Everything else defaults to chat mode

## Context Building

### Context Sources

The AI has access to extensive user context formatted in **natural language** (not JSON):

**IMPORTANT: Feature Enablement**
- The AI is explicitly informed whether check-ins and task management are **enabled** or **disabled** for the user
- If a feature is disabled, the AI is instructed **NOT to mention** that feature (e.g., "check-ins are disabled - do NOT mention check-ins, check-in data, or suggest starting check-ins")
- Context data is only included if the feature is enabled

1. **Feature Availability** (First in context - critical)
   - Check-ins enabled/disabled status
   - Task management enabled/disabled status
   - Explicit instructions about what NOT to mention if disabled

2. **User Profile**
   - Preferred name
   - Active categories/interests
   - Active schedules

3. **Health & Preferences**
   - Health conditions (ADHD, depression, etc.)
   - User notes for AI
   - Encouraging activities
   - Goals

4. **Check-in Data** (ONLY if check-ins are enabled)
   - Recent check-ins (mood, energy, breakfast, teeth brushing)
   - Average mood/energy trends
   - Trend direction (improving/declining/stable)
   - Today's check-in status
   - Recent activity summary
   - Mood trends

5. **Task Data** (ONLY if task management is enabled)
   - Active task count
   - Completed task count
   - Tasks due soon (next 7 days)
   - Task details (title, due date, priority)

6. **Schedule Data**
   - Active schedules with times and days
   - Schedule categories and periods

7. **Conversation History**
   - Recent topics discussed
   - Engagement level
   - Message patterns

8. **Automated Messages**
   - Recent messages sent to user
   - Task reminders received

### Context Format

Context is formatted as **natural language narrative** rather than structured data:

**Example:**
```
IMPORTANT - Feature availability: check-ins are enabled; task management is enabled
The user's preferred name is John
Their interests include: health, wellness, mindfulness
Over the last 5 check-ins:
Their average mood has been 4.1 out of 5
They ate breakfast 3 out of 5 times (60% of the time)
They completed their check-in today at 10:00, reporting that their mood was 4 out of 5 and energy was 3 out of 5
Their task information:
  - They have 3 active tasks
  - They have 1 task due within the next 7 days
    * "Buy groceries", due on 2025-11-05 (high priority)
```

**If features are disabled:**
```
IMPORTANT - Feature availability: check-ins are disabled - do NOT mention check-ins, check-in data, or suggest starting check-ins; task management is disabled - do NOT mention tasks, task creation, or task reminders
The user's preferred name is John
Their interests include: health, wellness, mindfulness
```

This natural language format is easier for language models to understand than structured JSON, and the explicit feature availability ensures the AI doesn't reference features the user hasn't opted into.

## Prompt System

### Prompt Types

The system supports multiple prompt templates:

1. **`wellness`** - Default conversational wellness assistant
2. **`command`** - Command parsing (structured output)
3. **`neurodivergent_support`** - Specialized support for ADHD/depression
4. **`checkin`** - Check-in assistance

### Prompt Customization

Custom prompts can be loaded from `resources/assistant_system_prompt.txt` (controlled by `AI_USE_CUSTOM_PROMPT` config).

**Fallback Hierarchy:**
1. Custom prompt (if enabled and loaded)
2. Built-in template for requested type
3. Default `wellness` prompt

### Command Mode Prompt Format

Command mode uses a **key-value format** (not JSON) for better AI compatibility:

```
ACTION: create_task
TITLE: buy groceries
```

The parser supports multiple formats:
1. Key-value format (preferred)
2. JSON format (legacy support)
3. Natural language (fallback parsing)

## Response Processing

### Post-Processing Steps

1. **Command Extraction** (`_extract_command_from_response()`)
   - For command mode: Extracts clean structured format
   - Handles key-value pairs, JSON, or natural language
   - Removes code fragments and explanations
   - Filters out Python code blocks (```python), imports, function definitions

2. **Smart Truncation** (`_smart_truncate_response()`)
   - Enforces length limits (`AI_MAX_RESPONSE_LENGTH`, `AI_MAX_RESPONSE_WORDS`)
   - Cuts at sentence boundaries when possible
   - Adds ellipsis for incomplete responses

3. **Conversational Enhancement** (`_enhance_conversational_engagement()`)
   - Adds engagement prompts if response lacks them
   - Context-aware prompt selection
   - Only applied to non-command modes

## Caching

### Response Cache

- **Purpose**: Avoid regenerating identical responses
- **Scope**: Cached by prompt + user_id + mode
- **TTL**: 5 minutes (`AI_RESPONSE_CACHE_TTL`)
- **Max Size**: 100 entries
- **Behavior**: 
  - NOT cached for chat mode (allows variation)
  - Cached for command/clarification modes (deterministic)
  - LRU eviction when full

### Context Cache

- **Purpose**: Cache expensive context building
- **TTL**: 5 minutes (`CONTEXT_CACHE_TTL`)
- **Max Size**: 100 entries

## Error Handling & Fallbacks

### Fallback Hierarchy

1. **LM Studio Available** → Generate via API
2. **Connection Test Fails** → Enhanced contextual fallback
3. **API Busy/Timeout** → Contextual fallback with user data
4. **Generation Error** → Contextual fallback

### Contextual Fallback (`_get_contextual_fallback()`)

When LM Studio is unavailable, the system uses intelligent keyword-based responses:

- **Context-Aware**: Uses actual user data when available
- **Supportive**: Asks for information when context missing
- **Specific**: Handles connection errors, work fatigue, mood inquiries
- **Personalized**: Includes user name when available

**Example Fallbacks:**
- Missing context: "I don't have enough information about how you're doing today, but we can figure it out together! How about you tell me about your day so far?"
- Connection error: "I'm having some technical difficulties right now. Could you please try again in a moment?"
- Mood inquiry: Provides actual mood data if available

## Configuration

### Key Settings (in `core/config.py`)

**Connection:**
- `LM_STUDIO_BASE_URL` - API endpoint (default: `http://localhost:1234/v1`)
- `LM_STUDIO_MODEL` - Model name (default: `phi-2`)
- `AI_CONNECTION_TEST_TIMEOUT` - Connection test timeout (15s)

**Timeouts:**
- `AI_TIMEOUT_SECONDS` - Default timeout (30s)
- `AI_CONTEXTUAL_RESPONSE_TIMEOUT` - Contextual responses (35s)
- `AI_COMMAND_PARSING_TIMEOUT` - Command parsing (15s)
- `AI_QUICK_RESPONSE_TIMEOUT` - Quick responses (8s)

**Response Limits:**
- `AI_MAX_RESPONSE_LENGTH` - Max characters (1200)
- `AI_MAX_RESPONSE_TOKENS` - Max tokens (300)
- `AI_MIN_RESPONSE_LENGTH` - Min characters (50)

**Temperature (Randomness):**
- `AI_CHAT_TEMPERATURE` - Chat mode (0.7 - conversational)
- `AI_COMMAND_TEMPERATURE` - Command mode (0.0 - deterministic)
- `AI_CLARIFICATION_TEMPERATURE` - Clarification (0.1 - consistent)

**Caching:**
- `AI_CACHE_RESPONSES` - Enable/disable caching (default: true)
- `AI_RESPONSE_CACHE_TTL` - Cache TTL (300s = 5 minutes)

## Concurrency & Threading

### Locking Strategy

- **Per-User Locks**: Each user has a dedicated lock (`_locks_by_user`)
- **Lock Timeout**: 3 seconds max wait
- **Fallback on Busy**: If lock unavailable, uses fallback instead of blocking

This prevents concurrent generation conflicts while allowing better concurrency than a single global lock.

## Data Flow

### Contextual Response Generation Flow

```
User Prompt
    ↓
Build Context (user_context_manager.get_ai_context())
    ↓
Format Context (natural language)
    ↓
Create Prompt (_create_comprehensive_context_prompt())
    ↓
Check Cache (if enabled and not chat mode)
    ↓
Test LM Studio Connection
    ↓
Acquire User Lock (with timeout)
    ↓
Call LM Studio API (_call_lm_studio_api())
    ↓
Post-Process Response
    ├─ Extract command (if command mode)
    ├─ Smart truncation
    └─ Enhance engagement (if chat mode)
    ↓
Cache Response (if not chat mode)
    ↓
Store Conversation Interaction
    ↓
Return Response
```

## Integration Points

### Storage
- Conversation history stored via `store_chat_interaction()`
- Context data loaded via `get_user_data()`, `get_recent_checkins()`, etc.

### Command Parsing
- Command responses parsed by `communication/message_processing/command_parser.py`
- Supports key-value, JSON, and natural language formats

### User Context
- Context built by `user/context_manager.py`
- Includes profile, activity, preferences, mood trends, conversation history

## Best Practices

1. **Use `generate_contextual_response()`** for user-facing interactions - it provides better personalization
2. **Use `generate_response()`** for simple, non-contextual needs (e.g., testing)
3. **Don't bypass mode detection** unless you have a specific reason - auto-detection is robust
4. **Handle fallbacks gracefully** - the system will return fallback responses when LM Studio is unavailable
5. **Respect timeouts** - use appropriate timeout for the use case (quick vs. contextual)
6. **Cache appropriately** - command mode benefits from caching, chat mode should vary

## Testing

AI functionality tests are in `tests/ai/`:

- Run: `python tests/ai/run_ai_functionality_tests.py`
- Tests validate response quality, context usage, mode detection, and error handling
- Results: `tests/ai/results/ai_functionality_test_results_latest.md`

## Troubleshooting

### LM Studio Not Available
- Check if LM Studio is running on configured port
- Verify `LM_STUDIO_BASE_URL` in config
- System will use fallbacks automatically

### Slow Responses
- Check timeout settings
- Verify context isn't too large (natural language context is verbose)
- Consider caching for deterministic responses

### Poor Response Quality
- Check prompt customization (`resources/assistant_system_prompt.txt`)
- Verify context includes relevant data
- Review prompt templates in `ai/prompt_manager.py`
- Check if AI is fabricating data (run AI functionality tests)
- Verify responses match prompts (run AI functionality tests)

### Response Truncation
- Check `max_tokens` in prompt templates (`ai/prompt_manager.py`)
- Verify `AI_MAX_RESPONSE_TOKENS` in config
- Model may be stopping early despite token limits

### AI Fabricating Data
- AI may claim check-ins, tasks, or data exist when context shows none
- Context explicitly states "They have not completed any check-ins yet" when no data exists
- Verify context building includes explicit "no data" messages
- Run AI functionality tests to detect this issue (T-4.1)

### AI Referencing Non-existent Context
- AI may reference conversation history or check-ins that don't exist
- Context should explicitly state when features are disabled or data is missing
- Tests validate that AI doesn't make references without actual context

### Context Not Being Used
- Ensure `generate_contextual_response()` is used (not `generate_response()`)
- Check that user_id is valid
- Verify context building isn't failing silently

## Module Reference

### `ai/chatbot.py`
- `AIChatBotSingleton` - Main chatbot class
- `get_ai_chatbot()` - Get singleton instance
- `generate_response()` - Basic response generation
- `generate_contextual_response()` - Context-aware responses
- `_detect_mode()` - Mode detection logic
- `_create_comprehensive_context_prompt()` - Context prompt builder

### `ai/prompt_manager.py`
- `PromptManager` - Prompt template management
- `get_prompt_manager()` - Get singleton instance
- `get_prompt()` - Get prompt for type
- `get_prompt_template()` - Get full template object

### `ai/cache_manager.py`
- `ResponseCache` - Response caching
- `ContextCache` - Context caching
- `get_response_cache()` - Get response cache instance
- `get_context_cache()` - Get context cache instance

### `user/context_manager.py`
- `UserContextManager` - Context building
- `get_ai_context()` - Build comprehensive context
- `format_context_for_ai()` - Format context as string

---

**Note**: This documentation reflects the actual implementation as of 2025-11-01. For specific API details, refer to the code in `ai/` directory.

