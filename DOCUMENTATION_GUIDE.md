# Documentation Guide

> **File**: `DOCUMENTATION_GUIDE.md`  
> **Audience**: Developers and contributors  
> **Purpose**: Organize, author, and maintain project documentation  
> **Style**: Comprehensive reference with actionable guidance
> **Pair**: `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
> This document is paired with `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`, and any potential changes must be considered within the context of both docs.


## Quick Reference

This section helps you choose the right documentation file quickly and safely.

**Core entry points**

- **Project overview and philosophy**  
  See `README.md` for high-level context, core principles, and navigation.

- **Environment setup and run commands**  
  See the "Quick Start (Recommended)" and "Environment Setup" sections in `HOW_TO_RUN.md`.

- **Development workflow**  
  See `DEVELOPMENT_WORKFLOW.md` for the detailed standard development cycle and safe-change process.  
  For a condensed workflow summary, see `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`.

- **Architecture and data flow**  
  See `ARCHITECTURE.md` for module layout, data handling patterns, and UI architecture.  
  For an AI-optimized summary, see `ai_development_docs/AI_ARCHITECTURE.md`.

- **Logging, testing, and error handling**  
  - Logging: `logs/LOGGING_GUIDE.md` and `ai_development_docs/AI_LOGGING_GUIDE.md`  
  - Testing: `tests/TESTING_GUIDE.md` and `ai_development_docs/AI_TESTING_GUIDE.md`  
  - Error handling: `core/ERROR_HANDLING_GUIDE.md` and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`

- **AI collaboration and rules**  
  - Session constraints and guardrails: `ai_development_docs/AI_SESSION_STARTER.md`  
  - AI navigation and patterns: `ai_development_docs/AI_REFERENCE.md`

- **Change history and priorities**  
  - Detailed change history: `development_docs/CHANGELOG_DETAIL.md`  
  - AI-focused summaries: `ai_development_docs/AI_CHANGELOG.md`  
  - Plans and roadmaps: `TODO.md`, `development_docs/PLANS.md`

**When editing documentation**

- If you edit any document that has an AI or human counterpart, you must follow the rules in the "Documentation Synchronization Checklist" section below.
- Use generated reports (for example, `development_docs/LEGACY_REFERENCE_REPORT.md`) to detect stale references and path drift before finalizing changes.



## 1. Documentation Categories

This section defines how documentation is grouped and how each group should be used.

### 1.1. Human-facing documents

Human-facing documents are the detailed, explanatory sources of truth. They prioritize context, rationale, and troubleshooting.

Examples:

- **`README.md`**  
  High-level introduction, philosophy, and navigation.

- **`HOW_TO_RUN.md`**  
  Environment setup, run commands, and troubleshooting for starting services and the UI.

- **`DEVELOPMENT_WORKFLOW.md`**  
  Safe development cycle, preconditions, standard tasks, and emergency procedures.

- **`ARCHITECTURE.md`**  
  Directory layout, module responsibilities, user data model, and UI patterns.

- **`logs/LOGGING_GUIDE.md`**  
  Logging design, logger hierarchy, log file locations, rotation, and analysis approaches.

- **`tests/TESTING_GUIDE.md`**  
  Testing philosophy, types, organization, commands, parallel execution notes, and manual testing procedures.

- **`core/ERROR_HANDLING_GUIDE.md`**  
  Error handling architecture, patterns, recovery strategies, and error logging practices.

- **`PROJECT_VISION.md`**  
  Longer-term goals, values, and direction of the project.

When in doubt, human-focused docs are the place to look for rationale, context, and full explanations.

### 1.2. AI-facing documents

AI-facing documents are concise references that help AI collaborators behave safely and efficiently. They summarize patterns and route to the right human documents.

Key AI-facing docs:

- **`ai_development_docs/AI_SESSION_STARTER.md`**  
  Session constraints, must-follow rules, and safety boundaries.

- **`ai_development_docs/AI_REFERENCE.md`**  
  AI-oriented troubleshooting, escalation patterns, and routing to other AI docs.

- **`ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`**  
  Condensed development workflow, with links to sections in `DEVELOPMENT_WORKFLOW.md`.

- **`ai_development_docs/AI_ARCHITECTURE.md`**  
  High-level architectural cues and module overviews, with references to `ARCHITECTURE.md`.

- **`ai_development_docs/AI_DOCUMENTATION_GUIDE.md`**  
  AI-focused navigation for the documentation set and quick reference for sync rules.

- **`ai_development_docs/AI_LOGGING_GUIDE.md`**  
  Fast logging usage patterns, triage workflows, and log locations.

- **`ai_development_docs/AI_TESTING_GUIDE.md`**  
  Fast testing patterns, commands, and debugging guidance.

- **`ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`**  
  Error handling patterns, error categories, and links to `core/ERROR_HANDLING_GUIDE.md`.

- **`ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md`**  
  Patterns for safely removing legacy code and using automated reports.

AI-facing docs should not duplicate full explanations when a human doc already covers them; they should instead point to the relevant section.

### 1.3. Generated and analytical documentation

Some documents are generated by tools and must not be hand-edited. They are used as references and reports, not as primary editing targets.

Examples (non-exhaustive):

- **`development_docs/FUNCTION_REGISTRY_DETAIL.md`**  
- **`development_docs/MODULE_DEPENDENCIES_DETAIL.md`**  
- **`development_docs/LEGACY_REFERENCE_REPORT.md`**  
- **`development_docs/UNUSED_IMPORTS_REPORT.md`**  
- **`development_docs/HIGH_COMPLEXITY_FUNCTIONS_ANALYSIS.md`**  
- **`development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`**  
- **`ai_development_docs/AI_FUNCTION_REGISTRY.md`**  
- **`ai_development_docs/AI_MODULE_DEPENDENCIES.md`**

For a more complete list and generation details, see the "Generated Documentation Standards" section below.


## 2. Standards and Templates

This section defines how documentation files should be structured, labeled, and cross-referenced.

### 2.1. Metadata for `.md` documentation files

Every documentation file (`.md`) must start with a metadata block so it can be located and referenced unambiguously.

Required format:

```markdown
# File Name

> **File**: `relative/path/from/project/root`
> **Audience**: [Target audience]
> **Purpose**: [What this document is for]
> **Style**: [Tone and depth]
> **Pair**: `<PAIRED_DOC_PATH>`  # Only for human/AI doc pairs
> **Parent**: `<PARENT_DOC_PATH>`  # Only for subordinate docs
```

Notes:
- `File` must always match the relative path from the project root (for example, `logs/LOGGING_GUIDE.md`).
- `Pair` must be present for all docs that participate in a doc pair (for example, `ai_development_docs/AI_LOGGING_GUIDE.md`).
  - The `Pair` line should be followed by a short sentence stating that changes must be considered in the context of both docs.
- `Parent` is used when a doc is subordinate to a higher-level doc (for example, manual guides under a primary testing guide).
  - It does not imply H2 lockstep like Pair.
  - It exists purely to guide routing, standards, and terminology.
For docs that are neither paired nor subordinate, omit both `Pair` and `Parent`.

Examples:

Paired doc (human-side):

```markdown
# File Name

> **File**: `logs/LOGGING_GUIDE.md`
> **Audience**: Developers and maintainers
> **Purpose**: Explain how logging works and how to use it safely
> **Style**: Detailed, explanatory
> **Pair**: `ai_development_docs/AI_LOGGING_GUIDE.md`
> This document is paired with `ai_development_docs/AI_LOGGING_GUIDE.md` and any changes must be considered in the context of both docs.
```

AI-side paired doc:
```markdown
> **File**: `ai_development_docs/AI_LOGGING_GUIDE.md`
> **Pair**: `logs/LOGGING_GUIDE.md`
> **Audience**: AI collaborators and tools
> **Purpose**: Routing and constraints for logging usage
> **Style**: Minimal, routing-first
> For detailed behavior, examples, and rationale, use the matching sections in `logs/LOGGING_GUIDE.md`.
> Keep this file’s H2 headings in lockstep with `logs/LOGGING_GUIDE.md` when making changes.
```

Subordinate (parented) doc:
# File Name

```markdown
> **File**: `tests/MANUAL_TESTING_GUIDE.md`
> **Audience**: Developers and AI assistants performing manual testing
> **Purpose**: Canonical manual testing flows and checklists
> **Style**: Checklist-first, concise but detailed
> **Parent**: `tests/TESTING_GUIDE.md`
> This document is subordinate to `tests/TESTING_GUIDE.md` and must remain consistent with its standards and terminology.
```

### 2.2. Metadata for `.mdc` rule files

For `.mdc` rule files used by tools like Cursor:

- Prefer YAML frontmatter with a `file` field, or,
- Use a single comment line if there is no frontmatter.

Example with frontmatter:

```yaml
---
description: "AI behavior rules for error handling"
file: ".cursor/rules/testing-guidelines.mdc"
---
```

Example with comment only:

```markdown
<!-- File: .cursor/rules/testing-guidelines.mdc -->
```

### 2.3. Structure guidelines for human-facing docs

Human-facing docs (for example, `DOCUMENTATION_GUIDE.md`, `logs/LOGGING_GUIDE.md`, `tests/TESTING_GUIDE.md`) should:

- Use numbered H2/H3 headings as described in section 2.5.
- Include detailed explanations, rationale, and examples.
- Prefer step-by-step checklists where possible.
- Cross-reference other docs using specific section numbers when you are pointing to particular behavior or rules.

### 2.4. Structure guidelines for AI-facing docs

AI-facing docs in `ai_development_docs/` should:

- Keep content short and routing-focused.
- Prefer linking to AI_* docs first, then to human docs for deep detail.
- Avoid reproducing long explanations that already exist in human-facing docs.
- Emphasize constraints, entry points, and which sections of human docs to use.

### 2.5. Heading numbering standard

All main documentation files must use numbered H2 and H3 headings:

- **H2 headings**: Numbered sequentially starting at 1 (for example, `## 1. Section Title`, `## 2. Next Section`).
- **H3 headings**: Numbered with the parent section number (for example, `### 2.1. Subsection`, `### 2.2. Another Subsection`).
- **Standard format**: Numbers must include a trailing period and space (for example, `## 2. Title` not `## 2 Title`).
- **Exceptions**: Changelog files, plan files, and `TODO.md` are excluded from numbering as they have their own structure.
- **Special cases**: Q&A headings (for example, `Q: ...`) and step headings (for example, `Step 1: ...`) should be converted to bold text instead of additional numbered headings.

### 2.6. Cross-referencing standards

Use these rules whenever you link from one documentation file to another:

- When referencing another topic from a detailed (human) doc, prefer the detailed doc in that category first (for example, `tests/TESTING_GUIDE.md`). If an AI-facing doc exists, you may mention it as the AI counterpart.
- When referencing another topic from an AI doc, prefer the AI_* doc first (for example, `ai_development_docs/AI_TESTING_GUIDE.md`). That AI doc should then route to the matching human doc as needed.
- When referencing a specific section in another doc, use numbered section references, for example: `See section 2. "Logging Architecture" in logs/LOGGING_GUIDE.md.`
- Paired docs must maintain identical H2 heading sets. When you add, rename, remove, or reorder an H2 in one doc, apply the same change in its paired doc.

## 3. Documentation Synchronization Checklist

This section replaces the standalone documentation sync checklist. It defines how to keep paired documentation files synchronized.

### 3.1. Paired documentation files

The following pairs must be kept in sync:

- `DEVELOPMENT_WORKFLOW.md` <-> `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`  
- `ARCHITECTURE.md` <-> `ai_development_docs/AI_ARCHITECTURE.md`  
- `DOCUMENTATION_GUIDE.md` <-> `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`  
- `development_docs/CHANGELOG_DETAIL.md` <-> `ai_development_docs/AI_CHANGELOG.md`  

Specialized guides:

- `logs/LOGGING_GUIDE.md` <-> `ai_development_docs/AI_LOGGING_GUIDE.md`  
- `tests/TESTING_GUIDE.md` <-> `ai_development_docs/AI_TESTING_GUIDE.md`  
- `core/ERROR_HANDLING_GUIDE.md` <-> `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`

Rules for paired docs:

- The **set of H2 headings must be identical** between the human and AI version.  
- You may shorten, reorder, or add subheadings (H3, H4) independently, as long as the H2 set stays the same.  
- When you add, rename, or remove any H2 in one file, you must make the same change in its pair.

### 3.2. Before making documentation changes

Use this checklist before editing any doc that might be part of a pair:

- Identify whether the file has an AI or human counterpart.  
- If it does, open both files at the same time.  
- Run the docs sync tools if needed to detect existing drift (see "Automated tools" below).  
- Review `development_docs/LEGACY_REFERENCE_REPORT.md` for path drift and outdated references.

### 3.3. During documentation updates

While editing paired docs:

- Update the human-facing doc first to get the full explanation correct.  
- Update the AI-facing doc second, summarizing and routing to the human doc instead of duplicating text.  
- Keep the H2 headings aligned between both files (add/remove/rename at the same time).  
- Verify all cross-references between docs are still accurate (paths, section names, and filenames).

### 3.4. After documentation updates

When you are done editing:

- Run the docs sync tools again to confirm there are no new sync issues.  
- Skim the diffs of both files to check that H2 headings match as a set.  
- Update any "Last Updated" metadata if present.  
- Validate that links to generated reports or other docs resolve correctly in the repository.

### 3.5. Automated tools

Several automation tools support documentation and sync:

- `python ai_development_tools/ai_tools_runner.py doc-sync`  
  Scans for mismatched headings, path drift, ASCII compliance, and heading numbering issues in documentation.

- `python ai_development_tools/ai_tools_runner.py legacy`  
  Analyses references and code paths for deprecated or stale usage.

- `python ai_development_tools/ai_tools_runner.py version-sync`  
  Helps ensure version strings remain coherent across files.

Additional tools such as `audit`, `quick-status`, `test-coverage`, and `validate-work` live in `ai_development_tools/ai_tools_runner.py` and may output supporting reports used by documentation.

For detailed tool behavior, see `ai_development_tools/AI_DEV_TOOLS_GUIDE.md`.


## 4. Maintenance Guidelines

This section covers ongoing maintenance practices beyond basic synchronization.

### 4.1. Updating AI documentation

When updating an AI-facing document:

- Prefer referencing other AI docs first, then human docs.  
- Keep content brief and operational: commands, patterns, and routing.  
- Remove redundant text when another AI doc already covers the same rule.  
- Add explicit references to the relevant section in the paired human doc for context.  
- When you add a new section in the AI doc, ensure the same H2 exists in the paired human doc.

### 4.2. Updating human documentation

When updating a human-facing document:

- Provide enough context and examples that a beginner developer can follow the guidance.  
- Include motivations, edge cases, and troubleshooting tips where they matter.  
- Keep cross-references up to date; prefer linking to specific sections instead of entire files when possible.  
- If the doc has an AI counterpart, make sure the AI doc still accurately summarizes and routes to the correct sections.

### 4.3. Adding new documentation

When adding a new documentation file:

- Decide whether it should be human-facing, AI-facing, or both.  
- If a new pair is needed, register it conceptually under "Paired documentation files" and ensure both files share the same H2 set.  
- Follow the file address requirement and standard structure for the chosen audience.  
- If the document is generated, ensure it follows the "Generated Documentation Standards" section rather than these general rules.

### 4.4. Generated documentation maintenance

- Never manually edit generated files listed in "Generated Documentation Standards".  
- To update generated content, change the generating tool or its configuration and regenerate.  
- If a generated file gains manually curated sections, document the rules clearly in this guide and in the generating tool's README.


## 5. Generated Documentation Standards

This section defines how generated docs must identify themselves and how they are maintained.

### 5.1. Identification requirements

Every generated file must begin with a clear statement that it is generated and not to be edited manually.

Example:

```markdown
> **Generated**: This file is auto-generated by ai_development_tools/generate_function_registry.py. Do not edit manually.
> **Generated by**: ai_development_tools/generate_function_registry.py
```

Generated metadata should include:

- The generating tool path.  
- A brief description of what the tool does.  
- Any important notes (for example, whether manual annotations are preserved).

### 5.2. Maintenance rules

- Do not hand-edit generated outputs except where explicitly allowed and documented.  
- To change the content of a generated file, update the script in `ai_development_tools` or related tooling and regenerate.  
- If manual annotations are allowed (for example, in a "hybrid" report), clearly mark which sections are tool-owned and which are human-owned.

### 5.3. Known generated files

Common generated files include:

- `development_docs/FUNCTION_REGISTRY_DETAIL.md`  
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`  
- `development_docs/LEGACY_REFERENCE_REPORT.md`  
- `development_docs/UNUSED_IMPORTS_REPORT.md`  
- `development_docs/HIGH_COMPLEXITY_FUNCTIONS_ANALYSIS.md`  
- `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`  
- `ai_development_docs/AI_FUNCTION_REGISTRY.md`  
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md`

For a full and current list, refer to generated file headers and the `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` documentation.

### 5.4. Automation commands for generated docs

Use `ai_development_tools/ai_tools_runner.py` for documentation-related automation (for example, sync checks and report generation), instead of editing generated files by hand.

Typical documentation-related commands include:

- `docs` - regenerate documentation artifacts and reports  
- `doc-sync` - check documentation synchronisation and paired headings  
- `coverage` - regenerate coverage metrics that feed into documentation planning  
- `legacy` - scan for legacy references that may require documentation updates  
- `unused-imports` - detect unused imports and generate reports under `development_docs/`  
- `trees` - generate directory tree reports that can be referenced from documentation  
- `status` - print a quick system status summary that can inform high-level docs

The definitive list of commands and their semantics lives in `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` and `ai_development_tools/services/operations.py`. Do not duplicate that full reference here; treat this guide as a routing layer and use the README as the source of truth for command behavior.

## 6. Resources

Useful supporting materials and locations:

- `.cursor/rules/`  
  Rulesets that govern AI behavior and baseline constraints.

- `ai_development_docs/AI_SESSION_STARTER.md`  
  Required reading for AI collaborators before performing code changes.

- `ai_development_docs/AI_REFERENCE.md`  
  Central AI navigation and troubleshooting reference.

- `development_docs/CHANGELOG_DETAIL.md` and `ai_development_docs/AI_CHANGELOG.md`  
  Detailed and condensed histories of changes.

- `ai_development_tools/AI_DEV_TOOLS_GUIDE.md`  
  Entry point for documentation on analysis, audit, and sync tools.

- Team notes, meeting summaries, and planning docs in `development_docs/` or adjacent locations for context not yet formalized here.