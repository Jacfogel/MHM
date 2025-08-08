# TODO.md - MHM Project Tasks

## High Priority

### Enhanced Logging System ✅ **RESOLVED**
- [x] Created organized logs directory structure (`logs/`, `logs/backups/`, `logs/archive/`)
- [x] Implemented component-based log separation (app, discord, ai, user_activity, errors)
- [x] Added structured logging with JSON metadata support
- [x] Implemented time-based log rotation (daily with 7-day retention)
- [x] Added log compression for files older than 7 days
- [x] Created ComponentLogger class for targeted logging
- [x] Updated configuration with new log file paths
- [x] Maintained backward compatibility with existing logging
- [x] **Component Logger Migration**: Updated 42 files across all priorities to use component-specific loggers
- [x] **Test Fixes**: Fixed 2 logger behavior test failures (missing `total_files` field and cleanup function bug)
- [x] **Documentation**: Moved LOGGING_GUIDE.md to logs directory for better organization

### Discord Heartbeat Warning Spam ✅ **RESOLVED**
- [x] Fixed Discord bot heartbeat warning spam that was flooding logs
- [x] Root cause: Event loop blocking Discord bot heartbeat mechanism
- [x] Implemented proper async task management in Discord bot main loop
- [x] Added intelligent logging filter to handle remaining warnings gracefully
- [x] Result: Log files reduced from 2MB+ to normal size (~100KB)

### UI Test Failures - Critical Issues ✅ **RESOLVED**
### Check-in Flow Behavior & Stability (New)
- [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_daily_checkin`, `FLOW_DAILY_CHECKIN`, `get_recent_daily_checkins`, `store_daily_checkin_response`)
- [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
- [ ] Consider inactivity-based expiration in addition to outbound-triggered expiry (optional)

- [x] Fix widget constructor parameter mismatches in simple UI tests
  - [x] Fix CategorySelectionWidget and ChannelSelectionWidget user_id parameter issues
  - [x] Fix DynamicListField and DynamicListContainer title/items parameter issues
- [x] Fix account creation UI test data issues
  - [x] Resolve user context update failures in integration tests
  - [x] Fix missing account data in persistence tests
  - [x] Fix duplicate username handling test failures

### Pytest Marker Application Project ✅ **COMPLETED**
- [x] Applied pytest markers to all test files across 4 directories (unit, behavior, integration, UI)
- [x] Enhanced test organization with 101 specific marker application tasks completed
- [x] Fixed critical UI dialog issue where dialogs were appearing during automated testing
- [x] Enhanced test runner with new UI test mode and improved filtering capabilities
- [x] Verified marker functionality with comprehensive testing of all marker combinations
- [x] Improved test filtering for selective execution (unit, behavior, integration, ui, critical, regression, smoke)
- [x] Resolved test infrastructure issues by removing problematic test files
- [x] Updated documentation with completion status
- [x] Cleaned up project files and moved documentation to appropriate locations

### Test Infrastructure Cleanup ✅ **COMPLETED**
- [x] Removed debug scripts not part of formal test suite (`test_user_creation_debug.py`)
- [x] Removed redundant example files (`tests/examples/test_marker_examples.py`)
- [x] Cleaned up empty directories (`tests/examples/`)
- [x] Moved project documentation to appropriate locations (`tests/` directory)
- [x] Verified test collection still works correctly after cleanup (630 tests collected)

### Test Failures - Critical Issues ✅ **RESOLVED**
- [x] Fix test user creation failures in behavior tests
  - [x] Resolve "name 'logger' is not defined" error in test utilities
  - [x] Fix user data loading failures in account management tests
  - [x] Fix missing 'schedules' and 'account' keys in test data
  - [x] Fix CommunicationManager attribute errors in tests
- [x] Fix AI chatbot system prompt test failures
  - [x] Update test expectations for command prompt content
- [x] Fix test utilities demo failures
  - [x] Resolve basic user creation failures in demo tests

### Discord Bot Responsiveness ✅ **COMPLETED**
- [x] Fixed Discord bot not responding to messages
- [x] Added missing channel initialization step in service startup
- [x] Fixed Discord command registration conflict (duplicate help commands)
- [x] Verified Discord bot is now connected and responding

### Channel Interaction Implementation Plan ✅ **COMPLETED**
- [x] Enhanced Discord Commands - !help, !tasks, !checkin, !profile, !schedule, !messages, !status
- [x] Natural Language Processing - Intent recognition, entity extraction, context awareness
- [x] Discord-Specific Features - Rich embeds, buttons, interactive elements (basic implementation)
- [ ] Advanced Integration - Cross-channel sync, advanced analytics

### LM Studio AI Model Configuration ✅ **COMPLETED**
- [x] Centralized timeouts and confidence thresholds for the LM Studio AI model
- [x] Updated all AI-related components to use centralized configuration
- [x] Created comprehensive test script to verify configuration
- [x] Updated documentation

### AI Response Length Centralization ✅ **COMPLETED**
- [x] Centralized AI model response character length in config
- [x] Added AI_MAX_RESPONSE_LENGTH configuration constant
- [x] Updated bot/ai_chatbot.py to use centralized response length
- [x] Updated bot/interaction_manager.py to use centralized response length
- [x] Verified both modules use consistent 150-character limit
- [x] Created and ran verification test script

## Medium Priority

### User Experience Improvements
- [ ] Enhanced error messages for better user feedback
- [ ] Improved natural language processing accuracy
- [ ] Better conversation flow management

### Performance Optimizations
- [ ] Optimize AI response times
- [ ] Improve message processing efficiency
- [ ] Reduce memory usage

## Low Priority

### Documentation
- [ ] Update user guides
- [ ] Improve code documentation
- [ ] Create troubleshooting guides

### Testing
- [ ] Add more comprehensive tests
- [ ] Improve test coverage
- [ ] Add integration tests

## Completed Tasks

### UI Test Failures Resolution ✅ **COMPLETED** (2025-08-07)
### Check-in Flow Improvements ✅ **COMPLETED** (2025-08-07)
- [x] Expire check-in after next unrelated outbound message
- [x] Add `/checkin` trigger and improved intro prompt
- [x] Legacy shims for check-in APIs to keep tests/modules working
- [x] Fix restart monitor iteration error
- [x] Fixed widget constructor parameter mismatches (4 failures)
  - [x] CategorySelectionWidget - removed user_id parameter, uses parent only
  - [x] ChannelSelectionWidget - removed user_id parameter, uses parent only
  - [x] DynamicListField - fixed parameter names (preset_label, editable, checked)
  - [x] DynamicListContainer - fixed parameter names (field_key)
- [x] Fixed account creation UI test data issues (3 failures)
  - [x] Updated tests to use proper user ID lookup from test utilities
  - [x] Fixed user context update failures in integration tests
  - [x] Fixed missing account data in persistence tests
  - [x] Fixed duplicate username handling test failures
- [x] Updated test expectations to match actual test utility behavior
- [x] **Result**: All 591 tests now passing (100% success rate)

### Discord Enhancement ✅ **COMPLETED**
- [x] Enhanced Discord Commands - !help, !tasks, !checkin, !profile, !schedule, !messages, !status
- [x] Natural Language Processing - Intent recognition, entity extraction, context awareness
- [x] Discord-Specific Features - Rich embeds, buttons, interactive elements (basic implementation)
- [ ] Advanced Integration - Cross-channel sync, advanced analytics

### AI Configuration Centralization ✅ **COMPLETED**
- [x] Centralized LM Studio AI model timeouts and confidence thresholds
- [x] Updated bot/ai_chatbot.py to use centralized configuration
- [x] Updated bot/enhanced_command_parser.py to use centralized configuration
- [x] Created test script to verify all configurations are properly set
- [x] Updated CHANGELOG files

### Task Response Quality Improvements ✅ **COMPLETED**
- [x] Fixed task formatting - No more JSON or system prompts in responses
- [x] Fixed response length - All responses now under 200 characters, no more truncation
- [x] Fixed task suggestions - Contextual suggestions based on actual task data
- [x] Fixed reminder format - Time-based reminders ("30 minutes to an hour before", etc.)
- [x] Fixed AI enhancement - Properly disabled for task responses to prevent formatting issues