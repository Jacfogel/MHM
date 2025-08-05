# TODO.md - MHM Project Tasks

## High Priority

### Test Failures - Critical Issues ⚠️ **OUTSTANDING**
- [ ] Fix test user creation failures in behavior tests
  - [ ] Resolve "name 'logger' is not defined" error in test utilities
  - [ ] Fix user data loading failures in account management tests
  - [ ] Fix missing 'schedules' and 'account' keys in test data
  - [ ] Fix CommunicationManager attribute errors in tests
- [ ] Fix AI chatbot system prompt test failures
  - [ ] Update test expectations for command prompt content
- [ ] Fix test utilities demo failures
  - [ ] Resolve basic user creation failures in demo tests

### Discord Bot Responsiveness ✅ **COMPLETED**
- [x] Fixed Discord bot not responding to messages
- [x] Added missing channel initialization step in service startup
- [x] Fixed Discord command registration conflict (duplicate help commands)
- [x] Verified Discord bot is now connected and responding

### Automatic Restart System ✅ **COMPLETED**
- [x] Implemented automatic restart monitor for stuck communication channels
- [x] Added background thread that checks every minute for channels stuck in INITIALIZING or ERROR states
- [x] Implemented smart restart logic with 5-minute cooldown between attempts
- [x] Added failure tracking to prevent infinite restart loops
- [x] Integrated restart monitor with CommunicationManager startup/shutdown
- [x] Tested and verified system works correctly with Discord bot

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