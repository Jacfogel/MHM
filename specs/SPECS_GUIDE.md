# Behavior Specifications Guide

> **File**: `specs/SPECS_GUIDE.md`  
> **Audience**: Human developers and AI collaborators  
> **Purpose**: Define what behavior specs are, when to write them, and how they relate to other project documentation  
> **Style**: Practical reference with templates and examples  
> **Last Updated**: 2026-05-16

Behavior specs describe **what the product must do** for a focused capability (usually user-visible). They do not replace architecture guides, development workflow docs, or changelogs.

For communication architecture and adapter boundaries, see [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md). For documentation standards and pairing rules, see [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md).

---

## 1. How Specs Fit the Documentation Stack

| Question | Open this |
|----------|-----------|
| What must happen when a user does X? | `specs/<topic>.md` |
| Where does code live and what patterns apply? | [ARCHITECTURE.md](../ARCHITECTURE.md), [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), channel guides |
| How do I change code safely (venv, tests, audits)? | [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md), `ai_development_docs/AI_*` guides |
| What work is planned or in progress? | [PLANS.md](../development_docs/PLANS.md), [TODO.md](../TODO.md) |
| What shipped in a session? | [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md), [AI_CHANGELOG.md](../ai_development_docs/AI_CHANGELOG.md) |
| How do I test the project overall? | [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md), [TEST_PLAN.md](../development_docs/TEST_PLAN.md) |

Specs are **shared by humans and AI** (no AI/human paired spec files). One spec file per capability is enough.

---

## 2. When to Add or Update a Spec

Add or update a spec when:

- You are changing **user-visible behavior** (especially under `communication/`).
- The behavior is easy to get wrong, regress, or forget across sessions.
- Manual Discord (or channel) validation is part of the definition of done.

Skip specs for:

- Refactors with **no** behavior change.
- Log-only, tooling-only, or internal cleanup work.
- Duplicating content that already lives in a guide (copy patterns, not prose).

When behavior changes: update the spec **before or with** the code, add or adjust tests when practical, and record the ship in the session changelog.

---

## 3. File Layout and Naming

[EXAMPLE]

```text
specs/
  SPECS_GUIDE.md
  discord-welcome-and-onboarding.md
  <short-topic>.md
```

Naming:

- Use lowercase kebab-case: `checkin-scheduled-send.md`, `conversation-cancel-back.md`.
- Prefer one capability per file; split when a file becomes hard to scan.

Reference specs from [PLANS.md](../development_docs/PLANS.md) or [TODO.md](../TODO.md) with a single line, for example: `Spec: specs/discord-welcome-and-onboarding.md`.

---

## 4. Spec File Template

Each spec must begin with a metadata block. Use full paths from the project root in **Implementation** and **Related** lines (per [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) section 3.7).

[EXAMPLE] Topic spec body sections (unnumbered headings): **Purpose**, **Requirements** (with `### Requirement:` and `#### Scenario:` subheadings), **Out of scope**, **Manual test checklist**, **Related documentation**. See [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md) for a full example.

### 4.1. Requirement and scenario wording

- **SHALL** / **MUST** - required behavior; change the spec first if you intend to break it.
- **GIVEN / WHEN / THEN** - one testable situation; add **AND** lines when needed.
- Describe **observable outcomes** (messages sent, flags set, errors shown), not internal implementation details unless the detail is part of the contract.

### 4.2. Heading and numbering rules

Spec topic files (`specs/<topic>.md`) are **exempt** from H2/H3 numbering required in most human guides (same class as [PLANS.md](../development_docs/PLANS.md) and [TODO.md](../TODO.md)). Use clear `##` / `###` titles instead.

This guide (`SPECS_GUIDE.md`) uses numbered sections so it can be referenced from [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) like other top-level guides.

### 4.3. Metadata dates

Update **Last Updated** on the spec when requirements or scenarios change (same `YYYY-MM-DD` convention as plan items in [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) section 3.9).

---

## 5. Workflow for AI Collaborators

Before editing files listed in a spec's **Implementation** block:

1. Read the spec and treat **Requirements** as the behavior contract.
2. Read architecture and channel guides for structure and safety ([COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md), relevant `AI_*` guides).
3. Implement or adjust code and tests.
4. Update the spec if behavior intentionally changed.
5. Add one changelog entry for the session ([CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) and [AI_CHANGELOG.md](../ai_development_docs/AI_CHANGELOG.md)).

Do not copy long guide sections into specs; link to them under **Related documentation**.

---

## 6. Example Specs

| Spec | Covers |
|------|--------|
| [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md) | Discord welcome DM, welcome tracking, create/link account onboarding |

Add new rows here when you add specs worth listing.

---

## 7. Tooling and config registration

Behavior spec files are registered in [`development_tools/config/development_tools_config.json`](../development_tools/config/development_tools_config.json):

- `fix_version_sync.docs` - includes each `specs/<topic>.md` plus [SPECS_GUIDE.md](SPECS_GUIDE.md) (feeds `DEFAULT_DOCS` for doc-sync, path-drift, heading, and ASCII tools).
- `constants.fix_version_sync_directories` - `specs/` root for version-sync directory scans.
- `path_drift.ignored_path_patterns` - heading fragments that are not file paths (for example "Behavior specifications", "Manual test checklist").

When you add a new spec file, append its path to `fix_version_sync.docs` and document it in section 6 of this guide. See [LIST_OF_LISTS.md](../development_docs/LIST_OF_LISTS.md) section 4.

---

## 8. Related Documentation

- [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) - section 2.4, behavior specifications category
- [AI_DOCUMENTATION_GUIDE.md](../ai_development_docs/AI_DOCUMENTATION_GUIDE.md) - AI routing to specs
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture
- [communication/communication_channels/discord/DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter details
