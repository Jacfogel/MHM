# Documentation Guide

> **Audience**: Developers and contributors  
> **Purpose**: Documentation organization, standards, and maintenance  
> **Style**: Reference, organizational, comprehensive

This guide defines the audience and purpose of each documentation file in the MHM project.

## 📊 Documentation Summary Table

| File | Audience | Purpose | Style |
|------|----------|---------|-------|
| **README.md** | New users & developers | Project overview and features | Comprehensive, beginner-friendly |
| **HOW_TO_RUN.md** | New users & developers | Setup and installation | Step-by-step, troubleshooting-focused |
| **DEVELOPMENT_WORKFLOW.md** | Developers & contributors | Safe development practices | Comprehensive, step-by-step, supportive |
| **QUICK_REFERENCE.md** | Developers & contributors | Essential commands and troubleshooting | Concise, scannable, action-oriented |
| **ARCHITECTURE.md** | Developers & contributors | System design and components | Technical, detailed, reference-oriented |
| **AI_CHANGELOG.md** | AI collaborators & developers | Brief summaries of recent changes for AI context | Concise, action-oriented, scannable |
| **CHANGELOG_DETAIL.md** | Developers & contributors | Complete detailed changelog history | Chronological, detailed, reference-oriented |
| **TODO.md** | Developers & contributors | Current priorities and planned work | Organized, actionable, beginner-friendly |
| **DOCUMENTATION_GUIDE.md** | Developers & contributors | Documentation organization and standards | Reference, organizational, comprehensive |
| **PLANS.md** | Human developer and AI collaborators | Development plans and strategies | Actionable, checklist-focused, progress-tracked |
| **FUNCTION_REGISTRY_DETAIL.md** | Human developer and AI collaborators | Complete function documentation | Comprehensive, detailed, reference-oriented |
| **MODULE_DEPENDENCIES_DETAIL.md** | Human developer and AI collaborators | Complete module dependency map | Comprehensive, detailed, reference-oriented |

> **See [README.md](README.md) for complete navigation and project overview**

## 📋 Documentation Categories

### 🤖 AI-Focused Documentation
*Intended for AI assistants (Cursor, Codex, etc.)*

#### Core AI Guidelines
- **`AI_SESSION_STARTER.md`** - Essential context for new AI sessions
- **`AI_REFERENCE.md`** - Troubleshooting and system understanding
- **`AI_CHANGELOG.md`** - Brief summaries for AI context
- **`PLANS.md`** - Development plans, testing status, and UI migration patterns
- **`AI_FUNCTION_REGISTRY.md`** - Function patterns and documentation status
- **`AI_MODULE_DEPENDENCIES.md`** - Module dependency patterns and status
- **`.cursor/rules/`** - Cursor-specific rules and guidelines

#### AI-Specific Rules
- **`.cursor/rules/audit.mdc`** - Audit rules for documentation and analysis
- **`.cursor/rules/context.mdc`** - Context rules for development work
- **`.cursor/rules/critical.mdc`** - Critical rules for development work

### 👤 User-Focused Documentation
*Intended for the human developer (you)*

#### Getting Started
- **`README.md`** - Project overview and features
- **`HOW_TO_RUN.md`** - Setup and installation instructions

#### Development Guides
- **`DEVELOPMENT_WORKFLOW.md`** - Safe development practices for beginners
- **`QUICK_REFERENCE.md`** - Essential commands and troubleshooting
- **`PLANS.md`** - Development plans, UI migration, and testing strategies

#### Technical Reference
- **`ARCHITECTURE.md`** - System structure and data organization
- **`AI_CHANGELOG.md`** - Brief summaries for AI context
- **`CHANGELOG_DETAIL.md`** - Complete detailed changelog history
- **`TODO.md`** - Current development priorities
- **`PLANS.md`** - Development plans, testing strategy, and UI migration details
- **`FUNCTION_REGISTRY_DETAIL.md`** - Complete function documentation
- **`MODULE_DEPENDENCIES_DETAIL.md`** - Complete module dependency map

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
- Update both `AI_RULES.md` and relevant Cursor rules
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

## 🔍 Audit-First Protocol

### What It Is
The Audit-First Protocol is a mandatory system that ensures all documentation and analysis is based on actual data, not assumptions. Before creating any significant documentation, AI assistants must run audit tools to get accurate information.

### How It Works
1. **Run Audit Tools**: Execute `python ai_tools/ai_tools_runner.py audit` to get comprehensive system data
2. **Show Results**: Display audit statistics and findings to the user
3. **Get Approval**: Ask for user approval before proceeding with documentation
4. **Use Real Data**: Base all documentation on actual audit results, not assumptions

### Available Audit Tools
- **`function_discovery.py`** - Find all functions in the codebase
- **`decision_support.py`** - Analyze code complexity and identify issues
- **`audit_function_registry.py`** - Check function documentation completeness
- **`audit_module_dependencies.py`** - Map module dependencies
- **`analyze_documentation.py`** - Analyze documentation coverage and redundancy

### When to Use
- Before creating any new documentation
- Before updating existing documentation significantly
- When user asks for "complete" or "comprehensive" information
- When accuracy and completeness are critical
- When user expresses concern about trust or reliability

## 🎯 Quick Reference

### For AI Assistants:
- Start with `AI_RULES.md` for core rules
- Check `AI_CONTEXT.md` for project context
- Review `AI_ORIENTATION.md` for collaboration guidelines
- Use `AI_QUICK_REFERENCE.md` for quick commands
- Check `.cursor/rules/` for specific guidelines
- Keep responses concise and focused
- **ALWAYS** use Audit-First Protocol for documentation

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