# Run AI Functionality Tests


> **File**: `.cursor/commands/ai-functionality-tests.md`
## Overview
Execute AI functionality tests (manual review tests) that validate AI response quality, performance, and edge cases. **The AI (you) MUST review the results and document findings directly in the test results file.** This includes validating PASS/PARTIAL/FAIL grading and identifying tests that were incorrectly graded.

## Steps
1. Run the AI functionality tests:
   ```powershell
   python tests/ai/run_ai_functionality_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Some tests failed or were partial" -ForegroundColor Yellow }
   ```

2. **CRITICAL: AI Review of Results**:
   - Open `tests/ai/results/ai_functionality_test_results_latest.md`
   - Review EVERY test result, not just PARTIAL/FAIL
   - Validate that PASS/PARTIAL/FAIL grading is correct for each test
   - **MOST IMPORTANT: Check for prompt-response mismatches** - Automated validation struggles with this, so it's YOUR KEY RESPONSIBILITY
   - Look for:
     - **Prompt-response mismatches** (e.g., "How are you?" gets redirected instead of answered, "Tell me something helpful" gets questions instead of helpful info, "Tell me about yourself" asks for user info instead of describing AI)
     - AI fabricating data when none exists (check-ins, conversation history)
     - Code fragments in command responses
     - Incorrect assumptions about context that was provided
     - Vague references ("that", "it") when context is missing
     - Inappropriate assumptions from simple greetings (e.g., assuming user is overwhelmed from "Hello")
   - Document findings by adding an "AI Review of Test Results" section at the end of the results file
   - **Add "Manual Review Notes" to each affected test result** documenting the specific prompt-response mismatch or issue found
   - Include:
     - Tests with incorrect grading (PASS → FAIL, etc.)
     - Specific issues found (fabricated data, mismatched prompts, etc.)
     - Test validation improvements needed
   - Update the summary at the top to note AI review was performed

3. Check logs (if needed):
   - `tests/logs/test_consolidated.log` - Component logs from `mhm.*` loggers
   - `tests/logs/test_run.log` - Test execution logs from the test runner
   - Both files use consolidated logging (no individual component log files)

4. For failures or partials:
   - Identify root causes (response quality issues, unexpected content, etc.)
   - Determine if fixes are needed in the AI system or test validation
   - Update test plan or test validation rules if needed

5. Document findings:
   - **MUST add "Manual Review Notes" to each affected test result** in `tests/ai/results/ai_functionality_test_results_latest.md`
   - **MUST add AI review section to `tests/ai/results/ai_functionality_test_results_latest.md`** at the end
   - Include corrected grading for any tests (e.g., "T-12.2: PASS → FAIL")
   - Specifically note prompt-response mismatches found (automated validation struggles with these)
   - Note what validation improvements are needed
   - Update `tests/AI_FUNCTIONALITY_TEST_PLAN.md` with status changes if needed

## Test Details
- **Test Type**: Manual review tests (AI reviews responses automatically, human review may be needed for complex issues)
- **Automatic Validation**: Tests automatically check for (but struggles with nuanced intent matching):
  - Meta-text (e.g., "Response 1:", "Mode:", test artifacts)
  - Code fragments in responses (Python imports, functions, code blocks, etc.)
  - Response truncation (mid-sentence endings at common truncation points)
  - Basic response-prompt mismatches (keyword-based checks, e.g., "Tell me a short story" should mention stories)
  - AI fabricating data (e.g., claiming check-ins exist when there are none)
  - AI referencing non-existent context (e.g., conversation history, check-in data)
  - Inappropriate assumptions (past dates, assumed locations)
  - Role reversal patterns (basic detection)
  - Response appropriateness (length, topic relevance)
- **Manual Review Required**: Automated validation STRUGGLES with prompt-response intent matching:
  - Cannot reliably detect if "How are you?" gets redirected vs. answered
  - Cannot reliably detect if "Tell me something helpful" provides info vs. asks questions
  - Cannot reliably detect if responses actually address prompt intent (vs. just containing keywords)
  - **This is YOUR KEY RESPONSIBILITY** - you must manually check each response matches its prompt
- **Test Categories**: 
  - Core functionality (response generation, mode detection)
  - Integration (context, conversation history)
  - Error handling
  - Cache behavior
  - Performance metrics
  - Response quality
  - Edge cases

## Output Files
- **Results**: `tests/ai/results/ai_functionality_test_results_latest.md` (also timestamped versions, last 10 kept)
- **Logs**: `tests/logs/test_consolidated.log` (component logs), `tests/logs/test_run.log` (test execution)
- **No Individual Logs**: Component-specific log files (ai.log, app.log, etc.) are NOT created

## Response Template
#### Test Results
- Status: Passed / Partial / Failed
- Total Tests: X
- Passed: X | Partial: X | Failed: X
- Performance: Average response time Xs (if applicable)

#### Issues Found
- Test ID: Description of issue
- Root Cause: Analysis of why this occurred
- Recommendation: Suggested fix or follow-up

#### Follow-up
- Tests needing attention
- Validation rules that may need adjustment
- System improvements identified

## Additional Guidance
- See `tests/AI_FUNCTIONALITY_TEST_PLAN.md` for complete test plan and coverage
- See `tests/ai/ai_response_validator.py` for validation rules and patterns
- Deterministic tests moved to `tests/unit/test_ai_deterministic.py` (run via pytest)

## Test Result Interpretation

### Response Sections
- **Prompt**: The user input provided to the AI
- **Response**: The full AI response (for multi-turn conversations, all responses separated by `|`)
- **Notes**: Test-specific observations (does NOT duplicate response text)
- **Context Available**: Actual context details provided to the AI (user_name, mood_trend, recent_topics, checkins_enabled, etc.) - only shows meaningful values, not empty/False/0
- **Manual Review Notes**: Issues identified during AI review (prompt-response mismatches, grading corrections, etc.)

### Common Issues

**Truncation Issues**:
- Responses ending at 200/300 characters mid-sentence indicate truncation problems
- May be due to `max_tokens` limits or model stopping early

**AI Fabrication**:
- AI claims check-ins, tasks, or data exist when context shows none
- Test T-4.1 explicitly detects this issue

**Prompt-Response Mismatches** (CRITICAL - Automated validation struggles with this):
- **YOUR KEY RESPONSIBILITY**: Check if responses actually address prompts, not just contain keywords
- Common patterns to watch for:
  - "How are you?" / "How are you doing today?" → Should acknowledge/greet, not redirect to "What's on your mind?" or "How can I help?"
  - "Tell me something helpful" → Should provide helpful information, not ask questions
  - "How are you feeling?" → Should answer how AI is feeling, not redirect to "How can I help today?"
  - "Tell me about yourself" → Should describe AI capabilities/personality, not ask for user's name (role reversal)
  - "Hello" / "Hi" → Should not assume negative mental state (overwhelmed, anxious) without context
  - "How am I doing?" → Should ask for information explicitly when context missing, not use vague references ("that", "it")
- Automated validator has basic checks but struggles with nuanced intent matching - manual review is essential

**Code Fragments**:
- Command responses should NOT include Python code, imports, or code blocks
- Extraction logic should remove these automatically

**Missing Context Handling**:
- When context is missing, AI should ask for information explicitly (e.g., "I don't know how you're feeling today, but we can try to figure it out together. How about you tell me about your day so far?")
- Generic responses like "How are you feeling?" are not helpful
- Responses should NOT use vague references like "that" or "it" when no previous context exists

**Incorrect Grading to Watch For**:
- **Tests marked PASS but response doesn't match prompt intent** (MOST COMMON - automated validation struggles here)
- Tests marked PASS but AI fabricates data (check-ins, conversation history)
- Tests marked PASS but contains code fragments
- Tests marked PASS/PARTIAL but should be FAIL due to critical issues (prompt-response mismatches, meta-text leaks, etc.)

## AI Review Checklist

When reviewing test results, validate (in priority order):

- [ ] **Prompt-Response Matching** (HIGHEST PRIORITY - automated validation struggles here):
  - Does "How are you?" get a greeting/acknowledgment or just redirect?
  - Does "Tell me something helpful" provide helpful info or just ask questions?
  - Does "Tell me about yourself" describe AI or ask for user info?
  - Does "Hello" assume negative mental state without context?
  - Does "How am I doing?" ask explicitly or use vague references?
  - Does response actually address the prompt intent, not just contain keywords?
- [ ] **Correct Grading**: Does the PASS/PARTIAL/FAIL status match the actual response quality?
- [ ] **No Fabricated Data**: Does AI claim check-ins/conversations exist when context shows none?
- [ ] **Code Fragments**: Are command responses clean (no Python code, imports, etc.)?
- [ ] **Context Appropriateness**: Does AI reference context that was actually provided? (Check Context Available section)
- [ ] **Manual Review Notes**: Have findings been added to each affected test's "Manual Review Notes" section?
- [ ] **Documentation**: Have findings been added to the "AI Review of Test Results" section at the end of the file?

