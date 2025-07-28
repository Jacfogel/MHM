# Function Registry - MHM Project

> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete registry of all functions and classes in the MHM codebase  
> **Status**: **ACTIVE** - Auto-generated from codebase analysis with template enhancement  
> **Last Updated**: 2025-07-28 03:27:17

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](TODO.md) for current documentation priorities**

## 📋 **Overview**

### **Function Documentation Coverage: 93.8% ⚠️ NEEDS ATTENTION**
- **Files Scanned**: 123
- **Functions Found**: 1194
- **Methods Found**: 774
- **Classes Found**: 119
- **Total Items**: 1968
- **Functions Documented**: 1112
- **Methods Documented**: 734
- **Classes Documented**: 87
- **Total Documented**: 1846
- **Template-Generated**: 21
- **Last Updated**: 2025-07-28

**Status**: ⚠️ **GOOD** - Most functions documented, some gaps remain

**Template Enhancement**: This registry now includes automatic template generation for:
- **Auto-generated Qt functions** (qtTrId, setupUi, retranslateUi)
- **Test functions** (with scenario-based descriptions)
- **Special Python methods** (__init__, __new__, __post_init__, etc.)
- **Constructor methods** and **main functions**

**Note**: This registry is automatically generated from the actual codebase. Functions without docstrings are marked as needing documentation. Template-generated documentation is applied to improve coverage.

## 🔍 **Function Categories**

### **Core System Functions** (295)
Core system utilities, configuration, error handling, and data management functions.

### **Communication Functions** (155)
Bot implementations, channel management, and communication utilities.

### **User Interface Functions** (260)
UI dialogs, widgets, and user interaction functions.

### **User Management Functions** (24)
User context, preferences, and data management functions.

### **Task Management Functions** (13)
Task management and scheduling functions.

### **Test Functions** (333)
Test functions and testing utilities.

## 📁 **Module Organization**

### `bot/` - Communication Channel Implementations

#### `bot/ai_chatbot.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the object
- ✅ `__init__(self, max_size, ttl)` - Initialize the object.
- ✅ `__init__(self)` - Initialize the object.
- ✅ `__new__(cls)` - Create a new instance.
- ✅ `_call_lm_studio_api(self, messages, max_tokens, temperature, timeout)` - Make an API call to LM Studio using OpenAI-compatible format.
- ✅ `_cleanup_lru(self)` - Remove least recently used items.
- ✅ `_create_command_parsing_prompt(self, user_prompt)` - Create a prompt instructing the model to return strict JSON.
- ✅ `_create_comprehensive_context_prompt(self, user_id, user_prompt)` - Create a comprehensive context prompt with all user data for LM Studio.
- ✅ `_detect_mode(self, user_prompt)` - Detect whether the prompt is a command or a chat query.
- ✅ `_detect_resource_constraints(self)` - Detect if system is resource-constrained.
- ✅ `_generate_key(self, prompt, user_id)` - Generate cache key from prompt and optional user context.
- ✅ `_get_adaptive_timeout(self, base_timeout)` - Get adaptive timeout based on system resources.
- ✅ `_get_contextual_fallback(self, user_prompt, user_id)` - Provide contextually aware fallback responses based on user data and prompt analysis.
Now actually analyzes user's check-in data for meaningful responses.
- ✅ `_get_fallback_personalized_message(self, user_id)` - Provide fallback personalized messages when AI model is not available.
- ✅ `_get_fallback_response(self, user_prompt)` - Legacy fallback method for backwards compatibility.
- ✅ `_load_custom_prompt(self)` - Load the custom system prompt from file.
- ✅ `_optimize_prompt(self, user_prompt, context)` - Create optimized messages array for LM Studio API.
- ✅ `_test_lm_studio_connection(self)` - Test connection to LM Studio server.
- ✅ `generate_contextual_response(self, user_id, user_prompt, timeout)` - Generate a context-aware response using comprehensive user data.
Integrates with existing UserContext and UserPreferences systems.
- ✅ `generate_personalized_message(self, user_id, timeout)` - Generate a personalized message by examining the user's recent responses
(daily check-in data). Uses longer timeout since this is not real-time.
- ✅ `generate_quick_response(self, user_prompt, user_id)` - Generate a quick response for real-time chat (Discord, etc.).
Uses shorter timeout optimized for responsiveness.
- ✅ `generate_response(self, user_prompt, timeout, user_id, mode)` - Generate a basic AI response from user_prompt, using LM Studio API.
Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
- ✅ `get(self, prompt, user_id)` - Get cached response if available and not expired.
- ✅ `get_ai_chatbot()` - Return the shared AIChatBot instance.
- ✅ `get_ai_status(self)` - Get detailed status information about the AI system.
- ✅ `get_system_prompt(self, prompt_type)` - Get the appropriate system prompt for the given type.

Args:
    prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support')
    
Returns:
    The system prompt string
- ✅ `is_ai_available(self)` - Check if the AI model is available and functional.
- ✅ `reload_prompt(self)` - Reload the custom prompt from file (useful for development).
- ✅ `reload_system_prompt(self)` - Reload the system prompt from file (useful for development and testing).
- ✅ `set(self, prompt, response, user_id)` - Cache a response.
- ✅ `test_system_prompt_integration(self)` - Test the system prompt integration and return status information.
**Classes:**
- ✅ `AIChatBotSingleton` - A Singleton container for LM Studio API client (replacing GPT4All).
  - ✅ `AIChatBotSingleton.__init__(self)` - Initialize the object.
  - ✅ `AIChatBotSingleton.__new__(cls)` - Create a new instance.
  - ✅ `AIChatBotSingleton._call_lm_studio_api(self, messages, max_tokens, temperature, timeout)` - Make an API call to LM Studio using OpenAI-compatible format.
  - ✅ `AIChatBotSingleton._create_command_parsing_prompt(self, user_prompt)` - Create a prompt instructing the model to return strict JSON.
  - ✅ `AIChatBotSingleton._create_comprehensive_context_prompt(self, user_id, user_prompt)` - Create a comprehensive context prompt with all user data for LM Studio.
  - ✅ `AIChatBotSingleton._detect_mode(self, user_prompt)` - Detect whether the prompt is a command or a chat query.
  - ✅ `AIChatBotSingleton._detect_resource_constraints(self)` - Detect if system is resource-constrained.
  - ✅ `AIChatBotSingleton._get_adaptive_timeout(self, base_timeout)` - Get adaptive timeout based on system resources.
  - ✅ `AIChatBotSingleton._get_contextual_fallback(self, user_prompt, user_id)` - Provide contextually aware fallback responses based on user data and prompt analysis.
Now actually analyzes user's check-in data for meaningful responses.
  - ✅ `AIChatBotSingleton._get_fallback_personalized_message(self, user_id)` - Provide fallback personalized messages when AI model is not available.
  - ✅ `AIChatBotSingleton._get_fallback_response(self, user_prompt)` - Legacy fallback method for backwards compatibility.
  - ✅ `AIChatBotSingleton._optimize_prompt(self, user_prompt, context)` - Create optimized messages array for LM Studio API.
  - ✅ `AIChatBotSingleton._test_lm_studio_connection(self)` - Test connection to LM Studio server.
  - ✅ `AIChatBotSingleton.generate_contextual_response(self, user_id, user_prompt, timeout)` - Generate a context-aware response using comprehensive user data.
Integrates with existing UserContext and UserPreferences systems.
  - ✅ `AIChatBotSingleton.generate_personalized_message(self, user_id, timeout)` - Generate a personalized message by examining the user's recent responses
(daily check-in data). Uses longer timeout since this is not real-time.
  - ✅ `AIChatBotSingleton.generate_quick_response(self, user_prompt, user_id)` - Generate a quick response for real-time chat (Discord, etc.).
Uses shorter timeout optimized for responsiveness.
  - ✅ `AIChatBotSingleton.generate_response(self, user_prompt, timeout, user_id, mode)` - Generate a basic AI response from user_prompt, using LM Studio API.
Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
  - ✅ `AIChatBotSingleton.get_ai_status(self)` - Get detailed status information about the AI system.
  - ✅ `AIChatBotSingleton.is_ai_available(self)` - Check if the AI model is available and functional.
  - ✅ `AIChatBotSingleton.reload_system_prompt(self)` - Reload the system prompt from file (useful for development and testing).
  - ✅ `AIChatBotSingleton.test_system_prompt_integration(self)` - Test the system prompt integration and return status information.
- ✅ `ResponseCache` - Simple in-memory cache for AI responses to avoid repeated calculations.
  - ✅ `ResponseCache.__init__(self, max_size, ttl)` - Initialize the object.
  - ✅ `ResponseCache._cleanup_lru(self)` - Remove least recently used items.
  - ✅ `ResponseCache._generate_key(self, prompt, user_id)` - Generate cache key from prompt and optional user context.
  - ✅ `ResponseCache.get(self, prompt, user_id)` - Get cached response if available and not expired.
  - ✅ `ResponseCache.set(self, prompt, response, user_id)` - Cache a response.
- ✅ `SystemPromptLoader` - Handles loading and managing the AI system prompt from the custom prompt file.
Provides fallback prompts if the custom file is not available.
  - ✅ `SystemPromptLoader.__init__(self)` - Initialize the object
  - ✅ `SystemPromptLoader._load_custom_prompt(self)` - Load the custom system prompt from file.
  - ✅ `SystemPromptLoader.get_system_prompt(self, prompt_type)` - Get the appropriate system prompt for the given type.

Args:
    prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support')
    
Returns:
    The system prompt string
  - ✅ `SystemPromptLoader.reload_prompt(self)` - Reload the custom prompt from file (useful for development).

#### `bot/base_channel.py`
**Functions:**
- ✅ `__init__(self, config)` - Initialize the object.
- ✅ `__post_init__(self)` - Post-initialization setup.
- ✅ `_set_status(self, status, error_message)` - Internal method to update status
- ✅ `channel_type(self)` - Return whether this channel is sync or async
- ✅ `get_error(self)` - Get last error message
- ✅ `get_status(self)` - Get current channel status
- ✅ `is_ready(self)` - Check if channel is ready to send/receive messages
**Classes:**
- ✅ `BaseChannel` - Abstract base class for all communication channels
  - ✅ `BaseChannel.__init__(self, config)` - Initialize the object.
  - ✅ `BaseChannel._set_status(self, status, error_message)` - Internal method to update status
  - ✅ `BaseChannel.channel_type(self)` - Return whether this channel is sync or async
  - ✅ `BaseChannel.get_error(self)` - Get last error message
  - ✅ `BaseChannel.get_status(self)` - Get current channel status
  - ✅ `BaseChannel.is_ready(self)` - Check if channel is ready to send/receive messages
- ✅ `ChannelConfig` - Configuration for communication channels
  - ✅ `ChannelConfig.__post_init__(self)` - Post-initialization setup.
- ❌ `ChannelStatus` - No description
- ❌ `ChannelType` - No description

#### `bot/channel_factory.py`
**Functions:**
- ✅ `create_channel(cls, name, config)` - Create a channel instance
- ✅ `get_available_channels(cls)` - Get list of available channel types
- ✅ `register_channel(cls, name, channel_class)` - Register a new channel type
**Classes:**
- ✅ `ChannelFactory` - Factory for creating communication channels
  - ✅ `ChannelFactory.create_channel(cls, name, config)` - Create a channel instance
  - ✅ `ChannelFactory.get_available_channels(cls)` - Get list of available channel types
  - ✅ `ChannelFactory.register_channel(cls, name, channel_class)` - Register a new channel type

#### `bot/channel_registry.py`
**Functions:**
- ✅ `register_all_channels()` - Register all available communication channels

#### `bot/communication_manager.py`
**Functions:**
- ✅ `__getattr__(self, name)` - Forward attribute access to the base channel for backward compatibility.

Args:
    name: The attribute name to access
    
Returns:
    The attribute value from the base channel
- ✅ `__init__(self)` - Initialize the object.
- ✅ `__init__(self, base_channel)` - Initialize the legacy channel wrapper.

Args:
    base_channel: The base channel to wrap
- ✅ `__new__(cls)` - Ensure that only one instance of the CommunicationManager exists (Singleton pattern).
- ✅ `_check_logging_health(self)` - Check if logging is still working and recover if needed.

Verifies that the logging system is functional and attempts to restart it if issues are detected.
- ✅ `_create_legacy_channel_access(self)` - Create legacy channel access for backward compatibility.

Creates wrapper objects that provide the old interface for existing code.
- ✅ `_create_task_reminder_message(self, task)` - Create a formatted task reminder message.
- ✅ `_get_default_channel_configs(self)` - Get default channel configurations
- ✅ `_get_recipient_for_service(self, user_id, messaging_service, preferences)` - Get the appropriate recipient ID for the messaging service
- ✅ `_handle_scheduled_checkin(self, user_id, messaging_service, recipient)` - Handle scheduled check-in messages based on user preferences and frequency.
- ✅ `_run_async_safely(self, coro)` - Run async function safely, handling existing event loops.

Args:
    coro: The coroutine to run
    
Returns:
    The result of the coroutine
- ✅ `_run_async_sync(self, coro)` - Run async function synchronously using our managed loop
- ✅ `_send_ai_generated_message(self, user_id, category, messaging_service, recipient)` - Send an AI-generated personalized message using contextual AI
- ✅ `_send_checkin_prompt(self, user_id, messaging_service, recipient)` - Send a check-in prompt message to start the daily check-in flow.
- ✅ `_send_predefined_message(self, user_id, category, messaging_service, recipient)` - Send a pre-defined message from the user's message library
- ✅ `_setup_event_loop(self)` - Set up a dedicated event loop for async operations
- ✅ `_should_send_checkin_prompt(self, user_id, checkin_prefs)` - Determine if it's time to send a check-in prompt based on user preferences.
This checks if enough time has passed since the last check-in.
- ✅ `_shutdown_sync(self)` - Synchronous shutdown method for all channels.

Stops all communication channels and cleans up resources.
- ✅ `channels(self)` - Backward compatibility property
- ✅ `channels(self, value)` - Backward compatibility setter
- ✅ `get_available_channels(self)` - Get list of available/initialized channels
- ✅ `handle_message_sending(self, user_id, category)` - Handle sending messages for a user and category with improved recipient resolution.
Now uses scheduled check-ins instead of random replacement.
- ✅ `handle_task_reminder(self, user_id, task_id)` - Handle sending task reminders for a user.
- ✅ `initialize_channels_from_config(self, channel_configs)` - Initialize channels from configuration
- ✅ `is_channel_ready(self, channel_name)` - Check if a specific channel is ready
- ✅ `is_initialized(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel is initialized
- ✅ `receive_messages(self)` - Legacy method - synchronous.

Returns:
    List of received messages
- ✅ `run_event_loop()` - Run the event loop in a separate thread for async operations.

This nested function is used to manage the event loop for async channel operations.
- ✅ `run_in_thread()` - Run the coroutine in a separate thread with its own event loop.

This nested function ensures async operations can run safely in a threaded environment.
- ✅ `send_message(self)` - Legacy method - synchronous.

Returns:
    The result of sending the message
- ✅ `send_message_sync(self, channel_name, recipient, message)` - Synchronous wrapper with logging health check
- ✅ `set_scheduler_manager(self, scheduler_manager)` - Set the scheduler manager for the communication manager.
- ✅ `start(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel started successfully
- ✅ `start_all(self)` - Legacy method - maintains synchronous interface
- ✅ `stop(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel stopped successfully
- ✅ `stop_all(self)` - Stop all communication channels
**Classes:**
- ✅ `BotInitializationError` - Custom exception for bot initialization failures.
- ✅ `CommunicationManager` - Manages all communication channels with improved modularity
  - ✅ `CommunicationManager.__init__(self)` - Initialize the object.
  - ✅ `CommunicationManager.__new__(cls)` - Ensure that only one instance of the CommunicationManager exists (Singleton pattern).
  - ✅ `CommunicationManager._check_logging_health(self)` - Check if logging is still working and recover if needed.

Verifies that the logging system is functional and attempts to restart it if issues are detected.
  - ✅ `CommunicationManager._create_legacy_channel_access(self)` - Create legacy channel access for backward compatibility.

Creates wrapper objects that provide the old interface for existing code.
  - ✅ `CommunicationManager._create_task_reminder_message(self, task)` - Create a formatted task reminder message.
  - ✅ `CommunicationManager._get_default_channel_configs(self)` - Get default channel configurations
  - ✅ `CommunicationManager._get_recipient_for_service(self, user_id, messaging_service, preferences)` - Get the appropriate recipient ID for the messaging service
  - ✅ `CommunicationManager._handle_scheduled_checkin(self, user_id, messaging_service, recipient)` - Handle scheduled check-in messages based on user preferences and frequency.
  - ✅ `CommunicationManager._run_async_sync(self, coro)` - Run async function synchronously using our managed loop
  - ✅ `CommunicationManager._send_ai_generated_message(self, user_id, category, messaging_service, recipient)` - Send an AI-generated personalized message using contextual AI
  - ✅ `CommunicationManager._send_checkin_prompt(self, user_id, messaging_service, recipient)` - Send a check-in prompt message to start the daily check-in flow.
  - ✅ `CommunicationManager._send_predefined_message(self, user_id, category, messaging_service, recipient)` - Send a pre-defined message from the user's message library
  - ✅ `CommunicationManager._setup_event_loop(self)` - Set up a dedicated event loop for async operations
  - ✅ `CommunicationManager._should_send_checkin_prompt(self, user_id, checkin_prefs)` - Determine if it's time to send a check-in prompt based on user preferences.
This checks if enough time has passed since the last check-in.
  - ✅ `CommunicationManager._shutdown_sync(self)` - Synchronous shutdown method for all channels.

Stops all communication channels and cleans up resources.
  - ✅ `CommunicationManager.channels(self)` - Backward compatibility property
  - ✅ `CommunicationManager.channels(self, value)` - Backward compatibility setter
  - ✅ `CommunicationManager.get_available_channels(self)` - Get list of available/initialized channels
  - ✅ `CommunicationManager.handle_message_sending(self, user_id, category)` - Handle sending messages for a user and category with improved recipient resolution.
Now uses scheduled check-ins instead of random replacement.
  - ✅ `CommunicationManager.handle_task_reminder(self, user_id, task_id)` - Handle sending task reminders for a user.
  - ✅ `CommunicationManager.initialize_channels_from_config(self, channel_configs)` - Initialize channels from configuration
  - ✅ `CommunicationManager.is_channel_ready(self, channel_name)` - Check if a specific channel is ready
  - ✅ `CommunicationManager.send_message_sync(self, channel_name, recipient, message)` - Synchronous wrapper with logging health check
  - ✅ `CommunicationManager.set_scheduler_manager(self, scheduler_manager)` - Set the scheduler manager for the communication manager.
  - ✅ `CommunicationManager.start_all(self)` - Legacy method - maintains synchronous interface
  - ✅ `CommunicationManager.stop_all(self)` - Stop all communication channels
- ✅ `LegacyChannelWrapper` - Provides complete backward compatibility for channel access
  - ✅ `LegacyChannelWrapper.__getattr__(self, name)` - Forward attribute access to the base channel for backward compatibility.

Args:
    name: The attribute name to access
    
Returns:
    The attribute value from the base channel
  - ✅ `LegacyChannelWrapper.__init__(self, base_channel)` - Initialize the legacy channel wrapper.

Args:
    base_channel: The base channel to wrap
  - ✅ `LegacyChannelWrapper._run_async_safely(self, coro)` - Run async function safely, handling existing event loops.

Args:
    coro: The coroutine to run
    
Returns:
    The result of the coroutine
  - ✅ `LegacyChannelWrapper.is_initialized(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel is initialized
  - ✅ `LegacyChannelWrapper.receive_messages(self)` - Legacy method - synchronous.

Returns:
    List of received messages
  - ✅ `LegacyChannelWrapper.send_message(self)` - Legacy method - synchronous.

Returns:
    The result of sending the message
  - ✅ `LegacyChannelWrapper.start(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel started successfully
  - ✅ `LegacyChannelWrapper.stop(self)` - Legacy method - synchronous.

Returns:
    bool: True if the channel stopped successfully
- ✅ `MessageSendError` - Custom exception for message sending failures.

#### `bot/conversation_manager.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the object.
- ✅ `_complete_checkin(self, user_id, user_state)` - Complete the check-in and provide personalized feedback
- ✅ `_generate_completion_message(self, user_id, data)` - Generate a personalized completion message based on responses
- ✅ `_get_next_question(self, user_id, user_state)` - Get the next question in the check-in flow
- ✅ `_get_personalized_welcome(self, user_id, question_count)` - Generate a personalized welcome message based on user history
- ✅ `_get_question_text(self, question_key, previous_data)` - Get appropriate question text based on question type and previous responses
- ✅ `_handle_daily_checkin(self, user_id, user_state, message_text)` - Enhanced daily check-in flow with dynamic questions and better validation
- ✅ `_start_dynamic_checkin(self, user_id)` - Start a dynamic check-in flow based on user preferences
- ✅ `_validate_response(self, question_key, response)` - Validate user response based on question type
- ✅ `handle_contextual_question(self, user_id, message_text)` - Handle a single contextual question without entering a conversation flow.
Perfect for one-off questions that benefit from user context.
- ✅ `handle_inbound_message(self, user_id, message_text)` - Primary entry point. Takes user's message and returns a (reply_text, completed).

Now defaults to contextual chat for all messages unless user is in a specific flow
or uses a special command.
- ✅ `start_daily_checkin(self, user_id)` - Public method to start a daily check-in flow for a user.
This is the proper way to initiate check-ins from external modules.
**Classes:**
- ❌ `ConversationManager` - No description
  - ✅ `ConversationManager.__init__(self)` - Initialize the object.
  - ✅ `ConversationManager._complete_checkin(self, user_id, user_state)` - Complete the check-in and provide personalized feedback
  - ✅ `ConversationManager._generate_completion_message(self, user_id, data)` - Generate a personalized completion message based on responses
  - ✅ `ConversationManager._get_next_question(self, user_id, user_state)` - Get the next question in the check-in flow
  - ✅ `ConversationManager._get_personalized_welcome(self, user_id, question_count)` - Generate a personalized welcome message based on user history
  - ✅ `ConversationManager._get_question_text(self, question_key, previous_data)` - Get appropriate question text based on question type and previous responses
  - ✅ `ConversationManager._handle_daily_checkin(self, user_id, user_state, message_text)` - Enhanced daily check-in flow with dynamic questions and better validation
  - ✅ `ConversationManager._start_dynamic_checkin(self, user_id)` - Start a dynamic check-in flow based on user preferences
  - ✅ `ConversationManager._validate_response(self, question_key, response)` - Validate user response based on question type
  - ✅ `ConversationManager.handle_contextual_question(self, user_id, message_text)` - Handle a single contextual question without entering a conversation flow.
Perfect for one-off questions that benefit from user context.
  - ✅ `ConversationManager.handle_inbound_message(self, user_id, message_text)` - Primary entry point. Takes user's message and returns a (reply_text, completed).

Now defaults to contextual chat for all messages unless user is in a specific flow
or uses a special command.
  - ✅ `ConversationManager.start_daily_checkin(self, user_id)` - Public method to start a daily check-in flow for a user.
This is the proper way to initiate check-ins from external modules.

#### `bot/discord_bot.py`
**Functions:**
- ✅ `__init__(self, config)` - Initialize the object.
- ✅ `_register_commands(self)` - Register Discord commands
- ✅ `_register_events(self)` - Register Discord event handlers
- ✅ `_run_bot_in_thread(self)` - Run Discord bot in completely isolated thread with its own event loop
- ✅ `channel_type(self)` - Get the channel type for Discord bot.

Returns:
    ChannelType.ASYNC: Discord bot operates asynchronously
- ✅ `is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the Discord bot is initialized and ready
- ✅ `start(self)` - Legacy start method.

Initializes the Discord bot if not already running.
- ✅ `stop(self)` - Legacy stop method - thread-safe.

Stops the Discord bot and cleans up resources.
**Classes:**
- ❌ `DiscordBot` - No description
  - ✅ `DiscordBot.__init__(self, config)` - Initialize the object.
  - ✅ `DiscordBot._register_commands(self)` - Register Discord commands
  - ✅ `DiscordBot._register_events(self)` - Register Discord event handlers
  - ✅ `DiscordBot._run_bot_in_thread(self)` - Run Discord bot in completely isolated thread with its own event loop
  - ✅ `DiscordBot.channel_type(self)` - Get the channel type for Discord bot.

Returns:
    ChannelType.ASYNC: Discord bot operates asynchronously
  - ✅ `DiscordBot.is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the Discord bot is initialized and ready
  - ✅ `DiscordBot.start(self)` - Legacy start method.

Initializes the Discord bot if not already running.
  - ✅ `DiscordBot.stop(self)` - Legacy stop method - thread-safe.

Stops the Discord bot and cleans up resources.

#### `bot/email_bot.py`
**Functions:**
- ✅ `__init__(self, config)` - Initialize the EmailBot with configuration.

Args:
    config: Channel configuration object. If None, creates default config
           with email-specific settings (max_retries=3, retry_delay=1.0,
           backoff_multiplier=2.0)
- ✅ `_receive_emails_sync(self)` - Receive emails synchronously
- ✅ `_send_email_sync(self, recipient, message, kwargs)` - Send email synchronously
- ✅ `_test_imap_connection(self)` - Test IMAP connection synchronously
- ✅ `_test_smtp_connection(self)` - Test SMTP connection synchronously
- ✅ `channel_type(self)` - Get the channel type for email bot.

Returns:
    ChannelType.SYNC: Email operations are synchronous
- ✅ `is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the email bot is initialized and ready
- ✅ `start(self)` - Legacy start method.

Initializes the email bot using the legacy interface.
- ✅ `stop(self)` - Legacy stop method.

Shuts down the email bot using the legacy interface.
**Classes:**
- ❌ `EmailBot` - No description
  - ✅ `EmailBot.__init__(self, config)` - Initialize the EmailBot with configuration.

Args:
    config: Channel configuration object. If None, creates default config
           with email-specific settings (max_retries=3, retry_delay=1.0,
           backoff_multiplier=2.0)
  - ✅ `EmailBot._receive_emails_sync(self)` - Receive emails synchronously
  - ✅ `EmailBot._send_email_sync(self, recipient, message, kwargs)` - Send email synchronously
  - ✅ `EmailBot._test_imap_connection(self)` - Test IMAP connection synchronously
  - ✅ `EmailBot._test_smtp_connection(self)` - Test SMTP connection synchronously
  - ✅ `EmailBot.channel_type(self)` - Get the channel type for email bot.

Returns:
    ChannelType.SYNC: Email operations are synchronous
  - ✅ `EmailBot.is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the email bot is initialized and ready
  - ✅ `EmailBot.start(self)` - Legacy start method.

Initializes the email bot using the legacy interface.
  - ✅ `EmailBot.stop(self)` - Legacy stop method.

Shuts down the email bot using the legacy interface.
- ✅ `EmailBotError` - Custom exception for email bot-related errors.

#### `bot/telegram_bot.py`
**Functions:**
- ✅ `__init__(self, config)` - Initialize the object.
- ❌ `add_message_command(self, update, context)` - No description
- ✅ `add_message_conv_handler(self)` - Create a conversation handler for adding new messages.

Returns:
    ConversationHandler: Configured conversation handler for message addition flow
- ✅ `add_new_period(self, update, context)` - Handle adding a new time period to the schedule.

Args:
    update: Telegram update object
    context: Callback context
    
Returns:
    int: Next conversation state
- ❌ `cancel(self, update, context)` - No description
- ✅ `channel_type(self)` - Get the channel type for Telegram bot.

Returns:
    ChannelType.ASYNC: Telegram bot operates asynchronously
- ✅ `daily_checkin_conv_handler(self)` - Create a conversation handler for daily check-in flow.

Returns:
    ConversationHandler: Configured conversation handler for daily check-in flow
- ✅ `days_selected(self, update, context)` - Handle days selection
- ✅ `edit_schedule_period(self, update, context)` - Edit schedule period
- ❌ `ensure_user_exists(self, update)` - No description
- ✅ `get_base_days_keyboard(self)` - Create a keyboard with days of the week for user selection.

Returns:
    InlineKeyboardMarkup: Keyboard with days of the week and submit button
- ✅ `get_user_categories(self, user_id)` - Get user's message categories.
- ✅ `get_user_categories_for_telegram(self, user_id)` - Get user's message categories for Telegram bot.
- ✅ `handle_category_selection(self, update, context)` - Handle category selection
- ✅ `handle_period_selection(self, update, context)` - Handle period selection
- ✅ `handle_schedule_category_selection(self, update, context)` - Handle schedule category selection
- ✅ `handle_user_command(self, update, context)` - Handle /user command to show user information.
- ✅ `is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the Telegram bot is initialized and ready
- ✅ `message_received(self, update, context)` - Handle received message text
- ✅ `prompt_category_selection(self, update, context, action, prompt_message, is_message)` - Prompt user to select a category
- ❌ `prompt_for_days(self, update, context)` - No description
- ✅ `prompt_for_message(self, update, context, category)` - Prompt user to enter a message
- ❌ `prompt_for_time_periods(self, update, context)` - No description
- ✅ `run_polling(self)` - Run Telegram polling safely in a separate thread with an event loop.
- ✅ `run_telegram_bot_in_background()` - Run the Telegram bot in the background.

Creates and starts a Telegram bot instance for background operation.
- ✅ `save_new_message(self, update, context)` - Save a new message with selected days and time periods.

Args:
    update: Telegram update object
    context: Callback context containing message data
- ✅ `schedule_conv_handler(self)` - Create a conversation handler for schedule management.

Returns:
    ConversationHandler: Configured conversation handler for schedule editing flow
- ✅ `scream_command(self, update, context)` - Handle the /scream command.

Toggles screaming mode for the bot's responses.

Args:
    update: Telegram update object
    context: Callback context
- ❌ `show_schedule(self, update, context, category)` - No description
- ✅ `start(self)` - Legacy start method - calls the new async initialize.

Initializes the Telegram bot using the legacy interface.
- ✅ `stop(self)` - Legacy stop method - calls the new async shutdown.

Shuts down the Telegram bot using the legacy interface.
- ✅ `time_periods_selected(self, update, context)` - Handle time periods selection
- ✅ `update_time_periods_keyboard(self, update, context, selected)` - Update the time periods keyboard to reflect current selections.

Args:
    update: Telegram update object
    context: Callback context
    selected: List of currently selected time periods
- ✅ `view_edit_schedule_command(self, update, context)` - View/edit schedule command
- ✅ `whisper_command(self, update, context)` - Handle the /whisper command.

Toggles whispering mode for the bot's responses.

Args:
    update: Telegram update object
    context: Callback context
**Classes:**
- ❌ `TelegramBot` - No description
  - ✅ `TelegramBot.__init__(self, config)` - Initialize the object.
  - ❌ `TelegramBot.add_message_command(self, update, context)` - No description
  - ✅ `TelegramBot.add_message_conv_handler(self)` - Create a conversation handler for adding new messages.

Returns:
    ConversationHandler: Configured conversation handler for message addition flow
  - ✅ `TelegramBot.add_new_period(self, update, context)` - Handle adding a new time period to the schedule.

Args:
    update: Telegram update object
    context: Callback context
    
Returns:
    int: Next conversation state
  - ❌ `TelegramBot.cancel(self, update, context)` - No description
  - ✅ `TelegramBot.channel_type(self)` - Get the channel type for Telegram bot.

Returns:
    ChannelType.ASYNC: Telegram bot operates asynchronously
  - ✅ `TelegramBot.daily_checkin_conv_handler(self)` - Create a conversation handler for daily check-in flow.

Returns:
    ConversationHandler: Configured conversation handler for daily check-in flow
  - ✅ `TelegramBot.days_selected(self, update, context)` - Handle days selection
  - ✅ `TelegramBot.edit_schedule_period(self, update, context)` - Edit schedule period
  - ❌ `TelegramBot.ensure_user_exists(self, update)` - No description
  - ✅ `TelegramBot.get_base_days_keyboard(self)` - Create a keyboard with days of the week for user selection.

Returns:
    InlineKeyboardMarkup: Keyboard with days of the week and submit button
  - ✅ `TelegramBot.get_user_categories(self, user_id)` - Get user's message categories.
  - ✅ `TelegramBot.get_user_categories_for_telegram(self, user_id)` - Get user's message categories for Telegram bot.
  - ✅ `TelegramBot.handle_category_selection(self, update, context)` - Handle category selection
  - ✅ `TelegramBot.handle_period_selection(self, update, context)` - Handle period selection
  - ✅ `TelegramBot.handle_schedule_category_selection(self, update, context)` - Handle schedule category selection
  - ✅ `TelegramBot.handle_user_command(self, update, context)` - Handle /user command to show user information.
  - ✅ `TelegramBot.is_initialized(self)` - Legacy method for backward compatibility.

Returns:
    bool: True if the Telegram bot is initialized and ready
  - ✅ `TelegramBot.message_received(self, update, context)` - Handle received message text
  - ✅ `TelegramBot.prompt_category_selection(self, update, context, action, prompt_message, is_message)` - Prompt user to select a category
  - ❌ `TelegramBot.prompt_for_days(self, update, context)` - No description
  - ✅ `TelegramBot.prompt_for_message(self, update, context, category)` - Prompt user to enter a message
  - ❌ `TelegramBot.prompt_for_time_periods(self, update, context)` - No description
  - ✅ `TelegramBot.run_polling(self)` - Run Telegram polling safely in a separate thread with an event loop.
  - ✅ `TelegramBot.save_new_message(self, update, context)` - Save a new message with selected days and time periods.

Args:
    update: Telegram update object
    context: Callback context containing message data
  - ✅ `TelegramBot.schedule_conv_handler(self)` - Create a conversation handler for schedule management.

Returns:
    ConversationHandler: Configured conversation handler for schedule editing flow
  - ✅ `TelegramBot.scream_command(self, update, context)` - Handle the /scream command.

Toggles screaming mode for the bot's responses.

Args:
    update: Telegram update object
    context: Callback context
  - ❌ `TelegramBot.show_schedule(self, update, context, category)` - No description
  - ✅ `TelegramBot.start(self)` - Legacy start method - calls the new async initialize.

Initializes the Telegram bot using the legacy interface.
  - ✅ `TelegramBot.stop(self)` - Legacy stop method - calls the new async shutdown.

Shuts down the Telegram bot using the legacy interface.
  - ✅ `TelegramBot.time_periods_selected(self, update, context)` - Handle time periods selection
  - ✅ `TelegramBot.update_time_periods_keyboard(self, update, context, selected)` - Update the time periods keyboard to reflect current selections.

Args:
    update: Telegram update object
    context: Callback context
    selected: List of currently selected time periods
  - ✅ `TelegramBot.view_edit_schedule_command(self, update, context)` - View/edit schedule command
  - ✅ `TelegramBot.whisper_command(self, update, context)` - Handle the /whisper command.

Toggles whispering mode for the bot's responses.

Args:
    update: Telegram update object
    context: Callback context
- ✅ `TelegramBotError` - Custom exception for Telegram bot-related errors.

#### `bot/user_context_manager.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the UserContextManager.

Sets up conversation history storage for tracking user interactions.
- ✅ `_get_active_schedules(self, schedules)` - Get list of currently active schedule periods.

Args:
    schedules: Dictionary containing schedule periods
    
Returns:
    list: List of active schedule period names
- ✅ `_get_conversation_history(self, user_id)` - Get recent conversation history with this user.
- ✅ `_get_conversation_insights(self, user_id)` - Get insights from recent chat interactions.
- ✅ `_get_minimal_context(self, user_id)` - Fallback minimal context if full context generation fails.

Args:
    user_id: The user's ID (can be None for anonymous context)
    
Returns:
    dict: Minimal context with basic information
- ✅ `_get_mood_trends(self, user_id)` - Analyze recent mood and energy trends.
- ✅ `_get_recent_activity(self, user_id)` - Get recent user activity and responses.
- ✅ `_get_user_preferences(self, user_id)` - Get user preferences using new structure.
- ✅ `_get_user_profile(self, user_id)` - Get basic user profile information using existing user infrastructure.
- ✅ `add_conversation_exchange(self, user_id, user_message, ai_response)` - Add a conversation exchange to history.

Args:
    user_id: The user's ID
    user_message: The user's message
    ai_response: The AI's response
- ✅ `format_context_for_ai(self, context)` - Format user context into a concise string for AI prompt.

Args:
    context: User context dictionary
    
Returns:
    str: Formatted context string for AI consumption
- ✅ `get_current_user_context(self, include_conversation_history)` - Get context for the currently logged-in user using the existing UserContext singleton.

Args:
    include_conversation_history: Whether to include recent conversation history
    
Returns:
    Dict containing all relevant user context for current user
- ✅ `get_user_context(self, user_id, include_conversation_history)` - Get comprehensive user context for AI conversation.

Args:
    user_id: The user's ID
    include_conversation_history: Whether to include recent conversation history
    
Returns:
    Dict containing all relevant user context
**Classes:**
- ✅ `UserContextManager` - Manages rich user context for AI conversations.
  - ✅ `UserContextManager.__init__(self)` - Initialize the UserContextManager.

Sets up conversation history storage for tracking user interactions.
  - ✅ `UserContextManager._get_active_schedules(self, schedules)` - Get list of currently active schedule periods.

Args:
    schedules: Dictionary containing schedule periods
    
Returns:
    list: List of active schedule period names
  - ✅ `UserContextManager._get_conversation_history(self, user_id)` - Get recent conversation history with this user.
  - ✅ `UserContextManager._get_conversation_insights(self, user_id)` - Get insights from recent chat interactions.
  - ✅ `UserContextManager._get_minimal_context(self, user_id)` - Fallback minimal context if full context generation fails.

Args:
    user_id: The user's ID (can be None for anonymous context)
    
Returns:
    dict: Minimal context with basic information
  - ✅ `UserContextManager._get_mood_trends(self, user_id)` - Analyze recent mood and energy trends.
  - ✅ `UserContextManager._get_recent_activity(self, user_id)` - Get recent user activity and responses.
  - ✅ `UserContextManager._get_user_preferences(self, user_id)` - Get user preferences using new structure.
  - ✅ `UserContextManager._get_user_profile(self, user_id)` - Get basic user profile information using existing user infrastructure.
  - ✅ `UserContextManager.add_conversation_exchange(self, user_id, user_message, ai_response)` - Add a conversation exchange to history.

Args:
    user_id: The user's ID
    user_message: The user's message
    ai_response: The AI's response
  - ✅ `UserContextManager.format_context_for_ai(self, context)` - Format user context into a concise string for AI prompt.

Args:
    context: User context dictionary
    
Returns:
    str: Formatted context string for AI consumption
  - ✅ `UserContextManager.get_current_user_context(self, include_conversation_history)` - Get context for the currently logged-in user using the existing UserContext singleton.

Args:
    include_conversation_history: Whether to include recent conversation history
    
Returns:
    Dict containing all relevant user context for current user
  - ✅ `UserContextManager.get_user_context(self, user_id, include_conversation_history)` - Get comprehensive user context for AI conversation.

Args:
    user_id: The user's ID
    include_conversation_history: Whether to include recent conversation history
    
Returns:
    Dict containing all relevant user context

### `core/` - Core System Modules

#### `core/auto_cleanup.py`
**Functions:**
- ✅ `auto_cleanup_if_needed(root_path, interval_days)` - Main function to check if cleanup is needed and perform it if so.
Returns True if cleanup was performed, False if not needed.
- ✅ `calculate_cache_size(pycache_dirs, pyc_files)` - Calculate total size of cache files.
- ✅ `find_pyc_files(root_path)` - Find all .pyc files recursively.
- ✅ `find_pycache_dirs(root_path)` - Find all __pycache__ directories recursively.
- ✅ `get_cleanup_status()` - Get information about the cleanup status.
- ✅ `get_last_cleanup_timestamp()` - Get the timestamp of the last cleanup from tracker file.
- ✅ `perform_cleanup(root_path)` - Perform the actual cleanup of cache files.
- ✅ `should_run_cleanup(interval_days)` - Check if cleanup should run based on last cleanup time.
- ✅ `update_cleanup_timestamp()` - Update the cleanup tracker file with current timestamp.

#### `core/backup_manager.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the BackupManager with default settings.

Sets up backup directory, maximum backup count, and ensures backup directory exists.
- ✅ `_add_directory_to_zip(self, zipf, directory, zip_path)` - Recursively add a directory to the zip file.
- ✅ `_backup_config_files(self, zipf)` - Backup configuration files.
- ✅ `_backup_log_files(self, zipf)` - Backup log files.
- ✅ `_backup_user_data(self, zipf)` - Backup all user data directories.
- ✅ `_cleanup_old_backups(self)` - Remove old backups to keep only the most recent ones.
- ✅ `_create_backup_manifest(self, zipf, backup_name, include_users, include_config, include_logs)` - Create a manifest file describing the backup contents.
- ✅ `_get_backup_info(self, backup_path)` - Get information about a specific backup.
- ✅ `_restore_config_files(self, zipf)` - Restore configuration files from backup.
- ✅ `_restore_user_data(self, zipf)` - Restore user data from backup.
- ✅ `create_automatic_backup(operation_name)` - Create an automatic backup before major operations.

Args:
    operation_name: Name of the operation being performed

Returns:
    Path to the backup file, or None if failed
- ✅ `create_backup(self, backup_name, include_users, include_config, include_logs)` - Create a comprehensive backup of the system.

Args:
    backup_name: Custom name for the backup (auto-generated if None)
    include_users: Whether to include user data
    include_config: Whether to include configuration files
    include_logs: Whether to include log files

Returns:
    Path to the backup file, or None if failed
- ✅ `ensure_backup_directory(self)` - Ensure backup directory exists.
- ✅ `list_backups(self)` - List all available backups with metadata.
- ✅ `perform_safe_operation(operation_func)` - Perform an operation with automatic backup and rollback capability.

Args:
    operation_func: Function to perform
    *args: Arguments for the operation function
    **kwargs: Keyword arguments for the operation function

Returns:
    True if operation succeeded, False if it failed and was rolled back
- ✅ `restore_backup(self, backup_path, restore_users, restore_config)` - Restore from a backup file.

Args:
    backup_path: Path to the backup file
    restore_users: Whether to restore user data
    restore_config: Whether to restore configuration files

Returns:
    True if restoration was successful, False otherwise
- ✅ `validate_backup(self, backup_path)` - Validate a backup file for integrity and completeness.

Args:
    backup_path: Path to the backup file

Returns:
    Tuple of (is_valid, list_of_errors)
- ✅ `validate_system_state()` - Validate the current system state for consistency.

Returns:
    True if system is in a valid state, False otherwise
**Classes:**
- ✅ `BackupManager` - Manages automatic backups and rollback operations.
  - ✅ `BackupManager.__init__(self)` - Initialize the BackupManager with default settings.

Sets up backup directory, maximum backup count, and ensures backup directory exists.
  - ✅ `BackupManager._add_directory_to_zip(self, zipf, directory, zip_path)` - Recursively add a directory to the zip file.
  - ✅ `BackupManager._backup_config_files(self, zipf)` - Backup configuration files.
  - ✅ `BackupManager._backup_log_files(self, zipf)` - Backup log files.
  - ✅ `BackupManager._backup_user_data(self, zipf)` - Backup all user data directories.
  - ✅ `BackupManager._cleanup_old_backups(self)` - Remove old backups to keep only the most recent ones.
  - ✅ `BackupManager._create_backup_manifest(self, zipf, backup_name, include_users, include_config, include_logs)` - Create a manifest file describing the backup contents.
  - ✅ `BackupManager._get_backup_info(self, backup_path)` - Get information about a specific backup.
  - ✅ `BackupManager._restore_config_files(self, zipf)` - Restore configuration files from backup.
  - ✅ `BackupManager._restore_user_data(self, zipf)` - Restore user data from backup.
  - ✅ `BackupManager.create_backup(self, backup_name, include_users, include_config, include_logs)` - Create a comprehensive backup of the system.

Args:
    backup_name: Custom name for the backup (auto-generated if None)
    include_users: Whether to include user data
    include_config: Whether to include configuration files
    include_logs: Whether to include log files

Returns:
    Path to the backup file, or None if failed
  - ✅ `BackupManager.ensure_backup_directory(self)` - Ensure backup directory exists.
  - ✅ `BackupManager.list_backups(self)` - List all available backups with metadata.
  - ✅ `BackupManager.restore_backup(self, backup_path, restore_users, restore_config)` - Restore from a backup file.

Args:
    backup_path: Path to the backup file
    restore_users: Whether to restore user data
    restore_config: Whether to restore configuration files

Returns:
    True if restoration was successful, False otherwise
  - ✅ `BackupManager.validate_backup(self, backup_path)` - Validate a backup file for integrity and completeness.

Args:
    backup_path: Path to the backup file

Returns:
    Tuple of (is_valid, list_of_errors)

#### `core/checkin_analytics.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the CheckinAnalytics instance.

This class provides analytics and insights from daily check-in data.
- ✅ `_calculate_habit_score(self, checkins)` - Calculate habit score (0-100)
- ✅ `_calculate_mood_score(self, checkins)` - Calculate mood score (0-100)
- ✅ `_calculate_overall_completion(self, habit_stats)` - Calculate overall habit completion rate
- ✅ `_calculate_sleep_consistency(self, hours)` - Calculate sleep consistency (lower variance = more consistent)
- ✅ `_calculate_sleep_score(self, checkins)` - Calculate sleep score (0-100)
- ✅ `_calculate_streak(self, checkins, habit_key)` - Calculate current and best streaks for a habit
- ✅ `_get_habit_status(self, completion_rate)` - Get status description for habit completion rate
- ✅ `_get_mood_distribution(self, moods)` - Calculate distribution of mood scores
- ✅ `_get_score_level(self, score)` - Get wellness score level description
- ✅ `_get_sleep_recommendations(self, avg_hours, avg_quality, poor_days)` - Generate sleep recommendations
- ✅ `_get_wellness_recommendations(self, mood_score, habit_score, sleep_score)` - Generate wellness recommendations based on component scores
- ✅ `get_habit_analysis(self, user_id, days)` - Analyze habit patterns from check-in data
- ✅ `get_mood_trends(self, user_id, days)` - Analyze mood trends over the specified period
- ✅ `get_sleep_analysis(self, user_id, days)` - Analyze sleep patterns from check-in data
- ✅ `get_wellness_score(self, user_id, days)` - Calculate a comprehensive wellness score based on recent check-ins
**Classes:**
- ❌ `CheckinAnalytics` - No description
  - ✅ `CheckinAnalytics.__init__(self)` - Initialize the CheckinAnalytics instance.

This class provides analytics and insights from daily check-in data.
  - ✅ `CheckinAnalytics._calculate_habit_score(self, checkins)` - Calculate habit score (0-100)
  - ✅ `CheckinAnalytics._calculate_mood_score(self, checkins)` - Calculate mood score (0-100)
  - ✅ `CheckinAnalytics._calculate_overall_completion(self, habit_stats)` - Calculate overall habit completion rate
  - ✅ `CheckinAnalytics._calculate_sleep_consistency(self, hours)` - Calculate sleep consistency (lower variance = more consistent)
  - ✅ `CheckinAnalytics._calculate_sleep_score(self, checkins)` - Calculate sleep score (0-100)
  - ✅ `CheckinAnalytics._calculate_streak(self, checkins, habit_key)` - Calculate current and best streaks for a habit
  - ✅ `CheckinAnalytics._get_habit_status(self, completion_rate)` - Get status description for habit completion rate
  - ✅ `CheckinAnalytics._get_mood_distribution(self, moods)` - Calculate distribution of mood scores
  - ✅ `CheckinAnalytics._get_score_level(self, score)` - Get wellness score level description
  - ✅ `CheckinAnalytics._get_sleep_recommendations(self, avg_hours, avg_quality, poor_days)` - Generate sleep recommendations
  - ✅ `CheckinAnalytics._get_wellness_recommendations(self, mood_score, habit_score, sleep_score)` - Generate wellness recommendations based on component scores
  - ✅ `CheckinAnalytics.get_habit_analysis(self, user_id, days)` - Analyze habit patterns from check-in data
  - ✅ `CheckinAnalytics.get_mood_trends(self, user_id, days)` - Analyze mood trends over the specified period
  - ✅ `CheckinAnalytics.get_sleep_analysis(self, user_id, days)` - Analyze sleep patterns from check-in data
  - ✅ `CheckinAnalytics.get_wellness_score(self, user_id, days)` - Calculate a comprehensive wellness score based on recent check-ins

#### `core/config.py`
**Functions:**
- ✅ `__init__(self, message, missing_configs, warnings)` - Initialize the object.
- ✅ `ensure_user_directory(user_id)` - Ensure user directory exists if using subdirectories.
- ✅ `get_available_channels()` - Get list of available communication channels based on configuration.
- ✅ `get_user_data_dir(user_id)` - Get the data directory for a specific user.
- ✅ `get_user_file_path(user_id, file_type)` - Get the file path for a specific user file type.
- ✅ `print_configuration_report()` - Print a detailed configuration report to the console.
- ✅ `validate_ai_configuration()` - Validate AI-related configuration settings.
- ✅ `validate_all_configuration()` - Comprehensive configuration validation that checks all aspects of the configuration.

Returns:
    Dict containing validation results with the following structure:
    {
        'valid': bool,
        'errors': List[str],
        'warnings': List[str],
        'available_channels': List[str],
        'summary': str
    }
- ✅ `validate_and_raise_if_invalid()` - Validate configuration and raise ConfigValidationError if invalid.

Returns:
    List of available communication channels if validation passes.

Raises:
    ConfigValidationError: If configuration is invalid with detailed error information.
- ✅ `validate_communication_channels()` - Validate communication channel configurations.
- ✅ `validate_core_paths()` - Validate that all core paths are accessible and can be created if needed.
- ✅ `validate_discord_config()` - Validate Discord configuration settings.

Returns:
    bool: True if Discord configuration is valid
    
Raises:
    ConfigurationError: If DISCORD_BOT_TOKEN is missing
- ✅ `validate_email_config()` - Validate email configuration settings.

Returns:
    bool: True if email configuration is valid
    
Raises:
    ConfigurationError: If required email configuration variables are missing
- ✅ `validate_environment_variables()` - Check for common environment variable issues.
- ✅ `validate_file_organization_settings()` - Validate file organization settings.
- ✅ `validate_logging_configuration()` - Validate logging configuration.
- ✅ `validate_minimum_config()` - Ensure at least one communication channel is configured
- ✅ `validate_scheduler_configuration()` - Validate scheduler configuration.
- ✅ `validate_telegram_config()` - Validate Telegram configuration (currently deactivated).

Raises:
    ConfigurationError: Always raised as Telegram channel is deactivated.
**Classes:**
- ✅ `ConfigValidationError` - Custom exception for configuration validation errors with detailed information.
  - ✅ `ConfigValidationError.__init__(self, message, missing_configs, warnings)` - Initialize the object.

#### `core/error_handling.py`
**Functions:**
- ✅ `__enter__(self)` - Enter the context manager for safe file operations.

Returns:
    self: The SafeFileContext instance
- ✅ `__exit__(self, exc_type, exc_val, exc_tb)` - Exit the context manager and handle any exceptions.

Args:
    exc_type: Type of exception if any occurred
    exc_val: Exception value if any occurred
    exc_tb: Exception traceback if any occurred
- ✅ `__init__(self, message, details, recoverable)` - Initialize a new MHM error.

Args:
    message: Human-readable error message
    details: Optional dictionary with additional error details
    recoverable: Whether this error can be recovered from
- ✅ `__init__(self, name, description)` - Initialize an error recovery strategy.

Args:
    name: The name of the recovery strategy
    description: A description of what this strategy does
- ✅ `__init__(self)` - Initialize the FileNotFoundRecovery strategy.
- ✅ `__init__(self)` - Initialize the JSONDecodeRecovery strategy.
- ✅ `__init__(self)` - Initialize the ErrorHandler with default recovery strategies.

Sets up recovery strategies for common error types like missing files and corrupted JSON.
- ✅ `__init__(self, file_path, operation, user_id, category)` - Initialize the safe file context.

Args:
    file_path: Path to the file being operated on
    operation: Description of the operation being performed
    user_id: ID of the user performing the operation
    category: Category of the operation
- ✅ `_get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
- ✅ `_get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
- ✅ `_get_user_friendly_message(self, error, context)` - Convert technical error to user-friendly message.
- ✅ `_log_error(self, error, context)` - Log error with context.
- ✅ `_show_user_error(self, error, context, custom_message)` - Show user-friendly error message.
- ✅ `can_handle(self, error)` - Check if this strategy can handle the given error.
- ✅ `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check
    
Returns:
    True if this strategy can handle FileNotFoundError or file operation errors containing "not found"
- ✅ `can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check
    
Returns:
    True if this strategy can handle JSON decode errors or JSON-related file operation errors
- ❌ `decorator(func)` - No description
- ✅ `handle_communication_error(error, channel, operation, user_id)` - Convenience function for handling communication errors.
- ✅ `handle_configuration_error(error, setting, operation)` - Convenience function for handling configuration errors.
- ✅ `handle_error(self, error, context, operation, user_friendly)` - Handle an error with recovery strategies and logging.

Args:
    error: The exception that occurred
    context: Additional context about the error
    operation: Description of the operation that failed
    user_friendly: Whether to show user-friendly error messages
    
Returns:
    True if error was recovered from, False otherwise
- ✅ `handle_errors(operation, context, user_friendly, default_return)` - Decorator to automatically handle errors in functions.

Args:
    operation: Description of the operation (defaults to function name)
    context: Additional context to pass to error handler
    user_friendly: Whether to show user-friendly error messages
    default_return: Value to return if error occurs and can't be recovered
- ✅ `handle_file_error(error, file_path, operation, user_id, category)` - Convenience function for handling file-related errors.
- ✅ `recover(self, error, context)` - Attempt to recover from the error. Returns True if successful.
- ✅ `recover(self, error, context)` - Attempt to recover from the error by creating missing files with default data.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information
    
Returns:
    True if recovery was successful, False otherwise
- ✅ `recover(self, error, context)` - Attempt to recover from the error by recreating corrupted JSON files.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information
    
Returns:
    True if recovery was successful, False otherwise
- ✅ `safe_file_operation(file_path, operation, user_id, category)` - Context manager for safe file operations with automatic error handling.

Usage:
    with safe_file_operation("path/to/file.json", "loading user data", user_id="123"):
        # file operations here
- ❌ `wrapper()` - No description
**Classes:**
- ✅ `AIError` - Raised when AI operations fail.
- ✅ `CommunicationError` - Raised when communication channels fail.
- ✅ `ConfigurationError` - Raised when configuration is invalid or missing.
- ✅ `DataError` - Raised when there are issues with data files or data integrity.
- ✅ `ErrorHandler` - Centralized error handler for MHM.
  - ✅ `ErrorHandler.__init__(self)` - Initialize the ErrorHandler with default recovery strategies.

Sets up recovery strategies for common error types like missing files and corrupted JSON.
  - ✅ `ErrorHandler._get_user_friendly_message(self, error, context)` - Convert technical error to user-friendly message.
  - ✅ `ErrorHandler._log_error(self, error, context)` - Log error with context.
  - ✅ `ErrorHandler._show_user_error(self, error, context, custom_message)` - Show user-friendly error message.
  - ✅ `ErrorHandler.handle_error(self, error, context, operation, user_friendly)` - Handle an error with recovery strategies and logging.

Args:
    error: The exception that occurred
    context: Additional context about the error
    operation: Description of the operation that failed
    user_friendly: Whether to show user-friendly error messages
    
Returns:
    True if error was recovered from, False otherwise
- ✅ `ErrorRecoveryStrategy` - Base class for error recovery strategies.
  - ✅ `ErrorRecoveryStrategy.__init__(self, name, description)` - Initialize an error recovery strategy.

Args:
    name: The name of the recovery strategy
    description: A description of what this strategy does
  - ✅ `ErrorRecoveryStrategy.can_handle(self, error)` - Check if this strategy can handle the given error.
  - ✅ `ErrorRecoveryStrategy.recover(self, error, context)` - Attempt to recover from the error. Returns True if successful.
- ✅ `FileNotFoundRecovery` - Recovery strategy for missing files.
  - ✅ `FileNotFoundRecovery.__init__(self)` - Initialize the FileNotFoundRecovery strategy.
  - ✅ `FileNotFoundRecovery._get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
  - ✅ `FileNotFoundRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check
    
Returns:
    True if this strategy can handle FileNotFoundError or file operation errors containing "not found"
  - ✅ `FileNotFoundRecovery.recover(self, error, context)` - Attempt to recover from the error by creating missing files with default data.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information
    
Returns:
    True if recovery was successful, False otherwise
- ✅ `FileOperationError` - Raised when file operations fail.
- ✅ `JSONDecodeRecovery` - Recovery strategy for corrupted JSON files.
  - ✅ `JSONDecodeRecovery.__init__(self)` - Initialize the JSONDecodeRecovery strategy.
  - ✅ `JSONDecodeRecovery._get_default_data(self, file_path, context)` - Get appropriate default data based on file type.
  - ✅ `JSONDecodeRecovery.can_handle(self, error)` - Check if this strategy can handle the given error.

Args:
    error: The exception to check
    
Returns:
    True if this strategy can handle JSON decode errors or JSON-related file operation errors
  - ✅ `JSONDecodeRecovery.recover(self, error, context)` - Attempt to recover from the error by recreating corrupted JSON files.

Args:
    error: The exception that occurred
    context: Additional context containing file_path and other relevant information
    
Returns:
    True if recovery was successful, False otherwise
- ✅ `MHMError` - Base exception for all MHM-specific errors.
  - ✅ `MHMError.__init__(self, message, details, recoverable)` - Initialize a new MHM error.

Args:
    message: Human-readable error message
    details: Optional dictionary with additional error details
    recoverable: Whether this error can be recovered from
- ✅ `RecoveryError` - Raised when error recovery fails.
- ✅ `SafeFileContext` - Context manager for safe file operations.
  - ✅ `SafeFileContext.__enter__(self)` - Enter the context manager for safe file operations.

Returns:
    self: The SafeFileContext instance
  - ✅ `SafeFileContext.__exit__(self, exc_type, exc_val, exc_tb)` - Exit the context manager and handle any exceptions.

Args:
    exc_type: Type of exception if any occurred
    exc_val: Exception value if any occurred
    exc_tb: Exception traceback if any occurred
  - ✅ `SafeFileContext.__init__(self, file_path, operation, user_id, category)` - Initialize the safe file context.

Args:
    file_path: Path to the file being operated on
    operation: Description of the operation being performed
    user_id: ID of the user performing the operation
    category: Category of the operation
- ✅ `SchedulerError` - Raised when scheduler operations fail.
- ✅ `UserInterfaceError` - Raised when UI operations fail.
- ✅ `ValidationError` - Raised when data validation fails.

#### `core/file_operations.py`
**Functions:**
- ✅ `create_user_files(user_id, categories, user_preferences)` - Creates files for a new user in the appropriate structure.
Ensures schedules.json contains a block for each category, plus checkin and task reminder blocks.

Args:
    user_id: The user ID
    categories: List of message categories the user is opted into
    user_preferences: Optional user preferences dict to determine which files to create
- ✅ `determine_file_path(file_type, identifier)` - Determine file path based on file type and identifier.
Updated to support new organized structure.

Args:
    file_type: Type of file ('users', 'messages', 'schedules', 'sent_messages', 'default_messages', 'tasks')
    identifier: Identifier for the file (format depends on file_type)
    
Returns:
    str: Full file path
    
Raises:
    FileOperationError: If file_type is unknown or identifier format is invalid
- ✅ `load_json_data(file_path)` - Load data from a JSON file with comprehensive error handling and auto-create user files if missing.

Args:
    file_path: Path to the JSON file to load
    
Returns:
    dict/list: Loaded JSON data, or None if loading failed
- ✅ `save_json_data(data, file_path)` - Save data to a JSON file with comprehensive error handling.

Args:
    data: Data to save (must be JSON serializable)
    file_path: Path where to save the file
    
Returns:
    bool: True if successful, False if failed
    
Raises:
    FileOperationError: If saving fails
- ✅ `verify_file_access(paths)` - Verify that files exist and are accessible.

Args:
    paths: List of file paths to verify
    
Raises:
    FileOperationError: If any file is not found or inaccessible

#### `core/logger.py`
**Functions:**
- ✅ `disable_module_logging(module_name)` - Disable debug logging for a specific module.

Args:
    module_name: Name of the module to disable debug logging for
- ✅ `force_restart_logging()` - Force restart the logging system by clearing all handlers and reinitializing.

Useful when logging configuration becomes corrupted or needs to be reset.

Returns:
    bool: True if restart was successful, False otherwise
- ✅ `get_log_level_from_env()` - Get log level from environment variable, default to WARNING for quiet mode.

Returns:
    int: Logging level constant (e.g., logging.WARNING, logging.DEBUG)
- ✅ `get_logger(name)` - Get a logger with the specified name.

Args:
    name: Logger name (usually __name__ from the calling module)
    
Returns:
    logging.Logger: Configured logger instance
- ✅ `get_verbose_mode()` - Get current verbose mode status.

Returns:
    bool: True if verbose mode is enabled
- ✅ `set_console_log_level(level)` - Set the console logging level while keeping file logging at DEBUG.

Args:
    level: logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
- ✅ `set_verbose_mode(enabled)` - Explicitly set verbose mode.

Args:
    enabled (bool): True to enable verbose mode, False for quiet mode
- ✅ `setup_logging()` - Set up logging with file and console handlers. Ensure it is called only once.

Creates a dual-handler logging system:
- File handler: Always logs at DEBUG level with rotation
- Console handler: Respects verbosity settings (WARNING by default)

Automatically suppresses noisy third-party library logging.
- ✅ `suppress_noisy_logging()` - Suppress excessive logging from third-party libraries.

Sets logging level to WARNING for common noisy libraries to reduce log spam
while keeping important warnings and errors visible.
- ✅ `toggle_verbose_logging()` - Toggle between verbose (DEBUG/INFO) and quiet (WARNING+) logging for console output.
File logging always remains at DEBUG level.

Returns:
    bool: True if verbose mode is now enabled, False if quiet mode

#### `core/message_management.py`
**Functions:**
- ✅ `add_message(user_id, category, message_data, index)` - Add a new message to a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_data: Dictionary containing message data
    index: Optional position to insert the message (None for append)
- ✅ `create_message_file_from_defaults(user_id, category)` - Create a user's message file for a specific category from default messages.
This is the actual worker function that creates the file.

Args:
    user_id: The user ID
    category: The specific category to create a message file for
    
Returns:
    bool: True if file was created successfully
- ✅ `delete_message(user_id, category, message_id)` - Delete a specific message from a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to delete
    
Raises:
    ValidationError: If the message ID is not found or the category is invalid
- ✅ `edit_message(user_id, category, message_id, updated_data)` - Edit an existing message in a user's category.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to edit
    updated_data: Dictionary containing updated message data
    
Raises:
    ValidationError: If message ID is not found or category is invalid
- ✅ `ensure_user_message_files(user_id, categories)` - Ensure user has message files for specified categories.
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
- ✅ `get_last_10_messages(user_id, category)` - Get the last 10 messages for a user and category, sorted by timestamp descending.

Args:
    user_id: The user ID
    category: The message category
    
Returns:
    List[dict]: List of the last 10 sent messages for the category
- ✅ `get_message_categories()` - Retrieves message categories from the environment variable CATEGORIES.
Allows for either a comma-separated string or a JSON array.

Returns:
    List[str]: List of message categories
- ✅ `get_timestamp_for_sorting(item)` - Convert timestamp to float for consistent sorting.

Args:
    item: Dictionary containing a timestamp field or other data type
    
Returns:
    float: Timestamp as float for sorting, or 0.0 for invalid items
- ✅ `load_default_messages(category)` - Load default messages for the given category.

Args:
    category: The message category to load defaults for
    
Returns:
    List[dict]: List of default messages for the category
- ✅ `store_sent_message(user_id, category, message_id, message)` - Store a sent message for a user and category, with per-category grouping and cleanup.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the sent message
    message: The message content that was sent
- ✅ `update_message(user_id, category, message_id, new_message_data)` - Update a message by its message_id.

Args:
    user_id: The user ID
    category: The message category
    message_id: The ID of the message to update
    new_message_data: Complete new message data to replace the existing message
    
Raises:
    ValidationError: If message ID is not found or category is invalid

#### `core/response_tracking.py`
**Functions:**
- ✅ `_get_response_log_filename(response_type)` - Get the filename for a response log type.
- ✅ `get_recent_chat_interactions(user_id, limit)` - Get recent chat interactions for a user.
- ✅ `get_recent_daily_checkins(user_id, limit)` - Get recent daily check-in responses for a user.
- ✅ `get_recent_responses(user_id, response_type, limit)` - Get recent responses for a user from appropriate file structure.
- ✅ `get_timestamp_for_sorting(item)` - Convert timestamp to float for consistent sorting
- ✅ `get_user_checkin_preferences(user_id)` - Get user's check-in preferences from their preferences file.
- ✅ `get_user_checkin_questions(user_id)` - Get the enabled check-in questions for a user.
- ✅ `get_user_info_for_tracking(user_id)` - Get user information for response tracking.
- ✅ `is_user_checkins_enabled(user_id)` - Check if check-ins are enabled for a user.
- ✅ `store_chat_interaction(user_id, user_message, ai_response, context_used)` - Store a chat interaction between user and AI.
- ✅ `store_daily_checkin_response(user_id, response_data)` - Store a daily check-in response.
- ✅ `store_user_response(user_id, response_data, response_type)` - Store user response data in appropriate file structure.
- ✅ `track_user_response(user_id, category, response_data)` - Track a user's response to a message.

#### `core/schedule_management.py`
**Functions:**
- ❌ `add_schedule_period(category, period_name, start_time, end_time, scheduler_manager)` - No description
- ✅ `clear_schedule_periods_cache(user_id, category)` - Clear the schedule periods cache for a specific user/category or all.
- ✅ `delete_schedule_period(category, period_name, scheduler_manager)` - Delete a schedule period from a category.

Args:
    category: The schedule category
    period_name: The name of the period to delete
    scheduler_manager: Optional scheduler manager for rescheduling (default: None)
- ❌ `edit_schedule_period(category, period_name, new_start_time, new_end_time, scheduler_manager)` - No description
- ✅ `get_current_day_names()` - Returns the name of the current day plus 'ALL' for universal day messages.
- ✅ `get_current_time_periods_with_validation(user_id, category)` - Returns the current active time periods for a user and category.
If no active period is found, defaults to the first available period.
- ✅ `get_reminder_periods_and_days(user_id, category)` - Load reminder periods and days for a category (e.g., 'tasks') from schedules.json.
- ✅ `get_schedule_days(user_id, category)` - Get the schedule days for a user and category.

Args:
    user_id: The user ID
    category: The schedule category
    
Returns:
    list: List of days for the schedule, defaults to all days of the week
- ✅ `get_schedule_time_periods(user_id, category)` - Get schedule time periods for a specific user and category (new format).
- ✅ `get_user_info_for_schedule_management(user_id)` - Get user info for schedule management operations.
- ✅ `is_schedule_period_active(user_id, category, period_name)` - Check if a schedule period is currently active.

Args:
    user_id: The user ID
    category: The schedule category
    period_name: The name of the period to check
    
Returns:
    bool: True if the period is active, False otherwise (defaults to True if field is missing)
- ✅ `migrate_legacy_schedule_keys(user_id)` - Migrate all user schedule files from legacy 'start'/'end' keys to canonical 'start_time'/'end_time'.
If user_id is None, migrate all users.
- ✅ `set_reminder_periods_and_days(user_id, category, periods, days)` - Save reminder periods and days for a category to schedules.json.
- ✅ `set_schedule_days(user_id, category, days)` - Set the schedule days for a user and category.

Args:
    user_id: The user ID
    category: The schedule category
    days: List of days to set for the schedule
- ✅ `set_schedule_period_active(user_id, category, period_name, active)` - Set whether a schedule period is active or inactive.

Args:
    user_id: The user ID
    category: The schedule category
    period_name: The name of the period to modify
    active: Whether the period should be active (default: True)
    
Returns:
    bool: True if the period was found and updated, False otherwise
- ✅ `set_schedule_periods(user_id, category, periods_dict)` - Replace all schedule periods for a category with the given dict (period_name: {active, days, start_time, end_time}).
- ✅ `time_12h_display_to_24h(hour_12, minute, is_pm)` - Convert 12-hour display format to 24-hour time string.

Args:
    hour_12 (int): Hour in 12-hour format (1-12)
    minute (int): Minute (0-59)
    is_pm (bool): True if PM, False if AM
    
Returns:
    str: Time in 24-hour format (HH:MM)
- ✅ `time_24h_to_12h_display(time_24h)` - Convert 24-hour time string (HH:MM) to 12-hour display format.

Args:
    time_24h (str): Time in 24-hour format (e.g., "14:30")
    
Returns:
    tuple: (hour_12, minute, is_pm) where:
        - hour_12 (int): Hour in 12-hour format (1-12)
        - minute (int): Minute (0-59)
        - is_pm (bool): True if PM, False if AM
- ✅ `validate_and_format_time(time_str)` - Validate and format a time string to HH:MM format.

Args:
    time_str: Time string to validate and format
    
Returns:
    str: Formatted time string in HH:MM format
    
Raises:
    ValueError: If the time format is invalid

#### `core/scheduler.py`
**Functions:**
- ✅ `__init__(self, communication_manager)` - Initialize the SchedulerManager with communication manager.

Args:
    communication_manager: The communication manager for sending messages
- ✅ `cleanup_old_tasks(self, user_id, category)` - Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category.
- ✅ `cleanup_task_reminders(user_id, task_id)` - Standalone function to clean up task reminders for a user.
This can be called from the admin UI without needing a scheduler instance.
- ✅ `cleanup_task_reminders(self, user_id, task_id)` - Clean up task reminders for a user or specific task.
- ✅ `get_random_time_within_period(self, user_id, category, period, timezone_str)` - Get a random time within a specified period for a given category.
- ✅ `get_random_time_within_task_period(self, start_time, end_time)` - Generate a random time within a task reminder period.
Args:
    start_time: Start time in HH:MM format (e.g., "17:00")
    end_time: End time in HH:MM format (e.g., "18:00")
Returns:
    Random time in HH:MM format
- ✅ `get_user_categories(user_id)` - Get user's message categories.
- ✅ `get_user_checkin_preferences(user_id)` - Get user's check-in preferences.
- ✅ `get_user_task_preferences(user_id)` - Get user's task preferences.
- ✅ `handle_sending_scheduled_message(self, user_id, category, retry_attempts, retry_delay)` - Handles the sending of scheduled messages with retries.
- ✅ `handle_task_reminder(self, user_id, task_id, retry_attempts, retry_delay)` - Handles sending task reminders with retries.
- ✅ `is_job_for_category(self, job, user_id, category)` - Determines if a job is scheduled for a specific user and category.
- ✅ `is_time_conflict(self, user_id, schedule_datetime)` - Checks if there is a time conflict with any existing scheduled jobs for the user.
- ✅ `log_scheduled_tasks(self)` - Logs all current and upcoming scheduled tasks in a user-friendly manner.
- ✅ `process_user_schedules(user_id)` - Process schedules for a specific user.
- ✅ `reset_and_reschedule_daily_messages(self, category, user_id)` - Resets scheduled tasks for a specific category and reschedules daily messages for that category.
- ✅ `run_daily_scheduler(self)` - Starts the daily scheduler in a separate thread that handles all users.
- ✅ `schedule_all_task_reminders(user_id)` - Standalone function to schedule all task reminders for a user.
This can be called from the admin UI without needing a scheduler instance.
- ✅ `schedule_all_task_reminders(self, user_id)` - Schedule reminders for all active tasks for a user.
For each reminder period, pick one random task and schedule it at a random time within the period.
- ✅ `schedule_all_users_immediately(self)` - Schedule daily messages immediately for all users
- ✅ `schedule_checkin_at_exact_time(self, user_id, period_name)` - Schedule a check-in at the exact time specified in the period.
- ✅ `schedule_daily_message_job(self, user_id, category)` - Schedules daily messages immediately for the specified user and category.
Schedules one message per active period in the category.
- ✅ `schedule_message_at_random_time(self, user_id, category)` - Schedules a message at a random time within the user's preferred time periods.
- ✅ `schedule_message_for_period(self, user_id, category, period_name)` - Schedules a message at a random time within a specific period for a user and category.
- ✅ `schedule_task_reminder(self, user_id, task_id, reminder_time)` - Legacy function for backward compatibility.
Schedule a reminder for a specific task at the specified time.
- ✅ `schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str)` - Schedule a reminder for a specific task at a specific date and time.
- ✅ `schedule_task_reminder_at_time(self, user_id, task_id, reminder_time)` - Schedule a reminder for a specific task at the specified time (daily).
- ❌ `scheduler_loop()` - No description
- ✅ `set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes)` - Set a Windows scheduled task to wake the computer before a scheduled message.

Args:
    schedule_time: The datetime when the message is scheduled
    user_id: The user ID
    category: The message category
    period: The time period name
    wake_ahead_minutes: Minutes before schedule_time to wake the computer (default: 4)
- ✅ `stop_scheduler(self)` - Stops the scheduler thread.
**Classes:**
- ❌ `SchedulerManager` - No description
  - ✅ `SchedulerManager.__init__(self, communication_manager)` - Initialize the SchedulerManager with communication manager.

Args:
    communication_manager: The communication manager for sending messages
  - ✅ `SchedulerManager.cleanup_old_tasks(self, user_id, category)` - Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category.
  - ✅ `SchedulerManager.cleanup_task_reminders(self, user_id, task_id)` - Clean up task reminders for a user or specific task.
  - ✅ `SchedulerManager.get_random_time_within_period(self, user_id, category, period, timezone_str)` - Get a random time within a specified period for a given category.
  - ✅ `SchedulerManager.get_random_time_within_task_period(self, start_time, end_time)` - Generate a random time within a task reminder period.
Args:
    start_time: Start time in HH:MM format (e.g., "17:00")
    end_time: End time in HH:MM format (e.g., "18:00")
Returns:
    Random time in HH:MM format
  - ✅ `SchedulerManager.handle_sending_scheduled_message(self, user_id, category, retry_attempts, retry_delay)` - Handles the sending of scheduled messages with retries.
  - ✅ `SchedulerManager.handle_task_reminder(self, user_id, task_id, retry_attempts, retry_delay)` - Handles sending task reminders with retries.
  - ✅ `SchedulerManager.is_job_for_category(self, job, user_id, category)` - Determines if a job is scheduled for a specific user and category.
  - ✅ `SchedulerManager.is_time_conflict(self, user_id, schedule_datetime)` - Checks if there is a time conflict with any existing scheduled jobs for the user.
  - ✅ `SchedulerManager.log_scheduled_tasks(self)` - Logs all current and upcoming scheduled tasks in a user-friendly manner.
  - ✅ `SchedulerManager.reset_and_reschedule_daily_messages(self, category, user_id)` - Resets scheduled tasks for a specific category and reschedules daily messages for that category.
  - ✅ `SchedulerManager.run_daily_scheduler(self)` - Starts the daily scheduler in a separate thread that handles all users.
  - ✅ `SchedulerManager.schedule_all_task_reminders(self, user_id)` - Schedule reminders for all active tasks for a user.
For each reminder period, pick one random task and schedule it at a random time within the period.
  - ✅ `SchedulerManager.schedule_all_users_immediately(self)` - Schedule daily messages immediately for all users
  - ✅ `SchedulerManager.schedule_checkin_at_exact_time(self, user_id, period_name)` - Schedule a check-in at the exact time specified in the period.
  - ✅ `SchedulerManager.schedule_daily_message_job(self, user_id, category)` - Schedules daily messages immediately for the specified user and category.
Schedules one message per active period in the category.
  - ✅ `SchedulerManager.schedule_message_at_random_time(self, user_id, category)` - Schedules a message at a random time within the user's preferred time periods.
  - ✅ `SchedulerManager.schedule_message_for_period(self, user_id, category, period_name)` - Schedules a message at a random time within a specific period for a user and category.
  - ✅ `SchedulerManager.schedule_task_reminder(self, user_id, task_id, reminder_time)` - Legacy function for backward compatibility.
Schedule a reminder for a specific task at the specified time.
  - ✅ `SchedulerManager.schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str)` - Schedule a reminder for a specific task at a specific date and time.
  - ✅ `SchedulerManager.schedule_task_reminder_at_time(self, user_id, task_id, reminder_time)` - Schedule a reminder for a specific task at the specified time (daily).
  - ✅ `SchedulerManager.set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes)` - Set a Windows scheduled task to wake the computer before a scheduled message.

Args:
    schedule_time: The datetime when the message is scheduled
    user_id: The user ID
    category: The message category
    period: The time period name
    wake_ahead_minutes: Minutes before schedule_time to wake the computer (default: 4)
  - ✅ `SchedulerManager.stop_scheduler(self)` - Stops the scheduler thread.

#### `core/service.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the MHM backend service.

Sets up communication manager, scheduler manager, and registers emergency shutdown handler.
- ✅ `check_and_fix_logging(self)` - Check if logging is working and restart if needed
- ✅ `check_reschedule_requests(self)` - Check for and process reschedule request files from UI
- ✅ `check_test_message_requests(self)` - Check for and process test message request files from admin panel
- ✅ `cleanup_reschedule_requests(self)` - Clean up any remaining reschedule request files
- ✅ `cleanup_test_message_requests(self)` - Clean up any remaining test message request files
- ✅ `emergency_shutdown(self)` - Emergency shutdown handler registered with atexit
- ✅ `get_user_categories(user_id)` - Get the message categories for a specific user.

Args:
    user_id: The user's ID
    
Returns:
    List[str]: List of message categories the user is subscribed to
- ✅ `initialize_paths(self)` - Initialize and verify all required file paths for the service.

Creates paths for log files, user data directories, and message files for all users.

Returns:
    List[str]: List of all initialized file paths
- ✅ `main()` - Main entry point for the MHM backend service.

Creates and starts the service, handling initialization errors and graceful shutdown.
- ✅ `run_service_loop(self)` - Keep the service running until shutdown is requested
- ✅ `shutdown(self)` - Gracefully shutdown the service
- ✅ `signal_handler(self, signum, frame)` - Handle shutdown signals for graceful service termination.

Args:
    signum: Signal number
    frame: Current stack frame
- ✅ `start(self)` - Start the MHM backend service.

Initializes communication channels, scheduler, and begins the main service loop.
Sets up signal handlers for graceful shutdown.
- ✅ `validate_configuration(self)` - Validate all configuration settings before starting the service.
**Classes:**
- ✅ `InitializationError` - Custom exception for initialization errors.
- ❌ `MHMService` - No description
  - ✅ `MHMService.__init__(self)` - Initialize the MHM backend service.

Sets up communication manager, scheduler manager, and registers emergency shutdown handler.
  - ✅ `MHMService.check_and_fix_logging(self)` - Check if logging is working and restart if needed
  - ✅ `MHMService.check_reschedule_requests(self)` - Check for and process reschedule request files from UI
  - ✅ `MHMService.check_test_message_requests(self)` - Check for and process test message request files from admin panel
  - ✅ `MHMService.cleanup_reschedule_requests(self)` - Clean up any remaining reschedule request files
  - ✅ `MHMService.cleanup_test_message_requests(self)` - Clean up any remaining test message request files
  - ✅ `MHMService.emergency_shutdown(self)` - Emergency shutdown handler registered with atexit
  - ✅ `MHMService.initialize_paths(self)` - Initialize and verify all required file paths for the service.

Creates paths for log files, user data directories, and message files for all users.

Returns:
    List[str]: List of all initialized file paths
  - ✅ `MHMService.run_service_loop(self)` - Keep the service running until shutdown is requested
  - ✅ `MHMService.shutdown(self)` - Gracefully shutdown the service
  - ✅ `MHMService.signal_handler(self, signum, frame)` - Handle shutdown signals for graceful service termination.

Args:
    signum: Signal number
    frame: Current stack frame
  - ✅ `MHMService.start(self)` - Start the MHM backend service.

Initializes communication channels, scheduler, and begins the main service loop.
Sets up signal handlers for graceful shutdown.
  - ✅ `MHMService.validate_configuration(self)` - Validate all configuration settings before starting the service.

#### `core/service_utilities.py`
**Functions:**
- ✅ `__init__(self, interval)` - Initialize the throttler with a specified interval.

Args:
    interval: Time interval in seconds between allowed operations
- ✅ `create_reschedule_request(user_id, category)` - Create a reschedule request flag file for the service to pick up
- ✅ `is_service_running()` - Check if the MHM service is currently running
- ✅ `load_and_localize_datetime(datetime_str, timezone_str)` - Load and localize a datetime string to a specific timezone.

Args:
    datetime_str: Datetime string in format "YYYY-MM-DD HH:MM"
    timezone_str: Timezone string (default: 'America/Regina')
    
Returns:
    datetime: Timezone-aware datetime object
    
Raises:
    InvalidTimeFormatError: If datetime_str format is invalid
- ✅ `should_run(self)` - Check if enough time has passed since the last run to allow another execution.

Returns:
    bool: True if the operation should run, False if it should be throttled
- ✅ `title_case(text)` - Convert text to title case with proper handling of special cases.

Args:
    text: The text to convert to title case
    
Returns:
    str: Text converted to title case
- ✅ `wait_for_network(timeout)` - Wait for the network to be available, retrying every 5 seconds up to a timeout.
**Classes:**
- ✅ `InvalidTimeFormatError` - Exception raised when time format is invalid.

Used for time parsing and validation operations.
- ✅ `Throttler` - A utility class for throttling operations based on time intervals.

Prevents operations from running too frequently by tracking the last execution time.
  - ✅ `Throttler.__init__(self, interval)` - Initialize the throttler with a specified interval.

Args:
    interval: Time interval in seconds between allowed operations
  - ✅ `Throttler.should_run(self)` - Check if enough time has passed since the last run to allow another execution.

Returns:
    bool: True if the operation should run, False if it should be throttled

#### `core/ui_management.py`
**Functions:**
- ✅ `add_period_widget_to_layout(layout, period_name, period_data, category, parent_widget, widget_list, delete_callback)` - Add a period widget to a layout with proper display formatting.

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
- ✅ `clear_period_widgets_from_layout(layout, widget_list)` - Clear all period widgets from a layout.

Args:
    layout: The QVBoxLayout to clear
    widget_list: Optional list to track widgets (will be cleared if provided)

Returns:
    None
- ✅ `collect_period_data_from_widgets(widget_list, category)` - Collect period data from a list of period widgets.

Args:
    widget_list: List of PeriodRowWidget instances
    category: The category (tasks, checkin, or schedule category)

Returns:
    Dictionary of period data with storage-formatted names, each with only 'active', 'days', 'start_time', 'end_time'.
- ✅ `load_period_widgets_for_category(layout, user_id, category, parent_widget, widget_list, delete_callback)` - Load and display period widgets for a specific category.

Args:
    layout: The QVBoxLayout to add widgets to
    user_id: The user ID
    category: The category (tasks, checkin, or schedule category)
    parent_widget: The parent widget for period widgets
    widget_list: Optional list to track widgets
    delete_callback: Optional callback for delete signal

Returns:
    List of created widgets
- ✅ `period_name_for_display(period_name, category)` - Convert period name to display format using existing logic.

Args:
    period_name: The period name to convert
    category: The category (tasks, checkin, or schedule category)

Returns:
    Display-formatted period name
- ✅ `period_name_for_storage(display_name, category)` - Convert display period name to storage format.

Args:
    display_name: The display-formatted period name
    category: The category (tasks, checkin, or schedule category)

Returns:
    Storage-formatted period name (preserve original case)

#### `core/user_data_handlers.py`
**Functions:**
- ✅ `get_all_user_ids()` - Return a list of *all* user IDs known to the system.
- ✅ `get_user_data(user_id, data_types, fields, auto_create, include_metadata)` - Migrated implementation of get_user_data.
- ✅ `register_data_loader(data_type, loader_func, file_type, default_fields, metadata_fields, description)` - Proxy to the original *register_data_loader*.

Imported here so callers can simply do::

    from core.user_data_handlers import register_data_loader

…and forget about *core.user_management*.
- ✅ `save_user_data(user_id, data_updates, auto_create, update_index, create_backup, validate_data)` - Migrated implementation of save_user_data.
- ✅ `save_user_data_transaction(user_id, data_updates, auto_create)` - Atomic wrapper copied from user_management.
- ✅ `update_channel_preferences(user_id, updates)` - Specialised helper – update only the *preferences.channel* subtree.
- ✅ `update_user_account(user_id, updates)` - Update (part of) a user’s *account.json* file.

This is a thin convenience wrapper around :pyfunc:`save_user_data` that
scopes *updates* to the ``account`` data-type.
- ✅ `update_user_context(user_id, updates)` - Update *user_context.json* for the given user.
- ✅ `update_user_preferences(user_id, updates)` - Update *preferences.json*.

Includes the extra bookkeeping originally implemented in
``core.user_management.update_user_preferences`` (default schedule creation
for new categories, message-file creation, etc.) so behaviour remains
unchanged.
- ✅ `update_user_schedules(user_id, schedules_data)` - Persist a complete schedules dict for *user_id*.

Wrapper around the original helper in **core.user_management** – keeps
outside modules decoupled from the legacy path.

#### `core/user_data_manager.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the UserDataManager.

Sets up backup directory and index file path for user data management operations.
- ✅ `_get_last_interaction(self, user_id)` - Get the timestamp of the user's last interaction with the system.

Args:
    user_id: The user's ID
    
Returns:
    str: ISO format timestamp of last interaction, or default if none found
- ✅ `backup_user_data(user_id, include_messages)` - Create a backup of user data.

Args:
    user_id: The user's ID
    include_messages: Whether to include message files in backup
    
Returns:
    str: Path to the created backup file
- ✅ `backup_user_data(self, user_id, include_messages)` - Create a complete backup of user's data
- ✅ `build_user_index()` - Build an index of all users and their message data.
- ✅ `delete_user_completely(user_id, create_backup)` - Completely delete a user and all their data.

Args:
    user_id: The user's ID
    create_backup: Whether to create a backup before deletion
    
Returns:
    bool: True if user was deleted successfully
- ✅ `delete_user_completely(self, user_id, create_backup)` - Completely remove all traces of a user from the system
- ✅ `export_user_data(user_id, export_format)` - Export user data to a structured format.

Args:
    user_id: The user's ID
    export_format: Format for export (currently only "json" supported)
    
Returns:
    Dict containing all user data in structured format
- ✅ `export_user_data(self, user_id, export_format)` - Export all user data to a structured format
- ✅ `get_all_user_summaries()` - Get summaries for all users.
- ✅ `get_user_analytics_summary(user_id)` - Get an analytics summary for a user including interaction patterns and data usage.

Args:
    user_id: The user's ID
    
Returns:
    Dict containing analytics summary information
- ✅ `get_user_categories(user_id)` - Get user's message categories.
- ✅ `get_user_data_summary(user_id)` - Get a summary of user data.

Args:
    user_id: The user's ID
    
Returns:
    Dict containing user data summary
- ✅ `get_user_data_summary(self, user_id)` - Get a comprehensive summary of user data including file counts and sizes.

Args:
    user_id: The user's ID
    
Returns:
    Dict containing summary information about the user's data
- ✅ `get_user_info_for_data_manager(user_id)` - Get user info for data manager operations - uses new hybrid structure.
- ✅ `get_user_message_files(self, user_id)` - Get all message file paths for a user
- ✅ `get_user_summary(user_id)` - Get a summary of user data and message statistics.
- ✅ `rebuild_full_index(self)` - Rebuild the complete user index from scratch.

Scans all user directories and creates a fresh index with current information.

Returns:
    bool: True if index was rebuilt successfully
- ✅ `rebuild_user_index()` - Rebuild the complete user index.

Returns:
    bool: True if index was rebuilt successfully
- ✅ `remove_from_index(self, user_id)` - Remove a user from the index.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if user was removed from index successfully
- ✅ `search_users(self, query, search_fields)` - Search for users based on query string and specified fields.

Args:
    query: Search query string
    search_fields: List of fields to search in (default: all fields)
    
Returns:
    List of user summaries matching the search criteria
- ✅ `update_message_references(user_id)` - Update message file references for a user.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if references were updated successfully
- ✅ `update_message_references(self, user_id)` - Add/update message file references in user profile
- ✅ `update_user_index(user_id)` - Update the user index for a specific user.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if index was updated successfully
- ✅ `update_user_index(self, user_id)` - Update the user index with current information for a specific user.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if index was updated successfully
**Classes:**
- ✅ `UserDataManager` - Enhanced user data management with references, backup, and indexing capabilities
  - ✅ `UserDataManager.__init__(self)` - Initialize the UserDataManager.

Sets up backup directory and index file path for user data management operations.
  - ✅ `UserDataManager._get_last_interaction(self, user_id)` - Get the timestamp of the user's last interaction with the system.

Args:
    user_id: The user's ID
    
Returns:
    str: ISO format timestamp of last interaction, or default if none found
  - ✅ `UserDataManager.backup_user_data(self, user_id, include_messages)` - Create a complete backup of user's data
  - ✅ `UserDataManager.delete_user_completely(self, user_id, create_backup)` - Completely remove all traces of a user from the system
  - ✅ `UserDataManager.export_user_data(self, user_id, export_format)` - Export all user data to a structured format
  - ✅ `UserDataManager.get_user_data_summary(self, user_id)` - Get a comprehensive summary of user data including file counts and sizes.

Args:
    user_id: The user's ID
    
Returns:
    Dict containing summary information about the user's data
  - ✅ `UserDataManager.get_user_message_files(self, user_id)` - Get all message file paths for a user
  - ✅ `UserDataManager.rebuild_full_index(self)` - Rebuild the complete user index from scratch.

Scans all user directories and creates a fresh index with current information.

Returns:
    bool: True if index was rebuilt successfully
  - ✅ `UserDataManager.remove_from_index(self, user_id)` - Remove a user from the index.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if user was removed from index successfully
  - ✅ `UserDataManager.search_users(self, query, search_fields)` - Search for users based on query string and specified fields.

Args:
    query: Search query string
    search_fields: List of fields to search in (default: all fields)
    
Returns:
    List of user summaries matching the search criteria
  - ✅ `UserDataManager.update_message_references(self, user_id)` - Add/update message file references in user profile
  - ✅ `UserDataManager.update_user_index(self, user_id)` - Update the user index with current information for a specific user.

Args:
    user_id: The user's ID
    
Returns:
    bool: True if index was updated successfully

#### `core/user_data_validation.py`
**Functions:**
- ❌ `is_valid_email(email)` - No description
- ❌ `is_valid_phone(phone)` - No description
- ✅ `title_case(text)` - Convert text to title case while keeping certain small words lowercase.
- ✅ `validate_new_user_data(user_id, data_updates)` - Validate complete dataset required for a brand-new user.
- ✅ `validate_personalization_data(data)` - Validate *context/personalization* structure.

No field is required; we only type-check fields that are present.
This logic previously lived in ``core.user_management``.
- ✅ `validate_schedule_periods(periods, category)` - Validate schedule periods and return (is_valid, error_messages).

Args:
    periods: Dictionary of period_name -> period_data
    category: Category name for error messages (e.g., "tasks", "check-ins")

Returns:
    Tuple of (is_valid, list_of_error_messages)
- ❌ `validate_time_format(time_str)` - No description
- ✅ `validate_user_update(user_id, data_type, updates)` - Validate partial updates to an existing user's data.

#### `core/user_management.py`
**Functions:**
- ✅ `_load_presets_json()` - Load presets from resources/presets.json (cached).
- ✅ `add_personalization_item(user_id, field, item)` - Add an item to a list field in personalization data using centralized system.
- ✅ `clear_personalization_cache(user_id)` - Clear the personalization cache for a specific user or all users.
- ✅ `clear_user_caches(user_id)` - Clear user data caches.
- ✅ `create_default_personalization_data()` - Create default personalization data structure.
- ✅ `create_default_schedule_periods(category)` - Create default schedule periods for a new category.
- ✅ `create_new_user(user_data)` - Create a new user with the new data structure.
- ✅ `ensure_all_categories_have_schedules(user_id)` - Ensure all categories in user preferences have corresponding schedules.
- ✅ `ensure_category_has_default_schedule(user_id, category)` - Ensure a category has default schedule periods if it doesn't exist.
- ✅ `ensure_unique_ids(data)` - Ensure all messages have unique IDs.
- ✅ `get_all_user_ids()` - Get all user IDs from the system.
- ✅ `get_available_data_types()` - Get list of available data types.
- ✅ `get_data_type_info(data_type)` - Get information about a specific data type.
- ✅ `get_personalization_field(user_id, field)` - Get a specific field from personalization data using centralized system.
- ✅ `get_predefined_options(field)` - Return predefined options for a personalization field.
- ✅ `get_timezone_options()` - Get timezone options.
- ✅ `get_user_account_status(user_id)` - Get user's account status using centralized system.
- ✅ `get_user_categories(user_id)` - Get user's message categories using centralized system.
- ✅ `get_user_channel_type(user_id)` - Get user's communication channel type using centralized system.
- ❌ `get_user_data()` - No description
- ✅ `get_user_data_with_metadata(user_id, data_types)` - Get user data with file metadata using centralized system.
- ✅ `get_user_email(user_id)` - Get user's email address using centralized system.
- ✅ `get_user_essential_info(user_id)` - Get essential user information using centralized system.
- ✅ `get_user_id_by_chat_id(chat_id)` - Get user ID by chat ID.
- ✅ `get_user_id_by_discord_user_id(discord_user_id)` - Get user ID by Discord user ID.
- ✅ `get_user_id_by_internal_username(internal_username)` - Get user ID by internal username.
- ✅ `get_user_preferred_name(user_id)` - Get user's preferred name using centralized system.
- ✅ `load_and_ensure_ids(user_id)` - Load messages for all categories and ensure IDs are unique for a user.
- ✅ `load_user_account_data(user_id, auto_create)` - Load user account data from account.json.
- ✅ `load_user_context_data(user_id, auto_create)` - Load user context data from user_context.json.
- ✅ `load_user_preferences_data(user_id, auto_create)` - Load user preferences data from preferences.json.
- ✅ `load_user_schedules_data(user_id, auto_create)` - Load user schedules data from schedules.json.
- ✅ `migrate_legacy_schedules_structure(schedules_data)` - Migrate legacy schedules structure to new format.
- ✅ `register_data_loader(data_type, loader_func, file_type, default_fields, metadata_fields, description)` - Register a new data loader for the centralized system.

Args:
    data_type: Unique identifier for the data type
    loader_func: Function that loads the data
    file_type: File type identifier
    default_fields: Commonly accessed fields
    metadata_fields: Fields that contain metadata
    description: Human-readable description
- ✅ `remove_personalization_item(user_id, field, item)` - Remove an item from a list field in personalization data using centralized system.
- ✅ `save_user_account_data(user_id, account_data)` - Save user account data to account.json.
- ✅ `save_user_context_data(user_id, context_data)` - Save user context data to user_context.json.
- ❌ `save_user_data()` - No description
- ❌ `save_user_data_transaction()` - No description
- ✅ `save_user_preferences_data(user_id, preferences_data)` - Save user preferences data to preferences.json.
- ✅ `save_user_schedules_data(user_id, schedules_data)` - Save user schedules data to schedules.json.
- ✅ `update_channel_preferences(user_id, updates, auto_create)` - Update channel preferences without triggering category schedule creation.
- ✅ `update_personalization_field(user_id, field, value)` - Update a specific field in personalization data using centralized system.
- ✅ `update_user_account(user_id, updates, auto_create)` - Update user account information.
- ✅ `update_user_context(user_id, updates, auto_create)` - Update user context information.
- ✅ `update_user_preferences(user_id, updates, auto_create)` - Update user preferences.
- ✅ `update_user_schedules(user_id, schedules_data)` - Update user schedules data.

#### `core/validation.py`

### `root/` - Root Files

#### `run_mhm.py`
**Functions:**
- ✅ `main()` - Launch the MHM Manager UI

#### `run_tests.py`
**Functions:**
- ✅ `main()` - Main test runner function.
- ✅ `run_specific_module(module_name)` - Run tests for a specific module.
- ✅ `run_test_categories()` - Run tests by category.
- ✅ `run_tests_with_pytest(test_paths, markers, verbose, coverage)` - Run tests using pytest with specified options.
- ✅ `show_test_summary()` - Show summary of available tests.

### `scripts/` - Unknown Directory

#### `scripts/debug/debug_category_dialog.py`
**Functions:**
- ✅ `main()` - Run all tests
- ✅ `test_category_widget_clear()` - Test if CategorySelectionWidget.set_selected_categories([]) works
- ✅ `test_preferences_update()` - Test if update_user_preferences works
- ✅ `test_user_data_functions()` - Test if update_user_account and update_user_preferences work

#### `scripts/debug/debug_comprehensive_prompt.py`
**Functions:**
- ✅ `debug_comprehensive_prompt()` - Debug the comprehensive context prompt generation.

#### `scripts/debug/debug_lm_studio_timeout.py`
**Functions:**
- ✅ `check_lm_studio_process()` - Check if LM Studio process is running and using resources.
- ✅ `test_chat_completions()` - Test the chat completions endpoint with different timeouts.
- ✅ `test_models_endpoint()` - Test the models endpoint with different timeouts.
- ✅ `test_network_connectivity()` - Test basic network connectivity to LM Studio.
- ✅ `test_system_info()` - Test system information endpoints.

#### `scripts/debug/debug_preferences.py`
**Functions:**
- ❌ `debug_preferences()` - No description

#### `scripts/migration/migrate_messaging_service.py`
**Functions:**
- ✅ `migrate_messaging_service()` - Migrate messaging_service to channel.type for all users.
- ✅ `verify_migration(users)` - Verify that the migration was successful.

#### `scripts/migration/migrate_schedule_format.py`
**Functions:**
- ✅ `main()` - Main migration function.
- ✅ `migrate_legacy_schedules_structure(schedules_data)` - Convert legacy flat schedule structure to new nested format.
- ✅ `migrate_user_files()` - Migrate all user files to new format.
- ✅ `remove_enabled_fields_from_preferences(prefs)` - Remove 'enabled' fields from preferences.
- ✅ `remove_enabled_fields_from_schedules(schedules_data)` - Remove 'enabled' fields from schedule periods.

#### `scripts/migration/migrate_schedules_cleanup.py`
**Functions:**
- ✅ `collapse_days(days)` - Collapse a list of days to ['ALL'] if all days of the week are present.

If the days list contains all seven days of the week, it is collapsed
to ['ALL'] for more efficient storage and processing.

Args:
    days: List of day names to check
    
Returns:
    List containing either ['ALL'] if all days present, or the original days list
- ✅ `find_all_schedules_files(base_dir)` - Find all user schedule files in the data directory.

Searches for schedules.json files in user subdirectories
within the specified base directory.

Args:
    base_dir: Base directory to search in (default: "data/users")
    
Returns:
    List of file paths to user schedule files
- ✅ `main()` - Main function to migrate all user schedule files.

Finds all user schedule files and applies the migration
to clean up schedule data structure and optimize day lists.
- ❌ `migrate_schedules_file(schedules_path)` - No description

#### `scripts/migration/migrate_sent_messages.py`
**Functions:**
- ✅ `main()` - Main migration function.
- ✅ `migrate_sent_messages()` - Migrate sent_messages.json files from user root directories to messages folders.
- ✅ `update_file_operations_code()` - Update the file operations code to use the new sent_messages path structure.

#### `scripts/migration/migrate_user_data_structure.py`
**Functions:**
- ✅ `__init__(self, dry_run, backup)` - Initialize the object
- ✅ `backup_user_data(self, user_id, user_dir)` - Create backup of user data before migration.
- ✅ `cleanup_old_files(self, user_dir)` - Remove old files after successful migration.
- ✅ `is_already_migrated(self, user_dir)` - Check if user data is already in new structure.
- ✅ `load_current_data(self, user_id, user_dir)` - Load all current data files for a user.
- ✅ `main()` - Main migration function.
- ✅ `migrate_all_users(self)` - Migrate all users in the system.
- ✅ `migrate_user(self, user_id)` - Migrate a single user's data.
- ✅ `save_new_data(self, user_id, new_data)` - Save the new data structure for a user.
- ✅ `transform_data(self, user_id, current_data)` - Transform current data structure to new structure.
**Classes:**
- ✅ `UserDataMigrator` - Handles migration of user data from old structure to new structure.
  - ✅ `UserDataMigrator.__init__(self, dry_run, backup)` - Initialize the object
  - ✅ `UserDataMigrator.backup_user_data(self, user_id, user_dir)` - Create backup of user data before migration.
  - ✅ `UserDataMigrator.cleanup_old_files(self, user_dir)` - Remove old files after successful migration.
  - ✅ `UserDataMigrator.is_already_migrated(self, user_dir)` - Check if user data is already in new structure.
  - ✅ `UserDataMigrator.load_current_data(self, user_id, user_dir)` - Load all current data files for a user.
  - ✅ `UserDataMigrator.migrate_all_users(self)` - Migrate all users in the system.
  - ✅ `UserDataMigrator.migrate_user(self, user_id)` - Migrate a single user's data.
  - ✅ `UserDataMigrator.save_new_data(self, user_id, new_data)` - Save the new data structure for a user.
  - ✅ `UserDataMigrator.transform_data(self, user_id, current_data)` - Transform current data structure to new structure.

#### `scripts/testing/ai/test_ai_with_clear_cache.py`
**Functions:**
- ✅ `test_ai_with_clear_cache()` - Test AI responses with cleared cache.
- ✅ `test_direct_api_call()` - Test direct API call with comprehensive context.

#### `scripts/testing/ai/test_comprehensive_ai.py`
**Functions:**
- ✅ `test_ai_status()` - Test the AI status to confirm it's using comprehensive context.
- ✅ `test_comprehensive_ai_access()` - Test the comprehensive AI access to user data.

#### `scripts/testing/ai/test_data_integrity.py`
**Functions:**
- ✅ `test_data_integrity()` - Test Data Integrity

#### `scripts/testing/ai/test_lm_studio.py`
**Functions:**
- ✅ `test_ai_chatbot_status()` - Test the AI chatbot status.
- ✅ `test_lm_studio_connection()` - Test the LM Studio connection directly.
- ✅ `test_simple_response()` - Test a simple AI response.

#### `scripts/testing/ai/test_new_modules.py`
**Functions:**
- ✅ `main()` - Run all tests
- ✅ `test_file_operations_module()` - Test file_operations.py module
- ✅ `test_message_management_module()` - Test message_management.py module
- ✅ `test_response_tracking_module()` - Test response_tracking.py module
- ✅ `test_schedule_management_module()` - Test schedule_management.py module
- ✅ `test_service_utilities_module()` - Test service_utilities.py module
- ✅ `test_user_management_module()` - Test user_management.py module
- ✅ `test_validation_module()` - Test validation.py module

#### `scripts/testing/analyze_documentation_overlap.py`
**Functions:**
- ✅ `analyze_file_purposes(docs)` - Analyze the purpose and content of each documentation file.
- ✅ `extract_sections(content)` - Extract sections from markdown content.
- ✅ `find_common_topics(docs)` - Find common topics across documentation files.
- ✅ `generate_consolidation_report()` - Generate a report on documentation consolidation opportunities.
- ✅ `get_documentation_files()` - Get all documentation files and their content.

#### `scripts/testing/test_all_dialogs.py`

#### `scripts/testing/test_category_dialog.py`

#### `scripts/testing/test_migration.py`
**Functions:**
- ✅ `main()` - Test the migration in dry-run mode.

#### `scripts/testing/test_user_data_analysis.py`
**Functions:**
- ✅ `test_fallback_directly()` - Test the fallback method directly.
- ✅ `test_user_data_analysis()` - Test the enhanced fallback with user-specific questions.

#### `scripts/testing/test_utils_functions.py`
**Functions:**
- ✅ `main()` - Run all tests
- ✅ `test_basic_imports()` - Test that we can import all the key modules
- ✅ `test_file_operations()` - Test basic file operations
- ✅ `test_user_operations()` - Test user-related operations
- ✅ `test_utility_functions()` - Test utility functions

#### `scripts/testing/validate_config.py`
**Functions:**
- ✅ `main()` - Main entry point for the module

#### `scripts/utilities/add_checkin_schedules.py`
**Functions:**
- ✅ `add_checkin_schedules_to_existing_users()` - Add check-in schedules to existing users who have check-ins enabled
- ✅ `show_user_checkin_status()` - Show the current check-in status for all users

#### `scripts/utilities/check_checkin_schedules.py`
**Functions:**
- ✅ `check_checkin_schedules()` - Check check-in schedules for all users
- ✅ `show_management_commands()` - Show how to manage check-in schedules
- ✅ `show_schedule_period_structure()` - Show the structure of check-in schedule periods

#### `scripts/utilities/cleanup/cleanup_data_test_users.py`
**Functions:**
- ✅ `cleanup_data_test_users()` - Remove test users from the data/users directory
- ✅ `main()` - Main cleanup function

#### `scripts/utilities/cleanup/cleanup_real_test_users.py`
**Functions:**
- ✅ `cleanup_real_test_users()` - Clean up test users in the real data directory.

#### `scripts/utilities/cleanup/cleanup_test_data.py`
**Functions:**
- ✅ `cleanup_backup_files()` - Remove backup files from migration and testing
- ✅ `cleanup_old_scripts()` - Remove old migration and testing scripts that are no longer needed
- ✅ `cleanup_test_users()` - Remove test user directories
- ✅ `get_script_dir()` - Get the MHM root directory
- ✅ `main()` - Run the cleanup process

#### `scripts/utilities/cleanup/cleanup_user_message_files.py`
**Functions:**
- ✅ `check_message_file_format(file_path)` - Check if a message file is in the old format (list of strings).
- ✅ `cleanup_user_message_files()` - Clean up user message files by removing unwanted files and ensuring proper ones exist.
- ✅ `main()` - Main function to run the cleanup.

#### `scripts/utilities/cleanup_duplicate_messages.py`
**Functions:**
- ✅ `check_duplicates_in_file(filepath)` - Check for duplicate messages in a single file.
- ✅ `clean_duplicates(args)` - Main function to clean duplicates from all message files.
- ✅ `create_backup(filepath)` - Create a backup of the file before modification.
- ✅ `find_message_files()` - Find all JSON message files in the configured messages directory.
- ✅ `main()` - Main entry point for the module

#### `scripts/utilities/cleanup_test_users.py`
**Functions:**
- ✅ `cleanup_test_users()` - Remove test users from the real data directory
- ✅ `main()` - Main cleanup function

#### `scripts/utilities/fix_user_schedules.py`
**Functions:**
- ✅ `fix_user_schedules(user_id)` - Fix the schedule structure for a specific user.

#### `scripts/utilities/rebuild_index.py`
**Functions:**
- ✅ `main()` - Rebuild the user index.

#### `scripts/utilities/refactoring/analyze_migration_needs.py`
**Functions:**
- ✅ `analyze_migration_needs()` - Analyze what needs to be migrated from core.user_management.
- ✅ `extract_imports_from_file(filepath)` - Extract all imports from a Python file.

#### `scripts/utilities/refactoring/find_legacy_get_user_data.py`

#### `scripts/utilities/refactoring/find_legacy_imports.py`

#### `scripts/utilities/refactoring/fix_broken_imports.py`
**Functions:**
- ✅ `backup_file(filepath)` - Create a backup of the file.
- ✅ `fix_imports_in_file(filepath)` - Fix broken imports in a single file.
- ✅ `main()` - Main fix function.

#### `scripts/utilities/refactoring/migrate_legacy_imports.py`
**Functions:**
- ✅ `backup_file(filepath)` - Create a backup of the file.
- ✅ `main()` - Main migration function.
- ✅ `migrate_imports_in_file(filepath)` - Migrate imports in a single file.

#### `scripts/utilities/restore_custom_periods.py`
**Functions:**
- ✅ `main()` - Main restoration function.
- ✅ `migrate_legacy_schedules_structure(schedules_data)` - Convert legacy flat schedule structure to new nested format.
- ✅ `restore_custom_periods()` - Restore custom periods from backup for all users.

#### `scripts/utilities/user_data_cli.py`
**Functions:**
- ✅ `cmd_backup_user(args)` - Create a backup of user data
- ✅ `cmd_index(args)` - Manage user index
- ✅ `cmd_list_users(args)` - List all users with basic info
- ✅ `cmd_summary(args)` - Show user data summary
- ✅ `cmd_update_references(args)` - Update message references for a user
- ✅ `format_size(size_bytes)` - Format bytes to human readable format
- ✅ `main()` - Main entry point for the module

### `tasks/` - Task Management

#### `tasks/task_management.py`
**Functions:**
- ✅ `are_tasks_enabled(user_id)` - Check if task management is enabled for a user.
- ✅ `complete_task(user_id, task_id)` - Mark a task as completed.
- ✅ `create_task(user_id, title, description, due_date, due_time, priority, category, reminder_periods)` - Create a new task for a user.
- ✅ `delete_task(user_id, task_id)` - Delete a task (permanently remove it).
- ✅ `ensure_task_directory(user_id)` - Ensure the task directory structure exists for a user.
- ✅ `get_task_by_id(user_id, task_id)` - Get a specific task by ID.
- ✅ `get_tasks_due_soon(user_id, days_ahead)` - Get tasks due within the specified number of days.
- ✅ `get_user_task_stats(user_id)` - Get task statistics for a user.
- ✅ `load_active_tasks(user_id)` - Load active tasks for a user.
- ✅ `load_completed_tasks(user_id)` - Load completed tasks for a user.
- ✅ `save_active_tasks(user_id, tasks)` - Save active tasks for a user.
- ✅ `save_completed_tasks(user_id, tasks)` - Save completed tasks for a user.
- ✅ `update_task(user_id, task_id, updates)` - Update an existing task.
**Classes:**
- ✅ `TaskManagementError` - Custom exception for task management errors.

### `tests/` - Test Files

#### `tests/behavior/test_account_management_real_behavior.py`
**Functions:**
- ✅ `cleanup_test_environment(test_dir)` - Clean up test environment
- ✅ `create_test_user_data(user_id, test_data_dir, base_state)` - Create test user data with specific base state
- ✅ `main()` - Run all real behavior tests
- ✅ `setup_test_environment(test_data_dir)` - Create isolated test environment with temporary directories
- ✅ `test_category_management_real_behavior(test_data_dir)` - Test actual category management with message file operations
- ✅ `test_data_consistency_real_behavior(test_data_dir)` - Test data consistency across multiple operations
- ✅ `test_feature_enablement_real_behavior(test_data_dir)` - Test actual feature enablement with file creation/deletion
- ✅ `test_integration_scenarios_real_behavior(test_data_dir)` - Test complex integration scenarios with multiple operations
- ✅ `test_schedule_period_management_real_behavior(test_data_dir)` - Test actual schedule period management with file persistence
- ✅ `test_user_data_loading_real_behavior(test_data_dir)` - Test actual user data loading with file verification

#### `tests/behavior/test_communication_behavior.py`
**Functions:**
- ✅ `comm_manager(self)` - Create a CommunicationManager instance for testing.
- ✅ `mock_channel_config(self)` - Create a mock channel configuration.
- ✅ `realistic_mock_channel(self)` - Create a realistic mock channel with proper async methods.
- ✅ `temp_dir(self)` - Create a temporary directory for testing.
- ✅ `test_communication_manager_error_handling(self, comm_manager, realistic_mock_channel)` - Test error handling in communication manager.
- ✅ `test_communication_manager_initialization(self, comm_manager)` - Test CommunicationManager initialization.
- ✅ `test_communication_manager_singleton(self, comm_manager)` - Test that CommunicationManager follows singleton pattern.
- ✅ `test_get_available_channels(self, comm_manager, realistic_mock_channel)` - Test getting available channels with realistic channel setup.
- ✅ `test_initialize_channels_from_config(self, mock_factory, comm_manager, mock_channel_config, realistic_mock_channel)` - Test channel initialization from configuration with realistic channel behavior.
- ✅ `test_is_channel_ready_with_realistic_channel(self, comm_manager, realistic_mock_channel)` - Test checking if a channel is ready with realistic channel behavior.
- ✅ `test_legacy_channel_wrapper_method_delegation(self, realistic_mock_channel)` - Test that LegacyChannelWrapper properly delegates methods to base channel.
- ✅ `test_legacy_channel_wrapper_with_realistic_channel(self, realistic_mock_channel)` - Test LegacyChannelWrapper functionality with realistic channel behavior.
- ✅ `test_send_message_sync_channel_not_found(self, comm_manager)` - Test synchronous message sending when channel doesn't exist.
- ✅ `test_send_message_sync_channel_not_ready(self, comm_manager, realistic_mock_channel)` - Test synchronous message sending when channel is not ready.
- ✅ `test_send_message_sync_with_realistic_channel(self, comm_manager, realistic_mock_channel)` - Test synchronous message sending with realistic channel behavior.
**Classes:**
- ✅ `TestCommunicationManager` - Test cases for the CommunicationManager class.
  - ✅ `TestCommunicationManager.comm_manager(self)` - Create a CommunicationManager instance for testing.
  - ✅ `TestCommunicationManager.mock_channel_config(self)` - Create a mock channel configuration.
  - ✅ `TestCommunicationManager.realistic_mock_channel(self)` - Create a realistic mock channel with proper async methods.
  - ✅ `TestCommunicationManager.temp_dir(self)` - Create a temporary directory for testing.
  - ✅ `TestCommunicationManager.test_communication_manager_error_handling(self, comm_manager, realistic_mock_channel)` - Test error handling in communication manager.
  - ✅ `TestCommunicationManager.test_communication_manager_initialization(self, comm_manager)` - Test CommunicationManager initialization.
  - ✅ `TestCommunicationManager.test_communication_manager_singleton(self, comm_manager)` - Test that CommunicationManager follows singleton pattern.
  - ✅ `TestCommunicationManager.test_get_available_channels(self, comm_manager, realistic_mock_channel)` - Test getting available channels with realistic channel setup.
  - ✅ `TestCommunicationManager.test_initialize_channels_from_config(self, mock_factory, comm_manager, mock_channel_config, realistic_mock_channel)` - Test channel initialization from configuration with realistic channel behavior.
  - ✅ `TestCommunicationManager.test_is_channel_ready_with_realistic_channel(self, comm_manager, realistic_mock_channel)` - Test checking if a channel is ready with realistic channel behavior.
  - ✅ `TestCommunicationManager.test_legacy_channel_wrapper_method_delegation(self, realistic_mock_channel)` - Test that LegacyChannelWrapper properly delegates methods to base channel.
  - ✅ `TestCommunicationManager.test_legacy_channel_wrapper_with_realistic_channel(self, realistic_mock_channel)` - Test LegacyChannelWrapper functionality with realistic channel behavior.
  - ✅ `TestCommunicationManager.test_send_message_sync_channel_not_found(self, comm_manager)` - Test synchronous message sending when channel doesn't exist.
  - ✅ `TestCommunicationManager.test_send_message_sync_channel_not_ready(self, comm_manager, realistic_mock_channel)` - Test synchronous message sending when channel is not ready.
  - ✅ `TestCommunicationManager.test_send_message_sync_with_realistic_channel(self, comm_manager, realistic_mock_channel)` - Test synchronous message sending with realistic channel behavior.

#### `tests/behavior/test_message_behavior.py`
**Functions:**
- ✅ `test_add_message_file_error(self, test_data_dir)` - Test add_message handles file errors gracefully.
- ✅ `test_add_message_success(self, test_data_dir)` - Test adding a message successfully.
- ✅ `test_create_message_file_from_defaults_success(self, test_data_dir)` - Test creating message file from defaults successfully.
- ✅ `test_delete_message_file_error(self, test_data_dir)` - Test delete_message handles file errors gracefully.
- ✅ `test_delete_message_not_found(self, test_data_dir)` - Test deleting a message that doesn't exist.
- ✅ `test_delete_message_success(self, test_data_dir)` - Test deleting a message successfully.
- ✅ `test_edit_message_file_error(self, test_data_dir)` - Test edit_message handles file errors gracefully.
- ✅ `test_edit_message_not_found(self, test_data_dir)` - Test editing a message that doesn't exist.
- ✅ `test_edit_message_success(self, test_data_dir)` - Test editing a message successfully.
- ✅ `test_ensure_user_message_files_success(self, test_data_dir)` - Test ensuring user message files exist successfully.
- ✅ `test_full_message_lifecycle(self, test_data_dir)` - Test complete message lifecycle (add, edit, delete).
- ✅ `test_get_last_10_messages_empty(self, test_data_dir)` - Test getting last 10 messages when none exist.
- ✅ `test_get_last_10_messages_success(self, test_data_dir)` - Test getting last 10 sent messages successfully.
- ✅ `test_get_message_categories_custom(self)` - Test getting custom message categories.
- ✅ `test_get_message_categories_default(self)` - Test getting default message categories.
- ✅ `test_get_message_categories_empty(self)` - Test getting message categories when none are defined.
- ✅ `test_get_message_categories_success(self)` - Test getting message categories successfully.
- ✅ `test_load_default_messages_file_not_found(self, test_data_dir, mock_config)` - Test loading default messages when file doesn't exist.
- ✅ `test_load_default_messages_invalid_json(self, test_data_dir, mock_config)` - Test loading default messages with invalid JSON.
- ✅ `test_load_default_messages_success(self, test_data_dir)` - Test loading default messages successfully.
- ✅ `test_store_sent_message_file_error(self, test_data_dir)` - Test store_sent_message handles file errors gracefully.
- ✅ `test_store_sent_message_success(self, test_data_dir)` - Test storing a sent message successfully.
- ✅ `test_update_message_success(self, test_data_dir)` - Test updating a message successfully.
**Classes:**
- ✅ `TestDefaultMessages` - Test default message loading functionality.
  - ✅ `TestDefaultMessages.test_load_default_messages_file_not_found(self, test_data_dir, mock_config)` - Test loading default messages when file doesn't exist.
  - ✅ `TestDefaultMessages.test_load_default_messages_invalid_json(self, test_data_dir, mock_config)` - Test loading default messages with invalid JSON.
  - ✅ `TestDefaultMessages.test_load_default_messages_success(self, test_data_dir)` - Test loading default messages successfully.
- ✅ `TestErrorHandling` - Test error handling in message management functions.
  - ✅ `TestErrorHandling.test_add_message_file_error(self, test_data_dir)` - Test add_message handles file errors gracefully.
  - ✅ `TestErrorHandling.test_delete_message_file_error(self, test_data_dir)` - Test delete_message handles file errors gracefully.
  - ✅ `TestErrorHandling.test_edit_message_file_error(self, test_data_dir)` - Test edit_message handles file errors gracefully.
  - ✅ `TestErrorHandling.test_store_sent_message_file_error(self, test_data_dir)` - Test store_sent_message handles file errors gracefully.
- ✅ `TestIntegration` - Test integration between message management functions.
  - ✅ `TestIntegration.test_full_message_lifecycle(self, test_data_dir)` - Test complete message lifecycle (add, edit, delete).
- ✅ `TestMessageCRUD` - Test message CRUD operations.
  - ✅ `TestMessageCRUD.test_add_message_success(self, test_data_dir)` - Test adding a message successfully.
  - ✅ `TestMessageCRUD.test_delete_message_not_found(self, test_data_dir)` - Test deleting a message that doesn't exist.
  - ✅ `TestMessageCRUD.test_delete_message_success(self, test_data_dir)` - Test deleting a message successfully.
  - ✅ `TestMessageCRUD.test_edit_message_not_found(self, test_data_dir)` - Test editing a message that doesn't exist.
  - ✅ `TestMessageCRUD.test_edit_message_success(self, test_data_dir)` - Test editing a message successfully.
  - ✅ `TestMessageCRUD.test_update_message_success(self, test_data_dir)` - Test updating a message successfully.
- ✅ `TestMessageCategories` - Test message category functionality.
  - ✅ `TestMessageCategories.test_get_message_categories_custom(self)` - Test getting custom message categories.
  - ✅ `TestMessageCategories.test_get_message_categories_default(self)` - Test getting default message categories.
  - ✅ `TestMessageCategories.test_get_message_categories_empty(self)` - Test getting message categories when none are defined.
  - ✅ `TestMessageCategories.test_get_message_categories_success(self)` - Test getting message categories successfully.
- ✅ `TestMessageFileManagement` - Test message file creation and management.
  - ✅ `TestMessageFileManagement.test_create_message_file_from_defaults_success(self, test_data_dir)` - Test creating message file from defaults successfully.
  - ✅ `TestMessageFileManagement.test_ensure_user_message_files_success(self, test_data_dir)` - Test ensuring user message files exist successfully.
- ✅ `TestSentMessages` - Test sent message tracking functionality.
  - ✅ `TestSentMessages.test_get_last_10_messages_empty(self, test_data_dir)` - Test getting last 10 messages when none exist.
  - ✅ `TestSentMessages.test_get_last_10_messages_success(self, test_data_dir)` - Test getting last 10 sent messages successfully.
  - ✅ `TestSentMessages.test_store_sent_message_success(self, test_data_dir)` - Test storing a sent message successfully.

#### `tests/behavior/test_scheduler_behavior.py`
**Functions:**
- ✅ `mock_communication_manager()` - Create a mock communication manager.
- ✅ `scheduler_manager(self, mock_communication_manager)` - Create a SchedulerManager instance for testing.
- ✅ `test_cleanup_old_tasks(self, scheduler_manager, test_data_dir)` - Test cleaning up old scheduled tasks.
- ✅ `test_cleanup_task_reminders_specific_task(self)` - Test cleaning up specific task reminders.
- ✅ `test_cleanup_task_reminders_success(self)` - Test cleaning up task reminders.
- ✅ `test_get_random_time_within_period_invalid_times(self, scheduler_manager)` - Test getting random time with invalid time format.
- ✅ `test_get_random_time_within_period_valid_times(self, scheduler_manager)` - Test getting random time within a valid time period.
- ✅ `test_get_user_categories_no_user(self)` - Test getting categories for non-existent user.
- ✅ `test_get_user_categories_success(self, mock_user_data)` - Test getting user categories successfully.
- ✅ `test_get_user_checkin_preferences_no_user(self)` - Test getting check-in preferences for non-existent user.
- ✅ `test_get_user_checkin_preferences_success(self, mock_user_data)` - Test getting user check-in preferences successfully.
- ✅ `test_get_user_task_preferences_no_user(self)` - Test getting task preferences for non-existent user.
- ✅ `test_get_user_task_preferences_success(self, mock_user_data)` - Test getting user task preferences successfully.
- ✅ `test_is_job_for_category_no_jobs(self, scheduler_manager)` - Test checking for jobs when no jobs exist.
- ✅ `test_is_job_for_category_with_matching_job(self, scheduler_manager)` - Test checking for jobs when a matching job exists.
- ✅ `test_is_job_for_category_with_non_matching_job(self, scheduler_manager)` - Test checking for jobs when no matching job exists.
- ✅ `test_is_time_conflict_no_conflicts(self, scheduler_manager)` - Test time conflict detection when no conflicts exist.
- ✅ `test_log_scheduled_tasks(self, scheduler_manager)` - Test logging of scheduled tasks.
- ✅ `test_random_time_generation_consistency(self, mock_communication_manager)` - Test that random time generation is consistent within bounds.
- ✅ `test_schedule_all_task_reminders_disabled(self, test_data_dir)` - Test scheduling task reminders when task management is disabled.
- ✅ `test_schedule_all_task_reminders_success(self, test_data_dir)` - Test scheduling all task reminders for a user.
- ✅ `test_scheduler_lifecycle(self, mock_communication_manager, test_data_dir)` - Test complete scheduler lifecycle.
- ✅ `test_scheduler_manager_initialization(self, mock_communication_manager)` - Test SchedulerManager initialization.
- ✅ `test_scheduler_with_empty_user_list(self, mock_communication_manager)` - Test scheduler behavior with no users.
- ✅ `test_scheduler_with_invalid_user_data(self, mock_communication_manager)` - Test scheduler behavior with invalid user data.
- ✅ `test_scheduler_with_mock_users(self, mock_communication_manager)` - Test scheduler with mock user data.
- ✅ `test_stop_scheduler_no_thread(self, scheduler_manager)` - Test stopping scheduler when no thread is running.
**Classes:**
- ✅ `TestSchedulerEdgeCases` - Test scheduler edge cases and error conditions.
  - ✅ `TestSchedulerEdgeCases.test_random_time_generation_consistency(self, mock_communication_manager)` - Test that random time generation is consistent within bounds.
  - ✅ `TestSchedulerEdgeCases.test_scheduler_with_empty_user_list(self, mock_communication_manager)` - Test scheduler behavior with no users.
  - ✅ `TestSchedulerEdgeCases.test_scheduler_with_invalid_user_data(self, mock_communication_manager)` - Test scheduler behavior with invalid user data.
- ✅ `TestSchedulerFunctions` - Test standalone scheduler functions.
  - ✅ `TestSchedulerFunctions.test_get_user_categories_no_user(self)` - Test getting categories for non-existent user.
  - ✅ `TestSchedulerFunctions.test_get_user_categories_success(self, mock_user_data)` - Test getting user categories successfully.
  - ✅ `TestSchedulerFunctions.test_get_user_checkin_preferences_no_user(self)` - Test getting check-in preferences for non-existent user.
  - ✅ `TestSchedulerFunctions.test_get_user_checkin_preferences_success(self, mock_user_data)` - Test getting user check-in preferences successfully.
  - ✅ `TestSchedulerFunctions.test_get_user_task_preferences_no_user(self)` - Test getting task preferences for non-existent user.
  - ✅ `TestSchedulerFunctions.test_get_user_task_preferences_success(self, mock_user_data)` - Test getting user task preferences successfully.
- ✅ `TestSchedulerIntegration` - Test scheduler integration scenarios.
  - ✅ `TestSchedulerIntegration.test_scheduler_lifecycle(self, mock_communication_manager, test_data_dir)` - Test complete scheduler lifecycle.
  - ✅ `TestSchedulerIntegration.test_scheduler_with_mock_users(self, mock_communication_manager)` - Test scheduler with mock user data.
- ✅ `TestSchedulerManager` - Test SchedulerManager functionality.
  - ✅ `TestSchedulerManager.scheduler_manager(self, mock_communication_manager)` - Create a SchedulerManager instance for testing.
  - ✅ `TestSchedulerManager.test_cleanup_old_tasks(self, scheduler_manager, test_data_dir)` - Test cleaning up old scheduled tasks.
  - ✅ `TestSchedulerManager.test_get_random_time_within_period_invalid_times(self, scheduler_manager)` - Test getting random time with invalid time format.
  - ✅ `TestSchedulerManager.test_get_random_time_within_period_valid_times(self, scheduler_manager)` - Test getting random time within a valid time period.
  - ✅ `TestSchedulerManager.test_is_job_for_category_no_jobs(self, scheduler_manager)` - Test checking for jobs when no jobs exist.
  - ✅ `TestSchedulerManager.test_is_job_for_category_with_matching_job(self, scheduler_manager)` - Test checking for jobs when a matching job exists.
  - ✅ `TestSchedulerManager.test_is_job_for_category_with_non_matching_job(self, scheduler_manager)` - Test checking for jobs when no matching job exists.
  - ✅ `TestSchedulerManager.test_is_time_conflict_no_conflicts(self, scheduler_manager)` - Test time conflict detection when no conflicts exist.
  - ✅ `TestSchedulerManager.test_log_scheduled_tasks(self, scheduler_manager)` - Test logging of scheduled tasks.
  - ✅ `TestSchedulerManager.test_scheduler_manager_initialization(self, mock_communication_manager)` - Test SchedulerManager initialization.
  - ✅ `TestSchedulerManager.test_stop_scheduler_no_thread(self, scheduler_manager)` - Test stopping scheduler when no thread is running.
- ✅ `TestTaskReminderFunctions` - Test task reminder specific functions.
  - ✅ `TestTaskReminderFunctions.test_cleanup_task_reminders_specific_task(self)` - Test cleaning up specific task reminders.
  - ✅ `TestTaskReminderFunctions.test_cleanup_task_reminders_success(self)` - Test cleaning up task reminders.
  - ✅ `TestTaskReminderFunctions.test_schedule_all_task_reminders_disabled(self, test_data_dir)` - Test scheduling task reminders when task management is disabled.
  - ✅ `TestTaskReminderFunctions.test_schedule_all_task_reminders_success(self, test_data_dir)` - Test scheduling all task reminders for a user.

#### `tests/behavior/test_service_behavior.py`
**Functions:**
- ❌ `mock_get_user_data_side_effect(user_id, data_type)` - No description
- ✅ `mock_join_side_effect()` - Mock side effect for os.path.join that returns test file path.

Returns the test request file path when the specific filename
is requested, otherwise delegates to the real os.path.join.

Args:
    *args: Path components to join
    
Returns:
    str: Joined path, or test file path for specific filename
- ✅ `mock_join_side_effect()` - Mock side effect for os.path.join that returns test file path.

Returns the test request file path when the specific filename
is requested, otherwise delegates to the real os.path.join.

Args:
    *args: Path components to join
    
Returns:
    str: Joined path, or test file path for specific filename
- ✅ `mock_shutdown_side_effect()` - Mock side effect for service shutdown that changes actual service state.

Updates the service running status and calls stop methods on managers
to simulate real service shutdown behavior for testing.
- ✅ `mock_sleep_side_effect(seconds)` - Mock side effect for time.sleep that breaks out of service loop.

Tracks call count and stops the service after a few iterations
to prevent infinite loops during testing.

Args:
    seconds: Number of seconds to sleep (ignored in mock)
- ✅ `mock_start_side_effect()` - Mock side effect for service start that changes actual service state.

Updates the service running status and startup time to simulate
real service startup behavior for testing.
- ✅ `service(self)` - Create an MHMService instance for testing.
- ✅ `temp_base_dir(self)` - Create a temporary base directory for file-based communication tests.
- ✅ `temp_dir(self)` - Create a temporary directory for testing.
- ✅ `test_check_and_fix_logging_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test logging health check with real file operations.
- ✅ `test_check_reschedule_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test processing of reschedule request files with real file operations.
- ✅ `test_check_test_message_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test processing of test message request files with real file operations.
- ✅ `test_cleanup_reschedule_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test cleanup of reschedule request files with real file operations.
- ✅ `test_cleanup_test_message_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test cleanup of test message request files with real file operations.
- ✅ `test_emergency_shutdown_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test emergency shutdown with real state changes.
- ✅ `test_get_user_categories_real_behavior(self)` - REAL BEHAVIOR TEST: Test get_user_categories with real data structures.
- ✅ `test_initialize_paths_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test path initialization with real file system operations.
- ✅ `test_main_function_real_behavior(self)` - REAL BEHAVIOR TEST: Test main function with real service creation.
- ✅ `test_real_cleanup_removes_actual_files(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Verify that cleanup actually removes real files.
- ✅ `test_real_emergency_shutdown_changes_service_state(self)` - REAL BEHAVIOR TEST: Verify that emergency shutdown actually changes service state.
- ✅ `test_real_file_based_communication_creates_and_removes_files(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Verify that test message requests actually create and remove files.
- ✅ `test_real_get_user_categories_returns_actual_data(self)` - REAL BEHAVIOR TEST: Verify that get_user_categories returns actual data structures.
- ✅ `test_real_service_error_recovery_stops_service(self)` - REAL BEHAVIOR TEST: Verify that error recovery actually stops the service.
- ✅ `test_real_service_initialization_creates_actual_service(self)` - REAL BEHAVIOR TEST: Verify that service initialization creates a real service object.
- ✅ `test_real_signal_handler_changes_service_state(self)` - REAL BEHAVIOR TEST: Verify that signal handler actually changes service state.
- ✅ `test_run_service_loop_shutdown_file_detection_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test service loop detects shutdown request file with real file operations.
- ✅ `test_service_error_recovery_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service error recovery with real state changes.
- ✅ `test_service_file_based_communication_integration_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test service file-based communication integration with real file operations.
- ✅ `test_service_initialization(self, service)` - Test MHMService initialization.
- ✅ `test_service_integration_with_managers_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service integration with real manager objects.
- ✅ `test_service_loop_heartbeat_logging_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service loop heartbeat logging with real state management.
- ✅ `test_shutdown_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service shutdown with real state changes.
- ✅ `test_signal_handler_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test signal handler with real state changes.
- ✅ `test_start_service_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service startup with real state changes.
- ✅ `test_validate_configuration_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test configuration validation with real file operations.
**Classes:**
- ✅ `TestMHMService` - Test cases for the MHMService class.
  - ✅ `TestMHMService.service(self)` - Create an MHMService instance for testing.
  - ✅ `TestMHMService.temp_base_dir(self)` - Create a temporary base directory for file-based communication tests.
  - ✅ `TestMHMService.temp_dir(self)` - Create a temporary directory for testing.
  - ✅ `TestMHMService.test_check_and_fix_logging_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test logging health check with real file operations.
  - ✅ `TestMHMService.test_check_reschedule_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test processing of reschedule request files with real file operations.
  - ✅ `TestMHMService.test_check_test_message_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test processing of test message request files with real file operations.
  - ✅ `TestMHMService.test_cleanup_reschedule_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test cleanup of reschedule request files with real file operations.
  - ✅ `TestMHMService.test_cleanup_test_message_requests_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test cleanup of test message request files with real file operations.
  - ✅ `TestMHMService.test_emergency_shutdown_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test emergency shutdown with real state changes.
  - ✅ `TestMHMService.test_get_user_categories_real_behavior(self)` - REAL BEHAVIOR TEST: Test get_user_categories with real data structures.
  - ✅ `TestMHMService.test_initialize_paths_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test path initialization with real file system operations.
  - ✅ `TestMHMService.test_main_function_real_behavior(self)` - REAL BEHAVIOR TEST: Test main function with real service creation.
  - ✅ `TestMHMService.test_real_cleanup_removes_actual_files(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Verify that cleanup actually removes real files.
  - ✅ `TestMHMService.test_real_emergency_shutdown_changes_service_state(self)` - REAL BEHAVIOR TEST: Verify that emergency shutdown actually changes service state.
  - ✅ `TestMHMService.test_real_file_based_communication_creates_and_removes_files(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Verify that test message requests actually create and remove files.
  - ✅ `TestMHMService.test_real_get_user_categories_returns_actual_data(self)` - REAL BEHAVIOR TEST: Verify that get_user_categories returns actual data structures.
  - ✅ `TestMHMService.test_real_service_error_recovery_stops_service(self)` - REAL BEHAVIOR TEST: Verify that error recovery actually stops the service.
  - ✅ `TestMHMService.test_real_service_initialization_creates_actual_service(self)` - REAL BEHAVIOR TEST: Verify that service initialization creates a real service object.
  - ✅ `TestMHMService.test_real_signal_handler_changes_service_state(self)` - REAL BEHAVIOR TEST: Verify that signal handler actually changes service state.
  - ✅ `TestMHMService.test_run_service_loop_shutdown_file_detection_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test service loop detects shutdown request file with real file operations.
  - ✅ `TestMHMService.test_service_error_recovery_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service error recovery with real state changes.
  - ✅ `TestMHMService.test_service_file_based_communication_integration_real_behavior(self, temp_base_dir, service)` - REAL BEHAVIOR TEST: Test service file-based communication integration with real file operations.
  - ✅ `TestMHMService.test_service_initialization(self, service)` - Test MHMService initialization.
  - ✅ `TestMHMService.test_service_integration_with_managers_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service integration with real manager objects.
  - ✅ `TestMHMService.test_service_loop_heartbeat_logging_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service loop heartbeat logging with real state management.
  - ✅ `TestMHMService.test_shutdown_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service shutdown with real state changes.
  - ✅ `TestMHMService.test_signal_handler_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test signal handler with real state changes.
  - ✅ `TestMHMService.test_start_service_real_behavior(self, service)` - REAL BEHAVIOR TEST: Test service startup with real state changes.
  - ✅ `TestMHMService.test_validate_configuration_real_behavior(self, temp_dir, service)` - REAL BEHAVIOR TEST: Test configuration validation with real file operations.

#### `tests/behavior/test_task_behavior.py`
**Functions:**
- ✅ `temp_dir(self)` - Create a temporary directory for testing.
- ✅ `test_are_tasks_enabled(self, mock_get_user_data)` - Test checking if tasks are enabled with mock user data.
- ✅ `test_complete_task(self, mock_get_user_dir, temp_dir)` - Test task completion with file and side effect verification.
- ✅ `test_create_task(self, mock_get_user_dir, temp_dir)` - Test task creation with file verification.
- ✅ `test_delete_task(self, mock_get_user_dir, temp_dir)` - Test task deletion with file verification.
- ✅ `test_ensure_task_directory(self, mock_get_user_dir, user_id, temp_dir)` - Test task directory creation.
- ✅ `test_get_task_by_id(self, mock_get_user_dir, temp_dir)` - Test getting a task by ID with file verification.
- ✅ `test_get_tasks_due_soon(self, mock_get_user_dir, temp_dir)` - Test getting tasks due soon with file verification.
- ✅ `test_get_user_task_stats(self, mock_get_user_dir, temp_dir)` - Test getting user task statistics with file verification.
- ✅ `test_load_active_tasks(self, mock_get_user_dir, user_id, temp_dir)` - Test loading active tasks.
- ✅ `test_save_active_tasks(self, mock_get_user_dir, user_id, temp_dir)` - Test saving active tasks.
- ✅ `test_update_task(self, mock_get_user_dir, temp_dir)` - Test task updating with file verification.
- ✅ `user_id(self)` - Create a test user ID.
**Classes:**
- ✅ `TestTaskManagement` - Test cases for task management functions.
  - ✅ `TestTaskManagement.temp_dir(self)` - Create a temporary directory for testing.
  - ✅ `TestTaskManagement.test_are_tasks_enabled(self, mock_get_user_data)` - Test checking if tasks are enabled with mock user data.
  - ✅ `TestTaskManagement.test_complete_task(self, mock_get_user_dir, temp_dir)` - Test task completion with file and side effect verification.
  - ✅ `TestTaskManagement.test_create_task(self, mock_get_user_dir, temp_dir)` - Test task creation with file verification.
  - ✅ `TestTaskManagement.test_delete_task(self, mock_get_user_dir, temp_dir)` - Test task deletion with file verification.
  - ✅ `TestTaskManagement.test_ensure_task_directory(self, mock_get_user_dir, user_id, temp_dir)` - Test task directory creation.
  - ✅ `TestTaskManagement.test_get_task_by_id(self, mock_get_user_dir, temp_dir)` - Test getting a task by ID with file verification.
  - ✅ `TestTaskManagement.test_get_tasks_due_soon(self, mock_get_user_dir, temp_dir)` - Test getting tasks due soon with file verification.
  - ✅ `TestTaskManagement.test_get_user_task_stats(self, mock_get_user_dir, temp_dir)` - Test getting user task statistics with file verification.
  - ✅ `TestTaskManagement.test_load_active_tasks(self, mock_get_user_dir, user_id, temp_dir)` - Test loading active tasks.
  - ✅ `TestTaskManagement.test_save_active_tasks(self, mock_get_user_dir, user_id, temp_dir)` - Test saving active tasks.
  - ✅ `TestTaskManagement.test_update_task(self, mock_get_user_dir, temp_dir)` - Test task updating with file verification.
  - ✅ `TestTaskManagement.user_id(self)` - Create a test user ID.

#### `tests/conftest.py`
**Functions:**
- ❌ `_update_index(user_id)` - No description
- ✅ `cleanup_test_users_after_session()` - Remove test users from both data/users/ and tests/data/users/ after all tests.
- ✅ `isolate_logging()` - Ensure complete logging isolation during tests to prevent test logs from appearing in main app.log.
- ✅ `mock_ai_response()` - Mock AI response for testing.
- ✅ `mock_communication_data()` - Mock communication data for testing.
- ✅ `mock_config(test_data_dir)` - Mock configuration for testing with proper test data directory.
- ✅ `mock_logger()` - Mock logger for testing.
- ✅ `mock_message_data()` - Mock message data for testing.
- ✅ `mock_schedule_data()` - Mock schedule data for testing.
- ✅ `mock_service_data()` - Mock service data for testing.
- ✅ `mock_task_data()` - Mock task data for testing.
- ✅ `mock_user_data(test_data_dir, mock_config, request)` - Create mock user data for testing with unique user ID for each test.
- ✅ `mock_user_data_with_messages(test_data_dir, mock_config, request)` - Create mock user data for testing with automated_messages enabled and categories.
- ✅ `patch_user_data_dirs()` - Patch BASE_DATA_DIR and USER_INFO_DIR_PATH to use tests/data/users/ for all tests.
- ✅ `pytest_collection_modifyitems(config, items)` - Modify test collection to add default markers.
- ✅ `pytest_configure(config)` - Configure pytest for MHM testing.
- ✅ `pytest_runtest_logreport(report)` - Log individual test results.
- ✅ `pytest_sessionfinish(session, exitstatus)` - Log test session finish.
- ✅ `pytest_sessionstart(session)` - Log test session start.
- ✅ `setup_logging_isolation()` - Set up logging isolation before any core modules are imported.
- ✅ `setup_test_logging()` - Set up dedicated logging for tests with complete isolation from main app logging.
- ✅ `temp_file()` - Create a temporary file for testing.
- ✅ `test_data_dir()` - Create a temporary test data directory for all tests.
- ✅ `update_user_index_for_test(test_data_dir)` - Helper fixture to update user index for test users.

#### `tests/integration/test_account_lifecycle.py`
**Functions:**
- ✅ `save_user_data_simple(self, user_id, account_data, preferences_data, schedules_data)` - Helper function to save user data in the correct format.
- ✅ `setup_test_environment(self)` - Set up isolated test environment for each test.
- ✅ `test_add_message_category(self, test_data_dir, mock_config, update_user_index_for_test)` - Test adding a new message category to user preferences.
- ✅ `test_add_schedule_period(self, test_data_dir, mock_config)` - Test adding a new schedule period to user schedules.
- ✅ `test_complete_account_lifecycle(self, test_data_dir, mock_config)` - Test complete account lifecycle: create, modify, disable, re-enable, delete.
- ✅ `test_create_basic_account(self, test_data_dir, mock_config)` - Test creating a basic account with only messages enabled.
- ✅ `test_create_full_account(self, test_data_dir, mock_config)` - Test creating a full account with all features enabled.
- ✅ `test_disable_tasks_for_full_user(self, test_data_dir, mock_config)` - Test disabling tasks for a user who has all features enabled.
- ✅ `test_enable_checkins_for_basic_user(self, test_data_dir, mock_config)` - Test enabling check-ins for a user who only has messages enabled.
- ✅ `test_modify_schedule_period(self, test_data_dir, mock_config)` - Test modifying an existing schedule period.
- ✅ `test_reenable_tasks_for_user(self, test_data_dir, mock_config)` - Test re-enabling tasks for a user who previously had them disabled.
- ✅ `test_remove_message_category(self, test_data_dir, mock_config)` - Test removing a message category from user preferences.
- ✅ `test_remove_schedule_period(self, test_data_dir, mock_config)` - Test removing a schedule period from user schedules.
**Classes:**
- ✅ `TestAccountLifecycle` - Test complete account lifecycle workflows with real behavior verification.
  - ✅ `TestAccountLifecycle.save_user_data_simple(self, user_id, account_data, preferences_data, schedules_data)` - Helper function to save user data in the correct format.
  - ✅ `TestAccountLifecycle.setup_test_environment(self)` - Set up isolated test environment for each test.
  - ✅ `TestAccountLifecycle.test_add_message_category(self, test_data_dir, mock_config, update_user_index_for_test)` - Test adding a new message category to user preferences.
  - ✅ `TestAccountLifecycle.test_add_schedule_period(self, test_data_dir, mock_config)` - Test adding a new schedule period to user schedules.
  - ✅ `TestAccountLifecycle.test_complete_account_lifecycle(self, test_data_dir, mock_config)` - Test complete account lifecycle: create, modify, disable, re-enable, delete.
  - ✅ `TestAccountLifecycle.test_create_basic_account(self, test_data_dir, mock_config)` - Test creating a basic account with only messages enabled.
  - ✅ `TestAccountLifecycle.test_create_full_account(self, test_data_dir, mock_config)` - Test creating a full account with all features enabled.
  - ✅ `TestAccountLifecycle.test_disable_tasks_for_full_user(self, test_data_dir, mock_config)` - Test disabling tasks for a user who has all features enabled.
  - ✅ `TestAccountLifecycle.test_enable_checkins_for_basic_user(self, test_data_dir, mock_config)` - Test enabling check-ins for a user who only has messages enabled.
  - ✅ `TestAccountLifecycle.test_modify_schedule_period(self, test_data_dir, mock_config)` - Test modifying an existing schedule period.
  - ✅ `TestAccountLifecycle.test_reenable_tasks_for_user(self, test_data_dir, mock_config)` - Test re-enabling tasks for a user who previously had them disabled.
  - ✅ `TestAccountLifecycle.test_remove_message_category(self, test_data_dir, mock_config)` - Test removing a message category from user preferences.
  - ✅ `TestAccountLifecycle.test_remove_schedule_period(self, test_data_dir, mock_config)` - Test removing a schedule period from user schedules.

#### `tests/integration/test_account_management.py`
**Functions:**
- ✅ `main()` - Run all account management tests and generate a comprehensive report
- ✅ `test_account_management_data_structures()` - Test that account management can handle the expected data structures
- ✅ `test_account_management_functions()` - Test that all account management functions can be called (with safe test data)
- ✅ `test_account_management_imports()` - Test that all account management modules can be imported without errors
- ✅ `test_account_management_integration()` - Test that account management integrates properly with other systems
- ✅ `test_account_management_safe_operations()` - Test account management operations with temporary test data
- ✅ `test_account_management_validation()` - Test that account management validation works correctly

#### `tests/integration/test_user_creation.py`
**Functions:**
- ✅ `test_basic_email_user_creation(self, test_data_dir, mock_config)` - Test creating a basic email user with minimal settings.
- ✅ `test_corrupted_data_handling(self, test_data_dir, mock_config)` - Test handling corrupted user data.
- ✅ `test_discord_user_creation(self, test_data_dir, mock_config)` - Test creating a Discord user with full features enabled.
- ✅ `test_duplicate_user_creation(self, test_data_dir, mock_config)` - Test creating a user that already exists.
- ✅ `test_email_validation(self)` - Test email validation.
- ✅ `test_full_user_lifecycle(self, test_data_dir, mock_config)` - Test complete user lifecycle: create, update, delete.
- ✅ `test_invalid_user_id(self, test_data_dir, mock_config)` - Test creating user with invalid user ID.
- ✅ `test_multiple_users_same_channel(self, test_data_dir, mock_config)` - Test creating multiple users with the same channel type.
- ✅ `test_required_fields_validation(self, test_data_dir, mock_config)` - Test that required fields are validated.
- ✅ `test_telegram_user_creation(self, test_data_dir, mock_config)` - Test creating a Telegram user with mixed features.
- ✅ `test_timezone_validation(self)` - Test timezone validation.
- ✅ `test_user_creation_with_schedules(self, test_data_dir, mock_config)` - Test creating a user with schedule periods.
- ✅ `test_user_with_all_features(self, test_data_dir, mock_config)` - Test creating a user with all possible features enabled.
- ✅ `test_user_with_custom_fields(self, test_data_dir, mock_config)` - Test creating a user with extensive custom fields.
- ✅ `test_username_validation(self)` - Test username validation.
**Classes:**
- ✅ `TestUserCreationErrorHandling` - Test error handling during user creation.
  - ✅ `TestUserCreationErrorHandling.test_corrupted_data_handling(self, test_data_dir, mock_config)` - Test handling corrupted user data.
  - ✅ `TestUserCreationErrorHandling.test_duplicate_user_creation(self, test_data_dir, mock_config)` - Test creating a user that already exists.
  - ✅ `TestUserCreationErrorHandling.test_invalid_user_id(self, test_data_dir, mock_config)` - Test creating user with invalid user ID.
- ✅ `TestUserCreationIntegration` - Test integration scenarios for user creation.
  - ✅ `TestUserCreationIntegration.test_full_user_lifecycle(self, test_data_dir, mock_config)` - Test complete user lifecycle: create, update, delete.
  - ✅ `TestUserCreationIntegration.test_multiple_users_same_channel(self, test_data_dir, mock_config)` - Test creating multiple users with the same channel type.
  - ✅ `TestUserCreationIntegration.test_user_with_all_features(self, test_data_dir, mock_config)` - Test creating a user with all possible features enabled.
- ✅ `TestUserCreationScenarios` - Test comprehensive user creation scenarios.
  - ✅ `TestUserCreationScenarios.test_basic_email_user_creation(self, test_data_dir, mock_config)` - Test creating a basic email user with minimal settings.
  - ✅ `TestUserCreationScenarios.test_discord_user_creation(self, test_data_dir, mock_config)` - Test creating a Discord user with full features enabled.
  - ✅ `TestUserCreationScenarios.test_telegram_user_creation(self, test_data_dir, mock_config)` - Test creating a Telegram user with mixed features.
  - ✅ `TestUserCreationScenarios.test_user_creation_with_schedules(self, test_data_dir, mock_config)` - Test creating a user with schedule periods.
  - ✅ `TestUserCreationScenarios.test_user_with_custom_fields(self, test_data_dir, mock_config)` - Test creating a user with extensive custom fields.
- ✅ `TestUserCreationValidation` - Test validation scenarios during user creation.
  - ✅ `TestUserCreationValidation.test_email_validation(self)` - Test email validation.
  - ✅ `TestUserCreationValidation.test_required_fields_validation(self, test_data_dir, mock_config)` - Test that required fields are validated.
  - ✅ `TestUserCreationValidation.test_timezone_validation(self)` - Test timezone validation.
  - ✅ `TestUserCreationValidation.test_username_validation(self)` - Test username validation.

#### `tests/task_management.py`

#### `tests/ui/test_account_creation_ui.py`
**Functions:**
- ✅ `dialog(self, qapp, test_data_dir, mock_config)` - Create account creation dialog for testing.
- ❌ `mock_accept_impl()` - No description
- ✅ `qapp()` - Create QApplication instance for UI testing.
- ✅ `test_account_creation_real_behavior(self, dialog, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test complete account creation workflow with real file operations.
- ✅ `test_dialog_initialization_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test dialog initializes correctly with proper UI state.
- ✅ `test_duplicate_username_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of duplicate usernames.
- ✅ `test_feature_enablement_persistence_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test that feature enablement is properly persisted.
- ✅ `test_feature_enablement_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test feature enablement checkboxes control tab visibility.
- ✅ `test_feature_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test feature validation with proper category requirements.
- ✅ `test_file_system_error_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of file system errors.
- ✅ `test_full_account_lifecycle_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test complete account lifecycle with real file operations.
- ✅ `test_invalid_data_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of invalid data during account creation.
- ✅ `test_messages_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test messages-specific validation when messages are enabled.
- ✅ `test_multiple_users_same_features_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test creating multiple users with same features.
- ✅ `test_timezone_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test timezone validation with real UI interactions.
- ✅ `test_user_index_integration_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test user index integration with real file operations.
- ✅ `test_user_profile_dialog_integration(self, qapp, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test integration with user profile dialog.
- ✅ `test_username_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test username validation with real UI interactions.
- ✅ `test_widget_data_collection_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test that widgets properly collect and return data.
- ✅ `test_widget_error_handling_real_behavior(self, qapp, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of widget errors during account creation.
**Classes:**
- ✅ `TestAccountCreationDialogRealBehavior` - Test account creation dialog with real behavior verification.
  - ✅ `TestAccountCreationDialogRealBehavior.dialog(self, qapp, test_data_dir, mock_config)` - Create account creation dialog for testing.
  - ✅ `TestAccountCreationDialogRealBehavior.test_account_creation_real_behavior(self, dialog, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test complete account creation workflow with real file operations.
  - ✅ `TestAccountCreationDialogRealBehavior.test_dialog_initialization_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test dialog initializes correctly with proper UI state.
  - ✅ `TestAccountCreationDialogRealBehavior.test_feature_enablement_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test feature enablement checkboxes control tab visibility.
  - ✅ `TestAccountCreationDialogRealBehavior.test_feature_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test feature validation with proper category requirements.
  - ✅ `TestAccountCreationDialogRealBehavior.test_messages_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test messages-specific validation when messages are enabled.
  - ✅ `TestAccountCreationDialogRealBehavior.test_timezone_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test timezone validation with real UI interactions.
  - ✅ `TestAccountCreationDialogRealBehavior.test_username_validation_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test username validation with real UI interactions.
  - ✅ `TestAccountCreationDialogRealBehavior.test_widget_data_collection_real_behavior(self, dialog, test_data_dir)` - REAL BEHAVIOR TEST: Test that widgets properly collect and return data.
- ✅ `TestAccountCreationErrorHandling` - Test error handling in account creation and management.
  - ✅ `TestAccountCreationErrorHandling.test_duplicate_username_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of duplicate usernames.
  - ✅ `TestAccountCreationErrorHandling.test_file_system_error_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of file system errors.
  - ✅ `TestAccountCreationErrorHandling.test_invalid_data_handling_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of invalid data during account creation.
  - ✅ `TestAccountCreationErrorHandling.test_widget_error_handling_real_behavior(self, qapp, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test handling of widget errors during account creation.
- ✅ `TestAccountCreationIntegration` - Test integration scenarios for account creation and management.
  - ✅ `TestAccountCreationIntegration.test_full_account_lifecycle_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test complete account lifecycle with real file operations.
  - ✅ `TestAccountCreationIntegration.test_multiple_users_same_features_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test creating multiple users with same features.
- ✅ `TestAccountManagementRealBehavior` - Test account management functionality with real behavior verification.
  - ✅ `TestAccountManagementRealBehavior.test_feature_enablement_persistence_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test that feature enablement is properly persisted.
  - ✅ `TestAccountManagementRealBehavior.test_user_index_integration_real_behavior(self, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test user index integration with real file operations.
  - ✅ `TestAccountManagementRealBehavior.test_user_profile_dialog_integration(self, qapp, test_data_dir, mock_config)` - REAL BEHAVIOR TEST: Test integration with user profile dialog.

#### `tests/ui/test_dialogs.py`
**Functions:**
- ✅ `main()` - Run all tests and generate a comprehensive report
- ❌ `mock_save(data)` - No description
- ✅ `test_dialog_imports()` - Test that all dialog modules can be imported without errors
- ✅ `test_dialog_instantiation()` - Test that dialogs can be instantiated (without showing them)
- ✅ `test_generated_files_exist()` - Test that all generated Python UI files exist
- ✅ `test_ui_files_exist()` - Test that all required UI files exist
- ✅ `test_user_data_access()` - Test that we can access user data for testing - READ ONLY
- ✅ `test_widget_imports()` - Test that all widget modules can be imported without errors

#### `tests/unit/test_cleanup.py`
**Functions:**
- ✅ `__init__(self, test_data_dir)` - Initialize the cleanup manager.
- ✅ `_cleanup_old_test_logs(self, keep_days)` - Clean up old test log files.
- ✅ `_cleanup_single_user(self, user_id)` - Clean up a single test user.
- ✅ `_cleanup_temp_files(self)` - Clean up temporary test files.
- ✅ `_create_user_backup(self, user_id, user_path)` - Create a backup of user data before cleanup.
- ✅ `_find_orphaned_files(self)` - Find orphaned files in the user directory.
- ✅ `_find_test_users(self)` - Find all test users in the user directory.
- ✅ `_validate_user_data(self, user_id, user_path)` - Validate a single user's data integrity.
- ✅ `cleanup_test_users(self, user_ids)` - Clean up test user data.

Args:
    user_ids: List of user IDs to clean up. If None, cleans up all test users.
    
Returns:
    bool: True if cleanup was successful, False otherwise.
- ✅ `main()` - Command-line interface for test cleanup.
- ✅ `reset_test_environment(self)` - Reset the entire test environment.
- ✅ `validate_test_data_integrity(self)` - Validate the integrity of test data.
**Classes:**
- ✅ `CleanupManager` - Manages test data cleanup and isolation.
  - ✅ `CleanupManager.__init__(self, test_data_dir)` - Initialize the cleanup manager.
  - ✅ `CleanupManager._cleanup_old_test_logs(self, keep_days)` - Clean up old test log files.
  - ✅ `CleanupManager._cleanup_single_user(self, user_id)` - Clean up a single test user.
  - ✅ `CleanupManager._cleanup_temp_files(self)` - Clean up temporary test files.
  - ✅ `CleanupManager._create_user_backup(self, user_id, user_path)` - Create a backup of user data before cleanup.
  - ✅ `CleanupManager._find_orphaned_files(self)` - Find orphaned files in the user directory.
  - ✅ `CleanupManager._find_test_users(self)` - Find all test users in the user directory.
  - ✅ `CleanupManager._validate_user_data(self, user_id, user_path)` - Validate a single user's data integrity.
  - ✅ `CleanupManager.cleanup_test_users(self, user_ids)` - Clean up test user data.

Args:
    user_ids: List of user IDs to clean up. If None, cleans up all test users.
    
Returns:
    bool: True if cleanup was successful, False otherwise.
  - ✅ `CleanupManager.reset_test_environment(self)` - Reset the entire test environment.
  - ✅ `CleanupManager.validate_test_data_integrity(self)` - Validate the integrity of test data.

#### `tests/unit/test_config.py`
**Functions:**
- ✅ `test_base_data_dir_default(self)` - Test BASE_DATA_DIR default value.
- ✅ `test_default_messages_dir_path_default(self)` - Test DEFAULT_MESSAGES_DIR_PATH default value.
- ✅ `test_environment_override(self)` - Test environment variable override.
- ✅ `test_user_info_dir_path_default(self)` - Test USER_INFO_DIR_PATH default value.
- ✅ `test_validate_ai_configuration_missing_url(self)` - Test AI configuration validation with missing URL.
- ✅ `test_validate_ai_configuration_success(self)` - Test successful AI configuration validation.
- ✅ `test_validate_all_configuration_success(self, test_data_dir)` - Test comprehensive configuration validation.
- ✅ `test_validate_and_raise_if_invalid_failure(self)` - Test validation failure raises ConfigurationError.
- ✅ `test_validate_and_raise_if_invalid_success(self, test_data_dir)` - Test successful validation with no exceptions.
- ✅ `test_validate_communication_channels_no_tokens(self)` - Test communication channels validation with no tokens.
- ✅ `test_validate_communication_channels_success(self)` - Test successful communication channels validation.
- ✅ `test_validate_core_paths_missing_directory(self)` - Test core path validation with missing directory.
- ✅ `test_validate_core_paths_success(self, test_data_dir)` - Test successful core path validation.
- ✅ `test_validate_environment_variables_success(self)` - Test successful environment variables validation.
- ✅ `test_validate_file_organization_settings_success(self)` - Test successful file organization settings validation.
- ✅ `test_validate_logging_configuration_success(self)` - Test successful logging configuration validation.
- ✅ `test_validate_scheduler_configuration_success(self)` - Test successful scheduler configuration validation.
**Classes:**
- ✅ `TestConfigConstants` - Test configuration constants.
  - ✅ `TestConfigConstants.test_base_data_dir_default(self)` - Test BASE_DATA_DIR default value.
  - ✅ `TestConfigConstants.test_default_messages_dir_path_default(self)` - Test DEFAULT_MESSAGES_DIR_PATH default value.
  - ✅ `TestConfigConstants.test_environment_override(self)` - Test environment variable override.
  - ✅ `TestConfigConstants.test_user_info_dir_path_default(self)` - Test USER_INFO_DIR_PATH default value.
- ✅ `TestConfigValidation` - Test configuration validation functions.
  - ✅ `TestConfigValidation.test_validate_ai_configuration_missing_url(self)` - Test AI configuration validation with missing URL.
  - ✅ `TestConfigValidation.test_validate_ai_configuration_success(self)` - Test successful AI configuration validation.
  - ✅ `TestConfigValidation.test_validate_all_configuration_success(self, test_data_dir)` - Test comprehensive configuration validation.
  - ✅ `TestConfigValidation.test_validate_and_raise_if_invalid_failure(self)` - Test validation failure raises ConfigurationError.
  - ✅ `TestConfigValidation.test_validate_and_raise_if_invalid_success(self, test_data_dir)` - Test successful validation with no exceptions.
  - ✅ `TestConfigValidation.test_validate_communication_channels_no_tokens(self)` - Test communication channels validation with no tokens.
  - ✅ `TestConfigValidation.test_validate_communication_channels_success(self)` - Test successful communication channels validation.
  - ✅ `TestConfigValidation.test_validate_core_paths_missing_directory(self)` - Test core path validation with missing directory.
  - ✅ `TestConfigValidation.test_validate_core_paths_success(self, test_data_dir)` - Test successful core path validation.
  - ✅ `TestConfigValidation.test_validate_environment_variables_success(self)` - Test successful environment variables validation.
  - ✅ `TestConfigValidation.test_validate_file_organization_settings_success(self)` - Test successful file organization settings validation.
  - ✅ `TestConfigValidation.test_validate_logging_configuration_success(self)` - Test successful logging configuration validation.
  - ✅ `TestConfigValidation.test_validate_scheduler_configuration_success(self)` - Test successful scheduler configuration validation.

#### `tests/unit/test_error_handling.py`
**Functions:**
- ❌ `backup_function()` - No description
- ❌ `cleanup_function()` - No description
- ❌ `corrupt_data_function()` - No description
- ❌ `inner_function()` - No description
- ❌ `inner_function()` - No description
- ❌ `outer_function()` - No description
- ❌ `outer_function()` - No description
- ❌ `recover_data_function()` - No description
- ❌ `state_validation_function()` - No description
- ✅ `test_config_error(self)` - Test ConfigError exception.
- ✅ `test_data_error(self)` - Test DataError exception.
- ✅ `test_error_handler_custom_return(self)` - Test error_handler with custom return value.
- ✅ `test_error_handler_exception(self)` - Test error_handler with exception.
- ✅ `test_error_handler_logs_error(self)` - Test error_handler logs errors.
- ✅ `test_error_handler_nested_exceptions(self)` - Test error_handler with nested exceptions.
- ✅ `test_error_handler_success(self)` - Test error_handler with successful function.
- ✅ `test_error_handler_with_args_kwargs(self)` - Test error_handler with function arguments.
- ✅ `test_error_handling_different_exception_types(self)` - Test error handling with different exception types and side effects.
- ✅ `test_error_handling_in_function_chain(self)` - Test error handling in a chain of functions.
- ✅ `test_error_handling_with_recovery(self)` - Test error handling with recovery mechanisms and real side effects.
- ✅ `test_file_operation_error(self)` - Test FileOperationError exception.
- ✅ `test_function()` - Test Function.
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function(exception_type)` - Test Function
- ✅ `test_function(arg1, arg2, kwarg1)` - Test Function
- ✅ `test_function(arg1, arg2, kwarg1)` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_function()` - Test Function
- ✅ `test_handle_configuration_error(self)` - Test handle_configuration_error function.
- ✅ `test_handle_errors_custom_return(self)` - Test handle_errors with custom return value.
- ✅ `test_handle_errors_exception(self)` - Test handle_errors with exception.
- ✅ `test_handle_errors_logs_error(self)` - Test handle_errors logs errors.
- ✅ `test_handle_errors_specific_exception(self)` - Test handle_errors with specific exception handling.
- ✅ `test_handle_errors_success(self)` - Test handle_errors with successful function.
- ✅ `test_handle_errors_with_args_kwargs(self)` - Test handle_errors with function arguments.
- ✅ `test_handle_errors_with_logging_disabled(self)` - Test handle_errors when logging is disabled.
- ✅ `test_handle_file_error(self)` - Test handle_file_error function.
- ✅ `test_mhm_error_basic(self)` - Test basic MHMError creation.
- ✅ `test_mhm_error_with_details(self)` - Test MHMError with custom details.
- ✅ `test_validation_error(self)` - Test ValidationError exception.
**Classes:**
- ✅ `TestCustomExceptions` - Test custom exception classes.
  - ✅ `TestCustomExceptions.test_config_error(self)` - Test ConfigError exception.
  - ✅ `TestCustomExceptions.test_data_error(self)` - Test DataError exception.
  - ✅ `TestCustomExceptions.test_file_operation_error(self)` - Test FileOperationError exception.
  - ✅ `TestCustomExceptions.test_mhm_error_basic(self)` - Test basic MHMError creation.
  - ✅ `TestCustomExceptions.test_mhm_error_with_details(self)` - Test MHMError with custom details.
  - ✅ `TestCustomExceptions.test_validation_error(self)` - Test ValidationError exception.
- ✅ `TestErrorHandlerDecorator` - Test the handle_errors decorator.
  - ✅ `TestErrorHandlerDecorator.test_error_handler_custom_return(self)` - Test error_handler with custom return value.
  - ✅ `TestErrorHandlerDecorator.test_error_handler_exception(self)` - Test error_handler with exception.
  - ✅ `TestErrorHandlerDecorator.test_error_handler_logs_error(self)` - Test error_handler logs errors.
  - ✅ `TestErrorHandlerDecorator.test_error_handler_success(self)` - Test error_handler with successful function.
- ✅ `TestErrorHandlingEdgeCases` - Test error handling edge cases.
  - ✅ `TestErrorHandlingEdgeCases.test_error_handler_nested_exceptions(self)` - Test error_handler with nested exceptions.
  - ✅ `TestErrorHandlingEdgeCases.test_error_handler_with_args_kwargs(self)` - Test error_handler with function arguments.
  - ✅ `TestErrorHandlingEdgeCases.test_handle_errors_with_args_kwargs(self)` - Test handle_errors with function arguments.
  - ✅ `TestErrorHandlingEdgeCases.test_handle_errors_with_logging_disabled(self)` - Test handle_errors when logging is disabled.
- ✅ `TestErrorHandlingFunctions` - Test specific error handling functions.
  - ✅ `TestErrorHandlingFunctions.test_handle_configuration_error(self)` - Test handle_configuration_error function.
  - ✅ `TestErrorHandlingFunctions.test_handle_file_error(self)` - Test handle_file_error function.
- ✅ `TestErrorHandlingIntegration` - Test error handling integration scenarios.
  - ✅ `TestErrorHandlingIntegration.test_error_handling_different_exception_types(self)` - Test error handling with different exception types and side effects.
  - ✅ `TestErrorHandlingIntegration.test_error_handling_in_function_chain(self)` - Test error handling in a chain of functions.
  - ✅ `TestErrorHandlingIntegration.test_error_handling_with_recovery(self)` - Test error handling with recovery mechanisms and real side effects.
- ✅ `TestHandleErrorsDecorator` - Test the handle_errors decorator.
  - ✅ `TestHandleErrorsDecorator.test_handle_errors_custom_return(self)` - Test handle_errors with custom return value.
  - ✅ `TestHandleErrorsDecorator.test_handle_errors_exception(self)` - Test handle_errors with exception.
  - ✅ `TestHandleErrorsDecorator.test_handle_errors_logs_error(self)` - Test handle_errors logs errors.
  - ✅ `TestHandleErrorsDecorator.test_handle_errors_specific_exception(self)` - Test handle_errors with specific exception handling.
  - ✅ `TestHandleErrorsDecorator.test_handle_errors_success(self)` - Test handle_errors with successful function.

#### `tests/unit/test_file_operations.py`
**Functions:**
- ✅ `test_determine_file_path_default_messages(self, test_data_dir)` - Test determining file path for default messages.
- ✅ `test_determine_file_path_invalid_file_type(self)` - Test determining file path with invalid file type.
- ✅ `test_determine_file_path_invalid_user_id(self)` - Test determining file path with invalid user ID.
- ✅ `test_determine_file_path_user_file(self, test_data_dir)` - Test determining file path for user file.
- ✅ `test_ensure_user_directory_already_exists(self, test_data_dir)` - Test ensuring user directory that already exists.
- ✅ `test_ensure_user_directory_success(self, test_data_dir)` - Test ensuring user directory exists.
- ✅ `test_file_operations_lifecycle(self, test_data_dir)` - Test complete file operations lifecycle with real side effects.
- ✅ `test_get_user_file_path_success(self, test_data_dir)` - Test getting user file path successfully.
- ✅ `test_load_json_data_corrupted_json(self, temp_file)` - Test loading corrupted JSON data.
- ✅ `test_load_json_data_empty_file(self, temp_file)` - Test loading from empty file.
- ✅ `test_load_json_data_file_not_found(self)` - Test loading JSON data from non-existent file.
- ✅ `test_load_json_data_success(self, temp_file)` - Test loading JSON data successfully.
- ✅ `test_load_json_data_unicode_content(self, temp_file)` - Test loading JSON data with unicode content.
- ✅ `test_load_large_json_data(self, temp_file)` - Test loading large JSON data.
- ✅ `test_save_json_data_complex_objects(self, temp_file)` - Test saving JSON data with complex objects.
- ✅ `test_save_json_data_create_directory(self, test_data_dir)` - Test saving JSON data with directory creation.
- ✅ `test_save_json_data_permission_error(self)` - Test saving JSON data with permission error.
- ✅ `test_save_json_data_success(self, temp_file)` - Test saving JSON data successfully.
- ✅ `test_save_large_json_data(self, temp_file)` - Test saving large JSON data with performance verification.
- ✅ `test_verify_file_access_missing_file(self)` - Test file access verification for missing file.
- ✅ `test_verify_file_access_permission_error(self)` - Test file access verification with permission error.
- ✅ `test_verify_file_access_success(self, temp_file)` - Test file access verification for accessible file.
**Classes:**
- ✅ `TestFileOperations` - Test file operations functions.
  - ✅ `TestFileOperations.test_determine_file_path_default_messages(self, test_data_dir)` - Test determining file path for default messages.
  - ✅ `TestFileOperations.test_determine_file_path_user_file(self, test_data_dir)` - Test determining file path for user file.
  - ✅ `TestFileOperations.test_ensure_user_directory_already_exists(self, test_data_dir)` - Test ensuring user directory that already exists.
  - ✅ `TestFileOperations.test_ensure_user_directory_success(self, test_data_dir)` - Test ensuring user directory exists.
  - ✅ `TestFileOperations.test_get_user_file_path_success(self, test_data_dir)` - Test getting user file path successfully.
  - ✅ `TestFileOperations.test_load_json_data_corrupted_json(self, temp_file)` - Test loading corrupted JSON data.
  - ✅ `TestFileOperations.test_load_json_data_empty_file(self, temp_file)` - Test loading from empty file.
  - ✅ `TestFileOperations.test_load_json_data_file_not_found(self)` - Test loading JSON data from non-existent file.
  - ✅ `TestFileOperations.test_load_json_data_success(self, temp_file)` - Test loading JSON data successfully.
  - ✅ `TestFileOperations.test_save_json_data_create_directory(self, test_data_dir)` - Test saving JSON data with directory creation.
  - ✅ `TestFileOperations.test_save_json_data_permission_error(self)` - Test saving JSON data with permission error.
  - ✅ `TestFileOperations.test_save_json_data_success(self, temp_file)` - Test saving JSON data successfully.
  - ✅ `TestFileOperations.test_verify_file_access_missing_file(self)` - Test file access verification for missing file.
  - ✅ `TestFileOperations.test_verify_file_access_permission_error(self)` - Test file access verification with permission error.
  - ✅ `TestFileOperations.test_verify_file_access_success(self, temp_file)` - Test file access verification for accessible file.
- ✅ `TestFileOperationsEdgeCases` - Test edge cases and error conditions.
  - ✅ `TestFileOperationsEdgeCases.test_determine_file_path_invalid_file_type(self)` - Test determining file path with invalid file type.
  - ✅ `TestFileOperationsEdgeCases.test_determine_file_path_invalid_user_id(self)` - Test determining file path with invalid user ID.
  - ✅ `TestFileOperationsEdgeCases.test_file_operations_lifecycle(self, test_data_dir)` - Test complete file operations lifecycle with real side effects.
  - ✅ `TestFileOperationsEdgeCases.test_load_json_data_unicode_content(self, temp_file)` - Test loading JSON data with unicode content.
  - ✅ `TestFileOperationsEdgeCases.test_save_json_data_complex_objects(self, temp_file)` - Test saving JSON data with complex objects.
- ✅ `TestFileOperationsPerformance` - Test file operations performance and large data handling.
  - ✅ `TestFileOperationsPerformance.test_load_large_json_data(self, temp_file)` - Test loading large JSON data.
  - ✅ `TestFileOperationsPerformance.test_save_large_json_data(self, temp_file)` - Test saving large JSON data with performance verification.

#### `tests/unit/test_user_management.py`
**Functions:**
- ✅ `test_create_user_files_success(self, test_data_dir, mock_config)` - Test creating user files successfully.
- ✅ `test_get_all_user_ids_empty(self, test_data_dir)` - Test getting user IDs when no users exist.
- ✅ `test_get_all_user_ids_with_users(self, test_data_dir, mock_user_data, mock_config)` - Test getting user IDs when users exist.
- ✅ `test_get_user_context_nonexistent_user(self, mock_config)` - Test getting context for non-existent user.
- ✅ `test_get_user_context_success(self, mock_user_data, mock_config)` - Test getting user context successfully.
- ✅ `test_get_user_data_account_nonexistent_chat_id(self, mock_config)` - Test getting user account for non-existent user.
- ✅ `test_get_user_data_account_nonexistent_discord_id(self, mock_config)` - Test getting user account for non-existent user.
- ✅ `test_get_user_data_account_nonexistent_email(self, mock_config)` - Test getting user account for non-existent user.
- ✅ `test_get_user_data_account_with_chat_id(self, mock_user_data, mock_config)` - Test getting user account with chat_id field.
- ✅ `test_get_user_data_account_with_discord_id(self, mock_user_data, mock_config)` - Test getting user account with discord_user_id field.
- ✅ `test_get_user_data_account_with_email(self, test_data_dir, mock_config)` - Test getting user account with email successfully.
- ✅ `test_get_user_data_invalid_type(self, mock_user_data, mock_config)` - Test getting invalid data type using hybrid API.
- ✅ `test_get_user_data_multiple_types(self, mock_user_data, mock_config)` - Test getting multiple data types using hybrid API.
- ✅ `test_get_user_data_nonexistent_user(self, mock_config)` - Test getting data for nonexistent user using hybrid API.
- ✅ `test_get_user_data_single_type(self, mock_user_data, mock_config)` - Test getting single data type using hybrid API.
- ✅ `test_get_user_preferences_corrupted_file(self, test_data_dir, mock_config)` - Test getting preferences with corrupted JSON file.
- ✅ `test_get_user_preferences_nonexistent_user(self, mock_config)` - Test getting preferences for non-existent user.
- ✅ `test_get_user_preferences_success(self, mock_user_data, mock_config)` - Test getting user preferences successfully.
- ✅ `test_hybrid_get_user_data_nonexistent_user(self, mock_config)` - Test loading non-existent user data using new hybrid API.
- ✅ `test_hybrid_get_user_data_success(self, mock_user_data, mock_config)` - Test loading user data successfully using new hybrid API.
- ✅ `test_save_user_data_success(self, test_data_dir, mock_config)` - Test saving user data successfully using new system.
- ✅ `test_save_user_preferences_invalid_user_id(self)` - Test saving preferences with invalid user ID.
- ✅ `test_update_user_preferences_nonexistent_user(self, mock_config)` - Test updating preferences for non-existent user.
- ✅ `test_update_user_preferences_success(self, mock_user_data, mock_config)` - Test updating user preferences successfully.
- ✅ `test_user_lifecycle(self, test_data_dir, mock_config)` - Test complete user lifecycle with real side effects and system state verification.
**Classes:**
- ✅ `TestUserManagement` - Test user management functions.
  - ✅ `TestUserManagement.test_create_user_files_success(self, test_data_dir, mock_config)` - Test creating user files successfully.
  - ✅ `TestUserManagement.test_get_all_user_ids_empty(self, test_data_dir)` - Test getting user IDs when no users exist.
  - ✅ `TestUserManagement.test_get_all_user_ids_with_users(self, test_data_dir, mock_user_data, mock_config)` - Test getting user IDs when users exist.
  - ✅ `TestUserManagement.test_get_user_context_nonexistent_user(self, mock_config)` - Test getting context for non-existent user.
  - ✅ `TestUserManagement.test_get_user_context_success(self, mock_user_data, mock_config)` - Test getting user context successfully.
  - ✅ `TestUserManagement.test_get_user_data_account_nonexistent_chat_id(self, mock_config)` - Test getting user account for non-existent user.
  - ✅ `TestUserManagement.test_get_user_data_account_nonexistent_discord_id(self, mock_config)` - Test getting user account for non-existent user.
  - ✅ `TestUserManagement.test_get_user_data_account_nonexistent_email(self, mock_config)` - Test getting user account for non-existent user.
  - ✅ `TestUserManagement.test_get_user_data_account_with_chat_id(self, mock_user_data, mock_config)` - Test getting user account with chat_id field.
  - ✅ `TestUserManagement.test_get_user_data_account_with_discord_id(self, mock_user_data, mock_config)` - Test getting user account with discord_user_id field.
  - ✅ `TestUserManagement.test_get_user_data_account_with_email(self, test_data_dir, mock_config)` - Test getting user account with email successfully.
  - ✅ `TestUserManagement.test_get_user_preferences_nonexistent_user(self, mock_config)` - Test getting preferences for non-existent user.
  - ✅ `TestUserManagement.test_get_user_preferences_success(self, mock_user_data, mock_config)` - Test getting user preferences successfully.
  - ✅ `TestUserManagement.test_hybrid_get_user_data_nonexistent_user(self, mock_config)` - Test loading non-existent user data using new hybrid API.
  - ✅ `TestUserManagement.test_hybrid_get_user_data_success(self, mock_user_data, mock_config)` - Test loading user data successfully using new hybrid API.
  - ✅ `TestUserManagement.test_save_user_data_success(self, test_data_dir, mock_config)` - Test saving user data successfully using new system.
  - ✅ `TestUserManagement.test_update_user_preferences_success(self, mock_user_data, mock_config)` - Test updating user preferences successfully.
- ✅ `TestUserManagementEdgeCases` - Test edge cases and error conditions.
  - ✅ `TestUserManagementEdgeCases.test_get_user_data_invalid_type(self, mock_user_data, mock_config)` - Test getting invalid data type using hybrid API.
  - ✅ `TestUserManagementEdgeCases.test_get_user_data_multiple_types(self, mock_user_data, mock_config)` - Test getting multiple data types using hybrid API.
  - ✅ `TestUserManagementEdgeCases.test_get_user_data_nonexistent_user(self, mock_config)` - Test getting data for nonexistent user using hybrid API.
  - ✅ `TestUserManagementEdgeCases.test_get_user_data_single_type(self, mock_user_data, mock_config)` - Test getting single data type using hybrid API.
  - ✅ `TestUserManagementEdgeCases.test_get_user_preferences_corrupted_file(self, test_data_dir, mock_config)` - Test getting preferences with corrupted JSON file.
  - ✅ `TestUserManagementEdgeCases.test_save_user_preferences_invalid_user_id(self)` - Test saving preferences with invalid user ID.
  - ✅ `TestUserManagementEdgeCases.test_update_user_preferences_nonexistent_user(self, mock_config)` - Test updating preferences for non-existent user.
  - ✅ `TestUserManagementEdgeCases.test_user_lifecycle(self, test_data_dir, mock_config)` - Test complete user lifecycle with real side effects and system state verification.

### `ui/` - User Interface Components

#### `ui/dialogs/account_creator_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, communication_manager)` - Initialize the object.
- ✅ `accept(self)` - Override accept to prevent automatic dialog closing.
- ✅ `center_dialog(self)` - Center the dialog on the parent window.
- ✅ `close_dialog(self)` - Close the dialog properly.
- ✅ `create_account(self, account_data)` - Create the user account.
- ✅ `create_account_dialog(parent, communication_manager)` - Create and show the account creation dialog.
- ✅ `get_account_data(self)` - Get the account data from the form.
- ✅ `keyPressEvent(self, event)` - Handle key press events for the dialog.
- ✅ `load_category_widget(self)` - Load the category selection widget.
- ✅ `load_checkin_settings_widget(self)` - Load the check-in settings widget.
- ✅ `load_message_service_widget(self)` - Load the message service selection widget.
- ✅ `load_task_management_widget(self)` - Load the task management widget.
- ✅ `on_category_changed(self, categories)` - Handle category selection change (no longer used - widgets don't have signals).
- ✅ `on_checkin_group_toggled(self, checked)` - Handle check-in group toggle (no longer used in tab structure).
- ✅ `on_contact_info_changed(self, service, value)` - Handle contact information change (no longer used - widgets don't have signals).
- ✅ `on_feature_toggled(self, checked)` - Handle feature enablement checkbox toggles.
- ❌ `on_personalization_save(data)` - No description
- ✅ `on_preferred_name_changed(self)` - Handle preferred name change.
- ✅ `on_service_changed(self, service, value)` - Handle service selection change (no longer used - widgets don't have signals).
- ✅ `on_task_group_toggled(self, checked)` - Handle task management group toggle (no longer used in tab structure).
- ✅ `on_username_changed(self)` - Handle username change.
- ✅ `open_personalization_dialog(self)` - Open the personalization dialog.
- ✅ `setup_connections(self)` - Setup signal connections.
- ✅ `setup_feature_group_boxes(self)` - Setup group boxes for task management and check-ins (no longer collapsible in tab structure).
- ✅ `setup_profile_button(self)` - Setup the profile button.
- ✅ `update_profile_button_state(self)` - Update the profile button to show if profile has been configured.
- ✅ `update_tab_visibility(self)` - Update tab visibility based on feature enablement.
- ✅ `validate_account_data(self)` - Validate the account data.
- ✅ `validate_and_accept(self)` - Validate input and accept the dialog.
- ✅ `validate_input(self)` - Validate the input and return (is_valid, error_message).
**Classes:**
- ✅ `AccountCreatorDialog` - Account creation dialog using existing UI files.
  - ✅ `AccountCreatorDialog.__init__(self, parent, communication_manager)` - Initialize the object.
  - ✅ `AccountCreatorDialog.accept(self)` - Override accept to prevent automatic dialog closing.
  - ✅ `AccountCreatorDialog.center_dialog(self)` - Center the dialog on the parent window.
  - ✅ `AccountCreatorDialog.close_dialog(self)` - Close the dialog properly.
  - ✅ `AccountCreatorDialog.create_account(self, account_data)` - Create the user account.
  - ✅ `AccountCreatorDialog.get_account_data(self)` - Get the account data from the form.
  - ✅ `AccountCreatorDialog.keyPressEvent(self, event)` - Handle key press events for the dialog.
  - ✅ `AccountCreatorDialog.load_category_widget(self)` - Load the category selection widget.
  - ✅ `AccountCreatorDialog.load_checkin_settings_widget(self)` - Load the check-in settings widget.
  - ✅ `AccountCreatorDialog.load_message_service_widget(self)` - Load the message service selection widget.
  - ✅ `AccountCreatorDialog.load_task_management_widget(self)` - Load the task management widget.
  - ✅ `AccountCreatorDialog.on_category_changed(self, categories)` - Handle category selection change (no longer used - widgets don't have signals).
  - ✅ `AccountCreatorDialog.on_checkin_group_toggled(self, checked)` - Handle check-in group toggle (no longer used in tab structure).
  - ✅ `AccountCreatorDialog.on_contact_info_changed(self, service, value)` - Handle contact information change (no longer used - widgets don't have signals).
  - ✅ `AccountCreatorDialog.on_feature_toggled(self, checked)` - Handle feature enablement checkbox toggles.
  - ✅ `AccountCreatorDialog.on_preferred_name_changed(self)` - Handle preferred name change.
  - ✅ `AccountCreatorDialog.on_service_changed(self, service, value)` - Handle service selection change (no longer used - widgets don't have signals).
  - ✅ `AccountCreatorDialog.on_task_group_toggled(self, checked)` - Handle task management group toggle (no longer used in tab structure).
  - ✅ `AccountCreatorDialog.on_username_changed(self)` - Handle username change.
  - ✅ `AccountCreatorDialog.open_personalization_dialog(self)` - Open the personalization dialog.
  - ✅ `AccountCreatorDialog.setup_connections(self)` - Setup signal connections.
  - ✅ `AccountCreatorDialog.setup_feature_group_boxes(self)` - Setup group boxes for task management and check-ins (no longer collapsible in tab structure).
  - ✅ `AccountCreatorDialog.setup_profile_button(self)` - Setup the profile button.
  - ✅ `AccountCreatorDialog.update_profile_button_state(self)` - Update the profile button to show if profile has been configured.
  - ✅ `AccountCreatorDialog.update_tab_visibility(self)` - Update tab visibility based on feature enablement.
  - ✅ `AccountCreatorDialog.validate_account_data(self)` - Validate the account data.
  - ✅ `AccountCreatorDialog.validate_and_accept(self)` - Validate input and accept the dialog.
  - ✅ `AccountCreatorDialog.validate_input(self)` - Validate the input and return (is_valid, error_message).

#### `ui/dialogs/admin_panel.py`
**Functions:**
- ✅ `__init__(self, parent)` - Initialize the AdminPanelDialog.

Args:
    parent: Parent widget for the dialog
- ✅ `get_admin_data(self)` - Get the admin panel data.

Returns:
    dict: Admin panel data (currently returns empty dict as placeholder)
- ✅ `set_admin_data(self, data)` - Set the admin panel data.

Args:
    data: Admin panel data to set (currently not implemented)
- ✅ `setup_ui(self)` - Setup the UI components.
**Classes:**
- ✅ `AdminPanelDialog` - Dialog for admin panel functionality.
  - ✅ `AdminPanelDialog.__init__(self, parent)` - Initialize the AdminPanelDialog.

Args:
    parent: Parent widget for the dialog
  - ✅ `AdminPanelDialog.get_admin_data(self)` - Get the admin panel data.

Returns:
    dict: Admin panel data (currently returns empty dict as placeholder)
  - ✅ `AdminPanelDialog.set_admin_data(self, data)` - Set the admin panel data.

Args:
    data: Admin panel data to set (currently not implemented)
  - ✅ `AdminPanelDialog.setup_ui(self)` - Setup the UI components.

#### `ui/dialogs/category_management_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ❌ `get_selected_categories(self)` - No description
- ✅ `load_user_category_data(self)` - Load user's current category settings
- ✅ `on_enable_messages_toggled(self, checked)` - Handle enable automated messages checkbox toggle.
- ✅ `save_category_settings(self)` - Save the selected categories back to user preferences
- ❌ `set_selected_categories(self, categories)` - No description
**Classes:**
- ❌ `CategoryManagementDialog` - No description
  - ✅ `CategoryManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - ❌ `CategoryManagementDialog.get_selected_categories(self)` - No description
  - ✅ `CategoryManagementDialog.load_user_category_data(self)` - Load user's current category settings
  - ✅ `CategoryManagementDialog.on_enable_messages_toggled(self, checked)` - Handle enable automated messages checkbox toggle.
  - ✅ `CategoryManagementDialog.save_category_settings(self)` - Save the selected categories back to user preferences
  - ❌ `CategoryManagementDialog.set_selected_categories(self, categories)` - No description

#### `ui/dialogs/channel_management_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ❌ `get_selected_channel(self)` - No description
- ❌ `save_channel_settings(self)` - No description
- ❌ `set_selected_channel(self, channel, value)` - No description
**Classes:**
- ❌ `ChannelManagementDialog` - No description
  - ✅ `ChannelManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - ❌ `ChannelManagementDialog.get_selected_channel(self)` - No description
  - ❌ `ChannelManagementDialog.save_channel_settings(self)` - No description
  - ❌ `ChannelManagementDialog.set_selected_channel(self, channel, value)` - No description

#### `ui/dialogs/checkin_management_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ✅ `get_checkin_settings(self)` - Get the current check-in settings.
- ✅ `load_user_checkin_data(self)` - Load the user's current check-in settings
- ❌ `on_enable_checkins_toggled(self, checked)` - No description
- ✅ `save_checkin_settings(self)` - Save the check-in settings back to user preferences
- ✅ `set_checkin_settings(self, settings)` - Set the check-in settings.
**Classes:**
- ✅ `CheckinManagementDialog` - Dialog for managing check-in settings.
  - ✅ `CheckinManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - ✅ `CheckinManagementDialog.get_checkin_settings(self)` - Get the current check-in settings.
  - ✅ `CheckinManagementDialog.load_user_checkin_data(self)` - Load the user's current check-in settings
  - ❌ `CheckinManagementDialog.on_enable_checkins_toggled(self, checked)` - No description
  - ✅ `CheckinManagementDialog.save_checkin_settings(self)` - Save the check-in settings back to user preferences
  - ✅ `CheckinManagementDialog.set_checkin_settings(self, settings)` - Set the check-in settings.

#### `ui/dialogs/schedule_editor_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id, category, on_save)` - Initialize the object.
- ✅ `add_new_period(self, period_name, period_data)` - Add a new period row using the PeriodRowWidget.
- ✅ `cancel(self)` - Cancel the dialog.
- ✅ `center_dialog(self)` - Center the dialog on the parent window.
- ✅ `collect_period_data(self)` - Collect period data using the new reusable function.
- ✅ `get_schedule_data(self)` - Get the current schedule data.
- ✅ `load_existing_data(self)` - Load existing schedule data using the new reusable function.
- ✅ `open_schedule_editor(parent, user_id, category, on_save)` - Open the schedule editor dialog.
- ✅ `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- ✅ `save_schedule(self)` - Save the schedule data.
- ✅ `set_schedule_data(self, data)` - Set the schedule data.
- ✅ `setup_functionality(self)` - Setup the functionality and connect signals.
- ✅ `undo_last_delete(self)` - Undo the last deletion.
**Classes:**
- ✅ `ScheduleEditorDialog` - Dialog for editing schedules.
  - ✅ `ScheduleEditorDialog.__init__(self, parent, user_id, category, on_save)` - Initialize the object.
  - ✅ `ScheduleEditorDialog.add_new_period(self, period_name, period_data)` - Add a new period row using the PeriodRowWidget.
  - ✅ `ScheduleEditorDialog.cancel(self)` - Cancel the dialog.
  - ✅ `ScheduleEditorDialog.center_dialog(self)` - Center the dialog on the parent window.
  - ✅ `ScheduleEditorDialog.collect_period_data(self)` - Collect period data using the new reusable function.
  - ✅ `ScheduleEditorDialog.get_schedule_data(self)` - Get the current schedule data.
  - ✅ `ScheduleEditorDialog.load_existing_data(self)` - Load existing schedule data using the new reusable function.
  - ✅ `ScheduleEditorDialog.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - ✅ `ScheduleEditorDialog.save_schedule(self)` - Save the schedule data.
  - ✅ `ScheduleEditorDialog.set_schedule_data(self, data)` - Set the schedule data.
  - ✅ `ScheduleEditorDialog.setup_functionality(self)` - Setup the functionality and connect signals.
  - ✅ `ScheduleEditorDialog.undo_last_delete(self)` - Undo the last deletion.

#### `ui/dialogs/task_management_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ❌ `get_statistics(self)` - No description
- ❌ `on_enable_task_management_toggled(self, checked)` - No description
- ✅ `save_task_settings(self)` - Save the task settings.
**Classes:**
- ❌ `TaskManagementDialog` - No description
  - ✅ `TaskManagementDialog.__init__(self, parent, user_id)` - Initialize the object.
  - ❌ `TaskManagementDialog.get_statistics(self)` - No description
  - ❌ `TaskManagementDialog.on_enable_task_management_toggled(self, checked)` - No description
  - ✅ `TaskManagementDialog.save_task_settings(self)` - Save the task settings.

#### `ui/dialogs/user_profile_dialog.py`
**Functions:**
- ✅ `__init__(self, parent, user_id, on_save, existing_data)` - Initialize the object.
- ✅ `add_custom_field(self, parent_layout, field_type, value, checked)` - Add a custom field row with checkbox, entry, and delete button.
- ✅ `add_loved_one_widget(self, parent_layout, loved_one_data)` - Add a loved one widget to the layout.

Args:
    parent_layout: Parent layout to add the widget to
    loved_one_data: Optional existing loved one data
- ✅ `cancel(self)` - Cancel the personalization dialog.
- ✅ `center_dialog(self)` - Center the dialog on the parent window.
- ✅ `collect_custom_field_data(self, group_box)` - Collect data from custom field checkboxes and entries.

Args:
    group_box: Group box containing custom fields
    
Returns:
    list: List of selected values from checkboxes and custom entries
- ✅ `collect_loved_ones_data(self)` - Collect data from loved ones widgets.

Returns:
    list: List of loved ones data dictionaries
- ✅ `create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text)` - Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete).
- ✅ `create_goals_section(self)` - Create the goals section of the personalization dialog.

Returns:
    QGroupBox: Goals section group box
- ✅ `create_health_section(self)` - Create the health section of the personalization dialog.

Returns:
    QGroupBox: Health section group box
- ✅ `create_interests_section(self)` - Create the interests section of the personalization dialog.

Returns:
    QGroupBox: Interests section group box
- ✅ `create_loved_ones_section(self)` - Create the loved ones section of the personalization dialog.

Returns:
    QGroupBox: Loved ones section group box
- ✅ `create_notes_section(self)` - Create the notes section of the personalization dialog.

Returns:
    QGroupBox: Notes section group box
- ✅ `keyPressEvent(self, event)` - Handle key press events for the dialog.
- ✅ `open_personalization_dialog(parent, user_id, on_save, existing_data)` - Open the personalization dialog.

Args:
    parent: Parent widget
    user_id: User ID for the personalization data
    on_save: Optional callback function to call when saving
    existing_data: Optional existing personalization data
    
Returns:
    QDialog.DialogCode: Dialog result code
- ✅ `remove_custom_field(self, field_frame)` - Remove a custom field from the layout.
- ✅ `remove_loved_one_widget(self, frame)` - Remove a loved one widget from the layout.

Args:
    frame: Frame widget to remove
- ✅ `save_personalization(self)` - Save the personalization data.
- ✅ `setup_ui(self)` - Setup the user interface.
- ✅ `title_case(s)` - Convert snake_case or lowercase to Title Case.

Args:
    s: String to convert to title case
    
Returns:
    str: String converted to title case
**Classes:**
- ✅ `UserProfileDialog` - PySide6-based personalization dialog for user account creation and management.
  - ✅ `UserProfileDialog.__init__(self, parent, user_id, on_save, existing_data)` - Initialize the object.
  - ✅ `UserProfileDialog.add_custom_field(self, parent_layout, field_type, value, checked)` - Add a custom field row with checkbox, entry, and delete button.
  - ✅ `UserProfileDialog.add_loved_one_widget(self, parent_layout, loved_one_data)` - Add a loved one widget to the layout.

Args:
    parent_layout: Parent layout to add the widget to
    loved_one_data: Optional existing loved one data
  - ✅ `UserProfileDialog.cancel(self)` - Cancel the personalization dialog.
  - ✅ `UserProfileDialog.center_dialog(self)` - Center the dialog on the parent window.
  - ✅ `UserProfileDialog.collect_custom_field_data(self, group_box)` - Collect data from custom field checkboxes and entries.

Args:
    group_box: Group box containing custom fields
    
Returns:
    list: List of selected values from checkboxes and custom entries
  - ✅ `UserProfileDialog.collect_loved_ones_data(self)` - Collect data from loved ones widgets.

Returns:
    list: List of loved ones data dictionaries
  - ✅ `UserProfileDialog.create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text)` - Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete).
  - ✅ `UserProfileDialog.create_goals_section(self)` - Create the goals section of the personalization dialog.

Returns:
    QGroupBox: Goals section group box
  - ✅ `UserProfileDialog.create_health_section(self)` - Create the health section of the personalization dialog.

Returns:
    QGroupBox: Health section group box
  - ✅ `UserProfileDialog.create_interests_section(self)` - Create the interests section of the personalization dialog.

Returns:
    QGroupBox: Interests section group box
  - ✅ `UserProfileDialog.create_loved_ones_section(self)` - Create the loved ones section of the personalization dialog.

Returns:
    QGroupBox: Loved ones section group box
  - ✅ `UserProfileDialog.create_notes_section(self)` - Create the notes section of the personalization dialog.

Returns:
    QGroupBox: Notes section group box
  - ✅ `UserProfileDialog.keyPressEvent(self, event)` - Handle key press events for the dialog.
  - ✅ `UserProfileDialog.remove_custom_field(self, field_frame)` - Remove a custom field from the layout.
  - ✅ `UserProfileDialog.remove_loved_one_widget(self, frame)` - Remove a loved one widget from the layout.

Args:
    frame: Frame widget to remove
  - ✅ `UserProfileDialog.save_personalization(self)` - Save the personalization data.
  - ✅ `UserProfileDialog.setup_ui(self)` - Setup the user interface.

#### `ui/generated/account_creator_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_create_account)` - Auto-generated Qt UI translation function for account_creator_dialog.
- ✅ `setupUi(self, Dialog_create_account)` - Auto-generated Qt UI setup function for account_creator_dialog.
**Classes:**
- ❌ `Ui_Dialog_create_account` - No description
  - ✅ `Ui_Dialog_create_account.retranslateUi(self, Dialog_create_account)` - Auto-generated Qt UI translation function for account_creator_dialog.
  - ✅ `Ui_Dialog_create_account.setupUi(self, Dialog_create_account)` - Auto-generated Qt UI setup function for account_creator_dialog.

#### `ui/generated/admin_panel_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, ui_app_mainwindow)` - Auto-generated Qt UI translation function for admin_panel.
- ✅ `setupUi(self, ui_app_mainwindow)` - Auto-generated Qt UI setup function for admin_panel.
**Classes:**
- ❌ `Ui_ui_app_mainwindow` - No description
  - ✅ `Ui_ui_app_mainwindow.retranslateUi(self, ui_app_mainwindow)` - Auto-generated Qt UI translation function for admin_panel.
  - ✅ `Ui_ui_app_mainwindow.setupUi(self, ui_app_mainwindow)` - Auto-generated Qt UI setup function for admin_panel.

#### `ui/generated/category_management_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_category_management)` - Auto-generated Qt UI translation function for category_management_dialog.
- ✅ `setupUi(self, Dialog_category_management)` - Auto-generated Qt UI setup function for category_management_dialog.
**Classes:**
- ❌ `Ui_Dialog_category_management` - No description
  - ✅ `Ui_Dialog_category_management.retranslateUi(self, Dialog_category_management)` - Auto-generated Qt UI translation function for category_management_dialog.
  - ✅ `Ui_Dialog_category_management.setupUi(self, Dialog_category_management)` - Auto-generated Qt UI setup function for category_management_dialog.

#### `ui/generated/category_selection_widget_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Form_category_selection_widget)` - Auto-generated Qt UI translation function for category_selection_widget.
- ✅ `setupUi(self, Form_category_selection_widget)` - Auto-generated Qt UI setup function for category_selection_widget.
**Classes:**
- ❌ `Ui_Form_category_selection_widget` - No description
  - ✅ `Ui_Form_category_selection_widget.retranslateUi(self, Form_category_selection_widget)` - Auto-generated Qt UI translation function for category_selection_widget.
  - ✅ `Ui_Form_category_selection_widget.setupUi(self, Form_category_selection_widget)` - Auto-generated Qt UI setup function for category_selection_widget.

#### `ui/generated/channel_management_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog)` - Auto-generated Qt UI translation function for channel_management_dialog.
- ✅ `setupUi(self, Dialog)` - Auto-generated Qt UI setup function for channel_management_dialog.
**Classes:**
- ❌ `Ui_Dialog` - No description
  - ✅ `Ui_Dialog.retranslateUi(self, Dialog)` - Auto-generated Qt UI translation function for channel_management_dialog.
  - ✅ `Ui_Dialog.setupUi(self, Dialog)` - Auto-generated Qt UI setup function for channel_management_dialog.

#### `ui/generated/channel_selection_widget_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Form_channel_selection)` - Auto-generated Qt UI translation function for channel_selection_widget.
- ✅ `setupUi(self, Form_channel_selection)` - Auto-generated Qt UI setup function for channel_selection_widget.
**Classes:**
- ❌ `Ui_Form_channel_selection` - No description
  - ✅ `Ui_Form_channel_selection.retranslateUi(self, Form_channel_selection)` - Auto-generated Qt UI translation function for channel_selection_widget.
  - ✅ `Ui_Form_channel_selection.setupUi(self, Form_channel_selection)` - Auto-generated Qt UI setup function for channel_selection_widget.

#### `ui/generated/checkin_element_template_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Form_checkin_element_template)` - Auto-generated Qt UI translation function for checkin_element_template.
- ✅ `setupUi(self, Form_checkin_element_template)` - Auto-generated Qt UI setup function for checkin_element_template.
**Classes:**
- ❌ `Ui_Form_checkin_element_template` - No description
  - ✅ `Ui_Form_checkin_element_template.retranslateUi(self, Form_checkin_element_template)` - Auto-generated Qt UI translation function for checkin_element_template.
  - ✅ `Ui_Form_checkin_element_template.setupUi(self, Form_checkin_element_template)` - Auto-generated Qt UI setup function for checkin_element_template.

#### `ui/generated/checkin_management_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_checkin_management)` - Auto-generated Qt UI translation function for checkin_management_dialog.
- ✅ `setupUi(self, Dialog_checkin_management)` - Auto-generated Qt UI setup function for checkin_management_dialog.
**Classes:**
- ❌ `Ui_Dialog_checkin_management` - No description
  - ✅ `Ui_Dialog_checkin_management.retranslateUi(self, Dialog_checkin_management)` - Auto-generated Qt UI translation function for checkin_management_dialog.
  - ✅ `Ui_Dialog_checkin_management.setupUi(self, Dialog_checkin_management)` - Auto-generated Qt UI setup function for checkin_management_dialog.

#### `ui/generated/checkin_settings_widget_pyqt.py`
**Functions:**
- ✅ `retranslateUi(self, Form_checkin_settings)` - Auto-generated Qt UI translation function for checkin_settings_widget.
- ✅ `setupUi(self, Form_checkin_settings)` - Auto-generated Qt UI setup function for checkin_settings_widget.
**Classes:**
- ❌ `Ui_Form_checkin_settings` - No description
  - ✅ `Ui_Form_checkin_settings.retranslateUi(self, Form_checkin_settings)` - Auto-generated Qt UI translation function for checkin_settings_widget.
  - ✅ `Ui_Form_checkin_settings.setupUi(self, Form_checkin_settings)` - Auto-generated Qt UI setup function for checkin_settings_widget.

#### `ui/generated/dynamic_list_field_template_pyqt.py`
**Functions:**
- ✅ `retranslateUi(self, Form_dynamic_list_field_template)` - Auto-generated Qt UI translation function for dynamic_list_field_template.
- ✅ `setupUi(self, Form_dynamic_list_field_template)` - Auto-generated Qt UI setup function for dynamic_list_field_template.
**Classes:**
- ❌ `Ui_Form_dynamic_list_field_template` - No description
  - ✅ `Ui_Form_dynamic_list_field_template.retranslateUi(self, Form_dynamic_list_field_template)` - Auto-generated Qt UI translation function for dynamic_list_field_template.
  - ✅ `Ui_Form_dynamic_list_field_template.setupUi(self, Form_dynamic_list_field_template)` - Auto-generated Qt UI setup function for dynamic_list_field_template.

#### `ui/generated/period_row_template_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Form_period_row_template)` - Auto-generated Qt UI translation function for period_row_template.
- ✅ `setupUi(self, Form_period_row_template)` - Auto-generated Qt UI setup function for period_row_template.
**Classes:**
- ❌ `Ui_Form_period_row_template` - No description
  - ✅ `Ui_Form_period_row_template.retranslateUi(self, Form_period_row_template)` - Auto-generated Qt UI translation function for period_row_template.
  - ✅ `Ui_Form_period_row_template.setupUi(self, Form_period_row_template)` - Auto-generated Qt UI setup function for period_row_template.

#### `ui/generated/schedule_editor_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_edit_schedule)` - Auto-generated Qt UI translation function for schedule_editor_dialog.
- ✅ `setupUi(self, Dialog_edit_schedule)` - Auto-generated Qt UI setup function for schedule_editor_dialog.
**Classes:**
- ❌ `Ui_Dialog_edit_schedule` - No description
  - ✅ `Ui_Dialog_edit_schedule.retranslateUi(self, Dialog_edit_schedule)` - Auto-generated Qt UI translation function for schedule_editor_dialog.
  - ✅ `Ui_Dialog_edit_schedule.setupUi(self, Dialog_edit_schedule)` - Auto-generated Qt UI setup function for schedule_editor_dialog.

#### `ui/generated/task_management_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_task_management)` - Auto-generated Qt UI translation function for task_management_dialog.
- ✅ `setupUi(self, Dialog_task_management)` - Auto-generated Qt UI setup function for task_management_dialog.
**Classes:**
- ❌ `Ui_Dialog_task_management` - No description
  - ✅ `Ui_Dialog_task_management.retranslateUi(self, Dialog_task_management)` - Auto-generated Qt UI translation function for task_management_dialog.
  - ✅ `Ui_Dialog_task_management.setupUi(self, Dialog_task_management)` - Auto-generated Qt UI setup function for task_management_dialog.

#### `ui/generated/task_settings_widget_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Form_task_settings)` - Auto-generated Qt UI translation function for task_settings_widget.
- ✅ `setupUi(self, Form_task_settings)` - Auto-generated Qt UI setup function for task_settings_widget.
**Classes:**
- ❌ `Ui_Form_task_settings` - No description
  - ✅ `Ui_Form_task_settings.retranslateUi(self, Form_task_settings)` - Auto-generated Qt UI translation function for task_settings_widget.
  - ✅ `Ui_Form_task_settings.setupUi(self, Form_task_settings)` - Auto-generated Qt UI setup function for task_settings_widget.

#### `ui/generated/user_profile_management_dialog_pyqt.py`
**Functions:**
- ❌ `qtTrId(id)` - No description
- ✅ `retranslateUi(self, Dialog_user_profile)` - Auto-generated Qt UI translation function for user_profile_management_dialog.
- ✅ `setupUi(self, Dialog_user_profile)` - Auto-generated Qt UI setup function for user_profile_management_dialog.
**Classes:**
- ❌ `Ui_Dialog_user_profile` - No description
  - ✅ `Ui_Dialog_user_profile.retranslateUi(self, Dialog_user_profile)` - Auto-generated Qt UI translation function for user_profile_management_dialog.
  - ✅ `Ui_Dialog_user_profile.setupUi(self, Dialog_user_profile)` - Auto-generated Qt UI setup function for user_profile_management_dialog.

#### `ui/generated/user_profile_settings_widget_pyqt.py`
**Functions:**
- ✅ `retranslateUi(self, Form_user_profile_settings)` - Auto-generated Qt UI translation function for user_profile_settings_widget.
- ✅ `setupUi(self, Form_user_profile_settings)` - Auto-generated Qt UI setup function for user_profile_settings_widget.
**Classes:**
- ❌ `Ui_Form_user_profile_settings` - No description
  - ✅ `Ui_Form_user_profile_settings.retranslateUi(self, Form_user_profile_settings)` - Auto-generated Qt UI translation function for user_profile_settings_widget.
  - ✅ `Ui_Form_user_profile_settings.setupUi(self, Form_user_profile_settings)` - Auto-generated Qt UI setup function for user_profile_settings_widget.

#### `ui/ui_app_qt.py`
**Functions:**
- ✅ `__init__(self)` - Initialize the object.
- ✅ `__init__(self)` - Initialize the object.
- ❌ `cleanup_old_requests()` - No description
- ✅ `closeEvent(self, event)` - Handle window close event
- ✅ `confirm_test_message(self, parent_dialog, category)` - Confirm and send test message
- ✅ `connect_signals(self)` - Connect UI signals to slots
- ✅ `create_new_user(self)` - Open dialog to create a new user
- ✅ `disable_content_management(self)` - Disable content management buttons
- ✅ `edit_user_messages(self)` - Open message editing interface for selected user
- ✅ `edit_user_schedules(self)` - Open schedule editing interface for selected user
- ✅ `enable_content_management(self)` - Enable content management buttons
- ✅ `force_clean_cache(self)` - Force cache cleanup regardless of schedule.
- ✅ `initialize_ui(self)` - Initialize the UI state
- ✅ `is_service_running(self)` - Check if the MHM service is running
- ✅ `load_theme(self)` - Load and apply the QSS theme from the styles directory
- ✅ `load_ui(self)` - Load the UI from the .ui file
- ✅ `load_user_categories(self, user_id)` - Load categories for the selected user
- ✅ `main()` - Main entry point for the Qt-based UI application
- ❌ `manage_categories(self)` - No description
- ❌ `manage_checkins(self)` - No description
- ❌ `manage_communication_settings(self)` - No description
- ❌ `manage_personalization(self)` - No description
- ❌ `manage_tasks(self)` - No description
- ✅ `on_category_selected(self, category)` - Handle category selection
- ❌ `on_save(data)` - No description
- ✅ `on_schedule_save()` - Callback when schedule is saved.
- ✅ `on_user_selected(self, user_display)` - Handle user selection from combo box
- ✅ `open_message_editor(self, parent_dialog, category)` - Open the message editing window for a specific category
- ✅ `open_schedule_editor(self, parent_dialog, category)` - Open the schedule editing window for a specific category
- ✅ `refresh_user_list(self)` - Refresh the user list in the combo box using user index
- ✅ `restart_service(self)` - Restart the MHM backend service
- ✅ `restart_service(self)` - Restart the MHM service
- ✅ `send_actual_test_message(self, category)` - Send a test message via the running service
- ✅ `send_test_message(self)` - Send a test message to the selected user
- ✅ `show_configuration_help(self, parent_window)` - Show help for fixing configuration issues.
- ✅ `shutdown_ui_components(self, communication_manager)` - Shutdown any UI-created components gracefully
- ✅ `start_service(self)` - Start the MHM backend service
- ✅ `start_service(self)` - Start the MHM service
- ✅ `stop_service(self)` - Stop the MHM backend service
- ✅ `stop_service(self)` - Stop the MHM service
- ✅ `system_health_check(self)` - Perform a basic system health check.
- ✅ `toggle_logging_verbosity(self)` - Toggle logging verbosity and update menu.
- ✅ `update_service_status(self)` - Update the service status display
- ✅ `update_user_index_on_startup(self)` - Automatically update the user index when the admin panel starts
- ✅ `validate_configuration(self)` - Show detailed configuration validation report.
- ✅ `validate_configuration_before_start(self)` - Validate configuration before attempting to start the service.
- ✅ `view_all_users_summary(self)` - Show a summary of all users in the system.
- ✅ `view_cache_status(self)` - Show cache cleanup status and information.
- ✅ `view_log_file(self)` - Open the log file in the default text editor.
**Classes:**
- ✅ `MHMManagerUI` - Main MHM Management UI using PySide6
  - ✅ `MHMManagerUI.__init__(self)` - Initialize the object.
  - ✅ `MHMManagerUI.closeEvent(self, event)` - Handle window close event
  - ✅ `MHMManagerUI.confirm_test_message(self, parent_dialog, category)` - Confirm and send test message
  - ✅ `MHMManagerUI.connect_signals(self)` - Connect UI signals to slots
  - ✅ `MHMManagerUI.create_new_user(self)` - Open dialog to create a new user
  - ✅ `MHMManagerUI.disable_content_management(self)` - Disable content management buttons
  - ✅ `MHMManagerUI.edit_user_messages(self)` - Open message editing interface for selected user
  - ✅ `MHMManagerUI.edit_user_schedules(self)` - Open schedule editing interface for selected user
  - ✅ `MHMManagerUI.enable_content_management(self)` - Enable content management buttons
  - ✅ `MHMManagerUI.force_clean_cache(self)` - Force cache cleanup regardless of schedule.
  - ✅ `MHMManagerUI.initialize_ui(self)` - Initialize the UI state
  - ✅ `MHMManagerUI.load_theme(self)` - Load and apply the QSS theme from the styles directory
  - ✅ `MHMManagerUI.load_ui(self)` - Load the UI from the .ui file
  - ✅ `MHMManagerUI.load_user_categories(self, user_id)` - Load categories for the selected user
  - ❌ `MHMManagerUI.manage_categories(self)` - No description
  - ❌ `MHMManagerUI.manage_checkins(self)` - No description
  - ❌ `MHMManagerUI.manage_communication_settings(self)` - No description
  - ❌ `MHMManagerUI.manage_personalization(self)` - No description
  - ❌ `MHMManagerUI.manage_tasks(self)` - No description
  - ✅ `MHMManagerUI.on_category_selected(self, category)` - Handle category selection
  - ✅ `MHMManagerUI.on_user_selected(self, user_display)` - Handle user selection from combo box
  - ✅ `MHMManagerUI.open_message_editor(self, parent_dialog, category)` - Open the message editing window for a specific category
  - ✅ `MHMManagerUI.open_schedule_editor(self, parent_dialog, category)` - Open the schedule editing window for a specific category
  - ✅ `MHMManagerUI.refresh_user_list(self)` - Refresh the user list in the combo box using user index
  - ✅ `MHMManagerUI.restart_service(self)` - Restart the MHM service
  - ✅ `MHMManagerUI.send_actual_test_message(self, category)` - Send a test message via the running service
  - ✅ `MHMManagerUI.send_test_message(self)` - Send a test message to the selected user
  - ✅ `MHMManagerUI.show_configuration_help(self, parent_window)` - Show help for fixing configuration issues.
  - ✅ `MHMManagerUI.shutdown_ui_components(self, communication_manager)` - Shutdown any UI-created components gracefully
  - ✅ `MHMManagerUI.start_service(self)` - Start the MHM service
  - ✅ `MHMManagerUI.stop_service(self)` - Stop the MHM service
  - ✅ `MHMManagerUI.system_health_check(self)` - Perform a basic system health check.
  - ✅ `MHMManagerUI.toggle_logging_verbosity(self)` - Toggle logging verbosity and update menu.
  - ✅ `MHMManagerUI.update_service_status(self)` - Update the service status display
  - ✅ `MHMManagerUI.update_user_index_on_startup(self)` - Automatically update the user index when the admin panel starts
  - ✅ `MHMManagerUI.validate_configuration(self)` - Show detailed configuration validation report.
  - ✅ `MHMManagerUI.view_all_users_summary(self)` - Show a summary of all users in the system.
  - ✅ `MHMManagerUI.view_cache_status(self)` - Show cache cleanup status and information.
  - ✅ `MHMManagerUI.view_log_file(self)` - Open the log file in the default text editor.
- ✅ `ServiceManager` - Manages the MHM backend service process
  - ✅ `ServiceManager.__init__(self)` - Initialize the object.
  - ✅ `ServiceManager.is_service_running(self)` - Check if the MHM service is running
  - ✅ `ServiceManager.restart_service(self)` - Restart the MHM backend service
  - ✅ `ServiceManager.start_service(self)` - Start the MHM backend service
  - ✅ `ServiceManager.stop_service(self)` - Stop the MHM backend service
  - ✅ `ServiceManager.validate_configuration_before_start(self)` - Validate configuration before attempting to start the service.

#### `ui/widgets/category_selection_widget.py`
**Functions:**
- ✅ `__init__(self, parent)` - Initialize the object.
- ❌ `get_selected_categories(self)` - No description
- ❌ `set_selected_categories(self, categories)` - No description
**Classes:**
- ❌ `CategorySelectionWidget` - No description
  - ✅ `CategorySelectionWidget.__init__(self, parent)` - Initialize the object.
  - ❌ `CategorySelectionWidget.get_selected_categories(self)` - No description
  - ❌ `CategorySelectionWidget.set_selected_categories(self, categories)` - No description

#### `ui/widgets/channel_selection_widget.py`
**Functions:**
- ✅ `__init__(self, parent)` - Initialize the ChannelSelectionWidget.

Sets up the UI for channel selection with Discord, Email, and Telegram options,
along with timezone selection. Populates timezone options and sets default
timezone to America/Regina.

Args:
    parent: Parent widget (optional)
- ✅ `get_all_contact_info(self)` - Get all contact info fields from the widget.
- ❌ `get_selected_channel(self)` - No description
- ✅ `get_timezone(self)` - Get the selected timezone.
- ✅ `populate_timezones(self)` - Populate the timezone combo box with options.
- ❌ `set_contact_info(self, email, phone, discord_id, timezone)` - No description
- ❌ `set_selected_channel(self, channel, value)` - No description
- ✅ `set_timezone(self, timezone)` - Set the timezone.
**Classes:**
- ❌ `ChannelSelectionWidget` - No description
  - ✅ `ChannelSelectionWidget.__init__(self, parent)` - Initialize the ChannelSelectionWidget.

Sets up the UI for channel selection with Discord, Email, and Telegram options,
along with timezone selection. Populates timezone options and sets default
timezone to America/Regina.

Args:
    parent: Parent widget (optional)
  - ✅ `ChannelSelectionWidget.get_all_contact_info(self)` - Get all contact info fields from the widget.
  - ❌ `ChannelSelectionWidget.get_selected_channel(self)` - No description
  - ✅ `ChannelSelectionWidget.get_timezone(self)` - Get the selected timezone.
  - ✅ `ChannelSelectionWidget.populate_timezones(self)` - Populate the timezone combo box with options.
  - ❌ `ChannelSelectionWidget.set_contact_info(self, email, phone, discord_id, timezone)` - No description
  - ❌ `ChannelSelectionWidget.set_selected_channel(self, channel, value)` - No description
  - ✅ `ChannelSelectionWidget.set_timezone(self, timezone)` - Set the timezone.

#### `ui/widgets/checkin_settings_widget.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ✅ `add_new_question(self)` - Add a new check-in question.
- ✅ `add_new_time_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
- ✅ `connect_question_checkboxes(self)` - Connect all question checkboxes to track changes.
- ✅ `find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
- ✅ `get_checkin_settings(self)` - Get the current check-in settings.
- ✅ `get_default_question_state(self, question_key)` - Get default enabled state for a question.
- ✅ `load_existing_data(self)` - Load existing check-in data.
- ✅ `on_question_toggled(self, checked)` - Handle question checkbox toggle.
- ✅ `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- ✅ `set_checkin_settings(self, settings)` - Set the check-in settings.
- ✅ `set_question_checkboxes(self, questions)` - Set question checkboxes based on saved preferences.
- ✅ `setup_connections(self)` - Setup signal connections.
- ✅ `showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
- ✅ `undo_last_question_delete(self)` - Undo the last question deletion.
- ✅ `undo_last_time_period_delete(self)` - Undo the last time period deletion.
**Classes:**
- ✅ `CheckinSettingsWidget` - Widget for check-in settings configuration.
  - ✅ `CheckinSettingsWidget.__init__(self, parent, user_id)` - Initialize the object.
  - ✅ `CheckinSettingsWidget.add_new_question(self)` - Add a new check-in question.
  - ✅ `CheckinSettingsWidget.add_new_time_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
  - ✅ `CheckinSettingsWidget.connect_question_checkboxes(self)` - Connect all question checkboxes to track changes.
  - ✅ `CheckinSettingsWidget.find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
  - ✅ `CheckinSettingsWidget.get_checkin_settings(self)` - Get the current check-in settings.
  - ✅ `CheckinSettingsWidget.get_default_question_state(self, question_key)` - Get default enabled state for a question.
  - ✅ `CheckinSettingsWidget.load_existing_data(self)` - Load existing check-in data.
  - ✅ `CheckinSettingsWidget.on_question_toggled(self, checked)` - Handle question checkbox toggle.
  - ✅ `CheckinSettingsWidget.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - ✅ `CheckinSettingsWidget.set_checkin_settings(self, settings)` - Set the check-in settings.
  - ✅ `CheckinSettingsWidget.set_question_checkboxes(self, questions)` - Set question checkboxes based on saved preferences.
  - ✅ `CheckinSettingsWidget.setup_connections(self)` - Setup signal connections.
  - ✅ `CheckinSettingsWidget.showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
  - ✅ `CheckinSettingsWidget.undo_last_question_delete(self)` - Undo the last question deletion.
  - ✅ `CheckinSettingsWidget.undo_last_time_period_delete(self)` - Undo the last time period deletion.

#### `ui/widgets/dynamic_list_container.py`
**Functions:**
- ✅ `__init__(self, parent, field_key)` - Initialize the object.
- ✅ `__post_init__(self)` - Post-initialization setup.
- ❌ `_add_blank_row(self)` - No description
- ❌ `_deduplicate_values(self, trigger_row, skip_warning)` - No description
- ❌ `_ensure_single_blank_row(self, current_blank)` - No description
- ❌ `_first_blank_index(self)` - No description
- ❌ `_on_preset_toggled(self, row)` - No description
- ❌ `_on_row_deleted(self, row)` - No description
- ❌ `_on_row_edited(self, row)` - No description
- ❌ `get_values(self)` - No description
- ❌ `set_values(self, selected)` - No description
**Classes:**
- ✅ `DynamicListContainer` - Manages a vertical list of DynamicListField rows.
  - ✅ `DynamicListContainer.__init__(self, parent, field_key)` - Initialize the object.
  - ✅ `DynamicListContainer.__post_init__(self)` - Post-initialization setup.
  - ❌ `DynamicListContainer._add_blank_row(self)` - No description
  - ❌ `DynamicListContainer._deduplicate_values(self, trigger_row, skip_warning)` - No description
  - ❌ `DynamicListContainer._ensure_single_blank_row(self, current_blank)` - No description
  - ❌ `DynamicListContainer._first_blank_index(self)` - No description
  - ❌ `DynamicListContainer._on_preset_toggled(self, row)` - No description
  - ❌ `DynamicListContainer._on_row_deleted(self, row)` - No description
  - ❌ `DynamicListContainer._on_row_edited(self, row)` - No description
  - ❌ `DynamicListContainer.get_values(self)` - No description
  - ❌ `DynamicListContainer.set_values(self, selected)` - No description

#### `ui/widgets/dynamic_list_field.py`
**Functions:**
- ✅ `__init__(self, parent, preset_label, editable, checked)` - Initialize the object.
- ❌ `_on_delete(self)` - No description
- ❌ `get_text(self)` - No description
- ❌ `is_blank(self)` - No description
- ❌ `is_checked(self)` - No description
- ✅ `on_checkbox_toggled(self)` - Called when user clicks the checkbox.
- ✅ `on_editing_finished(self)` - Notify parent container that text editing has finished (for duplicate validation).
- ✅ `on_text_changed(self)` - Called when user types in the text field.
- ❌ `set_checked(self, state)` - No description
- ❌ `set_text(self, text)` - No description
**Classes:**
- ✅ `DynamicListField` - Single row consisting of checkbox + editable text + delete button.
  - ✅ `DynamicListField.__init__(self, parent, preset_label, editable, checked)` - Initialize the object.
  - ❌ `DynamicListField._on_delete(self)` - No description
  - ❌ `DynamicListField.get_text(self)` - No description
  - ❌ `DynamicListField.is_blank(self)` - No description
  - ❌ `DynamicListField.is_checked(self)` - No description
  - ✅ `DynamicListField.on_checkbox_toggled(self)` - Called when user clicks the checkbox.
  - ✅ `DynamicListField.on_editing_finished(self)` - Notify parent container that text editing has finished (for duplicate validation).
  - ✅ `DynamicListField.on_text_changed(self)` - Called when user types in the text field.
  - ❌ `DynamicListField.set_checked(self, state)` - No description
  - ❌ `DynamicListField.set_text(self, text)` - No description

#### `ui/widgets/period_row_widget.py`
**Functions:**
- ✅ `__init__(self, parent, period_name, period_data)` - Initialize the object.
- ✅ `get_period_data(self)` - Get the current period data from the widget.
- ✅ `get_period_name(self)` - Get the current period name.
- ✅ `get_selected_days(self)` - Get the currently selected days.
- ✅ `is_valid(self)` - Check if the period data is valid.
- ✅ `load_days(self, days)` - Load day selections.
- ✅ `load_period_data(self)` - Load period data into the widget.
- ✅ `on_individual_day_toggled(self, checked)` - Handle individual day checkbox toggle.
- ✅ `on_select_all_days_toggled(self, checked)` - Handle 'Select All Days' checkbox toggle.
- ✅ `request_delete(self)` - Request deletion of this period row.
- ✅ `set_period_name(self, name)` - Set the period name.
- ✅ `setup_functionality(self)` - Setup the widget functionality and connect signals.
**Classes:**
- ✅ `PeriodRowWidget` - Reusable widget for editing time periods with days selection.
  - ✅ `PeriodRowWidget.__init__(self, parent, period_name, period_data)` - Initialize the object.
  - ✅ `PeriodRowWidget.get_period_data(self)` - Get the current period data from the widget.
  - ✅ `PeriodRowWidget.get_period_name(self)` - Get the current period name.
  - ✅ `PeriodRowWidget.get_selected_days(self)` - Get the currently selected days.
  - ✅ `PeriodRowWidget.is_valid(self)` - Check if the period data is valid.
  - ✅ `PeriodRowWidget.load_days(self, days)` - Load day selections.
  - ✅ `PeriodRowWidget.load_period_data(self)` - Load period data into the widget.
  - ✅ `PeriodRowWidget.on_individual_day_toggled(self, checked)` - Handle individual day checkbox toggle.
  - ✅ `PeriodRowWidget.on_select_all_days_toggled(self, checked)` - Handle 'Select All Days' checkbox toggle.
  - ✅ `PeriodRowWidget.request_delete(self)` - Request deletion of this period row.
  - ✅ `PeriodRowWidget.set_period_name(self, name)` - Set the period name.
  - ✅ `PeriodRowWidget.setup_functionality(self)` - Setup the widget functionality and connect signals.

#### `ui/widgets/task_settings_widget.py`
**Functions:**
- ✅ `__init__(self, parent, user_id)` - Initialize the object.
- ✅ `add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
- ✅ `find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
- ✅ `get_statistics(self)` - Get real task statistics for the user.
- ✅ `get_task_settings(self)` - Get the current task settings.
- ❌ `load_existing_data(self)` - No description
- ✅ `remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
- ✅ `set_task_settings(self, settings)` - Set the task settings.
- ✅ `setup_connections(self)` - Setup signal connections.
- ✅ `showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
- ✅ `undo_last_period_delete(self)` - Undo the last time period deletion.
**Classes:**
- ❌ `TaskSettingsWidget` - No description
  - ✅ `TaskSettingsWidget.__init__(self, parent, user_id)` - Initialize the object.
  - ✅ `TaskSettingsWidget.add_new_period(self, checked, period_name, period_data)` - Add a new time period using the PeriodRowWidget.
  - ✅ `TaskSettingsWidget.find_lowest_available_period_number(self)` - Find the lowest available integer (2+) that's not currently used in period names.
  - ✅ `TaskSettingsWidget.get_statistics(self)` - Get real task statistics for the user.
  - ✅ `TaskSettingsWidget.get_task_settings(self)` - Get the current task settings.
  - ❌ `TaskSettingsWidget.load_existing_data(self)` - No description
  - ✅ `TaskSettingsWidget.remove_period_row(self, row_widget)` - Remove a period row and store it for undo.
  - ✅ `TaskSettingsWidget.set_task_settings(self, settings)` - Set the task settings.
  - ✅ `TaskSettingsWidget.setup_connections(self)` - Setup signal connections.
  - ✅ `TaskSettingsWidget.showEvent(self, event)` - Handle widget show event.

Called when the widget becomes visible. Currently just calls the parent
implementation but can be extended for initialization that needs to happen
when the widget is shown.

Args:
    event: The show event object
  - ✅ `TaskSettingsWidget.undo_last_period_delete(self)` - Undo the last time period deletion.

#### `ui/widgets/user_profile_settings_widget.py`
**Functions:**
- ✅ `__init__(self, parent, user_id, existing_data)` - Initialize the object.
- ✅ `get_checkbox_group(self, group_name)` - Get checked values for a specific group.
- ✅ `get_personalization_data(self)` - Get all personalization data from the form, preserving existing data structure.
- ✅ `get_settings(self)` - Get the current user profile settings.
- ✅ `load_existing_data(self)` - Load existing personalization data into the form.
- ✅ `populate_timezones(self)` - Populate the timezone combo box with options and enable selection.
- ✅ `set_checkbox_group(self, group_name, values)` - Set checkboxes for a specific group based on values.
- ✅ `set_settings(self, settings)` - Set the user profile settings.
**Classes:**
- ✅ `UserProfileSettingsWidget` - Widget for user profile settings configuration.
  - ✅ `UserProfileSettingsWidget.__init__(self, parent, user_id, existing_data)` - Initialize the object.
  - ✅ `UserProfileSettingsWidget.get_checkbox_group(self, group_name)` - Get checked values for a specific group.
  - ✅ `UserProfileSettingsWidget.get_personalization_data(self)` - Get all personalization data from the form, preserving existing data structure.
  - ✅ `UserProfileSettingsWidget.get_settings(self)` - Get the current user profile settings.
  - ✅ `UserProfileSettingsWidget.load_existing_data(self)` - Load existing personalization data into the form.
  - ✅ `UserProfileSettingsWidget.populate_timezones(self)` - Populate the timezone combo box with options and enable selection.
  - ✅ `UserProfileSettingsWidget.set_checkbox_group(self, group_name, values)` - Set checkboxes for a specific group based on values.
  - ✅ `UserProfileSettingsWidget.set_settings(self, settings)` - Set the user profile settings.

### `user/` - User Data and Context

#### `user/user_context.py`
**Functions:**
- ✅ `__new__(cls)` - Create a new instance.
- ✅ `_get_active_schedules(self, schedules)` - Get list of currently active schedule periods.

Args:
    schedules: Dictionary containing schedule periods
    
Returns:
    list: List of active schedule period names
- ✅ `get_internal_username(self)` - Retrieves the internal_username from the user_data dictionary.

Returns:
    str: The current internal username, or None if not set.
- ✅ `get_preference(self, key)` - Retrieves a user preference from the user_data dictionary.

Args:
    key (str): The preference key to retrieve.

Returns:
    any: The current preference value, or None if not set.
- ✅ `get_preferred_name(self)` - Retrieves the preferred_name from the user_data dictionary.

Returns:
    str: The current preferred name, or None if not set.
- ✅ `get_user_context(self)` - Get comprehensive user context for AI conversations.

Returns:
    dict: Dictionary containing all relevant user context information
- ✅ `get_user_id(self)` - Retrieves the user_id from the user_data dictionary.

Returns:
    str: The current user ID, or None if not set.
- ✅ `load_user_data(self, user_id)` - Loads user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be loaded.
- ✅ `save_user_data(self, user_id)` - Saves user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be saved.
- ✅ `set_internal_username(self, internal_username)` - Sets the internal_username in the user_data dictionary.

Args:
    internal_username (str): The internal username to be set.
- ✅ `set_preference(self, key, value)` - Sets a user preference in the user_data dictionary.

Args:
    key (str): The preference key to be set.
    value (any): The preference value to be set.
- ✅ `set_preferred_name(self, preferred_name)` - Sets the preferred_name in the user_data dictionary.

Args:
    preferred_name (str): The preferred name to be set.
- ✅ `set_user_id(self, user_id)` - Sets the user_id in the user_data dictionary.

Args:
    user_id (str): The user ID to be set.
- ✅ `update_preference(self, key, value)` - Updates a user preference and saves the data.

Args:
    key (str): The preference key to be updated.
    value (any): The preference value to be set.
**Classes:**
- ❌ `UserContext` - No description
  - ✅ `UserContext.__new__(cls)` - Create a new instance.
  - ✅ `UserContext._get_active_schedules(self, schedules)` - Get list of currently active schedule periods.

Args:
    schedules: Dictionary containing schedule periods
    
Returns:
    list: List of active schedule period names
  - ✅ `UserContext.get_internal_username(self)` - Retrieves the internal_username from the user_data dictionary.

Returns:
    str: The current internal username, or None if not set.
  - ✅ `UserContext.get_preference(self, key)` - Retrieves a user preference from the user_data dictionary.

Args:
    key (str): The preference key to retrieve.

Returns:
    any: The current preference value, or None if not set.
  - ✅ `UserContext.get_preferred_name(self)` - Retrieves the preferred_name from the user_data dictionary.

Returns:
    str: The current preferred name, or None if not set.
  - ✅ `UserContext.get_user_context(self)` - Get comprehensive user context for AI conversations.

Returns:
    dict: Dictionary containing all relevant user context information
  - ✅ `UserContext.get_user_id(self)` - Retrieves the user_id from the user_data dictionary.

Returns:
    str: The current user ID, or None if not set.
  - ✅ `UserContext.load_user_data(self, user_id)` - Loads user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be loaded.
  - ✅ `UserContext.save_user_data(self, user_id)` - Saves user data using the new user management functions.

Args:
    user_id (str): The user ID whose data needs to be saved.
  - ✅ `UserContext.set_internal_username(self, internal_username)` - Sets the internal_username in the user_data dictionary.

Args:
    internal_username (str): The internal username to be set.
  - ✅ `UserContext.set_preference(self, key, value)` - Sets a user preference in the user_data dictionary.

Args:
    key (str): The preference key to be set.
    value (any): The preference value to be set.
  - ✅ `UserContext.set_preferred_name(self, preferred_name)` - Sets the preferred_name in the user_data dictionary.

Args:
    preferred_name (str): The preferred name to be set.
  - ✅ `UserContext.set_user_id(self, user_id)` - Sets the user_id in the user_data dictionary.

Args:
    user_id (str): The user ID to be set.
  - ✅ `UserContext.update_preference(self, key, value)` - Updates a user preference and saves the data.

Args:
    key (str): The preference key to be updated.
    value (any): The preference value to be set.

#### `user/user_preferences.py`
**Functions:**
- ✅ `__init__(self, user_id)` - Initialize UserPreferences for a specific user.

Args:
    user_id: The user's unique identifier
- ✅ `get_all_preferences(self)` - Get all preferences.
- ✅ `get_preference(self, key)` - Get a preference value.
- ✅ `is_schedule_period_active(user_id, category, period_name)` - Wrapper for :func:`core.schedule_management.is_schedule_period_active`.
- ✅ `load_preferences(self)` - Load user preferences using the new user management functions.
- ✅ `remove_preference(self, key)` - Remove a preference.
- ✅ `save_preferences(self)` - Save user preferences using the new user management functions.
- ✅ `set_preference(self, key, value)` - Set a preference and save it.
- ✅ `set_schedule_period_active(user_id, category, period_name, is_active)` - Wrapper for :func:`core.schedule_management.set_schedule_period_active`.
- ✅ `update_preference(self, key, value)` - Update a preference (alias for set_preference for consistency).
**Classes:**
- ✅ `UserPreferences` - Manages user preferences and settings.

Provides methods for loading, saving, and managing user preferences
including schedule period settings and general user preferences.
  - ✅ `UserPreferences.__init__(self, user_id)` - Initialize UserPreferences for a specific user.

Args:
    user_id: The user's unique identifier
  - ✅ `UserPreferences.get_all_preferences(self)` - Get all preferences.
  - ✅ `UserPreferences.get_preference(self, key)` - Get a preference value.
  - ✅ `UserPreferences.is_schedule_period_active(user_id, category, period_name)` - Wrapper for :func:`core.schedule_management.is_schedule_period_active`.
  - ✅ `UserPreferences.load_preferences(self)` - Load user preferences using the new user management functions.
  - ✅ `UserPreferences.remove_preference(self, key)` - Remove a preference.
  - ✅ `UserPreferences.save_preferences(self)` - Save user preferences using the new user management functions.
  - ✅ `UserPreferences.set_preference(self, key, value)` - Set a preference and save it.
  - ✅ `UserPreferences.set_schedule_period_active(user_id, category, period_name, is_active)` - Wrapper for :func:`core.schedule_management.set_schedule_period_active`.
  - ✅ `UserPreferences.update_preference(self, key, value)` - Update a preference (alias for set_preference for consistency).

