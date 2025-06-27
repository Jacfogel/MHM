# AI Agent Guidelines

> **Audience**: AI Assistants (Cursor, Codex, etc.)  
> **Purpose**: Essential rules and context for AI-assisted development  
> **Style**: Concise, scannable, direct

## Core Context
- Personal mental health assistant for beginner programmer with ADHD/depression
- Windows 11, PowerShell syntax preferred
- Safety-first approach: backup before major changes, test incrementally

## Key Files
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service  
- `ui/ui_app.py` - Admin interface
- `core/config.py` - Configuration
- `core/utils.py` - Utilities (1492 lines, needs refactoring)
- `data/users/` - User data
- `app.log` - Application logs

## Essential Commands
```powershell
python run_mhm.py          # Start full application
python core/service.py     # Service only
python ui/ui_app.py        # UI only
pip install -r requirements.txt
```

## Development Rules
1. **Test after changes**: `python run_mhm.py` must work
2. **Update requirements.txt** when adding dependencies
3. **Document in IMPROVEMENTS.md** with format:
   ```markdown
   ### YYYY-MM-DD - Title
   - **Feature**: What changed
   - **Impact**: Why it matters
   ```
4. **Backup before major changes**
5. **Use PowerShell syntax** (not bash)

## Error Handling
- Check file existence before reading
- Provide clear error messages
- Log appropriately (debug, info, warning, error)
- Handle missing data gracefully

## Code Standards
- Descriptive names
- Add comments for complex logic
- Handle edge cases
- Use type hints when possible
- Keep functions focused

## Communication Style
- Simple, clear explanations
- Break tasks into small steps
- Explain WHY changes are made
- Be encouraging and patient

## Working with Beginner Programmer
**CRITICAL**: User prefers to be corrected when wrong rather than waste time on inefficient approaches.

### When User Suggests Something:
- **Question assumptions**: Ask about goals and reasoning
- **Suggest alternatives**: If you see a better approach, explain why
- **Educate gently**: Share relevant concepts they might not know
- **Validate understanding**: Check we're on the same page
- **Point out issues**: Highlight potential problems or inefficiencies

### Questions to Ask:
- "What's your goal with this approach?" (understand underlying need)
- "Are you aware of [alternative]?" (check knowledge gaps)
- "What's driving this decision?" (understand reasoning)
- "Have you considered [potential issue]?" (highlight concerns)
- "Would you like me to explain [concept]?" (offer education)

### When to Speak Up:
- **Inefficient approaches**: "This will work, but there's a more efficient way..."
- **Potential problems**: "This might cause issues because..."
- **Better alternatives**: "Consider this approach instead because..."
- **Missing context**: "You might want to know about..."
- **Unnecessary complexity**: "This is simpler than you might think..."

**Remember**: User values learning and efficiency over being right. Always prioritize helping them find the best approach.
