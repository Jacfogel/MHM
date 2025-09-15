# AI Documentation Guide - Quick Reference

> **Purpose**: Essential documentation navigation for AI collaborators  
> **For details**: See [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md)

## 🚀 Document Selection

### **Quick Decision Tree**
1. **New to project?** → `../README.md`
2. **Setting up?** → `../HOW_TO_RUN.md`
3. **Developing?** → `../DEVELOPMENT_WORKFLOW.md`
4. **Need commands?** → `../QUICK_REFERENCE.md`
5. **Understanding system?** → `../ARCHITECTURE.md`
6. **AI collaboration?** → `AI_*` files
7. **Current status?** → `AI_CHANGELOG.md`, `../TODO.md`

### **Document Categories**
- **Human-Facing**: `../README.md`, `../DEVELOPMENT_WORKFLOW.md`, `../ARCHITECTURE.md`
- **AI-Facing**: `AI_*` files, `.cursor/rules/`
- **Status/History**: `CHANGELOG_*.md`, `../TODO.md`, `development_docs/PLANS.md`

## 📋 AI Documentation

### **Core AI Files**
- **`AI_SESSION_STARTER.md`** - Essential context for new sessions
- **`AI_REFERENCE.md`** - Troubleshooting and system understanding
- **`AI_CHANGELOG.md`** - Brief summaries for AI context
- **`AI_DEVELOPMENT_WORKFLOW.md`** - Development patterns
- **`AI_ARCHITECTURE.md`** - Architectural patterns
- **`AI_DOCUMENTATION_GUIDE.md`** - Documentation navigation

### **AI Rules**
- **`.cursor/rules/audit.mdc`** - Audit rules
- **`.cursor/rules/context.mdc`** - Context rules
- **`.cursor/rules/critical.mdc`** - Critical rules

## 🔄 Maintenance

### **Paired Document Updates**
**CRITICAL**: When updating human-facing documents, check AI-facing counterparts:
- **../DEVELOPMENT_WORKFLOW.md** ↔ **AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **AI_ARCHITECTURE.md**
- **../DOCUMENTATION_GUIDE.md** ↔ **AI_DOCUMENTATION_GUIDE.md**
- **development_docs/CHANGELOG_DETAIL.md** ↔ **AI_CHANGELOG.md**

## 🎯 AI Standards
- **Concise**: Essential information only
- **Scannable**: Clear headers and bullet points
- **Pattern-focused**: Decision trees and common scenarios
- **Cross-referenced**: Clear links to detailed docs

## 🏗️ Coding Standards

### **Helper Function Naming Convention**
- **Pattern**: `_main_function__helper_name`
- **Purpose**: Improve traceability and searchability
- **Examples**: 
  - `_handle_list_tasks__format_due_date()`
  - `_handle_create_task__parse_relative_date()`
- **Benefits**: Clear ownership, easy search, better debugging

### **Function Types**
- **Implementation Functions**: Core API (`create_task`, `get_user_data`) - standard snake_case
- **Helper Functions**: Internal support (`_main_function__helper_name`) - double underscore pattern
- **Main Functions**: Public interface (`_handle_list_tasks()`) - standard snake_case

### **When to Use Each**
- **Implementation**: Core functionality used across modules
- **Helper**: Break down complexity within main functions
- **Main**: Public interfaces and orchestration

---

**Remember**: Keep AI documentation concise, pattern-focused, always cross-referenced.

---

## What's In The Full Doc
- See `../DOCUMENTATION_GUIDE.md` for the full document map: quick reference, documentation summary table, maintenance guidelines, standards, and coding/naming conventions, plus links to all human‑facing and AI‑facing documents.
