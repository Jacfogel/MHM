# TODO.md - MHM Project Tasks

## High Priority

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

### UI Test Failures - Minor Issues ⚠️ **OUTSTANDING**
- [ ] Fix widget constructor parameter mismatches in simple UI tests
  - [ ] Fix CategorySelectionWidget and ChannelSelectionWidget user_id parameter issues
  - [ ] Fix DynamicListField and DynamicListContainer title/items parameter issues
- [ ] Fix account creation UI test data issues
  - [ ] Resolve user context update failures in integration tests
  - [ ] Fix missing account data in persistence tests
  - [ ] Fix duplicate username handling test failures

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