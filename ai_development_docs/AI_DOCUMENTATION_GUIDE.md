# AI Documentation Guide - Quick Reference

> **Purpose**: Fast navigation of documentation assets for AI collaborators  
> **Style**: Concise, pattern-focused, actionable  
> **For details**: See [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md)

## Quick Reference

### Document Selection Decision Tree
1. Orientation -> `../README.md`
2. Setup/usage -> `../HOW_TO_RUN.md`
3. Safe workflow -> `../DEVELOPMENT_WORKFLOW.md`
4. Architecture -> `../ARCHITECTURE.md`
5. AI collaboration -> `AI_SESSION_STARTER.md`
6. Status snapshot -> `AI_CHANGELOG.md`, `../TODO.md`
7. Full history -> `../development_docs/CHANGELOG_DETAIL.md`

### Key Navigation Links
- Human overview: `../README.md`
- Safe practices: `../DEVELOPMENT_WORKFLOW.md`
- Architecture: `../ARCHITECTURE.md`
- AI rules: `.cursor/rules/*.mdc`
- Change tracking: `AI_CHANGELOG.md`

## Documentation Categories

### Human-Facing Documents
- `README.md`, `HOW_TO_RUN.md`, `DEVELOPMENT_WORKFLOW.md`, `ARCHITECTURE.md` -> detailed context and examples.

### AI-Facing Documents
- `AI_SESSION_STARTER.md`, `AI_REFERENCE.md`, `AI_DEVELOPMENT_WORKFLOW.md`, `AI_ARCHITECTURE.md`, this guide -> quick patterns.
- `AI_LOGGING_GUIDE.md`, `AI_TESTING_GUIDE.md`, `AI_ERROR_HANDLING_GUIDE.md` -> specialized technical guides.

### Status and History
- `AI_CHANGELOG.md`, `../TODO.md`, `development_docs/PLANS.md` -> current priorities and upcoming work.

### Technical Reference
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/MODULE_DEPENDENCIES_DETAIL.md` -> deep API and dependency maps.
- `ai_development_tools/audit_package_exports.py` -> audit tool for package-level exports (`--package <name>` or `--all`).

## Standards and Templates

### Standard Document Structure
- Metadata block (audience, purpose, style) + quick reference + main sections.
- Keep section order aligned across paired docs.
- Link to the partner document for the opposite audience.

### Cursor Command Documentation Standards
- Commands describe behaviours, not raw shell transcripts.
- Use PowerShell syntax with `$LASTEXITCODE` checks.
- Require structured output sections for consistent answers.
- List critical files explicitly.

### Coding and Naming References
- Helper functions follow `_main_function__helper_name`.
- Public APIs should stay wrapper-free; consolidate duplicates.
- Reference canonical module paths when documenting behaviour.
- Package-level imports: Prefer `from <package> import <item>` (e.g., `from core import CheckinAnalytics`). Module-level imports still work for backward compatibility.

## Main Sections
- Mirror the human guide's section order (Quick Reference, Main Sections, maintenance notes).
- Pull deep explanations from `../DOCUMENTATION_GUIDE.md`; keep this file scoped to action cues.

## Audience-Specific Optimization

### Human-Facing Documents
- Provide rationale, examples, and troubleshooting detail.
- Maintain an encouraging tone with cross-references.

### AI-Facing Documents
- Capture decision trees, safeguards, and essential patterns only.
- Avoid duplicating the same guidance across multiple AI files-link instead.

## Maintenance Guidelines

### Paired Documentation
- Update these pairs together with identical section order: `DEVELOPMENT_WORKFLOW` <-> `AI_DEVELOPMENT_WORKFLOW`, `ARCHITECTURE` <-> `AI_ARCHITECTURE`, `DOCUMENTATION_GUIDE` <-> this file, `CHANGELOG_DETAIL` <-> `AI_CHANGELOG`, `LOGGING_GUIDE` <-> `AI_LOGGING_GUIDE`, `TESTING_GUIDE` <-> `AI_TESTING_GUIDE`, `ERROR_HANDLING_GUIDE` <-> `AI_ERROR_HANDLING_GUIDE`.

### Updating AI Documentation
- Summarise key rules and point to the authoritative human doc.
- Remove redundancy when another AI file already covers it.

### Updating Human Documentation
- Expand on rationale, provide examples, and surface troubleshooting.
- Keep cross-references current.

### Adding New Documentation
- Decide primary audience first, then follow that style guide.
- Register the new file in this mapping and create its counterpart if needed.

## Generated Documentation Standards

### Identification Requirements
- Generated files must include the standard header with generator name, timestamp, and source.

### Maintenance Rules
- Never hand-edit generated outputs; update the generating tool and regenerate.
- **Exception**: `MODULE_DEPENDENCIES_DETAIL.md` preserves manual enhancements between `<!-- MANUAL_ENHANCEMENT_START -->` and `<!-- MANUAL_ENHANCEMENT_END -->` markers.
- Archive or rotate outputs as needed for audits.

### Known Generated Files
- Reference the full generated-file roster in `../DOCUMENTATION_GUIDE.md`.
- Prioritise these when responding: `ai_development_tools/AI_STATUS.md`, `ai_development_tools/AI_PRIORITIES.md`, `development_docs/DIRECTORY_TREE.md`, `development_docs/UNUSED_IMPORTS_REPORT.md`.

## Resources
- `.cursor/rules/` for governing policies.
- `ai_development_tools/README.md` for automation entry points.
- `AI_SESSION_STARTER.md` for must-follow constraints before coding.
- `../development_docs/CHANGELOG_DETAIL.md` for rich historical context.
