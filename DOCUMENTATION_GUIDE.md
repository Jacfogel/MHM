# Documentation Guide

> **Audience**: Developers and contributors  
> **Purpose**: Documentation organization, standards, and maintenance  
> **Style**: Reference, organizational, comprehensive

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_DOCUMENTATION_GUIDE.md](AI_DOCUMENTATION_GUIDE.md) for AI-optimized quick reference**

## 🚀 Quick Reference

### **Document Selection Decision Tree**
1. **New to project?** → `README.md`
2. **Setting up?** → `HOW_TO_RUN.md`
3. **Developing?** → `DEVELOPMENT_WORKFLOW.md`
4. **Need commands?** → `QUICK_REFERENCE.md`
5. **Understanding system?** → `ARCHITECTURE.md`
6. **AI collaboration?** → `AI_*` files
7. **Current status?** → `AI_CHANGELOG.md`, `TODO.md`
8. **Complete history?** → `CHANGELOG_DETAIL.md`

### **Documentation Categories**
- **Human-Facing**: `README.md`, `DEVELOPMENT_WORKFLOW.md`, `ARCHITECTURE.md`
- **AI-Facing**: `AI_*` files, `.cursor/rules/`
- **Status/History**: `CHANGELOG_*.md`, `TODO.md`, `PLANS.md`
- **Technical Reference**: `FUNCTION_REGISTRY_*.md`, `MODULE_DEPENDENCIES_*.md`

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
| **PLANS.md** | Human developer and AI collaborators | Development plans and strategies | Actionable, checklist-focused, progress-tracked |
| **FUNCTION_REGISTRY_DETAIL.md** | Human developer and AI collaborators | Complete function documentation | Comprehensive, detailed, reference-oriented |
| **MODULE_DEPENDENCIES_DETAIL.md** | Human developer and AI collaborators | Complete module dependency map | Comprehensive, detailed, reference-oriented |

## 📋 Documentation Categories

### 🤖 AI-Focused Documentation
*Intended for AI assistants (Cursor, Codex, etc.)*

#### Core AI Guidelines
- **`AI_SESSION_STARTER.md`** - Essential context for new AI sessions
- **`AI_REFERENCE.md`** - Troubleshooting and system understanding
- **`AI_CHANGELOG.md`** - Brief summaries for AI context
- **`AI_DEVELOPMENT_WORKFLOW.md`** - AI-optimized development patterns
- **`AI_ARCHITECTURE.md`** - AI-optimized architectural patterns
- **`AI_DOCUMENTATION_GUIDE.md`** - AI-optimized documentation navigation
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
- **`CHANGELOG_DETAIL.md`** - Complete detailed changelog history
- **`TODO.md`** - Current development priorities
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

### **Paired Document Maintenance**
**CRITICAL**: When updating any human-facing document, check if corresponding AI-facing document needs updates:

- **DEVELOPMENT_WORKFLOW.md** ↔ **AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **AI_ARCHITECTURE.md**
- **DOCUMENTATION_GUIDE.md** ↔ **AI_DOCUMENTATION_GUIDE.md**
- **CHANGELOG_DETAIL.md** ↔ **AI_CHANGELOG.md**

### When Updating AI Documentation:
- Keep it concise and focused
- Update both AI docs and relevant Cursor rules
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
- **Check if paired document is needed**

## 🎯 Quick Reference

### For AI Assistants:
- Start with `AI_SESSION_STARTER.md` for core rules
- Check `AI_REFERENCE.md` for troubleshooting
- Use `AI_DEVELOPMENT_WORKFLOW.md` for development patterns
- Use `AI_ARCHITECTURE.md` for architectural patterns
- Use `AI_DOCUMENTATION_GUIDE.md` for documentation navigation
- Check `.cursor/rules/` for specific guidelines
- Keep responses concise and focused
- **ALWAYS** use Audit-First Protocol for documentation

### For Human Developer:
- Start with `README.md` for overview
- Use `DEVELOPMENT_WORKFLOW.md` for safe practices
- Reference `QUICK_REFERENCE.md` for common tasks
- Check `ARCHITECTURE.md` for system understanding

Remember: The goal is to make collaboration between human and AI as efficient and effective as possible! 