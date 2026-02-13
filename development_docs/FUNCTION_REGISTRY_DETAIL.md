# Function Registry - MHM Project

> **File**: `development_docs/FUNCTION_REGISTRY_DETAIL.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-02-12 23:52:39
> **Source**: `python development_tools/generate_function_registry.py` - Function Registry Generator
> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete registry of all functions and classes in the MHM codebase  
> **Status**: **ACTIVE** - Auto-generated from codebase analysis with template enhancement

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](../TODO.md) for current documentation priorities**

## Overview

### **Function Documentation Coverage: 95.9% [OK] COMPLETED**
- **Files Scanned**: 110
- **Functions Found**: 1573
- **Methods Found**: 1151
- **Classes Found**: 154
- **Total Items**: 2724
- **Functions Documented**: 1502
- **Methods Documented**: 1111
- **Classes Documented**: 120
- **Total Documented**: 2613
- **Template-Generated**: 4
- **Last Updated**: 2026-02-12

**Status**: [OK] **EXCELLENT** - All functions have proper documentation

**Template Enhancement**: This registry now includes automatic template generation for:
- **Auto-generated Qt functions** (qtTrId, setupUi, retranslateUi)
- **Test functions** (with scenario-based descriptions)
- **Special Python methods** (__init__, __new__, __post_init__, etc.)
- **Constructor methods** and **main functions**

**Note**: This registry is automatically generated from the actual codebase. Functions without docstrings are marked as needing documentation. Template-generated documentation is applied to improve coverage.

## Function Categories

### **Core System Functions** (571)
Core system utilities, configuration, error handling, and data management functions.

### **Communication Functions** (410)
Bot implementations, channel management, and communication utilities.

### **User Interface Functions** (411)
UI dialogs, widgets, and user interaction functions.

### **User Management Functions** (32)
User context, preferences, and data management functions.

### **Task Management Functions** (21)
Task management and scheduling functions.

### **Test Functions** (0)
Test functions and testing utilities.

## Module Organization

### `ai/` - Unknown Directory

#### `ai/__init__.py`

#### `ai/cache_manager.py`
**Functions:**
- [OK] `__init__(self, max_size, ttl)` - Initialize the response cache
- [OK] `__init__(self, ttl)` - Initialize the context cache
- [OK] `_cleanup_lru(self)` - Remove least recently used items
- [OK] `_generate_key(self, prompt, user_id, prompt_type)` - Generate cache key from prompt, user context, and prompt type
- [OK] `_remove_entry(self, key)` - Remove an entry from the cache
- [OK] `clear(self)` - Clear all cached responses
- [OK] `clear(self)` - Clear all cached contexts
- [OK] `clear_expired(self)` - Remove all expired entries from the cache
- [OK] `clear_expired(self)` - Remove all expired contexts
- [OK] `get(self, prompt, user_id, prompt_type)` - Get cached response if available and not expired
- [OK] `get(self, user_id)` - Get cached context for a user
- [OK] `get_context_cache()` - Get the global context cache instance
- [OK] `get_entries_by_type(self, prompt_type)` - Get all cache entries for a specific prompt type
- [OK] `get_response_cache()` - Get the global response cache instance
- [OK] `get_stats(self)` - Get cache statistics
- [OK] `remove_entries_by_type(self, prompt_type)` - Remove all cache entries for a specific prompt type
- [OK] `remove_user_entries(self, user_id)` - Remove all cache entries for a specific user
- [OK] `set(self, prompt, response, user_id, prompt_type, metadata)` - Cache a response
- [OK] `set(self, user_id, context)` - Cache context for a user
**Classes:**
- [OK] `CacheEntry` - Entry in the response cache
- [OK] `ContextCache` - Cache for user context information
  - [OK] `ContextCache.__init__(self, ttl)` - Initialize the context cache
  - [OK] `ContextCache.clear(self)` - Clear all cached contexts
  - [OK] `ContextCache.clear_expired(self)` - Remove all expired contexts
  - [OK] `ContextCache.get(self, user_id)` - Get cached context for a user
  - [OK] `ContextCache.set(self, user_id, context)` - Cache context for a user
- [OK] `ResponseCache` - Simple in-memory cache for AI responses to avoid repeated calculations
  - [OK] `ResponseCache.__init__(self, max_size, ttl)` - Initialize the response cache
  - [OK] `ResponseCache._cleanup_lru(self)` - Remove least recently used items
  - [OK] `ResponseCache._generate_key(self, prompt, user_id, prompt_type)` - Generate cache key from prompt, user context, and prompt type
  - [OK] `ResponseCache._remove_entry(self, key)` - Remove an entry from the cache
  - [OK] `ResponseCache.clear(self)` - Clear all cached responses
  - [OK] `ResponseCache.clear_expired(self)` - Remove all expired entries from the cache
  - [OK] `ResponseCache.get(self, prompt, user_id, prompt_type)` - Get cached response if available and not expired
  - [OK] `ResponseCache.get_entries_by_type(self, prompt_type)` - Get all cache entries for a specific prompt type
  - [OK] `ResponseCache.get_stats(self)` - Get cache statistics
  - [OK] `ResponseCache.remove_entries_by_type(self, prompt_type)` - Remove all cache entries for a specific prompt type
  - [OK] `ResponseCache.remove_user_entries(self, user_id)` - Remove all cache entries for a specific user
  - [OK] `ResponseCache.set(self, prompt, response, user_id, prompt_type, metadata)` - Cache a response

#### `ai/chatbot.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the object.
- [OK] `__new__(cls)` - Create a new instance.
- [OK] `_call_lm_studio_api(self, messages, max_tokens, temperature, timeout)` - Make an API call to LM Studio using OpenAI-compatible format.
- [OK] `_clean_system_prompt_leaks(self, response)` - Remove any leaked system prompt metadata from AI responses.
Prevents meta-text like "User Context:", "IMPORTANT - Feature availability:" from appearing in user-facing responses.
- [OK] `_create_command_parsing_prompt(self, user_prompt)` - Create a prompt instructing the model to return strict JSON.

If clarification is True, the prompt encourages the model to ask for
clarification when the user's request is ambiguous or incomplete.
- [OK] `_create_comprehensive_context_prompt(self, user_id, user_prompt)` - Create a comprehensive context prompt with all user data for LM Studio.
- [OK] `_detect_mode(self, user_prompt)` - Detect whether the prompt is a command or a chat query.
- [OK] `_detect_resource_constraints(self)` - Detect if system is resource-constrained.
- [OK] `_enhance_conversational_engagement(self, response)` - Enhance response to ensure good conversational engagement.
Adds engagement prompts if the response doesn't already have them.
- [OK] `_extract_command_from_response(self, response)` - Extract command structure from command mode responses.
Handles multiple formats: JSON, key-value pairs (ACTION: ...), or natural language.
Returns clean structured format for parser.
- [OK] `_get_adaptive_timeout(self, base_timeout)` - Get adaptive timeout based on system resources.
- [OK] `_get_contextual_fallback(self, user_prompt, user_id)` - Provide contextually aware fallback responses based on user data and prompt analysis.
Now actually analyzes user's check-in data for meaningful responses.
- [OK] `_get_fallback_personalized_message(self, user_id)` - Provide fallback personalized messages when AI model is not available.
- [OK] `_get_fallback_response(self, user_prompt)` - Legacy fallback method for backwards compatibility.
- [OK] `_make_cache_key_inputs(self, mode, user_prompt, user_id)` - Create consistent cache key inputs with validation.

Returns:
    tuple: (user_prompt, user_id, mode)
- [OK] `_optimize_prompt(self, user_prompt, context)` - Create optimized messages array for LM Studio API.
- [OK] `_smart_truncate_response(self, text, max_chars, max_words)` - Smartly truncate response to avoid mid-sentence cuts.
Supports both character and word limits.
- [OK] `_test_lm_studio_connection(self)` - Test connection to LM Studio server with validation.

Returns:
    None: Always returns None
- [OK] `generate_contextual_response(self, user_id, user_prompt, timeout)` - Generate a context-aware response using comprehensive user data.
Integrates with existing UserContext and UserPreferences systems.
- [OK] `generate_personalized_message(self, user_id, timeout)` - Generate a personalized message by examining the user's recent responses
(check-in data). Uses longer timeout since this is not real-time.
- [OK] `generate_quick_response(self, user_prompt, user_id)` - Generate a quick response for real-time chat (Discord, etc.).
Uses shorter timeout optimized for responsiveness.
- [OK] `generate_response(self, user_prompt, timeout, user_id, mode)` - Generate a basic AI response from user_prompt, using LM Studio API.
Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
- [OK] `get_ai_chatbot()` - Return the shared AIChatBot instance.
- [OK] `get_ai_status(self)` - Get detailed status information about the AI system.
- [OK] `is_ai_available(self)` - Check if the AI model is available and functional.
- [OK] `reload_system_prompt(self)` - Reload the system prompt from file (useful for development and testing).
- [OK] `test_system_prompt_integration(self)` - Test the system prompt integration and return status information.
**Classes:**
- [OK] `AIChatBotSingleton` - A Singleton container for LM Studio API client.
  - [OK] `AIChatBotSingleton.__init__(self)` - Initialize the object.
  - [OK] `AIChatBotSingleton.__new__(cls)` - Create a new instance.
  - [OK] `AIChatBotSingleton._call_lm_studio_api(self, messages, max_tokens, temperature, timeout)` - Make an API call to LM Studio using OpenAI-compatible format.
  - [OK] `AIChatBotSingleton._clean_system_prompt_leaks(self, response)` - Remove any leaked system prompt metadata from AI responses.
Prevents meta-text like "User Context:", "IMPORTANT - Feature availability:" from appearing in user-facing responses.
  - [OK] `AIChatBotSingleton._create_command_parsing_prompt(self, user_prompt)` - Create a prompt instructing the model to return strict JSON.

If clarification is True, the prompt encourages the model to ask for
clarification when the user's request is ambiguous or incomplete.
  - [OK] `AIChatBotSingleton._create_comprehensive_context_prompt(self, user_id, user_prompt)` - Create a comprehensive context prompt with all user data for LM Studio.
  - [OK] `AIChatBotSingleton._detect_mode(self, user_prompt)` - Detect whether the prompt is a command or a chat query.
  - [OK] `AIChatBotSingleton._detect_resource_constraints(self)` - Detect if system is resource-constrained.
  - [OK] `AIChatBotSingleton._enhance_conversational_engagement(self, response)` - Enhance response to ensure good conversational engagement.
Adds engagement prompts if the response doesn't already have them.
  - [OK] `AIChatBotSingleton._extract_command_from_response(self, response)` - Extract command structure from command mode responses.
Handles multiple formats: JSON, key-value pairs (ACTION: ...), or natural language.
Returns clean structured format for parser.
  - [OK] `AIChatBotSingleton._get_adaptive_timeout(self, base_timeout)` - Get adaptive timeout based on system resources.
  - [OK] `AIChatBotSingleton._get_contextual_fallback(self, user_prompt, user_id)` - Provide contextually aware fallback responses based on user data and prompt analysis.
Now actually analyzes user's check-in data for meaningful responses.
  - [OK] `AIChatBotSingleton._get_fallback_personalized_message(self, user_id)` - Provide fallback personalized messages when AI model is not available.
  - [OK] `AIChatBotSingleton._get_fallback_response(self, user_prompt)` - Legacy fallback method for backwards compatibility.
  - [OK] `AIChatBotSingleton._make_cache_key_inputs(self, mode, user_prompt, user_id)` - Create consistent cache key inputs with validation.

Returns:
    tuple: (user_prompt, user_id, mode)
  - [OK] `AIChatBotSingleton._optimize_prompt(self, user_prompt, context)` - Create optimized messages array for LM Studio API.
  - [OK] `AIChatBotSingleton._smart_truncate_response(self, text, max_chars, max_words)` - Smartly truncate response to avoid mid-sentence cuts.
Supports both character and word limits.
  - [OK] `AIChatBotSingleton._test_lm_studio_connection(self)` - Test connection to LM Studio server with validation.

Returns:
    None: Always returns None
  - [OK] `AIChatBotSingleton.generate_contextual_response(self, user_id, user_prompt, timeout)` - Generate a context-aware response using comprehensive user data.
Integrates with existing UserContext and UserPreferences systems.
  - [OK] `AIChatBotSingleton.generate_personalized_message(self, user_id, timeout)` - Generate a personalized message by examining the user's recent responses
(check-in data). Uses longer timeout since this is not real-time.
  - [OK] `AIChatBotSingleton.generate_quick_response(self, user_prompt, user_id)` - Generate a quick response for real-time chat (Discord, etc.).
Uses shorter timeout optimized for responsiveness.
  - [OK] `AIChatBotSingleton.generate_response(self, user_prompt, timeout, user_id, mode)` - Generate a basic AI response from user_prompt, using LM Studio API.
Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
  - [OK] `AIChatBotSingleton.get_ai_status(self)` - Get detailed status information about the AI system.
  - [OK] `AIChatBotSingleton.is_ai_available(self)` - Check if the AI model is available and functional.
  - [OK] `AIChatBotSingleton.reload_system_prompt(self)` - Reload the system prompt from file (useful for development and testing).
  - [OK] `AIChatBotSingleton.test_system_prompt_integration(self)` - Test the system prompt integration and return status information.

#### `ai/context_builder.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the context builder
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `_calculate_wellness_score(self, breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate)` - Calculate overall wellness score (0-100)
- [OK] `_determine_trend(self, values)` - Determine trend from a list of values
- [OK] `_generate_insights(self, breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate, mood_trend, energy_trend)` - Generate insights from analyzed data
- [OK] `analyze_context(self, context_data)` - Analyze context data to extract insights

Args:
    context_data: Context data to analyze

Returns:
    ContextAnalysis with insights and trends
- [OK] `build_user_context(self, user_id, include_conversation_history)` - Build comprehensive context for a user

Args:
    user_id: User ID to build context for
    include_conversation_history: Whether to include conversation history

Returns:
    ContextData object with all available context
- [OK] `create_checkin_context(self, user_id, checkin_type)` - Create context specifically for check-in interactions

Args:
    user_id: User ID
    checkin_type: Type of check-in (daily, weekly, etc.)

Returns:
    Check-in specific context string
- [OK] `create_context_prompt(self, context_data, analysis)` - Create a context prompt string for AI interactions

Args:
    context_data: User context data
    analysis: Optional pre-computed analysis

Returns:
    Formatted context prompt string
- [OK] `create_task_context(self, user_id, task_description)` - Create context specifically for task-related interactions

Args:
    user_id: User ID
    task_description: Description of the task

Returns:
    Task-specific context string
- [OK] `get_context_builder()` - Get the global context builder instance
**Classes:**
- [OK] `ContextAnalysis` - Analysis results from context data
  - [OK] `ContextAnalysis.__post_init__(self)` - Post-initialization setup
- [OK] `ContextBuilder` - Builds comprehensive context for AI interactions
  - [OK] `ContextBuilder.__init__(self)` - Initialize the context builder
  - [OK] `ContextBuilder._calculate_wellness_score(self, breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate)` - Calculate overall wellness score (0-100)
  - [OK] `ContextBuilder._determine_trend(self, values)` - Determine trend from a list of values
  - [OK] `ContextBuilder._generate_insights(self, breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate, mood_trend, energy_trend)` - Generate insights from analyzed data
  - [OK] `ContextBuilder.analyze_context(self, context_data)` - Analyze context data to extract insights

Args:
    context_data: Context data to analyze

Returns:
    ContextAnalysis with insights and trends
  - [OK] `ContextBuilder.build_user_context(self, user_id, include_conversation_history)` - Build comprehensive context for a user

Args:
    user_id: User ID to build context for
    include_conversation_history: Whether to include conversation history

Returns:
    ContextData object with all available context
  - [OK] `ContextBuilder.create_checkin_context(self, user_id, checkin_type)` - Create context specifically for check-in interactions

Args:
    user_id: User ID
    checkin_type: Type of check-in (daily, weekly, etc.)

Returns:
    Check-in specific context string
  - [OK] `ContextBuilder.create_context_prompt(self, context_data, analysis)` - Create a context prompt string for AI interactions

Args:
    context_data: User context data
    analysis: Optional pre-computed analysis

Returns:
    Formatted context prompt string
  - [OK] `ContextBuilder.create_task_context(self, user_id, task_description)` - Create context specifically for task-related interactions

Args:
    user_id: User ID
    task_description: Description of the task

Returns:
    Task-specific context string
- [OK] `ContextData` - Structured context data for AI interactions
  - [OK] `ContextData.__post_init__(self)` - Post-initialization setup

#### `ai/conversation_history.py`
**Functions:**
- [OK] `__init__(self, max_sessions_per_user, max_messages_per_session)` - Initialize the conversation history manager
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `_cleanup_old_sessions(self, user_id)` - Clean up old sessions for a user
- [OK] `add_message(self, user_id, role, content, metadata)` - Add a message to the active conversation session

Args:
    user_id: User ID
    role: Message role ("user" or "assistant")
    content: Message content
    metadata: Optional message metadata

Returns:
    True if message was added successfully
- [OK] `clear_history(self, user_id)` - Clear all conversation history for a user

Args:
    user_id: User ID

Returns:
    True if history was cleared successfully
- [OK] `delete_session(self, user_id, session_id)` - Delete a specific conversation session

Args:
    user_id: User ID
    session_id: Session ID to delete

Returns:
    True if session was deleted successfully
- [OK] `end_session(self, user_id)` - End the active conversation session for a user

Args:
    user_id: User ID

Returns:
    True if session was ended successfully
- [OK] `get_active_session(self, user_id)` - Get the active conversation session for a user

Args:
    user_id: User ID

Returns:
    Active conversation session or None
- [OK] `get_conversation_history()` - Get the global conversation history instance
- [OK] `get_conversation_summary(self, user_id, session_id)` - Get a summary of conversation history

Args:
    user_id: User ID
    session_id: Optional specific session ID

Returns:
    Conversation summary string
- [OK] `get_history(self, user_id, limit, include_metadata)` - Get conversation history for a user

Args:
    user_id: User ID
    limit: Maximum number of messages to return
    include_metadata: Whether to include message metadata

Returns:
    List of conversation messages
- [OK] `get_recent_messages(self, user_id, count)` - Get recent conversation messages for a user

Args:
    user_id: User ID
    count: Number of recent messages to return

Returns:
    List of recent conversation messages
- [OK] `get_session_messages(self, user_id, session_id)` - Get all messages from a specific session

Args:
    user_id: User ID
    session_id: Session ID

Returns:
    List of messages in the session
- [OK] `get_statistics(self, user_id)` - Get conversation statistics for a user

Args:
    user_id: User ID

Returns:
    Dictionary with conversation statistics
- [OK] `start_session(self, user_id, session_id)` - Start a new conversation session

Args:
    user_id: User ID
    session_id: Optional custom session ID

Returns:
    Session ID
**Classes:**
- [OK] `ConversationHistory` - Manages conversation history for AI interactions
  - [OK] `ConversationHistory.__init__(self, max_sessions_per_user, max_messages_per_session)` - Initialize the conversation history manager
  - [OK] `ConversationHistory._cleanup_old_sessions(self, user_id)` - Clean up old sessions for a user
  - [OK] `ConversationHistory.add_message(self, user_id, role, content, metadata)` - Add a message to the active conversation session

Args:
    user_id: User ID
    role: Message role ("user" or "assistant")
    content: Message content
    metadata: Optional message metadata

Returns:
    True if message was added successfully
  - [OK] `ConversationHistory.clear_history(self, user_id)` - Clear all conversation history for a user

Args:
    user_id: User ID

Returns:
    True if history was cleared successfully
  - [OK] `ConversationHistory.delete_session(self, user_id, session_id)` - Delete a specific conversation session

Args:
    user_id: User ID
    session_id: Session ID to delete

Returns:
    True if session was deleted successfully
  - [OK] `ConversationHistory.end_session(self, user_id)` - End the active conversation session for a user

Args:
    user_id: User ID

Returns:
    True if session was ended successfully
  - [OK] `ConversationHistory.get_active_session(self, user_id)` - Get the active conversation session for a user

Args:
    user_id: User ID

Returns:
    Active conversation session or None
  - [OK] `ConversationHistory.get_conversation_summary(self, user_id, session_id)` - Get a summary of conversation history

Args:
    user_id: User ID
    session_id: Optional specific session ID

Returns:
    Conversation summary string
  - [OK] `ConversationHistory.get_history(self, user_id, limit, include_metadata)` - Get conversation history for a user

Args:
    user_id: User ID
    limit: Maximum number of messages to return
    include_metadata: Whether to include message metadata

Returns:
    List of conversation messages
  - [OK] `ConversationHistory.get_recent_messages(self, user_id, count)` - Get recent conversation messages for a user

Args:
    user_id: User ID
    count: Number of recent messages to return

Returns:
    List of recent conversation messages
  - [OK] `ConversationHistory.get_session_messages(self, user_id, session_id)` - Get all messages from a specific session

Args:
    user_id: User ID
    session_id: Session ID

Returns:
    List of messages in the session
  - [OK] `ConversationHistory.get_statistics(self, user_id)` - Get conversation statistics for a user

Args:
    user_id: User ID

Returns:
    Dictionary with conversation statistics
  - [OK] `ConversationHistory.start_session(self, user_id, session_id)` - Start a new conversation session

Args:
    user_id: User ID
    session_id: Optional custom session ID

Returns:
    Session ID
- [OK] `ConversationMessage` - A single message in a conversation
  - [OK] `ConversationMessage.__post_init__(self)` - Post-initialization setup
- [OK] `ConversationSession` - A conversation session with multiple messages
  - [OK] `ConversationSession.__post_init__(self)` - Post-initialization setup

#### `ai/lm_studio_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize LM Studio status detector
- [OK] `ensure_lm_studio_ready()` - Ensure LM Studio is ready, attempting automatic model loading if needed
- [OK] `get_lm_studio_manager()` - Get the global LM Studio manager instance
- [OK] `is_lm_studio_ready()` - Check if LM Studio is ready for AI features
- [OK] `is_lm_studio_running(self)` - Check if LM Studio process is running
- [OK] `is_model_loaded(self)` - Check if the configured model is actually loaded (not just available) in LM Studio
- [OK] `is_ready(self)` - Check if LM Studio is ready (server running and model loaded)
- [OK] `is_server_responding(self)` - Check if LM Studio server is responding on the configured port
- [OK] `load_model_automatically(self)` - Automatically load the configured model if server is running but no model is loaded
**Classes:**
- [OK] `LMStudioManager` - Detects LM Studio status and model availability
  - [OK] `LMStudioManager.__init__(self)` - Initialize LM Studio status detector
  - [OK] `LMStudioManager.is_lm_studio_running(self)` - Check if LM Studio process is running
  - [OK] `LMStudioManager.is_model_loaded(self)` - Check if the configured model is actually loaded (not just available) in LM Studio
  - [OK] `LMStudioManager.is_ready(self)` - Check if LM Studio is ready (server running and model loaded)
  - [OK] `LMStudioManager.is_server_responding(self)` - Check if LM Studio server is responding on the configured port
  - [OK] `LMStudioManager.load_model_automatically(self)` - Automatically load the configured model if server is running but no model is loaded

#### `ai/prompt_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the prompt manager
- [OK] `_load_custom_prompt(self)` - Load the custom system prompt from file
- [OK] `add_prompt_template(self, template)` - Add a custom prompt template

Args:
    template: PromptTemplate to add
- [OK] `create_checkin_prompt(self, checkin_type, user_context)` - Create a check-in specific prompt

Args:
    checkin_type: Type of check-in (daily, weekly, etc.)
    user_context: User context information

Returns:
    Check-in specific prompt
- [OK] `create_contextual_prompt(self, base_prompt, context, user_input)` - Create a contextual prompt by combining base prompt, context, and user input

Args:
    base_prompt: Base system prompt
    context: Contextual information
    user_input: User's input

Returns:
    Combined contextual prompt
- [OK] `create_task_prompt(self, task_description, user_context)` - Create a task-specific prompt

Args:
    task_description: Description of the task
    user_context: User context information

Returns:
    Task-specific prompt
- [OK] `custom_prompt_length(self)` - Get the length of the custom prompt.
- [OK] `fallback_prompt_keys(self)` - Get the keys of available fallback prompts.
- [OK] `get_available_prompts(self)` - Get all available prompt types and their descriptions

Returns:
    Dictionary mapping prompt types to descriptions
- [OK] `get_prompt(self, prompt_type)` - Get the appropriate prompt for the given type

Args:
    prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support', etc.)

Returns:
    The prompt string
- [OK] `get_prompt_manager()` - Get the global prompt manager instance
- [OK] `get_prompt_template(self, prompt_type)` - Get the full prompt template for the given type

Args:
    prompt_type: Type of prompt

Returns:
    PromptTemplate object or None if not found
- [OK] `has_custom_prompt(self)` - Check if a custom prompt is loaded.
- [OK] `reload_custom_prompt(self)` - Reload the custom prompt from file (useful for development)
- [OK] `remove_prompt_template(self, prompt_type)` - Remove a custom prompt template

Args:
    prompt_type: Name of the template to remove

Returns:
    True if template was removed, False if not found
**Classes:**
- [OK] `PromptManager` - Manages AI prompts and templates
  - [OK] `PromptManager.__init__(self)` - Initialize the prompt manager
  - [OK] `PromptManager._load_custom_prompt(self)` - Load the custom system prompt from file
  - [OK] `PromptManager.add_prompt_template(self, template)` - Add a custom prompt template

Args:
    template: PromptTemplate to add
  - [OK] `PromptManager.create_checkin_prompt(self, checkin_type, user_context)` - Create a check-in specific prompt

Args:
    checkin_type: Type of check-in (daily, weekly, etc.)
    user_context: User context information

Returns:
    Check-in specific prompt
  - [OK] `PromptManager.create_contextual_prompt(self, base_prompt, context, user_input)` - Create a contextual prompt by combining base prompt, context, and user input

Args:
    base_prompt: Base system prompt
    context: Contextual information
    user_input: User's input

Returns:
    Combined contextual prompt
  - [OK] `PromptManager.create_task_prompt(self, task_description, user_context)` - Create a task-specific prompt

Args:
    task_description: Description of the task
    user_context: User context information

Returns:
    Task-specific prompt
  - [OK] `PromptManager.custom_prompt_length(self)` - Get the length of the custom prompt.
  - [OK] `PromptManager.fallback_prompt_keys(self)` - Get the keys of available fallback prompts.
  - [OK] `PromptManager.get_available_prompts(self)` - Get all available prompt types and their descriptions

Returns:
    Dictionary mapping prompt types to descriptions
  - [OK] `PromptManager.get_prompt(self, prompt_type)` - Get the appropriate prompt for the given type

Args:
    prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support', etc.)

Returns:
    The prompt string
  - [OK] `PromptManager.get_prompt_template(self, prompt_type)` - Get the full prompt template for the given type

Args:
    prompt_type: Type of prompt

Returns:
    PromptTemplate object or None if not found
  - [OK] `PromptManager.has_custom_prompt(self)` - Check if a custom prompt is loaded.
  - [OK] `PromptManager.reload_custom_prompt(self)` - Reload the custom prompt from file (useful for development)
  - [OK] `PromptManager.remove_prompt_template(self, prompt_type)` - Remove a custom prompt template

Args:
    prompt_type: Name of the template to remove

Returns:
    True if template was removed, False if not found
- [OK] `PromptTemplate` - Template for AI prompts

### `communication/` - Communication Channel Implementations

#### `communication/__init__.py`
**Functions:**
- [OK] `__getattr__(name)` - Lazy import handler for items with circular dependencies.

Note: This function intentionally does not use @handle_errors decorator
to avoid circular dependencies with error handling infrastructure.

#### `communication/command_handlers/__init__.py`

#### `communication/command_handlers/account_handler.py`
**Functions:**
- [OK] `_generate_confirmation_code()` - Generate a 6-digit confirmation code
- [OK] `_get_user_id_by_username(self, username)` - Get user ID by username
- [OK] `_handle_check_account_status(self, user_id)` - Check if user has an account linked
- [OK] `_handle_create_account(self, user_id, entities)` - Handle account creation request.

Args:
    user_id: The user's internal ID (if they already have one) or channel identifier
    entities: Command entities containing username and other account data

Returns:
    InteractionResponse with account creation result
- [OK] `_handle_link_account(self, user_id, entities)` - Handle account linking request.

Args:
    user_id: The channel identifier (Discord ID, email, etc.)
    entities: Command entities containing username and confirmation code

Returns:
    InteractionResponse with account linking result
- [OK] `_send_confirmation_code(user_id, confirmation_code, channel_type, channel_identifier)` - Send confirmation code via email (for account linking security).

When linking a Discord account to an existing MHM account, the confirmation code
is sent to the email address associated with the MHM account for security verification.

Args:
    user_id: Internal user ID of the existing MHM account
    confirmation_code: The 6-digit confirmation code
    channel_type: The channel being linked ('discord', 'email', etc.) - used for message context
    channel_identifier: Channel-specific identifier (Discord user ID, etc.) - used for message context only
- [OK] `_username_exists(self, username)` - Check if a username already exists in the system
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent
- [OK] `get_examples(self)` - Get example commands for account management.
- [OK] `get_help(self)` - Get help text for account management commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle account management interactions
**Classes:**
- [OK] `AccountManagementHandler` - Handler for account management interactions
  - [OK] `AccountManagementHandler._get_user_id_by_username(self, username)` - Get user ID by username
  - [OK] `AccountManagementHandler._handle_check_account_status(self, user_id)` - Check if user has an account linked
  - [OK] `AccountManagementHandler._handle_create_account(self, user_id, entities)` - Handle account creation request.

Args:
    user_id: The user's internal ID (if they already have one) or channel identifier
    entities: Command entities containing username and other account data

Returns:
    InteractionResponse with account creation result
  - [OK] `AccountManagementHandler._handle_link_account(self, user_id, entities)` - Handle account linking request.

Args:
    user_id: The channel identifier (Discord ID, email, etc.)
    entities: Command entities containing username and confirmation code

Returns:
    InteractionResponse with account linking result
  - [OK] `AccountManagementHandler._username_exists(self, username)` - Check if a username already exists in the system
  - [OK] `AccountManagementHandler.can_handle(self, intent)` - Check if this handler can handle the given intent
  - [OK] `AccountManagementHandler.get_examples(self)` - Get example commands for account management.
  - [OK] `AccountManagementHandler.get_help(self)` - Get help text for account management commands.
  - [OK] `AccountManagementHandler.handle(self, user_id, parsed_command)` - Handle account management interactions

#### `communication/command_handlers/analytics_handler.py`
**Functions:**
- [OK] `_build_trend_graph(self, recent_data, value_key, label, max_points)` - Build a simple ASCII trend graph for recent check-in values.
- [OK] `_clean_checkin_label(self, label)` - Remove redundant suffixes from check-in labels.
- [OK] `_extract_checkin_responses(self, checkin, question_keys)` - Extract responses from current check-in records.
- [OK] `_format_basic_analytics_line(self, question)` - Format a single basic analytics line.
- [OK] `_format_checkin_response_value(self, key, value, question_defs)` - Format a check-in response value for display.
- [OK] `_format_numeric_value(self, value)` - Format numeric values with minimal trailing decimals.
- [OK] `_get_checkin_label(self, key, question_defs)` - Get a readable label for a check-in response key.
- [OK] `_get_field_scale(self, field)` - Determine the scale for a field (1-5 scale, or None for other types)

Returns:
    int: Scale value (5 for 1-5 scale fields, None for other types)
- [OK] `_get_ordered_checkin_keys(self, checkin, responses)` - Preserve original check-in order when available.
- [OK] `_get_question_scale(self, key, question_defs)` - Return scale max for a question when available.
- [OK] `_handle_checkin_analysis(self, user_id, entities)` - Show comprehensive check-in response analysis
- [OK] `_handle_checkin_history(self, user_id, entities)` - Show check-in history
- [OK] `_handle_completion_rate(self, user_id, entities)` - Show completion rate
- [OK] `_handle_energy_trends(self, user_id, entities)` - Show energy trends analysis
- [OK] `_handle_habit_analysis(self, user_id, entities)` - Show habit analysis
- [OK] `_handle_mood_trends(self, user_id, entities)` - Show mood trends analysis
- [OK] `_handle_quant_summary(self, user_id, entities)` - Show per-field quantitative summaries for opted-in fields.
- [OK] `_handle_show_analytics(self, user_id, entities)` - Show comprehensive analytics overview
- [OK] `_handle_sleep_analysis(self, user_id, entities)` - Show sleep analysis
- [OK] `_handle_task_analytics(self, user_id, entities)` - Show comprehensive task analytics and insights
- [OK] `_handle_task_stats(self, user_id, entities)` - Show detailed task statistics
- [OK] `_handle_wellness_score(self, user_id, entities)` - Show wellness score
- [OK] `_truncate_response(self, response, max_length)` - Truncate response to fit Discord message limits
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for analytics.
- [OK] `get_help(self)` - Get help text for analytics commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle analytics and insights interactions.
**Classes:**
- [OK] `AnalyticsHandler` - Handler for analytics and insights interactions
  - [OK] `AnalyticsHandler._build_trend_graph(self, recent_data, value_key, label, max_points)` - Build a simple ASCII trend graph for recent check-in values.
  - [OK] `AnalyticsHandler._clean_checkin_label(self, label)` - Remove redundant suffixes from check-in labels.
  - [OK] `AnalyticsHandler._extract_checkin_responses(self, checkin, question_keys)` - Extract responses from current check-in records.
  - [OK] `AnalyticsHandler._format_basic_analytics_line(self, question)` - Format a single basic analytics line.
  - [OK] `AnalyticsHandler._format_checkin_response_value(self, key, value, question_defs)` - Format a check-in response value for display.
  - [OK] `AnalyticsHandler._format_numeric_value(self, value)` - Format numeric values with minimal trailing decimals.
  - [OK] `AnalyticsHandler._get_checkin_label(self, key, question_defs)` - Get a readable label for a check-in response key.
  - [OK] `AnalyticsHandler._get_field_scale(self, field)` - Determine the scale for a field (1-5 scale, or None for other types)

Returns:
    int: Scale value (5 for 1-5 scale fields, None for other types)
  - [OK] `AnalyticsHandler._get_ordered_checkin_keys(self, checkin, responses)` - Preserve original check-in order when available.
  - [OK] `AnalyticsHandler._get_question_scale(self, key, question_defs)` - Return scale max for a question when available.
  - [OK] `AnalyticsHandler._handle_checkin_analysis(self, user_id, entities)` - Show comprehensive check-in response analysis
  - [OK] `AnalyticsHandler._handle_checkin_history(self, user_id, entities)` - Show check-in history
  - [OK] `AnalyticsHandler._handle_completion_rate(self, user_id, entities)` - Show completion rate
  - [OK] `AnalyticsHandler._handle_energy_trends(self, user_id, entities)` - Show energy trends analysis
  - [OK] `AnalyticsHandler._handle_habit_analysis(self, user_id, entities)` - Show habit analysis
  - [OK] `AnalyticsHandler._handle_mood_trends(self, user_id, entities)` - Show mood trends analysis
  - [OK] `AnalyticsHandler._handle_quant_summary(self, user_id, entities)` - Show per-field quantitative summaries for opted-in fields.
  - [OK] `AnalyticsHandler._handle_show_analytics(self, user_id, entities)` - Show comprehensive analytics overview
  - [OK] `AnalyticsHandler._handle_sleep_analysis(self, user_id, entities)` - Show sleep analysis
  - [OK] `AnalyticsHandler._handle_task_analytics(self, user_id, entities)` - Show comprehensive task analytics and insights
  - [OK] `AnalyticsHandler._handle_task_stats(self, user_id, entities)` - Show detailed task statistics
  - [OK] `AnalyticsHandler._handle_wellness_score(self, user_id, entities)` - Show wellness score
  - [OK] `AnalyticsHandler._truncate_response(self, response, max_length)` - Truncate response to fit Discord message limits
  - [OK] `AnalyticsHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `AnalyticsHandler.get_examples(self)` - Get example commands for analytics.
  - [OK] `AnalyticsHandler.get_help(self)` - Get help text for analytics commands.
  - [OK] `AnalyticsHandler.handle(self, user_id, parsed_command)` - Handle analytics and insights interactions.

#### `communication/command_handlers/base_handler.py`
**Functions:**
- [OK] `_create_error_response(self, error_message, user_id)` - Create a standardized error response with validation.

Args:
    error_message: The error message to include
    user_id: Optional user ID for logging

Returns:
    InteractionResponse: Error response, or None if inputs are invalid
- [OK] `_validate_parsed_command(self, parsed_command)` - Validate that parsed command is properly formatted with enhanced validation.

Returns:
    bool: True if valid, False otherwise
- [OK] `_validate_user_id(self, user_id)` - Validate that user ID is properly formatted with enhanced validation.

Returns:
    bool: True if valid, False otherwise
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.

Args:
    intent: The intent string to check (e.g., 'create_task', 'show_profile')

Returns:
    bool: True if can handle, False otherwise
- [OK] `get_examples(self)` - Get example commands for this handler with validation.

Returns:
    List[str]: Example commands, empty list if failed
- [OK] `get_help(self)` - Get help text for this handler with validation.

Returns:
    str: Help text, default if failed
- [OK] `handle(self, user_id, parsed_command)` - Handle the interaction and return a response with validation.

Returns:
    InteractionResponse: Response to the interaction
**Classes:**
- [OK] `InteractionHandler` - Abstract base class for interaction handlers
  - [OK] `InteractionHandler._create_error_response(self, error_message, user_id)` - Create a standardized error response with validation.

Args:
    error_message: The error message to include
    user_id: Optional user ID for logging

Returns:
    InteractionResponse: Error response, or None if inputs are invalid
  - [OK] `InteractionHandler._validate_parsed_command(self, parsed_command)` - Validate that parsed command is properly formatted with enhanced validation.

Returns:
    bool: True if valid, False otherwise
  - [OK] `InteractionHandler._validate_user_id(self, user_id)` - Validate that user ID is properly formatted with enhanced validation.

Returns:
    bool: True if valid, False otherwise
  - [OK] `InteractionHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.

Args:
    intent: The intent string to check (e.g., 'create_task', 'show_profile')

Returns:
    bool: True if can handle, False otherwise
  - [OK] `InteractionHandler.get_examples(self)` - Get example commands for this handler with validation.

Returns:
    List[str]: Example commands, empty list if failed
  - [OK] `InteractionHandler.get_help(self)` - Get help text for this handler with validation.

Returns:
    str: Help text, default if failed
  - [OK] `InteractionHandler.handle(self, user_id, parsed_command)` - Handle the interaction and return a response with validation.

Returns:
    InteractionResponse: Response to the interaction

#### `communication/command_handlers/checkin_handler.py`
**Functions:**
- [OK] `_handle_checkin_status(self, user_id)` - Handle check-in status request
- [OK] `_handle_continue_checkin(self, user_id, entities)` - Handle continuing a check-in
- [OK] `_handle_start_checkin(self, user_id)` - Handle starting a check-in by delegating to conversation manager
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for check-ins.
- [OK] `get_help(self)` - Get help text for check-in commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle check-in interactions.
**Classes:**
- [OK] `CheckinHandler` - Handler for check-in interactions
  - [OK] `CheckinHandler._handle_checkin_status(self, user_id)` - Handle check-in status request
  - [OK] `CheckinHandler._handle_continue_checkin(self, user_id, entities)` - Handle continuing a check-in
  - [OK] `CheckinHandler._handle_start_checkin(self, user_id)` - Handle starting a check-in by delegating to conversation manager
  - [OK] `CheckinHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `CheckinHandler.get_examples(self)` - Get example commands for check-ins.
  - [OK] `CheckinHandler.get_help(self)` - Get help text for check-in commands.
  - [OK] `CheckinHandler.handle(self, user_id, parsed_command)` - Handle check-in interactions.

#### `communication/command_handlers/interaction_handlers.py`
**Functions:**
- [OK] `_handle_commands_list(self, user_id)` - Handle commands list request
- [OK] `_handle_examples(self, user_id, entities)` - Handle examples request
- [OK] `_handle_general_help(self, user_id, entities)` - Handle general help request
- [OK] `_handle_messages(self, user_id)` - Handle messages request with message history and settings
- [OK] `_handle_status(self, user_id)` - Handle status request with detailed system information
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_all_handlers()` - Get all registered handlers
- [OK] `get_examples(self)` - Get example commands for help.
- [OK] `get_help(self)` - Get help text for help commands.
- [OK] `get_interaction_handler(intent)` - Get the appropriate handler for an intent
- [OK] `handle(self, user_id, parsed_command)` - Handle help and command information interactions.
**Classes:**
- [OK] `HelpHandler` - Handler for help and command information
  - [OK] `HelpHandler._handle_commands_list(self, user_id)` - Handle commands list request
  - [OK] `HelpHandler._handle_examples(self, user_id, entities)` - Handle examples request
  - [OK] `HelpHandler._handle_general_help(self, user_id, entities)` - Handle general help request
  - [OK] `HelpHandler._handle_messages(self, user_id)` - Handle messages request with message history and settings
  - [OK] `HelpHandler._handle_status(self, user_id)` - Handle status request with detailed system information
  - [OK] `HelpHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `HelpHandler.get_examples(self)` - Get example commands for help.
  - [OK] `HelpHandler.get_help(self)` - Get help text for help commands.
  - [OK] `HelpHandler.handle(self, user_id, parsed_command)` - Handle help and command information interactions.

#### `communication/command_handlers/notebook_handler.py`
**Functions:**
- [OK] `_format_entry_id(self, entry)` - Format entry ID as short ID (e.g., n3f2a9c - no dash for easier mobile typing).
- [OK] `_format_entry_response(self, entry)` - Formats a single entry for display.
- [OK] `_handle_add_list_item(self, user_id, entities)` - Handle adding item to list.
- [OK] `_handle_add_tags(self, user_id, entities)` - Handle adding tags to entry.
- [OK] `_handle_append_to_entry(self, user_id, entities)` - Handle appending to entry body.
- [OK] `_handle_archive_entry(self, user_id, entities, archived)` - Handle archiving/unarchiving entry.
- [OK] `_handle_create_journal(self, user_id, entities)` - Handle journal entry creation.
- [OK] `_handle_create_list(self, user_id, entities)` - Handle list creation.
- [OK] `_handle_create_note(self, user_id, entities)` - Handle note creation.
- [OK] `_handle_create_quick_note(self, user_id, entities)` - Handle quick note creation - no body text required, automatically grouped as 'Quick Notes'.
- [OK] `_handle_list_archived(self, user_id, entities)` - Handle listing archived entries.
- [OK] `_handle_list_by_group(self, user_id, entities)` - Handle listing entries by group.
- [OK] `_handle_list_by_tag(self, user_id, entities)` - Handle listing entries by tag.
- [OK] `_handle_list_inbox(self, user_id, entities)` - Handle listing inbox entries.
- [OK] `_handle_list_pinned(self, user_id, entities)` - Handle listing pinned entries.
- [OK] `_handle_list_recent(self, user_id, entities, notes_only)` - Handle listing recent entries.
- [OK] `_handle_pin_entry(self, user_id, entities, pinned)` - Handle pinning/unpinning entry.
- [OK] `_handle_remove_list_item(self, user_id, entities)` - Handle removing item from list.
- [OK] `_handle_remove_tags(self, user_id, entities)` - Handle removing tags from entry.
- [OK] `_handle_search_entries(self, user_id, entities)` - Handle searching entries.
- [OK] `_handle_set_entry_body(self, user_id, entities)` - Handle setting entry body.
- [OK] `_handle_set_group(self, user_id, entities)` - Handle setting entry group.
- [OK] `_handle_show_entry(self, user_id, entities)` - Handle showing an entry.
- [OK] `_handle_toggle_list_item_done(self, user_id, entities)` - Handle toggling list item done status.
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for notebook.
- [OK] `get_help(self)` - Get help text for notebook commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle notebook interactions.
**Classes:**
- [OK] `NotebookHandler` - Handler for notebook management interactions.
  - [OK] `NotebookHandler._format_entry_id(self, entry)` - Format entry ID as short ID (e.g., n3f2a9c - no dash for easier mobile typing).
  - [OK] `NotebookHandler._format_entry_response(self, entry)` - Formats a single entry for display.
  - [OK] `NotebookHandler._handle_add_list_item(self, user_id, entities)` - Handle adding item to list.
  - [OK] `NotebookHandler._handle_add_tags(self, user_id, entities)` - Handle adding tags to entry.
  - [OK] `NotebookHandler._handle_append_to_entry(self, user_id, entities)` - Handle appending to entry body.
  - [OK] `NotebookHandler._handle_archive_entry(self, user_id, entities, archived)` - Handle archiving/unarchiving entry.
  - [OK] `NotebookHandler._handle_create_journal(self, user_id, entities)` - Handle journal entry creation.
  - [OK] `NotebookHandler._handle_create_list(self, user_id, entities)` - Handle list creation.
  - [OK] `NotebookHandler._handle_create_note(self, user_id, entities)` - Handle note creation.
  - [OK] `NotebookHandler._handle_create_quick_note(self, user_id, entities)` - Handle quick note creation - no body text required, automatically grouped as 'Quick Notes'.
  - [OK] `NotebookHandler._handle_list_archived(self, user_id, entities)` - Handle listing archived entries.
  - [OK] `NotebookHandler._handle_list_by_group(self, user_id, entities)` - Handle listing entries by group.
  - [OK] `NotebookHandler._handle_list_by_tag(self, user_id, entities)` - Handle listing entries by tag.
  - [OK] `NotebookHandler._handle_list_inbox(self, user_id, entities)` - Handle listing inbox entries.
  - [OK] `NotebookHandler._handle_list_pinned(self, user_id, entities)` - Handle listing pinned entries.
  - [OK] `NotebookHandler._handle_list_recent(self, user_id, entities, notes_only)` - Handle listing recent entries.
  - [OK] `NotebookHandler._handle_pin_entry(self, user_id, entities, pinned)` - Handle pinning/unpinning entry.
  - [OK] `NotebookHandler._handle_remove_list_item(self, user_id, entities)` - Handle removing item from list.
  - [OK] `NotebookHandler._handle_remove_tags(self, user_id, entities)` - Handle removing tags from entry.
  - [OK] `NotebookHandler._handle_search_entries(self, user_id, entities)` - Handle searching entries.
  - [OK] `NotebookHandler._handle_set_entry_body(self, user_id, entities)` - Handle setting entry body.
  - [OK] `NotebookHandler._handle_set_group(self, user_id, entities)` - Handle setting entry group.
  - [OK] `NotebookHandler._handle_show_entry(self, user_id, entities)` - Handle showing an entry.
  - [OK] `NotebookHandler._handle_toggle_list_item_done(self, user_id, entities)` - Handle toggling list item done status.
  - [OK] `NotebookHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `NotebookHandler.get_examples(self)` - Get example commands for notebook.
  - [OK] `NotebookHandler.get_help(self)` - Get help text for notebook commands.
  - [OK] `NotebookHandler.handle(self, user_id, parsed_command)` - Handle notebook interactions.

#### `communication/command_handlers/profile_handler.py`
**Functions:**
- [OK] `_format_profile_text(self, account_data, context_data, preferences_data)` - Create a clean, readable profile string for channels like Discord.
- [OK] `_handle_profile_stats(self, user_id)` - Handle profile statistics
- [OK] `_handle_show_profile(self, user_id)` - Handle showing user profile with comprehensive personalization data
- [OK] `_handle_update_profile(self, user_id, entities)` - Handle comprehensive profile updates
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for profile management.
- [OK] `get_help(self)` - Get help text for profile management commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle profile management interactions.
**Classes:**
- [OK] `ProfileHandler` - Handler for profile management interactions
  - [OK] `ProfileHandler._format_profile_text(self, account_data, context_data, preferences_data)` - Create a clean, readable profile string for channels like Discord.
  - [OK] `ProfileHandler._handle_profile_stats(self, user_id)` - Handle profile statistics
  - [OK] `ProfileHandler._handle_show_profile(self, user_id)` - Handle showing user profile with comprehensive personalization data
  - [OK] `ProfileHandler._handle_update_profile(self, user_id, entities)` - Handle comprehensive profile updates
  - [OK] `ProfileHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `ProfileHandler.get_examples(self)` - Get example commands for profile management.
  - [OK] `ProfileHandler.get_help(self)` - Get help text for profile management commands.
  - [OK] `ProfileHandler.handle(self, user_id, parsed_command)` - Handle profile management interactions.

#### `communication/command_handlers/schedule_handler.py`
**Functions:**
- [OK] `_handle_add_schedule_period(self, user_id, entities)` - Add a new schedule period with enhanced options
- [OK] `_handle_edit_schedule_period(self, user_id, entities)` - Edit an existing schedule period with enhanced options
- [OK] `_handle_schedule_status(self, user_id, entities)` - Show status of schedules
- [OK] `_handle_show_schedule(self, user_id, entities)` - Show schedule for a specific category or all categories
- [OK] `_handle_update_schedule(self, user_id, entities)` - Update schedule settings
- [OK] `_normalize_time_string_to_12h(self, time_str)` - Normalize common user-provided time strings to a consistent 12-hour format.

This is NOT timestamp handling — it is schedule time-of-day formatting
for user-facing text.

Accepted inputs:
- "9am", "9 am"
- "09:00", "9:00"
- "21:30"
- "9"

Output examples:
- "9 AM"
- "09:00 AM"
- "09:30 PM"
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for schedule management.
- [OK] `get_help(self)` - Get help text for schedule management commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle schedule management interactions.
**Classes:**
- [OK] `ScheduleManagementHandler` - Handler for schedule management interactions
  - [OK] `ScheduleManagementHandler._handle_add_schedule_period(self, user_id, entities)` - Add a new schedule period with enhanced options
  - [OK] `ScheduleManagementHandler._handle_edit_schedule_period(self, user_id, entities)` - Edit an existing schedule period with enhanced options
  - [OK] `ScheduleManagementHandler._handle_schedule_status(self, user_id, entities)` - Show status of schedules
  - [OK] `ScheduleManagementHandler._handle_show_schedule(self, user_id, entities)` - Show schedule for a specific category or all categories
  - [OK] `ScheduleManagementHandler._handle_update_schedule(self, user_id, entities)` - Update schedule settings
  - [OK] `ScheduleManagementHandler._normalize_time_string_to_12h(self, time_str)` - Normalize common user-provided time strings to a consistent 12-hour format.

This is NOT timestamp handling — it is schedule time-of-day formatting
for user-facing text.

Accepted inputs:
- "9am", "9 am"
- "09:00", "9:00"
- "21:30"
- "9"

Output examples:
- "9 AM"
- "09:00 AM"
- "09:30 PM"
  - [OK] `ScheduleManagementHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `ScheduleManagementHandler.get_examples(self)` - Get example commands for schedule management.
  - [OK] `ScheduleManagementHandler.get_help(self)` - Get help text for schedule management commands.
  - [OK] `ScheduleManagementHandler.handle(self, user_id, parsed_command)` - Handle schedule management interactions.

#### `communication/command_handlers/shared_types.py`
**Classes:**
- [OK] `InteractionResponse` - Response from an interaction handler
- [OK] `ParsedCommand` - Parsed command with intent and entities

#### `communication/command_handlers/task_handler.py`
**Functions:**
- [OK] `_find_task_by_identifier(self, tasks, identifier)` - Find a task by number, name, or task_id.

Shared method to eliminate code duplication. Used by complete, delete, and update handlers.

Args:
    tasks: List of task dictionaries to search
    identifier: Task identifier (number, name, or task_id)

Returns:
    Task dictionary if found, None otherwise
- [OK] `_find_task_by_identifier_for_operation(self, tasks, identifier, context)` - Find a task by number, name, or task_id for a given operation context.
- [OK] `_get_task_candidates(self, tasks, identifier)` - Return candidate tasks matching identifier by id, number, or name.
- [OK] `_handle_complete_task(self, user_id, entities)` - Handle task completion
- [OK] `_handle_complete_task__find_most_urgent_task(self, tasks)` - Find the most urgent task based on priority and due date
- [OK] `_handle_create_task(self, user_id, entities)` - Handle task creation
- [OK] `_handle_create_task__parse_relative_date(self, date_str)` - Convert relative date strings to proper dates
- [OK] `_handle_delete_task(self, user_id, entities)` - Handle task deletion
- [OK] `_handle_list_tasks(self, user_id, entities)` - Handle task listing with enhanced filtering and details
- [OK] `_handle_list_tasks__apply_filters(self, user_id, tasks, filter_type, priority_filter, tag_filter)` - Apply filters to tasks and return filtered list.
- [OK] `_handle_list_tasks__build_filter_info(self, filter_type, priority_filter, tag_filter)` - Build filter information list.
- [OK] `_handle_list_tasks__build_response(self, task_list, filter_info, total_tasks)` - Build the main task list response.
- [OK] `_handle_list_tasks__create_rich_data(self, filter_info, tasks)` - Create rich data for Discord embeds.
- [OK] `_handle_list_tasks__format_due_date(self, due_date)` - Format due date with urgency indicator.
- [OK] `_handle_list_tasks__format_list(self, tasks)` - Format task list with enhanced details.
- [OK] `_handle_list_tasks__generate_suggestions(self, tasks, filter_info)` - Generate contextual suggestions based on current state.
- [OK] `_handle_list_tasks__get_suggestion(self, tasks)` - Get contextual show suggestion based on task analysis.
- [OK] `_handle_list_tasks__no_tasks_response(self, filter_type, priority_filter, tag_filter)` - Get appropriate response when no tasks match filters.
- [OK] `_handle_list_tasks__sort_tasks(self, tasks)` - Sort tasks by priority and due date.
- [OK] `_handle_task_stats(self, user_id, entities)` - Handle task statistics with dynamic time periods
- [OK] `_handle_update_task(self, user_id, entities)` - Handle task updates
- [OK] `_parse_time_string(self, time_str)` - Parse time string to HH:MM format
- [OK] `can_handle(self, intent)` - Check if this handler can handle the given intent.
- [OK] `get_examples(self)` - Get example commands for task management.
- [OK] `get_help(self)` - Get help text for task management commands.
- [OK] `handle(self, user_id, parsed_command)` - Handle task management interactions.
**Classes:**
- [OK] `TaskManagementHandler` - Handler for task management interactions
  - [OK] `TaskManagementHandler._find_task_by_identifier(self, tasks, identifier)` - Find a task by number, name, or task_id.

Shared method to eliminate code duplication. Used by complete, delete, and update handlers.

Args:
    tasks: List of task dictionaries to search
    identifier: Task identifier (number, name, or task_id)

Returns:
    Task dictionary if found, None otherwise
  - [OK] `TaskManagementHandler._find_task_by_identifier_for_operation(self, tasks, identifier, context)` - Find a task by number, name, or task_id for a given operation context.
  - [OK] `TaskManagementHandler._get_task_candidates(self, tasks, identifier)` - Return candidate tasks matching identifier by id, number, or name.
  - [OK] `TaskManagementHandler._handle_complete_task(self, user_id, entities)` - Handle task completion
  - [OK] `TaskManagementHandler._handle_complete_task__find_most_urgent_task(self, tasks)` - Find the most urgent task based on priority and due date
  - [OK] `TaskManagementHandler._handle_create_task(self, user_id, entities)` - Handle task creation
  - [OK] `TaskManagementHandler._handle_create_task__parse_relative_date(self, date_str)` - Convert relative date strings to proper dates
  - [OK] `TaskManagementHandler._handle_delete_task(self, user_id, entities)` - Handle task deletion
  - [OK] `TaskManagementHandler._handle_list_tasks(self, user_id, entities)` - Handle task listing with enhanced filtering and details
  - [OK] `TaskManagementHandler._handle_list_tasks__apply_filters(self, user_id, tasks, filter_type, priority_filter, tag_filter)` - Apply filters to tasks and return filtered list.
  - [OK] `TaskManagementHandler._handle_list_tasks__build_filter_info(self, filter_type, priority_filter, tag_filter)` - Build filter information list.
  - [OK] `TaskManagementHandler._handle_list_tasks__build_response(self, task_list, filter_info, total_tasks)` - Build the main task list response.
  - [OK] `TaskManagementHandler._handle_list_tasks__create_rich_data(self, filter_info, tasks)` - Create rich data for Discord embeds.
  - [OK] `TaskManagementHandler._handle_list_tasks__format_due_date(self, due_date)` - Format due date with urgency indicator.
  - [OK] `TaskManagementHandler._handle_list_tasks__format_list(self, tasks)` - Format task list with enhanced details.
  - [OK] `TaskManagementHandler._handle_list_tasks__generate_suggestions(self, tasks, filter_info)` - Generate contextual suggestions based on current state.
  - [OK] `TaskManagementHandler._handle_list_tasks__get_suggestion(self, tasks)` - Get contextual show suggestion based on task analysis.
  - [OK] `TaskManagementHandler._handle_list_tasks__no_tasks_response(self, filter_type, priority_filter, tag_filter)` - Get appropriate response when no tasks match filters.
  - [OK] `TaskManagementHandler._handle_list_tasks__sort_tasks(self, tasks)` - Sort tasks by priority and due date.
  - [OK] `TaskManagementHandler._handle_task_stats(self, user_id, entities)` - Handle task statistics with dynamic time periods
  - [OK] `TaskManagementHandler._handle_update_task(self, user_id, entities)` - Handle task updates
  - [OK] `TaskManagementHandler._parse_time_string(self, time_str)` - Parse time string to HH:MM format
  - [OK] `TaskManagementHandler.can_handle(self, intent)` - Check if this handler can handle the given intent.
  - [OK] `TaskManagementHandler.get_examples(self)` - Get example commands for task management.
  - [OK] `TaskManagementHandler.get_help(self)` - Get help text for task management commands.
  - [OK] `TaskManagementHandler.handle(self, user_id, parsed_command)` - Handle task management interactions.

#### `communication/communication_channels/__init__.py`

#### `communication/communication_channels/base/base_channel.py`
**Functions:**
- [OK] `__init__(self, config)` - Initialize the object.
- [OK] `__post_init__(self)` - Post-initialization setup.
- [OK] `_set_status(self, status, error_message)` - Internal method to update status
- [OK] `channel_type(self)` - Return whether this channel is sync or async
- [OK] `get_error(self)` - Get last error message
- [OK] `get_status(self)` - Get current channel status
- [OK] `is_ready(self)` - Check if channel is ready to send/receive messages
**Classes:**
- [OK] `BaseChannel` - Abstract base class for all communication channels
  - [OK] `BaseChannel.__init__(self, config)` - Initialize the object.
  - [OK] `BaseChannel._set_status(self, status, error_message)` - Internal method to update status
  - [OK] `BaseChannel.channel_type(self)` - Return whether this channel is sync or async
  - [OK] `BaseChannel.get_error(self)` - Get last error message
  - [OK] `BaseChannel.get_status(self)` - Get current channel status
  - [OK] `BaseChannel.is_ready(self)` - Check if channel is ready to send/receive messages
- [OK] `ChannelConfig` - Configuration for communication channels
  - [OK] `ChannelConfig.__post_init__(self)` - Post-initialization setup.
- [MISSING] `ChannelStatus` - No description
- [MISSING] `ChannelType` - No description

#### `communication/communication_channels/base/command_registry.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the command registry
- [OK] `__init__(self, bot)` - Initialize Discord command registry
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `get_all_commands(self)` - Get all registered commands
- [OK] `get_command(self, command_name)` - Get a command by name or alias
- [OK] `get_command_registry(channel_type, platform_instance)` - Get the appropriate command registry for a channel type
- [OK] `get_enabled_commands(self)` - Get all enabled commands
- [OK] `is_command_registered(self, command_name)` - Check if a command is registered
- [OK] `register_command(self, command_def)` - Register a command definition
- [OK] `register_with_platform(self, command_def)` - Register command with the specific platform (Discord, etc.)
- [OK] `register_with_platform(self, command_def)` - Register command with Discord
- [OK] `register_with_platform(self, command_def)` - Register command with email system
- [OK] `unregister_command(self, command_name)` - Unregister a command
- [OK] `unregister_from_platform(self, command_name)` - Unregister command from the specific platform
- [OK] `unregister_from_platform(self, command_name)` - Unregister command from Discord
- [OK] `unregister_from_platform(self, command_name)` - Unregister command from email system
**Classes:**
- [OK] `CommandDefinition` - Definition of a command that can be registered
  - [OK] `CommandDefinition.__post_init__(self)` - Post-initialization setup
- [OK] `CommandRegistry` - Abstract base class for command registration utilities
  - [OK] `CommandRegistry.__init__(self)` - Initialize the command registry
  - [OK] `CommandRegistry.get_all_commands(self)` - Get all registered commands
  - [OK] `CommandRegistry.get_command(self, command_name)` - Get a command by name or alias
  - [OK] `CommandRegistry.get_enabled_commands(self)` - Get all enabled commands
  - [OK] `CommandRegistry.is_command_registered(self, command_name)` - Check if a command is registered
  - [OK] `CommandRegistry.register_command(self, command_def)` - Register a command definition
  - [OK] `CommandRegistry.register_with_platform(self, command_def)` - Register command with the specific platform (Discord, etc.)
  - [OK] `CommandRegistry.unregister_command(self, command_name)` - Unregister a command
  - [OK] `CommandRegistry.unregister_from_platform(self, command_name)` - Unregister command from the specific platform
- [OK] `DiscordCommandRegistry` - Discord-specific command registry
  - [OK] `DiscordCommandRegistry.__init__(self, bot)` - Initialize Discord command registry
  - [OK] `DiscordCommandRegistry.register_with_platform(self, command_def)` - Register command with Discord
  - [OK] `DiscordCommandRegistry.unregister_from_platform(self, command_name)` - Unregister command from Discord
- [OK] `EmailCommandRegistry` - Email-specific command registry
  - [OK] `EmailCommandRegistry.register_with_platform(self, command_def)` - Register command with email system
  - [OK] `EmailCommandRegistry.unregister_from_platform(self, command_name)` - Unregister command from email system

#### `communication/communication_channels/base/message_formatter.py`
**Functions:**
- [OK] `create_interactive_elements(self, suggestions)` - Create interactive elements (buttons, menus, etc.) from suggestions
- [OK] `create_interactive_elements(self, suggestions)` - Create text-based interactive elements
- [OK] `create_interactive_elements(self, suggestions)` - Create email-friendly interactive elements
- [OK] `create_rich_content(self, message, rich_data)` - Create rich content (embed, card, etc.) from rich data
- [OK] `create_rich_content(self, message, rich_data)` - Create rich text content
- [OK] `create_rich_content(self, message, rich_data)` - Create rich email content
- [OK] `format_message(self, message, rich_data)` - Format a message with optional rich data
- [OK] `format_message(self, message, rich_data)` - Format a message as plain text
- [OK] `format_message(self, message, rich_data)` - Format a message for email
- [OK] `get_message_formatter(channel_type)` - Get the appropriate message formatter for a channel type
**Classes:**
- [OK] `EmailMessageFormatter` - Email-specific message formatter
  - [OK] `EmailMessageFormatter.create_interactive_elements(self, suggestions)` - Create email-friendly interactive elements
  - [OK] `EmailMessageFormatter.create_rich_content(self, message, rich_data)` - Create rich email content
  - [OK] `EmailMessageFormatter.format_message(self, message, rich_data)` - Format a message for email
- [OK] `MessageFormatter` - Abstract base class for message formatting utilities
  - [OK] `MessageFormatter.create_interactive_elements(self, suggestions)` - Create interactive elements (buttons, menus, etc.) from suggestions
  - [OK] `MessageFormatter.create_rich_content(self, message, rich_data)` - Create rich content (embed, card, etc.) from rich data
  - [OK] `MessageFormatter.format_message(self, message, rich_data)` - Format a message with optional rich data
- [OK] `TextMessageFormatter` - Simple text-based message formatter for plain text channels
  - [OK] `TextMessageFormatter.create_interactive_elements(self, suggestions)` - Create text-based interactive elements
  - [OK] `TextMessageFormatter.create_rich_content(self, message, rich_data)` - Create rich text content
  - [OK] `TextMessageFormatter.format_message(self, message, rich_data)` - Format a message as plain text

#### `communication/communication_channels/base/rich_formatter.py`
**Functions:**
- [OK] `__init__(self)` - Initialize Discord formatter
- [OK] `create_embed(self, message, rich_data)` - Create a rich embed/card from rich data
- [OK] `create_embed(self, message, rich_data)` - Create a Discord embed from rich data
- [OK] `create_embed(self, message, rich_data)` - Create rich HTML content for email
- [OK] `create_interactive_view(self, suggestions)` - Create interactive view with buttons/menus from suggestions
- [OK] `create_interactive_view(self, suggestions)` - Create a Discord view with buttons from suggestions
- [OK] `create_interactive_view(self, suggestions)` - Create HTML buttons for email
- [OK] `get_color_for_type(self, content_type)` - Get appropriate color for content type
- [OK] `get_color_for_type(self, content_type)` - Get Discord color for content type
- [OK] `get_color_for_type(self, content_type)` - Get HTML color for content type
- [OK] `get_rich_formatter(channel_type)` - Get the appropriate rich formatter for a channel type
**Classes:**
- [OK] `DiscordRichFormatter` - Discord-specific rich formatting utilities
  - [OK] `DiscordRichFormatter.__init__(self)` - Initialize Discord formatter
  - [OK] `DiscordRichFormatter.create_embed(self, message, rich_data)` - Create a Discord embed from rich data
  - [OK] `DiscordRichFormatter.create_interactive_view(self, suggestions)` - Create a Discord view with buttons from suggestions
  - [OK] `DiscordRichFormatter.get_color_for_type(self, content_type)` - Get Discord color for content type
- [OK] `EmailRichFormatter` - Email-specific rich formatting utilities
  - [OK] `EmailRichFormatter.create_embed(self, message, rich_data)` - Create rich HTML content for email
  - [OK] `EmailRichFormatter.create_interactive_view(self, suggestions)` - Create HTML buttons for email
  - [OK] `EmailRichFormatter.get_color_for_type(self, content_type)` - Get HTML color for content type
- [OK] `RichFormatter` - Abstract base class for rich formatting utilities
  - [OK] `RichFormatter.create_embed(self, message, rich_data)` - Create a rich embed/card from rich data
  - [OK] `RichFormatter.create_interactive_view(self, suggestions)` - Create interactive view with buttons/menus from suggestions
  - [OK] `RichFormatter.get_color_for_type(self, content_type)` - Get appropriate color for content type

#### `communication/communication_channels/discord/account_flow_handler.py`
**Functions:**
- [OK] `__init__(self, username, discord_user_id, timeout)` - Initialize the feature selection view for account creation.

Creates a Discord UI view with select menus and buttons for configuring
account features (tasks, check-ins, messages, timezone) during account creation.

Args:
    username: The username for the account being created
    discord_user_id: The Discord user ID of the account creator
    timeout: View timeout in seconds (default: 300.0)
- [OK] `__init__(self, parent_view)` - Initialize the task management feature select menu.

Creates a Discord select menu for enabling or disabling task management
features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `__init__(self, parent_view)` - Initialize the check-in feature select menu.

Creates a Discord select menu for enabling or disabling check-in
features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `__init__(self, parent_view)` - Initialize the automated messages feature select menu.

Creates a Discord select menu for enabling or disabling automated
messages features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `__init__(self, parent_view)` - Initialize the timezone selection menu.

Creates a Discord select menu for choosing the user's timezone during
account creation. Limited to 25 options (Discord's maximum).

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `__init__(self, parent_view)` - Initialize the account creation button.

Creates a Discord button that finalizes account creation with the
selected features when clicked.

Args:
    parent_view: The parent FeatureSelectionView containing the selected features
**Classes:**
- [OK] `CheckinFeatureSelect` - Select menu for check-in feature.
  - [OK] `CheckinFeatureSelect.__init__(self, parent_view)` - Initialize the check-in feature select menu.

Creates a Discord select menu for enabling or disabling check-in
features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [MISSING] `ConfirmLinkModal` - No description
- [OK] `CreateAccountButton` - Button to finalize account creation.
  - [OK] `CreateAccountButton.__init__(self, parent_view)` - Initialize the account creation button.

Creates a Discord button that finalizes account creation with the
selected features when clicked.

Args:
    parent_view: The parent FeatureSelectionView containing the selected features
- [MISSING] `CreateAccountModal` - No description
- [OK] `FeatureSelectionView` - View for selecting account features during creation.
  - [OK] `FeatureSelectionView.__init__(self, username, discord_user_id, timeout)` - Initialize the feature selection view for account creation.

Creates a Discord UI view with select menus and buttons for configuring
account features (tasks, check-ins, messages, timezone) during account creation.

Args:
    username: The username for the account being created
    discord_user_id: The Discord user ID of the account creator
    timeout: View timeout in seconds (default: 300.0)
- [MISSING] `LinkAccountModal` - No description
- [OK] `MessageFeatureSelect` - Select menu for automated messages feature.
  - [OK] `MessageFeatureSelect.__init__(self, parent_view)` - Initialize the automated messages feature select menu.

Creates a Discord select menu for enabling or disabling automated
messages features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `TaskFeatureSelect` - Select menu for task management feature.
  - [OK] `TaskFeatureSelect.__init__(self, parent_view)` - Initialize the task management feature select menu.

Creates a Discord select menu for enabling or disabling task management
features during account creation.

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes
- [OK] `TimezoneSelect` - Select menu for timezone selection.
  - [OK] `TimezoneSelect.__init__(self, parent_view)` - Initialize the timezone selection menu.

Creates a Discord select menu for choosing the user's timezone during
account creation. Limited to 25 options (Discord's maximum).

Args:
    parent_view: The parent FeatureSelectionView to update when selection changes

#### `communication/communication_channels/discord/api_client.py`
**Functions:**
- [OK] `__init__(self, bot)` - Initialize the Discord API client
- [OK] `get_connection_latency(self)` - Get the bot's connection latency
- [OK] `get_discord_api_client(bot)` - Get a Discord API client instance
- [OK] `is_connected(self)` - Check if the bot is connected to Discord
**Classes:**
- [OK] `DiscordAPIClient` - Discord API client for handling Discord-specific operations
  - [OK] `DiscordAPIClient.__init__(self, bot)` - Initialize the Discord API client
  - [OK] `DiscordAPIClient.get_connection_latency(self)` - Get the bot's connection latency
  - [OK] `DiscordAPIClient.is_connected(self)` - Check if the bot is connected to Discord
- [OK] `MessageData` - Data structure for Discord messages
- [OK] `SendMessageOptions` - Options for sending messages

#### `communication/communication_channels/discord/bot.py`
**Functions:**
- [OK] `__init__(self, config)` - Initialize the object.
- [OK] `_check_dns_resolution(self, hostname)` - Check DNS resolution with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `_check_network_connectivity(self, hostname, port)` - Check network connectivity with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `_check_network_health(self)` - Comprehensive network health check with detailed reporting
- [OK] `_create_action_row(self, suggestions)` - Create Discord action row with validation.

Returns:
    discord.ui.View: Created view, None if failed
- [OK] `_create_discord_embed(self, message, rich_data)` - Create Discord embed with validation.

Returns:
    discord.Embed: Created embed, None if failed
- [OK] `_get_detailed_connection_status(self)` - Get detailed connection status information
- [OK] `_shared__update_connection_status(self, status, error_info)` - Update connection status with detailed error information
- [OK] `_should_attempt_reconnection(self)` - Determine if reconnection should be attempted based on various factors
- [OK] `_start_ngrok_tunnel(self, port)` - Start ngrok tunnel for webhook server (development only).

Args:
    port: Local port to tunnel (e.g., 8080)
- [OK] `_stop_ngrok_tunnel(self)` - Stop ngrok tunnel if running.
- [OK] `_wait_for_network_recovery(self, max_wait)` - Wait for network recovery with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `can_send_messages(self)` - Check if the Discord bot can actually send messages
- [OK] `channel_type(self)` - Get the channel type for Discord bot.

Returns:
    ChannelType.ASYNC: Discord bot operates asynchronously
- [OK] `get_connection_status_summary(self)` - Get a human-readable connection status summary
- [OK] `get_health_status(self)` - Get comprehensive health status information
- [OK] `initialize__register_commands(self)` - Register Discord commands
- [OK] `initialize__register_events(self)` - Register Discord event handlers
- [OK] `initialize__run_bot_in_thread(self)` - Run Discord bot in completely isolated thread with its own event loop
- [OK] `is_actually_connected(self)` - Check if the Discord bot is actually connected, regardless of initialization status
**Classes:**
- [MISSING] `DiscordBot` - No description
  - [OK] `DiscordBot.__init__(self, config)` - Initialize the object.
  - [OK] `DiscordBot._check_dns_resolution(self, hostname)` - Check DNS resolution with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `DiscordBot._check_network_connectivity(self, hostname, port)` - Check network connectivity with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `DiscordBot._check_network_health(self)` - Comprehensive network health check with detailed reporting
  - [OK] `DiscordBot._create_action_row(self, suggestions)` - Create Discord action row with validation.

Returns:
    discord.ui.View: Created view, None if failed
  - [OK] `DiscordBot._create_discord_embed(self, message, rich_data)` - Create Discord embed with validation.

Returns:
    discord.Embed: Created embed, None if failed
  - [OK] `DiscordBot._get_detailed_connection_status(self)` - Get detailed connection status information
  - [OK] `DiscordBot._shared__update_connection_status(self, status, error_info)` - Update connection status with detailed error information
  - [OK] `DiscordBot._should_attempt_reconnection(self)` - Determine if reconnection should be attempted based on various factors
  - [OK] `DiscordBot._start_ngrok_tunnel(self, port)` - Start ngrok tunnel for webhook server (development only).

Args:
    port: Local port to tunnel (e.g., 8080)
  - [OK] `DiscordBot._stop_ngrok_tunnel(self)` - Stop ngrok tunnel if running.
  - [OK] `DiscordBot._wait_for_network_recovery(self, max_wait)` - Wait for network recovery with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `DiscordBot.can_send_messages(self)` - Check if the Discord bot can actually send messages
  - [OK] `DiscordBot.channel_type(self)` - Get the channel type for Discord bot.

Returns:
    ChannelType.ASYNC: Discord bot operates asynchronously
  - [OK] `DiscordBot.get_connection_status_summary(self)` - Get a human-readable connection status summary
  - [OK] `DiscordBot.get_health_status(self)` - Get comprehensive health status information
  - [OK] `DiscordBot.initialize__register_commands(self)` - Register Discord commands
  - [OK] `DiscordBot.initialize__register_events(self)` - Register Discord event handlers
  - [OK] `DiscordBot.initialize__run_bot_in_thread(self)` - Run Discord bot in completely isolated thread with its own event loop
  - [OK] `DiscordBot.is_actually_connected(self)` - Check if the Discord bot is actually connected, regardless of initialization status
- [OK] `DiscordConnectionStatus` - Detailed Discord connection status for better error reporting

#### `communication/communication_channels/discord/checkin_view.py`
**Functions:**
- [OK] `__init__(self, user_id)` - Initialize the check-in view with action buttons.

Creates a Discord UI view with buttons for canceling check-ins,
skipping questions, and accessing help during the check-in flow.

Args:
    user_id: The internal user ID for the check-in session
- [OK] `get_checkin_view(user_id)` - Create a Discord View with buttons for check-in flow.

Args:
    user_id: The user's internal user ID

Returns:
    discord.ui.View with buttons for check-in actions
**Classes:**
- [MISSING] `CheckinView` - No description
  - [OK] `CheckinView.__init__(self, user_id)` - Initialize the check-in view with action buttons.

Creates a Discord UI view with buttons for canceling check-ins,
skipping questions, and accessing help during the check-in flow.

Args:
    user_id: The internal user ID for the check-in session

#### `communication/communication_channels/discord/event_handler.py`
**Functions:**
- [OK] `__init__(self, bot)` - Initialize the Discord event handler
- [OK] `__post_init__(self)` - Post-initialization setup
- [OK] `_register_default_handlers(self)` - Register default event handlers
- [OK] `add_disconnect_handler(self, handler)` - Add a custom disconnect handler
- [OK] `add_error_handler(self, handler)` - Add a custom error handler
- [OK] `add_message_handler(self, handler)` - Add a custom message handler
- [OK] `add_ready_handler(self, handler)` - Add a custom ready handler
- [OK] `get_discord_event_handler(bot)` - Get a Discord event handler instance
- [OK] `register_events(self, bot)` - Register all event handlers with a Discord bot
**Classes:**
- [OK] `DiscordEventHandler` - Handles Discord events and routes them to appropriate handlers
  - [OK] `DiscordEventHandler.__init__(self, bot)` - Initialize the Discord event handler
  - [OK] `DiscordEventHandler._register_default_handlers(self)` - Register default event handlers
  - [OK] `DiscordEventHandler.add_disconnect_handler(self, handler)` - Add a custom disconnect handler
  - [OK] `DiscordEventHandler.add_error_handler(self, handler)` - Add a custom error handler
  - [OK] `DiscordEventHandler.add_message_handler(self, handler)` - Add a custom message handler
  - [OK] `DiscordEventHandler.add_ready_handler(self, handler)` - Add a custom ready handler
  - [OK] `DiscordEventHandler.register_events(self, bot)` - Register all event handlers with a Discord bot
- [OK] `EventContext` - Context for Discord events
  - [OK] `EventContext.__post_init__(self)` - Post-initialization setup
- [OK] `EventType` - Types of Discord events

#### `communication/communication_channels/discord/task_reminder_view.py`
**Functions:**
- [OK] `__init__(self, user_id, task_id, task_title)` - Initialize a Discord task reminder view with buttons.

Args:
    user_id: The user's internal user ID
    task_id: The task ID to display in the reminder
    task_title: The title of the task to display
- [OK] `get_task_reminder_view(user_id, task_id, task_title)` - Create a Discord View with buttons for task reminder actions.

Args:
    user_id: The user's internal user ID
    task_id: The task ID
    task_title: The task title

Returns:
    discord.ui.View with buttons for task reminder actions
**Classes:**
- [MISSING] `TaskReminderView` - No description
  - [OK] `TaskReminderView.__init__(self, user_id, task_id, task_title)` - Initialize a Discord task reminder view with buttons.

Args:
    user_id: The user's internal user ID
    task_id: The task ID to display in the reminder
    task_title: The title of the task to display

#### `communication/communication_channels/discord/webhook_handler.py`
**Functions:**
- [OK] `handle_application_authorized(event_data, bot_instance)` - Handle APPLICATION_AUTHORIZED webhook event.

This is triggered when a user authorizes the app.
We should send them a welcome DM immediately.

Args:
    event_data: The webhook event data
    bot_instance: The Discord bot instance (for sending DMs)

Returns:
    bool: True if handled successfully
- [OK] `handle_webhook_event(event_type, event_data, bot_instance)` - Route webhook events to appropriate handlers.

Args:
    event_type: The type of webhook event
    event_data: The event data
    bot_instance: The Discord bot instance

Returns:
    bool: True if handled successfully
- [OK] `parse_webhook_event(body)` - Parse Discord webhook event from request body.

Args:
    body: JSON string of the webhook event

Returns:
    Dict with event data, or None if invalid
- [OK] `verify_webhook_signature(signature, timestamp, body, public_key)` - Verify Discord webhook signature.

Discord signs webhook requests using ed25519. For simplicity, we'll verify
the signature matches Discord's expected format.

Args:
    signature: The X-Signature-Ed25519 header value
    timestamp: The X-Signature-Timestamp header value
    body: The raw request body
    public_key: The application's public key

Returns:
    bool: True if signature is valid

#### `communication/communication_channels/discord/webhook_server.py`
**Functions:**
- [OK] `__init__(self, port, bot_instance)` - Initialize webhook server.

Args:
    port: Port to listen on
    bot_instance: Discord bot instance (for sending DMs)
- [OK] `do_GET(self)` - Handle GET requests (health check)
- [OK] `do_OPTIONS(self)` - Handle OPTIONS requests (CORS preflight)
- [OK] `do_POST(self)` - Handle POST requests (Discord webhook events) - accepts any path
- [OK] `log_message(self, format)` - Override to use our logger instead of stderr
- [OK] `start(self)` - Start the webhook server
- [OK] `stop(self)` - Stop the webhook server
**Classes:**
- [OK] `DiscordWebhookHandler` - HTTP request handler for Discord webhook events
  - [OK] `DiscordWebhookHandler.do_GET(self)` - Handle GET requests (health check)
  - [OK] `DiscordWebhookHandler.do_OPTIONS(self)` - Handle OPTIONS requests (CORS preflight)
  - [OK] `DiscordWebhookHandler.do_POST(self)` - Handle POST requests (Discord webhook events) - accepts any path
  - [OK] `DiscordWebhookHandler.log_message(self, format)` - Override to use our logger instead of stderr
- [OK] `WebhookServer` - HTTP server for receiving Discord webhook events
  - [OK] `WebhookServer.__init__(self, port, bot_instance)` - Initialize webhook server.

Args:
    port: Port to listen on
    bot_instance: Discord bot instance (for sending DMs)
  - [OK] `WebhookServer.start(self)` - Start the webhook server
  - [OK] `WebhookServer.stop(self)` - Stop the webhook server

#### `communication/communication_channels/discord/welcome_handler.py`
**Functions:**
- [OK] `__init__(self, discord_user_id)` - Initialize the welcome view with account action buttons.

Creates a Discord UI view with buttons for creating a new account
or linking to an existing account. Buttons persist without timeout.

Args:
    discord_user_id: The Discord user ID for the welcome session
- [OK] `clear_welcomed_status(discord_user_id)` - Clear the welcomed status for a Discord user (e.g., when they deauthorize).
- [OK] `get_welcome_message(discord_user_id, discord_username, is_authorization)` - Get a welcome message for a new Discord user.

Args:
    discord_user_id: The user's Discord ID
    discord_username: The user's Discord username (optional, for prefilling)
    is_authorization: True if this is triggered by app authorization (DM), False for server messages

Returns:
    str: Welcome message text
- [OK] `get_welcome_message_view(discord_user_id)` - Create a Discord View with buttons for account creation and linking.

Args:
    discord_user_id: The user's Discord ID

Returns:
    discord.ui.View with buttons for account actions
- [OK] `has_been_welcomed(discord_user_id)` - Check if a Discord user has already been sent a welcome message.
- [OK] `mark_as_welcomed(discord_user_id)` - Mark a Discord user as having been welcomed.
**Classes:**
- [MISSING] `WelcomeView` - No description
  - [OK] `WelcomeView.__init__(self, discord_user_id)` - Initialize the welcome view with account action buttons.

Creates a Discord UI view with buttons for creating a new account
or linking to an existing account. Buttons persist without timeout.

Args:
    discord_user_id: The Discord user ID for the welcome session

#### `communication/communication_channels/email/bot.py`
**Functions:**
- [OK] `__init__(self, config)` - Initialize the EmailBot with configuration.

Args:
    config: Channel configuration object. If None, creates default config
           with email-specific settings (max_retries=3, retry_delay=1.0,
           backoff_multiplier=2.0)
- [MISSING] `_get_email_config(self)` - No description
- [OK] `_receive_emails_sync(self)` - Receive emails synchronously - only fetches UNSEEN emails for efficiency
- [OK] `_receive_emails_sync__extract_body(self, msg)` - Extract plain text body from email message
- [OK] `channel_type(self)` - Get the channel type for email bot.

Returns:
    ChannelType.SYNC: Email operations are synchronous
- [OK] `initialize__test_imap_connection(self)` - Test IMAP connection synchronously
- [OK] `initialize__test_smtp_connection(self)` - Test SMTP connection synchronously
- [OK] `send_message__send_email_sync(self, recipient, message, kwargs)` - Send email synchronously
**Classes:**
- [MISSING] `EmailBot` - No description
  - [OK] `EmailBot.__init__(self, config)` - Initialize the EmailBot with configuration.

Args:
    config: Channel configuration object. If None, creates default config
           with email-specific settings (max_retries=3, retry_delay=1.0,
           backoff_multiplier=2.0)
  - [MISSING] `EmailBot._get_email_config(self)` - No description
  - [OK] `EmailBot._receive_emails_sync(self)` - Receive emails synchronously - only fetches UNSEEN emails for efficiency
  - [OK] `EmailBot._receive_emails_sync__extract_body(self, msg)` - Extract plain text body from email message
  - [OK] `EmailBot.channel_type(self)` - Get the channel type for email bot.

Returns:
    ChannelType.SYNC: Email operations are synchronous
  - [OK] `EmailBot.initialize__test_imap_connection(self)` - Test IMAP connection synchronously
  - [OK] `EmailBot.initialize__test_smtp_connection(self)` - Test SMTP connection synchronously
  - [OK] `EmailBot.send_message__send_email_sync(self, recipient, message, kwargs)` - Send email synchronously
- [OK] `EmailBotError` - Custom exception for email bot-related errors.

#### `communication/core/__init__.py`
**Functions:**
- [OK] `__getattr__(name)` - Lazy import handler for items with circular dependencies.

Note: This function intentionally does not use @handle_errors decorator
to avoid circular dependencies with error handling infrastructure.

#### `communication/core/channel_monitor.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the channel monitor
- [OK] `_attempt_channel_restart(self, channel_name)` - Attempt to restart a specific channel
- [OK] `_check_and_restart_stuck_channels(self)` - Check for stuck channels and attempt restarts
- [OK] `_restart_monitor_loop(self)` - Main restart monitor loop that checks channel health
- [OK] `get_channel_health_status(self)` - Get health status for all monitored channels
- [OK] `record_channel_failure(self, channel_name)` - Record a failure for a specific channel
- [OK] `record_channel_success(self, channel_name)` - Record a success for a specific channel (resets failure count)
- [OK] `reset_channel_failures(self, channel_name)` - Reset failure counts for a specific channel or all channels
- [OK] `set_channels(self, channels_dict)` - Set the channels dictionary for monitoring
- [OK] `start_restart_monitor(self)` - Start the automatic restart monitor thread
- [OK] `stop_restart_monitor(self)` - Stop the automatic restart monitor thread
**Classes:**
- [OK] `ChannelMonitor` - Monitors channel health and manages automatic restart logic
  - [OK] `ChannelMonitor.__init__(self)` - Initialize the channel monitor
  - [OK] `ChannelMonitor._attempt_channel_restart(self, channel_name)` - Attempt to restart a specific channel
  - [OK] `ChannelMonitor._check_and_restart_stuck_channels(self)` - Check for stuck channels and attempt restarts
  - [OK] `ChannelMonitor._restart_monitor_loop(self)` - Main restart monitor loop that checks channel health
  - [OK] `ChannelMonitor.get_channel_health_status(self)` - Get health status for all monitored channels
  - [OK] `ChannelMonitor.record_channel_failure(self, channel_name)` - Record a failure for a specific channel
  - [OK] `ChannelMonitor.record_channel_success(self, channel_name)` - Record a success for a specific channel (resets failure count)
  - [OK] `ChannelMonitor.reset_channel_failures(self, channel_name)` - Reset failure counts for a specific channel or all channels
  - [OK] `ChannelMonitor.set_channels(self, channels_dict)` - Set the channels dictionary for monitoring
  - [OK] `ChannelMonitor.start_restart_monitor(self)` - Start the automatic restart monitor thread
  - [OK] `ChannelMonitor.stop_restart_monitor(self)` - Stop the automatic restart monitor thread

#### `communication/core/channel_orchestrator.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the CommunicationManager singleton
- [OK] `__init____setup_event_loop(self)` - Set up a dedicated event loop for async operations
- [OK] `__new__(cls)` - Ensure that only one instance of the CommunicationManager exists (Singleton pattern).
- [OK] `_check_logging_health(self)` - Check if logging is still working and recover if needed.

Verifies that the logging system is functional and attempts to restart it if issues are detected.
- [OK] `_create_task_reminder_message(self, task)` - Create task reminder message with validation.

Returns:
    str: Task reminder message, default if failed
- [OK] `_email_polling_loop(self)` - Background thread that periodically polls for incoming emails and processes them
- [OK] `_expire_checkin_flow_if_needed(self, user_id, category)` - Expire check-in flow if this is a non-scheduled message.
- [OK] `_get_default_channel_configs(self)` - Get default channel configurations
- [OK] `_get_recipient_for_service(self, user_id, messaging_service, preferences)` - Get recipient for service with validation.

Returns:
    Optional[str]: Recipient ID, None if failed
- [OK] `_handle_scheduled_checkin(self, user_id, messaging_service, recipient)` - Handle scheduled check-in messages based on user preferences and frequency.
- [OK] `_initialize_channel_with_retry_sync(self, channel, config)` - Synchronous version of channel initialization with retry logic
- [OK] `_process_incoming_email(self, email_msg)` - Process an incoming email message and send response
- [OK] `_select_weighted_message(self, available_messages, matching_periods)` - Select weighted message with validation.

Returns:
    str: Selected message, empty string if failed
- [OK] `_send_ai_generated_message(self, user_id, category, messaging_service, recipient)` - Send an AI-generated personalized message using contextual AI.

Returns:
    tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
- [OK] `_send_checkin_prompt(self, user_id, messaging_service, recipient)` - Send a check-in prompt message to start the check-in flow.
- [OK] `_send_email_response(self, recipient_email, response_text, subject)` - Send an email response to a user
- [OK] `_send_predefined_message(self, user_id, category, messaging_service, recipient)` - Send a pre-defined message from the user's message library with deduplication.

Returns:
    tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
- [OK] `_should_send_checkin_prompt(self, user_id, checkin_prefs)` - Determine if it's time to send a check-in prompt based on user preferences.
For check-ins, we respect the schedule-based approach - if the scheduler
triggered this function, it means it's time for a check-in during the
scheduled period.
- [OK] `_shutdown_sync(self)` - Synchronous shutdown method for all channels.

Stops all communication channels and cleans up resources.
- [OK] `_start_sync(self)` - Synchronous method to start all configured channels
- [MISSING] `create_view()` - No description
- [MISSING] `create_view()` - No description
- [OK] `get_active_channels(self)` - Get active channels with validation.

Returns:
    List[str]: List of active channels, empty list if failed
- [OK] `get_configured_channels(self)` - Get configured channels with validation.

Returns:
    List[str]: List of configured channels, empty list if failed
- [OK] `get_discord_connectivity_status(self)` - Get detailed Discord connectivity status if available
- [OK] `get_last_task_reminder(self, user_id)` - Get last task reminder with validation.

Returns:
    Optional[str]: Last task reminder, None if failed
- [OK] `get_registered_channels(self)` - Get registered channels with validation.

Returns:
    List[str]: List of registered channels, empty list if failed
- [OK] `handle_message_sending(self, user_id, category)` - Handle sending messages for a user and category with improved recipient resolution.
Now uses scheduled check-ins instead of random replacement.
- [OK] `handle_task_reminder(self, user_id, task_id)` - Handle task reminder with validation.

Returns:
    None: Always returns None
- [OK] `initialize_channels_from_config(self, channel_configs)` - Initialize channels from configuration with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `run_event_loop()` - Run the event loop in a separate thread for async operations.

This nested function is used to manage the event loop for async channel operations.
- [OK] `send_message_sync(self, channel_name, recipient, message)` - Synchronous wrapper with logging health check
- [OK] `send_message_sync__queue_failed_message(self, user_id, category, message, recipient, channel_name)` - Queue a failed message for retry
- [OK] `send_message_sync__run_async_sync(self, coro)` - Run async function synchronously using our managed loop
- [OK] `set_scheduler_manager(self, scheduler_manager)` - Set the scheduler manager for the communication manager.
- [OK] `start_all(self)` - Start all communication channels with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `start_all__start_email_polling(self)` - Start the email polling thread to process incoming emails
- [OK] `start_all__start_restart_monitor(self)` - Start the automatic restart monitor thread
- [OK] `start_all__start_retry_thread(self)` - Start the retry thread for failed messages
- [OK] `stop_all(self)` - Stop all communication channels with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `stop_all__stop_email_polling(self)` - Stop the email polling thread
- [OK] `stop_all__stop_restart_monitor(self)` - Stop the automatic restart monitor thread
- [OK] `stop_all__stop_retry_thread(self)` - Stop the retry thread
**Classes:**
- [OK] `BotInitializationError` - Custom exception for bot initialization failures.
- [OK] `CommunicationManager` - Manages all communication channels with improved modularity
  - [OK] `CommunicationManager.__init__(self)` - Initialize the CommunicationManager singleton
  - [OK] `CommunicationManager.__init____setup_event_loop(self)` - Set up a dedicated event loop for async operations
  - [OK] `CommunicationManager.__new__(cls)` - Ensure that only one instance of the CommunicationManager exists (Singleton pattern).
  - [OK] `CommunicationManager._check_logging_health(self)` - Check if logging is still working and recover if needed.

Verifies that the logging system is functional and attempts to restart it if issues are detected.
  - [OK] `CommunicationManager._create_task_reminder_message(self, task)` - Create task reminder message with validation.

Returns:
    str: Task reminder message, default if failed
  - [OK] `CommunicationManager._email_polling_loop(self)` - Background thread that periodically polls for incoming emails and processes them
  - [OK] `CommunicationManager._expire_checkin_flow_if_needed(self, user_id, category)` - Expire check-in flow if this is a non-scheduled message.
  - [OK] `CommunicationManager._get_default_channel_configs(self)` - Get default channel configurations
  - [OK] `CommunicationManager._get_recipient_for_service(self, user_id, messaging_service, preferences)` - Get recipient for service with validation.

Returns:
    Optional[str]: Recipient ID, None if failed
  - [OK] `CommunicationManager._handle_scheduled_checkin(self, user_id, messaging_service, recipient)` - Handle scheduled check-in messages based on user preferences and frequency.
  - [OK] `CommunicationManager._initialize_channel_with_retry_sync(self, channel, config)` - Synchronous version of channel initialization with retry logic
  - [OK] `CommunicationManager._process_incoming_email(self, email_msg)` - Process an incoming email message and send response
  - [OK] `CommunicationManager._select_weighted_message(self, available_messages, matching_periods)` - Select weighted message with validation.

Returns:
    str: Selected message, empty string if failed
  - [OK] `CommunicationManager._send_ai_generated_message(self, user_id, category, messaging_service, recipient)` - Send an AI-generated personalized message using contextual AI.

Returns:
    tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
  - [OK] `CommunicationManager._send_checkin_prompt(self, user_id, messaging_service, recipient)` - Send a check-in prompt message to start the check-in flow.
  - [OK] `CommunicationManager._send_email_response(self, recipient_email, response_text, subject)` - Send an email response to a user
  - [OK] `CommunicationManager._send_predefined_message(self, user_id, category, messaging_service, recipient)` - Send a pre-defined message from the user's message library with deduplication.

Returns:
    tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
  - [OK] `CommunicationManager._should_send_checkin_prompt(self, user_id, checkin_prefs)` - Determine if it's time to send a check-in prompt based on user preferences.
For check-ins, we respect the schedule-based approach - if the scheduler
triggered this function, it means it's time for a check-in during the
scheduled period.
  - [OK] `CommunicationManager._shutdown_sync(self)` - Synchronous shutdown method for all channels.

Stops all communication channels and cleans up resources.
  - [OK] `CommunicationManager._start_sync(self)` - Synchronous method to start all configured channels
  - [OK] `CommunicationManager.get_active_channels(self)` - Get active channels with validation.

Returns:
    List[str]: List of active channels, empty list if failed
  - [OK] `CommunicationManager.get_configured_channels(self)` - Get configured channels with validation.

Returns:
    List[str]: List of configured channels, empty list if failed
  - [OK] `CommunicationManager.get_discord_connectivity_status(self)` - Get detailed Discord connectivity status if available
  - [OK] `CommunicationManager.get_last_task_reminder(self, user_id)` - Get last task reminder with validation.

Returns:
    Optional[str]: Last task reminder, None if failed
  - [OK] `CommunicationManager.get_registered_channels(self)` - Get registered channels with validation.

Returns:
    List[str]: List of registered channels, empty list if failed
  - [OK] `CommunicationManager.handle_message_sending(self, user_id, category)` - Handle sending messages for a user and category with improved recipient resolution.
Now uses scheduled check-ins instead of random replacement.
  - [OK] `CommunicationManager.handle_task_reminder(self, user_id, task_id)` - Handle task reminder with validation.

Returns:
    None: Always returns None
  - [OK] `CommunicationManager.initialize_channels_from_config(self, channel_configs)` - Initialize channels from configuration with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `CommunicationManager.send_message_sync(self, channel_name, recipient, message)` - Synchronous wrapper with logging health check
  - [OK] `CommunicationManager.send_message_sync__queue_failed_message(self, user_id, category, message, recipient, channel_name)` - Queue a failed message for retry
  - [OK] `CommunicationManager.send_message_sync__run_async_sync(self, coro)` - Run async function synchronously using our managed loop
  - [OK] `CommunicationManager.set_scheduler_manager(self, scheduler_manager)` - Set the scheduler manager for the communication manager.
  - [OK] `CommunicationManager.start_all(self)` - Start all communication channels with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `CommunicationManager.start_all__start_email_polling(self)` - Start the email polling thread to process incoming emails
  - [OK] `CommunicationManager.start_all__start_restart_monitor(self)` - Start the automatic restart monitor thread
  - [OK] `CommunicationManager.start_all__start_retry_thread(self)` - Start the retry thread for failed messages
  - [OK] `CommunicationManager.stop_all(self)` - Stop all communication channels with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `CommunicationManager.stop_all__stop_email_polling(self)` - Stop the email polling thread
  - [OK] `CommunicationManager.stop_all__stop_restart_monitor(self)` - Stop the automatic restart monitor thread
  - [OK] `CommunicationManager.stop_all__stop_retry_thread(self)` - Stop the retry thread
- [OK] `MessageSendError` - Custom exception for message sending failures.

#### `communication/core/factory.py`
**Functions:**
- [OK] `_initialize_registry(cls)` - Initialize the channel registry from configuration
- [OK] `create_channel(cls, name, config)` - Create a channel instance
- [OK] `get_registered_channels(cls)` - Get list of registered channel types
**Classes:**
- [OK] `ChannelFactory` - Factory for creating communication channels using config-based discovery
  - [OK] `ChannelFactory._initialize_registry(cls)` - Initialize the channel registry from configuration
  - [OK] `ChannelFactory.create_channel(cls, name, config)` - Create a channel instance
  - [OK] `ChannelFactory.get_registered_channels(cls)` - Get list of registered channel types

#### `communication/core/retry_manager.py`
**Functions:**
- [OK] `__init__(self, send_callback)` - Initialize the retry manager

Args:
    send_callback: Optional callable that takes (channel_name, recipient, message, **kwargs)
                  and returns bool indicating success. If None, retries will only be logged.
- [OK] `_process_retry_queue(self)` - Process the retry queue and attempt to resend failed messages
- [OK] `_retry_loop(self)` - Main retry loop that processes failed messages
- [OK] `clear_queue(self)` - Clear all queued messages (use with caution)
- [OK] `get_queue_size(self)` - Get the current size of the retry queue
- [OK] `queue_failed_message(self, user_id, category, message, recipient, channel_name)` - Queue a failed message for retry
- [OK] `start_retry_thread(self)` - Start the retry thread for failed messages
- [OK] `stop_retry_thread(self)` - Stop the retry thread
**Classes:**
- [OK] `QueuedMessage` - Represents a message that failed to send and is queued for retry
- [OK] `RetryManager` - Manages message retry logic and failed message queuing
  - [OK] `RetryManager.__init__(self, send_callback)` - Initialize the retry manager

Args:
    send_callback: Optional callable that takes (channel_name, recipient, message, **kwargs)
                  and returns bool indicating success. If None, retries will only be logged.
  - [OK] `RetryManager._process_retry_queue(self)` - Process the retry queue and attempt to resend failed messages
  - [OK] `RetryManager._retry_loop(self)` - Main retry loop that processes failed messages
  - [OK] `RetryManager.clear_queue(self)` - Clear all queued messages (use with caution)
  - [OK] `RetryManager.get_queue_size(self)` - Get the current size of the retry queue
  - [OK] `RetryManager.queue_failed_message(self, user_id, category, message, recipient, channel_name)` - Queue a failed message for retry
  - [OK] `RetryManager.start_retry_thread(self)` - Start the retry thread for failed messages
  - [OK] `RetryManager.stop_retry_thread(self)` - Stop the retry thread

#### `communication/core/welcome_manager.py`
**Functions:**
- [OK] `_load_welcome_tracking()` - Load the welcome tracking data.
- [OK] `_save_welcome_tracking(tracking_data)` - Save the welcome tracking data.
- [OK] `clear_welcomed_status(channel_identifier, channel_type)` - Clear the welcomed status for a user (e.g., when they deauthorize).

Args:
    channel_identifier: The user's channel-specific identifier
    channel_type: The type of channel ('discord', 'email', etc.)

Returns:
    bool: True if successful
- [OK] `get_welcome_message(channel_identifier, channel_type, username, is_authorization)` - Get a channel-agnostic welcome message for a new user.

Args:
    channel_identifier: The user's channel-specific identifier
    channel_type: The type of channel ('discord', 'email', etc.)
    username: Optional username to prefill
    is_authorization: True if this is triggered by app authorization, False for general messages

Returns:
    str: Welcome message text
- [OK] `has_been_welcomed(channel_identifier, channel_type)` - Check if a user has already been sent a welcome message.

Args:
    channel_identifier: The user's channel-specific identifier (Discord ID, email, etc.)
    channel_type: The type of channel ('discord', 'email', etc.)

Returns:
    bool: True if user has been welcomed
- [OK] `mark_as_welcomed(channel_identifier, channel_type)` - Mark a user as having been welcomed.

Args:
    channel_identifier: The user's channel-specific identifier
    channel_type: The type of channel ('discord', 'email', etc.)

Returns:
    bool: True if successful

#### `communication/message_processing/__init__.py`

#### `communication/message_processing/command_parser.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the enhanced command parser.

Sets up the parser with AI chatbot integration and interaction handlers,
and initializes rule-based intent patterns for common commands.
- [OK] `_ai_enhanced_parse(self, message, user_id)` - Parse using AI chatbot capabilities
- [OK] `_calculate_confidence(self, intent, match, message)` - Calculate confidence score for a parsed command
- [OK] `_extract_entities_from_ai_response(self, ai_response)` - Extract entities from AI response text
- [OK] `_extract_entities_rule_based(self, intent, match, message)` - Extract entities using rule-based patterns
- [OK] `_extract_intent_from_ai_response(self, ai_response)` - Extract intent from AI response text
- [OK] `_extract_task_entities(self, title)` - Extract task-related entities from title
- [OK] `_extract_task_name_from_context(self, message)` - Extract task name from natural language context
- [OK] `_extract_update_entities(self, update_text)` - Extract update entities from update text
- [OK] `_is_valid_intent(self, intent)` - Check if intent is supported by any handler
- [OK] `_match_message(message_for_match)` - Attempt to match intents against the provided message.
- [OK] `_parse_key_value_format(self, response)` - Parse key-value format (ACTION: ..., TITLE: ..., etc.)
Returns (intent, entities) tuple
- [OK] `_rule_based_parse(self, message)` - Parse using rule-based patterns
- [OK] `get_enhanced_command_parser()` - Get the global enhanced command parser instance
- [OK] `get_suggestions(self, partial_message)` - Get command suggestions based on partial input
- [OK] `parse(self, message, user_id)` - Parse a user message into a structured command.

Returns:
    ParsingResult with parsed command, confidence, and method used
- [OK] `parse_command(message)` - Convenience function to parse a command
**Classes:**
- [OK] `EnhancedCommandParser` - Enhanced command parser that combines rule-based and AI parsing
  - [OK] `EnhancedCommandParser.__init__(self)` - Initialize the enhanced command parser.

Sets up the parser with AI chatbot integration and interaction handlers,
and initializes rule-based intent patterns for common commands.
  - [OK] `EnhancedCommandParser._ai_enhanced_parse(self, message, user_id)` - Parse using AI chatbot capabilities
  - [OK] `EnhancedCommandParser._calculate_confidence(self, intent, match, message)` - Calculate confidence score for a parsed command
  - [OK] `EnhancedCommandParser._extract_entities_from_ai_response(self, ai_response)` - Extract entities from AI response text
  - [OK] `EnhancedCommandParser._extract_entities_rule_based(self, intent, match, message)` - Extract entities using rule-based patterns
  - [OK] `EnhancedCommandParser._extract_intent_from_ai_response(self, ai_response)` - Extract intent from AI response text
  - [OK] `EnhancedCommandParser._extract_task_entities(self, title)` - Extract task-related entities from title
  - [OK] `EnhancedCommandParser._extract_task_name_from_context(self, message)` - Extract task name from natural language context
  - [OK] `EnhancedCommandParser._extract_update_entities(self, update_text)` - Extract update entities from update text
  - [OK] `EnhancedCommandParser._is_valid_intent(self, intent)` - Check if intent is supported by any handler
  - [OK] `EnhancedCommandParser._parse_key_value_format(self, response)` - Parse key-value format (ACTION: ..., TITLE: ..., etc.)
Returns (intent, entities) tuple
  - [OK] `EnhancedCommandParser._rule_based_parse(self, message)` - Parse using rule-based patterns
  - [OK] `EnhancedCommandParser.get_suggestions(self, partial_message)` - Get command suggestions based on partial input
  - [OK] `EnhancedCommandParser.parse(self, message, user_id)` - Parse a user message into a structured command.

Returns:
    ParsingResult with parsed command, confidence, and method used
- [OK] `ParsingResult` - Result of command parsing with confidence and method used

#### `communication/message_processing/conversation_flow_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the object.
- [OK] `_cache_expired_checkin_order(self, user_id, user_state)` - Cache the question order for a same-day restart after expiration.
- [OK] `_complete_checkin(self, user_id, user_state)` - Complete the check-in and provide personalized feedback
- [OK] `_date_str(dt)` - Return YYYY-MM-DD without sprinkling strftime format strings.
- [OK] `_expire_inactive_checkins(self, user_id)` - Remove stale check-in flows that have been idle beyond the allowed window.
- [OK] `_generate_completion_message(self, user_id, data)` - Generate a personalized completion message based on responses
- [OK] `_generate_context_aware_reminder_suggestions(self, user_id, task_id)` - Generate reminder period suggestions based on task's due date/time.

Examples:
- Task due in 6 days (no time) -> "1 to 2 days before", "3 to 4 days before"
- Task due in 12 days at 10:00 AM -> "1 to 2 hours before", "1 to 2 days before", "3 to 5 days before"
- [OK] `_get_cached_checkin_order(self, user_id)` - Return same-day cached question order if present and valid.
- [OK] `_get_next_question(self, user_id, user_state)` - Get the next question in the check-in flow
- [OK] `_get_personalized_welcome(self, user_id, question_count)` - Generate a personalized welcome message based on user history
- [OK] `_get_question_text(self, question_key, previous_data, user_id)` - Get appropriate question text based on question type and previous responses
- [OK] `_handle_checkin(self, user_id, user_state, message_text)` - Enhanced check-in flow with dynamic questions and better validation
- [OK] `_handle_command_during_checkin(self, user_id, message_text)` - Handle common commands while user is in a checkin flow
- [OK] `_handle_list_items_flow(self, user_id, user_state, message_text)` - Handle continuation of list items flow.
- [OK] `_handle_note_body_flow(self, user_id, user_state, message_text)` - Handle continuation of note body flow.
- [OK] `_handle_task_due_date_flow(self, user_id, user_state, message_text)` - Handle continuation of task due date/time flow.
- [OK] `_handle_task_reminder_followup(self, user_id, user_state, message_text)` - Handle user's response to reminder period question after task creation.

Parses natural language responses like:
- "30 minutes to an hour before"
- "3 to 5 hours before"
- "1 to 2 days before"
- "No reminders needed" / "No" / "Skip"
- [OK] `_load_user_states(self)` - Load user states from disk with comprehensive logging
- [OK] `_parse_date_time_from_text(self, text)` - Parse date and time from natural language text.

Returns: (date_str in YYYY-MM-DD format, time_str in HH:MM format or None)
- [OK] `_parse_reminder_periods_from_text(self, user_id, task_id, text)` - Parse reminder periods from natural language text.

Examples:
- "30 minutes to an hour before" -> reminder 30-60 min before due time
- "3 to 5 hours before" -> reminder 3-5 hours before due time
- "1 to 2 days before" -> reminder 1-2 days before due date

Returns list of reminder period dicts with date, start_time, end_time.
- [OK] `_parse_time_from_text(self, text)` - Parse time from natural language text.

Examples:
- "10am", "10:00am", "10:30am" -> "10:00", "10:30"
- "2pm", "14:00" -> "14:00"
- "at 3pm" -> "15:00"
- [OK] `_save_user_states(self)` - Save user states to disk with comprehensive logging and error handling
- [OK] `_select_checkin_questions_with_weighting(self, user_id, enabled_questions)` - Select check-in questions using weighted randomization with always/sometimes and min/max configuration.

Args:
    user_id: User ID
    enabled_questions: Dictionary of enabled questions from user preferences
        Each question can have:
        - 'enabled': bool (whether question is enabled)
        - 'always_include': bool (whether to always include this question)
        - 'sometimes_include': bool (whether to sometimes include this question)

Returns:
    List of question keys in selected order
- [OK] `_start_dynamic_checkin(self, user_id)` - Start a dynamic check-in flow based on user preferences with weighted question selection
- [OK] `_validate_response(self, question_key, response, user_id)` - Validate user response based on question type using dynamic manager
- [OK] `clear_all_states(self)` - Clear all user states - primarily for testing.
- [OK] `clear_stuck_flows(self, user_id)` - Clear any stuck conversation flows for a user.
This is a safety mechanism to reset flow state when it gets stuck.
- [OK] `expire_checkin_flow_due_to_unrelated_outbound(self, user_id)` - Expire an active check-in flow when an unrelated outbound message is sent.
Safe no-op if no flow or different flow is active.
- [OK] `handle_contextual_question(self, user_id, message_text)` - Handle a single contextual question without entering a conversation flow.
Perfect for one-off questions that benefit from user context.
- [OK] `handle_inbound_message(self, user_id, message_text)` - Primary entry point. Takes user's message and returns a (reply_text, completed).

Now defaults to contextual chat for all messages unless user is in a specific flow
or uses a special command.
- [OK] `restart_checkin(self, user_id)` - Force restart a check-in flow, clearing any existing checkin state.
This should be used when user explicitly wants to start over.
- [OK] `start_analytics_flow(self, user_id)` - Start the analytics flow for a user.

Initiates the analytics display flow by routing the "show analytics" command
through the interaction manager. Returns the response message and completion status.

Args:
    user_id: The internal user ID to start the analytics flow for

Returns:
    tuple[str, bool]: Response message and completion status (always True for this flow)
- [OK] `start_checkin(self, user_id)` - Public method to start a check-in flow for a user.
This is the proper way to initiate check-ins from external modules.
- [OK] `start_messages_flow(self, user_id)` - Start the messages flow for a user.

Initiates the messages management flow by routing the "show messages" command
through the interaction manager. Returns the response message and completion status.

Args:
    user_id: The internal user ID to start the messages flow for

Returns:
    tuple[str, bool]: Response message and completion status (always True for this flow)
- [MISSING] `start_profile_flow(self, user_id)` - No description
- [MISSING] `start_schedule_flow(self, user_id)` - No description
- [OK] `start_task_due_date_flow(self, user_id, task_id)` - Start a task due date/time flow.
Called by task handler after creating a task without a due date.
- [OK] `start_task_reminder_followup(self, user_id, task_id)` - Start a task reminder follow-up flow.
Called by task handler after creating a task with a due date.
- [OK] `start_tasks_flow(self, user_id)` - Starter for a future tasks multi-step flow (placeholder).
**Classes:**
- [MISSING] `ConversationManager` - No description
  - [OK] `ConversationManager.__init__(self)` - Initialize the object.
  - [OK] `ConversationManager._cache_expired_checkin_order(self, user_id, user_state)` - Cache the question order for a same-day restart after expiration.
  - [OK] `ConversationManager._complete_checkin(self, user_id, user_state)` - Complete the check-in and provide personalized feedback
  - [OK] `ConversationManager._expire_inactive_checkins(self, user_id)` - Remove stale check-in flows that have been idle beyond the allowed window.
  - [OK] `ConversationManager._generate_completion_message(self, user_id, data)` - Generate a personalized completion message based on responses
  - [OK] `ConversationManager._generate_context_aware_reminder_suggestions(self, user_id, task_id)` - Generate reminder period suggestions based on task's due date/time.

Examples:
- Task due in 6 days (no time) -> "1 to 2 days before", "3 to 4 days before"
- Task due in 12 days at 10:00 AM -> "1 to 2 hours before", "1 to 2 days before", "3 to 5 days before"
  - [OK] `ConversationManager._get_cached_checkin_order(self, user_id)` - Return same-day cached question order if present and valid.
  - [OK] `ConversationManager._get_next_question(self, user_id, user_state)` - Get the next question in the check-in flow
  - [OK] `ConversationManager._get_personalized_welcome(self, user_id, question_count)` - Generate a personalized welcome message based on user history
  - [OK] `ConversationManager._get_question_text(self, question_key, previous_data, user_id)` - Get appropriate question text based on question type and previous responses
  - [OK] `ConversationManager._handle_checkin(self, user_id, user_state, message_text)` - Enhanced check-in flow with dynamic questions and better validation
  - [OK] `ConversationManager._handle_command_during_checkin(self, user_id, message_text)` - Handle common commands while user is in a checkin flow
  - [OK] `ConversationManager._handle_list_items_flow(self, user_id, user_state, message_text)` - Handle continuation of list items flow.
  - [OK] `ConversationManager._handle_note_body_flow(self, user_id, user_state, message_text)` - Handle continuation of note body flow.
  - [OK] `ConversationManager._handle_task_due_date_flow(self, user_id, user_state, message_text)` - Handle continuation of task due date/time flow.
  - [OK] `ConversationManager._handle_task_reminder_followup(self, user_id, user_state, message_text)` - Handle user's response to reminder period question after task creation.

Parses natural language responses like:
- "30 minutes to an hour before"
- "3 to 5 hours before"
- "1 to 2 days before"
- "No reminders needed" / "No" / "Skip"
  - [OK] `ConversationManager._load_user_states(self)` - Load user states from disk with comprehensive logging
  - [OK] `ConversationManager._parse_date_time_from_text(self, text)` - Parse date and time from natural language text.

Returns: (date_str in YYYY-MM-DD format, time_str in HH:MM format or None)
  - [OK] `ConversationManager._parse_reminder_periods_from_text(self, user_id, task_id, text)` - Parse reminder periods from natural language text.

Examples:
- "30 minutes to an hour before" -> reminder 30-60 min before due time
- "3 to 5 hours before" -> reminder 3-5 hours before due time
- "1 to 2 days before" -> reminder 1-2 days before due date

Returns list of reminder period dicts with date, start_time, end_time.
  - [OK] `ConversationManager._parse_time_from_text(self, text)` - Parse time from natural language text.

Examples:
- "10am", "10:00am", "10:30am" -> "10:00", "10:30"
- "2pm", "14:00" -> "14:00"
- "at 3pm" -> "15:00"
  - [OK] `ConversationManager._save_user_states(self)` - Save user states to disk with comprehensive logging and error handling
  - [OK] `ConversationManager._select_checkin_questions_with_weighting(self, user_id, enabled_questions)` - Select check-in questions using weighted randomization with always/sometimes and min/max configuration.

Args:
    user_id: User ID
    enabled_questions: Dictionary of enabled questions from user preferences
        Each question can have:
        - 'enabled': bool (whether question is enabled)
        - 'always_include': bool (whether to always include this question)
        - 'sometimes_include': bool (whether to sometimes include this question)

Returns:
    List of question keys in selected order
  - [OK] `ConversationManager._start_dynamic_checkin(self, user_id)` - Start a dynamic check-in flow based on user preferences with weighted question selection
  - [OK] `ConversationManager._validate_response(self, question_key, response, user_id)` - Validate user response based on question type using dynamic manager
  - [OK] `ConversationManager.clear_all_states(self)` - Clear all user states - primarily for testing.
  - [OK] `ConversationManager.clear_stuck_flows(self, user_id)` - Clear any stuck conversation flows for a user.
This is a safety mechanism to reset flow state when it gets stuck.
  - [OK] `ConversationManager.expire_checkin_flow_due_to_unrelated_outbound(self, user_id)` - Expire an active check-in flow when an unrelated outbound message is sent.
Safe no-op if no flow or different flow is active.
  - [OK] `ConversationManager.handle_contextual_question(self, user_id, message_text)` - Handle a single contextual question without entering a conversation flow.
Perfect for one-off questions that benefit from user context.
  - [OK] `ConversationManager.handle_inbound_message(self, user_id, message_text)` - Primary entry point. Takes user's message and returns a (reply_text, completed).

Now defaults to contextual chat for all messages unless user is in a specific flow
or uses a special command.
  - [OK] `ConversationManager.restart_checkin(self, user_id)` - Force restart a check-in flow, clearing any existing checkin state.
This should be used when user explicitly wants to start over.
  - [OK] `ConversationManager.start_analytics_flow(self, user_id)` - Start the analytics flow for a user.

Initiates the analytics display flow by routing the "show analytics" command
through the interaction manager. Returns the response message and completion status.

Args:
    user_id: The internal user ID to start the analytics flow for

Returns:
    tuple[str, bool]: Response message and completion status (always True for this flow)
  - [OK] `ConversationManager.start_checkin(self, user_id)` - Public method to start a check-in flow for a user.
This is the proper way to initiate check-ins from external modules.
  - [OK] `ConversationManager.start_messages_flow(self, user_id)` - Start the messages flow for a user.

Initiates the messages management flow by routing the "show messages" command
through the interaction manager. Returns the response message and completion status.

Args:
    user_id: The internal user ID to start the messages flow for

Returns:
    tuple[str, bool]: Response message and completion status (always True for this flow)
  - [MISSING] `ConversationManager.start_profile_flow(self, user_id)` - No description
  - [MISSING] `ConversationManager.start_schedule_flow(self, user_id)` - No description
  - [OK] `ConversationManager.start_task_due_date_flow(self, user_id, task_id)` - Start a task due date/time flow.
Called by task handler after creating a task without a due date.
  - [OK] `ConversationManager.start_task_reminder_followup(self, user_id, task_id)` - Start a task reminder follow-up flow.
Called by task handler after creating a task with a due date.
  - [OK] `ConversationManager.start_tasks_flow(self, user_id)` - Starter for a future tasks multi-step flow (placeholder).

#### `communication/message_processing/intent_validation.py`
**Functions:**
- [OK] `is_valid_intent(intent, interaction_handlers)` - Return True if any handler can handle the given intent.

Args:
    intent: The intent string to validate.
    interaction_handlers: Mapping of handler name to handler instance;
        each value must have a can_handle(intent) method.

Returns:
    True if any handler's can_handle(intent) returns True, False otherwise.

#### `communication/message_processing/interaction_manager.py`
**Functions:**
- [OK] `__init__(self)` - Special Python method
- [MISSING] `_augment_suggestions(self, parsed_command, response)` - No description
- [OK] `_enhance_response_with_ai(self, user_id, response, parsed_command)` - Enhance a structured response with AI contextual information
- [OK] `_extract_intent_from_text(self, text)` - Extract intent from AI text response
- [OK] `_get_commands_response(self)` - Return a concise, channel-agnostic commands list for quick discovery.
- [OK] `_get_help_response(self, user_id, message)` - Get a help response when command parsing fails
- [OK] `_handle_contextual_chat(self, user_id, message, channel_type)` - Handle contextual chat using AI chatbot with mixed intent support
- [OK] `_handle_structured_command(self, user_id, parsing_result, channel_type)` - Handle a structured command using interaction handlers
- [OK] `_is_ai_command_response(self, ai_response)` - Check if AI response indicates this was a command
- [OK] `_is_clarification_request(self, ai_response)` - Check if AI response is asking for clarification
- [OK] `_is_valid_intent(self, intent)` - Check if intent is supported by any handler
- [OK] `_parse_ai_command_response(self, ai_response, original_message)` - Parse AI command response into ParsedCommand
- [OK] `_try_ai_command_parsing(self, user_id, message, channel_type)` - Attempt to parse ambiguous messages using AI command parsing.
- [OK] `add_suggestion(text)` - Add a suggestion if it is unique and space remains.
- [OK] `get_available_commands(self, user_id)` - Get list of available commands for the user
- [OK] `get_command_definitions(self)` - Return canonical command definitions: name, mapped_message, description.
- [OK] `get_interaction_manager()` - Get the global interaction manager instance
- [OK] `get_mapped_message(self)` - Get the mapped message, defaulting to !{name} if not specified.
- [OK] `get_slash_command_map(self)` - Expose slash command mappings without coupling callers to internals.
Returns a dict like {'tasks': 'show my tasks', ...} suitable for Discord registration.
- [OK] `get_user_suggestions(self, user_id, context)` - Get personalized suggestions for the user
- [OK] `handle_message(self, user_id, message, channel_type)` - Main entry point for handling user messages.

Args:
    user_id: The user's ID
    message: The user's message
    channel_type: Type of channel (discord, email)

Returns:
    InteractionResponse with appropriate response
- [OK] `handle_user_message(user_id, message, channel_type)` - Convenience function to handle a user message
- [OK] `parse_due(task)` - Parse due date/time into a datetime for sorting.
Uses canonical parsers from time_utilities (no inline parsing).
**Classes:**
- [OK] `CommandDefinition` - Canonical command definition.

- name: The slash/bang command name without prefix (e.g. "tasks")
- mapped_message: The internal message text to feed the parser/handlers (e.g. "show my tasks")
    - Use None for "discoverability-only" commands (no mapping/translation)
- description: Human-facing help text
- is_flow: Whether this command should invoke a flow starter directly
  - [OK] `CommandDefinition.get_mapped_message(self)` - Get the mapped message, defaulting to !{name} if not specified.
- [OK] `InteractionManager` - Main manager for handling user interactions across all channels
  - [OK] `InteractionManager.__init__(self)` - Special Python method
  - [MISSING] `InteractionManager._augment_suggestions(self, parsed_command, response)` - No description
  - [OK] `InteractionManager._enhance_response_with_ai(self, user_id, response, parsed_command)` - Enhance a structured response with AI contextual information
  - [OK] `InteractionManager._extract_intent_from_text(self, text)` - Extract intent from AI text response
  - [OK] `InteractionManager._get_commands_response(self)` - Return a concise, channel-agnostic commands list for quick discovery.
  - [OK] `InteractionManager._get_help_response(self, user_id, message)` - Get a help response when command parsing fails
  - [OK] `InteractionManager._handle_contextual_chat(self, user_id, message, channel_type)` - Handle contextual chat using AI chatbot with mixed intent support
  - [OK] `InteractionManager._handle_structured_command(self, user_id, parsing_result, channel_type)` - Handle a structured command using interaction handlers
  - [OK] `InteractionManager._is_ai_command_response(self, ai_response)` - Check if AI response indicates this was a command
  - [OK] `InteractionManager._is_clarification_request(self, ai_response)` - Check if AI response is asking for clarification
  - [OK] `InteractionManager._is_valid_intent(self, intent)` - Check if intent is supported by any handler
  - [OK] `InteractionManager._parse_ai_command_response(self, ai_response, original_message)` - Parse AI command response into ParsedCommand
  - [OK] `InteractionManager._try_ai_command_parsing(self, user_id, message, channel_type)` - Attempt to parse ambiguous messages using AI command parsing.
  - [OK] `InteractionManager.get_available_commands(self, user_id)` - Get list of available commands for the user
  - [OK] `InteractionManager.get_command_definitions(self)` - Return canonical command definitions: name, mapped_message, description.
  - [OK] `InteractionManager.get_slash_command_map(self)` - Expose slash command mappings without coupling callers to internals.
Returns a dict like {'tasks': 'show my tasks', ...} suitable for Discord registration.
  - [OK] `InteractionManager.get_user_suggestions(self, user_id, context)` - Get personalized suggestions for the user
  - [OK] `InteractionManager.handle_message(self, user_id, message, channel_type)` - Main entry point for handling user messages.

Args:
    user_id: The user's ID
    message: The user's message
    channel_type: Type of channel (discord, email)

Returns:
    InteractionResponse with appropriate response

#### `communication/message_processing/message_router.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the message router
- [OK] `_route_bang_command(self, message)` - Route a bang command with validation.

Returns:
    RoutingResult: Routing result, UNKNOWN if failed
- [OK] `_route_slash_command(self, message)` - Route a slash command with validation.

Returns:
    RoutingResult: Routing result, UNKNOWN if failed
- [OK] `get_bang_command_map(self)` - Get bang command map with validation.

Returns:
    Dict[str, str]: Bang command map, empty dict if failed
- [OK] `get_command_definitions(self)` - Get command definitions with validation.

Returns:
    List[Dict[str, str]]: Command definitions, empty list if failed
- [OK] `get_command_mapping(self, command_name)` - Get command mapping with validation.

Returns:
    Optional[str]: Command mapping, None if failed
- [OK] `get_message_router()` - Get the global message router instance
- [OK] `get_slash_command_map(self)` - Get slash command map with validation.

Returns:
    Dict[str, str]: Slash command map, empty dict if failed
- [OK] `is_flow_command(self, command_name)` - Check if command is flow command with validation.

Returns:
    bool: True if flow command, False otherwise
- [OK] `route_message(self, message)` - Route a message to determine its type and appropriate handling.

Args:
    message: The user's message
    
Returns:
    RoutingResult with message type and routing information
**Classes:**
- [OK] `MessageRouter` - Routes messages to appropriate handlers based on message type and content
  - [OK] `MessageRouter.__init__(self)` - Initialize the message router
  - [OK] `MessageRouter._route_bang_command(self, message)` - Route a bang command with validation.

Returns:
    RoutingResult: Routing result, UNKNOWN if failed
  - [OK] `MessageRouter._route_slash_command(self, message)` - Route a slash command with validation.

Returns:
    RoutingResult: Routing result, UNKNOWN if failed
  - [OK] `MessageRouter.get_bang_command_map(self)` - Get bang command map with validation.

Returns:
    Dict[str, str]: Bang command map, empty dict if failed
  - [OK] `MessageRouter.get_command_definitions(self)` - Get command definitions with validation.

Returns:
    List[Dict[str, str]]: Command definitions, empty list if failed
  - [OK] `MessageRouter.get_command_mapping(self, command_name)` - Get command mapping with validation.

Returns:
    Optional[str]: Command mapping, None if failed
  - [OK] `MessageRouter.get_slash_command_map(self)` - Get slash command map with validation.

Returns:
    Dict[str, str]: Slash command map, empty dict if failed
  - [OK] `MessageRouter.is_flow_command(self, command_name)` - Check if command is flow command with validation.

Returns:
    bool: True if flow command, False otherwise
  - [OK] `MessageRouter.route_message(self, message)` - Route a message to determine its type and appropriate handling.

Args:
    message: The user's message
    
Returns:
    RoutingResult with message type and routing information
- [OK] `MessageType` - Types of messages that can be routed
- [OK] `RoutingResult` - Result of message routing

### `core/` - Core System Modules

#### `core/__init__.py`
**Functions:**
- [OK] `__getattr__(name)` - Lazy import handler for items with circular dependencies

#### `core/auto_cleanup.py`
**Functions:**
- [OK] `_calculate_cache_size__calculate_pyc_files_size(pyc_files)` - Calculate total size of standalone .pyc files.
- [OK] `_calculate_cache_size__calculate_pycache_directories_size(pycache_dirs)` - Calculate total size of __pycache__ directories.
- [OK] `_get_cleanup_status__build_status_response(last_date, days_since, next_cleanup)` - Build the final status response dictionary.
- [OK] `_get_cleanup_status__calculate_days_since_cleanup(last_cleanup_timestamp)` - Calculate days since last cleanup.
- [OK] `_get_cleanup_status__format_next_cleanup_date(last_date)` - Format the next cleanup date or return 'Overdue'.
- [OK] `_get_cleanup_status__get_invalid_tracker_status()` - Get status when cleanup tracker exists but contains an invalid timestamp.
- [OK] `_get_cleanup_status__get_never_cleaned_status()` - Get status when cleanup has never been performed.
- [OK] `_perform_cleanup__discover_cache_files(root_path)` - Discover all cache files and directories in the given root path.
- [OK] `_perform_cleanup__log_completion_results(removed_dirs, removed_files, total_size)` - Log the final cleanup results and statistics.
- [OK] `_perform_cleanup__log_discovery_results(pycache_dirs, pyc_files)` - Calculate total size and log discovery results.
- [OK] `_perform_cleanup__remove_cache_directories(pycache_dirs)` - Remove all __pycache__ directories.
- [OK] `_perform_cleanup__remove_cache_files(pycache_dirs, pyc_files)` - Remove all discovered cache directories and files.
- [OK] `_perform_cleanup__remove_cache_files_list(pyc_files)` - Remove all standalone .pyc files.
- [OK] `archive_old_messages_for_all_users()` - Archive old messages for all users during monthly cleanup.
This runs alongside the cache cleanup to maintain message file sizes.
- [OK] `auto_cleanup_if_needed(root_path, interval_days)` - Main function to check if cleanup is needed and perform it if so.
Returns True if cleanup was performed, False if not needed.
- [OK] `calculate_cache_size(pycache_dirs, pyc_files)` - Calculate total size of cache files.
- [OK] `cleanup_data_directory()` - Clean up old files in the data directory (backups, requests, archives).
This can be called independently of the full auto_cleanup cycle.
Returns True if cleanup was performed, False otherwise.
- [OK] `cleanup_old_backup_files()` - Clean up old backup files from data/backups directory.
Uses same retention policy as BackupManager (30 days by default, max 10 files).
- [OK] `cleanup_old_message_archives()` - Clean up old message archive files from user directories.
Removes archive files older than 90 days (archives are already compressed).
- [OK] `cleanup_old_request_files()` - Clean up old request files from data/requests directory.
Removes request files older than 7 days.
- [OK] `cleanup_tests_data_directory()` - Clean up temporary files and directories in tests/data/ directory.
Removes tmp_* directories, test JSON files, and other test artifacts.
This is separate from production data cleanup.
- [OK] `find_pyc_files(root_path)` - Find all .pyc files recursively.
- [OK] `find_pycache_dirs(root_path)` - Find all __pycache__ directories recursively.
- [OK] `get_cleanup_status()` - Get information about the cleanup status.
- [OK] `get_last_cleanup_timestamp()` - Get the timestamp of the last cleanup from tracker file.
- [OK] `perform_cleanup(root_path)` - Perform the actual cleanup of cache files.
- [OK] `should_run_cleanup(interval_days)` - Check if cleanup should run based on last cleanup time.
- [OK] `update_cleanup_timestamp()` - Update the cleanup tracker file with current timestamp.

#### `core/backup_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the BackupManager with default settings.

Sets up backup directory, maximum backup count, and ensures backup directory exists.
- [OK] `_add_directory_to_zip(self, zipf, directory, zip_path)` - Recursively add a directory to the zip file.
- [OK] `_backup_config_files(self, zipf)` - Backup configuration files.
- [OK] `_backup_log_files(self, zipf)` - Backup log files.
- [OK] `_backup_project_code(self, zipf)` - Backup project code files (Python files, configs, etc.).
- [OK] `_backup_user_data(self, zipf)` - Backup all user data directories.
- [OK] `_cleanup_old_backups(self)` - Remove old backups by count and age retention policy.
- [OK] `_create_backup__cleanup_old_backups(self)` - Clean up old backups by count and age.
- [OK] `_create_backup__create_zip_file(self, backup_path, backup_name, include_users, include_config, include_logs, include_code)` - Create the backup zip file with all specified components.
- [OK] `_create_backup__setup_backup(self, backup_name)` - Setup backup name and path parameters.
- [OK] `_create_backup_manifest(self, zipf, backup_name, include_users, include_config, include_logs, include_code)` - Create a manifest file describing the backup contents.
- [OK] `_get_backup_info(self, backup_path)` - Get information about a specific backup.
- [OK] `_restore_config_files(self, zipf)` - Restore configuration files from backup.
- [OK] `_restore_user_data(self, zipf)` - Restore user data from backup.
- [OK] `_validate_backup__check_file_exists(self, backup_path, errors)` - Check if the backup file exists and add error if not.
- [OK] `_validate_backup__check_file_integrity(self, zipf, errors)` - Check if the zip file is not corrupted.
- [OK] `_validate_backup__validate_content_requirements(self, zipf, errors)` - Validate that backup contains required content.
- [OK] `_validate_backup__validate_manifest(self, zipf, errors)` - Validate the backup manifest file.
- [OK] `_validate_backup__validate_zip_file(self, backup_path)` - Validate zip file integrity and contents.
- [OK] `_validate_system_state__ensure_user_data_directory()` - Ensure the user data directory exists, creating it if necessary.
- [OK] `_validate_system_state__validate_user_index()` - Validate the user index file and corresponding user directories.
- [OK] `create_automatic_backup(operation_name)` - Create an automatic backup before major operations.

Args:
    operation_name: Name of the operation being performed

Returns:
    Path to the backup file, or None if failed
- [OK] `create_backup(self, backup_name, include_users, include_config, include_logs, include_code)` - Create a comprehensive backup with validation.

Returns:
    Optional[str]: Path to backup file, None if failed
- [OK] `ensure_backup_directory(self)` - Ensure backup directory exists with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `list_backups(self)` - List all available backups with metadata.
- [OK] `perform_safe_operation(operation_func)` - Perform an operation with automatic backup and rollback capability.

Args:
    operation_func: Function to perform
    *args: Arguments for the operation function
    **kwargs: Keyword arguments for the operation function

Returns:
    True if operation succeeded, False if it failed and was rolled back
- [OK] `restore_backup(self, backup_path, restore_users, restore_config)` - Restore backup with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `validate_backup(self, backup_path)` - Validate a backup file for integrity and completeness.

Args:
    backup_path: Path to the backup file

Returns:
    Tuple of (is_valid, list_of_errors)
- [OK] `validate_system_state()` - Validate the current system state for consistency.

Returns:
    True if system is in a valid state, False otherwise
**Classes:**
- [OK] `BackupManager` - Manages automatic backups and rollback operations.
  - [OK] `BackupManager.__init__(self)` - Initialize the BackupManager with default settings.

Sets up backup directory, maximum backup count, and ensures backup directory exists.
  - [OK] `BackupManager._add_directory_to_zip(self, zipf, directory, zip_path)` - Recursively add a directory to the zip file.
  - [OK] `BackupManager._backup_config_files(self, zipf)` - Backup configuration files.
  - [OK] `BackupManager._backup_log_files(self, zipf)` - Backup log files.
  - [OK] `BackupManager._backup_project_code(self, zipf)` - Backup project code files (Python files, configs, etc.).
  - [OK] `BackupManager._backup_user_data(self, zipf)` - Backup all user data directories.
  - [OK] `BackupManager._cleanup_old_backups(self)` - Remove old backups by count and age retention policy.
  - [OK] `BackupManager._create_backup__cleanup_old_backups(self)` - Clean up old backups by count and age.
  - [OK] `BackupManager._create_backup__create_zip_file(self, backup_path, backup_name, include_users, include_config, include_logs, include_code)` - Create the backup zip file with all specified components.
  - [OK] `BackupManager._create_backup__setup_backup(self, backup_name)` - Setup backup name and path parameters.
  - [OK] `BackupManager._create_backup_manifest(self, zipf, backup_name, include_users, include_config, include_logs, include_code)` - Create a manifest file describing the backup contents.
  - [OK] `BackupManager._get_backup_info(self, backup_path)` - Get information about a specific backup.
  - [OK] `BackupManager._restore_config_files(self, zipf)` - Restore configuration files from backup.
  - [OK] `BackupManager._restore_user_data(self, zipf)` - Restore user data from backup.
  - [OK] `BackupManager._validate_backup__check_file_exists(self, backup_path, errors)` - Check if the backup file exists and add error if not.
  - [OK] `BackupManager._validate_backup__check_file_integrity(self, zipf, errors)` - Check if the zip file is not corrupted.
  - [OK] `BackupManager._validate_backup__validate_content_requirements(self, zipf, errors)` - Validate that backup contains required content.
  - [OK] `BackupManager._validate_backup__validate_manifest(self, zipf, errors)` - Validate the backup manifest file.
  - [OK] `BackupManager._validate_backup__validate_zip_file(self, backup_path)` - Validate zip file integrity and contents.
  - [OK] `BackupManager.create_backup(self, backup_name, include_users, include_config, include_logs, include_code)` - Create a comprehensive backup with validation.

Returns:
    Optional[str]: Path to backup file, None if failed
  - [OK] `BackupManager.ensure_backup_directory(self)` - Ensure backup directory exists with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `BackupManager.list_backups(self)` - List all available backups with metadata.
  - [OK] `BackupManager.restore_backup(self, backup_path, restore_users, restore_config)` - Restore backup with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `BackupManager.validate_backup(self, backup_path)` - Validate a backup file for integrity and completeness.

Args:
    backup_path: Path to the backup file

Returns:
    Tuple of (is_valid, list_of_errors)

#### `core/checkin_analytics.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the CheckinAnalytics instance.

This class provides analytics and insights from check-in data.
- [OK] `_bucket_scale_value(value)` - Bucket a numeric value to the nearest 1-5 integer (half-up).
- [OK] `_calculate_energy_score(self, checkins)` - Calculate energy score (0-100)
- [OK] `_calculate_habit_score(self, checkins)` - Calculate habit score (0-100)
- [OK] `_calculate_mood_score(self, checkins)` - Calculate mood score (0-100)
- [OK] `_calculate_overall_completion(self, habit_stats)` - Calculate overall habit completion rate
- [OK] `_calculate_sleep_consistency(self, hours)` - Calculate sleep consistency (lower variance = more consistent)
- [OK] `_calculate_sleep_duration(self, sleep_time, wake_time)` - Calculate sleep duration in hours from sleep_time and wake_time (HH:MM format).
- [OK] `_calculate_sleep_score(self, checkins)` - Calculate sleep score (0-100)
- [OK] `_calculate_streak(self, checkins, habit_key)` - Calculate current and best streaks for a habit
- [OK] `_coerce_numeric(value)` - Convert numeric-like values to float, skipping invalid or skipped entries.
- [OK] `_coerce_sleep_hours(self, value)` - Convert sleep schedule values into hours.
- [OK] `_coerce_yes_no(self, value)` - Convert yes/no-like values to bool.
- [OK] `_get_energy_distribution(self, energies)` - Calculate distribution of energy scores (bucketed to 1-5).
- [OK] `_get_habit_status(self, completion_rate)` - Get status description for habit completion rate
- [OK] `_get_mood_distribution(self, moods)` - Calculate distribution of mood scores (bucketed to 1-5).
- [OK] `_get_questions_asked(self, checkin)` - Return the list of questions asked for a check-in.
- [OK] `_get_score_level(self, score)` - Get wellness score level description
- [OK] `_get_sleep_recommendations(self, avg_hours, avg_quality, poor_days)` - Generate sleep recommendations
- [OK] `_get_wellness_recommendations(self, mood_score, energy_score, habit_score, sleep_score)` - Generate wellness recommendations based on component scores
- [OK] `_is_answered_value(self, value)` - Return True if the value counts as answered.
- [OK] `_is_question_asked(self, checkin, question_key)` - Check if a question was asked for a check-in.
- [OK] `convert_score_100_to_5(score_100)` - Convert a score from 0-100 scale to 1-5 scale for display.

Args:
    score_100: Score on 0-100 scale

Returns:
    Score on 1-5 scale, rounded to 1 decimal place
- [OK] `convert_score_5_to_100(score_5)` - Convert a score from 1-5 scale to 0-100 scale for calculations.

Args:
    score_5: Score on 1-5 scale

Returns:
    Score on 0-100 scale
- [OK] `get_available_data_types(self, user_id, days)` - Detect what types of data are available for analytics
- [OK] `get_basic_analytics(self, user_id, days)` - Return basic per-question stats grouped by category.
- [OK] `get_checkin_history(self, user_id, days)` - Get check-in history with proper date formatting
- [OK] `get_completion_rate(self, user_id, days)` - Calculate overall completion rate for check-ins
- [OK] `get_energy_trends(self, user_id, days)` - Analyze energy trends over the specified period
- [OK] `get_habit_analysis(self, user_id, days)` - Analyze habit patterns from check-in data
- [OK] `get_mood_trends(self, user_id, days)` - Analyze mood trends over the specified period
- [OK] `get_quantitative_summaries(self, user_id, days, enabled_fields)` - Compute per-field averages and ranges for opted-in quantitative fields.

Parameters:
    user_id: target user
    days: number of recent check-ins to analyze
    enabled_fields: list of fields to include (e.g., ['mood','energy','stress','sleep_quality','anxiety'])

Returns mapping: { field: { 'average': float, 'min': float, 'max': float, 'count': int } }
Only includes fields that appear in the data and are in enabled_fields if provided.
- [OK] `get_sleep_analysis(self, user_id, days)` - Analyze sleep patterns from check-in data
- [OK] `get_task_weekly_stats(self, user_id, days)` - Calculate weekly statistics for tasks
- [OK] `get_wellness_score(self, user_id, days)` - Calculate overall wellness score from check-in data
**Classes:**
- [MISSING] `CheckinAnalytics` - No description
  - [OK] `CheckinAnalytics.__init__(self)` - Initialize the CheckinAnalytics instance.

This class provides analytics and insights from check-in data.
  - [OK] `CheckinAnalytics._bucket_scale_value(value)` - Bucket a numeric value to the nearest 1-5 integer (half-up).
  - [OK] `CheckinAnalytics._calculate_energy_score(self, checkins)` - Calculate energy score (0-100)
  - [OK] `CheckinAnalytics._calculate_habit_score(self, checkins)` - Calculate habit score (0-100)
  - [OK] `CheckinAnalytics._calculate_mood_score(self, checkins)` - Calculate mood score (0-100)
  - [OK] `CheckinAnalytics._calculate_overall_completion(self, habit_stats)` - Calculate overall habit completion rate
  - [OK] `CheckinAnalytics._calculate_sleep_consistency(self, hours)` - Calculate sleep consistency (lower variance = more consistent)
  - [OK] `CheckinAnalytics._calculate_sleep_duration(self, sleep_time, wake_time)` - Calculate sleep duration in hours from sleep_time and wake_time (HH:MM format).
  - [OK] `CheckinAnalytics._calculate_sleep_score(self, checkins)` - Calculate sleep score (0-100)
  - [OK] `CheckinAnalytics._calculate_streak(self, checkins, habit_key)` - Calculate current and best streaks for a habit
  - [OK] `CheckinAnalytics._coerce_numeric(value)` - Convert numeric-like values to float, skipping invalid or skipped entries.
  - [OK] `CheckinAnalytics._coerce_sleep_hours(self, value)` - Convert sleep schedule values into hours.
  - [OK] `CheckinAnalytics._coerce_yes_no(self, value)` - Convert yes/no-like values to bool.
  - [OK] `CheckinAnalytics._get_energy_distribution(self, energies)` - Calculate distribution of energy scores (bucketed to 1-5).
  - [OK] `CheckinAnalytics._get_habit_status(self, completion_rate)` - Get status description for habit completion rate
  - [OK] `CheckinAnalytics._get_mood_distribution(self, moods)` - Calculate distribution of mood scores (bucketed to 1-5).
  - [OK] `CheckinAnalytics._get_questions_asked(self, checkin)` - Return the list of questions asked for a check-in.
  - [OK] `CheckinAnalytics._get_score_level(self, score)` - Get wellness score level description
  - [OK] `CheckinAnalytics._get_sleep_recommendations(self, avg_hours, avg_quality, poor_days)` - Generate sleep recommendations
  - [OK] `CheckinAnalytics._get_wellness_recommendations(self, mood_score, energy_score, habit_score, sleep_score)` - Generate wellness recommendations based on component scores
  - [OK] `CheckinAnalytics._is_answered_value(self, value)` - Return True if the value counts as answered.
  - [OK] `CheckinAnalytics._is_question_asked(self, checkin, question_key)` - Check if a question was asked for a check-in.
  - [OK] `CheckinAnalytics.convert_score_100_to_5(score_100)` - Convert a score from 0-100 scale to 1-5 scale for display.

Args:
    score_100: Score on 0-100 scale

Returns:
    Score on 1-5 scale, rounded to 1 decimal place
  - [OK] `CheckinAnalytics.convert_score_5_to_100(score_5)` - Convert a score from 1-5 scale to 0-100 scale for calculations.

Args:
    score_5: Score on 1-5 scale

Returns:
    Score on 0-100 scale
  - [OK] `CheckinAnalytics.get_available_data_types(self, user_id, days)` - Detect what types of data are available for analytics
  - [OK] `CheckinAnalytics.get_basic_analytics(self, user_id, days)` - Return basic per-question stats grouped by category.
  - [OK] `CheckinAnalytics.get_checkin_history(self, user_id, days)` - Get check-in history with proper date formatting
  - [OK] `CheckinAnalytics.get_completion_rate(self, user_id, days)` - Calculate overall completion rate for check-ins
  - [OK] `CheckinAnalytics.get_energy_trends(self, user_id, days)` - Analyze energy trends over the specified period
  - [OK] `CheckinAnalytics.get_habit_analysis(self, user_id, days)` - Analyze habit patterns from check-in data
  - [OK] `CheckinAnalytics.get_mood_trends(self, user_id, days)` - Analyze mood trends over the specified period
  - [OK] `CheckinAnalytics.get_quantitative_summaries(self, user_id, days, enabled_fields)` - Compute per-field averages and ranges for opted-in quantitative fields.

Parameters:
    user_id: target user
    days: number of recent check-ins to analyze
    enabled_fields: list of fields to include (e.g., ['mood','energy','stress','sleep_quality','anxiety'])

Returns mapping: { field: { 'average': float, 'min': float, 'max': float, 'count': int } }
Only includes fields that appear in the data and are in enabled_fields if provided.
  - [OK] `CheckinAnalytics.get_sleep_analysis(self, user_id, days)` - Analyze sleep patterns from check-in data
  - [OK] `CheckinAnalytics.get_task_weekly_stats(self, user_id, days)` - Calculate weekly statistics for tasks
  - [OK] `CheckinAnalytics.get_wellness_score(self, user_id, days)` - Calculate overall wellness score from check-in data

#### `core/checkin_dynamic_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the dynamic check-in manager.
- [OK] `_get_numeric_response_fallback(self, question_responses, answer_value)` - Return response list for nearest integer key when float answers are provided.
- [OK] `_load_data(self)` - Load questions and responses data from JSON files.
- [OK] `_normalize_time(self, time_str)` - Normalize time string to HH:MM format (24-hour).

Supports formats like:
- "11:30 PM" -> "23:30"
- "7:00 AM" -> "07:00"
- "23:30" -> "23:30"
- "7:00" -> "07:00" (assumes AM if no AM/PM)
- [OK] `_parse_numerical_response(self, answer)` - Parse numerical responses including written numbers, decimals, and mixed formats.
- [OK] `_parse_time_pair_response(self, answer)` - Parse sleep time and wake time from user response.

Supports formats like:
- "11:30 PM and 7:00 AM"
- "23:30 and 07:00"
- "11:30pm, 7:00am"
- "11:30 PM, 7:00 AM"
- [OK] `build_next_question_with_response(self, question_key, previous_question_key, previous_answer)` - Build the next question text with a response statement from the previous answer.
- [OK] `delete_custom_question(self, user_id, question_key)` - Delete a custom question from user preferences.
- [OK] `get_all_questions(self, user_id)` - Get all question definitions, merging predefined and custom questions.

Custom questions take precedence over predefined questions with the same key.
- [OK] `get_categories(self)` - Get all question categories.
- [OK] `get_custom_questions(self, user_id)` - Get custom questions for a specific user from preferences.
- [OK] `get_enabled_questions_for_ui(self, user_id)` - Get questions formatted for UI display with enabled_by_default status.

Includes both predefined and custom questions if user_id is provided.
- [OK] `get_question_definition(self, question_key, user_id)` - Get the definition for a specific question.

Checks custom questions first (if user_id provided), then predefined questions.
- [OK] `get_question_templates(self)` - Get available question templates for creating custom questions.
- [OK] `get_question_text(self, question_key, user_id)` - Get the question text for a specific question.
- [OK] `get_question_type(self, question_key)` - Get the type of a specific question.
- [OK] `get_question_validation(self, question_key)` - Get validation rules for a specific question.
- [OK] `get_response_statement(self, question_key, answer_value)` - Get a random response statement for a question answer.
- [OK] `get_transition_phrase(self)` - Get a random transition phrase.
- [OK] `save_custom_question(self, user_id, question_key, question_def)` - Save a custom question to user preferences.
- [OK] `validate_answer(self, question_key, answer, user_id)` - Validate an answer for a specific question.
**Classes:**
- [OK] `DynamicCheckinManager` - Manages dynamic check-in questions and responses loaded from JSON files.
  - [OK] `DynamicCheckinManager.__init__(self)` - Initialize the dynamic check-in manager.
  - [OK] `DynamicCheckinManager._get_numeric_response_fallback(self, question_responses, answer_value)` - Return response list for nearest integer key when float answers are provided.
  - [OK] `DynamicCheckinManager._load_data(self)` - Load questions and responses data from JSON files.
  - [OK] `DynamicCheckinManager._normalize_time(self, time_str)` - Normalize time string to HH:MM format (24-hour).

Supports formats like:
- "11:30 PM" -> "23:30"
- "7:00 AM" -> "07:00"
- "23:30" -> "23:30"
- "7:00" -> "07:00" (assumes AM if no AM/PM)
  - [OK] `DynamicCheckinManager._parse_numerical_response(self, answer)` - Parse numerical responses including written numbers, decimals, and mixed formats.
  - [OK] `DynamicCheckinManager._parse_time_pair_response(self, answer)` - Parse sleep time and wake time from user response.

Supports formats like:
- "11:30 PM and 7:00 AM"
- "23:30 and 07:00"
- "11:30pm, 7:00am"
- "11:30 PM, 7:00 AM"
  - [OK] `DynamicCheckinManager.build_next_question_with_response(self, question_key, previous_question_key, previous_answer)` - Build the next question text with a response statement from the previous answer.
  - [OK] `DynamicCheckinManager.delete_custom_question(self, user_id, question_key)` - Delete a custom question from user preferences.
  - [OK] `DynamicCheckinManager.get_all_questions(self, user_id)` - Get all question definitions, merging predefined and custom questions.

Custom questions take precedence over predefined questions with the same key.
  - [OK] `DynamicCheckinManager.get_categories(self)` - Get all question categories.
  - [OK] `DynamicCheckinManager.get_custom_questions(self, user_id)` - Get custom questions for a specific user from preferences.
  - [OK] `DynamicCheckinManager.get_enabled_questions_for_ui(self, user_id)` - Get questions formatted for UI display with enabled_by_default status.

Includes both predefined and custom questions if user_id is provided.
  - [OK] `DynamicCheckinManager.get_question_definition(self, question_key, user_id)` - Get the definition for a specific question.

Checks custom questions first (if user_id provided), then predefined questions.
  - [OK] `DynamicCheckinManager.get_question_templates(self)` - Get available question templates for creating custom questions.
  - [OK] `DynamicCheckinManager.get_question_text(self, question_key, user_id)` - Get the question text for a specific question.
  - [OK] `DynamicCheckinManager.get_question_type(self, question_key)` - Get the type of a specific question.
  - [OK] `DynamicCheckinManager.get_question_validation(self, question_key)` - Get validation rules for a specific question.
  - [OK] `DynamicCheckinManager.get_response_statement(self, question_key, answer_value)` - Get a random response statement for a question answer.
  - [OK] `DynamicCheckinManager.get_transition_phrase(self)` - Get a random transition phrase.
  - [OK] `DynamicCheckinManager.save_custom_question(self, user_id, question_key, question_def)` - Save a custom question to user preferences.
  - [OK] `DynamicCheckinManager.validate_answer(self, question_key, answer, user_id)` - Validate an answer for a specific question.

#### `core/config.py`
**Functions:**
- [OK] `__init__(self, message, missing_configs, warnings)` - Initialize the object.
- [OK] `_normalize_path(value)` - Normalize path strings from environment to avoid Windows escape issues.
- Removes CR/LF control chars
- Strips surrounding quotes
- Normalizes separators to OS-specific
- [OK] `ensure_user_directory(user_id)` - Ensure user directory exists if using subdirectories.
- [OK] `get_available_channels()` - Get list of available communication channels based on configuration.

Returns:
    List[str]: List of available channel names that can be used with ChannelFactory
- [OK] `get_backups_dir()` - Get the backups directory, redirected under tests when MHM_TESTING=1.
Returns tests/data/backups if testing, otherwise BASE_DATA_DIR/backups.
- [OK] `get_channel_class_mapping()` - Get mapping of channel names to their class names for dynamic imports.

Returns:
    Dict[str, str]: Mapping of channel name to fully qualified class name
- [OK] `get_user_data_dir(user_id)` - Get the data directory for a specific user.
- [OK] `get_user_file_path(user_id, file_type)` - Get the file path for a specific user file type.
- [OK] `print_configuration_report()` - Print a detailed configuration report to the console.
- [OK] `validate_ai_configuration()` - Validate AI-related configuration settings.
- [OK] `validate_all_configuration()` - Comprehensive configuration validation that checks all aspects of the configuration.

Returns:
    Dict containing validation results with the following structure:
    {
        'valid': bool,
        'errors': List[str],
        'warnings': List[str],
        'available_channels': List[str],
        'summary': str
    }
- [OK] `validate_and_raise_if_invalid()` - Validate configuration and raise ConfigValidationError if invalid.

Note: This function intentionally does not use @handle_errors decorator
because it is designed to raise ConfigValidationError exceptions, which
should propagate to the caller for proper error handling.

Returns:
    List of available communication channels if validation passes.

Raises:
    ConfigValidationError: If configuration is invalid with detailed error information.
- [OK] `validate_communication_channels()` - Validate communication channel configurations.
- [OK] `validate_core_paths()` - Validate that all core paths are accessible and can be created if needed.
- [OK] `validate_environment_variables()` - Check for common environment variable issues.
- [OK] `validate_file_organization_settings()` - Validate file organization settings.
- [OK] `validate_logging_configuration()` - Validate logging configuration.
- [OK] `validate_scheduler_configuration()` - Validate scheduler configuration.
**Classes:**
- [OK] `ConfigValidationError` - Custom exception for configuration validation errors with detailed information.
  - [OK] `ConfigValidationError.__init__(self, message, missing_configs, warnings)` - Initialize the object.

#### `core/error_handling.py`
**Functions:**
- [OK] `__enter__(self)` - Enter the context manager for safe file operations.

Returns:
    self: The SafeFileContext instance
- [OK] `__exit__(self, exc_type, exc_val, exc_tb)` - Exit the context manager and handle any exceptions.

Args:
    exc_type: Type of exception if any occurred
    exc_val: Exception value if any occurred
    exc_tb: Exception traceback if any occurred
- [OK] `__init__(self, message, details, recoverable)` - Initialize a new MHM error.

Args:
    message: Human-readable error message
    details: Optional dictionary with additional error details
    recoverable: Whether this error can be recovered from
- [OK] `__init__(self, name, description)` - Initialize an error recovery strategy.

Args:
    name: The name of the recovery strategy
    description: A description of what this strategy does
- [OK] `__init__(self)` - Initialize the FileNotFoundRecovery strategy.
- [OK] `__init__(self)` - Initialize the JSONDecodeRecovery strategy.
- [OK] `__init__(self)` - Initialize the NetworkRecovery strategy.
- [OK] `__init__(self)` - Initialize the ConfigurationRecovery strategy.
- [OK] `__init__(self)` - Initialize the ErrorHandler with default recovery strategies.

Sets up recovery strategies for common error types like missing files and corrupted JSON.
- [OK] `__init__(self, file_path, operation, user_id, category)` - Initialize the safe file context.

Args:
    file_path: Path to the file being operated on
    operation: Description of the operation being performed
    user_id: ID of the user performing the operation
    category: Category of the operation
- [OK] `_get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
- [OK] `_get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
- [OK] `_get_user_friendly_message(self, error, context)` - Convert technical error to user-friendly message.
- [OK] `_log_error(self, error, context)` - Log error with context.
- [MISSING] `_now_datetime_full()` - No description
- [MISSING] `_now_timestamp_full()` - No description
- [OK] `_show_user_error(self, error, context, custom_message)` - Show user-friendly error message.
- [OK] `can_handle(self, error)` - Check if this strategy can handle the given error.
- [OK] `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle FileNotFoundError or file operation errors containing "not found"
- [OK] `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle JSON decode errors or JSON-related file operation errors
- [OK] `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle network-related errors
- [OK] `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle configuration-related errors
- [MISSING] `decorator(func)` - No description
- [OK] `handle_ai_error(error, operation, user_id)` - Convenience function for handling AI-related errors.
- [OK] `handle_communication_error(error, channel, operation, user_id)` - Convenience function for handling communication errors.
- [OK] `handle_configuration_error(error, setting, operation)` - Convenience function for handling configuration errors.
- [OK] `handle_error(self, error, context, operation, user_friendly)` - Handle an error with recovery strategies and logging.

Args:
    error: The exception that occurred
    context: Additional context about the error
    operation: Description of the operation that failed
    user_friendly: Whether to show user-friendly error messages

Returns:
    True if error was recovered from, False otherwise
- [OK] `handle_errors(operation, context, user_friendly, default_return)` - Decorator to automatically handle errors in functions.

Args:
    operation: Description of the operation (defaults to function name)
    context: Additional context to pass to error handler
    user_friendly: Whether to show user-friendly error messages
    default_return: Value to return if error occurs and can't be recovered
- [OK] `handle_file_error(error, file_path, operation, user_id, category)` - Convenience function for handling file-related errors.
- [OK] `handle_network_error(error, operation, user_id)` - Convenience function for handling network errors.
- [OK] `handle_validation_error(error, field, operation, user_id)` - Convenience function for handling validation errors.
- [OK] `recover(self, error, context)` - Attempt to recover from the error. Returns True if successful.
- [OK] `recover(self, error, context)` - Attempt to recover from the error by creating missing files with default data.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information

Returns:
    True if recovery was successful, False otherwise
- [OK] `recover(self, error, context)` - Attempt to recover from the error by recreating corrupted JSON files.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information

Returns:
    True if recovery was successful, False otherwise
- [OK] `recover(self, error, context)` - Attempt to recover from network errors by waiting and retrying.

Args:
    error: The exception that occurred
    context: Additional context containing operation details

Returns:
    True if recovery was successful, False otherwise
- [OK] `recover(self, error, context)` - Attempt to recover from configuration errors by using default values.

Args:
    error: The exception that occurred
    context: Additional context containing configuration details

Returns:
    True if recovery was successful, False otherwise
- [OK] `safe_file_operation(file_path, operation, user_id, category)` - Context manager for safe file operations with automatic error handling.

Usage:
    with safe_file_operation("path/to/file.json", "loading user data", user_id="123"):
        # file operations here
- [MISSING] `wrapper()` - No description
**Classes:**
- [OK] `AIError` - Raised when AI operations fail.
- [OK] `CommunicationError` - Raised when communication channels fail.
- [OK] `ConfigurationError` - Raised when configuration is invalid or missing.
- [OK] `ConfigurationRecovery` - Recovery strategy for configuration-related errors.
  - [OK] `ConfigurationRecovery.__init__(self)` - Initialize the ConfigurationRecovery strategy.
  - [OK] `ConfigurationRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle configuration-related errors
  - [OK] `ConfigurationRecovery.recover(self, error, context)` - Attempt to recover from configuration errors by using default values.

Args:
    error: The exception that occurred
    context: Additional context containing configuration details

Returns:
    True if recovery was successful, False otherwise
- [OK] `DataError` - Raised when there are issues with data files or data integrity.
- [OK] `ErrorHandler` - Centralized error handler for MHM.
  - [OK] `ErrorHandler.__init__(self)` - Initialize the ErrorHandler with default recovery strategies.

Sets up recovery strategies for common error types like missing files and corrupted JSON.
  - [OK] `ErrorHandler._get_user_friendly_message(self, error, context)` - Convert technical error to user-friendly message.
  - [OK] `ErrorHandler._log_error(self, error, context)` - Log error with context.
  - [OK] `ErrorHandler._show_user_error(self, error, context, custom_message)` - Show user-friendly error message.
  - [OK] `ErrorHandler.handle_error(self, error, context, operation, user_friendly)` - Handle an error with recovery strategies and logging.

Args:
    error: The exception that occurred
    context: Additional context about the error
    operation: Description of the operation that failed
    user_friendly: Whether to show user-friendly error messages

Returns:
    True if error was recovered from, False otherwise
- [OK] `ErrorRecoveryStrategy` - Base class for error recovery strategies.
  - [OK] `ErrorRecoveryStrategy.__init__(self, name, description)` - Initialize an error recovery strategy.

Args:
    name: The name of the recovery strategy
    description: A description of what this strategy does
  - [OK] `ErrorRecoveryStrategy.can_handle(self, error)` - Check if this strategy can handle the given error.
  - [OK] `ErrorRecoveryStrategy.recover(self, error, context)` - Attempt to recover from the error. Returns True if successful.
- [OK] `FileNotFoundRecovery` - Recovery strategy for missing files.
  - [OK] `FileNotFoundRecovery.__init__(self)` - Initialize the FileNotFoundRecovery strategy.
  - [OK] `FileNotFoundRecovery._get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
  - [OK] `FileNotFoundRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle FileNotFoundError or file operation errors containing "not found"
  - [OK] `FileNotFoundRecovery.recover(self, error, context)` - Attempt to recover from the error by creating missing files with default data.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information

Returns:
    True if recovery was successful, False otherwise
- [OK] `FileOperationError` - Raised when file operations fail.
- [OK] `JSONDecodeRecovery` - Recovery strategy for corrupted JSON files.
  - [OK] `JSONDecodeRecovery.__init__(self)` - Initialize the JSONDecodeRecovery strategy.
  - [OK] `JSONDecodeRecovery._get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
  - [OK] `JSONDecodeRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle JSON decode errors or JSON-related file operation errors
  - [OK] `JSONDecodeRecovery.recover(self, error, context)` - Attempt to recover from the error by recreating corrupted JSON files.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information

Returns:
    True if recovery was successful, False otherwise
- [OK] `MHMError` - Base exception for all MHM-specific errors.
  - [OK] `MHMError.__init__(self, message, details, recoverable)` - Initialize a new MHM error.

Args:
    message: Human-readable error message
    details: Optional dictionary with additional error details
    recoverable: Whether this error can be recovered from
- [OK] `NetworkRecovery` - Recovery strategy for network-related errors.
  - [OK] `NetworkRecovery.__init__(self)` - Initialize the NetworkRecovery strategy.
  - [OK] `NetworkRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check

Returns:
    True if this strategy can handle network-related errors
  - [OK] `NetworkRecovery.recover(self, error, context)` - Attempt to recover from network errors by waiting and retrying.

Args:
    error: The exception that occurred
    context: Additional context containing operation details

Returns:
    True if recovery was successful, False otherwise
- [OK] `RecoveryError` - Raised when error recovery fails.
- [OK] `SafeFileContext` - Context manager for safe file operations.
  - [OK] `SafeFileContext.__enter__(self)` - Enter the context manager for safe file operations.

Returns:
    self: The SafeFileContext instance
  - [OK] `SafeFileContext.__exit__(self, exc_type, exc_val, exc_tb)` - Exit the context manager and handle any exceptions.

Args:
    exc_type: Type of exception if any occurred
    exc_val: Exception value if any occurred
    exc_tb: Exception traceback if any occurred
  - [OK] `SafeFileContext.__init__(self, file_path, operation, user_id, category)` - Initialize the safe file context.

Args:
    file_path: Path to the file being operated on
    operation: Description of the operation being performed
    user_id: ID of the user performing the operation
    category: Category of the operation
- [OK] `SchedulerError` - Raised when scheduler operations fail.
- [OK] `UserInterfaceError` - Raised when UI operations fail.
- [OK] `ValidationError` - Raised when data validation fails.

#### `core/file_auditor.py`
**Functions:**
- [OK] `__init__(self)` - Special Python method
- [MISSING] `_classify_path(path)` - No description
- [OK] `_get_audit_directories(self)` - Get configurable audit directories from environment or use defaults.
- [MISSING] `_split_env_list(value)` - No description
- [OK] `critical(self)` - No-op critical logging for fallback logger.
- [OK] `debug(self)` - No-op debug logging for fallback logger.
- [OK] `error(self)` - No-op error logging for fallback logger.
- [OK] `info(self)` - No-op info logging for fallback logger.
- [OK] `record_created(path, reason, extra)` - Programmatically record a file creation event.

Safe to call even if auditor disabled. Includes optional stack if FILE_AUDIT_STACK=1.
- [OK] `start(self)` - Start the file auditor (no-op for now).
- [MISSING] `start_auditor()` - No description
- [OK] `stop(self)` - Stop the file auditor (no-op for now).
- [MISSING] `stop_auditor()` - No description
- [OK] `warning(self)` - No-op warning logging for fallback logger.
**Classes:**
- [OK] `FileAuditor` - Auditor for tracking file creation and modification patterns.
  - [OK] `FileAuditor.__init__(self)` - Special Python method
  - [OK] `FileAuditor._get_audit_directories(self)` - Get configurable audit directories from environment or use defaults.
  - [OK] `FileAuditor.start(self)` - Start the file auditor (no-op for now).
  - [OK] `FileAuditor.stop(self)` - Stop the file auditor (no-op for now).
- [MISSING] `_DummyLogger` - No description
  - [OK] `_DummyLogger.critical(self)` - No-op critical logging for fallback logger.
  - [OK] `_DummyLogger.debug(self)` - No-op debug logging for fallback logger.
  - [OK] `_DummyLogger.error(self)` - No-op error logging for fallback logger.
  - [OK] `_DummyLogger.info(self)` - No-op info logging for fallback logger.
  - [OK] `_DummyLogger.warning(self)` - No-op warning logging for fallback logger.

#### `core/file_locking.py`
**Functions:**
- [OK] `file_lock(file_path, timeout, retry_interval)` - Context manager for file locking on Windows.

Uses a separate lock file (file_path + '.lock') to coordinate access.
File creation is atomic on Windows, so we use file existence as the lock.

Args:
    file_path: Path to the file to lock
    timeout: Maximum time to wait for lock (seconds)
    retry_interval: Time between lock attempts (seconds)

Yields:
    File handle (opened in 'r+b' mode)

Raises:
    TimeoutError: If lock cannot be acquired within timeout
    OSError: If file operations fail
- [OK] `file_lock(file_path, timeout, retry_interval)` - Context manager for file locking on Unix/Linux.

Uses fcntl.flock() to acquire an exclusive lock on a file.
Retries if the file is locked by another process.

Args:
    file_path: Path to the file to lock
    timeout: Maximum time to wait for lock (seconds)
    retry_interval: Time between lock attempts (seconds)

Yields:
    File handle (opened in 'r+b' mode for locking)

Raises:
    TimeoutError: If lock cannot be acquired within timeout
    OSError: If file operations fail
- [OK] `safe_json_read(file_path, default)` - Safely read JSON file with file locking.

Args:
    file_path: Path to JSON file
    default: Default value to return if file doesn't exist or is invalid

Returns:
    dict: Parsed JSON data or default value
- [OK] `safe_json_write(file_path, data, indent)` - Safely write JSON file with file locking and atomic write.

Uses atomic write pattern: write to temp file, then rename.
This prevents corruption if the process crashes during write.

Args:
    file_path: Path to JSON file
    data: Data to write (must be JSON-serializable)
    indent: JSON indentation level

Returns:
    bool: True if write succeeded, False otherwise

#### `core/file_operations.py`
**Functions:**
- [OK] `_create_user_files__account_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` - Create account.json with actual user data.
- [OK] `_create_user_files__checkins_file(user_id)` - Create checkins.json only if checkins are enabled.
- [OK] `_create_user_files__context_file(user_id, user_prefs)` - Create user_context.json with actual personalization data.
- [OK] `_create_user_files__determine_feature_enablement(user_prefs)` - Determine which features are enabled based on user preferences.

Args:
    user_prefs: User preferences dictionary

Returns:
    tuple: (tasks_enabled, checkins_enabled)
- [OK] `_create_user_files__log_files(user_id)` - Initialize empty log files if they don't exist.
- [OK] `_create_user_files__message_files(user_id, categories)` - Create message files for each enabled category directly.
- [OK] `_create_user_files__preferences_file(user_id, user_prefs, categories, tasks_enabled, checkins_enabled)` - Create preferences.json with actual user data.
- [OK] `_create_user_files__schedules_file(user_id, categories, user_prefs, tasks_enabled, checkins_enabled)` - Create schedules file with appropriate structure.
- [OK] `_create_user_files__sent_messages_file(user_id)` - Create sent_messages.json in messages/ subdirectory.
- [OK] `_create_user_files__task_files(user_id)` - Create task files if tasks are enabled.
- [OK] `_create_user_files__update_user_references(user_id)` - Auto-update message references and user index.
- [OK] `create_user_files(user_id, categories, user_preferences)` - Creates files for a new user in the appropriate structure.
Ensures schedules.json contains a block for each category, plus checkin and task reminder blocks.

Args:
    user_id: The user ID
    categories: List of message categories the user is opted into
    user_preferences: Optional user preferences dict to determine which files to create

Returns:
    bool: True if successful, False if failed
- [OK] `determine_file_path(file_type, identifier)` - Determine file path based on file type and identifier.
Updated to support new organized structure.

Args:
    file_type: Type of file ('users', 'messages', 'schedules', 'sent_messages', 'default_messages', 'tasks')
    identifier: Identifier for the file (format depends on file_type)

Returns:
    str: Full file path, empty string if invalid

Raises:
    FileOperationError: If file_type is unknown or identifier format is invalid
- [OK] `load_json_data(file_path)` - Load data from a JSON file with comprehensive error handling and auto-create user files if missing.

Args:
    file_path: Path to the JSON file to load

Returns:
    dict/list: Loaded JSON data, or empty dict if loading failed
- [OK] `save_json_data(data, file_path)` - Save data to a JSON file with comprehensive error handling.

Args:
    data: Data to save (must be JSON serializable)
    file_path: Path where to save the file

Returns:
    bool: True if successful, False if failed

Raises:
    FileOperationError: If saving fails
- [OK] `verify_file_access(paths)` - Verify that files exist and are accessible.

Args:
    paths: List of file paths to verify

Returns:
    bool: True if all files exist and are accessible, False otherwise

Raises:
    FileOperationError: If any file is not found or inaccessible

#### `core/headless_service.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the headless service manager.
- [OK] `can_start_headless_service(self)` - Check if it's safe to start a headless service.
- [OK] `get_headless_service_status(self)` - Get status of headless service processes.
- [OK] `get_service_info(self)` - Get comprehensive information about all MHM services.
- [OK] `main()` - Main entry point for headless service management.
- [OK] `reschedule_messages(self, user_id, category)` - Reschedule messages using the service's built-in reschedule system.
- [OK] `send_test_message(self, user_id, category)` - Send a test message using the service's built-in test message system.
- [OK] `start_headless_service(self)` - Start the headless MHM service safely.
- [OK] `stop_headless_service(self)` - Stop the headless MHM service safely using the service's built-in shutdown mechanism.
- [OK] `stop_ui_services(self)` - Stop UI-managed services using the service's built-in shutdown mechanism.
**Classes:**
- [OK] `HeadlessServiceManager` - Manages headless MHM service operations safely alongside UI management.
  - [OK] `HeadlessServiceManager.__init__(self)` - Initialize the headless service manager.
  - [OK] `HeadlessServiceManager.can_start_headless_service(self)` - Check if it's safe to start a headless service.
  - [OK] `HeadlessServiceManager.get_headless_service_status(self)` - Get status of headless service processes.
  - [OK] `HeadlessServiceManager.get_service_info(self)` - Get comprehensive information about all MHM services.
  - [OK] `HeadlessServiceManager.reschedule_messages(self, user_id, category)` - Reschedule messages using the service's built-in reschedule system.
  - [OK] `HeadlessServiceManager.send_test_message(self, user_id, category)` - Send a test message using the service's built-in test message system.
  - [OK] `HeadlessServiceManager.start_headless_service(self)` - Start the headless MHM service safely.
  - [OK] `HeadlessServiceManager.stop_headless_service(self)` - Stop the headless MHM service safely using the service's built-in shutdown mechanism.
  - [OK] `HeadlessServiceManager.stop_ui_services(self)` - Stop UI-managed services using the service's built-in shutdown mechanism.

#### `core/logger.py`
**Functions:**
- [OK] `__init__(self, component_name, log_file_path, level)` - Initialize a component-specific logger.

Sets up a dedicated logger for a specific component with file-based logging,
rotation, and error handling. The logger writes to a dedicated log file
and optionally to a consolidated errors.log file.

Args:
    component_name: Name of the component (e.g., 'discord', 'ai', 'scheduler')
    log_file_path: Path to the component's dedicated log file
    level: Logging level (default: logging.INFO)
- [OK] `__init__(self, filename, backup_dir, maxBytes, backupCount, encoding, delay, when, interval)` - Initialize a rotating file handler that moves rotated files to a backup directory.

Args:
    filename: Path to the log file
    backup_dir: Directory where rotated log files will be moved
    maxBytes: Maximum file size before rotation (0 = disabled)
    backupCount: Number of backup files to keep (0 = unlimited)
    encoding: File encoding (default: None, uses system default)
    delay: If True, delay file opening until first write
    when: Time-based rotation interval ('midnight', 'H', 'D', etc.)
    interval: Number of intervals between rotations
- [OK] `__init__(self)` - Initialize the heartbeat warning filter.

Sets up counters and timers for tracking Discord heartbeat warnings
to prevent log spam while maintaining visibility of the issue.
- [OK] `__init__(self, excluded_prefixes)` - Initialize filter with list of logger name prefixes to exclude.

Args:
    excluded_prefixes: List of logger name prefixes to filter out
        (e.g., ['discord', 'aiohttp'] to exclude all Discord and aiohttp logs)
- [OK] `__init__(self, name)` - Initialize a dummy logger for test mode.

Args:
    name: Logger name (unused, kept for interface compatibility)
- [OK] `__init__(self, name)` - Initialize a dummy component logger for test mode.

Provides a no-op logger interface that discards all log messages
to keep test output clean when verbose logging is disabled.

Args:
    name: Component name (e.g., 'discord', 'ai')
- [OK] `_get_log_paths_for_environment()` - Get appropriate log paths based on the current environment.
- [OK] `_is_dev_tools_run()` - True when entry point or env indicates development tools (audit, scripts, etc.).
- [OK] `_is_testing_environment()` - Check if we're running in a testing environment.
- [OK] `_log(self, level, message)` - Internal logging method with structured data support.
- [OK] `apply_test_context_formatter_to_all_loggers()` - Apply PytestContextLogFormatter to all existing loggers when in test mode.
- [OK] `cleanup_old_archives(max_days)` - Remove archived log files older than specified days.

Args:
    max_days (int): Maximum age in days for archived files (default 30)

Returns:
    int: Number of files removed
- [OK] `cleanup_old_logs(max_total_size_mb)` - Clean up old log files if total size exceeds the limit.

Args:
    max_total_size_mb (int): Maximum total size in MB before cleanup (default 50MB)

Returns:
    bool: True if cleanup was performed, False otherwise
- [OK] `clear_log_file_locks()` - Clear any file locks that might be preventing log rotation.

This function attempts to handle Windows file locking issues by:
1. Temporarily disabling log rotation
2. Closing all log file handlers
3. Reopening them with fresh file handles

Returns:
    bool: True if locks were cleared successfully, False otherwise
- [OK] `compress_old_logs()` - Compress log files older than 7 days and move them to archive directory.

Returns:
    int: Number of files compressed and archived
- [OK] `critical(self, message)` - Log critical message with optional structured data.
- [OK] `critical(self, message)` - No-op critical logging for test mode.
- [OK] `debug(self, message)` - Log debug message with optional structured data.
- [OK] `debug(self, message)` - No-op debug logging for test mode.
- [OK] `disable_module_logging(module_name)` - Disable debug logging for a specific module.

Args:
    module_name: Name of the module to disable debug logging for
- [OK] `doRollover(self)` - Do a rollover, as described in __init__().
- [OK] `ensure_logs_directory()` - Ensure the logs directory structure exists.
- [OK] `error(self, message)` - Log error message with optional structured data.
- [OK] `error(self, message)` - No-op error logging for test mode.
- [OK] `filter(self, record)` - Filter Discord heartbeat warnings to prevent log spam.

Args:
    record: logging.LogRecord to filter

Returns:
    bool: True if record should be logged, False to suppress
- [OK] `filter(self, record)` - Filter log records based on excluded prefixes.

Args:
    record: logging.LogRecord to filter

Returns:
    bool: True if record should be logged, False if it matches excluded prefixes
- [OK] `force_restart_logging()` - Force restart the logging system by clearing all handlers and reinitializing.

Useful when logging configuration becomes corrupted or needs to be reset.

Returns:
    bool: True if restart was successful, False otherwise
- [OK] `format(self, record)` - Format log record with test context prepended when in test mode.

Automatically prepends the current test name to log messages during pytest runs
to help identify which test generated each log entry. Skips component loggers
(those starting with "mhm.") to avoid duplication.

Args:
    record: logging.LogRecord to format

Returns:
    str: Formatted log message with optional test context
- [OK] `get_component_logger(component_name)` - Get or create a component-specific logger.

Args:
    component_name: Name of the component (e.g., 'discord', 'ai', 'user_activity')

Returns:
    ComponentLogger: Logger for the specified component
- [OK] `get_log_file_info()` - Get information about current log files and their sizes.

Returns:
    dict: Information about log files including total size and file count
- [OK] `get_log_level_from_env()` - Get log level from environment variable, default to WARNING for quiet mode.

Returns:
    int: Logging level constant (e.g., logging.WARNING, logging.DEBUG)
- [OK] `get_logger(name)` - Get a logger with the specified name.

Args:
    name: Logger name (usually __name__)

Returns:
    logging.Logger: Configured logger
- [OK] `get_verbose_mode()` - Get current verbose mode status.

Returns:
    bool: True if verbose mode is enabled
- [OK] `info(self, message)` - Log info message with optional structured data.
- [OK] `info(self, message)` - No-op info logging for test mode.
- [OK] `set_console_log_level(level)` - Set the console logging level while keeping file logging at DEBUG.

Args:
    level: logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
- [OK] `set_verbose_mode(enabled)` - Explicitly set verbose mode.

Args:
    enabled (bool): True to enable verbose mode, False for quiet mode
- [OK] `setup_logging()` - Set up logging with file and console handlers. Ensure it is called only once.

Creates a dual-handler logging system:
- File handler: Always logs at DEBUG level with rotation
- Console handler: Respects verbosity settings (WARNING by default)

Automatically suppresses noisy third-party library logging.
- [OK] `setup_third_party_error_logging()` - Set up dedicated error logging for third-party libraries.

Routes ERROR and CRITICAL messages from asyncio, discord, and aiohttp
to the errors.log file instead of app.log.
- [OK] `shouldRollover(self, record)` - Determine if rollover should occur based on both time and size.
Prevents rollover for files that are too small or too recently created.
- [OK] `suppress_noisy_logging()` - Suppress excessive logging from third-party libraries.

Sets logging level to WARNING for common noisy libraries to reduce log spam
while keeping important warnings and errors visible.
- [OK] `toggle_verbose_logging()` - Toggle between verbose (DEBUG/INFO) and quiet (WARNING+) logging for console output.
File logging always remains at DEBUG level.

Returns:
    bool: True if verbose mode is now enabled, False if quiet mode
- [OK] `warning(self, message)` - Log warning message with optional structured data.
- [OK] `warning(self, message)` - No-op warning logging for test mode.
**Classes:**
- [OK] `BackupDirectoryRotatingFileHandler` - Custom rotating file handler that moves rotated files to a backup directory.
Supports both time-based and size-based rotation.
  - [OK] `BackupDirectoryRotatingFileHandler.__init__(self, filename, backup_dir, maxBytes, backupCount, encoding, delay, when, interval)` - Initialize a rotating file handler that moves rotated files to a backup directory.

Args:
    filename: Path to the log file
    backup_dir: Directory where rotated log files will be moved
    maxBytes: Maximum file size before rotation (0 = disabled)
    backupCount: Number of backup files to keep (0 = unlimited)
    encoding: File encoding (default: None, uses system default)
    delay: If True, delay file opening until first write
    when: Time-based rotation interval ('midnight', 'H', 'D', etc.)
    interval: Number of intervals between rotations
  - [OK] `BackupDirectoryRotatingFileHandler.doRollover(self)` - Do a rollover, as described in __init__().
  - [OK] `BackupDirectoryRotatingFileHandler.shouldRollover(self, record)` - Determine if rollover should occur based on both time and size.
Prevents rollover for files that are too small or too recently created.
- [OK] `ComponentLogger` - Component-specific logger that writes to dedicated log files.

Each component gets its own log file with appropriate rotation and formatting.
  - [OK] `ComponentLogger.__init__(self, component_name, log_file_path, level)` - Initialize a component-specific logger.

Sets up a dedicated logger for a specific component with file-based logging,
rotation, and error handling. The logger writes to a dedicated log file
and optionally to a consolidated errors.log file.

Args:
    component_name: Name of the component (e.g., 'discord', 'ai', 'scheduler')
    log_file_path: Path to the component's dedicated log file
    level: Logging level (default: logging.INFO)
  - [OK] `ComponentLogger._log(self, level, message)` - Internal logging method with structured data support.
  - [OK] `ComponentLogger.critical(self, message)` - Log critical message with optional structured data.
  - [OK] `ComponentLogger.debug(self, message)` - Log debug message with optional structured data.
  - [OK] `ComponentLogger.error(self, message)` - Log error message with optional structured data.
  - [OK] `ComponentLogger.info(self, message)` - Log info message with optional structured data.
  - [OK] `ComponentLogger.warning(self, message)` - Log warning message with optional structured data.
- [MISSING] `DummyComponentLogger` - No description
  - [OK] `DummyComponentLogger.__init__(self, name)` - Initialize a dummy component logger for test mode.

Provides a no-op logger interface that discards all log messages
to keep test output clean when verbose logging is disabled.

Args:
    name: Component name (e.g., 'discord', 'ai')
  - [OK] `DummyComponentLogger.critical(self, message)` - No-op critical logging for test mode.
  - [OK] `DummyComponentLogger.debug(self, message)` - No-op debug logging for test mode.
  - [OK] `DummyComponentLogger.error(self, message)` - No-op error logging for test mode.
  - [OK] `DummyComponentLogger.info(self, message)` - No-op info logging for test mode.
  - [OK] `DummyComponentLogger.warning(self, message)` - No-op warning logging for test mode.
- [OK] `ExcludeLoggerNamesFilter` - Filter to exclude records for specific logger name prefixes.
Example use: prevent Discord-related logs from going to app.log.
  - [OK] `ExcludeLoggerNamesFilter.__init__(self, excluded_prefixes)` - Initialize filter with list of logger name prefixes to exclude.

Args:
    excluded_prefixes: List of logger name prefixes to filter out
        (e.g., ['discord', 'aiohttp'] to exclude all Discord and aiohttp logs)
  - [OK] `ExcludeLoggerNamesFilter.filter(self, record)` - Filter log records based on excluded prefixes.

Args:
    record: logging.LogRecord to filter

Returns:
    bool: True if record should be logged, False if it matches excluded prefixes
- [OK] `HeartbeatWarningFilter` - Filter to suppress excessive Discord heartbeat warnings while keeping track of them.

- Allows first 3 heartbeat warnings to pass through
- Suppresses subsequent warnings for 10 minutes
- Logs a summary every hour with total count
  - [OK] `HeartbeatWarningFilter.__init__(self)` - Initialize the heartbeat warning filter.

Sets up counters and timers for tracking Discord heartbeat warnings
to prevent log spam while maintaining visibility of the issue.
  - [OK] `HeartbeatWarningFilter.filter(self, record)` - Filter Discord heartbeat warnings to prevent log spam.

Args:
    record: logging.LogRecord to filter

Returns:
    bool: True if record should be logged, False to suppress
- [OK] `PytestContextLogFormatter` - Custom formatter that automatically prepends test names to log messages.
  - [OK] `PytestContextLogFormatter.format(self, record)` - Format log record with test context prepended when in test mode.

Automatically prepends the current test name to log messages during pytest runs
to help identify which test generated each log entry. Skips component loggers
(those starting with "mhm.") to avoid duplication.

Args:
    record: logging.LogRecord to format

Returns:
    str: Formatted log message with optional test context
- [MISSING] `_DummyLogger` - No description
  - [OK] `_DummyLogger.__init__(self, name)` - Initialize a dummy logger for test mode.

Args:
    name: Logger name (unused, kept for interface compatibility)

#### `core/message_analytics.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the MessageAnalytics instance.

This class provides analytics and insights from sent message data.
- [OK] `get_delivery_success_rate(self, user_id, days)` - Analyze message delivery success rates.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)

Returns:
    Dict containing delivery statistics
- [OK] `get_message_frequency(self, user_id, days, category)` - Analyze message send frequency by category and time period.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)
    category: Optional category filter (None = all categories)

Returns:
    Dict containing frequency statistics
- [OK] `get_message_summary(self, user_id, days)` - Get a comprehensive summary of message activity.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)

Returns:
    Dict containing summary statistics
**Classes:**
- [MISSING] `MessageAnalytics` - No description
  - [OK] `MessageAnalytics.__init__(self)` - Initialize the MessageAnalytics instance.

This class provides analytics and insights from sent message data.
  - [OK] `MessageAnalytics.get_delivery_success_rate(self, user_id, days)` - Analyze message delivery success rates.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)

Returns:
    Dict containing delivery statistics
  - [OK] `MessageAnalytics.get_message_frequency(self, user_id, days, category)` - Analyze message send frequency by category and time period.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)
    category: Optional category filter (None = all categories)

Returns:
    Dict containing frequency statistics
  - [OK] `MessageAnalytics.get_message_summary(self, user_id, days)` - Get a comprehensive summary of message activity.

Args:
    user_id: The user ID to analyze
    days: Number of days to analyze (default: 30)

Returns:
    Dict containing summary statistics

#### `core/message_management.py`
**Functions:**
- [OK] `_normalize_message_timestamps(data, file_path)` - Normalize timestamps in persisted sent_messages data to the canonical TIMESTAMP_FULL shape.

Returns:
    bool: True if any timestamps were rewritten.
- [OK] `_parse_legacy_timestamp_for_normalization(timestamp_str)` - Parse an older timestamp shape when normalizing persisted sent_messages data.

The returned datetime is naive (no timezone) so it can be serialized using TIMESTAMP_FULL.
- [OK] `_parse_message_timestamp(timestamp_str)` - Parse timestamp string to datetime object.

Args:
    timestamp_str: Timestamp string to parse

Returns:
    datetime: Parsed datetime object (UTC) or sentinel minimum
- [OK] `add_message(user_id, category, message_data, index)` - Add a new message to a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_data: Dictionary containing message data
    index: Optional position to insert the message (None for append)
- [OK] `archive_old_messages(user_id, days_to_keep)` - Archive messages older than specified days.

This function implements file rotation by moving old messages to archive files,
keeping the active sent_messages.json file manageable in size.

Args:
    user_id: The user ID
    days_to_keep: Number of days to keep in active file

Returns:
    bool: True if archiving successful
- [OK] `create_message_file_from_defaults(user_id, category)` - Create a user's message file for a specific category from default messages.
This is the actual worker function that creates the file.

Args:
    user_id: The user ID
    category: The specific category to create a message file for

Returns:
    bool: True if file was created successfully
- [OK] `delete_message(user_id, category, message_id)` - Delete a specific message from a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to delete

Raises:
    ValidationError: If the message ID is not found or the category is invalid
- [OK] `edit_message(user_id, category, message_id, updated_data)` - Edit an existing message in a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to edit
    updated_data: Dictionary containing updated message data

Raises:
    ValidationError: If message ID is not found or category is invalid
- [OK] `ensure_user_message_files(user_id, categories)` - Ensure user has message files for specified categories.
Creates messages directory if missing, checks which files are missing, and creates them.

Args:
    user_id: The user ID
    categories: List of categories to check/create message files for (can be subset of user's categories)

Returns:
    dict: Summary of the operation with keys:
        - success: bool - True if all files were created/validated successfully
        - directory_created: bool - True if messages directory was created
        - files_checked: int - Number of categories checked
        - files_created: int - Number of new files created
        - files_existing: int - Number of files that already existed
- [OK] `get_message_categories()` - Retrieves message categories from the environment variable CATEGORIES.
Allows for either a comma-separated string or a JSON array.

Returns:
    List[str]: List of message categories
- [OK] `get_recent_messages(user_id, category, limit, days_back)` - Get recent messages with flexible filtering.

This function replaces get_last_10_messages() with enhanced functionality
that supports both category-specific and cross-category queries.

Args:
    user_id: The user ID
    category: Optional category filter (None = all categories)
    limit: Maximum number of messages to return
    days_back: Only include messages from last N days

Returns:
    List[dict]: List of recent messages, sorted by timestamp descending
- [OK] `get_timestamp_for_sorting(item)` - Convert timestamp to float for consistent sorting.

Args:
    item: Dictionary containing a timestamp field or other data type

Returns:
    float: Timestamp as float for sorting, or 0.0 for invalid items
- [OK] `load_default_messages(category)` - Load default messages for a specific category.
- [OK] `load_user_messages(user_id, category)` - Load user's message templates for a specific category.

Args:
    user_id: The user ID
    category: The message category

Returns:
    List[dict]: List of message templates for the category
- [OK] `store_sent_message(user_id, category, message_id, message, delivery_status, time_period)` - Store sent message in chronological order.

This function maintains the chronological structure by inserting new messages
in the correct position based on timestamp.

Args:
    user_id: The user ID
    category: The message category
    message_id: The message ID
    message: The message content
    delivery_status: Delivery status (default: "sent")
    time_period: The time period when the message was sent (e.g., "morning", "evening")

Returns:
    bool: True if message stored successfully
- [OK] `update_message(user_id, category, message_id, new_message_data)` - Update a message by its message_id.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to update
    new_message_data: Complete new message data to replace the existing message

Raises:
    ValidationError: If message ID is not found or category is invalid

#### `core/response_tracking.py`
**Functions:**
- [OK] `_get_response_log_filename(response_type)` - Get the filename for a response log type.
- [OK] `get_checkins_by_days(user_id, days)` - Get check-ins from the last N calendar days.
- [OK] `get_recent_chat_interactions(user_id, limit)` - Get recent chat interactions for a user.
- [OK] `get_recent_checkins(user_id, limit)` - Get recent check-in responses for a user.
- [OK] `get_recent_responses(user_id, response_type, limit)` - Get recent responses for a user from appropriate file structure.
- [OK] `get_timestamp_for_sorting(item)` - Convert timestamp to float for consistent sorting
- [OK] `get_user_info_for_tracking(user_id)` - Get user information for response tracking.
- [OK] `is_user_checkins_enabled(user_id)` - Check if check-ins are enabled for a user.
- [OK] `store_chat_interaction(user_id, user_message, ai_response, context_used)` - Store a chat interaction between user and AI.
- [OK] `store_user_response(user_id, response_data, response_type)` - Store user response data in appropriate file structure.
- [OK] `track_user_response(user_id, category, response_data)` - Track a user's response to a message.

#### `core/schedule_management.py`
**Functions:**
- [MISSING] `add_schedule_period(category, period_name, start_time, end_time, scheduler_manager)` - No description
- [OK] `clear_schedule_periods_cache(user_id, category)` - Clear the schedule periods cache for a specific user/category or all.
- [OK] `delete_schedule_period(category, period_name, scheduler_manager)` - Delete a schedule period from a category.

Args:
    category: The schedule category
    period_name: The name of the period to delete
    scheduler_manager: Optional scheduler manager for rescheduling (default: None)
- [MISSING] `edit_schedule_period(category, period_name, new_start_time, new_end_time, scheduler_manager)` - No description
- [OK] `get_current_day_names()` - Returns the name of the current day plus 'ALL' for universal day messages.
- [OK] `get_current_time_periods_with_validation(user_id, category)` - Returns the current active time periods for a user and category.
If no active period is found, defaults to the first available period.
- [OK] `get_period_data__time_12h_display_to_24h(hour_12, minute, is_pm)` - Convert 12-hour display format to 24-hour time string.

Args:
    hour_12 (int): Hour in 12-hour format (1-12)
    minute (int): Minute (0-59)
    is_pm (bool): True if PM, False if AM

Returns:
    str: Time in 24-hour format (HH:MM)
- [OK] `get_period_data__time_24h_to_12h_display(time_24h)` - Convert 24-hour time string (HH:MM) to 12-hour display format.

Args:
    time_24h (str): Time in 24-hour format (e.g., "14:30")

Returns:
    tuple: (hour_12, minute, is_pm) where:
        - hour_12 (int): Hour in 12-hour format (1-12)
        - minute (int): Minute (0-59)
        - is_pm (bool): True if PM, False if AM
- [OK] `get_period_data__validate_and_format_time(time_str)` - Validate and format a time string to HH:MM format.

Args:
    time_str: Time string to validate and format

Returns:
    str: Formatted time string in HH:MM format

Raises:
    ValueError: If the time format is invalid
- [OK] `get_schedule_days(user_id, category)` - Get the schedule days for a user and category.

Args:
    user_id: The user ID
    category: The schedule category

Returns:
    list: List of days for the schedule, defaults to all days of the week
- [OK] `get_schedule_time_periods(user_id, category)` - Get schedule time periods for a specific user and category (new format).
- [OK] `get_user_info_for_schedule_management(user_id)` - Get user info for schedule management operations.
- [OK] `is_schedule_period_active(user_id, category, period_name)` - Check if a schedule period is currently active.

Args:
    user_id: The user ID
    category: The schedule category
    period_name: The name of the period to check

Returns:
    bool: True if the period is active, False otherwise (defaults to True if field is missing)
- [OK] `set_schedule_days(user_id, category, days)` - Set the schedule days for a user and category.

Args:
    user_id: The user ID
    category: The schedule category
    days: List of days to set for the schedule
- [OK] `set_schedule_period_active(user_id, category, period_name, active)` - Set whether a schedule period is active or inactive.

Args:
    user_id: The user ID
    category: The schedule category
    period_name: The name of the period to modify
    active: Whether the period should be active (default: True)

Returns:
    bool: True if the period was found and updated, False otherwise
- [OK] `set_schedule_periods(user_id, category, periods_dict)` - Replace all schedule periods for a category with the given dict (period_name: {active, days, start_time, end_time}).
- [OK] `sort_key(item)` - Generate a sort key for schedule period items.

Args:
    item: Tuple of (period_name, period_data) from schedule periods dict

Returns:
    Tuple of (priority, start_time_obj) where priority determines position
    (ALL periods get highest priority to appear last)

#### `core/schedule_utilities.py`
**Functions:**
- [OK] `get_active_schedules(schedules)` - Get list of currently active schedule periods.

Args:
    schedules: Dictionary containing schedule periods

Returns:
    list: List of active schedule period names
- [OK] `get_current_active_schedules(schedules, current_time)` - Get list of schedule periods that are currently active based on time and day.
- [OK] `is_schedule_active(schedule_data, current_time)` - Check if a schedule period is currently active based on time and day.

Args:
    schedule_data: Dictionary containing schedule period data
    current_time: Current time to check against (defaults to now)

Returns:
    bool: True if the schedule is active, False otherwise

#### `core/scheduler.py`
**Functions:**
- [OK] `__init__(self, communication_manager)` - Initialize the SchedulerManager with communication manager.

Args:
    communication_manager: The communication manager for sending messages
- [OK] `_remove_user_message_job(self, user_id, category)` - Removes user message jobs from the scheduler after execution.
This makes user message jobs effectively one-time jobs.
- [OK] `_select_task_for_reminder__calculate_due_date_weight(self, task, today)` - Calculate due date proximity weight for a task.
- [OK] `_select_task_for_reminder__calculate_priority_weight(self, task)` - Calculate priority-based weight for a task.
- [OK] `_select_task_for_reminder__calculate_task_weights(self, incomplete_tasks, today)` - Calculate weights for all tasks.
- [OK] `_select_task_for_reminder__handle_edge_cases(self, incomplete_tasks)` - Handle edge cases for task selection.
- [OK] `_select_task_for_reminder__select_task_by_weight(self, task_weights, incomplete_tasks)` - Select a task based on calculated weights using weighted random selection.
- [OK] `_select_task_for_reminder__task_key(self, task, index)` - Build a stable key for tracking reminder selection state.
- [OK] `check_and_perform_weekly_backup(self)` - Check if a weekly backup is needed and perform it if so.
Runs during the daily scheduler job at 01:00 (before log archival at 02:00).
Creates a backup if:
- No backups exist, OR
- Last backup is 7+ days old
Keeps last 10 backups with 30-day retention as configured in BackupManager.
- [OK] `cleanup_old_tasks(self, user_id, category)` - Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category.
- [OK] `cleanup_orphaned_task_reminders(self)` - Periodic cleanup job to remove reminders for tasks that no longer exist.

Scans all scheduled reminder jobs and verifies the associated tasks still exist.
Removes reminders for tasks that have been deleted or completed.
Runs daily at 03:00.
- [OK] `cleanup_task_reminders(self, user_id, task_id)` - Clean up all reminders for a specific task.

Finds and removes all APScheduler jobs that call handle_task_reminder for the given task_id.
Handles both one-time reminders (schedule_task_reminder_at_datetime) and daily reminders (schedule_task_reminder_at_time).

Args:
    user_id: The user's ID
    task_id: The task ID to clean up reminders for

Returns:
    bool: True if cleanup succeeded (or no reminders found), False on error
- [OK] `clear_all_accumulated_jobs(self)` - Clears all accumulated scheduler jobs and reschedules only the necessary ones.
- [OK] `clear_all_accumulated_jobs_standalone()` - Standalone function to clear all accumulated scheduler jobs.
This can be called from the admin UI or service to fix job accumulation issues.
- [OK] `get_random_time_within_period(self, user_id, category, period, timezone_str)` - Get a random time within a specified period for a given category.
- [OK] `get_random_time_within_task_period(self, start_time, end_time)` - Generate a random time within a task reminder period.
Args:
    start_time: Start time in HH:MM format (e.g., "17:00")
    end_time: End time in HH:MM format (e.g., "18:00")
Returns:
    Random time in HH:MM format
- [OK] `handle_sending_scheduled_message(self, user_id, category, retry_attempts, retry_delay)` - Handles the sending of scheduled messages with retries.
This is a one-time job that removes itself after execution.
- [OK] `handle_task_reminder(self, user_id, task_id, retry_attempts, retry_delay)` - Handles sending task reminders with retries.
- [OK] `is_job_for_category(self, job, user_id, category)` - Determines if a job is scheduled for a specific user and category.
- [OK] `is_time_conflict(self, user_id, schedule_datetime)` - Checks if there is a time conflict with any existing scheduled jobs for the user.

NOTE:
The `schedule` library commonly uses naive datetimes for `job.next_run`.
Our schedule_datetime is often tz-aware (pytz). Subtracting naive/aware raises TypeError.
- [OK] `log_scheduled_tasks(self)` - Logs all current and upcoming scheduled tasks in a user-friendly manner.
- [OK] `perform_daily_log_archival(self)` - Perform daily log archival to compress old logs and clean up archives.
This runs automatically at 02:00 daily via the scheduler.
- [OK] `process_category_schedule(user_id, category)` - Process schedule for a specific user and category.
- [OK] `process_user_schedules(user_id)` - Process schedules for a specific user.
- [OK] `reset_and_reschedule_daily_messages(self, category, user_id)` - Resets scheduled tasks for a specific category and reschedules daily messages for that category.
- [OK] `run_category_scheduler_standalone(user_id, category)` - Standalone function to run scheduler for a specific user and category.
This can be called from the admin UI without needing a scheduler instance.
- [OK] `run_daily_scheduler(self)` - Starts the daily scheduler in a separate thread that handles all users.
- [OK] `run_full_daily_scheduler(self)` - Runs the full daily scheduler process - same as system startup.
This includes clearing accumulated jobs, scheduling all users, checkins, task reminders, and checking for weekly backups.
- [OK] `run_full_scheduler_standalone()` - Standalone function to run the full scheduler for all users.
This can be called from the admin UI without needing a scheduler instance.
- [OK] `run_user_scheduler_standalone(user_id)` - Standalone function to run scheduler for a specific user.
This can be called from the admin UI without needing a scheduler instance.
- [OK] `schedule_all_task_reminders(user_id)` - Standalone function to schedule all task reminders for a user.
This can be called from the admin UI without needing a scheduler instance.
- [OK] `schedule_all_task_reminders(self, user_id)` - Schedule reminders for all active tasks for a user.
For each reminder period, pick one random task and schedule it at a random time within the period.
- [OK] `schedule_all_users_immediately(self)` - Schedule daily messages immediately for all users
- [OK] `schedule_checkin_at_exact_time(self, user_id, period_name)` - Schedule a check-in at the exact time specified in the period.
- [OK] `schedule_daily_message_job(self, user_id, category)` - Schedules daily messages immediately for the specified user and category.
Schedules one message per active period in the category.
- [OK] `schedule_message_at_random_time(self, user_id, category)` - Schedules a message at a random time within the user's preferred time periods.
- [OK] `schedule_message_for_period(self, user_id, category, period_name)` - Schedules a message at a random time within a specific period for a user and category.
- [OK] `schedule_new_user(self, user_id)` - Schedule a newly created user immediately.
This method should be called after a new user is created to add them to the scheduler.

Args:
    user_id: The ID of the newly created user
- [OK] `schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str)` - Schedule a reminder for a specific task at a specific date and time.
- [OK] `schedule_task_reminder_at_time(self, user_id, task_id, reminder_time)` - Schedule a reminder for a specific task at the specified time (daily).
- [MISSING] `scheduler_loop()` - No description
- [OK] `select_task_for_reminder(self, incomplete_tasks)` - Select a task for reminder using priority-based and due date proximity weighting.

Args:
    incomplete_tasks: List of incomplete tasks to choose from

Returns:
    Selected task dictionary
- [OK] `set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes)` - Set a Windows scheduled task to wake the computer before a scheduled message.

Args:
    schedule_time: The datetime when the message is scheduled
    user_id: The user ID
    category: The message category
    period: The time period name
    wake_ahead_minutes: Minutes before schedule_time to wake the computer (default: 4)
- [OK] `stop_scheduler(self)` - Stops the scheduler thread.
**Classes:**
- [MISSING] `SchedulerManager` - No description
  - [OK] `SchedulerManager.__init__(self, communication_manager)` - Initialize the SchedulerManager with communication manager.

Args:
    communication_manager: The communication manager for sending messages
  - [OK] `SchedulerManager._remove_user_message_job(self, user_id, category)` - Removes user message jobs from the scheduler after execution.
This makes user message jobs effectively one-time jobs.
  - [OK] `SchedulerManager._select_task_for_reminder__calculate_due_date_weight(self, task, today)` - Calculate due date proximity weight for a task.
  - [OK] `SchedulerManager._select_task_for_reminder__calculate_priority_weight(self, task)` - Calculate priority-based weight for a task.
  - [OK] `SchedulerManager._select_task_for_reminder__calculate_task_weights(self, incomplete_tasks, today)` - Calculate weights for all tasks.
  - [OK] `SchedulerManager._select_task_for_reminder__handle_edge_cases(self, incomplete_tasks)` - Handle edge cases for task selection.
  - [OK] `SchedulerManager._select_task_for_reminder__select_task_by_weight(self, task_weights, incomplete_tasks)` - Select a task based on calculated weights using weighted random selection.
  - [OK] `SchedulerManager._select_task_for_reminder__task_key(self, task, index)` - Build a stable key for tracking reminder selection state.
  - [OK] `SchedulerManager.check_and_perform_weekly_backup(self)` - Check if a weekly backup is needed and perform it if so.
Runs during the daily scheduler job at 01:00 (before log archival at 02:00).
Creates a backup if:
- No backups exist, OR
- Last backup is 7+ days old
Keeps last 10 backups with 30-day retention as configured in BackupManager.
  - [OK] `SchedulerManager.cleanup_old_tasks(self, user_id, category)` - Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category.
  - [OK] `SchedulerManager.cleanup_orphaned_task_reminders(self)` - Periodic cleanup job to remove reminders for tasks that no longer exist.

Scans all scheduled reminder jobs and verifies the associated tasks still exist.
Removes reminders for tasks that have been deleted or completed.
Runs daily at 03:00.
  - [OK] `SchedulerManager.cleanup_task_reminders(self, user_id, task_id)` - Clean up all reminders for a specific task.

Finds and removes all APScheduler jobs that call handle_task_reminder for the given task_id.
Handles both one-time reminders (schedule_task_reminder_at_datetime) and daily reminders (schedule_task_reminder_at_time).

Args:
    user_id: The user's ID
    task_id: The task ID to clean up reminders for

Returns:
    bool: True if cleanup succeeded (or no reminders found), False on error
  - [OK] `SchedulerManager.clear_all_accumulated_jobs(self)` - Clears all accumulated scheduler jobs and reschedules only the necessary ones.
  - [OK] `SchedulerManager.get_random_time_within_period(self, user_id, category, period, timezone_str)` - Get a random time within a specified period for a given category.
  - [OK] `SchedulerManager.get_random_time_within_task_period(self, start_time, end_time)` - Generate a random time within a task reminder period.
Args:
    start_time: Start time in HH:MM format (e.g., "17:00")
    end_time: End time in HH:MM format (e.g., "18:00")
Returns:
    Random time in HH:MM format
  - [OK] `SchedulerManager.handle_sending_scheduled_message(self, user_id, category, retry_attempts, retry_delay)` - Handles the sending of scheduled messages with retries.
This is a one-time job that removes itself after execution.
  - [OK] `SchedulerManager.handle_task_reminder(self, user_id, task_id, retry_attempts, retry_delay)` - Handles sending task reminders with retries.
  - [OK] `SchedulerManager.is_job_for_category(self, job, user_id, category)` - Determines if a job is scheduled for a specific user and category.
  - [OK] `SchedulerManager.is_time_conflict(self, user_id, schedule_datetime)` - Checks if there is a time conflict with any existing scheduled jobs for the user.

NOTE:
The `schedule` library commonly uses naive datetimes for `job.next_run`.
Our schedule_datetime is often tz-aware (pytz). Subtracting naive/aware raises TypeError.
  - [OK] `SchedulerManager.log_scheduled_tasks(self)` - Logs all current and upcoming scheduled tasks in a user-friendly manner.
  - [OK] `SchedulerManager.perform_daily_log_archival(self)` - Perform daily log archival to compress old logs and clean up archives.
This runs automatically at 02:00 daily via the scheduler.
  - [OK] `SchedulerManager.reset_and_reschedule_daily_messages(self, category, user_id)` - Resets scheduled tasks for a specific category and reschedules daily messages for that category.
  - [OK] `SchedulerManager.run_daily_scheduler(self)` - Starts the daily scheduler in a separate thread that handles all users.
  - [OK] `SchedulerManager.run_full_daily_scheduler(self)` - Runs the full daily scheduler process - same as system startup.
This includes clearing accumulated jobs, scheduling all users, checkins, task reminders, and checking for weekly backups.
  - [OK] `SchedulerManager.schedule_all_task_reminders(self, user_id)` - Schedule reminders for all active tasks for a user.
For each reminder period, pick one random task and schedule it at a random time within the period.
  - [OK] `SchedulerManager.schedule_all_users_immediately(self)` - Schedule daily messages immediately for all users
  - [OK] `SchedulerManager.schedule_checkin_at_exact_time(self, user_id, period_name)` - Schedule a check-in at the exact time specified in the period.
  - [OK] `SchedulerManager.schedule_daily_message_job(self, user_id, category)` - Schedules daily messages immediately for the specified user and category.
Schedules one message per active period in the category.
  - [OK] `SchedulerManager.schedule_message_at_random_time(self, user_id, category)` - Schedules a message at a random time within the user's preferred time periods.
  - [OK] `SchedulerManager.schedule_message_for_period(self, user_id, category, period_name)` - Schedules a message at a random time within a specific period for a user and category.
  - [OK] `SchedulerManager.schedule_new_user(self, user_id)` - Schedule a newly created user immediately.
This method should be called after a new user is created to add them to the scheduler.

Args:
    user_id: The ID of the newly created user
  - [OK] `SchedulerManager.schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str)` - Schedule a reminder for a specific task at a specific date and time.
  - [OK] `SchedulerManager.schedule_task_reminder_at_time(self, user_id, task_id, reminder_time)` - Schedule a reminder for a specific task at the specified time (daily).
  - [OK] `SchedulerManager.select_task_for_reminder(self, incomplete_tasks)` - Select a task for reminder using priority-based and due date proximity weighting.

Args:
    incomplete_tasks: List of incomplete tasks to choose from

Returns:
    Selected task dictionary
  - [OK] `SchedulerManager.set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes)` - Set a Windows scheduled task to wake the computer before a scheduled message.

Args:
    schedule_time: The datetime when the message is scheduled
    user_id: The user ID
    category: The message category
    period: The time period name
    wake_ahead_minutes: Minutes before schedule_time to wake the computer (default: 4)
  - [OK] `SchedulerManager.stop_scheduler(self)` - Stops the scheduler thread.

#### `core/schemas.py`
**Functions:**
- [OK] `_accept_legacy_shape(cls, data)` - Accept legacy schedule data format where periods are at top-level.

This validator converts legacy schedule data (where periods are directly
in the dict) to the new format (where periods are under a 'periods' key).

Args:
    data: Schedule data dict that may be in legacy format

Returns:
    dict: Data in the new format with 'periods' key
- [MISSING] `_coerce_bool(cls, v)` - No description
- [MISSING] `_normalize_contact(self)` - No description
- [OK] `_normalize_days(cls, v)` - Normalize days list for message scheduling.

Ensures the days list is not empty by defaulting to ["ALL"] if the
input list is empty or None.

Args:
    v: List of day strings (may be empty)

Returns:
    List[str]: Normalized days list, defaults to ["ALL"] if empty
- [OK] `_normalize_discord_username(cls, v)` - Normalize Discord username while tolerating empty or legacy values.
- [OK] `_normalize_flags(cls, v)` - Normalize feature flag values to "enabled" or "disabled".

Converts various input formats (boolean, string variants) to the standard
"enabled"/"disabled" literal values using the _coerce_bool helper.

Args:
    v: Input value (bool, str, or other) to normalize

Returns:
    Literal["enabled", "disabled"]: Normalized flag value
- [OK] `_normalize_periods(cls, v)` - Normalize time periods list for message scheduling.

Ensures the time_periods list is not empty by defaulting to ["ALL"] if the
input list is empty or None.

Args:
    v: List of time period strings (may be empty)

Returns:
    List[str]: Normalized time periods list, defaults to ["ALL"] if empty
- [MISSING] `_valid_days(cls, v)` - No description
- [MISSING] `_valid_time(cls, v)` - No description
- [OK] `_validate_categories(cls, v)` - Validate that all categories are in the allowed list.
- [OK] `_validate_discord_id(cls, v)` - Validate and normalize Discord user ID.

Discord user IDs are snowflakes (numeric IDs) that are 17-19 digits long.
Empty strings are allowed (Discord ID is optional).
- [MISSING] `_validate_email(cls, v)` - No description
- [MISSING] `_validate_timezone(cls, v)` - No description
- [MISSING] `to_dict(self)` - No description
- [MISSING] `validate_account_dict(data)` - No description
- [MISSING] `validate_messages_file_dict(data)` - No description
- [MISSING] `validate_preferences_dict(data)` - No description
- [MISSING] `validate_schedules_dict(data)` - No description
**Classes:**
- [MISSING] `AccountModel` - No description
  - [OK] `AccountModel._normalize_discord_username(cls, v)` - Normalize Discord username while tolerating empty or legacy values.
  - [OK] `AccountModel._validate_discord_id(cls, v)` - Validate and normalize Discord user ID.

Discord user IDs are snowflakes (numeric IDs) that are 17-19 digits long.
Empty strings are allowed (Discord ID is optional).
  - [MISSING] `AccountModel._validate_email(cls, v)` - No description
  - [MISSING] `AccountModel._validate_timezone(cls, v)` - No description
- [MISSING] `CategoryScheduleModel` - No description
  - [OK] `CategoryScheduleModel._accept_legacy_shape(cls, data)` - Accept legacy schedule data format where periods are at top-level.

This validator converts legacy schedule data (where periods are directly
in the dict) to the new format (where periods are under a 'periods' key).

Args:
    data: Schedule data dict that may be in legacy format

Returns:
    dict: Data in the new format with 'periods' key
- [MISSING] `ChannelModel` - No description
  - [MISSING] `ChannelModel._normalize_contact(self)` - No description
- [MISSING] `FeaturesModel` - No description
  - [MISSING] `FeaturesModel._coerce_bool(cls, v)` - No description
  - [OK] `FeaturesModel._normalize_flags(cls, v)` - Normalize feature flag values to "enabled" or "disabled".

Converts various input formats (boolean, string variants) to the standard
"enabled"/"disabled" literal values using the _coerce_bool helper.

Args:
    v: Input value (bool, str, or other) to normalize

Returns:
    Literal["enabled", "disabled"]: Normalized flag value
- [MISSING] `MessageModel` - No description
  - [OK] `MessageModel._normalize_days(cls, v)` - Normalize days list for message scheduling.

Ensures the days list is not empty by defaulting to ["ALL"] if the
input list is empty or None.

Args:
    v: List of day strings (may be empty)

Returns:
    List[str]: Normalized days list, defaults to ["ALL"] if empty
  - [OK] `MessageModel._normalize_periods(cls, v)` - Normalize time periods list for message scheduling.

Ensures the time_periods list is not empty by defaulting to ["ALL"] if the
input list is empty or None.

Args:
    v: List of time period strings (may be empty)

Returns:
    List[str]: Normalized time periods list, defaults to ["ALL"] if empty
- [MISSING] `MessagesFileModel` - No description
- [MISSING] `PeriodModel` - No description
  - [MISSING] `PeriodModel._valid_days(cls, v)` - No description
  - [MISSING] `PeriodModel._valid_time(cls, v)` - No description
- [MISSING] `PreferencesModel` - No description
  - [OK] `PreferencesModel._validate_categories(cls, v)` - Validate that all categories are in the allowed list.
- [MISSING] `SchedulesModel` - No description
  - [MISSING] `SchedulesModel.to_dict(self)` - No description

#### `core/service.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the MHM backend service.

Sets up communication manager, scheduler manager, and registers emergency shutdown handler.
- [OK] `_check_and_fix_logging__check_recent_activity_timestamps(self, recent_content)` - Check if there's any recent activity within the last 5 minutes using timestamp patterns.
- [OK] `_check_and_fix_logging__ensure_log_file_exists(self)` - Ensure the log file exists, creating it if necessary.
- [OK] `_check_and_fix_logging__force_restart_logging_system(self)` - Force restart the logging system and update the global logger.
- [OK] `_check_and_fix_logging__read_recent_log_content(self)` - Read the last 1000 characters from the log file to check for recent activity.
- [OK] `_check_and_fix_logging__test_logging_functionality(self, test_message)` - Test if logging functionality works by writing a test message and flushing handlers.
- [OK] `_check_and_fix_logging__verify_test_message_present(self, recent_content, test_message, test_timestamp)` - Check if our test message or recent timestamp patterns are present in log content.
- [OK] `_check_reschedule_requests__cleanup_request_file(self, request_file, filename)` - Clean up a processed request file.
- [OK] `_check_reschedule_requests__discover_request_files(self, base_dir)` - Discover all reschedule request files in the base directory.
- [OK] `_check_reschedule_requests__get_base_directory(self)` - Get the base directory for reschedule request files.
- [OK] `_check_reschedule_requests__handle_processing_error(self, request_file, filename, error)` - Handle errors during request processing.
- [OK] `_check_reschedule_requests__parse_request_file(self, request_file)` - Parse and validate a reschedule request file.
- [OK] `_check_reschedule_requests__process_valid_request(self, request_data)` - Process a valid reschedule request.
- [OK] `_check_reschedule_requests__validate_request_data(self, request_data, filename)` - Validate request data and check if it should be processed.
- [OK] `_check_test_message_requests__cleanup_request_file(self, request_file, filename)` - Clean up a processed request file.
- [OK] `_check_test_message_requests__discover_request_files(self, base_dir)` - Discover all test message request files in the base directory.
- [OK] `_check_test_message_requests__get_base_directory(self)` - Get the base directory for test message request files.
- [OK] `_check_test_message_requests__get_message_content(self, user_id, category)` - Get the actual message content that will be sent.
- [OK] `_check_test_message_requests__handle_processing_error(self, request_file, filename, error)` - Handle errors during request processing.
- [OK] `_check_test_message_requests__parse_request_file(self, request_file)` - Parse and validate a test message request file.
- [OK] `_check_test_message_requests__process_valid_request(self, request_data)` - Process a valid test message request.
- [OK] `_check_test_message_requests__validate_request_data(self, request_data, filename)` - Validate request data and check if it should be processed.
- [OK] `_check_test_message_requests__write_response(self, user_id, category, message)` - Write the actual message content to a response file for the UI to read.
- [OK] `_cleanup_test_message_requests__get_base_directory(self)` - Get the base directory for test message request files.
- [OK] `_cleanup_test_message_requests__is_test_message_request_file(self, filename)` - Check if a filename matches the test message request file pattern.
- [OK] `_cleanup_test_message_requests__remove_request_file(self, request_file, filename)` - Remove a single test message request file with proper error handling.
- [OK] `_get_checkin_first_question(self, user_id)` - Get the first question that will be asked in the check-in.
- [OK] `_has_any_request_files(self, base_dir)` - Quick check if any request files exist (optimization to avoid full scan when not needed).
- [OK] `_write_checkin_response(self, user_id, first_question)` - Write the first check-in question to a response file for the UI to read.
- [OK] `check_and_fix_logging(self)` - Check if logging is working and restart if needed
- [OK] `check_checkin_prompt_requests(self)` - Check for and process check-in prompt request files from admin panel
- [OK] `check_reschedule_requests(self)` - Check for and process reschedule request files from UI
- [OK] `check_task_reminder_requests(self)` - Check for and process task reminder request files from admin panel
- [OK] `check_test_message_requests(self)` - Check for and process test message request files from admin panel
- [OK] `cleanup_reschedule_requests(self)` - Clean up any remaining reschedule request files
- [OK] `cleanup_test_message_requests(self)` - Clean up any remaining test message request files
- [OK] `emergency_shutdown(self)` - Emergency shutdown handler registered with atexit
- [OK] `get_scheduler_manager()` - Get the scheduler manager instance from the global service.
Safely handle cases where the global 'service' symbol may not be defined yet.
- [OK] `initialize_paths(self)` - Initialize and verify all required file paths for the service.

Creates paths for log files, user data directories, and message files for all users.

Returns:
    List[str]: List of all initialized file paths
- [OK] `main()` - Main entry point for the MHM backend service.

Creates and starts the service, handling initialization errors and graceful shutdown.
- [OK] `run_service_loop(self)` - Keep the service running until shutdown is requested
- [OK] `shutdown(self)` - Gracefully shutdown the service
- [OK] `signal_handler(self, signum, frame)` - Handle shutdown signals for graceful service termination.

Args:
    signum: Signal number
    frame: Current stack frame
- [OK] `start(self)` - Start the MHM backend service.

Initializes communication channels, scheduler, and begins the main service loop.
Sets up signal handlers for graceful shutdown.
- [OK] `validate_configuration(self)` - Validate all configuration settings before starting the service.
**Classes:**
- [OK] `InitializationError` - Custom exception for initialization errors.
- [MISSING] `MHMService` - No description
  - [OK] `MHMService.__init__(self)` - Initialize the MHM backend service.

Sets up communication manager, scheduler manager, and registers emergency shutdown handler.
  - [OK] `MHMService._check_and_fix_logging__check_recent_activity_timestamps(self, recent_content)` - Check if there's any recent activity within the last 5 minutes using timestamp patterns.
  - [OK] `MHMService._check_and_fix_logging__ensure_log_file_exists(self)` - Ensure the log file exists, creating it if necessary.
  - [OK] `MHMService._check_and_fix_logging__force_restart_logging_system(self)` - Force restart the logging system and update the global logger.
  - [OK] `MHMService._check_and_fix_logging__read_recent_log_content(self)` - Read the last 1000 characters from the log file to check for recent activity.
  - [OK] `MHMService._check_and_fix_logging__test_logging_functionality(self, test_message)` - Test if logging functionality works by writing a test message and flushing handlers.
  - [OK] `MHMService._check_and_fix_logging__verify_test_message_present(self, recent_content, test_message, test_timestamp)` - Check if our test message or recent timestamp patterns are present in log content.
  - [OK] `MHMService._check_reschedule_requests__cleanup_request_file(self, request_file, filename)` - Clean up a processed request file.
  - [OK] `MHMService._check_reschedule_requests__discover_request_files(self, base_dir)` - Discover all reschedule request files in the base directory.
  - [OK] `MHMService._check_reschedule_requests__get_base_directory(self)` - Get the base directory for reschedule request files.
  - [OK] `MHMService._check_reschedule_requests__handle_processing_error(self, request_file, filename, error)` - Handle errors during request processing.
  - [OK] `MHMService._check_reschedule_requests__parse_request_file(self, request_file)` - Parse and validate a reschedule request file.
  - [OK] `MHMService._check_reschedule_requests__process_valid_request(self, request_data)` - Process a valid reschedule request.
  - [OK] `MHMService._check_reschedule_requests__validate_request_data(self, request_data, filename)` - Validate request data and check if it should be processed.
  - [OK] `MHMService._check_test_message_requests__cleanup_request_file(self, request_file, filename)` - Clean up a processed request file.
  - [OK] `MHMService._check_test_message_requests__discover_request_files(self, base_dir)` - Discover all test message request files in the base directory.
  - [OK] `MHMService._check_test_message_requests__get_base_directory(self)` - Get the base directory for test message request files.
  - [OK] `MHMService._check_test_message_requests__get_message_content(self, user_id, category)` - Get the actual message content that will be sent.
  - [OK] `MHMService._check_test_message_requests__handle_processing_error(self, request_file, filename, error)` - Handle errors during request processing.
  - [OK] `MHMService._check_test_message_requests__parse_request_file(self, request_file)` - Parse and validate a test message request file.
  - [OK] `MHMService._check_test_message_requests__process_valid_request(self, request_data)` - Process a valid test message request.
  - [OK] `MHMService._check_test_message_requests__validate_request_data(self, request_data, filename)` - Validate request data and check if it should be processed.
  - [OK] `MHMService._check_test_message_requests__write_response(self, user_id, category, message)` - Write the actual message content to a response file for the UI to read.
  - [OK] `MHMService._cleanup_test_message_requests__get_base_directory(self)` - Get the base directory for test message request files.
  - [OK] `MHMService._cleanup_test_message_requests__is_test_message_request_file(self, filename)` - Check if a filename matches the test message request file pattern.
  - [OK] `MHMService._cleanup_test_message_requests__remove_request_file(self, request_file, filename)` - Remove a single test message request file with proper error handling.
  - [OK] `MHMService._get_checkin_first_question(self, user_id)` - Get the first question that will be asked in the check-in.
  - [OK] `MHMService._has_any_request_files(self, base_dir)` - Quick check if any request files exist (optimization to avoid full scan when not needed).
  - [OK] `MHMService._write_checkin_response(self, user_id, first_question)` - Write the first check-in question to a response file for the UI to read.
  - [OK] `MHMService.check_and_fix_logging(self)` - Check if logging is working and restart if needed
  - [OK] `MHMService.check_checkin_prompt_requests(self)` - Check for and process check-in prompt request files from admin panel
  - [OK] `MHMService.check_reschedule_requests(self)` - Check for and process reschedule request files from UI
  - [OK] `MHMService.check_task_reminder_requests(self)` - Check for and process task reminder request files from admin panel
  - [OK] `MHMService.check_test_message_requests(self)` - Check for and process test message request files from admin panel
  - [OK] `MHMService.cleanup_reschedule_requests(self)` - Clean up any remaining reschedule request files
  - [OK] `MHMService.cleanup_test_message_requests(self)` - Clean up any remaining test message request files
  - [OK] `MHMService.emergency_shutdown(self)` - Emergency shutdown handler registered with atexit
  - [OK] `MHMService.initialize_paths(self)` - Initialize and verify all required file paths for the service.

Creates paths for log files, user data directories, and message files for all users.

Returns:
    List[str]: List of all initialized file paths
  - [OK] `MHMService.run_service_loop(self)` - Keep the service running until shutdown is requested
  - [OK] `MHMService.shutdown(self)` - Gracefully shutdown the service
  - [OK] `MHMService.signal_handler(self, signum, frame)` - Handle shutdown signals for graceful service termination.

Args:
    signum: Signal number
    frame: Current stack frame
  - [OK] `MHMService.start(self)` - Start the MHM backend service.

Initializes communication channels, scheduler, and begins the main service loop.
Sets up signal handlers for graceful shutdown.
  - [OK] `MHMService.validate_configuration(self)` - Validate all configuration settings before starting the service.

#### `core/service_utilities.py`
**Functions:**
- [OK] `__init__(self, interval)` - Initialize the throttler with a specified interval.

Args:
    interval: Time interval in seconds between allowed operations
- [OK] `create_reschedule_request(user_id, category)` - Create a reschedule request file that the service will pick up.

Args:
    user_id: The user ID
    category: The category to reschedule

Returns:
    bool: True if request was created successfully
- [OK] `get_flags_dir()` - Get the directory for service flag files.
- [OK] `get_service_processes()` - Get detailed information about all MHM service processes
- [OK] `is_headless_service_running()` - Check if a headless MHM service is currently running
- [OK] `is_service_running()` - Check if the MHM service is currently running
- [OK] `is_ui_service_running()` - Check if a UI-managed MHM service is currently running
- [OK] `load_and_localize_datetime(datetime_str, timezone_str)` - Load and localize a datetime string to a specific timezone.

Args:
    datetime_str: Datetime string in format "YYYY-MM-DD HH:MM"
    timezone_str: Timezone string (default: 'America/Regina')

Returns:
    datetime: Timezone-aware datetime object

Raises:
    InvalidTimeFormatError: If datetime_str format is invalid
- [OK] `should_run(self)` - Check if enough time has passed since the last run to allow another execution.

IMPORTANT:
- Uses monotonic time (safe for measuring intervals).
- Does NOT update last_run when returning False.
- [OK] `wait_for_network(timeout)` - Wait for the network to be available, retrying every 5 seconds up to a timeout.
**Classes:**
- [OK] `InvalidTimeFormatError` - Exception raised when time format is invalid.

Used for time parsing and validation operations.
- [OK] `Throttler` - A utility class for throttling operations based on time intervals.

Prevents operations from running too frequently by tracking the last execution time.
  - [OK] `Throttler.__init__(self, interval)` - Initialize the throttler with a specified interval.

Args:
    interval: Time interval in seconds between allowed operations
  - [OK] `Throttler.should_run(self)` - Check if enough time has passed since the last run to allow another execution.

IMPORTANT:
- Uses monotonic time (safe for measuring intervals).
- Does NOT update last_run when returning False.

#### `core/tags.py`
**Functions:**
- [OK] `_load_default_tags_from_resources()` - Load default tags from resources/default_tags.json.

Returns:
    List of default tag strings, empty list if file not found or invalid
- [OK] `add_user_tag(user_id, tag)` - Add a tag to user's tag list (lazy initialization).

Args:
    user_id: User ID
    tag: Tag to add

Returns:
    True if successful, False otherwise
- [OK] `ensure_tags_initialized(user_id)` - Ensure tags.json is initialized for a user (lazy creation).
This is called when tasks are enabled or when the first notebook entry is created,
whichever happens first. Safe to call multiple times.

Args:
    user_id: User ID
- [OK] `ensure_user_dir_for_tags(user_id)` - Ensure user directory exists for tags (lazy creation).
Tags are stored as tags.json in the root user directory, like checkins.json and schedules.json.

Args:
    user_id: User ID

Returns:
    Path to user directory, or None if failed
- [OK] `get_user_tags(user_id)` - Get list of user's tags (lazy initialization).

Args:
    user_id: User ID

Returns:
    List of normalized tag strings
- [OK] `load_user_tags(user_id)` - Load user tags data from tags.json (lazy initialization).
Creates directory and file with default tags if they don't exist.

Args:
    user_id: User ID

Returns:
    Dictionary with tags data: {'tags': [...], 'metadata': {...}}
- [OK] `normalize_tag(tag)` - Normalizes a single tag by stripping whitespace, lowercasing, and optionally removing a leading '#'.
- [OK] `normalize_tags(tags)` - Normalizes a list of tags and removes duplicates.
- [OK] `parse_tags_from_text(text)` - Extracts tags (e.g., #tag, key:value) from a text string and returns the cleaned text and normalized tags.
- [OK] `remove_user_tag(user_id, tag)` - Remove a tag from user's tag list.

Args:
    user_id: User ID
    tag: Tag to remove

Returns:
    True if successful, False otherwise
- [OK] `save_user_tags(user_id, tags_data)` - Save user tags data to tags.json (lazy initialization).
Tags are now registered in USER_DATA_LOADERS, so this function can be called
directly or through save_user_data().

Args:
    user_id: User ID
    tags_data: Dictionary with tags data

Returns:
    True if successful, False otherwise
- [OK] `validate_tag(tag)` - Validates a single normalized tag for length and allowed characters.
Raises ValidationError if invalid.

#### `core/time_utilities.py`
**Functions:**
- [OK] `_log_time_error(operation, error)` - Log time utility failures without crashing the caller.
- [OK] `format_timestamp(dt, fmt)` - Format a datetime using a provided format string. Returns "" for None.
- [OK] `format_timestamp_milliseconds(dt)` - Debug-only: format to milliseconds (3 decimals).
Example output: "2026-01-18 12:34:56.789"
- [OK] `now_datetime_full()` - Current local-naive datetime with second precision matching TIMESTAMP_FULL.

This is the canonical replacement for datetime.now() in places that need a
datetime object (arithmetic/comparisons) rather than a formatted string.
- [OK] `now_datetime_minute()` - Current local-naive datetime rounded to minute precision matching TIMESTAMP_MINUTE.

Use for scheduler/UI state where minute precision is the canonical persisted shape.
- [OK] `now_timestamp_filename()` - Current local timestamp formatted with TIMESTAMP_FILENAME.
- [OK] `now_timestamp_full()` - Current local timestamp formatted with TIMESTAMP_FULL.
- [OK] `now_timestamp_minute()` - Current local timestamp formatted with TIMESTAMP_MINUTE.
- [OK] `parse_date_and_time_minute(date_str, time_str)` - Parse a DATE_ONLY + TIME_ONLY_MINUTE combination into a datetime.
Returns None on invalid input.
- [OK] `parse_date_only(value)` - Parse DATE_ONLY (date at 00:00). Returns None on invalid input.
- [OK] `parse_time_only_minute(value)` - Parse TIME_ONLY_MINUTE.
Note: datetime.strptime() will produce a datetime with a default date (1900-01-01).
Returns None on invalid input.
- [OK] `parse_timestamp(value)` - Parse a timestamp string using an allowed set of formats.
Returns None if no allowed format matches.

Use this only when multiple inputs are expected.
Prefer parse_timestamp_full / parse_timestamp_minute for critical state.
- [OK] `parse_timestamp_full(value)` - Parse TIMESTAMP_FULL. Returns None on invalid input.
- [OK] `parse_timestamp_minute(value)` - Parse TIMESTAMP_MINUTE. Returns None on invalid input.

#### `core/ui_management.py`
**Functions:**
- [OK] `_number_after_prefix(name, prefix)` - Extract integer after prefix in name, or None.
- [OK] `_number_from_regex(name, pattern)` - Extract first capture group as int from name using regex, or None.
- [OK] `add_period_row_to_layout(layout, period_widgets, period_name, period_data, parent_widget, delete_callback, after_add_callback)` - Create a period row widget, connect delete, add to layout and list.

Args:
    layout: QVBoxLayout to add the widget to.
    period_widgets: List to append the new widget to.
    period_name: Display name for the period.
    period_data: Dict with start_time, end_time, active, days.
    parent_widget: Parent for the PeriodRowWidget.
    delete_callback: Callback for delete_requested signal.
    after_add_callback: Optional callback(widget) after adding (e.g. for sort).

Returns:
    The created PeriodRowWidget or None on failure.
- [OK] `add_period_widget_to_layout(layout, period_name, period_data, category, parent_widget, widget_list, delete_callback)` - Add a period widget to a layout with proper display formatting.

Args:
    layout: The QVBoxLayout to add the widget to
    period_name: The period name
    period_data: The period data dictionary
    category: The category (tasks, checkin, or schedule category)
    parent_widget: The parent widget for the period widget
    widget_list: Optional list to track widgets
    delete_callback: Optional callback for delete signal

Returns:
    The created PeriodRowWidget or None if failed
- [OK] `clear_period_widgets_from_layout(layout, widget_list)` - Clear all period widgets from a layout.

Args:
    layout: The QVBoxLayout to clear
    widget_list: Optional list to track widgets (will be cleared if provided)

Returns:
    None
- [OK] `collect_period_data_from_widgets(widget_list, category)` - Collect period data from a list of period widgets.

Args:
    widget_list: List of PeriodRowWidget instances
    category: The category (tasks, checkin, or schedule category)

Returns:
    Dictionary of period data with storage-formatted names, each with only 'active', 'days', 'start_time', 'end_time'.
- [OK] `find_lowest_available_period_number(period_widgets, number_from_widget)` - Return the smallest integer >= 2 not used in period names.

Args:
    period_widgets: List of period row widgets (e.g. PeriodRowWidget).
    number_from_widget: Callable that takes a widget and returns the
        number extracted from its name if it matches the pattern, else None.

Returns:
    Lowest available number (>= 2).
- [OK] `load_period_widgets_for_category(layout, user_id, category, parent_widget, widget_list, delete_callback)` - Load and display period widgets for a specific category.

Args:
    layout: The QVBoxLayout to add widgets to
    user_id: The user ID
    category: The category (tasks, checkin, or schedule category)
    parent_widget: The parent widget for period widgets
    widget_list: Optional list to track widgets
    delete_callback: Optional callback for delete signal

Returns:
    List of created widgets
- [OK] `period_name_for_display(period_name, category)` - Convert period name to display format using existing logic.

Args:
    period_name: The period name to convert
    category: The category (tasks, checkin, or schedule category)

Returns:
    Display-formatted period name
- [OK] `period_name_for_storage(display_name, category)` - Convert display period name to storage format.

Args:
    display_name: The display-formatted period name
    category: The category (tasks, checkin, or schedule category)

Returns:
    Storage-formatted period name (preserve original case)
- [OK] `remove_period_row_from_layout(row_widget, layout, period_widgets, deleted_periods, guard_fn)` - Remove a period row from layout and list, store data for undo.

Args:
    row_widget: The period row widget to remove.
    layout: Layout to remove the widget from.
    period_widgets: List to remove the widget from.
    deleted_periods: List to append deleted data dict (period_name, start_time, end_time, active, days).
    guard_fn: If provided, callable(row_widget) returning True to abort removal (e.g. show message and return).

#### `core/user_data_handlers.py`
**Functions:**
- [OK] `_account_default_data(user_id)` - Default account data for auto-create (used only inside _get_user_data__load_impl).
- [OK] `_account_normalize_after_load(data)` - Ensure timezone exists on loaded account data.
- [OK] `_context_default_data(user_id)` - Default context data for auto-create.
- [MISSING] `_ensure_default_loaders_once()` - No description
- [OK] `_get_user_data__load_account(user_id, auto_create)` - Load user account data from account.json.
- [OK] `_get_user_data__load_context(user_id, auto_create)` - Load user context data from user_context.json.
- [OK] `_get_user_data__load_impl(user_id, auto_create, cache_key_prefix, file_key, cache_dict, default_data_factory, validate_fn, log_name, normalize_after_load)` - Internal: common load flow for user data (cache, file, default, validate).
- [OK] `_get_user_data__load_preferences(user_id, auto_create)` - Load user preferences data from preferences.json.
- [OK] `_get_user_data__load_schedules(user_id, auto_create)` - Load user schedules data from schedules.json.
- [OK] `_get_user_data__load_tags(user_id, auto_create)` - Load user tags data from tags.json.
- [OK] `_get_user_id_by_identifier__by_chat_id(chat_id)` - Helper function: Get user ID by chat ID.
- [OK] `_get_user_id_by_identifier__by_discord_user_id(discord_user_id)` - Helper function: Get user ID by Discord user ID using the user index for fast lookup.
- [OK] `_get_user_id_by_identifier__by_email(email)` - Helper function: Get user ID by email using the user index for fast lookup.
- [OK] `_get_user_id_by_identifier__by_internal_username(internal_username)` - Helper function: Get user ID by internal username using the user index for fast lookup.
- [OK] `_get_user_id_by_identifier__by_phone(phone)` - Helper function: Get user ID by phone using the user index for fast lookup.
- [OK] `_load_presets_json()` - Load presets from resources/presets.json (cached).
- [OK] `_preferences_default_data(user_id)` - Default preferences data for auto-create (user_id unused but required by factory signature).
- [OK] `_save_user_data__check_cross_file_invariants(user_id, merged_data, valid_types)` - Check and enforce cross-file invariants using in-memory merged data.

Updates merged_data in-place to maintain invariants without nested saves.

Returns:
    Updated merged_data dict, or None if invariants check failed
- [OK] `_save_user_data__create_backup(user_id, valid_types, create_backup)` - Create backup with validation.

Returns:
    bool: True if successful or not needed, False if failed
- [OK] `_save_user_data__merge_all_types(user_id, data_updates, valid_types, auto_create)` - Phase 1: Merge all data types in-memory.

Returns:
    Dict mapping data type to merged data, or None if merge failed
- [OK] `_save_user_data__merge_single_type(user_id, dt, updates, auto_create)` - Merge updates for a single data type with current data (in-memory only, no disk write).

Returns:
    Dict with merged data, or None if merge failed
- [OK] `_save_user_data__normalize_data(dt, updated)` - Normalize user data with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `_save_user_data__preserve_preference_settings(updated, updates, user_id)` - Preserve preference settings blocks when saving preferences.

Note: task_settings and checkin_settings blocks are preserved even when features are disabled.
This allows users to re-enable features later and restore their previous settings.
Feature enablement is controlled by account.features, not by the presence of settings blocks.

Settings preservation happens automatically through the merge process (current.copy() + updates),
so this function primarily serves as a placeholder for any future preference-specific handling.

Returns:
    bool: True if successful, False if failed
- [OK] `_save_user_data__save_account(user_id, account_data)` - Save user account data to account.json.
- [OK] `_save_user_data__save_context(user_id, context_data)` - Save user context data to user_context.json.
- [OK] `_save_user_data__save_preferences(user_id, preferences_data)` - Save user preferences data to preferences.json.
- [OK] `_save_user_data__save_schedules(user_id, schedules_data)` - Save user schedules data to schedules.json.
- [OK] `_save_user_data__save_tags(user_id, tags_data)` - Save user tags data to tags.json.
- [OK] `_save_user_data__update_index(user_id, result, update_index)` - Update user index with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `_save_user_data__validate_data(user_id, data_updates, valid_types, validate_data, is_new_user)` - Validate user data with enhanced validation.

Returns:
    tuple: (error_messages, validation_results)
- [OK] `_save_user_data__validate_input(user_id, data_updates)` - Validate input parameters with enhanced validation.

Returns:
    tuple: (is_valid, valid_types, error_messages)
- [OK] `_save_user_data__write_all_types(user_id, merged_data, valid_types)` - Phase 2: Write all merged data types to disk atomically.

Returns:
    Dict mapping data type to success status
- [OK] `_schedules_default_data(user_id)` - Default schedules data for auto-create (user_id unused).
- [OK] `clear_user_caches(user_id)` - Clear user data caches.
- [OK] `create_default_schedule_periods(category)` - Create default schedule periods for a new category.
- [OK] `create_new_user(user_data)` - Create a new user with the new data structure.
- [OK] `ensure_all_categories_have_schedules(user_id, suppress_logging)` - Ensure all categories in user preferences have corresponding schedules.
- [OK] `ensure_category_has_default_schedule(user_id, category)` - Ensure a category has default schedule periods if it doesn't exist.
- [OK] `ensure_unique_ids(data)` - Ensure all messages have unique IDs.
- [OK] `get_all_user_ids()` - Get all user IDs from the system.
- [OK] `get_available_data_types()` - Get list of available data types.
- [OK] `get_data_type_info(data_type)` - Get information about a specific data type.
- [OK] `get_predefined_options(field)` - Return predefined options for a personalization field.
- [OK] `get_timezone_options()` - Get timezone options.
- [OK] `get_user_categories(user_id)` - Get user's message categories using centralized data access.
- [OK] `get_user_data(user_id, data_types, fields, auto_create, include_metadata, normalize_on_read)` - Get user data with comprehensive validation.

Returns:
    Dict[str, Any]: User data dictionary, empty dict if failed
- [OK] `get_user_data_with_metadata(user_id, data_types)` - Get user data with file metadata using centralized system.
- [OK] `get_user_id_by_identifier(identifier)` - Get user ID by any identifier (internal_username, email, discord_user_id, phone).
- [OK] `load_and_ensure_ids(user_id)` - Load messages for all categories and ensure IDs are unique for a user.
- [OK] `migrate_legacy_schedules_structure(schedules_data)` - Migrate legacy schedules structure to new format.
- [OK] `register_data_loader(data_type, loader_func, file_type, default_fields, metadata_fields, description)` - Register a new data loader for the centralized system.

Args:
    data_type: Unique identifier for the data type
    loader_func: Function that loads the data
    file_type: File type identifier
    default_fields: Commonly accessed fields
    metadata_fields: Fields that contain metadata
    description: Human-readable description
- [OK] `register_default_loaders()` - Ensure required loaders are registered (idempotent).

Mutates the shared USER_DATA_LOADERS in-place, setting any missing/None
loader entries for: account, preferences, context, schedules, tags.
- [OK] `save_user_data(user_id, data_updates, auto_create, update_index, create_backup, validate_data)` - Save user data with two-phase approach: merge/validate in Phase 1, write in Phase 2.

Implements:
- Two-phase save (merge/validate first, then write)
- In-memory cross-file invariants
- Explicit processing order
- Atomic operations (all succeed or all fail)
- No nested saves
- [OK] `save_user_data_transaction(user_id, data_updates, auto_create)` - Atomic wrapper for user data updates.
- [OK] `update_channel_preferences(user_id, updates)` - Update channel preferences with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_user_account(user_id, updates)` - Update user account with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_user_context(user_id, updates)` - Update user context with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_user_preferences(user_id, updates)` - Update user preferences with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_user_schedules(user_id, schedules_data)` - Update user schedules with validation.

Returns:
    bool: True if successful, False if failed

#### `core/user_data_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the UserDataManager.

Sets up backup directory and index file path for user data management operations.
- [OK] `_get_last_interaction(self, user_id)` - Get the timestamp of the user's last interaction with the system.

Args:
    user_id: The user's ID

Returns:
    str: ISO format timestamp of last interaction, or default if none found
- [OK] `_get_user_data_summary__add_file_info(self, file_path, file_type, summary)` - Add basic file information to the summary.
- [OK] `_get_user_data_summary__add_log_file_info(self, log_file, log_type, summary)` - Add log file information to the summary.
- [OK] `_get_user_data_summary__add_message_file_info(self, file_path, category, summary, orphaned)` - Add message file information to the summary.
- [OK] `_get_user_data_summary__add_missing_message_file_info(self, file_path, category, summary, user_id)` - Add information for missing message files.
- [OK] `_get_user_data_summary__add_schedule_details(self, file_path, summary)` - Add schedule-specific details to the summary.
- [OK] `_get_user_data_summary__add_sent_messages_details(self, file_path, summary)` - Add sent messages count to the summary.
- [OK] `_get_user_data_summary__add_special_file_details(self, file_path, file_type, summary)` - Add special details for specific file types (schedules, sent_messages).
- [OK] `_get_user_data_summary__ensure_message_files(self, user_id, categories)` - Ensure message files exist for all user categories.
- [OK] `_get_user_data_summary__initialize_summary(self, user_id)` - Initialize the summary structure with default values.
- [OK] `_get_user_data_summary__process_core_files(self, user_id, summary)` - Process core user data files (profile, preferences, schedules, etc.).
- [OK] `_get_user_data_summary__process_enabled_message_files(self, user_id, categories, summary)` - Process message files for enabled categories.
- [OK] `_get_user_data_summary__process_log_files(self, user_id, summary)` - Process log files (checkins, chat_interactions).
- [OK] `_get_user_data_summary__process_message_files(self, user_id, summary)` - Process message files for all user categories.
- [OK] `_get_user_data_summary__process_orphaned_message_files(self, user_id, categories, message_files, summary)` - Process orphaned message files (categories not enabled but files exist).
- [OK] `backup_user_data(user_id, include_messages)` - Create a complete backup of user's data with validation.

Returns:
    str: Path to backup file, empty string if failed
- [OK] `backup_user_data(self, user_id, include_messages)` - Create a complete backup of user's data with validation.

Returns:
    str: Path to backup file, empty string if failed
- [OK] `build_user_index()` - Build an index of all users and their message data with validation.

Returns:
    Dict[str, Any]: User index, empty dict if failed
- [OK] `delete_user_completely(user_id, create_backup)` - Completely remove all traces of a user from the system with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `delete_user_completely(self, user_id, create_backup)` - Completely remove all traces of a user from the system with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `export_user_data(user_id, export_format)` - Export all user data to a structured format with validation.

Returns:
    Dict[str, Any]: Exported data, empty dict if failed
- [OK] `export_user_data(self, user_id, export_format)` - Export all user data to a structured format with validation.

Returns:
    Dict[str, Any]: Exported data, empty dict if failed
- [OK] `get_all_user_summaries()` - Get summaries for all users with validation.

Returns:
    List[Dict[str, Any]]: List of user summaries, empty list if failed
- [OK] `get_user_analytics_summary(user_id)` - Get an analytics summary for a user including interaction patterns and data usage.

Args:
    user_id: The user's ID

Returns:
    Dict containing analytics summary information
- [OK] `get_user_data_summary(user_id)` - Get comprehensive summary of user data with validation.

Returns:
    Dict[str, Any]: User data summary, error dict if failed
- [OK] `get_user_data_summary(self, user_id)` - Get comprehensive summary of user data with validation.

Returns:
    Dict[str, Any]: User data summary, error dict if failed
- [OK] `get_user_info_for_data_manager(user_id)` - Get user info using the new centralized data structure with validation.

Returns:
    Optional[Dict[str, Any]]: User info dict or None if failed
- [OK] `get_user_message_files(self, user_id)` - Get all message file paths for a user
- [OK] `get_user_summary(user_id)` - Get a summary of user data and message statistics with validation.

Returns:
    Dict[str, Any]: User summary, empty dict if failed
- [OK] `rebuild_full_index(self)` - Rebuild full user index with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `rebuild_user_index()` - Rebuild the complete user index.

Returns:
    bool: True if index was rebuilt successfully
- [OK] `remove_from_index(self, user_id)` - Remove user from index with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `search_users(self, query, search_fields)` - Search users with validation.

Returns:
    List[Dict[str, Any]]: Search results, empty list if failed
- [OK] `update_message_references(user_id)` - Update message references with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_message_references(self, user_id)` - Add/update message file references in user profile
- [OK] `update_user_index(user_id)` - Update user index with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `update_user_index(self, user_id)` - Update user index with validation.

Returns:
    bool: True if successful, False if failed
**Classes:**
- [OK] `UserDataManager` - Enhanced user data management with references, backup, and indexing capabilities
  - [OK] `UserDataManager.__init__(self)` - Initialize the UserDataManager.

Sets up backup directory and index file path for user data management operations.
  - [OK] `UserDataManager._get_last_interaction(self, user_id)` - Get the timestamp of the user's last interaction with the system.

Args:
    user_id: The user's ID

Returns:
    str: ISO format timestamp of last interaction, or default if none found
  - [OK] `UserDataManager._get_user_data_summary__add_file_info(self, file_path, file_type, summary)` - Add basic file information to the summary.
  - [OK] `UserDataManager._get_user_data_summary__add_log_file_info(self, log_file, log_type, summary)` - Add log file information to the summary.
  - [OK] `UserDataManager._get_user_data_summary__add_message_file_info(self, file_path, category, summary, orphaned)` - Add message file information to the summary.
  - [OK] `UserDataManager._get_user_data_summary__add_missing_message_file_info(self, file_path, category, summary, user_id)` - Add information for missing message files.
  - [OK] `UserDataManager._get_user_data_summary__add_schedule_details(self, file_path, summary)` - Add schedule-specific details to the summary.
  - [OK] `UserDataManager._get_user_data_summary__add_sent_messages_details(self, file_path, summary)` - Add sent messages count to the summary.
  - [OK] `UserDataManager._get_user_data_summary__add_special_file_details(self, file_path, file_type, summary)` - Add special details for specific file types (schedules, sent_messages).
  - [OK] `UserDataManager._get_user_data_summary__ensure_message_files(self, user_id, categories)` - Ensure message files exist for all user categories.
  - [OK] `UserDataManager._get_user_data_summary__initialize_summary(self, user_id)` - Initialize the summary structure with default values.
  - [OK] `UserDataManager._get_user_data_summary__process_core_files(self, user_id, summary)` - Process core user data files (profile, preferences, schedules, etc.).
  - [OK] `UserDataManager._get_user_data_summary__process_enabled_message_files(self, user_id, categories, summary)` - Process message files for enabled categories.
  - [OK] `UserDataManager._get_user_data_summary__process_log_files(self, user_id, summary)` - Process log files (checkins, chat_interactions).
  - [OK] `UserDataManager._get_user_data_summary__process_message_files(self, user_id, summary)` - Process message files for all user categories.
  - [OK] `UserDataManager._get_user_data_summary__process_orphaned_message_files(self, user_id, categories, message_files, summary)` - Process orphaned message files (categories not enabled but files exist).
  - [OK] `UserDataManager.backup_user_data(self, user_id, include_messages)` - Create a complete backup of user's data with validation.

Returns:
    str: Path to backup file, empty string if failed
  - [OK] `UserDataManager.delete_user_completely(self, user_id, create_backup)` - Completely remove all traces of a user from the system with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `UserDataManager.export_user_data(self, user_id, export_format)` - Export all user data to a structured format with validation.

Returns:
    Dict[str, Any]: Exported data, empty dict if failed
  - [OK] `UserDataManager.get_user_data_summary(self, user_id)` - Get comprehensive summary of user data with validation.

Returns:
    Dict[str, Any]: User data summary, error dict if failed
  - [OK] `UserDataManager.get_user_message_files(self, user_id)` - Get all message file paths for a user
  - [OK] `UserDataManager.rebuild_full_index(self)` - Rebuild full user index with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `UserDataManager.remove_from_index(self, user_id)` - Remove user from index with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `UserDataManager.search_users(self, query, search_fields)` - Search users with validation.

Returns:
    List[Dict[str, Any]]: Search results, empty list if failed
  - [OK] `UserDataManager.update_message_references(self, user_id)` - Add/update message file references in user profile
  - [OK] `UserDataManager.update_user_index(self, user_id)` - Update user index with validation.

Returns:
    bool: True if successful, False if failed

#### `core/user_data_validation.py`
**Functions:**
- [OK] `_shared__title_case(text)` - Convert text to title case with special handling for technical terms.
- [OK] `is_valid_category_name(name, max_length, field_name, allow_none)` - Validate that a category/group name is valid.

Category names should be simple identifiers: alphanumeric, spaces, hyphens, underscores.
This is used for grouping/categorizing items (e.g., notebook groups, task categories).

Args:
    name: Category name to validate (can be None if allow_none=True)
    max_length: Maximum allowed length (default: 50)
    field_name: Name of the field being validated (for error messages)
    allow_none: Whether None values are allowed (default: True)

Returns:
    True if category name is valid, False otherwise
- [OK] `is_valid_discord_id(discord_id)` - Validate Discord user ID format.

Discord user IDs are snowflakes (numeric IDs) that are 17-19 digits long.
Empty strings are allowed (Discord ID is optional).

Args:
    discord_id: The Discord user ID to validate

Returns:
    bool: True if valid Discord ID format or empty, False otherwise
- [MISSING] `is_valid_email(email)` - No description
- [MISSING] `is_valid_phone(phone)` - No description
- [OK] `is_valid_string_length(text, max_length, field_name, allow_none)` - Validate that a string is within the specified maximum length.

Args:
    text: String to validate (can be None if allow_none=True)
    max_length: Maximum allowed length
    field_name: Name of the field being validated (for error messages)
    allow_none: Whether None values are allowed

Returns:
    True if string length is valid, False otherwise
- [OK] `validate_new_user_data(user_id, data_updates)` - Validate complete dataset required for a brand-new user.
- [OK] `validate_personalization_data(data)` - Validate *context/personalization* structure.

No field is required; we only type-check fields that are present.
This logic previously lived in the legacy user management utilities.
- [OK] `validate_schedule_periods(periods, category)` - Validate schedule periods and return (is_valid, error_messages).

Args:
    periods: Dictionary of period_name -> period_data
    category: Category name for error messages (e.g., "tasks", "check-ins")

Returns:
    Tuple of (is_valid, list_of_error_messages)
- [MISSING] `validate_schedule_periods__validate_time_format(time_str)` - No description
- [OK] `validate_user_update(user_id, data_type, updates)` - Validate partial updates to an existing user's data.

### `root/` - Root Files

#### `run_headless_service.py`
**Functions:**
- [OK] `main()` - Main entry point for headless service launcher.

#### `run_mhm.py`
**Functions:**
- [OK] `main()` - Launch the MHM Manager UI.

Main entry point for the MHM Manager application. Resolves the Python
interpreter, sets up the environment, and launches the UI application.

Returns:
    int: Exit code (0 for success, 1 for failure)
- [OK] `prepare_launch_environment(script_dir)` - Create an environment dict that prefers the project's virtualenv.

Sets up PATH and PYTHONPATH to ensure the virtual environment is used
and project imports work correctly.

Args:
    script_dir (str): The project directory path

Returns:
    dict: Environment dictionary with PATH and PYTHONPATH configured
- [OK] `resolve_python_interpreter(script_dir)` - Return the preferred Python executable for the given project directory.

Checks for virtual environment Python first, then falls back to system Python.

Args:
    script_dir (str): The project directory path

Returns:
    str: Path to Python executable

#### `run_tests.py`
**Functions:**
- [OK] `_persist_captured_output()` - Persist captured pytest output with ANSI stripping to latest and timestamped logs.
- [OK] `_rotate_console_output_files(backups_dir, archive_dir)` - Keep only recent timestamped console outputs in backups and archive older ones.
- [OK] `build_windows_no_parallel_env()` - Return environment overrides for stable Windows serial UI/no_parallel runs.
- [OK] `check_critical_resources(resources)` - Check if resources exceed critical thresholds requiring termination.
- [OK] `check_resource_warnings(resources)` - Check if resources exceed warning thresholds.
- [OK] `cleanup_orphaned_pytest_processes()` - Find and kill any orphaned pytest worker processes on Windows.

Returns:
    int: Number of orphaned processes found and killed
- [OK] `cleanup_post_run_test_artifacts()` - Best-effort cleanup of transient artifacts after a run.

Keeps outputs that are intentionally useful (e.g., tests/logs, tests/coverage_html),
while removing transient tmp/cache files and common per-run JSON/directories in tests/data.
- [OK] `cleanup_stale_test_artifacts()` - Best-effort cleanup for stale pytest/build artifacts that commonly accumulate on Windows.
- [OK] `detect_stuck_process(last_output_time, current_time, threshold)` - Detect if process appears stuck (no output for extended period).
- [OK] `extract_failures_from_junit_xml(xml_path)` - Extract detailed failure information from JUnit XML.

Returns a list of dicts with 'test', 'message', and 'type' keys.
- [OK] `extract_pytest_session_info(output_text)` - Extract pytest session information from output text.
- [OK] `extract_results_from_output(output_text)` - Extract test results from pytest output text when JUnit XML is unavailable.
- [OK] `interrupt_handler(signum, frame)` - Handle interrupt signals (Ctrl+C) gracefully.
- [OK] `kill_process_tree_windows(pid)` - Kill a process and all its children on Windows.

Returns:
    bool: True if taskkill succeeded, False otherwise
- [OK] `main()` - Main entry point for MHM test runner.

Parses command-line arguments and executes pytest with appropriate configuration
based on the selected test mode (all, fast, unit, integration, behavior, ui, slow).

Returns:
    int: Exit code (0 for success, 1 for failure)
- [OK] `monitor_resources()` - Monitor system resource usage and return metrics.
- [OK] `parse_junit_xml(xml_path)` - Parse JUnit XML report to extract test statistics.

Returns a dictionary with: passed, failed, skipped, warnings, errors, total
- [OK] `print_combined_summary(parallel_results, no_parallel_results, description)` - Print a combined summary of test results from both parallel and serial runs.

Args:
    parallel_results: Results dict from parallel test run (or None if not run)
    no_parallel_results: Results dict from serial test run (or None if not run)
    description: Test mode description
- [OK] `print_test_mode_info()` - Print helpful information about test modes.
- [OK] `read_output(pipe, queue_obj)` - Read from pipe and put lines in queue, also write to terminal.
- [OK] `remove_tree_with_retries(path, retries, delay_seconds)` - Best-effort directory removal with short retries for Windows file-handle lag.
- [OK] `run_command(cmd, description, progress_interval, capture_output, test_context, env_overrides)` - Run a command and return results with periodic progress logs.

Args:
    cmd: Command to run
    description: Description for progress messages
    progress_interval: Seconds between progress updates
    capture_output: If True, capture results via JUnit XML (always True in practice)
    test_context: Optional dict with test run context (mode, phase, config, etc.)

Returns:
    dict with 'success', 'output', 'results', 'duration', 'warnings', 'failures' keys
- [OK] `run_static_logging_check()` - Run the static logging enforcement script before executing tests.
- [OK] `save_partial_results(junit_xml_path, interrupted, output_text, test_context)` - Save partial test results from JUnit XML, falling back to output text parsing.
- [OK] `setup_test_logger()` - Set up logger for test duration logging.

Creates a logger for test run duration logging and ensures the tests/logs
directory exists. Returns a configured logger instance.

Returns:
    logging.Logger: Configured logger instance for test runs
- [MISSING] `signal_handler(signum, frame)` - No description

### `tasks/` - Task Management

#### `tasks/__init__.py`

#### `tasks/task_management.py`
**Functions:**
- [OK] `_calculate_next_due_date(completion_date, recurrence_pattern, recurrence_interval, repeat_after_completion)` - Calculate the next due date for a recurring task.
- [OK] `_create_next_recurring_task_instance(user_id, completed_task)` - Create the next instance of a recurring task when the current one is completed.
- [OK] `add_user_task_tag(user_id, tag)` - Add a new tag to the user's tag list (shared tag system).
- [OK] `are_tasks_enabled(user_id)` - Check if task management is enabled for a user.
- [OK] `cleanup_task_reminders(user_id, task_id)` - Clean up all reminders for a specific task.
- [OK] `complete_task(user_id, task_id, completion_data)` - Mark a task as completed.
- [OK] `create_task(user_id, title, description, due_date, due_time, priority, reminder_periods, tags, quick_reminders, recurrence_pattern, recurrence_interval, repeat_after_completion)` - Create a new task for a user.
- [OK] `delete_task(user_id, task_id)` - Delete a task (permanently remove it).
- [OK] `ensure_task_directory(user_id)` - Ensure the task directory structure exists for a user with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `get_task_by_id(user_id, task_id)` - Get a specific task by ID.
- [OK] `get_tasks_due_soon(user_id, days_ahead)` - Get tasks due within the specified number of days.
- [OK] `get_user_task_stats(user_id)` - Get task statistics for a user.
- [OK] `load_active_tasks(user_id)` - Load active tasks for a user with validation.

Returns:
    List[Dict[str, Any]]: List of active tasks, empty list if failed
- [OK] `load_completed_tasks(user_id)` - Load completed tasks for a user.
- [OK] `remove_user_task_tag(user_id, tag)` - Remove a tag from the user's tag list (shared tag system).
- [OK] `restore_task(user_id, task_id)` - Restore a completed task to active status.
- [OK] `save_active_tasks(user_id, tasks)` - Save active tasks for a user.
- [OK] `save_completed_tasks(user_id, tasks)` - Save completed tasks for a user.
- [OK] `schedule_task_reminders(user_id, task_id, reminder_periods)` - Schedule reminders for a specific task based on its reminder periods.
- [OK] `setup_default_task_tags(user_id)` - Set up default tags for a user when task management is first enabled.
This initializes the tags directory and tags.json with default tags if they don't exist.
- [OK] `update_task(user_id, task_id, updates)` - Update an existing task.
**Classes:**
- [OK] `TaskManagementError` - Custom exception for task management errors.

### `ui/` - User Interface Components

#### `ui/__init__.py`

#### `ui/dialogs/__init__.py`

#### `ui/dialogs/account_creator_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, communication_manager)` - Initialize the account creator dialog.
- [OK] `_build_features_dict(self, features_enabled)` - Build features dictionary in the correct format.
- [OK] `_determine_chat_id(self, channel_type, email, phone, discord_user_id)` - Determine chat_id based on channel type.
- [OK] `_validate_and_accept__add_feature_settings(self, user_preferences, account_data, features_enabled)` - Add feature-specific settings to user preferences.
- [OK] `_validate_and_accept__build_account_data(self, username, preferred_name, timezone, channel_data, contact_info, categories, task_settings, checkin_settings, messages_enabled, tasks_enabled, checkins_enabled)` - Build the complete account data structure.
- [OK] `_validate_and_accept__build_user_preferences(self, account_data)` - Build user preferences data structure.
- [OK] `_validate_and_accept__collect_basic_user_info(self)` - Collect basic user information from UI fields.
- [OK] `_validate_and_accept__collect_channel_data(self)` - Collect channel and contact information from widgets.
- [OK] `_validate_and_accept__collect_data(self)` - Collect all data from UI and build account data structure.
- [OK] `_validate_and_accept__collect_feature_settings(self)` - Collect feature enablement states from UI.
- [OK] `_validate_and_accept__collect_widget_data(self)` - Collect data from all widgets.
- [OK] `_validate_and_accept__create_account(self, account_data)` - Create the account and set up all necessary components.
- [OK] `_validate_and_accept__handle_success(self, username)` - Handle successful account creation.
- [OK] `_validate_and_accept__input_errors(self)` - Validate input and show error dialog if validation fails.
- [OK] `_validate_and_accept__schedule_new_user(self, user_id)` - Schedule the new user in the scheduler.
- [OK] `_validate_and_accept__setup_task_tags(self, user_id, account_data)` - Set up task tags for the new user.
- [OK] `_validate_and_accept__show_error_dialog(self, title, message)` - Show an error dialog with the given title and message.
- [OK] `_validate_and_accept__show_success_dialog(self, username)` - Show a success dialog for account creation.
- [OK] `_validate_and_accept__update_user_index(self, user_id)` - Update user index for the new user.
- [OK] `accept(self)` - Override accept to prevent automatic dialog closing.
- [OK] `center_dialog(self)` - Center the dialog on the parent window.
- [OK] `close_dialog(self)` - Close the dialog properly.
- [OK] `create_account(self, account_data)` - Create the user account.
- [OK] `create_account_dialog(parent, communication_manager)` - Create and show the account creation dialog.
- [OK] `get_account_data(self)` - Get the account data from the form.
- [OK] `keyPressEvent(self, event)` - Handle key press events for the dialog.
- [OK] `load_category_widget(self)` - Load the category selection widget.
- [OK] `load_checkin_settings_widget(self)` - Load the check-in settings widget.
- [OK] `load_message_service_widget(self)` - Load the message service selection widget.
- [OK] `load_task_management_widget(self)` - Load the task management widget.
- [OK] `load_widgets(self)` - Load all the widget UI files into the placeholder widgets.
- [OK] `on_feature_toggled(self, checked)` - Handle feature enablement checkbox toggles.
- [MISSING] `on_personalization_save(data)` - No description
- [OK] `on_preferred_name_changed(self, text)` - Handle preferred name change.

Args:
    text: The new text from the textChanged signal (ignored, we read from widget)
- [OK] `on_username_changed(self, text)` - Handle username change.

Args:
    text: The new text from the textChanged signal (ignored, we read from widget)
- [OK] `open_personalization_dialog(self)` - Open the personalization dialog.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_dialog(self)` - Set up the dialog properties.
- [OK] `setup_feature_group_boxes(self)` - Setup group boxes for task management and check-ins (no longer collapsible in tab structure).
- [OK] `setup_profile_button(self)` - Setup the profile button.
- [OK] `update_profile_button_state(self)` - Update the profile button to show if profile has been configured.
- [OK] `update_tab_visibility(self)` - Update tab visibility based on feature enablement.
- [OK] `username(self)` - Get username from field if not set, ensuring we always have the latest value.
- [OK] `username(self, value)` - Set username value.
- [OK] `validate_account_data(self)` - Validate the account data.
- [OK] `validate_all_fields_static(username, preferred_name)` - Static method to validate all fields without UI dependencies.
- [OK] `validate_and_accept(self)` - Validate input and accept the dialog.
- [OK] `validate_input(self)` - Validate the input and return (is_valid, error_message).
- [OK] `validate_preferred_name_static(name)` - Static method to validate preferred name without UI dependencies.
- [OK] `validate_username_static(username)` - Static method to validate username without UI dependencies.
**Classes:**
- [OK] `AccountCreatorDialog` - Account creation dialog using existing UI files.
  - [OK] `AccountCreatorDialog.__init__(self, parent, communication_manager)` - Initialize the account creator dialog.
  - [OK] `AccountCreatorDialog._build_features_dict(self, features_enabled)` - Build features dictionary in the correct format.
  - [OK] `AccountCreatorDialog._determine_chat_id(self, channel_type, email, phone, discord_user_id)` - Determine chat_id based on channel type.
  - [OK] `AccountCreatorDialog._validate_and_accept__add_feature_settings(self, user_preferences, account_data, features_enabled)` - Add feature-specific settings to user preferences.
  - [OK] `AccountCreatorDialog._validate_and_accept__build_account_data(self, username, preferred_name, timezone, channel_data, contact_info, categories, task_settings, checkin_settings, messages_enabled, tasks_enabled, checkins_enabled)` - Build the complete account data structure.
  - [OK] `AccountCreatorDialog._validate_and_accept__build_user_preferences(self, account_data)` - Build user preferences data structure.
  - [OK] `AccountCreatorDialog._validate_and_accept__collect_basic_user_info(self)` - Collect basic user information from UI fields.
  - [OK] `AccountCreatorDialog._validate_and_accept__collect_channel_data(self)` - Collect channel and contact information from widgets.
  - [OK] `AccountCreatorDialog._validate_and_accept__collect_data(self)` - Collect all data from UI and build account data structure.
  - [OK] `AccountCreatorDialog._validate_and_accept__collect_feature_settings(self)` - Collect feature enablement states from UI.
  - [OK] `AccountCreatorDialog._validate_and_accept__collect_widget_data(self)` - Collect data from all widgets.
  - [OK] `AccountCreatorDialog._validate_and_accept__create_account(self, account_data)` - Create the account and set up all necessary components.
  - [OK] `AccountCreatorDialog._validate_and_accept__handle_success(self, username)` - Handle successful account creation.
  - [OK] `AccountCreatorDialog._validate_and_accept__input_errors(self)` - Validate input and show error dialog if validation fails.
  - [OK] `AccountCreatorDialog._validate_and_accept__schedule_new_user(self, user_id)` - Schedule the new user in the scheduler.
  - [OK] `AccountCreatorDialog._validate_and_accept__setup_task_tags(self, user_id, account_data)` - Set up task tags for the new user.
  - [OK] `AccountCreatorDialog._validate_and_accept__show_error_dialog(self, title, message)` - Show an error dialog with the given title and message.
  - [OK] `AccountCreatorDialog._validate_and_accept__show_success_dialog(self, username)` - Show a success dialog for account creation.
  - [OK] `AccountCreatorDialog._validate_and_accept__update_user_index(self, user_id)` - Update user index for the new user.
  - [OK] `AccountCreatorDialog.accept(self)` - Override accept to prevent automatic dialog closing.
  - [OK] `AccountCreatorDialog.center_dialog(self)` - Center the dialog on the parent window.
  - [OK] `AccountCreatorDialog.close_dialog(self)` - Close the dialog properly.
  - [OK] `AccountCreatorDialog.create_account(self, account_data)` - Create the user account.
  - [OK] `AccountCreatorDialog.get_account_data(self)` - Get the account data from the form.
  - [OK] `AccountCreatorDialog.keyPressEvent(self, event)` - Handle key press events for the dialog.
  - [OK] `AccountCreatorDialog.load_category_widget(self)` - Load the category selection widget.
  - [OK] `AccountCreatorDialog.load_checkin_settings_widget(self)` - Load the check-in settings widget.
  - [OK] `AccountCreatorDialog.load_message_service_widget(self)` - Load the message service selection widget.
  - [OK] `AccountCreatorDialog.load_task_management_widget(self)` - Load the task management widget.
  - [OK] `AccountCreatorDialog.load_widgets(self)` - Load all the widget UI files into the placeholder widgets.
  - [OK] `AccountCreatorDialog.on_feature_toggled(self, checked)` - Handle feature enablement checkbox toggles.
  - [OK] `AccountCreatorDialog.on_preferred_name_changed(self, text)` - Handle preferred name change.

Args:
    text: The new text from the textChanged signal (ignored, we read from widget)
  - [OK] `AccountCreatorDialog.on_username_changed(self, text)` - Handle username change.

Args:
    text: The new text from the textChanged signal (ignored, we read from widget)
  - [OK] `AccountCreatorDialog.open_personalization_dialog(self)` - Open the personalization dialog.
  - [OK] `AccountCreatorDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `AccountCreatorDialog.setup_dialog(self)` - Set up the dialog properties.
  - [OK] `AccountCreatorDialog.setup_feature_group_boxes(self)` - Setup group boxes for task management and check-ins (no longer collapsible in tab structure).
  - [OK] `AccountCreatorDialog.setup_profile_button(self)` - Setup the profile button.
  - [OK] `AccountCreatorDialog.update_profile_button_state(self)` - Update the profile button to show if profile has been configured.
  - [OK] `AccountCreatorDialog.update_tab_visibility(self)` - Update tab visibility based on feature enablement.
  - [OK] `AccountCreatorDialog.username(self)` - Get username from field if not set, ensuring we always have the latest value.
  - [OK] `AccountCreatorDialog.username(self, value)` - Set username value.
  - [OK] `AccountCreatorDialog.validate_account_data(self)` - Validate the account data.
  - [OK] `AccountCreatorDialog.validate_all_fields_static(username, preferred_name)` - Static method to validate all fields without UI dependencies.
  - [OK] `AccountCreatorDialog.validate_and_accept(self)` - Validate input and accept the dialog.
  - [OK] `AccountCreatorDialog.validate_input(self)` - Validate the input and return (is_valid, error_message).
  - [OK] `AccountCreatorDialog.validate_preferred_name_static(name)` - Static method to validate preferred name without UI dependencies.
  - [OK] `AccountCreatorDialog.validate_username_static(username)` - Static method to validate username without UI dependencies.

#### `ui/dialogs/admin_panel.py`
**Functions:**
- [OK] `__init__(self, parent)` - Initialize the AdminPanelDialog.

Args:
    parent: Parent widget for the dialog
- [OK] `get_admin_data(self)` - Get the admin panel data.

Returns:
    dict: Admin panel data (currently returns empty dict as placeholder)
- [OK] `set_admin_data(self, data)` - Set the admin panel data.

Args:
    data: Admin panel data to set (currently not implemented)
- [OK] `setup_ui(self)` - Setup the UI components.
**Classes:**
- [OK] `AdminPanelDialog` - Dialog for admin panel functionality.
  - [OK] `AdminPanelDialog.__init__(self, parent)` - Initialize the AdminPanelDialog.

Args:
    parent: Parent widget for the dialog
  - [OK] `AdminPanelDialog.get_admin_data(self)` - Get the admin panel data.

Returns:
    dict: Admin panel data (currently returns empty dict as placeholder)
  - [OK] `AdminPanelDialog.set_admin_data(self, data)` - Set the admin panel data.

Args:
    data: Admin panel data to set (currently not implemented)
  - [OK] `AdminPanelDialog.setup_ui(self)` - Setup the UI components.

#### `ui/dialogs/category_management_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [MISSING] `get_selected_categories(self)` - No description
- [OK] `load_user_category_data(self)` - Load user's current category settings
- [OK] `on_enable_messages_toggled(self, checked)` - Handle enable automated messages checkbox toggle.
- [OK] `save_category_settings(self)` - Save the selected categories back to user preferences
- [MISSING] `set_selected_categories(self, categories)` - No description
**Classes:**
- [MISSING] `CategoryManagementDialog` - No description
  - [OK] `CategoryManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - [MISSING] `CategoryManagementDialog.get_selected_categories(self)` - No description
  - [OK] `CategoryManagementDialog.load_user_category_data(self)` - Load user's current category settings
  - [OK] `CategoryManagementDialog.on_enable_messages_toggled(self, checked)` - Handle enable automated messages checkbox toggle.
  - [OK] `CategoryManagementDialog.save_category_settings(self)` - Save the selected categories back to user preferences
  - [MISSING] `CategoryManagementDialog.set_selected_categories(self, categories)` - No description

#### `ui/dialogs/channel_management_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [OK] `_on_save_clicked(self)` - Wrapper to handle save button click and show error dialog if needed.
- [MISSING] `get_selected_channel(self)` - No description
- [MISSING] `load_user_channel_data()` - No description
- [MISSING] `save_channel_settings(self)` - No description
- [MISSING] `set_selected_channel(self, channel, value)` - No description
**Classes:**
- [MISSING] `ChannelManagementDialog` - No description
  - [OK] `ChannelManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - [OK] `ChannelManagementDialog._on_save_clicked(self)` - Wrapper to handle save button click and show error dialog if needed.
  - [MISSING] `ChannelManagementDialog.get_selected_channel(self)` - No description
  - [MISSING] `ChannelManagementDialog.save_channel_settings(self)` - No description
  - [MISSING] `ChannelManagementDialog.set_selected_channel(self, channel, value)` - No description

#### `ui/dialogs/checkin_management_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [OK] `get_checkin_settings(self)` - Get the current check-in settings.
- [OK] `load_user_checkin_data(self)` - Load the user's current check-in settings
- [MISSING] `on_enable_checkins_toggled(self, checked)` - No description
- [OK] `save_checkin_settings(self)` - Save the check-in settings back to user preferences
- [OK] `set_checkin_settings(self, settings)` - Set the check-in settings.
**Classes:**
- [OK] `CheckinManagementDialog` - Dialog for managing check-in settings.
  - [OK] `CheckinManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - [OK] `CheckinManagementDialog.get_checkin_settings(self)` - Get the current check-in settings.
  - [OK] `CheckinManagementDialog.load_user_checkin_data(self)` - Load the user's current check-in settings
  - [MISSING] `CheckinManagementDialog.on_enable_checkins_toggled(self, checked)` - No description
  - [OK] `CheckinManagementDialog.save_checkin_settings(self)` - Save the check-in settings back to user preferences
  - [OK] `CheckinManagementDialog.set_checkin_settings(self, settings)` - Set the check-in settings.

#### `ui/dialogs/message_editor_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, category, message_data)` - Initialize the message edit dialog.
- [OK] `__init__(self, parent, user_id, category)` - Initialize the message editor dialog.
- [OK] `add_new_message(self)` - Add a new message.
- [OK] `delete_message_by_row(self, row)` - Delete message at the specified row.
- [OK] `edit_message_by_row(self, row)` - Edit message at the specified row.
- [OK] `edit_selected_message(self, item)` - Edit the selected message.
- [OK] `load_message_data(self)` - Load existing message data if editing.
- [OK] `load_messages(self)` - Load messages for the category.
- [OK] `open_message_editor_dialog(parent, user_id, category)` - Open the message editor dialog.
- [OK] `populate_table(self)` - Populate the table with messages.
- [OK] `save_message(self)` - Save the message data.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_initial_state(self)` - Setup initial dialog state.
- [OK] `setup_ui(self)` - Setup the UI components.
- [OK] `show_no_messages_state(self)` - Show state when no messages are found.
- [OK] `update_message_count(self)` - Update the message count label.
**Classes:**
- [OK] `MessageEditDialog` - Dialog for editing or adding a message.
  - [OK] `MessageEditDialog.__init__(self, parent, user_id, category, message_data)` - Initialize the message edit dialog.
  - [OK] `MessageEditDialog.load_message_data(self)` - Load existing message data if editing.
  - [OK] `MessageEditDialog.save_message(self)` - Save the message data.
  - [OK] `MessageEditDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `MessageEditDialog.setup_ui(self)` - Setup the UI components.
- [OK] `MessageEditorDialog` - Dialog for managing messages in a category.
  - [OK] `MessageEditorDialog.__init__(self, parent, user_id, category)` - Initialize the message editor dialog.
  - [OK] `MessageEditorDialog.add_new_message(self)` - Add a new message.
  - [OK] `MessageEditorDialog.delete_message_by_row(self, row)` - Delete message at the specified row.
  - [OK] `MessageEditorDialog.edit_message_by_row(self, row)` - Edit message at the specified row.
  - [OK] `MessageEditorDialog.edit_selected_message(self, item)` - Edit the selected message.
  - [OK] `MessageEditorDialog.load_messages(self)` - Load messages for the category.
  - [OK] `MessageEditorDialog.populate_table(self)` - Populate the table with messages.
  - [OK] `MessageEditorDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `MessageEditorDialog.setup_initial_state(self)` - Setup initial dialog state.
  - [OK] `MessageEditorDialog.show_no_messages_state(self)` - Show state when no messages are found.
  - [OK] `MessageEditorDialog.update_message_count(self)` - Update the message count label.

#### `ui/dialogs/process_watcher_dialog.py`
**Functions:**
- [OK] `__init__(self, parent)` - Initialize the ProcessWatcherDialog.

Args:
    parent: Parent widget for the dialog
- [OK] `closeEvent(self, event)` - Handle dialog close event.
- [OK] `on_process_selected(self)` - Handle process selection change.
- [OK] `refresh_processes(self)` - Refresh the process information.
- [OK] `setup_all_processes_tab(self)` - Setup the tab showing all Python processes.
- [OK] `setup_mhm_processes_tab(self)` - Setup the tab showing MHM-specific processes.
- [OK] `setup_process_details_tab(self)` - Setup the tab showing detailed process information.
- [OK] `setup_timer(self)` - Setup the auto-refresh timer.
- [OK] `setup_ui(self)` - Setup the UI components.
- [OK] `show_process_details(self, pid)` - Show detailed information about a process.
- [OK] `toggle_auto_refresh(self)` - Toggle auto-refresh functionality.
- [OK] `update_all_processes(self)` - Update the all processes table.
- [OK] `update_mhm_processes(self)` - Update the MHM processes table.
- [OK] `update_process_details_from_all(self)` - Update process details from all processes table.
- [OK] `update_process_details_from_mhm(self)` - Update process details from MHM processes table.
**Classes:**
- [OK] `ProcessWatcherDialog` - Dialog for monitoring Python processes and their associations.
  - [OK] `ProcessWatcherDialog.__init__(self, parent)` - Initialize the ProcessWatcherDialog.

Args:
    parent: Parent widget for the dialog
  - [OK] `ProcessWatcherDialog.closeEvent(self, event)` - Handle dialog close event.
  - [OK] `ProcessWatcherDialog.on_process_selected(self)` - Handle process selection change.
  - [OK] `ProcessWatcherDialog.refresh_processes(self)` - Refresh the process information.
  - [OK] `ProcessWatcherDialog.setup_all_processes_tab(self)` - Setup the tab showing all Python processes.
  - [OK] `ProcessWatcherDialog.setup_mhm_processes_tab(self)` - Setup the tab showing MHM-specific processes.
  - [OK] `ProcessWatcherDialog.setup_process_details_tab(self)` - Setup the tab showing detailed process information.
  - [OK] `ProcessWatcherDialog.setup_timer(self)` - Setup the auto-refresh timer.
  - [OK] `ProcessWatcherDialog.setup_ui(self)` - Setup the UI components.
  - [OK] `ProcessWatcherDialog.show_process_details(self, pid)` - Show detailed information about a process.
  - [OK] `ProcessWatcherDialog.toggle_auto_refresh(self)` - Toggle auto-refresh functionality.
  - [OK] `ProcessWatcherDialog.update_all_processes(self)` - Update the all processes table.
  - [OK] `ProcessWatcherDialog.update_mhm_processes(self)` - Update the MHM processes table.
  - [OK] `ProcessWatcherDialog.update_process_details_from_all(self)` - Update process details from all processes table.
  - [OK] `ProcessWatcherDialog.update_process_details_from_mhm(self)` - Update process details from MHM processes table.

#### `ui/dialogs/schedule_editor_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, category, on_save)` - Initialize the object.
- [OK] `_after_add_period(self, period_widget)` - Set creation order and resort after adding a period (for add_period_row_to_layout).
- [OK] `_trigger_rescheduling(self)` - Trigger rescheduling for this user and category when schedule changes.
- [OK] `accept(self)` - Override accept to prevent automatic dialog closing.
- [OK] `add_new_period(self, period_name, period_data)` - Add a new period row using the PeriodRowWidget.
- [OK] `cancel(self)` - Cancel the dialog.
- [OK] `center_dialog(self)` - Center the dialog on the parent window.
- [OK] `close_dialog(self)` - Close the dialog properly after successful save.
- [OK] `collect_period_data(self)` - Collect period data using the new reusable function.
- [OK] `find_lowest_available_period_number(self)` - Find the lowest available number for new period names.
- [OK] `get_schedule_data(self)` - Get the current schedule data.
- [MISSING] `guard(rw)` - No description
- [OK] `handle_save(self)` - Handle save button click - prevents dialog closure on validation errors.
- [OK] `load_existing_data(self)` - Load existing schedule data using the new reusable function.
- [MISSING] `number_from_widget(w)` - No description
- [OK] `open_schedule_editor(parent, user_id, category, on_save)` - Open the schedule editor dialog.
- [OK] `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- [OK] `resort_period_widgets(self)` - Re-sort the period widgets to maintain proper order (ALL at bottom).
- [OK] `save_schedule(self)` - Save the schedule data.
- [OK] `set_schedule_data(self, data)` - Set the schedule data.
- [OK] `setup_functionality(self)` - Setup the functionality and connect signals.
- [OK] `sort_key(widget)` - Generate a sort key for period widgets.

Args:
    widget: PeriodRowWidget instance to generate sort key for

Returns:
    Tuple of (priority, sort_value) where priority determines position
    (ALL periods get highest priority to appear last)
- [OK] `undo_last_delete(self)` - Undo the last deletion.
**Classes:**
- [OK] `ScheduleEditorDialog` - Dialog for editing schedules.
  - [OK] `ScheduleEditorDialog.__init__(self, parent, user_id, category, on_save)` - Initialize the object.
  - [OK] `ScheduleEditorDialog._after_add_period(self, period_widget)` - Set creation order and resort after adding a period (for add_period_row_to_layout).
  - [OK] `ScheduleEditorDialog._trigger_rescheduling(self)` - Trigger rescheduling for this user and category when schedule changes.
  - [OK] `ScheduleEditorDialog.accept(self)` - Override accept to prevent automatic dialog closing.
  - [OK] `ScheduleEditorDialog.add_new_period(self, period_name, period_data)` - Add a new period row using the PeriodRowWidget.
  - [OK] `ScheduleEditorDialog.cancel(self)` - Cancel the dialog.
  - [OK] `ScheduleEditorDialog.center_dialog(self)` - Center the dialog on the parent window.
  - [OK] `ScheduleEditorDialog.close_dialog(self)` - Close the dialog properly after successful save.
  - [OK] `ScheduleEditorDialog.collect_period_data(self)` - Collect period data using the new reusable function.
  - [OK] `ScheduleEditorDialog.find_lowest_available_period_number(self)` - Find the lowest available number for new period names.
  - [OK] `ScheduleEditorDialog.get_schedule_data(self)` - Get the current schedule data.
  - [OK] `ScheduleEditorDialog.handle_save(self)` - Handle save button click - prevents dialog closure on validation errors.
  - [OK] `ScheduleEditorDialog.load_existing_data(self)` - Load existing schedule data using the new reusable function.
  - [OK] `ScheduleEditorDialog.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - [OK] `ScheduleEditorDialog.resort_period_widgets(self)` - Re-sort the period widgets to maintain proper order (ALL at bottom).
  - [OK] `ScheduleEditorDialog.save_schedule(self)` - Save the schedule data.
  - [OK] `ScheduleEditorDialog.set_schedule_data(self, data)` - Set the schedule data.
  - [OK] `ScheduleEditorDialog.setup_functionality(self)` - Setup the functionality and connect signals.
  - [OK] `ScheduleEditorDialog.undo_last_delete(self)` - Undo the last deletion.

#### `ui/dialogs/task_completion_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, task_title)` - Initialize the task completion dialog.
- [OK] `get_completion_data(self)` - Get all completion data as a dictionary.
- [OK] `get_completion_date(self)` - Get completion date as string.
- [OK] `get_completion_notes(self)` - Get completion notes.
- [OK] `get_completion_time(self)` - Get completion time as 24-hour format string.
- [OK] `setup_completion_time_components(self)` - Setup the completion time input components.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_ui(self)` - Setup the UI components.
**Classes:**
- [OK] `TaskCompletionDialog` - Dialog for specifying task completion details.
  - [OK] `TaskCompletionDialog.__init__(self, parent, task_title)` - Initialize the task completion dialog.
  - [OK] `TaskCompletionDialog.get_completion_data(self)` - Get all completion data as a dictionary.
  - [OK] `TaskCompletionDialog.get_completion_date(self)` - Get completion date as string.
  - [OK] `TaskCompletionDialog.get_completion_notes(self)` - Get completion notes.
  - [OK] `TaskCompletionDialog.get_completion_time(self)` - Get completion time as 24-hour format string.
  - [OK] `TaskCompletionDialog.setup_completion_time_components(self)` - Setup the completion time input components.
  - [OK] `TaskCompletionDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `TaskCompletionDialog.setup_ui(self)` - Setup the UI components.

#### `ui/dialogs/task_crud_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the task CRUD dialog.
- [OK] `add_new_task(self)` - Open dialog to add a new task.
- [OK] `complete_selected_task(self)` - Mark the selected task as completed.
- [OK] `delete_completed_task(self)` - Permanently delete a completed task.
- [OK] `delete_selected_task(self)` - Delete the selected task.
- [OK] `edit_selected_task(self)` - Edit the selected task.
- [OK] `get_selected_task_id(self, table)` - Get the task ID of the selected row in the given table.
- [OK] `load_data(self)` - Load all task data and update displays.
- [OK] `refresh_active_tasks(self)` - Refresh the active tasks table.
- [OK] `refresh_completed_tasks(self)` - Refresh the completed tasks table.
- [OK] `restore_selected_task(self)` - Restore a completed task to active status.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_ui(self)` - Setup the UI components.
- [OK] `update_statistics(self)` - Update the statistics display.
**Classes:**
- [OK] `TaskCrudDialog` - Dialog for full CRUD operations on tasks.
  - [OK] `TaskCrudDialog.__init__(self, parent, user_id)` - Initialize the task CRUD dialog.
  - [OK] `TaskCrudDialog.add_new_task(self)` - Open dialog to add a new task.
  - [OK] `TaskCrudDialog.complete_selected_task(self)` - Mark the selected task as completed.
  - [OK] `TaskCrudDialog.delete_completed_task(self)` - Permanently delete a completed task.
  - [OK] `TaskCrudDialog.delete_selected_task(self)` - Delete the selected task.
  - [OK] `TaskCrudDialog.edit_selected_task(self)` - Edit the selected task.
  - [OK] `TaskCrudDialog.get_selected_task_id(self, table)` - Get the task ID of the selected row in the given table.
  - [OK] `TaskCrudDialog.load_data(self)` - Load all task data and update displays.
  - [OK] `TaskCrudDialog.refresh_active_tasks(self)` - Refresh the active tasks table.
  - [OK] `TaskCrudDialog.refresh_completed_tasks(self)` - Refresh the completed tasks table.
  - [OK] `TaskCrudDialog.restore_selected_task(self)` - Restore a completed task to active status.
  - [OK] `TaskCrudDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `TaskCrudDialog.setup_ui(self)` - Setup the UI components.
  - [OK] `TaskCrudDialog.update_statistics(self)` - Update the statistics display.

#### `ui/dialogs/task_edit_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, task_data)` - Initialize the task edit dialog.
- [OK] `add_reminder_period(self)` - Add a new reminder period.
- [OK] `collect_quick_reminders(self)` - Collect quick reminder options.
- [OK] `collect_recurring_task_data(self)` - Collect recurring task settings from the form.
- [OK] `collect_reminder_periods(self)` - Collect reminder period data from the UI.
- [OK] `collect_selected_tags(self)` - Collect selected tags from the tag widget.
- [OK] `delete_reminder_period(self, index)` - Delete a reminder period.
- [OK] `get_due_time_as_24h(self)` - Get due time as 24-hour format string.
- [OK] `load_recurring_task_data(self)` - Load recurring task data into the form.
- [OK] `load_task_data(self)` - Load existing task data into the form.
- [OK] `on_hour_changed(self, hour_text)` - Handle hour selection change.
- [OK] `on_minute_changed(self, minute_text)` - Handle minute selection change.
- [OK] `on_no_due_date_toggled(self, checked)` - Handle No Due Date checkbox toggle.
- [OK] `on_recurring_pattern_changed(self, pattern_text)` - Handle recurring pattern selection change.
- [OK] `render_reminder_period_row(self, index, period)` - Render a single reminder period row.
- [OK] `render_reminder_periods(self)` - Render the reminder periods in the UI.
- [OK] `save_task(self)` - Save the task data.
- [OK] `set_due_time_from_24h(self, time)` - Set due time components from 24-hour time.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_due_time_components(self)` - Setup the due time input components.
- [OK] `setup_recurring_task_components(self)` - Setup the recurring task input components.
- [OK] `setup_ui(self)` - Setup the UI components.
- [OK] `validate_form(self)` - Validate the form data.
**Classes:**
- [OK] `TaskEditDialog` - Dialog for creating or editing tasks.
  - [OK] `TaskEditDialog.__init__(self, parent, user_id, task_data)` - Initialize the task edit dialog.
  - [OK] `TaskEditDialog.add_reminder_period(self)` - Add a new reminder period.
  - [OK] `TaskEditDialog.collect_quick_reminders(self)` - Collect quick reminder options.
  - [OK] `TaskEditDialog.collect_recurring_task_data(self)` - Collect recurring task settings from the form.
  - [OK] `TaskEditDialog.collect_reminder_periods(self)` - Collect reminder period data from the UI.
  - [OK] `TaskEditDialog.collect_selected_tags(self)` - Collect selected tags from the tag widget.
  - [OK] `TaskEditDialog.delete_reminder_period(self, index)` - Delete a reminder period.
  - [OK] `TaskEditDialog.get_due_time_as_24h(self)` - Get due time as 24-hour format string.
  - [OK] `TaskEditDialog.load_recurring_task_data(self)` - Load recurring task data into the form.
  - [OK] `TaskEditDialog.load_task_data(self)` - Load existing task data into the form.
  - [OK] `TaskEditDialog.on_hour_changed(self, hour_text)` - Handle hour selection change.
  - [OK] `TaskEditDialog.on_minute_changed(self, minute_text)` - Handle minute selection change.
  - [OK] `TaskEditDialog.on_no_due_date_toggled(self, checked)` - Handle No Due Date checkbox toggle.
  - [OK] `TaskEditDialog.on_recurring_pattern_changed(self, pattern_text)` - Handle recurring pattern selection change.
  - [OK] `TaskEditDialog.render_reminder_period_row(self, index, period)` - Render a single reminder period row.
  - [OK] `TaskEditDialog.render_reminder_periods(self)` - Render the reminder periods in the UI.
  - [OK] `TaskEditDialog.save_task(self)` - Save the task data.
  - [OK] `TaskEditDialog.set_due_time_from_24h(self, time)` - Set due time components from 24-hour time.
  - [OK] `TaskEditDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `TaskEditDialog.setup_due_time_components(self)` - Setup the due time input components.
  - [OK] `TaskEditDialog.setup_recurring_task_components(self)` - Setup the recurring task input components.
  - [OK] `TaskEditDialog.setup_ui(self)` - Setup the UI components.
  - [OK] `TaskEditDialog.validate_form(self)` - Validate the form data.

#### `ui/dialogs/task_management_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [MISSING] `get_statistics(self)` - No description
- [MISSING] `on_enable_task_management_toggled(self, checked)` - No description
- [OK] `save_task_settings(self)` - Save the task settings.
**Classes:**
- [MISSING] `TaskManagementDialog` - No description
  - [OK] `TaskManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - [MISSING] `TaskManagementDialog.get_statistics(self)` - No description
  - [MISSING] `TaskManagementDialog.on_enable_task_management_toggled(self, checked)` - No description
  - [OK] `TaskManagementDialog.save_task_settings(self)` - Save the task settings.

#### `ui/dialogs/user_analytics_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the user analytics dialog.
- [OK] `configure_tab_visibility(self)` - Configure which tabs are visible based on available data.
- [OK] `detect_available_data_types(self)` - Detect what types of data are available and configure tab visibility.
- [OK] `load_analytics_data(self)` - Load and display analytics data.
- [OK] `load_habits_data(self)` - Load and display habit analytics.
- [OK] `load_mood_data(self)` - Load and display mood analytics.
- [OK] `load_overview_data(self)` - Load and display overview analytics.
- [OK] `load_quantitative_data(self)` - Load and display quantitative analytics.
- [OK] `load_sleep_data(self)` - Load and display sleep analytics.
- [OK] `on_time_period_changed(self, index)` - Handle time period selection change.
- [OK] `open_user_analytics_dialog(parent, user_id)` - Open the user analytics dialog.
- [OK] `refresh_analytics(self)` - Refresh all analytics data.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_initial_state(self)` - Setup initial dialog state.
- [OK] `show_error_state(self, error_message)` - Show error state with message.
- [OK] `show_loading_state(self)` - Show loading state while data is being processed.
**Classes:**
- [OK] `UserAnalyticsDialog` - Dialog for displaying comprehensive user analytics.
  - [OK] `UserAnalyticsDialog.__init__(self, parent, user_id)` - Initialize the user analytics dialog.
  - [OK] `UserAnalyticsDialog.configure_tab_visibility(self)` - Configure which tabs are visible based on available data.
  - [OK] `UserAnalyticsDialog.detect_available_data_types(self)` - Detect what types of data are available and configure tab visibility.
  - [OK] `UserAnalyticsDialog.load_analytics_data(self)` - Load and display analytics data.
  - [OK] `UserAnalyticsDialog.load_habits_data(self)` - Load and display habit analytics.
  - [OK] `UserAnalyticsDialog.load_mood_data(self)` - Load and display mood analytics.
  - [OK] `UserAnalyticsDialog.load_overview_data(self)` - Load and display overview analytics.
  - [OK] `UserAnalyticsDialog.load_quantitative_data(self)` - Load and display quantitative analytics.
  - [OK] `UserAnalyticsDialog.load_sleep_data(self)` - Load and display sleep analytics.
  - [OK] `UserAnalyticsDialog.on_time_period_changed(self, index)` - Handle time period selection change.
  - [OK] `UserAnalyticsDialog.refresh_analytics(self)` - Refresh all analytics data.
  - [OK] `UserAnalyticsDialog.setup_connections(self)` - Setup signal connections.
  - [OK] `UserAnalyticsDialog.setup_initial_state(self)` - Setup initial dialog state.
  - [OK] `UserAnalyticsDialog.show_error_state(self, error_message)` - Show error state with message.
  - [OK] `UserAnalyticsDialog.show_loading_state(self)` - Show loading state while data is being processed.

#### `ui/dialogs/user_profile_dialog.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, on_save, existing_data)` - Initialize the object.
- [OK] `add_custom_field(self, parent_layout, field_type, value, checked)` - Add a custom field row with checkbox, entry, and delete button.
- [OK] `add_loved_one_widget(self, parent_layout, loved_one_data)` - Add a loved one widget to the layout.

Args:
    parent_layout: Parent layout to add the widget to
    loved_one_data: Optional existing loved one data
- [OK] `cancel(self)` - Cancel the personalization dialog.
- [OK] `center_dialog(self)` - Center the dialog on the parent window.
- [OK] `collect_custom_field_data(self, group_box)` - Collect data from custom field checkboxes and entries.

Args:
    group_box: Group box containing custom fields

Returns:
    list: List of selected values from checkboxes and custom entries
- [OK] `collect_loved_ones_data(self)` - Collect data from loved ones widgets.

Returns:
    list: List of loved ones data dictionaries
- [OK] `create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text)` - Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete).
- [OK] `create_goals_section(self)` - Create the goals section of the personalization dialog.

Returns:
    QGroupBox: Goals section group box
- [OK] `create_health_section(self)` - Create the health section of the personalization dialog.

Returns:
    QGroupBox: Health section group box
- [OK] `create_interests_section(self)` - Create the interests section of the personalization dialog.

Returns:
    QGroupBox: Interests section group box
- [OK] `create_loved_ones_section(self)` - Create the loved ones section of the personalization dialog.

Returns:
    QGroupBox: Loved ones section group box
- [OK] `create_notes_section(self)` - Create the notes section of the personalization dialog.

Returns:
    QGroupBox: Notes section group box
- [OK] `keyPressEvent(self, event)` - Handle key press events for the dialog.
- [OK] `open_personalization_dialog(parent, user_id, on_save, existing_data)` - Open the personalization dialog.

Args:
    parent: Parent widget
    user_id: User ID for the personalization data
    on_save: Optional callback function to call when saving
    existing_data: Optional existing personalization data

Returns:
    QDialog.DialogCode: Dialog result code
- [OK] `remove_custom_field(self, field_frame)` - Remove a custom field from the layout.
- [OK] `remove_loved_one_widget(self, frame)` - Remove a loved one widget from the layout.

Args:
    frame: Frame widget to remove
- [OK] `save_personalization(self)` - Save the personalization data.
- [OK] `setup_ui(self)` - Setup the user interface.
- [OK] `title_case(s)` - Convert snake_case or lowercase to Title Case.

Args:
    s: String to convert to title case

Returns:
    str: String converted to title case
**Classes:**
- [OK] `UserProfileDialog` - PySide6-based personalization dialog for user account creation and management.
  - [OK] `UserProfileDialog.__init__(self, parent, user_id, on_save, existing_data)` - Initialize the object.
  - [OK] `UserProfileDialog.add_custom_field(self, parent_layout, field_type, value, checked)` - Add a custom field row with checkbox, entry, and delete button.
  - [OK] `UserProfileDialog.add_loved_one_widget(self, parent_layout, loved_one_data)` - Add a loved one widget to the layout.

Args:
    parent_layout: Parent layout to add the widget to
    loved_one_data: Optional existing loved one data
  - [OK] `UserProfileDialog.cancel(self)` - Cancel the personalization dialog.
  - [OK] `UserProfileDialog.center_dialog(self)` - Center the dialog on the parent window.
  - [OK] `UserProfileDialog.collect_custom_field_data(self, group_box)` - Collect data from custom field checkboxes and entries.

Args:
    group_box: Group box containing custom fields

Returns:
    list: List of selected values from checkboxes and custom entries
  - [OK] `UserProfileDialog.collect_loved_ones_data(self)` - Collect data from loved ones widgets.

Returns:
    list: List of loved ones data dictionaries
  - [OK] `UserProfileDialog.create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text)` - Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete).
  - [OK] `UserProfileDialog.create_goals_section(self)` - Create the goals section of the personalization dialog.

Returns:
    QGroupBox: Goals section group box
  - [OK] `UserProfileDialog.create_health_section(self)` - Create the health section of the personalization dialog.

Returns:
    QGroupBox: Health section group box
  - [OK] `UserProfileDialog.create_interests_section(self)` - Create the interests section of the personalization dialog.

Returns:
    QGroupBox: Interests section group box
  - [OK] `UserProfileDialog.create_loved_ones_section(self)` - Create the loved ones section of the personalization dialog.

Returns:
    QGroupBox: Loved ones section group box
  - [OK] `UserProfileDialog.create_notes_section(self)` - Create the notes section of the personalization dialog.

Returns:
    QGroupBox: Notes section group box
  - [OK] `UserProfileDialog.keyPressEvent(self, event)` - Handle key press events for the dialog.
  - [OK] `UserProfileDialog.remove_custom_field(self, field_frame)` - Remove a custom field from the layout.
  - [OK] `UserProfileDialog.remove_loved_one_widget(self, frame)` - Remove a loved one widget from the layout.

Args:
    frame: Frame widget to remove
  - [OK] `UserProfileDialog.save_personalization(self)` - Save the personalization data.
  - [OK] `UserProfileDialog.setup_ui(self)` - Setup the user interface.

#### `ui/generate_ui_files.py`
**Functions:**
- [OK] `generate_all_ui_files()` - Generate all UI files in the project.
- [OK] `generate_ui_file(ui_file_path, output_path)` - Generate a UI Python file from a .ui file with proper headers.

Args:
    ui_file_path: Path to the .ui file
    output_path: Path for the generated Python file

Returns:
    bool: True if successful, False otherwise
- [OK] `main()` - Main function.

#### `ui/ui_app_qt.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the object.
- [OK] `__init__(self)` - Initialize the object.
- [OK] `_check_discord_status(self)` - Check if Discord channel is actually running and connected

IMPORTANT: This will NEVER return True if the service is stopped.
Channels cannot run without the service, so we check service status first.

Checks for:
1. Initialization messages ("Discord bot initialized successfully" or "Discord connection status changed to: connected")
2. Recent activity (messages received/sent, "Discord healthy" status)
3. Falls back to assuming running if service is running and Discord is configured
- [OK] `_check_email_status(self)` - Check if Email channel is actually initialized and running

IMPORTANT: This will NEVER return True if the service is stopped.
Channels cannot run without the service, so we check service status first.
- [OK] `_check_ngrok_status(self)` - Check if ngrok tunnel is running and return PID
- [OK] `_send_test_message__get_selected_category(self)` - Get and validate the selected category from the dropdown.
- [OK] `_send_test_message__validate_service_running(self)` - Validate that the service is running.
- [OK] `_send_test_message__validate_user_selection(self)` - Validate that a user is selected.
- [MISSING] `cleanup_old_requests()` - No description
- [OK] `closeEvent(self, event)` - Handle window close event
- [OK] `connect_signals(self)` - Connect UI signals to slots
- [OK] `create_new_user(self)` - Create new user with validation.

Returns:
    None: Always returns None
- [OK] `disable_content_management(self)` - Disable content management buttons
- [OK] `edit_user_messages(self)` - Edit user messages with validation.

Returns:
    None: Always returns None
- [OK] `edit_user_schedules(self)` - Edit user schedules with validation.

Returns:
    None: Always returns None
- [OK] `enable_content_management(self)` - Enable content management buttons
- [OK] `force_clean_cache(self)` - Force cache cleanup with validation.

Returns:
    None: Always returns None
- [OK] `initialize_ui(self)` - Initialize the UI state
- [OK] `is_service_running(self)` - Check if the MHM service is running with validation.

Returns:
    tuple: (is_running, process_info)
- [OK] `load_theme(self)` - Load and apply the QSS theme from the styles directory
- [OK] `load_ui(self)` - Load the UI from the .ui file
- [OK] `load_user_categories(self, user_id)` - Load categories for the selected user
- [OK] `main()` - Main entry point for the Qt-based UI application
- [OK] `manage_categories(self)` - Manage categories with validation.

Returns:
    None: Always returns None
- [OK] `manage_checkins(self)` - Manage checkins with validation.

Returns:
    None: Always returns None
- [OK] `manage_communication_settings(self)` - Manage communication settings with validation.

Returns:
    None: Always returns None
- [OK] `manage_personalization(self)` - Manage personalization with validation.

Returns:
    None: Always returns None
- [OK] `manage_task_crud(self)` - Manage task CRUD with validation.

Returns:
    None: Always returns None
- [OK] `manage_tasks(self)` - Manage tasks with validation.

Returns:
    None: Always returns None
- [OK] `manage_user_analytics(self)` - Manage user analytics with validation.

Returns:
    None: Always returns None
- [OK] `on_category_selected(self, category)` - Handle category selection
- [MISSING] `on_save(data)` - No description
- [OK] `on_schedule_save()` - Callback when schedule is saved.
- [OK] `on_user_selected(self, user_display)` - Handle user selection with validation.

Returns:
    None: Always returns None
- [OK] `open_message_editor(self, parent_dialog, category)` - Open message editor with validation.

Returns:
    None: Always returns None
- [OK] `open_process_watcher(self)` - Open process watcher with validation.

Returns:
    None: Always returns None
- [OK] `open_schedule_editor(self, parent_dialog, category)` - Open schedule editor with validation.

Returns:
    None: Always returns None
- [OK] `refresh_user_list(self)` - Refresh the user list with validation.

Returns:
    None: Always returns None
- [OK] `restart_service(self)` - Restart the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `restart_service(self)` - Restart the MHM service
- [OK] `run_category_scheduler(self)` - Run scheduler for the selected user and category
- [OK] `run_full_scheduler(self)` - Run the full scheduler for all users
- [OK] `run_user_scheduler(self)` - Run scheduler for the selected user
- [OK] `send_actual_test_message(self, category)` - Send actual test message with validation.

Returns:
    None: Always returns None
- [OK] `send_checkin_prompt(self)` - Send a check-in prompt to the selected user for testing purposes.

Returns:
    None: Always returns None
- [OK] `send_task_reminder(self)` - Send a task reminder to the selected user for testing purposes.

Returns:
    None: Always returns None
- [OK] `send_test_message(self)` - Send test message with validation.

Returns:
    None: Always returns None
- [OK] `show_configuration_help(self, parent_window)` - Show help for fixing configuration issues.
- [OK] `shutdown_ui_components(self)` - Shutdown UI components with validation.

Returns:
    None: Always returns None
- [OK] `start_service(self)` - Start the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `start_service(self)` - Start the MHM service
- [OK] `stop_service(self)` - Stop the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
- [OK] `stop_service(self)` - Stop the MHM service
- [OK] `system_health_check(self)` - Perform a basic system health check.
- [OK] `toggle_logging_verbosity(self)` - Toggle logging verbosity and update menu.
- [OK] `update_service_status(self)` - Update the service status display
- [OK] `update_user_index_on_startup(self)` - Automatically update the user index when the admin panel starts
- [OK] `validate_configuration(self)` - Validate configuration with validation.

Returns:
    None: Always returns None
- [OK] `validate_configuration_before_start(self)` - Validate configuration before attempting to start the service.
- [OK] `view_all_users_summary(self)` - Show a summary of all users in the system.
- [OK] `view_cache_status(self)` - View cache status with validation.

Returns:
    None: Always returns None
- [OK] `view_log_file(self)` - View log file with validation.

Returns:
    None: Always returns None
**Classes:**
- [OK] `MHMManagerUI` - Main MHM Management UI using PySide6
  - [OK] `MHMManagerUI.__init__(self)` - Initialize the object.
  - [OK] `MHMManagerUI._check_discord_status(self)` - Check if Discord channel is actually running and connected

IMPORTANT: This will NEVER return True if the service is stopped.
Channels cannot run without the service, so we check service status first.

Checks for:
1. Initialization messages ("Discord bot initialized successfully" or "Discord connection status changed to: connected")
2. Recent activity (messages received/sent, "Discord healthy" status)
3. Falls back to assuming running if service is running and Discord is configured
  - [OK] `MHMManagerUI._check_email_status(self)` - Check if Email channel is actually initialized and running

IMPORTANT: This will NEVER return True if the service is stopped.
Channels cannot run without the service, so we check service status first.
  - [OK] `MHMManagerUI._check_ngrok_status(self)` - Check if ngrok tunnel is running and return PID
  - [OK] `MHMManagerUI._send_test_message__get_selected_category(self)` - Get and validate the selected category from the dropdown.
  - [OK] `MHMManagerUI._send_test_message__validate_service_running(self)` - Validate that the service is running.
  - [OK] `MHMManagerUI._send_test_message__validate_user_selection(self)` - Validate that a user is selected.
  - [OK] `MHMManagerUI.closeEvent(self, event)` - Handle window close event
  - [OK] `MHMManagerUI.connect_signals(self)` - Connect UI signals to slots
  - [OK] `MHMManagerUI.create_new_user(self)` - Create new user with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.disable_content_management(self)` - Disable content management buttons
  - [OK] `MHMManagerUI.edit_user_messages(self)` - Edit user messages with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.edit_user_schedules(self)` - Edit user schedules with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.enable_content_management(self)` - Enable content management buttons
  - [OK] `MHMManagerUI.force_clean_cache(self)` - Force cache cleanup with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.initialize_ui(self)` - Initialize the UI state
  - [OK] `MHMManagerUI.load_theme(self)` - Load and apply the QSS theme from the styles directory
  - [OK] `MHMManagerUI.load_ui(self)` - Load the UI from the .ui file
  - [OK] `MHMManagerUI.load_user_categories(self, user_id)` - Load categories for the selected user
  - [OK] `MHMManagerUI.manage_categories(self)` - Manage categories with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_checkins(self)` - Manage checkins with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_communication_settings(self)` - Manage communication settings with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_personalization(self)` - Manage personalization with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_task_crud(self)` - Manage task CRUD with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_tasks(self)` - Manage tasks with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.manage_user_analytics(self)` - Manage user analytics with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.on_category_selected(self, category)` - Handle category selection
  - [OK] `MHMManagerUI.on_user_selected(self, user_display)` - Handle user selection with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.open_message_editor(self, parent_dialog, category)` - Open message editor with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.open_process_watcher(self)` - Open process watcher with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.open_schedule_editor(self, parent_dialog, category)` - Open schedule editor with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.refresh_user_list(self)` - Refresh the user list with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.restart_service(self)` - Restart the MHM service
  - [OK] `MHMManagerUI.run_category_scheduler(self)` - Run scheduler for the selected user and category
  - [OK] `MHMManagerUI.run_full_scheduler(self)` - Run the full scheduler for all users
  - [OK] `MHMManagerUI.run_user_scheduler(self)` - Run scheduler for the selected user
  - [OK] `MHMManagerUI.send_actual_test_message(self, category)` - Send actual test message with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.send_checkin_prompt(self)` - Send a check-in prompt to the selected user for testing purposes.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.send_task_reminder(self)` - Send a task reminder to the selected user for testing purposes.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.send_test_message(self)` - Send test message with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.show_configuration_help(self, parent_window)` - Show help for fixing configuration issues.
  - [OK] `MHMManagerUI.shutdown_ui_components(self)` - Shutdown UI components with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.start_service(self)` - Start the MHM service
  - [OK] `MHMManagerUI.stop_service(self)` - Stop the MHM service
  - [OK] `MHMManagerUI.system_health_check(self)` - Perform a basic system health check.
  - [OK] `MHMManagerUI.toggle_logging_verbosity(self)` - Toggle logging verbosity and update menu.
  - [OK] `MHMManagerUI.update_service_status(self)` - Update the service status display
  - [OK] `MHMManagerUI.update_user_index_on_startup(self)` - Automatically update the user index when the admin panel starts
  - [OK] `MHMManagerUI.validate_configuration(self)` - Validate configuration with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.view_all_users_summary(self)` - Show a summary of all users in the system.
  - [OK] `MHMManagerUI.view_cache_status(self)` - View cache status with validation.

Returns:
    None: Always returns None
  - [OK] `MHMManagerUI.view_log_file(self)` - View log file with validation.

Returns:
    None: Always returns None
- [OK] `ServiceManager` - Manages the MHM backend service process
  - [OK] `ServiceManager.__init__(self)` - Initialize the object.
  - [OK] `ServiceManager.is_service_running(self)` - Check if the MHM service is running with validation.

Returns:
    tuple: (is_running, process_info)
  - [OK] `ServiceManager.restart_service(self)` - Restart the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `ServiceManager.start_service(self)` - Start the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `ServiceManager.stop_service(self)` - Stop the MHM backend service with validation.

Returns:
    bool: True if successful, False if failed
  - [OK] `ServiceManager.validate_configuration_before_start(self)` - Validate configuration before attempting to start the service.

#### `ui/widgets/__init__.py`

#### `ui/widgets/category_selection_widget.py`
**Functions:**
- [OK] `__init__(self, parent)` - Initialize the object.
- [MISSING] `get_selected_categories(self)` - No description
- [MISSING] `set_selected_categories(self, categories)` - No description
**Classes:**
- [MISSING] `CategorySelectionWidget` - No description
  - [OK] `CategorySelectionWidget.__init__(self, parent)` - Initialize the object.
  - [MISSING] `CategorySelectionWidget.get_selected_categories(self)` - No description
  - [MISSING] `CategorySelectionWidget.set_selected_categories(self, categories)` - No description

#### `ui/widgets/channel_selection_widget.py`
**Functions:**
- [OK] `__init__(self, parent)` - Initialize the ChannelSelectionWidget.

Sets up the UI for channel selection with Discord and Email options,
along with timezone selection. Populates timezone options and sets default
timezone to America/Regina.

Args:
    parent: Parent widget (optional)
- [OK] `get_all_contact_info(self)` - Get all contact info fields from the widget.
- [MISSING] `get_selected_channel(self)` - No description
- [OK] `get_timezone(self)` - Get the selected timezone.
- [OK] `populate_timezones(self)` - Populate the timezone combo box with options.
- [MISSING] `set_contact_info(self, email, discord_id, timezone)` - No description
- [MISSING] `set_selected_channel(self, channel, value)` - No description
- [OK] `set_timezone(self, timezone)` - Set the timezone.
**Classes:**
- [MISSING] `ChannelSelectionWidget` - No description
  - [OK] `ChannelSelectionWidget.__init__(self, parent)` - Initialize the ChannelSelectionWidget.

Sets up the UI for channel selection with Discord and Email options,
along with timezone selection. Populates timezone options and sets default
timezone to America/Regina.

Args:
    parent: Parent widget (optional)
  - [OK] `ChannelSelectionWidget.get_all_contact_info(self)` - Get all contact info fields from the widget.
  - [MISSING] `ChannelSelectionWidget.get_selected_channel(self)` - No description
  - [OK] `ChannelSelectionWidget.get_timezone(self)` - Get the selected timezone.
  - [OK] `ChannelSelectionWidget.populate_timezones(self)` - Populate the timezone combo box with options.
  - [MISSING] `ChannelSelectionWidget.set_contact_info(self, email, discord_id, timezone)` - No description
  - [MISSING] `ChannelSelectionWidget.set_selected_channel(self, channel, value)` - No description
  - [OK] `ChannelSelectionWidget.set_timezone(self, timezone)` - Set the timezone.

#### `ui/widgets/checkin_settings_widget.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [OK] `_clear_category_groups(self)` - Remove all category group boxes.
- [OK] `_clear_dynamic_question_checkboxes(self)` - Remove all dynamically created question checkboxes.
- [OK] `_delete_custom_question(self, question_key)` - Delete a custom question.
- [OK] `_edit_custom_question(self, question_key)` - Edit an existing custom question.
- [OK] `_on_always_toggled(self, question_key, checked)` - Handle always checkbox toggle - ensure sometimes is unchecked if always is checked.
- [OK] `_on_max_changed(self, value)` - Handle maximum questions value change - adjust min if needed.
- [OK] `_on_min_changed(self, value)` - Handle minimum questions value change - adjust max if needed.
- [OK] `_on_sometimes_toggled(self, question_key, checked)` - Handle sometimes checkbox toggle - ensure always is unchecked if sometimes is checked.
- [OK] `_refresh_question_display(self)` - Refresh the question display from current in-memory state.

Similar to tag_widget.refresh_tag_list() - updates display without reloading from preferences.
- [OK] `_setup_question_count_controls(self)` - Add min/max question count controls below the questions list.
- [OK] `_show_question_dialog(self, question_key, question_def)` - Show dialog for adding or editing a custom question.

Args:
    question_key: If provided, edit existing question; otherwise create new
    question_def: Existing question definition (for editing)
- [OK] `_validate_question_counts(self, skip_min_adjust)` - Validate min/max question counts based on enabled questions.

Args:
    skip_min_adjust: If True, don't adjust min value even if it's below min_required.
                     Used when max is reduced below min to allow min to match max.
- [OK] `add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
- [OK] `add_new_question(self)` - Add a new check-in question.
- [OK] `connect_question_checkboxes(self)` - Connect all question checkboxes to track changes.
- [OK] `find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
- [OK] `get_checkin_settings(self)` - Get the current check-in settings.
- [OK] `get_default_question_state(self, question_key)` - Get default enabled state for a question.
- [OK] `guard(_row_widget)` - Return True to abort removal (e.g. when only one period remains).
- [OK] `load_existing_data(self)` - Load existing check-in data.
- [MISSING] `number_from_widget(w)` - No description
- [OK] `on_question_toggled(self, checked)` - Handle question checkbox toggle.
- [MISSING] `on_template_selected(index)` - No description
- [OK] `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- [OK] `set_checkin_settings(self, settings)` - Set the check-in settings.
- [OK] `set_question_checkboxes(self, questions)` - Set question checkboxes based on saved preferences.

Groups questions by category and creates Always/Sometimes checkboxes for each.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Re-validate question counts to ensure
spinboxes have correct ranges when the dialog is shown.

Args:
    event: The show event object
- [OK] `undo_last_question_delete(self)` - Undo the last question deletion.
- [OK] `undo_last_time_period_delete(self)` - Undo the last time period deletion.
**Classes:**
- [OK] `CheckinSettingsWidget` - Widget for check-in settings configuration.
  - [OK] `CheckinSettingsWidget.__init__(self, parent, user_id)` - Initialize the object.
  - [OK] `CheckinSettingsWidget._clear_category_groups(self)` - Remove all category group boxes.
  - [OK] `CheckinSettingsWidget._clear_dynamic_question_checkboxes(self)` - Remove all dynamically created question checkboxes.
  - [OK] `CheckinSettingsWidget._delete_custom_question(self, question_key)` - Delete a custom question.
  - [OK] `CheckinSettingsWidget._edit_custom_question(self, question_key)` - Edit an existing custom question.
  - [OK] `CheckinSettingsWidget._on_always_toggled(self, question_key, checked)` - Handle always checkbox toggle - ensure sometimes is unchecked if always is checked.
  - [OK] `CheckinSettingsWidget._on_max_changed(self, value)` - Handle maximum questions value change - adjust min if needed.
  - [OK] `CheckinSettingsWidget._on_min_changed(self, value)` - Handle minimum questions value change - adjust max if needed.
  - [OK] `CheckinSettingsWidget._on_sometimes_toggled(self, question_key, checked)` - Handle sometimes checkbox toggle - ensure always is unchecked if sometimes is checked.
  - [OK] `CheckinSettingsWidget._refresh_question_display(self)` - Refresh the question display from current in-memory state.

Similar to tag_widget.refresh_tag_list() - updates display without reloading from preferences.
  - [OK] `CheckinSettingsWidget._setup_question_count_controls(self)` - Add min/max question count controls below the questions list.
  - [OK] `CheckinSettingsWidget._show_question_dialog(self, question_key, question_def)` - Show dialog for adding or editing a custom question.

Args:
    question_key: If provided, edit existing question; otherwise create new
    question_def: Existing question definition (for editing)
  - [OK] `CheckinSettingsWidget._validate_question_counts(self, skip_min_adjust)` - Validate min/max question counts based on enabled questions.

Args:
    skip_min_adjust: If True, don't adjust min value even if it's below min_required.
                     Used when max is reduced below min to allow min to match max.
  - [OK] `CheckinSettingsWidget.add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
  - [OK] `CheckinSettingsWidget.add_new_question(self)` - Add a new check-in question.
  - [OK] `CheckinSettingsWidget.connect_question_checkboxes(self)` - Connect all question checkboxes to track changes.
  - [OK] `CheckinSettingsWidget.find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
  - [OK] `CheckinSettingsWidget.get_checkin_settings(self)` - Get the current check-in settings.
  - [OK] `CheckinSettingsWidget.get_default_question_state(self, question_key)` - Get default enabled state for a question.
  - [OK] `CheckinSettingsWidget.load_existing_data(self)` - Load existing check-in data.
  - [OK] `CheckinSettingsWidget.on_question_toggled(self, checked)` - Handle question checkbox toggle.
  - [OK] `CheckinSettingsWidget.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - [OK] `CheckinSettingsWidget.set_checkin_settings(self, settings)` - Set the check-in settings.
  - [OK] `CheckinSettingsWidget.set_question_checkboxes(self, questions)` - Set question checkboxes based on saved preferences.

Groups questions by category and creates Always/Sometimes checkboxes for each.
  - [OK] `CheckinSettingsWidget.setup_connections(self)` - Setup signal connections.
  - [OK] `CheckinSettingsWidget.showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Re-validate question counts to ensure
spinboxes have correct ranges when the dialog is shown.

Args:
    event: The show event object
  - [OK] `CheckinSettingsWidget.undo_last_question_delete(self)` - Undo the last question deletion.
  - [OK] `CheckinSettingsWidget.undo_last_time_period_delete(self)` - Undo the last time period deletion.

#### `ui/widgets/dynamic_list_container.py`
**Functions:**
- [OK] `__init__(self, parent, field_key)` - Initialize the object.
- [OK] `__post_init__(self)` - Post-initialization setup.
- [MISSING] `_add_blank_row(self)` - No description
- [MISSING] `_deduplicate_values(self, trigger_row, skip_warning)` - No description
- [MISSING] `_ensure_single_blank_row(self, current_blank)` - No description
- [MISSING] `_first_blank_index(self)` - No description
- [MISSING] `_on_preset_toggled(self, row)` - No description
- [MISSING] `_on_row_deleted(self, row)` - No description
- [MISSING] `_on_row_edited(self, row)` - No description
- [MISSING] `get_values(self)` - No description
- [MISSING] `set_values(self, selected)` - No description
**Classes:**
- [OK] `DynamicListContainer` - Manages a vertical list of DynamicListField rows.
  - [OK] `DynamicListContainer.__init__(self, parent, field_key)` - Initialize the object.
  - [OK] `DynamicListContainer.__post_init__(self)` - Post-initialization setup.
  - [MISSING] `DynamicListContainer._add_blank_row(self)` - No description
  - [MISSING] `DynamicListContainer._deduplicate_values(self, trigger_row, skip_warning)` - No description
  - [MISSING] `DynamicListContainer._ensure_single_blank_row(self, current_blank)` - No description
  - [MISSING] `DynamicListContainer._first_blank_index(self)` - No description
  - [MISSING] `DynamicListContainer._on_preset_toggled(self, row)` - No description
  - [MISSING] `DynamicListContainer._on_row_deleted(self, row)` - No description
  - [MISSING] `DynamicListContainer._on_row_edited(self, row)` - No description
  - [MISSING] `DynamicListContainer.get_values(self)` - No description
  - [MISSING] `DynamicListContainer.set_values(self, selected)` - No description

#### `ui/widgets/dynamic_list_field.py`
**Functions:**
- [OK] `__init__(self, parent, preset_label, editable, checked)` - Initialize the object.
- [MISSING] `_on_delete(self)` - No description
- [MISSING] `get_text(self)` - No description
- [MISSING] `is_blank(self)` - No description
- [MISSING] `is_checked(self)` - No description
- [OK] `on_checkbox_toggled(self, checked)` - Called when user clicks the checkbox.

Args:
    checked: The new checked state from the toggled signal (ignored, we read from widget)
- [OK] `on_editing_finished(self)` - Notify parent container that text editing has finished (for duplicate validation).
- [OK] `on_text_changed(self, text)` - Called when user types in the text field.

Args:
    text: The new text from the textEdited signal (ignored, we read from widget)
- [MISSING] `set_checked(self, state)` - No description
- [MISSING] `set_text(self, text)` - No description
**Classes:**
- [OK] `DynamicListField` - Single row consisting of checkbox + editable text + delete button.
  - [OK] `DynamicListField.__init__(self, parent, preset_label, editable, checked)` - Initialize the object.
  - [MISSING] `DynamicListField._on_delete(self)` - No description
  - [MISSING] `DynamicListField.get_text(self)` - No description
  - [MISSING] `DynamicListField.is_blank(self)` - No description
  - [MISSING] `DynamicListField.is_checked(self)` - No description
  - [OK] `DynamicListField.on_checkbox_toggled(self, checked)` - Called when user clicks the checkbox.

Args:
    checked: The new checked state from the toggled signal (ignored, we read from widget)
  - [OK] `DynamicListField.on_editing_finished(self)` - Notify parent container that text editing has finished (for duplicate validation).
  - [OK] `DynamicListField.on_text_changed(self, text)` - Called when user types in the text field.

Args:
    text: The new text from the textEdited signal (ignored, we read from widget)
  - [MISSING] `DynamicListField.set_checked(self, state)` - No description
  - [MISSING] `DynamicListField.set_text(self, text)` - No description

#### `ui/widgets/period_row_widget.py`
**Functions:**
- [OK] `__init__(self, parent, period_name, period_data)` - Initialize the object.
- [OK] `_get_day_checkboxes(self)` - Get list of day checkboxes.
- [OK] `_set_read_only__all_period_read_only(self)` - Set ALL period to read-only with all days selected.
- [OK] `_set_read_only__apply_read_only_styling(self)` - Apply read-only visual styling.
- [OK] `_set_read_only__checkbox_states(self, read_only)` - Set checkbox states based on read-only mode and period type.
- [OK] `_set_read_only__clear_read_only_styling(self)` - Clear read-only visual styling.
- [OK] `_set_read_only__delete_button_visibility(self, read_only)` - Set delete button visibility based on read-only state.
- [OK] `_set_read_only__force_style_updates(self)` - Force style updates for all checkboxes.
- [OK] `_set_read_only__normal_checkbox_states(self, read_only)` - Set normal checkbox states for non-ALL periods.
- [OK] `_set_read_only__time_inputs(self, read_only)` - Set time input widgets to read-only mode.
- [OK] `_set_read_only__visual_styling(self, read_only)` - Apply visual styling for read-only state.
- [OK] `get_period_data(self)` - Get the current period data from the widget.
- [OK] `get_period_name(self)` - Get the current period name.
- [OK] `get_selected_days(self)` - Get the currently selected days.
- [OK] `is_valid(self)` - Check if the period data is valid.
- [OK] `load_days(self, days)` - Load day selections.
- [OK] `load_period_data(self)` - Load period data into the widget.
- [OK] `on_individual_day_toggled(self, checked)` - Handle individual day checkbox toggle.
- [OK] `on_select_all_days_toggled(self, checked)` - Handle 'Select All Days' checkbox toggle.
- [OK] `request_delete(self)` - Request deletion of this period row.
- [OK] `set_period_name(self, name)` - Set the period name.
- [OK] `set_read_only(self, read_only)` - Set the widget to read-only mode.
- [OK] `setup_functionality(self)` - Setup the widget functionality and connect signals.
**Classes:**
- [OK] `PeriodRowWidget` - Reusable widget for editing time periods with days selection.
  - [OK] `PeriodRowWidget.__init__(self, parent, period_name, period_data)` - Initialize the object.
  - [OK] `PeriodRowWidget._get_day_checkboxes(self)` - Get list of day checkboxes.
  - [OK] `PeriodRowWidget._set_read_only__all_period_read_only(self)` - Set ALL period to read-only with all days selected.
  - [OK] `PeriodRowWidget._set_read_only__apply_read_only_styling(self)` - Apply read-only visual styling.
  - [OK] `PeriodRowWidget._set_read_only__checkbox_states(self, read_only)` - Set checkbox states based on read-only mode and period type.
  - [OK] `PeriodRowWidget._set_read_only__clear_read_only_styling(self)` - Clear read-only visual styling.
  - [OK] `PeriodRowWidget._set_read_only__delete_button_visibility(self, read_only)` - Set delete button visibility based on read-only state.
  - [OK] `PeriodRowWidget._set_read_only__force_style_updates(self)` - Force style updates for all checkboxes.
  - [OK] `PeriodRowWidget._set_read_only__normal_checkbox_states(self, read_only)` - Set normal checkbox states for non-ALL periods.
  - [OK] `PeriodRowWidget._set_read_only__time_inputs(self, read_only)` - Set time input widgets to read-only mode.
  - [OK] `PeriodRowWidget._set_read_only__visual_styling(self, read_only)` - Apply visual styling for read-only state.
  - [OK] `PeriodRowWidget.get_period_data(self)` - Get the current period data from the widget.
  - [OK] `PeriodRowWidget.get_period_name(self)` - Get the current period name.
  - [OK] `PeriodRowWidget.get_selected_days(self)` - Get the currently selected days.
  - [OK] `PeriodRowWidget.is_valid(self)` - Check if the period data is valid.
  - [OK] `PeriodRowWidget.load_days(self, days)` - Load day selections.
  - [OK] `PeriodRowWidget.load_period_data(self)` - Load period data into the widget.
  - [OK] `PeriodRowWidget.on_individual_day_toggled(self, checked)` - Handle individual day checkbox toggle.
  - [OK] `PeriodRowWidget.on_select_all_days_toggled(self, checked)` - Handle 'Select All Days' checkbox toggle.
  - [OK] `PeriodRowWidget.request_delete(self)` - Request deletion of this period row.
  - [OK] `PeriodRowWidget.set_period_name(self, name)` - Set the period name.
  - [OK] `PeriodRowWidget.set_read_only(self, read_only)` - Set the widget to read-only mode.
  - [OK] `PeriodRowWidget.setup_functionality(self)` - Setup the widget functionality and connect signals.

#### `ui/widgets/tag_widget.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, mode, selected_tags, title)` - Initialize the tag widget.

Args:
    parent: Parent widget
    user_id: User ID for loading/saving tags
    mode: "management" for full CRUD operations, "selection" for checkbox selection
    selected_tags: List of currently selected tags (for selection mode)
    title: Title for the group box
- [OK] `add_tag(self)` - Add a new tag.
- [OK] `delete_tag(self)` - Delete the selected tag (management mode only).
- [OK] `edit_tag(self)` - Edit the selected tag (management mode only).
- [OK] `get_available_tags(self)` - Get the current list of available tags.
- [OK] `get_selected_tags(self)` - Get the currently selected tags (selection mode only).
- [OK] `load_tags(self)` - Load the user's tags.
- [OK] `on_tag_selection_changed(self, item)` - Handle when a tag checkbox is changed (selection mode only).
- [OK] `refresh_tag_list(self)` - Refresh the tag list display.
- [OK] `refresh_tags(self)` - Refresh the tags in the tag widget.
- [OK] `set_selected_tags(self, tags)` - Set the selected tags (selection mode only).
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `setup_ui(self)` - Setup the UI components based on mode.
- [OK] `undo_last_tag_delete(self)` - Undo the last tag deletion (account creation mode only).
- [OK] `update_button_states(self)` - Update button enabled states based on selection (management mode only).
**Classes:**
- [OK] `TagWidget` - Flexible tag widget that can work in management or selection mode.
  - [OK] `TagWidget.__init__(self, parent, user_id, mode, selected_tags, title)` - Initialize the tag widget.

Args:
    parent: Parent widget
    user_id: User ID for loading/saving tags
    mode: "management" for full CRUD operations, "selection" for checkbox selection
    selected_tags: List of currently selected tags (for selection mode)
    title: Title for the group box
  - [OK] `TagWidget.add_tag(self)` - Add a new tag.
  - [OK] `TagWidget.delete_tag(self)` - Delete the selected tag (management mode only).
  - [OK] `TagWidget.edit_tag(self)` - Edit the selected tag (management mode only).
  - [OK] `TagWidget.get_available_tags(self)` - Get the current list of available tags.
  - [OK] `TagWidget.get_selected_tags(self)` - Get the currently selected tags (selection mode only).
  - [OK] `TagWidget.load_tags(self)` - Load the user's tags.
  - [OK] `TagWidget.on_tag_selection_changed(self, item)` - Handle when a tag checkbox is changed (selection mode only).
  - [OK] `TagWidget.refresh_tag_list(self)` - Refresh the tag list display.
  - [OK] `TagWidget.refresh_tags(self)` - Refresh the tags in the tag widget.
  - [OK] `TagWidget.set_selected_tags(self, tags)` - Set the selected tags (selection mode only).
  - [OK] `TagWidget.setup_connections(self)` - Setup signal connections.
  - [OK] `TagWidget.setup_ui(self)` - Setup the UI components based on mode.
  - [OK] `TagWidget.undo_last_tag_delete(self)` - Undo the last tag deletion (account creation mode only).
  - [OK] `TagWidget.update_button_states(self)` - Update button enabled states based on selection (management mode only).

#### `ui/widgets/task_settings_widget.py`
**Functions:**
- [OK] `__init__(self, parent, user_id)` - Initialize the object.
- [OK] `add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
- [OK] `find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
- [OK] `get_available_tags(self)` - Get the current list of available tags from the tag widget.
- [OK] `get_recurring_task_settings(self)` - Get the current recurring task settings.
- [OK] `get_statistics(self)` - Get real task statistics for the user.
- [OK] `get_task_settings(self)` - Get the current task settings.
- [MISSING] `load_existing_data(self)` - No description
- [OK] `load_recurring_task_settings(self)` - Load recurring task settings from user preferences.
- [MISSING] `number_from_widget(w)` - No description
- [OK] `refresh_tags(self)` - Refresh the tags in the tag widget.
- [OK] `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- [OK] `save_recurring_task_settings(self)` - Save recurring task settings to user preferences.
- [OK] `set_recurring_task_settings(self, settings)` - Set the recurring task settings.
- [OK] `set_task_settings(self, settings)` - Set the task settings.
- [OK] `setup_connections(self)` - Setup signal connections.
- [OK] `showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
- [OK] `undo_last_period_delete(self)` - Undo the last time period deletion.
- [OK] `undo_last_tag_delete(self)` - Undo the last tag deletion (account creation mode only).
**Classes:**
- [MISSING] `TaskSettingsWidget` - No description
  - [OK] `TaskSettingsWidget.__init__(self, parent, user_id)` - Initialize the object.
  - [OK] `TaskSettingsWidget.add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
  - [OK] `TaskSettingsWidget.find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
  - [OK] `TaskSettingsWidget.get_available_tags(self)` - Get the current list of available tags from the tag widget.
  - [OK] `TaskSettingsWidget.get_recurring_task_settings(self)` - Get the current recurring task settings.
  - [OK] `TaskSettingsWidget.get_statistics(self)` - Get real task statistics for the user.
  - [OK] `TaskSettingsWidget.get_task_settings(self)` - Get the current task settings.
  - [MISSING] `TaskSettingsWidget.load_existing_data(self)` - No description
  - [OK] `TaskSettingsWidget.load_recurring_task_settings(self)` - Load recurring task settings from user preferences.
  - [OK] `TaskSettingsWidget.refresh_tags(self)` - Refresh the tags in the tag widget.
  - [OK] `TaskSettingsWidget.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - [OK] `TaskSettingsWidget.save_recurring_task_settings(self)` - Save recurring task settings to user preferences.
  - [OK] `TaskSettingsWidget.set_recurring_task_settings(self, settings)` - Set the recurring task settings.
  - [OK] `TaskSettingsWidget.set_task_settings(self, settings)` - Set the task settings.
  - [OK] `TaskSettingsWidget.setup_connections(self)` - Setup signal connections.
  - [OK] `TaskSettingsWidget.showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
  - [OK] `TaskSettingsWidget.undo_last_period_delete(self)` - Undo the last time period deletion.
  - [OK] `TaskSettingsWidget.undo_last_tag_delete(self)` - Undo the last tag deletion (account creation mode only).

#### `ui/widgets/user_profile_settings_widget.py`
**Functions:**
- [OK] `__init__(self, parent, user_id, existing_data)` - Initialize the object.
- [OK] `_get_personalization_data__ensure_required_fields(self, data)` - Ensure all required fields exist in the data structure.
- [OK] `_get_personalization_data__extract_basic_fields(self, data)` - Extract basic text fields from the UI.
- [OK] `_get_personalization_data__extract_date_of_birth(self, data)` - Extract date of birth from calendar widget with proper validation.
- [OK] `_get_personalization_data__extract_dynamic_containers(self, data)` - Extract data from all dynamic list containers.
- [OK] `_get_personalization_data__extract_gender_identity(self, data)` - Extract gender identity from checkboxes and custom input.
- [OK] `_get_personalization_data__extract_loved_ones(self, data)` - Extract loved ones data from text field with structured parsing.
- [OK] `_get_personalization_data__extract_notes(self, data)` - Extract notes for AI from text field.
- [OK] `get_personalization_data(self)` - Get all personalization data from the form, preserving existing data structure.
- [OK] `get_settings(self)` - Get the current user profile settings.
- [OK] `load_existing_data(self)` - Load existing personalization data into the form.
- [OK] `populate_timezones(self)` - Populate the timezone combo box with options and enable selection.
- [OK] `set_checkbox_group(self, group_name, values)` - Set checkboxes for a specific group based on values.
- [OK] `set_settings(self, settings)` - Set the user profile settings.
**Classes:**
- [OK] `UserProfileSettingsWidget` - Widget for user profile settings configuration.
  - [OK] `UserProfileSettingsWidget.__init__(self, parent, user_id, existing_data)` - Initialize the object.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__ensure_required_fields(self, data)` - Ensure all required fields exist in the data structure.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_basic_fields(self, data)` - Extract basic text fields from the UI.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_date_of_birth(self, data)` - Extract date of birth from calendar widget with proper validation.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_dynamic_containers(self, data)` - Extract data from all dynamic list containers.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_gender_identity(self, data)` - Extract gender identity from checkboxes and custom input.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_loved_ones(self, data)` - Extract loved ones data from text field with structured parsing.
  - [OK] `UserProfileSettingsWidget._get_personalization_data__extract_notes(self, data)` - Extract notes for AI from text field.
  - [OK] `UserProfileSettingsWidget.get_personalization_data(self)` - Get all personalization data from the form, preserving existing data structure.
  - [OK] `UserProfileSettingsWidget.get_settings(self)` - Get the current user profile settings.
  - [OK] `UserProfileSettingsWidget.load_existing_data(self)` - Load existing personalization data into the form.
  - [OK] `UserProfileSettingsWidget.populate_timezones(self)` - Populate the timezone combo box with options and enable selection.
  - [OK] `UserProfileSettingsWidget.set_checkbox_group(self, group_name, values)` - Set checkboxes for a specific group based on values.
  - [OK] `UserProfileSettingsWidget.set_settings(self, settings)` - Set the user profile settings.

### `user/` - User Data and Context

#### `user/__init__.py`

#### `user/context_manager.py`
**Functions:**
- [OK] `__init__(self)` - Initialize the UserContextManager.

Sets up conversation history storage for tracking user interactions.
- [OK] `_get_conversation_history(self, user_id)` - Get recent conversation history with this user.
- [OK] `_get_conversation_insights(self, user_id)` - Get insights from recent chat interactions.
- [OK] `_get_minimal_context(self, user_id)` - Fallback minimal context if full context generation fails.

Args:
    user_id: The user's ID (can be None for anonymous context)

Returns:
    dict: Minimal context with basic information
- [OK] `_get_mood_trends(self, user_id)` - Analyze recent mood and energy trends.
- [OK] `_get_recent_activity(self, user_id)` - Get recent user activity and responses.
- [OK] `_get_user_preferences(self, user_id)` - Get user preferences using new structure.
- [OK] `_get_user_profile(self, user_id)` - Get basic user profile information using existing user infrastructure.
- [OK] `add_conversation_exchange(self, user_id, user_message, ai_response)` - Add a conversation exchange to history.

Args:
    user_id: The user's ID
    user_message: The user's message
    ai_response: The AI's response
- [OK] `format_context_for_ai(self, context)` - Format user context into a concise string for AI prompt.

Args:
    context: User context dictionary

Returns:
    str: Formatted context string for AI consumption
- [OK] `get_ai_context(self, user_id, include_conversation_history)` - Get comprehensive user context for AI conversation.

Args:
    user_id: The user's ID
    include_conversation_history: Whether to include recent conversation history

Returns:
    Dict containing all relevant user context for AI processing
- [OK] `get_current_user_context(self, include_conversation_history)` - Get context for the currently logged-in user using the existing UserContext singleton.

Args:
    include_conversation_history: Whether to include recent conversation history

Returns:
    Dict containing all relevant user context for current user
**Classes:**
- [OK] `UserContextManager` - Manages rich user context for AI conversations.
  - [OK] `UserContextManager.__init__(self)` - Initialize the UserContextManager.

Sets up conversation history storage for tracking user interactions.
  - [OK] `UserContextManager._get_conversation_history(self, user_id)` - Get recent conversation history with this user.
  - [OK] `UserContextManager._get_conversation_insights(self, user_id)` - Get insights from recent chat interactions.
  - [OK] `UserContextManager._get_minimal_context(self, user_id)` - Fallback minimal context if full context generation fails.

Args:
    user_id: The user's ID (can be None for anonymous context)

Returns:
    dict: Minimal context with basic information
  - [OK] `UserContextManager._get_mood_trends(self, user_id)` - Analyze recent mood and energy trends.
  - [OK] `UserContextManager._get_recent_activity(self, user_id)` - Get recent user activity and responses.
  - [OK] `UserContextManager._get_user_preferences(self, user_id)` - Get user preferences using new structure.
  - [OK] `UserContextManager._get_user_profile(self, user_id)` - Get basic user profile information using existing user infrastructure.
  - [OK] `UserContextManager.add_conversation_exchange(self, user_id, user_message, ai_response)` - Add a conversation exchange to history.

Args:
    user_id: The user's ID
    user_message: The user's message
    ai_response: The AI's response
  - [OK] `UserContextManager.format_context_for_ai(self, context)` - Format user context into a concise string for AI prompt.

Args:
    context: User context dictionary

Returns:
    str: Formatted context string for AI consumption
  - [OK] `UserContextManager.get_ai_context(self, user_id, include_conversation_history)` - Get comprehensive user context for AI conversation.

Args:
    user_id: The user's ID
    include_conversation_history: Whether to include recent conversation history

Returns:
    Dict containing all relevant user context for AI processing
  - [OK] `UserContextManager.get_current_user_context(self, include_conversation_history)` - Get context for the currently logged-in user using the existing UserContext singleton.

Args:
    include_conversation_history: Whether to include recent conversation history

Returns:
    Dict containing all relevant user context for current user

#### `user/user_context.py`
**Functions:**
- [OK] `__new__(cls)` - Create a new instance.
- [OK] `get_instance_context(self)` - Get basic user context from the current UserContext instance.

Returns:
    dict: Dictionary containing basic user context information
- [OK] `get_internal_username(self)` - Retrieves the internal_username from the user_data dictionary.

Returns:
    str: The current internal username, or None if not set.
- [OK] `get_preferred_name(self)` - Retrieves the preferred_name from the user_data dictionary.

Returns:
    str: The current preferred name, or None if not set.
- [OK] `get_user_id(self)` - Retrieves the user_id from the user_data dictionary.

Returns:
    str: The current user ID, or None if not set.
- [OK] `load_user_data(self, user_id)` - Loads user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be loaded.
- [OK] `save_user_data(self, user_id)` - Saves user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be saved.
- [OK] `set_internal_username(self, internal_username)` - Sets the internal_username in the user_data dictionary.

Args:
    internal_username (str): The internal username to be set.
- [OK] `set_preferred_name(self, preferred_name)` - Sets the preferred_name in the user_data dictionary.

Args:
    preferred_name (str): The preferred name to be set.
- [OK] `set_user_id(self, user_id)` - Sets the user_id in the user_data dictionary.

Args:
    user_id (str): The user ID to be set.
**Classes:**
- [MISSING] `UserContext` - No description
  - [OK] `UserContext.__new__(cls)` - Create a new instance.
  - [OK] `UserContext.get_instance_context(self)` - Get basic user context from the current UserContext instance.

Returns:
    dict: Dictionary containing basic user context information
  - [OK] `UserContext.get_internal_username(self)` - Retrieves the internal_username from the user_data dictionary.

Returns:
    str: The current internal username, or None if not set.
  - [OK] `UserContext.get_preferred_name(self)` - Retrieves the preferred_name from the user_data dictionary.

Returns:
    str: The current preferred name, or None if not set.
  - [OK] `UserContext.get_user_id(self)` - Retrieves the user_id from the user_data dictionary.

Returns:
    str: The current user ID, or None if not set.
  - [OK] `UserContext.load_user_data(self, user_id)` - Loads user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be loaded.
  - [OK] `UserContext.save_user_data(self, user_id)` - Saves user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be saved.
  - [OK] `UserContext.set_internal_username(self, internal_username)` - Sets the internal_username in the user_data dictionary.

Args:
    internal_username (str): The internal username to be set.
  - [OK] `UserContext.set_preferred_name(self, preferred_name)` - Sets the preferred_name in the user_data dictionary.

Args:
    preferred_name (str): The preferred name to be set.
  - [OK] `UserContext.set_user_id(self, user_id)` - Sets the user_id in the user_data dictionary.

Args:
    user_id (str): The user ID to be set.

#### `user/user_preferences.py`
**Functions:**
- [OK] `__init__(self, user_id)` - Initialize UserPreferences for a specific user.

Args:
    user_id: The user's unique identifier
- [OK] `get_all_preferences(self)` - Get all preferences.
- [OK] `get_preference(self, key)` - Get a preference value.
- [OK] `is_schedule_period_active(user_id, category, period_name)` - Wrapper for :func:`core.schedule_management.is_schedule_period_active`.
- [OK] `load_preferences(self)` - Load user preferences using the new user management functions.
- [OK] `remove_preference(self, key)` - Remove a preference.
- [OK] `save_preferences(self)` - Save user preferences using the new user management functions.
- [OK] `set_preference(self, key, value)` - Set a preference and save it.
- [OK] `set_schedule_period_active(user_id, category, period_name, is_active)` - Wrapper for :func:`core.schedule_management.set_schedule_period_active`.
- [OK] `update_preference(self, key, value)` - Update a preference (alias for set_preference for consistency).
**Classes:**
- [OK] `UserPreferences` - Manages user preferences and settings.

Provides methods for loading, saving, and managing user preferences
including schedule period settings and general user preferences.

Note: This class is available but currently unused in the codebase. Most code
accesses preferences directly via get_user_data() and update_user_preferences().
This class is useful for workflows that need to make multiple preference changes
or track preference state during operations.

Example usage:
    prefs = UserPreferences(user_id)
    prefs.set_preference('theme', 'dark')
    prefs.set_preference('notifications', True)
    # Both changes saved automatically
  - [OK] `UserPreferences.__init__(self, user_id)` - Initialize UserPreferences for a specific user.

Args:
    user_id: The user's unique identifier
  - [OK] `UserPreferences.get_all_preferences(self)` - Get all preferences.
  - [OK] `UserPreferences.get_preference(self, key)` - Get a preference value.
  - [OK] `UserPreferences.is_schedule_period_active(user_id, category, period_name)` - Wrapper for :func:`core.schedule_management.is_schedule_period_active`.
  - [OK] `UserPreferences.load_preferences(self)` - Load user preferences using the new user management functions.
  - [OK] `UserPreferences.remove_preference(self, key)` - Remove a preference.
  - [OK] `UserPreferences.save_preferences(self)` - Save user preferences using the new user management functions.
  - [OK] `UserPreferences.set_preference(self, key, value)` - Set a preference and save it.
  - [OK] `UserPreferences.set_schedule_period_active(user_id, category, period_name, is_active)` - Wrapper for :func:`core.schedule_management.set_schedule_period_active`.
  - [OK] `UserPreferences.update_preference(self, key, value)` - Update a preference (alias for set_preference for consistency).

