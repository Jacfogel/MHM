# AI Documentation Guide

> **File**: `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
> **Pair**: [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md)
> **Audience**: AI collaborators and tools
> **Purpose**: Fast routing across docs for AI collaborators
> **Style**: Minimal, routing-first
> For detailed behavior and rationale, use the matching sections in DOCUMENTATION_GUIDE.md.
> Keep this file's H2 headings in lockstep with DOCUMENTATION_GUIDE.md whenever you change the structure.

## Quick Reference

Use this to decide which doc to open or reference.

- Project overview and philosophy: [README.md](README.md)
- Environment setup and run commands: [HOW_TO_RUN.md](HOW_TO_RUN.md) (Quick Start, Troubleshooting)
- Development workflow and safe changes: [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)
- Logging, testing, and error handling:
  - Logging: [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md)
  - Testing: [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)
  - Error handling: [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md)
- Documentation system and sync rules:
  - This doc: AI_DOCUMENTATION_GUIDE.md (routing rules and doc classes)
  - Detailed behavior: [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md), section 1. "Documentation Categories" and section 3. "Documentation Synchronization Checklist"
- AI collaboration and navigation helpers:
  - Session constraints and guardrails: [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md)
  - AI navigation and patterns: [AI_REFERENCE.md](ai_development_docs/AI_REFERENCE.md)

- Cross-referencing standards (AI view):
  - From AI docs, prefer AI_* docs first. Only reference detailed human docs directly when you need to send a human to specific deep explanations.
  - From human docs, prefer human docs first. For full rules, see section 3. "Documentation Synchronization Checklist" in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).

## 1. Documentation Categories

Minimal rules for which class of doc to use.

### 1.1. Detailed documentation

Use detailed docs when:

- You need explanations, rationale, or edge cases.  
- You are telling a human how to understand or extend the system.

Key examples:  
[README.md](README.md), [HOW_TO_RUN.md](HOW_TO_RUN.md), [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md),  
[ARCHITECTURE.md](ARCHITECTURE.md), [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md),  
[TESTING_GUIDE.md](tests/TESTING_GUIDE.md), [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md),  
[DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).

### 1.2. AI-facing documents

Use AI docs when:

- You need short patterns, commands, or routing hints.  
- You are deciding which doc or module to inspect next.

Key examples:  
[AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md), [AI_REFERENCE.md](ai_development_docs/AI_REFERENCE.md),  
[AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md), [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md),  
[AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md),  
AI_DOCUMENTATION_GUIDE.md.

### 1.3. Generated and analytical docs

Generated docs are read-only inputs (for example: registries, dependency maps, legacy reports).

- Do not advise editing them directly.  
- When they are wrong or stale, suggest updating the generator and regenerating the file rather than manual edits.


## 2. Standards and Templates

Minimal standards AI must respect.

- Every `.md` doc must include a `> **File**: \`...\`` line with its path from the repo root.  
- Number H2 and H3 headings (for example `## 2. Logging Architecture`, `### 2.1. Central logger module`) and ensure numbering stays aligned with any paired document. 
- Detailed docs should also include Audience/Purpose/Style when helpful.  
- Every `.mdc` rule file must either:
  - Use YAML frontmatter with a `file:` field, or  
  - Include a comment like `<!-- File: .cursor/rules/example.mdc -->`.

### 2.1. Heading numbering standard

- H2 headings: Sequential numbering starting at 1 (e.g., `## 1. Section`, `## 2. Next`)
- H3 headings: Parent section number + sub-number (e.g., `### 2.1. Subsection`, `### 2.2. Another`)
- Standard format: Trailing period and space required (e.g., `## 2. Title` not `## 2 Title`)
- Exceptions: Changelogs, plans, TODO.md excluded (own structure)
- Special cases: Q&A and Step headings -> bold text, not numbered

When suggesting new docs or edits:

- Follow the patterns in "Standards and Templates" in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).  
- Keep AI docs short and routing-focused; avoid re-explaining detailed content from the paired docs.

### 2.2. Example marking standards

**Mark examples clearly** so path drift checker skips them:
- Use `[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]` markers at start of example sections
- Use "Examples:" or "Example Usage:" headings for example sections
- Code blocks (between ` ``` `) are automatically excluded
- Place markers within 5 lines of path references they mark

**Why:** Examples often show intentional "bad" examples (short paths, non-existent files) that should not be flagged as path drift.

### 2.3. File path reference standards

**Primary rule: Use full paths from project root for all file references.**

**Format:**
- **Full paths (preferred)**: `development_tools/config/config.py`, `core/service.py`
- **Short names (acceptable only when directory is 100% obvious)**: In [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md), `development_tools/config/config.py` should still be used (full paths preferred)
- **Relative paths (use sparingly)**: `../README.md` (from `ai_development_docs/`), `AI_LOGGING_GUIDE.md` (same directory)

**Best practices:**
- Always prefer full paths when referencing files outside current directory
- Verify paths exist using file search tools before referencing
- Use backticks for file references: `` `core/service.py` ``

**Markdown link standard (for .md references):**
- Use only the filename as the link text, not the path.
  - **OK:** `[LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)`
  - **OK:** `[AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)`
- Keep the full project-root path in the link target so links remain unambiguous.
- Only convert `.md` references when the target file actually exists in the repo.
- **Metadata section link deduplication**: In metadata sections (H1 heading + lines starting with `>`), each unique file path is linked only once. Subsequent references to the same file in metadata remain as backticks (not converted to links) to avoid repetitive links.
- Do **not** convert:
  - `> **File**:` metadata lines
  - Code fences or inline code examples
  - Self-references to the current document
  - Example contexts (marked with `[OK]`, `[AVOID]`, etc.)

**Path drift checker:** Validates that referenced files exist. May flag short names if directory cannot be inferred from context.

### 2.4. Parent metadata (subordinate docs)

Some docs are not part of a human/AI pair but are still subordinate to a higher-level document.  
These use a `Parent` field in their metadata to guide AI behavior.

Example:

```markdown
> **File**: `tests/MANUAL_TESTING_GUIDE.md`
> **Audience**: Developers and AI assistants performing manual testing
> **Purpose**: Canonical manual testing flows and checklists
> **Style**: Checklist-first, concise but detailed
> **Parent**: `tests/TESTING_GUIDE.md`
> This document is subordinate to `tests/TESTING_GUIDE.md` and must remain consistent with its standards and terminology.
```

Rules for AI:

Do not treat `Parent` like `Pair`:
- No H2 lockstep requirement.
- No need to mirror section structure.

Before modifying a subordinate doc:
- Read the parent doc first.
- Use the parent to resolve terminology, standards, and safety constraints.

If a change alters behavior or expectations defined in the parent:
- Update both the parent doc and the subordinate doc, or
- Clearly flag the divergence.

Typical examples:
- `tests/MANUAL_TESTING_GUIDE.md`
  - `Parent`: `tests/TESTING_GUIDE.md`
- `tests/MANUAL_DISCORD_TEST_GUIDE.md`
  - `Parent`: [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md)
- [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md)
  - `Parent`: [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md)

## 3. Documentation Synchronization Checklist

AI summary of the sync rules. Full detail is in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).

### 3.1. Paired documentation files

Treat these as synchronized pairs:

- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) <-> `AI_DEVELOPMENT_WORKFLOW.md`  
- [ARCHITECTURE.md](ARCHITECTURE.md) <-> `AI_ARCHITECTURE.md`  
- [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) <-> `AI_DOCUMENTATION_GUIDE.md`  
- [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) <-> `AI_CHANGELOG.md`  
- [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) <-> `AI_LOGGING_GUIDE.md`  
- [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) <-> `AI_TESTING_GUIDE.md`  
- [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md) <-> `AI_ERROR_HANDLING_GUIDE.md`

### 3.2. Hard rules

- The H2 heading set must be identical across each pair.  
- If you add, remove, or rename an H2 in one file, you must do the same in its pair.  
- H3+ structure can differ.

### 3.3. Minimal checklist

- Before editing a paired doc, check if it has a counterpart and open both.  
- Prefer updating the detailed doc first, then adjust the AI doc to match.  
- After edits, run `python development_tools/run_development_tools.py doc-sync` if available and fix any mismatches.


## 4. Maintenance Guidelines

High-level guidance.

- When patterns change (workflow, architecture, logging, testing, error handling), update the relevant detailed doc section first.  
- After detailed docs change, update the paired AI docs to keep H2 sets aligned and summaries accurate.  
- Prefer extending existing sections over inventing new top-level docs; if a new pair is truly needed, ensure both sides share the same H2 set and add them to the pairing list above.


## 5. Generated Documentation Standards

AI view of generated docs.

- Generated files must clearly state they are generated and name the tool responsible.  
- Do not recommend editing generated files directly.  
- If content is wrong or stale, advise:
  - Updating the generator (for example, scripts in `development_tools/`), then  
  - Regenerating the file.

### 5.1. Metadata Standards

All generated files must include standardized metadata to identify their origin and generation details.

**Markdown files (.md):**
```markdown
# Document Title

> **File**: `path/to/file.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: YYYY-MM-DD HH:MM:SS
> **Source**: `python development_tools/path/to/generator.py` - Tool Description
> **Audience**: [Target audience]
> **Purpose**: [What this document is for]
> **Status**: **ACTIVE** - [Brief status note]
> **Version**: --scope - AI Collaboration System Active
> **Last Updated**: 2025-12-03
```

**JSON files (.json):**
```json
{
  "generated_by": "Tool Name - Tool Description",
  "last_generated": "YYYY-MM-DD HH:MM:SS",
  "source": "python development_tools/path/to/tool.py [command]",
  "note": "This file is auto-generated. Do not edit manually.",
  "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff",
  ...
}
```

**Generated files using this standard:**
- Markdown: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/MODULE_DEPENDENCIES_DETAIL.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`, `development_docs/UNUSED_IMPORTS_REPORT.md`, `development_docs/TEST_COVERAGE_REPORT.md`, `development_docs/DIRECTORY_TREE.md`, `ai_development_docs/AI_FUNCTION_REGISTRY.md`, `ai_development_docs/AI_MODULE_DEPENDENCIES.md`, `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`
- JSON: `development_tools/reports/analysis_detailed_results.json`, `development_tools/error_handling/error_handling_details.json`, `development_tools/config/analyze_config_results.json`

For detailed standards, see section 5.1 in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).

For generator usage and tooling details, see [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md).


For documentation automation (sync checks, reports, analysis), call:

```bash
python development_tools/run_development_tools.py <command>
```

and rely on [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) for command descriptions and options.

Typical documentation-related commands to suggest (without redefining them here):

- `docs`  
- `doc-sync`  
- `coverage`  
- `legacy`  
- `unused-imports`  
- `trees`  
- `status`  

## 6. Resources

If this file is not enough:

- [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) for detailed rules and rationale.  
- [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) for documentation-related tools and reports.  
- [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md) for session-wide constraints and priorities.  
- [AI_REFERENCE.md](ai_development_docs/AI_REFERENCE.md) for routing and escalation patterns.  
- [AI_CHANGELOG.md](ai_development_docs/AI_CHANGELOG.md) for recent changes that may affect documentation.