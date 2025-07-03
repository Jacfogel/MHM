# AI Agent Guidelines

> **Audience**: AI Assistants (Cursor, Codex, etc.)  
> **Purpose**: Essential rules and context for AI-assisted development  
> **Style**: Concise, scannable, direct

## Core Context
- Personal mental health assistant for beginner programmer with ADHD/depression
- Windows 11, PowerShell syntax preferred
- Safety-first approach: backup before major changes, test incrementally

## Project Vision
- **Communication-First Design**: All user interactions happen through communication channels (Discord, email, etc.)
- **AI-Powered Interface**: Users interact primarily through AI chatbot with optional menu systems
- **No Required User UI**: Admin interface exists for management, but users never need a separate UI
- **Channel-Agnostic Architecture**: Features work across all communication channels with minimal channel-specific code

## Key Files
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service  
- `ui/ui_app.py` - Admin interface (admin only, not for users)
- `core/config.py` - Configuration
- `core/file_operations.py`, `core/user_management.py`, `core/message_management.py`, `core/schedule_management.py`, `core/response_tracking.py`, `core/service_utilities.py`, `core/validation.py` - Utilities (formerly in utils.py, now refactored for clarity and maintainability)
- `bot/` - Communication channel implementations
- `data/users/` - User data

## Rule Organization

### High Priority Rules (Always Applied)
- **`core-guidelines.mdc`** - Core development rules, user context, and communication guidelines
- **`about-me.mdc`** - Personal background and project purpose

### Medium Priority Rules (Auto Attached)
- **`development-tasks.mdc`** - Task workflows and PowerShell operations
  - **File pattern**: `*.py`, `*.md`, `*.txt`
- **`code-quality.mdc`** - Code patterns and AI optimization
  - **File pattern**: `*.py`
- **`organization.mdc`** - Documentation and script organization
  - **File pattern**: `*.md`

## Development Workflow
1. **Test current state**: `python run_mhm.py`
2. **Create backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
3. **Make incremental changes**
4. **Test after each change**
5. **Update documentation**: `CHANGELOG.md`

## Error Handling
- Check file existence before reading
- Clear error messages
- Handle missing data gracefully
- Log appropriately
- Always verify command success with exit codes

## Communication
- Simple explanations
- Break tasks into steps
- Explain WHY changes are made
- Be patient and encouraging
- Question assumptions and suggest better alternatives

## Beginner Programmer Support
**CRITICAL**: User prefers correction over inefficient approaches.

- Question assumptions and goals
- Suggest better alternatives
- Educate about relevant concepts
- Point out potential issues
- Ask clarifying questions when unsure

**Remember**: User values learning and efficiency. Always help find the best approach.