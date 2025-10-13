# Documentation Guide

> **Audience**: Developers and contributors  
> **Purpose**: Organize, author, and maintain project documentation  
> **Style**: Comprehensive reference with actionable guidance

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md) for AI-optimized quick reference**

## Quick Reference

### Document Selection Decision Tree
1. **New to the project?** Start with `README.md`.
2. **Need setup or run instructions?** Read `HOW_TO_RUN.md` and `QUICK_REFERENCE.md`.
3. **Planning development work?** Follow `DEVELOPMENT_WORKFLOW.md`.
4. **Exploring the architecture?** Dive into `ARCHITECTURE.md`.
5. **Looking for AI collaboration context?** Check `ai_development_docs/AI_*` files.
6. **Tracking current status?** Review `TODO.md` and `ai_development_docs/AI_CHANGELOG.md`.
7. **Need full history?** Consult `development_docs/CHANGELOG_DETAIL.md`.
8. **Auditing decisions or functions?** Use `development_docs/FUNCTION_REGISTRY_DETAIL.md` and `development_docs/MODULE_DEPENDENCIES_DETAIL.md`.

### Key Navigation Links
- **Project Overview**: `README.md`
- **Getting Started**: `HOW_TO_RUN.md`
- **Safe Practices**: `DEVELOPMENT_WORKFLOW.md`
- **Architecture**: `ARCHITECTURE.md`
- **AI Collaboration**: `ai_development_docs/AI_SESSION_STARTER.md`
- **Changelog**: `development_docs/CHANGELOG_DETAIL.md`

## Documentation Categories

### Human-Facing Documents
- **`README.md`**: High-level project introduction and navigation.
- **`HOW_TO_RUN.md`**: Environment setup, running services, troubleshooting.
- **`DEVELOPMENT_WORKFLOW.md`**: Safe development workflow with detailed explanations.
- **`ARCHITECTURE.md`**: System design, modules, and data flow descriptions.

### AI-Facing Documents
- **`ai_development_docs/AI_SESSION_STARTER.md`**: Essential constraints for new AI sessions.
- **`ai_development_docs/AI_REFERENCE.md`**: Troubleshooting, rules, and escalation paths for AI collaborators.
- **`ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`**: Condensed workflow guidance.
- **`ai_development_docs/AI_ARCHITECTURE.md`**: High-level architecture cues and patterns.
- **`ai_development_docs/AI_DOCUMENTATION_GUIDE.md`**: Navigation aid for the AI documentation set.
- **`ai_development_docs/AI_LOGGING_GUIDE.md`**: Fast logging patterns and troubleshooting.
- **`ai_development_docs/AI_TESTING_GUIDE.md`**: Fast testing patterns and troubleshooting.
- **`ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`**: Fast error handling patterns and recovery.

### Status and History
- **`development_docs/CHANGELOG_DETAIL.md`**: Authoritative audit trail of changes.
- **`ai_development_docs/AI_CHANGELOG.md`**: Trimmed summaries for AI context windows.
- **`TODO.md`** and **`development_docs/PLANS.md`**: Active and upcoming work items.

### Technical Reference
- **`development_docs/FUNCTION_REGISTRY_DETAIL.md`**: Documentation for functions organized by module.
- **`development_docs/MODULE_DEPENDENCIES_DETAIL.md`**: Dependency mapping and architectural coupling notes.
- **`.cursor/rules/*.mdc`**: Cursor rule files that govern AI behaviour.

## Standards and Templates

### Standard Document Structure
Maintain a consistent structure for readability and automation:
```markdown
# Document Title

> **Audience**: [Target audience]  
> **Purpose**: [What this document is for]  
> **Style**: [Tone and depth]

> **See [README.md](README.md) ...**  
> **See [AI_*](ai_development_docs/AI_*.md) ...**

## Quick Reference
[Decision tree or navigation aids]

## Main Sections
[Detailed, well-structured content]
```

### Cursor Command Documentation Standards
- **Audience**: Commands describe what the AI should do, not raw shell scripts.
- **PowerShell Native**: Use parameterised PowerShell with `$LASTEXITCODE` checks.
- **Structured Output**: Define required report sections so responses are consistent.
- **Action-Oriented**: Break steps into ordered lists the AI can follow without guesswork.
- **Critical Files Lists**: Specify the exact files to read, especially for audits or reviews.

### Coding and Naming References
- **Helper functions** follow `_main_function__helper_name` pattern for traceability.
- **Implementation modules** should expose clear public APIs instead of wrappers.
- **Documentation** should refer to the canonical module or function name that appears in code.

## Audience-Specific Optimization

### Human-Facing Documents
- Provide context before instructions so newer developers understand the "why".
- Include full examples, code snippets, and expected outcomes.
- Use encouraging language and highlight safety precautions.
- Cross-reference related guides to reduce guesswork.

### AI-Facing Documents
- Keep entries concise and pattern-focused.
- Provide decision trees and checklists instead of long narratives.
- Link back to the human documents for complete explanations.
- Avoid duplicating the same detail across multiple AI files to preserve context space.

## Maintenance Guidelines

### Paired Documentation
- Update human and AI counterparts together: `DEVELOPMENT_WORKFLOW.md` <-> `AI_DEVELOPMENT_WORKFLOW.md`, `ARCHITECTURE.md` <-> `AI_ARCHITECTURE.md`, `DOCUMENTATION_GUIDE.md` <-> `AI_DOCUMENTATION_GUIDE.md`, `development_docs/CHANGELOG_DETAIL.md` <-> `AI_CHANGELOG.md`, `logs/LOGGING_GUIDE.md` <-> `AI_LOGGING_GUIDE.md`, `tests/TESTING_GUIDE.md` <-> `AI_TESTING_GUIDE.md`, `core/ERROR_HANDLING_GUIDE.md` <-> `AI_ERROR_HANDLING_GUIDE.md`.
- Keep the section order identical between paired files for predictable navigation.

### Updating AI Documentation
- Summarise only what is critical for decision-making.
- Replace large explanations with links to the human counterpart.
- Remove redundant sections when the information already exists in another AI document.

### Updating Human Documentation
- Add context, examples, and rationale to support less experienced developers.
- Maintain a supportive tone and include troubleshooting tips.
- Ensure cross-references point to the newest sources of truth.

### Adding New Documentation
- Identify the primary audience first.
- Follow the structure and tone guidelines for that audience.
- Add the new file to this guide and, if needed, create its paired document.
- Review automated tools (audits, generators) to determine whether they should track the new file.

## Generated Documentation Standards

### Identification Requirements
Every generated file must open with:
```markdown
> **Generated**: This file is auto-generated by [TOOL_NAME]. Do not edit manually.
> **Generated by**: [TOOL_NAME] - [DESCRIPTION]
> **Last Generated**: [TIMESTAMP]
> **Source**: [SOURCE FILES OR COMMANDS]
```

### Maintenance Rules
- Regenerate files by running the tool-never edit generated content manually.
- Update tool metadata whenever the generator changes behaviour.
- Archive prior outputs when trimming or rotating files to keep history auditable.

### Known Generated Files
- `ai_development_tools/AI_STATUS.md`
- `ai_development_tools/AI_PRIORITIES.md`
- `development_docs/DIRECTORY_TREE.md`
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
- `development_docs/LEGACY_REFERENCE_REPORT.md`
- `development_docs/UNUSED_IMPORTS_REPORT.md`
- `ai_development_docs/AI_FUNCTION_REGISTRY.md`
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md`

## Resources

- `.cursor/rules/` for AI collaboration policies.
- `ai_development_tools/README.md` for automation entry points.
- Prior changelog entries for historical context and lessons learned.
- Team knowledge base or meeting notes for decisions not yet documented elsewhere.
