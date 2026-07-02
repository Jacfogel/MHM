# Product AI Context and Action Refactoring Plan

> **File**: `ai/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`
> **Audience**: Developers and AI collaborators working on MHM's product AI behavior
> **Purpose**: Refactor product AI around rich user context, prompt categories, and AI-driven action execution
> **Scope**: Product AI only. Excludes Codex/development-agent instructions and generated development-tool priority docs.
> **Last Updated**: 2026-07-02

## 1. Direction

The product AI should become an in-app assistant that can use the user's MHM data, answer from that data, decide when an app action is useful, execute that action through MHM's existing domain APIs, and report the result naturally.

This plan intentionally removes `safety_and_boundaries` as a standalone prompt category. The important product concerns for this overhaul are context completeness, action capability, accurate app behavior, and maintainable migration. Validation, permissions, and write integrity still matter, but they belong in execution plumbing and domain services rather than as a prompt category.

The target categories are:

- `identity_and_tone`
- `product_capabilities`
- `context_data_access`
- `context_selection_and_memory`
- `conversation_behavior`
- `action_interpretation`
- `action_execution`
- `fallback_behavior`

## 2. Current State

Product AI response behavior is currently influenced by:

| Source | Current responsibility | Refactor concern |
| --- | --- | --- |
| `resources/prompts/assistant_system_prompt.txt` | Main companion prompt for chat-style generation. | Too broad and mixes identity, behavior, context rules, and capability claims. |
| `resources/prompts/command.txt` | Structured command parsing prompt with live action injection. | Useful for command extraction, but separate from conversational context and result-aware responses. |
| `ai/prompt_manager.py` | Loads prompts, templates, custom prompt file, and inline helper prompts. | Should become a category loader/composer instead of holding scattered prompt bodies. |
| `ai/conversational_context/*` | Builds natural-language context sections for chat prompts. | Chat assembly now consumes `AIContextEnvelope`; remaining work is prompt-rule de-duplication and migration/reduction of `context_phraser.py` helper ownership. |
| `user/context_manager.py` and `ai/context_builder.py` | Gather profile, preferences, recent activity, mood trends, health guidance, and conversation history. | `ai/context_builder.py` now adapts from `AIContextEnvelope`; `user/context_manager.py` remains a separate context surface to review before final cleanup. |
| `ai/command_interpreter.py` and `ai/command_registry.py` | Mode detection, command prompts, clarification, command output cleanup, live action list injection. | Should evolve into action interpretation, not just command parsing. |
| `communication/message_processing/interaction_manager.py` | Routes incoming messages through flows, command parsing, structured dispatch, and contextual chat. | Best existing integration point for AI-driven actions. |
| `communication/message_processing/structured_command_dispatcher.py` | Dispatches parsed commands to registered handlers and optionally enhances responses. | Best initial action execution backend. |
| `communication/command_handlers/*` | Domain handlers for tasks, check-ins, profile, schedules, analytics, notebooks, account, health, and natural language. | Existing action implementation surface should be reused first. |
| `tasks/*`, `checkins/*`, `messages/*`, `storage/*`, `core/*` | Domain data APIs and persistence helpers. | AI must read/write through these APIs, not direct JSON file access. |
| `ai/fallback_responses/*` | Deterministic copy when LM Studio is unavailable or generation fails. | Should align with the same context/action categories instead of being a parallel personality path. |
| `ai/response_generator.py` and `ai/response_postprocess.py` | Prompt assembly, engagement appending, leak cleanup, truncation. | Post-processing should remain mechanical; action/result behavior should move into explicit flow. |
| `core/config.py`, `.env.example`, `CONFIGURATION_REFERENCE.md` | AI prompt paths, LM Studio settings, response limits, temperatures, command thresholds. | New context/action controls need central config and docs. |
| `tests/ai/*`, `tests/unit/*`, `tests/behavior/*` | Prompt manager, context, command injection, fallback, AI quality, action-boundary tests. | Tests must shift from exact prompt wording to context/action contracts. |

## 3. Target Architecture

### 3.0 Current implementation status

The first cleanup pass established the context and catalog foundation, but it did not implement AI action planning or execution.

Completed:

- `ai/context_service.py` owns the canonical `AIContextEnvelope` and builds structured context sections for account, preferences, personal context, schedules, tasks, check-ins, messages, notebooks, health, analytics, conversation, and action catalog data.
- `ai/context_builder.py` now reads from `AIContextEnvelope` and converts to the existing `ContextData` shape for current callers.
- `ai/conversational_context/assembly.py` now builds chat context from one envelope instead of loading domains directly through `user_context_manager`.
- `ai/action_catalog.py` provides metadata for live parser intents without importing communication handlers or executing actions.
- `ai/prompt_flows.py` names the major product-AI flows and records category ownership for chat, action interpretation, action-result response, and fallback response.

Still not implemented:

- No AI action planner exists yet.
- No AI action executor exists yet.
- No conversion from `AIActionRequest` to `ParsedCommand` has been wired into the communication/action-execution path.
- `PromptManager` has not been converted into a full category composer.
- `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` and `assistant_system_prompt.txt` still need rule de-duplication.

This means the current code is a useful foundation slice, not the completed product-AI overhaul.

### 3.1 AI request pipeline

Create a product-AI pipeline with explicit stages:

1. **Input routing**: `InteractionManager.handle_message` remains the channel-neutral entry point.
2. **Context build**: a new AI context service builds an `AIContextEnvelope` for the current user.
3. **Intent/action planning**: AI decides whether the message needs only a response, one or more app actions, or clarification.
4. **Action execution**: selected actions execute through existing command handlers/domain services.
5. **Result-aware response**: AI receives action results and user context, then produces the final user-visible response.
6. **Persistence**: conversation/action history is recorded through existing tracking helpers.

This keeps AI in the product loop without letting it bypass existing persistence and validation paths.

### 3.2 AIContextEnvelope

Introduce a single structured context object owned by `ai/context_service.py` or a similarly named module:

- `metadata`: user id, current timestamp, timezone, active channel, requested intent, context version.
- `account`: account/profile fields relevant to identity, enabled features, linked channels, and app settings.
- `preferences`: categories, task settings, message settings, notification preferences, natural-language defaults.
- `personal_context`: preferred name, notes for AI, goals, activities for encouragement, custom fields.
- `schedules`: active schedule periods, message windows, upcoming eligible sends.
- `tasks`: active tasks, completed task summaries, overdue/due-soon tasks, groups, tags, recurring defaults.
- `checkins`: latest check-in, recent check-ins, trend summaries, enabled questions, incomplete daily state.
- `messages`: categories, recent sent messages, recent message text snippets, delivery state where relevant.
- `notebooks`: notebooks/lists/notes metadata and searchable recent entries where existing APIs support it.
- `health`: existing wellness guidance summaries and available high-level health context.
- `analytics`: compact computed summaries from existing analytics helpers.
- `conversation`: recent chat interactions and current in-memory conversation history.
- `action_catalog`: actions currently available for this user, including required fields and feature gating.

The envelope should expose both:

- `structured`: dictionaries/lists for action planning and tests.
- `prompt_sections`: compact text generated from the structured data for local-model prompts.

### 3.3 Context selection and token management

The AI should have access to all relevant in-app data, but the model prompt should not blindly include every byte every time. Build context in two layers:

- **Full context envelope**: complete normalized data available to the planner and tests.
- **Prompt context view**: selected and summarized fields for the current request.

Selection rules:

- Always include identity/profile, feature state, active tasks summary, and current conversation.
- Include detailed records when the user asks about that domain or when the planner needs fields to execute an action.
- Prefer domain summaries for large collections, with targeted detail expansion by id/title/category/date.
- Record which context sections were included so test failures can explain missing context.

### 3.4 Action model

Introduce an action planning contract:

```text
AIActionPlan
- response_intent: answer_only | execute_action | clarify
- actions: list[AIActionRequest]
- clarification_question: optional string
- response_notes: optional text for final response generation

AIActionRequest
- action_name: canonical action id
- entities: normalized fields
- confidence: numeric score
- requires_confirmation: bool
- source_message: original user message
```

Initial action execution should reuse existing infrastructure:

- Keep `AIActionRequest` as AI-layer planning data.
- Convert action requests to `ParsedCommand` in the communication/action-execution layer, then dispatch through `dispatch_structured_command`.
- Return `InteractionResponse` plus structured execution metadata to the response stage.

Only add direct domain-service action executors when existing handlers cannot express a needed action cleanly.

## 4. Category Ownership

| Category | Owns | Initial implementation home |
| --- | --- | --- |
| `identity_and_tone` | Assistant personality, style, response length defaults, naming. | Prompt category file loaded by `PromptManager`. |
| `product_capabilities` | Accurate list of MHM features and actions the assistant can use. | Generated from handler/action registry plus feature flags. |
| `context_data_access` | Which in-app data sources are loaded into `AIContextEnvelope`. | Implemented in `ai/context_service.py`; uses `storage`, `tasks`, `checkins`, `messages`, `notebooks`, `core` APIs. |
| `context_selection_and_memory` | Request-aware context compression, summaries, expansion, and conversation/action history. | `ai/context_service.py` plus existing `core/response_tracking.py` and `ai/conversation_history.py`. |
| `conversation_behavior` | Greeting/direct-answer behavior, concise wording, natural follow-ups. | Prompt category plus `response_generator`; remove conversational additions from post-processing where possible. |
| `action_interpretation` | Decide whether to answer, clarify, or execute actions; normalize entities. | `ai/command_interpreter.py` evolved or a proposed action-planner module. |
| `action_execution` | Execute planned app actions and report results. | Proposed action-executor module backed by `dispatch_structured_command` and command handlers. |
| `fallback_behavior` | Deterministic responses when LM Studio or planning fails. | `ai/fallback_responses/`, updated to consume context/action categories. |

## 5. Refactoring Phases

### Phase 0 - Lock current behavior with tests

- Add tests that document the current prompt assembly, command dispatch path, fallback behavior, and context sections.
- Prefer behavior assertions over exact prompt-string assertions.
- Add a "no direct AI writes" test that ensures product AI action execution goes through handlers/domain APIs, not JSON file writes.
- Add context coverage tests that prove the AI context includes account, preferences, personal context, tasks, check-ins, messages, schedules, notebooks where data exists.

### Phase 1 - Canonical context envelope

- Add `AIContextEnvelope` and `AIContextSection` models.
- Build the envelope from existing APIs:
  - `get_user_data(user_id, "all", normalize_on_read=True)` for registered user data.
  - Task APIs for active/completed/due-soon task detail.
  - Check-in APIs for recent check-ins and daily status.
  - Message APIs for categories and recent sent messages.
  - Notebook handlers/data helpers for note/list metadata and recent entries.
  - Existing health/context/analytics helpers for summaries.
- Replace ad hoc context assembly in `user/context_manager.py`, `ai/context_builder.py`, and `ai/conversational_context/context_phraser.py` incrementally by reading from the envelope.
- Preserve current public entry points until all callers migrate, but do not add permanent shims.

### Phase 2 - Prompt categories

- Move prompt text into category files or structured constants under a product-AI prompt directory.
- Make `PromptManager` compose chat, action-planning, action-result, command, and fallback prompts from categories.
- Remove duplicated rules between `assistant_system_prompt.txt` and `CONVERSATIONAL_CONTEXT_INSTRUCTIONS`.
- Replace broad capability claims with registry-driven capability text.
- Keep `resources/prompts/command.txt` only as the command/action planning category source or migrate it into the new category structure.

### Phase 3 - Action catalog

- Build an action catalog from existing command handlers and parser intents.
- For each action, record:
  - canonical action name
  - handler or domain API target
  - required/optional fields
  - feature requirements
  - confirmation policy
  - result shape
- Initial catalog should cover tasks, check-ins, profiles, schedules, analytics, notebooks, messages/help, account linking, and health-related reads.
- Keep the command parser's live intent list as a source until the catalog fully replaces it.

### Phase 4 - AI action planning

- Add a proposed action-planner module to produce `AIActionPlan`.
- Support three outputs: answer only, clarify, execute action.
- For local models without native tool calling, use strict parseable text or JSON internally; do not expose planning output directly to users.
- Feed the planner the current message, prompt context view, and action catalog.
- Add parser hardening so malformed planner output falls back to clarification or answer-only behavior.

### Phase 5 - Action execution and result-aware response

- Add a proposed action-executor module.
- Convert action requests to `ParsedCommand` in the communication/action-execution layer and call `dispatch_structured_command`.
- Capture result metadata:
  - action attempted
  - action completed
  - handler response
  - created/updated object ids if present in `rich_data`
  - user-visible message
- Feed results into final response generation so the assistant can say what happened based on actual execution output.
- Keep domain writes in existing services such as `tasks.task_service`, `storage.user_data_write`, check-in managers, schedule handlers, and notebook handlers.

### Phase 6 - Context-aware final response

- Split final response generation from action planning.
- For answer-only requests, generate from `AIContextEnvelope` and selected prompt sections.
- For executed actions, generate from action result metadata plus updated context.
- For clarification, ask one specific question based on missing fields.
- Remove or reduce `enhance_conversational_engagement()` so follow-up behavior is prompt-owned and result-aware.

### Phase 7 - Fallback alignment

- Update fallbacks to accept `AIContextEnvelope` or a compact fallback context.
- Keep deterministic fallback categories, but align copy with product capabilities and action availability.
- Add action-aware fallback behavior:
  - If AI planning fails but rule-based parsing is confident, execute through the existing structured command path.
  - If LM Studio is unavailable for chat, answer from deterministic summaries where possible.
  - If action execution fails, return the handler error/result instead of generic support copy.

### Phase 8 - Retire old prompt/context paths

- Remove duplicated prompt text and obsolete context builders only after callers and tests are migrated.
- Use the legacy compatibility process for any retained bridge:
  - `--find` the old symbol/path first.
  - Add `# LEGACY COMPATIBILITY:` only if the bridge is truly needed.
  - Log bridge usage.
  - Add narrow `legacy_scan_patterns` and an inventory entry in `development_tools/config/jsons/DEPRECATION_INVENTORY.json`.
  - Add removal criteria and tests.
  - Run `--verify` before deletion.
- Prefer direct migration over compatibility shims.

## 6. Legacy Compatibility Requirements

Follow `ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md` throughout the refactor.

Required rules:

- Do not keep old prompt/context/action paths as undocumented fallbacks.
- Any temporary bridge must be marked with `# LEGACY COMPATIBILITY:`.
- Bridge usage must be logged when exercised.
- Each bridge must have a specific removal plan.
- Add or update `development_tools/config/jsons/DEPRECATION_INVENTORY.json` with `active_bridge` or `deprecated_in_use`.
- Use narrow scan patterns only; avoid broad terms like `legacy`, `context`, or `prompt`.
- Run targeted legacy checks before and after retiring old paths.

Likely bridge candidates if direct migration is not possible:

| Candidate | Preferred outcome | Bridge name if unavoidable |
| --- | --- | --- |
| `resources/prompts/assistant_system_prompt.txt` | Migrate to category-composed prompt files. | `product_ai_legacy_assistant_prompt_bridge` |
| `resources/prompts/command.txt` | Reuse as `action_interpretation` category or migrate to action catalog prompt. | `product_ai_legacy_command_prompt_bridge` |
| `PromptManager.get_prompt("wellness")` | Replace internal callers with category-composed prompt APIs. | `product_ai_wellness_prompt_api_bridge` |
| `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` | Replace with category-owned context/conversation prompt sections. | `product_ai_context_instruction_bridge` |
| `UserContextManager.get_ai_context` | Delegate to `AIContextEnvelope` until callers migrate. | `product_ai_user_context_bridge` |
| `CommandInterpreter.detect_mode` | Replace with action planner routing after parity tests pass. | `product_ai_mode_detection_bridge` |

## 7. Testing Plan

Add tests before each behavior-changing phase.

Minimum test set:

- `tests/unit/test_ai_context_service.py`
  - envelope includes every available registered data type for a populated user
  - prompt view includes relevant sections for task, check-in, schedule, message, notebook, and profile requests
  - large collections are summarized with traceable expansion metadata
- `tests/unit/test_ai_action_catalog.py`
  - catalog contains handler-backed actions
  - feature-gated actions are included/excluded correctly
  - required fields and result shapes are declared
- Proposed unit tests for the action planner.
  - answer-only, clarification, and execute-action plans parse correctly
  - malformed model output degrades to clarification or answer-only
- Proposed behavior tests for AI action execution.
  - create/update/complete/delete task actions execute through existing handlers
  - profile/schedule/notebook/check-in actions route through existing handlers
  - action results are reflected in the final response
- Proposed behavior tests for AI context answering.
  - AI can answer questions using tasks, check-ins, schedules, messages, notes, profile, preferences, and health summaries
  - responses update after an action changes data
- Proposed unit tests for product-AI cleanup boundaries.
  - temporary bridges are listed in deprecation inventory
  - no unmarked `LEGACY COMPATIBILITY` paths exist in the product AI refactor area

Verification commands:

```powershell
python -m pytest tests/unit/test_ai_context_service.py tests/unit/test_ai_action_catalog.py -q
python -m pytest tests/unit/test_ai_prompt_flows.py tests/unit/test_ai_action_catalog.py -q
python development_tools/legacy/fix_legacy_references.py --find "product_ai_legacy"
python development_tools/legacy/fix_legacy_references.py --verify "product_ai_legacy"
python development_tools/run_development_tools.py audit --quick
```

## 8. Acceptance Criteria

The overhaul is complete when:

- Product AI has one canonical context envelope for current-user in-app data.
- Prompt assembly is category-based and no longer duplicates the same behavioral rules in multiple files.
- Capability text is generated from actual available actions/features.
- AI can choose actions, execute them through existing handlers/domain APIs, and respond from actual execution results.
- Fallback responses use the same context/action model.
- Old prompt/context/mode paths are either removed or registered as temporary bridges with removal criteria.
- Legacy verification reports no active untracked bridge references.
- Context/action behavior is covered by unit and behavior tests.

## 9. First Implementation Slice

Start with the least risky useful slice:

1. [x] Add `AIContextEnvelope` and a context service that reads account, preferences, context, schedules, tasks, check-ins, messages, conversation history, and health summaries.
2. [x] Add tests proving the envelope sees all populated in-app data for a test user.
3. [x] Add an action catalog generated from existing handlers and parser intents.
4. [ ] Add tests proving task actions route through the communication/action-execution layer into `dispatch_structured_command`.
5. [ ] Only after those tests pass, move full prompt composition to categories.

This sequence gives the AI richer data access first, then action execution, then prompt cleanup. Item 4 and full `PromptManager` category composition in item 5 are still future work; `ai/prompt_flows.py` only names/categorizes flows.

## 10. Implementation Log

### 2026-07-01 - Canonical context envelope slice

Completed:

- Added `ai/context_service.py` with `AIContextEnvelope`, `AIContextSection`, and `build_ai_context_envelope`.
- The initial envelope implementation built structured sections for account, preferences, personal context, schedules, tasks, check-ins, messages, notebooks, health, analytics, conversation, and a placeholder action catalog.
- Added request-aware prompt section selection with `included_sections` metadata so tests can explain which context was included.
- Exported the new context service API from `ai/__init__.py`.
- Added `tests/unit/test_ai_context_service.py` coverage for populated product data and prompt-section selection.

Verified:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_ai_context_service.py -q
```

Notes:

- Superseded by the later action-catalog slice: the envelope's `action_catalog` section now contains live catalog data, not a placeholder.
- Superseded by the later ContextBuilder slice: `ai/context_builder.py` now reads from the envelope. `user/context_manager.py` remains a separate context surface to review before final prompt cleanup.
- No legacy compatibility bridge was added in this slice.

### 2026-07-01 - Handler-backed action catalog slice

Completed:

- Added `ai/action_catalog.py` with `AIActionCatalog`, `AIActionDefinition`, `AIActionField`, and `AIActionRequest`.
- The catalog reads live rule-based intent names through `ai.command_registry` and records action metadata without importing communication handlers or executing handlers directly.
- Kept `AIActionRequest` as AI-layer planning data; dispatcher conversion belongs in the future communication/action-execution slice.
- Replaced the context envelope's placeholder `action_catalog` section with live catalog data and prompt summary text.
- Exported the action catalog API from `ai/__init__.py`.
- Added `tests/unit/test_ai_action_catalog.py` coverage for task action metadata and confirmed `AIActionRequest` remains AI-layer planning data only.

Verified:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_ai_action_catalog.py tests/unit/test_ai_context_service.py -q
```

Notes:

- The first catalog pass focuses on live intent/handler discovery and task action field metadata. Future slices should expand field metadata for check-ins, profile, schedule, analytics, notebooks, messages/help, account, and health reads.
- The catalog still does not write data or call handlers. Future execution must delegate writes to existing handlers via `dispatch_structured_command`; no direct domain-write executor was added.
- A separate action-execution test is still required before introducing planner/executor code.

### 2026-07-01 - ContextBuilder overlap reduction

Completed:

- Updated `ContextBuilder.build_user_context` in `ai/context_builder.py` to build from `AIContextEnvelope` instead of separately calling `UserContextManager`, `get_recent_responses`, and direct `get_user_data` reads.
- Added a narrow conversion from `AIContextEnvelope` to the existing `ContextData` shape so current callers keep working while the canonical data source is centralized.
- Kept `ContextBuilder.analyze_context` in place as the shared check-in analytics implementation used by conversational phrasing and fallback tests.
- Added `tests/unit/test_ai_context_builder_envelope.py` to prove `ContextBuilder` delegates to `build_ai_context_envelope`.

Verified:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_ai_context_builder_envelope.py tests/unit/test_ai_context_service.py tests/unit/test_context_phraser.py tests/unit/test_context_analytics_shared_source.py -q
.\.venv\Scripts\python.exe -m pytest tests/behavior/test_ai_context_builder_behavior.py tests/behavior/test_ai_context_builder_coverage_expansion.py -q
```

Notes:

- No `LEGACY COMPATIBILITY` bridge was added. This is a direct internal migration that preserves the public `ContextData` return type temporarily.
- Remaining context overlap is primarily in `user/context_manager.py` and `ai/conversational_context/context_phraser.py`; those should be migrated to consume envelope sections or prompt views before prompt-category cleanup begins.

### 2026-07-01 - Prompt-flow categorization and chat assembly cleanup

Course correction:

- The refactor should make product-AI prompt flow ownership clearer, not just add context/action plumbing. This slice explicitly categorizes prompt flows and removes direct domain loading from chat prompt assembly.

Completed:

- Added `ai/prompt_flows.py` with named product-AI prompt flows:
  - `chat_response`
  - `action_interpretation`
  - `action_result_response`
  - `fallback_response`
- Each flow records its category ownership, context source, and prompt owner.
- Updated `ai/conversational_context/assembly.py` so `assemble_comprehensive_messages()` uses the `chat_response` flow and builds one `AIContextEnvelope`.
- Updated `build_context_parts()` to phrase from the envelope's structured sections instead of calling `user_context_manager` and domain-loading helpers directly.
- Kept `ai/conversational_context/context_phraser.py` as a wording/helper module for now; it no longer owns top-level chat context loading.
- Exported prompt-flow APIs from `ai/__init__.py`.
- Added tests for prompt-flow categorization and envelope-backed conversational assembly.

Verified:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_ai_prompt_flows.py tests/unit/test_conversational_context_envelope.py tests/unit/test_conversational_context_actionability.py tests/behavior/test_conversational_action_boundaries.py tests/ai/test_context_includes_recent_messages.py -q
```

Notes:

- Chat prompt data loading is now centralized through `AIContextEnvelope`.
- The next cleanup should split `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` into category-owned prompt files/constants and remove duplicated behavioral rules from `assistant_system_prompt.txt`.
- After that, remaining context-phraser helpers that still load domains directly should either accept envelope sections or be deleted if assembly no longer calls them.

### 2026-07-02 - Audit hygiene and plan alignment

Completed:

- Confirmed the context/action/prompt-flow work is a foundation slice, not a complete AI action system.
- Kept action execution explicitly out of `ai/action_catalog.py`; the catalog remains metadata-only.
- Removed stale documentation claims that action-catalog tests prove `dispatch_structured_command` routing.
- Clarified that action planner, action executor, full prompt category composition, and prompt-rule de-duplication remain future work.
- Refreshed development-tool audit artifacts after related cleanup.

Verified:

```powershell
.\.venv\Scripts\python.exe development_tools/run_development_tools.py audit --full
```

Result:

- Tier 3 test outcome: clean.
- Doc sync: pass.
- Static analysis: clean.
- Duplicate functions: 0.
- Facade/shim candidates: 0.
