# System AI Overhaul Plan

> **File**: `ai/SYSTEM_AI_OVERHAUL_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Define and separate the current AI-service interaction types in MHM without overbuilding new architecture  
> **Style**: Practical, implementation-aware, boundary-focused  
> **Status**: ACTIVE (Phases 1–4 implemented 2026-05-18; Phase 5 planned)  
> **Parent**: [PROJECT_VISION.md](../PROJECT_VISION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md)

---

## 1. Purpose

This document defines the intended separation between the main ways the MHM system currently interacts with AI.

The goal is not to design a large new AI platform.

The goal is to make the existing AI behavior easier to understand, test, refactor, and extend by separating the current AI-service interaction types:

1. Conversational response generation
2. Command interpretation
3. Fallback response generation
4. Future/secondary AI uses

The current system has useful pieces already, but too many responsibilities are mixed together inside `ai/chatbot.py`, prompt text, command parsing, fallback logic, and context assembly.

This plan should guide a cleanup that keeps the current system practical while leaving room for future expansion.

---

## 2. Main Goal

The main goal is clear separation of AI-service interaction types.

The overhaul should answer:

- Why is the system calling AI in this moment?
- What kind of output is expected?
- Is the output user-visible?
- Is the output structured or conversational?
- Can this output trigger a system action?
- What validates the output before anything happens?
- What happens when AI is unavailable?

The system should not treat every AI call as a generic "chatbot response."

---

## 3. Current Problem

The current AI layer mixes several different responsibilities.

In practice, `ai/chatbot.py` currently handles or influences:

- conversational replies
- command mode detection
- command parsing prompts
- clarification-style responses
- contextual prompt building
- fallback responses
- response cleanup
- response caching
- AI availability checks
- LM Studio API calls
- personalized message generation
- contextual response generation

That makes the system harder to reason about because the same path may be used for different kinds of AI work.

The most important cleanup is not adding new complexity. It is separating the current purposes.

---

## 4. Core Principle

AI output is not system authority.

The deterministic system remains responsible for:

- command execution
- data writes
- task creation/update/delete
- notebook creation/update/delete
- schedules
- reminders
- validation
- permissions
- flow state
- fallback behavior

AI may help with:

- wording
- conversation
- intent interpretation
- extracting candidate fields
- asking a clarification question
- summarizing existing data

AI should not directly mutate persistent state.

---

## 5. Primary AI-Service Interaction Types

This section defines the main categories that should be separated first.

---

## 5.1 Conversational Response Generation

### Purpose

Generate a user-visible natural-language response for normal conversation, emotional support, reflection, encouragement, or general assistance.

### Current examples

- User says they feel overwhelmed.
- User asks how they have been doing.
- User asks for encouragement.
- User asks a general wellness/support question.

### Expected output

Natural language response intended to be sent to the user.

### Output shape

Plain text.

### May use context?

Yes, but context should be targeted and relevant.

Examples:

- preferred name
- recent check-in summary if directly relevant
- recent conversation context if useful
- enabled feature flags so AI does not suggest disabled features

### Must not do

Conversational response generation must not:

- create tasks
- create notes
- update schedules
- delete anything
- claim an action was completed unless the deterministic system completed it
- invent check-in data, task data, or stored memories

### Current implementation notes

This mostly maps to:

- `generate_response(..., mode="chat")`
- `generate_quick_response()`
- `generate_contextual_response()`
- `_create_comprehensive_context_prompt()`
- `_get_contextual_fallback()` when AI is unavailable

The refactor should make conversational generation a clearly named path.

---

## 5.2 Command Interpretation

Command interpretation includes three closely related subtypes that currently overlap:

1. Intent classification
2. Structured extraction
3. Clarification generation

These can be treated as one broad interaction type for now, but the internal responsibilities should be named clearly.

---

### 5.2.1 Intent Classification

#### Purpose

Determine whether the user's message appears to be asking for a system action.

Examples:

- create a task
- list tasks
- start a check-in
- create a note
- show schedule
- show analytics

#### Expected output

A candidate intent or "unknown / not a command."

#### Output shape

Structured data, not conversational prose.

Example conceptual output:

```text
intent: create_task
confidence: medium
needs_clarification: true
```

This does not need to be the final implementation format. The important rule is that classification output is not a final user-facing chatbot reply.

---

### 5.2.2 Structured Extraction

#### Purpose

Extract candidate fields from natural language after a likely command/action has been detected.

Examples:

From:

```text
remind me to call the dentist tomorrow afternoon
```

Extract candidate fields such as:

```text
action: create_task
title: call the dentist
due_date: tomorrow
time_hint: afternoon
```

#### Expected output

Candidate structured fields.

#### Output shape

Structured data.

#### Must not do

Structured extraction must not directly execute the action.

The deterministic command handler must validate the extracted fields before execution.

---

### 5.2.3 Clarification Generation

#### Purpose

Ask a follow-up question when classification or extraction finds that key information is missing or ambiguous.

Examples:

- "What should I call the task?"
- "When should I remind you?"
- "Did you want this as a task or just a note?"

#### Expected output

A short user-visible clarification question.

#### Output shape

Plain text, but constrained.

#### Important boundary

Clarification generation belongs to the command interpretation path, not the general conversational path.

The deterministic system should decide that clarification is needed. AI may help phrase the question.

---

## 5.3 Fallback Response Generation

### Purpose

Provide safe, useful behavior when AI cannot complete the intended interaction.

Fallbacks should be separate from normal conversational generation.

### Fallback triggers

- LM Studio unavailable
- model not loaded
- timeout
- AI output invalid
- structured extraction failed
- context retrieval failed
- command interpretation uncertain

### Expected output

Depends on the original interaction type.

Examples:

| Original interaction | Fallback behavior |
|---|---|
| conversational response | simple supportive template |
| command interpretation | deterministic parser or clarification |
| task creation | ask for missing required fields |
| analytics question | deterministic summary if possible |
| personalized message | preset/semi-random message |

### Must not do

Fallback logic must not pretend AI succeeded.

It should not say:

- "I created that task" unless the task was actually created
- "Based on your recent data" unless data was actually retrieved
- "I noticed a pattern" unless the pattern was deterministically available

### Current implementation notes

Fallback behavior currently appears inside:

- `_get_contextual_fallback()`
- `_get_fallback_personalized_message()`
- `_fallback_response_for_unavailable_lm()`
- lock-busy fallback paths
- failed API response paths

The refactor should make fallback behavior explicit by interaction type.

---

## 6. Secondary / Future AI-Service Interaction Types

The following interaction types may matter later, but they should not become major architecture work right now.

The current goal is only to leave clear space for them.

---

## 6.1 Context Summarization

Current status: basic / partially embedded.

The system may eventually use AI to summarize context before generating a response.

For now:

- do not build a complex new summarization pipeline
- keep context summaries simple and deterministic where possible
- avoid dumping all user data into every prompt
- leave room for future summarization improvements

---

## 6.2 Reflective Insight Generation

Current status: basic / partially supported by analytics and contextual responses.

The system may eventually use AI to phrase insights from deterministic analytics.

For now:

- deterministic analytics should calculate facts
- AI may phrase those facts supportively
- AI must not invent trends or conclusions

---

## 6.3 Message Personalization

Current status: basic / partially implemented.

The system may use AI to personalize automated messages.

For now:

- keep preset and semi-random messages valid without AI
- AI personalization should be optional
- AI output should be bounded by existing message categories and safety rules

---

## 6.4 Safety Evaluation

Current status: mostly deterministic and prompt-based.

The system may eventually use AI as an additional safety check.

For now:

- do not create a complex AI safety evaluator
- keep destructive action confirmation deterministic
- keep medical/mental-health boundaries in deterministic rules and prompts
- AI may support wording but should not own safety enforcement

---

## 7. Simplified Target Separation

The near-term target is this separation:

| AI-service interaction type | User-visible? | Expected output | Can execute actions? |
|---|---:|---|---:|
| Conversational response generation | Yes | Natural language | No |
| Command interpretation | No / sometimes | Structured candidate intent/entities | No |
| Clarification generation | Yes | Short question | No |
| Fallback response generation | Yes | Template or simple response | No |
| Future summarization/personalization/insight support | Maybe | Summary or wording | No |

Only deterministic handlers execute actions.

---

## 8. Practical Refactor Direction

This plan does not require a major new framework.

The practical refactor direction is:

1. Name the current AI call types clearly.
2. Separate conversational generation from command interpretation.
3. Treat classification/extraction/clarification as one command-interpretation family for now.
4. Separate fallback responses from normal AI responses.
5. Keep secondary AI uses simple and optional.
6. Add tests around boundaries.
7. **Phase 5 (planned):** Collapse thin facade delegates on `AIChatBotSingleton` once Phases 1–4 are stable (see Section 8.1).

---

## 8.1 Phase 5 — Collapse facade delegates (planned)

Phases 1–4 moved implementation into dedicated modules but left **one-line private delegates** on `AIChatBotSingleton` (for example `_get_contextual_fallback` → `get_fallback_responses().contextual()`). That is **transitional refactor wiring**, not `# LEGACY COMPATIBILITY` bridge code (see [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)). Phase 5 completes the refactor by removing those wrappers.

### What stays after Phase 5

- **Public API:** `get_ai_chatbot()`, `generate_response()`, `generate_contextual_response()`, `generate_quick_response()`, `is_ai_available()`, and related entry points used by `communication/`.
- **Orchestration in `chatbot.py`:** LM Studio calls, locks, cache, mode routing, and **direct** calls into `fallback_responses`, `command_interpreter`, `response_generator`, `prompt_manager`, `lm_studio_manager`.

### What Phase 5 removes

- Thin private methods that only forward to another module, for example:
  - `_get_contextual_fallback`, `_get_fallback_personalized_message`, `_personalize_fallback_with_profile_name`
  - `_detect_mode`, `_has_command_keyword`, `_needs_command_clarification`, `_create_command_parsing_prompt`, `_extract_command_from_response`, …
  - `_create_comprehensive_context_prompt`, `_enhance_conversational_engagement`

Replace each call site inside `chatbot.py` with the corresponding `get_*()` module call. Do **not** remove `get_ai_chatbot()` or the public generate/status methods.

### Steps (search-and-close)

1. **Inline in `chatbot.py`:** Call `get_fallback_responses()`, `get_command_interpreter()`, `get_response_generator()` directly from `generate_response`, `generate_contextual_response`, and helpers.
2. **Update tests:** Point unit/behavior tests at the canonical modules (for example `get_command_interpreter().detect_mode`) instead of `bot._detect_mode`, where the test target is module behavior rather than chatbot wiring.
3. **Delete delegate methods** from `AIChatBotSingleton` after references are gone.
4. **Verify:** Focused AI pytest, `audit`, duplicate-function scan (retain `not_duplicate` on any intentional thin wrappers if a few remain), doc/registry refresh.
5. **Do not** add `# LEGACY COMPATIBILITY` markers for this step unless a delegate intentionally routes to a deprecated path (it should not).

### Exit criteria

- No one-line `_…` delegates on `AIChatBotSingleton` that only forward to `ai/fallback_responses.py`, `ai/command_interpreter.py`, or `ai/response_generator.py`.
- `communication/` still imports only `get_ai_chatbot()` (no requirement to import submodules from channels).
- Tests and docs describe module ownership clearly; `SYSTEM_AI_GUIDE.md` updated to reflect post–Phase 5 layout.

### Related follow-ups (not Phase 5)

- Deeper deduplication of `ContextBuilder` vs `response_generator.create_comprehensive_context_prompt`.
- AI Chatbot Actionability Sprint and NLP items in [TODO.md](../TODO.md).

---

## 9. Suggested Code-Level Direction

This is not a required final module design, but it describes the kind of separation desired.

Potential future split:

```text
ai/
  chatbot.py                   # public facade / compatibility layer
  response_generator.py        # conversational responses
  command_interpreter.py       # classification + extraction + clarification
  fallback_responses.py        # fallback templates and routing
  context_builder.py           # existing context assembly, simplified over time
  prompt_manager.py            # prompt loading/templates
  lm_studio_manager.py         # LM Studio availability/API readiness
```

This does not need to happen all at once.

A first pass can keep `ai/chatbot.py` as the public facade and move logic gradually. After Phase 5, `chatbot.py` remains the orchestration facade but without redundant private forwarders.

---

## 10. Testing Focus

Testing should focus on boundaries rather than perfect AI wording.

Priority tests:

- conversational prompts do not produce command execution
- command interpretation returns structured candidates, not final prose
- extracted command data is validated before execution
- clarification is used when required fields are missing
- fallback does not claim success
- AI unavailable does not break deterministic commands
- generated responses do not fabricate user data

---

## 11. Non-Goals

This overhaul is not trying to:

- build an autonomous agent
- build a complex AI orchestration framework
- add vector search
- add embeddings
- create a full AI safety subsystem
- make every system operation AI-assisted
- replace command handlers
- replace deterministic validation

---

## 12. Success Criteria

This spec succeeds if the next refactor makes it easy to tell:

- this AI call is for conversation
- this AI call is for command interpretation
- this AI call is for clarification
- this AI call is fallback behavior
- this output is safe to show to the user
- this output is only a candidate and must be validated
- this path can still work when AI is unavailable

The result should be simpler than the current system, not more complex.
