# Manual Discord Testing Guide

## Overview
This guide provides step-by-step instructions for manually testing Discord commands to verify the Discord Commands implementation is working correctly.

## Prerequisites
- Discord bot token configured (`DISCORD_BOT_TOKEN`)
- Bot invited to test server with appropriate permissions
- MHM service running (`python run_headless_service.py start`)
- Test user account available

## Testing Checklist

### A. Profile Display Testing

#### Test 1: Natural Language Profile Request
1. **Send**: `show my profile`
2. **Verify**:
   - Response shows formatted text (not raw JSON)
   - Profile fields display correctly
   - No truncation or formatting issues
   - Response includes "**Your Profile:**" header
   - Fields show as bullet points with proper formatting

#### Test 2: Slash Command Profile
1. **Send**: `/profile`
2. **Verify**:
   - Rich embed appears with organized fields
   - Fields are properly structured in Discord embed format
   - Suggestions appear as buttons (if implemented)
   - No JSON syntax visible

#### Test 3: Bang Command Profile
1. **Send**: `!profile`
2. **Verify**:
   - Same formatting as natural language
   - Clean text output
   - No duplicate sections

### B. Help System Testing

#### Test 4: General Help
1. **Send**: `help`
2. **Verify**:
   - Categorized command list appears
   - Natural language is emphasized
   - Readable formatting with proper sections
   - All 6 categories present: Tasks, Check-ins, Profile, Analytics, Schedule, System

#### Test 5: Commands List
1. **Send**: `commands`
2. **Verify**:
   - Complete command list appears
   - All 6 categories present with proper headers
   - Natural language, explicit, and slash commands shown
   - Command types explanation provided
   - Flow management guidance included

#### Test 6: Examples
1. **Send**: `examples`
2. **Verify**:
   - Natural language examples provided
   - Practical examples like "call mom tomorrow"
   - Examples are actionable and useful
   - Category-specific examples available

#### Test 7: Category-Specific Help
1. **Send**: `help tasks`
2. **Verify**:
   - Task-specific examples provided
   - Commands are actionable
   - Examples include "create task", "list tasks", etc.

3. **Send**: `help checkin`
4. **Verify**:
   - Check-in specific examples
   - Conversational flow explanation
   - Commands like "start checkin", "checkin status"

5. **Send**: `help profile`
6. **Verify**:
   - Profile-specific examples
   - Commands like "show profile", "update name"

### C. Command Interaction Methods

#### Test 8: Natural Language Commands
1. **Send**: `create a task to buy groceries`
2. **Verify**: Task creation works correctly

3. **Send**: `show my tasks`
4. **Verify**: Task list displays properly

5. **Send**: `start a check-in`
6. **Verify**: Check-in flow begins

#### Test 9: Slash Commands
1. **Send**: `/tasks`
2. **Verify**: Task list displays

3. **Send**: `/profile`
4. **Verify**: Profile displays

5. **Send**: `/checkin`
6. **Verify**: Check-in flow begins

7. **Send**: `/help`
8. **Verify**: Help system works

#### Test 10: Bang Commands
1. **Send**: `!tasks`
2. **Verify**: Task list displays

3. **Send**: `!profile`
4. **Verify**: Profile displays

5. **Send**: `!help`
6. **Verify**: Help system works

### D. Flow Management

#### Test 11: Check-in Flow
1. **Start**: Send `start a check-in` or `/checkin`
2. **Verify**: Conversational interaction begins
3. **Test Cancel**: Send `cancel` or `/cancel`
4. **Verify**: Flow exits properly with confirmation

#### Test 12: Flow Clear
1. **Start**: Any flow
2. **Send**: `clear flows` or `/clear`
3. **Verify**: Flow exits and system confirms

### E. Edge Cases

#### Test 13: Unknown Commands
1. **Send**: `unknown command`
2. **Verify**: Graceful fallback response
3. **Verify**: Helpful error message

#### Test 14: Malformed Commands
1. **Send**: `!invalid`
2. **Verify**: Helpful error message
3. **Verify**: Suggestion to use help

#### Test 15: Incomplete Profile Data
1. **Create**: User with minimal profile data
2. **Send**: `show my profile`
3. **Verify**: Graceful handling of missing fields
4. **Verify**: Shows "Not set" or "Unknown" for missing data

## Expected Results

### Profile Display
- ✅ Clean formatted text (no JSON syntax)
- ✅ Proper markdown formatting
- ✅ All profile sections render correctly
- ✅ Rich embeds work for slash commands
- ✅ No duplicate formatting code paths

### Help System
- ✅ Comprehensive command discovery
- ✅ All command categories documented
- ✅ Natural language emphasized as primary method
- ✅ Practical examples provided
- ✅ Category-specific help available

### Command Interaction
- ✅ Natural language commands work
- ✅ Slash commands work
- ✅ Bang commands work
- ✅ Flow management works
- ✅ Edge cases handled gracefully

## Troubleshooting

### Common Issues
1. **Bot not responding**: Check if service is running
2. **Commands not working**: Verify bot has proper permissions
3. **Formatting issues**: Check for JSON syntax in responses
4. **Help not comprehensive**: Verify all categories are present

### Debug Steps
1. Check service status: `python run_headless_service.py status`
2. Check logs: `logs/discord.log`
3. Verify bot permissions in Discord server
4. Test with minimal commands first

## Success Criteria
- All profile displays show clean formatted text
- Help system provides comprehensive command discovery
- All command interaction methods work correctly
- Flow management works as expected
- Edge cases handled gracefully
- No JSON syntax visible in user-facing responses

## Documentation
- Record any issues found
- Screenshot any problems
- Document any unexpected behaviors
- Update this guide with any new findings
