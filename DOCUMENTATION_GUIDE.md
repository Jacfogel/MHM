# Documentation Guide

> **File**: `DOCUMENTATION_GUIDE.md`
> **Audience**: Developers and AI collaborators
> **Purpose**: Organize, author, and maintain project documentation
> **Style**: Comprehensive reference with actionable guidance

## 1. Quick Reference

Use this section to choose the right documentation file quickly and
safely.

### 1.1. Core entry points

- **Channels, website, and health integration**
  See [COMMUNICATION_GUIDE.md](communication/COMMUNICATION_GUIDE.md) for adapter boundaries, [SMS_GUIDE.md](communication/communication_channels/sms/SMS_GUIDE.md) for the Twilio pilot and simulator, [WEBSITE_GUIDE.md](website/WEBSITE_GUIDE.md) for browser/gateway deployment and billing, and [GOOGLE_HEALTH_GUIDE.md](integrations/google_health/GOOGLE_HEALTH_GUIDE.md) for OAuth, sync, and personalization.

-   **Project overview and philosophy**
    See [README.md](README.md) for high-level context, core principles,
    and navigation.

-   **Environment setup and run commands**
    See section 1. "Quick Start (Recommended)" in
    [HOW_TO_RUN.md](HOW_TO_RUN.md#1-quick-start-recommended), especially section
    1.3. "Step 3: Configure Environment (Optional)" in
    [HOW_TO_RUN.md](HOW_TO_RUN.md#13-step-3-configure-environment-optional).

-   **Configuration (.env and core/config.py)**
    See [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for the canonical list of config values, what they do, and common failure modes.

-   **User data persistence layout (data/users/{user_id}/...)**
    See [core/USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) for the canonical on-disk contract (files, subdirectories, and access rules).

-   **Development workflow and safe changes**
    See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for the
    standard development cycle and safe-change process.


-   **User-visible behavior requirements**
    See [specs/SPECS_GUIDE.md](specs/SPECS_GUIDE.md) and capability files under
    `specs/` (for example
    [specs/discord-welcome-and-onboarding.md](specs/discord-welcome-and-onboarding.md)).

-   **Architecture and data flow**
    See [ARCHITECTURE.md](ARCHITECTURE.md) for module layout, data
    handling patterns, and UI architecture.


-   **Logging, testing, error handling, and backups**

    -   Logging: [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).
    -   Testing: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and the
        [development-tools testing guide](https://github.com/Jacfogel/development-tools/blob/development/tests/development_tools/DEVELOPMENT_TOOLS_TESTING_GUIDE.md).
    -   Error handling: [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).
    -   Backups: [BACKUP_GUIDE.md](development_docs/BACKUP_GUIDE.md).
    -   Legacy removal: [LEGACY_COMPATIBILITY_GUIDE.md](development_docs/LEGACY_COMPATIBILITY_GUIDE.md).

-   **AI collaboration and rules**

    Read [AGENTS.md](AGENTS.md) for project constraints and task navigation.
    Shared topic guides apply to all contributors.

-   **Change history and priorities**

    -   Detailed change history:
        [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md)
    -   Recent change summaries:
        [CHANGELOG_BRIEF.md](development_docs/CHANGELOG_BRIEF.md)
    -   Plans and roadmaps: [TODO.md](TODO.md),
        [PLANS.md](development_docs/PLANS.md)

### 1.2. When editing documentation

-   Update the shared guide that owns the topic and follow section 4,
    "Documentation Synchronization Checklist", for affected references.
-   Use generated reports (for example,
    [LEGACY_REFERENCE_REPORT.md](development_tools/reports/LEGACY_REFERENCE_REPORT.md))
    to detect stale references and path drift before finalizing changes.

## 2. Documentation Categories

This section defines how documentation is grouped and how each group
should be used.

### 2.1. Shared topic guides

Shared topic guides are the detailed, explanatory sources of truth for
humans and AI collaborators.
They prioritize context, rationale, examples, and troubleshooting.

Key documents:

-   [README.md](README.md): High-level introduction, philosophy, and
    navigation.
-   [HOW_TO_RUN.md](HOW_TO_RUN.md): Environment setup, run commands, and
    troubleshooting for starting services and the UI.
-   [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md): Safe development
    cycle, preconditions, standard tasks, and emergency procedures.
-   [ARCHITECTURE.md](ARCHITECTURE.md): Directory layout, module responsibilities, and UI patterns.
-   [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md): Canonical configuration reference for `.env` and `core/config.py`.
-   [core/USER_DATA_MODEL.md](core/USER_DATA_MODEL.md): Canonical on-disk layout for `data/users/{user_id}/...`, persisted artifacts, and access/validation expectations.
-   [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md): Logging design, logger
    hierarchy, log file locations, rotation, and analysis approaches.
-   [TESTING_GUIDE.md](tests/TESTING_GUIDE.md): Testing philosophy,
    types, organization, commands, and manual testing procedures.
-   [tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md](tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md): Automated system AI functionality suite guidance (how to run and interpret).
-   [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md): Error
    handling architecture, patterns, recovery strategies, and error
    logging practices.
-   [BACKUP_GUIDE.md](development_docs/BACKUP_GUIDE.md): Backup,
    rotation, archiving systems, and restore procedures.
-   [PROJECT_VISION.md](PROJECT_VISION.md): Longer-term goals, values,
    and direction of the project.

When in doubt, shared topic guides are where you should look for
rationale, context, and full explanations.

### 2.2. Agent entry documents

Keep [AGENTS.md](AGENTS.md) short and actionable. This entry file also provides task navigation; it does not repeat topic guides. Do not create AI mirrors of shared guides.

### 2.3. Generated and analytical documentation

Some documents are generated by tools and must not be hand-edited. They
are reports and references, not primary editing targets. Navigation belongs in architecture and feature guides; detailed inventories support lookups, and audit reports own actionable findings.

Examples (non-exhaustive):

-   [FUNCTION_REGISTRY_DETAIL.md](development_tools/reports/FUNCTION_REGISTRY_DETAIL.md)
-   [MODULE_DEPENDENCIES_DETAIL.md](development_tools/reports/MODULE_DEPENDENCIES_DETAIL.md)
-   [LEGACY_REFERENCE_REPORT.md](development_tools/reports/LEGACY_REFERENCE_REPORT.md)
-   [TEST_COVERAGE_REPORT.md](development_docs/TEST_COVERAGE_REPORT.md)
-   [DIRECTORY_TREE.md](development_tools/reports/DIRECTORY_TREE.md)
-   [Priorities Brief](development_tools/PRIORITIES_BRIEF.md)
-   [Status Brief](development_tools/STATUS_BRIEF.md)
-   [Consolidated Report](development_tools/CONSOLIDATED_REPORT.md)

For generation details and maintenance rules, see section 6, "Generated
Documentation Standards".

### 2.4. Behavior specifications

Behavior specs are short, testable descriptions of **what the product must do**
for a focused capability. They are used by both human developers and AI
collaborators (no separate AI/human pair per spec file).

-   Index and rules: [specs/SPECS_GUIDE.md](specs/SPECS_GUIDE.md)
-   Topic files: `specs/<topic>.md` (requirements and GIVEN/WHEN/THEN scenarios)
-   Architecture and patterns stay in module guides (for example
    [COMMUNICATION_GUIDE.md](communication/COMMUNICATION_GUIDE.md)); specs state
    observable behavior only.

When to write or update a spec, file naming, templates, and workflow are defined in
[specs/SPECS_GUIDE.md](specs/SPECS_GUIDE.md). Spec topic files are exempt from H2
numbering (see section 3.5).

## 3. Standards and Templates

This section defines how documentation files should be structured,
labeled, cross-referenced, and maintained.

### 3.1. Metadata for `.md` documentation files

Every documentation file (`.md`) must start with a metadata block so it
can be located and referenced unambiguously.

Required format:

``` markdown
# File Name

> **File**: `relative/path/from/project/root`
> **Audience**: [Target audience]
> **Purpose**: [What this document is for]
> **Style**: [Tone and depth]
> **Parent**: ``  # Only for subordinate docs
```

Notes:

File must always match the relative path from the project root (for
example, logs/LOGGING_GUIDE.md).

Use `Parent` when a document is subordinate to a higher-level guide, such
as a manual testing guide. This establishes routing, standards, and
terminology; it does not require matching headings. Omit Parent for
standalone documents. Do not add Pair metadata.

[EXAMPLE] Shared topic guide:

``` markdown
# Logging Guide

> **File**: `logs/LOGGING_GUIDE.md`
> **Audience**: Developers and AI collaborators
> **Purpose**: Explain how logging works and how to use it safely
> **Style**: Detailed, explanatory
```

[EXAMPLE] Subordinate (parented) doc:

``` markdown
# File Name

> **File**: `tests/MANUAL_TESTING_GUIDE.md`
> **Audience**: Developers and AI assistants performing manual testing
> **Purpose**: Canonical manual testing flows and checklists
> **Style**: Checklist-first, concise but detailed
> **Parent**: `tests/TESTING_GUIDE.md`
> This document is subordinate to `tests/TESTING_GUIDE.md` and must remain consistent with its standards and terminology.
```

### 3.2. Contributor instruction files

Project-wide instructions live in [AGENTS.md](AGENTS.md). Keep them
short, actionable, and linked to the shared guides that own detailed
procedures. Cursor rules, commands, and plans are retired.

Existing task-specific skills remain under `.agents/skills/`. Their
metadata identifies the skill and when to use it; their File metadata
must identify the current skill path rather than a deleted Cursor command.

### 3.3. Structure guidelines for shared guides

Shared topic guides (for example, DOCUMENTATION_GUIDE.md,
logs/LOGGING_GUIDE.md, tests/TESTING_GUIDE.md) should:

-   Use numbered H2/H3 headings (see section 3.5).
-   Include detailed explanations, rationale, and examples.
-   Prefer step-by-step checklists where possible.
-   Cross-reference other docs using specific section numbers when
    pointing to specific behavior or rules.

### 3.4. Structure guidelines for entry documents

Keep entry documents brief, with essential constraints and links directly to shared guides. Do not duplicate detailed procedures.

### 3.5. Heading numbering standard

All main documentation files must use numbered H2 and H3 headings:

-   H2 headings: numbered sequentially starting at 1 (for example,
    ## 1. Section Title, ## 2. Next Section).
-   H3 headings: numbered with the parent section number (for example,
    ### 3.1. Subsection, ### 3.2. Another Subsection).
-   Standard format: numbers must include a trailing period and space
    (for example, ## 2. Title not ## 2 Title).

Exceptions:

Changelog files, plan files, TODO.md, and behavior spec topic files under
`specs/<topic>.md` are excluded from numbering as they have their own
structure (see [specs/SPECS_GUIDE.md](specs/SPECS_GUIDE.md#42-heading-and-numbering-rules), section 4.2. "Heading and numbering rules").

Q&A headings and step headings should be converted to bold text instead
of additional numbered headings.

### 3.6. Example marking standards

When including examples (especially examples showing what NOT to do),
mark them clearly so the path drift checker can skip them.

Required markers for examples:

Example sections with markers (preferred):

Use [OK], [AVOID], [GOOD], [BAD], [EXAMPLE] at the start of
the example section.

Place the marker on its own line or at the start of the section heading.

[AVOID] Avoid (ambiguous short names):

`bot.py` without context (could be Discord or email bot)

Example headings:

Use headings like "Examples:", "Example Usage:", "Example Code:" to mark
example sections.

Code blocks:

Examples in code blocks are automatically excluded from path drift
checking.

Why this matters:

Examples often contain intentional "bad" examples (short paths,
non-existent files) to demonstrate what NOT to do.

Without proper marking, these examples will be flagged as path drift
issues.

Note:

The path drift checker looks for these markers within 5 lines of a path
reference, so place markers close to the examples they mark.

### 3.7. File path reference standards

Primary rule: use full paths from project root for all file references.
This standard optimizes for AI collaborators who need unambiguous,
verifiable paths to navigate the codebase.

Format guidelines:

Full paths from project root (preferred):

Always use the complete path from the project root.

Examples: development_tools/config.py, core/config.py, core/service.py,
DOCUMENTATION_GUIDE.md

Why: unambiguous, verifiable, works from any context, enables reliable
file search.

Short names (acceptable only in very clear contexts):

May be used only when the directory is 100% obvious from document
context.

Caution: the path drift checker may flag these; ensure context makes the
directory unambiguous.

Relative paths (use sparingly):

May be used for files in the same directory or parent directory.

Caution: can break if docs are reorganized; prefer full paths when in
doubt.

Best practices for AI collaborators:

-   Always prefer full paths when referencing files outside the current
    directory.
-   Verify paths exist using file search tools before referencing.
-   Use consistent formatting: backticks for file references (for
    [EXAMPLE] example, `core/service.py`).

Path drift checker behavior:

The path drift checker (development_tools/docs/analyze_path_drift.py)
validates that referenced files exist.

It accepts full paths from project root.

It accepts relative paths (for example, ../README.md) when the file
exists relative to the source document.

It uses enhanced filtering to reduce false positives.

[OK] Good (full paths):
- `development_tools/shared/service/core.py`
- `core/config.py`
- `tests/TESTING_GUIDE.md`

[AVOID] Avoid (ambiguous short names):

`operations.py` (could be development_tools/shared/service/commands.py
or another operations.py)

`config.py` (could be core/config.py or development_tools/config.py)

`bot.py` without context (could be Discord or email bot)

### 3.8. Markdown link standard (for .md references)

Use only the filename as the link text, not the path. Use a target that
resolves from the source document so links are clickable in repository
viewers. In root documents this is the project-root relative path; in
nested documents use the appropriate relative path, such as `../README.md`.

[OK]

[LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)

[TESTING_GUIDE.md](tests/TESTING_GUIDE.md)

Rules:

-   Only convert .md references when the target file exists in the repo.
-   Do not convert inside:
    -   **File**: metadata lines

    -   code fences or inline code examples

    -   self-references to the current document unless linking to a
        specific section

    -   marked example contexts ([OK], [AVOID], etc.)

Metadata section link deduplication:

In metadata blocks, link each unique path once.

Subsequent references to the same path in metadata remain as backticks
(not links).

In body content, multiple links to the same file are allowed.

### 3.9. Dating convention for plan and TODO items

Plan files ([PLANS.md](development_docs/PLANS.md), [TODO.md](TODO.md),
and child plans such as [TEST_PLAN.md](development_docs/TEST_PLAN.md))
must date new items and status changes so you can track when work was
added or changed. This avoids stale "when did we last touch this?"
confusion and supports systematic plan consolidation.

**Format**: Use `YYYY-MM-DD` (ISO 8601) for consistency and sortability.

**New items**:

-   Plan entries: Add `**Date**: YYYY-MM-DD` or inline (e.g., "Added
    2026-02-28") when adding a new plan, phase, or checklist item.
-   TODO tasks: Add `- *Created*: YYYY-MM-DD` when adding a task.

**Progressed items**:

-   Status changes: When changing status (e.g., PLANNED -> IN PROGRESS),
    add the date: `**Status**: IN PROGRESS (since YYYY-MM-DD)`.
-   Checkbox completions: When checking off an item, append the date:
    `- [x] Item (YYYY-MM-DD)`.
-   Plan-level "Last Updated": Each plan file header should include
    `**Last Updated**: YYYY-MM-DD` and be updated when any substantive
    change is made.

**Placement**: Put dates near the item title or status line so they are
visible without expanding collapsed sections.

## 4. Documentation Synchronization Checklist

This section defines how to keep shared documentation and related
references synchronized with the implementation.

### 4.1. Shared documentation ownership

There are no paired documentation files. Each topic has one shared guide. The detailed changelog and short recent summary have independent structures; headings do not need to match.

The host configuration explicitly sets `constants.paired_docs` to an empty object. Maintain scan coverage through `fix_version_sync.docs`, `fix_version_sync.ai_docs`, and `constants.default_docs_extra` in the tracked host template and local override.

### 4.2. Synchronization workflow

Update the owning guide or spec, then fix affected navigation, links, configuration catalogs, and skill references. Run documentation checks. Do not create a second document solely to mirror the first.

### 4.3. Cross-doc consistency checks

Before finalizing doc changes:

-   Verify referenced paths exist (avoid path drift).
-   Verify section numbers referenced in links remain correct.
-   Verify example markers are present around intentional bad examples.
-   Verify headings and numbering follow section 3.5.
-   Validate links to generated reports or other docs resolve correctly.

### 4.4. When docs and code diverge

If docs and code disagree:

-   Call out the mismatch explicitly.
-   Propose whether to adjust docs, code, or both.
-   Do not silently "fix" one side without noting the discrepancy.

### 4.5. Automated tools


For an optional read-only section-link inventory, run:

```powershell
python development_tools/docs/analyze_documentation_sync.py --json --check-section-links
python development_tools/docs/analyze_documentation_sync.py --json --check-section-links --section-path HOW_TO_RUN.md --section-path DEVELOPMENT_WORKFLOW.md
```

The first command uses configured documentation paths; repeat `--section-path`
for a curated scope. JSON records source path/line, destination, actual heading,
and anchor status. Missing anchors are definite findings; unanchored numbered
citations are conservative hints requiring manual review. The heuristic checks
same-line inline links and ATX headings; it does not prove that every behavioral
reference is precise or interpret multiline prose. Historical/generated files,
metadata, fenced examples, and bare navigation links are skipped. Advisory counts
are advisory rather than mandatory failures, and the check never rewrites files.


``` bash
python development_tools/run_development_tools.py doc-sync
python development_tools/run_development_tools.py legacy
python development_tools/run_development_tools.py version-sync
```

Additional tools such as audit, quick-status, test-coverage, and
validate-work live in development_tools/run_development_tools.py and may
output supporting reports used by documentation.

For detailed tool behavior, see the [Development Tools README](development_tools/README.md).

## 5. Maintenance Guidelines

### 5.1. Updating agent entry documents

Keep essential constraints and navigation current. Link directly to the authoritative guide and avoid accumulating implementation history.

### 5.2. Updating shared documentation

When updating a shared topic guide:

-   Provide enough context and examples that a beginner developer can
    follow the guidance.
-   Include motivations, edge cases, and troubleshooting tips where they
    matter.
-   Keep cross-references up to date; prefer linking to specific
    sections instead of entire files when possible.
-   Preserve important rules, examples, rationale, and troubleshooting
    details. Remove material only when it is obsolete or superseded by
    an identified authoritative source.

### 5.3. Adding new documentation

When adding a new documentation file:

-   Check whether an existing shared guide or spec already owns the topic.
-   Maintain one shared source for the topic; do not create an AI mirror.
-   Index new files and register them in the host documentation scan catalog
    described in section 4.1.
-   Follow the file address requirement and standard structure for the
    chosen audience.
-   If the document is generated, follow section 6 instead of these
    general rules.

### 5.4. Generated documentation maintenance

Never manually edit generated files listed in section 6.

To update generated content, change the generating tool or its
configuration and regenerate.

If a generated file gains manually curated sections, document the rules
clearly in this guide and in the generating tool's README.

## 6. Generated Documentation Standards

### 6.1. Identification requirements

#### 6.1.1. Markdown files (.md)

All generated Markdown files must use this standardized metadata format:

``` markdown
# Document Title

> **File**: `path/to/file.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: YYYY-MM-DD HH:MM:SS
> **Source**: `python development_tools/path/to/generator.py` - Tool Description
> **Audience**: [Target audience]
> **Purpose**: [What this document is for]
> **Status**: **ACTIVE** - [Brief status note]
```

Required fields:

-   File
-   Generated
-   Last Generated
-   Source

Recommended fields:

-   Audience
-   Purpose
-   Status

Examples of generated Markdown files include:

-   development_tools/reports/FUNCTION_REGISTRY_DETAIL.md
-   development_tools/reports/MODULE_DEPENDENCIES_DETAIL.md
-   development_tools/reports/LEGACY_REFERENCE_REPORT.md
-   development_docs/TEST_COVERAGE_REPORT.md
-   development_tools/reports/DIRECTORY_TREE.md
-   development_tools/STATUS_BRIEF.md
-   development_tools/PRIORITIES_BRIEF.md
-   development_tools/CONSOLIDATED_REPORT.md

#### 6.1.2. JSON files (.json)

All generated JSON files (generated by the development tools suite) must
include standardized metadata fields at the root level:

``` json
{
  "generated_by": "Tool Name - Tool Description",
  "last_generated": "YYYY-MM-DD HH:MM:SS",
  "source": "python development_tools/path/to/tool.py [command]",
  "note": "This file is auto-generated. Do not edit manually.",
  "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff"
}
```

### 6.2. Maintenance rules

-   Do not hand-edit generated outputs except where explicitly allowed
    and documented.
-   To change the content of a generated file, update the script in
    development_tools/ or related tooling and regenerate.
-   If manual annotations are allowed (for example, in a hybrid report),
    clearly mark which sections are tool-owned and which are
    human-owned.

### 6.3. Known generated files

Common generated files include:

-   FUNCTION_REGISTRY_DETAIL.md
-   MODULE_DEPENDENCIES_DETAIL.md
-   LEGACY_REFERENCE_REPORT.md
-   TEST_COVERAGE_REPORT.md

### 6.4. Automation commands for generated docs

Use development_tools/run_development_tools.py for documentation-related
automation instead of editing generated files by hand.

Typical commands include:

-   docs
-   doc-sync
-   coverage
-   legacy
-   trees
-   status

The definitive list of commands and semantics lives in:

-   [Development Tools README](development_tools/README.md)

Command handlers live in development_tools/shared/service/commands.py.
Do not duplicate command semantics here.

## 7. Resources

Useful supporting materials and locations:

-   [AGENTS.md](AGENTS.md): Project constraints and navigation for AI collaborators.
-   [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) and
    [CHANGELOG_BRIEF.md](development_docs/CHANGELOG_BRIEF.md): Detailed and condensed histories.
-   [LEGACY_COMPATIBILITY_GUIDE.md](development_docs/LEGACY_COMPATIBILITY_GUIDE.md): Safe migration and removal procedures.
-   [README.md](development_tools/README.md): Analysis, audit, and documentation tooling.
