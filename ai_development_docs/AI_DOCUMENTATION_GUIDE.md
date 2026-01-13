# AI Documentation Guide

> **File**: `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`  
> **Pair**: [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md)  
> **Audience**: AI collaborators and tools  
> **Purpose**: Documentation standards (AI view): rules, conventions, constraints, and routing  
> **Style**: Brief, rule-heavy, and routing-aware  
> For detailed behavior, examples, and rationale, use the matching sections in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).  
> Keep this file's H2 headings in lockstep with [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) whenever you change the structure.

## 1. Quick Reference

Use this section to decide what to open or reference next.

### 1.1. Decision paths

- If you need project intent and priorities: use [PROJECT_VISION.md](../PROJECT_VISION.md) and [README.md](../README.md).
- If you need run commands or troubleshooting: use [HOW_TO_RUN.md](../HOW_TO_RUN.md).
- If you need architecture and module boundaries: use [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md), then [ARCHITECTURE.md](../ARCHITECTURE.md).
- If you need logging: use [AI_LOGGING_GUIDE.md](AI_LOGGING_GUIDE.md), then [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md).
- If you need testing: use [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md), then [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md).
- If you need error handling patterns: use [AI_ERROR_HANDLING_GUIDE.md](AI_ERROR_HANDLING_GUIDE.md), then [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md).
- If you need backups: use [AI_BACKUP_GUIDE.md](AI_BACKUP_GUIDE.md), then [BACKUP_GUIDE.md](../development_docs/BACKUP_GUIDE.md).

### 1.2. When editing documentation

- If the target doc is paired, follow section 4 in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).
- Prefer using documentation tooling (for example `python development_tools/run_development_tools.py doc-sync`) rather than guessing.

## 2. Documentation Categories

Minimal rules for which class of doc to use.

### 2.1. Human-facing documents

Use human docs when:
- You need explanation, rationale, edge cases, or troubleshooting.
- You are instructing a human how to understand or extend the system.

### 2.2. AI-facing documents

AI-facing docs must include:
- Critical rules, constraints, conventions, and boundaries that must be enforced.
- Routing guidance ("open this next") and entry points.
- Minimal summaries that point to the relevant human sections for deeper detail.

Do not mutate AI docs into pure routing lists. Keep them brief, but rule-heavy.

### 2.3. Generated and analytical documentation

Generated docs are read-only inputs (registries, dependency maps, legacy reports).
- Do not advise editing them directly.
- If a generated file is stale or wrong, recommend fixing the generator and regenerating.

## 3. Standards and Templates

AI must respect these standards when creating or editing documentation.

### 3.1. Metadata for `.md` documentation files

- Every `.md` doc must begin with a metadata block and include `> **File**:` with its path from repo root.
- If paired: include `Pair` and the lockstep sentence.
- If subordinate: include `Parent` (Parent does not imply H2 lockstep).

### 3.2. Metadata for `.mdc` rule files

For `.mdc` files:
- Prefer YAML frontmatter containing a `file:` field, or
- Use a comment-only marker with the file path.

### 3.3. Structure guidelines for human-facing docs

- Human docs must use numbered headings, include rationale and examples, and use section-number cross-references when pointing to specific rules.

### 3.4. Structure guidelines for AI-facing docs

AI docs should:
- Be brief, but include critical rules and boundaries.
- Prefer linking to AI_* docs first, then human docs for deep detail.
- Avoid reproducing long narrative explanations.

### 3.5. Heading numbering standard

- H2 headings: sequential numbering starting at 1 (e.g., `## 1. ...`, `## 2. ...`).
- H3 headings: parent section number + sub-number (e.g., `### 3.1. ...`).
- Format: trailing period and space required.

Exceptions:
- Changelogs, plan files, and `TODO.md` are excluded from numbering.

### 3.6. Example marking standards

Mark examples clearly so the path drift checker skips them:
- Use `[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]` markers near example sections.
- Code blocks are automatically excluded.
- Place markers within 5 lines of any path reference they mark.

### 3.7. File path reference standards

Primary rule: use full paths from project root for file references.

- Prefer: `core/service.py`, `development_tools/run_development_tools.py`, `ai_development_docs/AI_REFERENCE.md`.
- Avoid ambiguous short names like `config.py`, `operations.py`, `bot.py` unless directory context is 100% obvious.

Verify that referenced paths exist before asserting them.

### 3.8. Markdown link standard (for `.md` references)

- Use only the filename as link text (not the path).
- Keep full project-root paths in link targets.
- Only link files that exist.

Metadata link deduplication rule (human doc behavior):
- In metadata blocks, link each unique path once; subsequent repeats should remain as backticks.

## 4. Documentation Synchronization Checklist

### 4.1. Paired documentation files

- Paired human/AI docs must share the same H2 heading set.
- Any H2 structural change in one doc must be mirrored in the other doc immediately.

### 4.2. Synchronization workflow (practical)

1. Open both docs.
2. Edit the human doc first.
3. Mirror H2 changes into the AI doc immediately.
4. Update the AI doc rules, boundaries, and routing pointers to match the new reality.
5. Update cross-references and section numbers.
6. Run doc tooling checks.

### 4.3. Cross-doc consistency checks

Before finalizing:
- Verify referenced file paths exist.
- Verify section numbers referenced in text match current headings.
- Verify paired docs have identical H2 heading sets.
- Verify example markers are present around intentional bad examples.
- Verify numbering rules are followed.

### 4.4. When docs and code diverge

If docs and code disagree:
- Call out the mismatch explicitly.
- Propose whether docs, code, or both should change.
- Do not silently "fix" one side without noting the discrepancy.

### 4.5. Automated tools

Prefer using the development tools suite for enforcement:
- `python development_tools/run_development_tools.py doc-sync`
- `python development_tools/run_development_tools.py legacy`
- `python development_tools/run_development_tools.py version-sync`

## 5. Maintenance Guidelines

### 5.1. Updating AI documentation

- Prefer referencing AI docs first, then human docs.
- Keep content brief, but include critical rules and boundaries.
- Remove redundant text if another AI doc owns the rule.

### 5.2. Updating human documentation

- Human docs should contain detail, examples, and rationale.
- Keep cross-references and section numbers accurate.
- Ensure AI docs remain accurate summaries of constraints and routing.

### 5.3. Adding new documentation

- Decide whether a new doc needs an AI pair.
- If paired: create both and keep H2 sets identical.
- Apply metadata rules and numbering rules.

### 5.4. Generated documentation maintenance

- Do not edit generated files manually.
- Change the generator and regenerate.
- If hybrid files exist, clearly mark tool-owned vs human-owned sections.

## 6. Generated Documentation Standards

### 6.1. Identification requirements

Generated docs must clearly identify themselves as generated and must not be hand-edited.
See section 6.1 in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) for the canonical metadata formats.

### 6.2. Maintenance rules

- Regenerate generated files by updating the generator, not by manual edits.
- Preserve required metadata fields in generated outputs.

### 6.3. Known generated files

Treat generated files as reports; do not treat them as editable docs.

### 6.4. Automation commands for generated docs

Use `development_tools/run_development_tools.py` for doc-related automation.
Do not invent command semantics; defer to [DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/DEVELOPMENT_TOOLS_GUIDE.md).

## 7. Resources

- Cursor rules: `.cursor/rules/`
- Required AI guardrails: [AI_SESSION_STARTER.md](AI_SESSION_STARTER.md)
- AI navigation: [AI_REFERENCE.md](AI_REFERENCE.md)
- Tools docs: [AI_DEVELOPMENT_TOOLS_GUIDE.md](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md)