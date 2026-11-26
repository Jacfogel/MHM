# AI user context isolation

> **File**: `specs/ai-user-context-isolation.md`
> **Last Updated**: 2026-11-25
> **Implementation**: `ai/client/cache_manager.py`, `ai/context/service.py`, `ai/context/assembly.py`, `ai/context/chatbot_context.py`, `ai/fallback/context.py`, `ai/context/lifecycle.py`, `user/context_manager.py`, `core/web_account_service.py`
> **Automated tests**: `tests/ai/test_cache_manager.py`, `tests/unit/test_conversational_context_envelope.py`, `tests/behavior/test_retained_message_memory.py`, `tests/unit/test_web_account_service.py`, `tests/unit/test_logging_privacy.py`

## Purpose

Keep reused AI context and cached replies scoped to their owning account.

## Requirements

### Requirement: Cache identities remain distinct

- Response-cache identities SHALL preserve user, prompt type, and prompt boundaries. An absent user ID SHALL differ from a literal user ID named anonymous.
- Context-cache reads and writes and session-history reads SHALL use independent copies of nested mutable values.
- Cache and contextual-generation diagnostics SHALL NOT include prompt or personal-context previews.

#### Scenario: Ambiguous delimiters

GIVEN two user and prompt-type combinations that produce the same colon-joined text, WHEN one user caches a reply, THEN the other combination SHALL not retrieve it.

### Requirement: Reused envelopes require ownership

- Prompt assembly, chatbot summaries, and contextual fallbacks SHALL reject an envelope whose metadata lacks the requested user ID or names a different user.
- Rejection SHALL use the existing safe error boundary without exposing the foreign envelope in replies or diagnostic text.

#### Scenario: Foreign envelope

GIVEN an envelope belonging to another account, WHEN it is supplied for a user's reply, THEN no foreign names, tasks, history, or context SHALL appear in the generated message array or fallback context.

### Requirement: Website deletion clears initialized AI state

- Successful website account deletion SHALL clear that user's initialized response/context caches, session overlay, and conversation-history manager state.
- Cleanup SHALL be idempotent, SHALL preserve other users' entries, and SHALL not initialize unused cache/history instances.
- Cleanup failure SHALL return the existing unconfirmed-deletion response instead of reporting success.

## Out of scope

User-controlled memory retention, deletion coordination with work already in flight, administrator deletion paths, shared sessions, and distributed workers are remaining roadmap work. This contract does not certify complete account isolation across every subsystem.

## Manual test checklist

- On isolated accounts, compare private conversation context and cached replies across account switching.
- Delete one isolated website account and verify the other account's conversation still works.

## Related documentation

- [AI guide](../ai/SYSTEM_AI_GUIDE.md)
- [Multi-user roadmap](../development_docs/MULTI_USER_ROADMAP.md)
- [Website guide](../website/WEBSITE_GUIDE.md)
