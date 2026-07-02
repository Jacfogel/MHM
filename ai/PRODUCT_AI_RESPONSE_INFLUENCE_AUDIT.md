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

- `persona`
- `reply_rules`
- `data_honesty`
- `action_boundaries`
- `available_actions` (runtime injection from `AIActionCatalog`, not a prompt file)

Command parsing remains separate in `resources/prompts/command.txt`.

## 2. Current State

Product AI response behavior is currently influenced by:

| Source | Current responsibility | Refactor concern |
| --- | --- | --- |
| `resources/prompts/assistant_system_prompt.txt` | Legacy custom-prompt override path when `AI_USE_CUSTOM_PROMPT` is enabled. | Now mirrors `persona.txt`; chat composition no longer stacks this on top of category files. |
| `resources/prompts/command.txt` | Structured command parsing prompt with live action injection. | Useful for command extraction, but separate from conversational context and result-aware responses. |
| `ai/prompts/manager.py` | Loads prompts, templates, custom prompt file, and composes product-AI category prompts. | Category composition is in place; inline bodies for `create_task_prompt()` / `create_checkin_prompt()` remain temporary. |
| `ai/context/assembly.py` and `ai/context/phraser.py` | Builds natural-language context sections for chat prompts from `AIContextEnvelope`. | `ai/context/phraser.py` helper ownership can still be reduced over time. |
| `user/context_manager.py` and `ai/context/builder.py` | Gather profile, preferences, recent activity, mood trends, health guidance, and conversation history. | `ai/context/builder.py` adapts from `AIContextEnvelope`; `user/context_manager.py` remains a separate context surface to review before final cleanup. |
| `ai/prompts/command_interpreter.py` and `ai/prompts/command_registry.py` | Mode detection, command prompts, clarification, command output cleanup, live action list injection. | Should evolve into action interpretation, not just command parsing. |
| `communication/message_processing/interaction_manager.py` | Routes incoming messages through flows, command parsing, structured dispatch, and contextual chat. | Best existing integration point for AI-driven actions. |
| `communication/message_processing/structured_command_dispatcher.py` | Dispatches parsed commands to registered handlers and optionally enhances responses. | Best initial action execution backend. |
| `communication/command_handlers/*` | Domain handlers for tasks, check-ins, profile, schedules, analytics, notebooks, account, health, and natural language. | Existing action implementation surface should be reused first. |
| `tasks/*`, `checkins/*`, `messages/*`, `storage/*`, `core/*` | Domain data APIs and persistence helpers. | AI must read/write through these APIs, not direct JSON file access. |
| `ai/fallback/*` | Deterministic copy when LM Studio is unavailable or generation fails. | Should align with the same context/action categories instead of being a parallel personality path. |
| `ai/chat/response_generator.py` and `ai/chat/response_postprocess.py` | Prompt assembly, leak cleanup, truncation. | Post-processing is mechanical only; engagement follow-ups are owned by `reply_rules.txt`. |
| `core/config.py`, `.env.example`, `CONFIGURATION_REFERENCE.md` | AI prompt paths, LM Studio settings, response limits, temperatures, command thresholds. | New context/action controls need central config and docs. |
| `tests/ai/*`, `tests/unit/*`, `tests/behavior/*` | Prompt manager, context, command injection, fallback, AI quality, action-boundary tests. | Tests must shift from exact prompt wording to context/action contracts. |

## 3. Target Architecture

### 3.0 Current implementation status

The first cleanup pass established the context and catalog foundation, but it did not implement AI action planning or execution.

Completed:

- `ai/context/service.py` owns the canonical `AIContextEnvelope` and builds structured context sections for account, preferences, personal context, schedules, tasks, check-ins, messages, notebooks, health, analytics, conversation, and action catalog data.
- `ai/context/builder.py` reads from `AIContextEnvelope` and converts to the existing `ContextData` shape for current callers.
- `ai/context/assembly.py` builds chat context from one envelope instead of loading domains directly through `user_context_manager`.
- `ai/prompts/action_catalog.py` provides metadata for live parser intents without importing communication handlers or executing actions.
- `ai/prompts/flows.py` names the major product-AI flows and records category ownership for chat, action interpretation, action-result response, and fallback response.
- Product-AI prompt categories consolidated to four files under `resources/prompts/product_ai/` (`persona`, `reply_rules`, `data_honesty`, `action_boundaries`) plus runtime `available_actions` injection. Removed `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` and duplicate stacking of `assistant_system_prompt.txt` in chat assembly.

Still not implemented:

- No AI action planner exists yet.
- No AI action executor exists yet.
- No conversion from `AIActionRequest` to `ParsedCommand` has been wired into the communication/action-execution path.
- `action_interpretation` and `action_result_response` flows are declared but not yet wired into runtime composition beyond tests.

### 3.0.1 Prompt cleanup problem statement

The next cleanup should reduce prompt sprawl before adding more AI behavior. Current prompt behavior is hard to reason about because the same instructions are split across the companion prompt, contextual chat instructions, command parsing prompt, inline fallback prompts, and response post-processing. This makes behavior harder to tune, and it encourages future features to add more prompt text in whichever file is closest.

The prompt system should become easy to use and expand by making one clear rule true:

> Product AI flows choose categories; categories own prompt text; runtime services provide data and actions.

That means:

- `PromptManager` should compose prompts from named categories instead of exposing broad prompt-type bodies as the primary API.
- Context text should be supplied by `AIContextEnvelope` prompt sections, not handwritten directly into behavioral prompt rules.
- Capability text should come from `AIActionCatalog` and feature state, not static claims in `assistant_system_prompt.txt`.
- Chat behavior, action interpretation, action-result response, and fallback response should share category text where appropriate instead of duplicating wording.
- Post-processing should only clean formatting/leaks, not compensate for unclear prompt ownership.

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

Introduce a single structured context object owned by `ai/context/service.py` or a similarly named module:

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

| Category | Owns | Implementation home |
| --- | --- | --- |
| `persona` | Assistant personality, style, response length defaults, naming. | `resources/prompts/product_ai/persona.txt` |
| `reply_rules` | Greeting/direct-answer behavior, concise wording, natural follow-ups. | `resources/prompts/product_ai/reply_rules.txt` |
| `data_honesty` | Context visibility, data accuracy, feature availability, health personalization. | `resources/prompts/product_ai/data_honesty.txt` |
| `action_boundaries` | No false CRUD claims; offer language for action-like chat. | `resources/prompts/product_ai/action_boundaries.txt` |
| `available_actions` | Accurate list of MHM features and actions the assistant can use. | Runtime injection from `AIActionCatalog` / envelope (not a static file) |
| User context data | Which in-app data is loaded and phrased for the model. | `ai/context/service.py` + `ai/context/assembly.py` |
| Command parsing | Strict `ACTION:` extraction format. | `resources/prompts/command.txt` (separate from chat categories) |
| Action execution | Execute planned app actions and report results. | Future planner/executor via `dispatch_structured_command` (not prompt text) |
| Fallback copy | Deterministic responses when LM Studio or planning fails. | `ai/fallback/` using the same category contract where applicable |

### 4.1 Current prompt-source inventory

| Source | Status |
| --- | --- |
| `resources/prompts/product_ai/*.txt` | Four flow-aligned category files (`persona`, `reply_rules`, `data_honesty`, `action_boundaries`). |
| `resources/prompts/assistant_system_prompt.txt` | Slim persona mirror; optional custom override when `AI_USE_CUSTOM_PROMPT` is enabled. Not stacked on chat composition. |
| `resources/prompts/command.txt` | Command parse prompt with live action injection. Unchanged. |
| Legacy instructions module (removed) | Rules moved into category files. |
| `ai/prompts/manager.py` inline bodies | Temporary support for `create_task_prompt()` and `create_checkin_prompt()`. |
| `ai/fallback/*` | Deterministic fallback logic; should align with category wording over time. |
| `ai/chat/response_postprocess.py` | Leak cleanup, sign-off stripping, truncation only. |

### 4.2 Category file layout

```text
resources/prompts/product_ai/
- persona.txt
- reply_rules.txt
- data_honesty.txt
- action_boundaries.txt
```

Runtime `available_actions` text is injected during composition from `AIActionCatalog` or envelope structured data.

### 4.3 Prompt composition contract

Add a category-oriented API while preserving current public calls during migration:

```text
PromptManager.compose_product_prompt(flow_name, *, context_view=None, action_catalog=None, result_metadata=None) -> PromptTemplate
```

The composed prompt should include:

- flow name and category list from `ai/prompts/flows.py`
- category text in a stable order
- generated capability text from `AIActionCatalog` for flows that need it
- selected context prompt sections from `AIContextEnvelope`, passed as data rather than loaded by `PromptManager`
- optional action-result metadata for `action_result_response`

Existing `get_prompt("wellness")` and `get_prompt("command")` can delegate to this API temporarily, but new product-AI code should use flow/category composition directly.

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
- Replace ad hoc context assembly in `user/context_manager.py`, `ai/context/builder.py`, and `ai/context/phraser.py` incrementally by reading from the envelope.
- Preserve current public entry points until all callers migrate, but do not add permanent shims.

### Phase 2 - Prompt categories **COMPLETED (2026-07-02)**

- [x] Add `resources/prompts/product_ai/` category files aligned to chat flow jobs.
- [x] Add `PromptManager.compose_product_prompt()` and tests for stable category order.
- [x] Remove duplicate `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` and stop stacking `assistant_system_prompt.txt` on chat composition.
- [x] Replace static capability claims with runtime `available_actions` injection from `AIActionCatalog`.
- [ ] Wire `action_interpretation` and `action_result_response` flows into runtime composition beyond tests.
- [x] Align `ai/fallback/*` copy with composed category contract (partial — paths migrated; wording review remains).

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
- [x] Remove `enhance_conversational_engagement()` so follow-up behavior is prompt-owned (`reply_rules.txt`).

### Phase 7 - Fallback alignment

- Update fallbacks to accept `AIContextEnvelope` or a compact fallback context.
- Keep deterministic fallback categories, but align copy with product capabilities and action availability.
- Add action-aware fallback behavior:
  - If AI planning fails but rule-based parsing is confident, execute through the existing structured command path.
  - If LM Studio is unavailable for chat, answer from deterministic summaries where possible.
  - If action execution fails, return the handler error/result instead of generic support copy.

### Phase 8 - Retire old prompt/context paths **PARTIAL (2026-07-02)**

- [x] Migrated callers to `ai/client/`, `ai/context/`, `ai/prompts/`, `ai/chat/`, `ai/fallback/`; removed legacy flat modules and shim packages.
- [x] Removed empty `ai/conversational_context/` and `ai/fallback_responses/` directories.
- [ ] Retire `ai/context/builder.py` adapter when all callers consume `AIContextEnvelope` directly.
- [ ] Remove duplicated prompt text and obsolete context builders only after callers and tests are migrated.
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

## 9. Implementation Slices

### 9.1 Completed foundation slice

1. [x] Add `AIContextEnvelope` and a context service that reads account, preferences, context, schedules, tasks, check-ins, messages, conversation history, and health summaries.
2. [x] Add tests proving the envelope sees all populated in-app data for a test user.
3. [x] Add an action catalog generated from existing handlers and parser intents.

This slice gave the AI richer data access and capability metadata without adding action execution.

### 9.2 Next slice - prompt-system cleanup

Focus on making the prompting system easier to use, connect, and expand before adding planner/executor behavior.

1. [ ] Add product-AI category files under `resources/prompts/product_ai/`.
2. [ ] Add `PromptManager.compose_product_prompt()` for `chat_response`, using `ai/prompts/flows.py` category ownership.
3. [ ] Move duplicated conversational behavior out of `assistant_system_prompt.txt` and `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` into category-owned text.
4. [ ] Generate product capability text from `AIActionCatalog` for chat prompts, while preserving feature-disabled constraints from `AIContextEnvelope`.
5. [ ] Update `assemble_comprehensive_messages()` to consume the composed chat prompt plus envelope prompt sections.
6. [ ] Add tests that verify category inclusion, no duplicated greeting/direct-answer rules, action-boundary wording, and feature-disabled wording.
7. [ ] Keep existing `get_prompt("wellness")` behavior as a temporary API surface only if current callers still require it; document any bridge if it becomes a true legacy compatibility path.

Do not add AI action planning in this slice. The goal is prompt ownership clarity and lower duplication.

### 9.3 Following slice - action-routing proof

After prompt cleanup is stable:

1. [ ] Add tests proving task actions route through the communication/action-execution layer into `dispatch_structured_command`.
2. [ ] Add narrow conversion from `AIActionRequest` to `ParsedCommand`.
3. [ ] Capture structured execution metadata for final response generation.
4. [ ] Only then add AI action planner/executor behavior.

## 10. Implementation Log

### 2026-07-01 - Canonical context envelope slice

Completed:

- Added `ai/context/service.py` with `AIContextEnvelope`, `AIContextSection`, and `build_ai_context_envelope`.
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
- Superseded by the later ContextBuilder slice: `ai/context/builder.py` now reads from the envelope. `user/context_manager.py` remains a separate context surface to review before final prompt cleanup.
- No legacy compatibility bridge was added in this slice.

### 2026-07-01 - Handler-backed action catalog slice

Completed:

- Added `ai/prompts/action_catalog.py` with `AIActionCatalog`, `AIActionDefinition`, `AIActionField`, and `AIActionRequest`.
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

- Updated `ContextBuilder.build_user_context` in `ai/context/builder.py` to build from `AIContextEnvelope` instead of separately calling `UserContextManager`, `get_recent_responses`, and direct `get_user_data` reads.
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
- Remaining context overlap is primarily in `user/context_manager.py` and `ai/context/phraser.py`; those should be migrated to consume envelope sections or prompt views before prompt-category cleanup begins.

### 2026-07-01 - Prompt-flow categorization and chat assembly cleanup

Course correction:

- The refactor should make product-AI prompt flow ownership clearer, not just add context/action plumbing. This slice explicitly categorizes prompt flows and removes direct domain loading from chat prompt assembly.

Completed:

- Added `ai/prompts/flows.py` with named product-AI prompt flows:
  - `chat_response`
  - `action_interpretation`
  - `action_result_response`
  - `fallback_response`
- Each flow records its category ownership, context source, and prompt owner.
- Updated `ai/context/assembly.py` so `assemble_comprehensive_messages()` uses the `chat_response` flow and builds one `AIContextEnvelope`.
- Updated `build_context_parts()` to phrase from the envelope's structured sections instead of calling `user_context_manager` and domain-loading helpers directly.
- Kept `ai/context/phraser.py` as a wording/helper module for now; it no longer owns top-level chat context loading.
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
- Kept action execution explicitly out of `ai/prompts/action_catalog.py`; the catalog remains metadata-only.
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

### 2026-07-02 - Prompt cleanup slice definition

Completed:

- Added a concrete prompt cleanup problem statement centered on the rule: product AI flows choose categories, categories own prompt text, and runtime services provide data/actions.
- Added a current prompt-source inventory covering `assistant_system_prompt.txt`, `CONVERSATIONAL_CONTEXT_INSTRUCTIONS`, `command.txt`, inline `PromptManager` bodies, fallback responses, and response post-processing.
- Defined the proposed `resources/prompts/product_ai/` category file layout and a `PromptManager.compose_product_prompt()` contract.
- Expanded Phase 2 with specific migration steps for duplicated greeting, direct-answer, context visibility, feature availability, health-personalization, action-boundary, and capability rules.
- Replaced the old first-slice checklist with completed foundation, next prompt-system cleanup, and following action-routing proof slices.

Notes:

- This is documentation/planning only. No prompt files or runtime code were changed in this slice.
- The next implementation should start with `chat_response` composition and tests before changing command/action planning behavior.
