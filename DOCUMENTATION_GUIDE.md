# Documentation Guide

> **File**: `DOCUMENTATION_GUIDE.md`  
> **Audience**: Developers and contributors  
> **Purpose**: Organize, author, and maintain project documentation  
> **Style**: Comprehensive reference with actionable guidance  
> **Pair**:
> [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)  
> This document is paired with
> [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md),
> and any structural changes must keep H2 headings in lockstep across
> both docs.

## 1. Quick Reference

Use this section to choose the right documentation file quickly and
safely.

### 1.1. Core entry points

-   **Project overview and philosophy**  
    See [README.md](README.md) for high-level context, core principles,
    and navigation.

-   **Environment setup and run commands**  
    See the "Quick Start (Recommended)" and "Environment Setup" sections
    in [HOW_TO_RUN.md](HOW_TO_RUN.md).

-   **Configuration (.env and core/config.py)**  
    See [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for the canonical list of config values, what they do, and common failure modes.

-   **User data persistence layout (data/users/{user_id}/...)**  
    See [core/USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) for the canonical on-disk contract (files, subdirectories, and access rules).

-   **Development workflow and safe changes**  
    See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for the
    standard development cycle and safe-change process.  
    For a condensed workflow summary, see
    [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md).

-   **Architecture and data flow**  
    See [ARCHITECTURE.md](ARCHITECTURE.md) for module layout, data
    handling patterns, and UI architecture.  
    For an AI-optimized summary, see
    [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md).

-   **Logging, testing, error handling, and backups**

    -   Logging: [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) and
        [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md)  
    -   Testing: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md),
        [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md),
        and
        [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)  
    -   Error handling:
        [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md) and
        [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md)  
    -   Backups: [BACKUP_GUIDE.md](development_docs/BACKUP_GUIDE.md) and
        [AI_BACKUP_GUIDE.md](ai_development_docs/AI_BACKUP_GUIDE.md)

-   **AI collaboration and rules**

    -   Session constraints and guardrails:
        [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md)  

-   **Change history and priorities**

    -   Detailed change history:
        [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md)  
    -   AI-focused summaries:
        [AI_CHANGELOG.md](ai_development_docs/AI_CHANGELOG.md)  
    -   Plans and roadmaps: [TODO.md](TODO.md),
        [PLANS.md](development_docs/PLANS.md)

### 1.2. When editing documentation

-   If you edit any document that has an AI or human counterpart, follow
    section 4, "Documentation Synchronization Checklist".
-   Use generated reports (for example,
    [LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md))
    to detect stale references and path drift before finalizing changes.

## 2. Documentation Categories

This section defines how documentation is grouped and how each group
should be used.

### 2.1. Human-facing documents

Human-facing documents are the detailed, explanatory sources of truth.
They prioritize context, rationale, examples, and troubleshooting.

Examples:

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

When in doubt, human-facing docs are where you should look for
rationale, context, and full explanations.

### 2.2. AI-facing documents

AI-facing documents are concise references that help AI collaborators
behave safely and efficiently.

AI-facing docs should:

-   Capture rules, constraints, conventions, and boundaries that must be
    enforced.
-   Provide fast routing and "what to open next" guidance.
-   Avoid duplicating long explanations already present in the human
    doc, but include critical rules even if they appear elsewhere.

Key AI-facing docs:

-   [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md):
    Session constraints, must-follow rules, and safety boundaries.
-   [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md):
    Condensed workflow, with links to sections in
    [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).
-   [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md):
    High-level architectural cues and module overviews, with references
    to [ARCHITECTURE.md](ARCHITECTURE.md).
-   [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md):
    Documentation standards (AI view), sync rules, and enforcement
    boundaries.
-   [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md):
    Logging usage patterns, triage workflows, and log locations.
-   [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md):
    Testing patterns, commands, and debugging guidance.
-   [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md):
    Error categories, constraints, and links to
    [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).
-   [AI_LEGACY_REMOVAL_GUIDE.md](ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md):
    Patterns for safely removing legacy code and using automated
    reports.

### 2.3. Generated and analytical documentation

Some documents are generated by tools and must not be hand-edited. They
are reports and references, not primary editing targets.

Examples (non-exhaustive):

-   [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)
-   [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md)
-   [LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md)
-   [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)
-   [TEST_COVERAGE_REPORT.md](development_docs/TEST_COVERAGE_REPORT.md)
-   [AI_FUNCTION_REGISTRY.md](ai_development_docs/AI_FUNCTION_REGISTRY.md)
-   [AI_MODULE_DEPENDENCIES.md](ai_development_docs/AI_MODULE_DEPENDENCIES.md)

For generation details and maintenance rules, see section 6, "Generated
Documentation Standards".

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
> **Pair**: ``    # Only for human/AI doc pairs  
> **Parent**: ``  # Only for subordinate docs
```

Notes:

File must always match the relative path from the project root (for
example, logs/LOGGING_GUIDE.md).

Pair must be present for all docs that participate in a doc pair (for
example, ai_development_docs/AI_LOGGING_GUIDE.md).

The Pair line should be followed by a short sentence stating that
changes must be considered in the context of both docs.

Parent is used when a doc is subordinate to a higher-level doc (for
example, manual guides under a primary testing guide).

It does not imply H2 lockstep like Pair.

It exists to guide routing, standards, and terminology.

For docs that are neither paired nor subordinate, omit both Pair and
Parent.

[EXAMPLE] Paired doc (human-side):

``` markdown
# File Name

> **File**: `logs/LOGGING_GUIDE.md`  
> **Audience**: Developers and maintainers  
> **Purpose**: Explain how logging works and how to use it safely  
> **Style**: Detailed, explanatory  
> **Pair**: `ai_development_docs/AI_LOGGING_GUIDE.md`  
> This document is paired with `ai_development_docs/AI_LOGGING_GUIDE.md` and any changes must be considered in the context of both docs.
```

[EXAMPLE] AI-side paired doc:

``` markdown
# File Name

> **File**: `ai_development_docs/AI_LOGGING_GUIDE.md`  
> **Pair**: `logs/LOGGING_GUIDE.md`  
> **Audience**: AI collaborators and tools  
> **Purpose**: Routing and constraints for logging usage  
> **Style**: Minimal, routing-first  
> For detailed behavior, examples, and rationale, use the matching sections in `logs/LOGGING_GUIDE.md`.  
> Keep this file's H2 headings in lockstep with `logs/LOGGING_GUIDE.md` when making changes.
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

### 3.2. Metadata for .mdc rule files

For .mdc rule files used by tools like Cursor:

-   Prefer YAML frontmatter with a file field, or
-   Use a single comment line if there is no frontmatter.

[EXAMPLE] YAML frontmatter:

``` yaml
---
description: "AI behavior rules for error handling"
file: ".cursor/rules/testing-guidelines.mdc"
---
```

[EXAMPLE] Comment-only:

``` markdown
<!-- file: .cursor/rules/testing-guidelines.mdc -->
```

### 3.3. Structure guidelines for human-facing docs

Human-facing docs (for example, DOCUMENTATION_GUIDE.md,
logs/LOGGING_GUIDE.md, tests/TESTING_GUIDE.md) should:

-   Use numbered H2/H3 headings (see section 3.5).
-   Include detailed explanations, rationale, and examples.
-   Prefer step-by-step checklists where possible.
-   Cross-reference other docs using specific section numbers when
    pointing to specific behavior or rules.

### 3.4. Structure guidelines for AI-facing docs

AI-facing docs in ai_development_docs/ should:

-   Be brief, but include critical rules, constraints, conventions, and
    boundaries.
-   Include routing recommendations and "what to open next" guidance.
-   Prefer linking to AI_* docs first, then to human docs for deep
    detail.
-   Avoid reproducing long explanations already present in human-facing
    docs.

### 3.5. Heading numbering standard

All main documentation files must use numbered H2 and H3 headings:

-   H2 headings: numbered sequentially starting at 1 (for example,
    ## 1. Section Title, ## 2. Next Section).
-   H3 headings: numbered with the parent section number (for example,
    ### 3.1. Subsection, ### 3.2. Another Subsection).
-   Standard format: numbers must include a trailing period and space
    (for example, ## 2. Title not ## 2 Title).

Exceptions:

Changelog files, plan files, and TODO.md are excluded from numbering as
they have their own structure.

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
ai_development_docs/AI_DOCUMENTATION_GUIDE.md

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
    example, `core/service.py`).

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

Use only the filename as the link text, not the path. Keep the full
project-root path in the link target so links remain unambiguous.

[OK]

[LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)

[AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)

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

## 4. Documentation Synchronization Checklist

This section defines how to keep doc pairs and related references
synchronized.

### 4.1. Paired documentation files

Paired human/AI docs must share the same H2 heading set. If you add,
remove, rename, or reorder an H2 in one doc, you must do the same in the
paired doc.

Common pairs include:

-   DOCUMENTATION_GUIDE.md and
    ai_development_docs/AI_DOCUMENTATION_GUIDE.md
-   ARCHITECTURE.md and ai_development_docs/AI_ARCHITECTURE.md
-   logs/LOGGING_GUIDE.md and ai_development_docs/AI_LOGGING_GUIDE.md
-   tests/TESTING_GUIDE.md and ai_development_docs/AI_TESTING_GUIDE.md
-   core/ERROR_HANDLING_GUIDE.md and
    ai_development_docs/AI_ERROR_HANDLING_GUIDE.md
-   development_docs/BACKUP_GUIDE.md and
    ai_development_docs/AI_BACKUP_GUIDE.md

### 4.2. Synchronization workflow (practical)

Open both the human and AI doc.

Make the human doc changes first (the human doc is the detailed source
of truth).

Apply the same H2 heading changes to the AI doc immediately.

Update the AI doc content to reflect:

-   constraints, conventions, and boundaries
-   key patterns and "do / do not" rules
-   routing and "what to open next"

Update cross-references and section numbers as needed.

Run documentation tooling checks (see section 4.5).

### 4.3. Cross-doc consistency checks

Before finalizing doc changes:

-   Verify referenced paths exist (avoid path drift).
-   Verify section numbers referenced in links remain correct.
-   Verify paired docs have identical H2 heading sets.
-   Verify example markers are present around intentional bad examples.
-   Verify headings and numbering follow section 3.5.
-   Validate links to generated reports or other docs resolve correctly.

### 4.4. When docs and code diverge

If docs and code disagree:

-   Call out the mismatch explicitly.
-   Propose whether to adjust docs, code, or both.
-   Do not silently "fix" one side without noting the discrepancy.

### 4.5. Automated tools

``` bash
python development_tools/run_development_tools.py doc-sync
python development_tools/run_development_tools.py legacy
python development_tools/run_development_tools.py version-sync
```

Additional tools such as audit, quick-status, test-coverage, and
validate-work live in development_tools/run_development_tools.py and may
output supporting reports used by documentation.

For detailed tool behavior, see DEVELOPMENT_TOOLS_GUIDE.md.

## 5. Maintenance Guidelines

### 5.1. Updating AI documentation

When updating an AI-facing document:

-   Prefer referencing other AI docs first, then human docs.
-   Keep content brief and operational, but include critical rules and
    boundaries.
-   Remove redundant text when another AI doc already covers the same
    rule.
-   Add explicit references to the relevant section in the paired human
    doc for context.
-   When you add a new section in the AI doc, ensure the same H2 exists
    in the paired human doc.

### 5.2. Updating human documentation

When updating a human-facing document:

-   Provide enough context and examples that a beginner developer can
    follow the guidance.
-   Include motivations, edge cases, and troubleshooting tips where they
    matter.
-   Keep cross-references up to date; prefer linking to specific
    sections instead of entire files when possible.
-   If the doc has an AI counterpart, ensure the AI doc accurately
    summarizes constraints, patterns, and routing.

### 5.3. Adding new documentation

When adding a new documentation file:

-   Decide whether it should be human-facing, AI-facing, or both.
-   If a new pair is needed, register it conceptually under section 4.1
    and ensure both files share the same H2 set.
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

-   development_docs/FUNCTION_REGISTRY_DETAIL.md
-   development_docs/MODULE_DEPENDENCIES_DETAIL.md
-   development_docs/LEGACY_REFERENCE_REPORT.md
-   development_docs/UNUSED_IMPORTS_REPORT.md
-   development_docs/TEST_COVERAGE_REPORT.md
-   development_docs/DIRECTORY_TREE.md
-   ai_development_docs/AI_FUNCTION_REGISTRY.md
-   ai_development_docs/AI_MODULE_DEPENDENCIES.md
-   development_tools/AI_STATUS.md
-   development_tools/AI_PRIORITIES.md
-   development_tools/consolidated_report.txt

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
-   UNUSED_IMPORTS_REPORT.md
-   TEST_COVERAGE_REPORT.md
-   AI_FUNCTION_REGISTRY.md
-   AI_MODULE_DEPENDENCIES.md

### 6.4. Automation commands for generated docs

Use development_tools/run_development_tools.py for documentation-related
automation instead of editing generated files by hand.

Typical commands include:

-   docs
-   doc-sync
-   coverage
-   legacy
-   unused-imports
-   trees
-   status

The definitive list of commands and semantics lives in:

-   DEVELOPMENT_TOOLS_GUIDE.md
-   AI_DEVELOPMENT_TOOLS_GUIDE.md

Command handlers live in development_tools/shared/service/commands.py.
Do not duplicate command semantics here.

## 7. Resources

Useful supporting materials and locations:

-   .cursor/rules/: Rulesets that govern AI behavior and baseline
    constraints.
-   AI_SESSION_STARTER.md: Required reading for AI collaborators before
    performing code changes.
-   CHANGELOG_DETAIL.md and AI_CHANGELOG.md: Detailed and condensed
    histories of changes.
-   AI_DEVELOPMENT_TOOLS_GUIDE.md and DEVELOPMENT_TOOLS_GUIDE.md:
    Documentation on analysis, audit, and sync tools.