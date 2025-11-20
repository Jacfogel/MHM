# AI Documentation Guide

> **File**: `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
> **Pair**: `DOCUMENTATION_GUIDE.md`
> **Audience**: AI collaborators and tools
> **Purpose**: Fast routing across docs for AI collaborators
> **Style**: Minimal, routing-first
> For detailed behavior and rationale, use the matching sections in `DOCUMENTATION_GUIDE.md`.
> Keep this file's H2 headings in lockstep with `DOCUMENTATION_GUIDE.md` whenever you change the structure.

## Quick Reference

Use this to decide which doc to open or reference.

- Project overview and philosophy: `../README.md`
- Environment setup and run commands: `../HOW_TO_RUN.md` (Quick Start, Troubleshooting)
- Development workflow and safe changes: `AI_DEVELOPMENT_WORKFLOW.md`
- Logging, testing, and error handling:
  - Logging: `AI_LOGGING_GUIDE.md`
  - Testing: `AI_TESTING_GUIDE.md`
  - Error handling: `AI_ERROR_HANDLING_GUIDE.md`
- Documentation system and sync rules:
  - This doc: `AI_DOCUMENTATION_GUIDE.md` (routing rules and doc classes)
  - Detailed behavior: `../DOCUMENTATION_GUIDE.md`, section 1. "Documentation Categories" and section 3. "Documentation Synchronization Checklist"
- AI collaboration and navigation helpers:
  - Session constraints and guardrails: `AI_SESSION_STARTER.md`
  - AI navigation and patterns: `AI_REFERENCE.md`

- Cross-referencing standards (AI view):
  - From AI docs, prefer AI_* docs first. Only reference detailed human docs directly when you need to send a human to specific deep explanations.
  - From human docs, prefer human docs first. For full rules, see section 3. "Documentation Synchronization Checklist" in `DOCUMENTATION_GUIDE.md`.

## 1. Documentation Categories

Minimal rules for which class of doc to use.

### 1.1. Detailed documentation

Use detailed docs when:

- You need explanations, rationale, or edge cases.  
- You are telling a human how to understand or extend the system.

Key examples:  
`../README.md`, `../HOW_TO_RUN.md`, `../DEVELOPMENT_WORKFLOW.md`,  
`../ARCHITECTURE.md`, `../logs/LOGGING_GUIDE.md`,  
`../tests/TESTING_GUIDE.md`, `../core/ERROR_HANDLING_GUIDE.md`,  
`../DOCUMENTATION_GUIDE.md`.

### 1.2. AI-facing documents

Use AI docs when:

- You need short patterns, commands, or routing hints.  
- You are deciding which doc or module to inspect next.

Key examples:  
`AI_SESSION_STARTER.md`, `AI_REFERENCE.md`,  
`AI_DEVELOPMENT_WORKFLOW.md`, `AI_ARCHITECTURE.md`,  
`AI_LOGGING_GUIDE.md`, `AI_TESTING_GUIDE.md`, `AI_ERROR_HANDLING_GUIDE.md`,  
`AI_DOCUMENTATION_GUIDE.md`.

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
- Special cases: Q&A and Step headings → bold text, not numbered

When suggesting new docs or edits:

- Follow the patterns in "Standards and Templates" in `DOCUMENTATION_GUIDE.md`.  
- Keep AI docs short and routing-focused; avoid re-explaining detailed content from the paired docs.


## 3. Documentation Synchronization Checklist

AI summary of the sync rules. Full detail is in `DOCUMENTATION_GUIDE.md`.

### 3.1. Paired documentation files

Treat these as synchronized pairs:

- `DEVELOPMENT_WORKFLOW.md` <-> `AI_DEVELOPMENT_WORKFLOW.md`  
- `ARCHITECTURE.md` <-> `AI_ARCHITECTURE.md`  
- `DOCUMENTATION_GUIDE.md` <-> `AI_DOCUMENTATION_GUIDE.md`  
- `development_docs/CHANGELOG_DETAIL.md` <-> `AI_CHANGELOG.md`  
- `logs/LOGGING_GUIDE.md` <-> `AI_LOGGING_GUIDE.md`  
- `tests/TESTING_GUIDE.md` <-> `AI_TESTING_GUIDE.md`  
- `core/ERROR_HANDLING_GUIDE.md` <-> `AI_ERROR_HANDLING_GUIDE.md`

### 3.2. Hard rules

- The H2 heading set must be identical across each pair.  
- If you add, remove, or rename an H2 in one file, you must do the same in its pair.  
- H3+ structure can differ.

### 3.3. Minimal checklist

- Before editing a paired doc, check if it has a counterpart and open both.  
- Prefer updating the detailed doc first, then adjust the AI doc to match.  
- After edits, run `python ai_development_tools/ai_tools_runner.py doc-sync` if available and fix any mismatches.


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
  - Updating the generator (for example, scripts in `ai_development_tools/`), then  
  - Regenerating the file.

For generator usage and tooling details, see `ai_development_tools/AI_DEV_TOOLS_GUIDE.md`.


For documentation automation (sync checks, reports, analysis), call:

```bash
python ai_development_tools/ai_tools_runner.py <command>
```

and rely on `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` for command descriptions and options.

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

- `DOCUMENTATION_GUIDE.md` for detailed rules and rationale.  
- `ai_development_tools/AI_DEV_TOOLS_GUIDE.md` for documentation-related tools and reports.  
- `AI_SESSION_STARTER.md` for session-wide constraints and priorities.  
- `AI_REFERENCE.md` for routing and escalation patterns.  
- `AI_CHANGELOG.md` for recent changes that may affect documentation.