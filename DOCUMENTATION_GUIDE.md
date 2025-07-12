# Documentation Guide

This guide defines the audience and purpose of each documentation file in the MHM project.

## 📋 Documentation Categories

### 🤖 AI-Focused Documentation
*Intended for AI assistants (Cursor, Codex, etc.)*

#### Core AI Guidelines
- **`AGENTS.md`** - Essential rules and context for AI assistants
- **`.cursor/rules/`** - Cursor-specific rules and guidelines

#### AI-Specific Rules
- **`.cursor/rules/mhm-development.mdc`** - Core development rules
- **`.cursor/rules/about-me.mdc`** - User context and preferences
- **`.cursor/rules/agent-instructions.mdc`** - Basic agent instructions
- **`.cursor/rules/limit-new-md-files.mdc`** - Documentation organization rules
- **`.cursor/rules/test-and-single-use-scripts.mdc`** - Script organization rules

### 👤 User-Focused Documentation
*Intended for the human developer (you)*

#### Getting Started
- **`README.md`** - Project overview and features
- **`HOW_TO_RUN.md`** - Setup and installation instructions

#### Development Guides
- **`DEVELOPMENT_WORKFLOW.md`** - Safe development practices for beginners
- **`QUICK_REFERENCE.md`** - Essential commands and troubleshooting
- **`UI_MIGRATION_PLAN.md`** - UI migration, data migration, and backup best practices (see new section)

#### Technical Reference
- **`ARCHITECTURE.md`** - System structure and data organization
- **`CHANGELOG.md`** - Change log and recent updates (see 2025-07-10 for migration/backup best practices)
- **`TODO.md`** - Current development priorities

### 🔧 Configuration Files
*Used by both AI and human developers*

- **`requirements.txt`** - Python dependencies
- **`.env`** - Environment variables (create if needed)
- **`.gitignore`** - Git ignore patterns
- **`.gitattributes`** - Git file handling

## 📝 Documentation Standards

### AI-Focused Documentation Should:
- Be concise and scannable
- Focus on essential rules and context
- Use clear, direct language
- Avoid verbose explanations
- Be organized for quick reference

### User-Focused Documentation Should:
- Be comprehensive and beginner-friendly
- Include detailed explanations
- Provide step-by-step instructions
- Use encouraging, supportive language
- Include examples and troubleshooting

## 🔄 Maintenance Guidelines

### When Updating AI Documentation:
- Keep it concise and focused
- Update both `AGENTS.md` and relevant Cursor rules
- Test that AI assistants can understand the changes
- Remove any redundancy or duplication

### When Updating User Documentation:
- Maintain beginner-friendly language
- Include clear explanations of concepts
- Add examples where helpful
- Keep the encouraging, supportive tone

### When Adding New Documentation:
- Determine the primary audience (AI or User)
- Follow the appropriate style guidelines
- Update this guide to include the new file
- Consider if it could be consolidated with existing docs

## 🎯 Quick Reference

### For AI Assistants:
- Start with `AGENTS.md` for core rules
- Check `.cursor/rules/` for specific guidelines
- Keep responses concise and focused

### For Human Developer:
- Start with `README.md` for overview
- Use `DEVELOPMENT_WORKFLOW.md` for safe practices
- Reference `QUICK_REFERENCE.md` for common tasks
- Check `ARCHITECTURE.md` for system understanding

## 📈 Future Improvements

### Potential AI Documentation Enhancements:
- Add code examples to rules
- Create troubleshooting guides for common AI issues
- Add performance optimization guidelines
- Include testing strategies for AI-assisted development

### Potential User Documentation Enhancements:
- Add video tutorials
- Create interactive examples
- Include more visual diagrams
- Add community guidelines for contributions

Remember: The goal is to make collaboration between human and AI as efficient and effective as possible! 