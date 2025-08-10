# TODO.md - MHM Project Tasks

> **Audience**: Human Developer (Beginner Programmer)  and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TESTING_IMPROVEMENT_PLAN_DETAIL.md](TESTING_IMPROVEMENT_PLAN_DETAIL.md) for testing strategy**

## 📝 How to Add New TODOs

When adding new tasks, follow this format:

```markdown
**Task Title** - Brief description
- *What it means*: Simple explanation of the task
- *Why it helps*: Clear benefit or improvement
- *Estimated effort*: Small/Medium/Large
```

**Guidelines:**
- Use **bold** for task titles
- Group tasks by priority (High/Medium/Low sections)
- Use clear, action-oriented titles
- Include estimated effort to help with planning
- Add status indicators (⚠️ **IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md

## High Priority

**App Log Inactivity Investigation** - `logs/app.log` not receiving expected entries
- *What it means*: Diagnose why `app.log` is empty or sparse and restore expected application logging
- *Why it helps*: Ensures central visibility for non-component events and simplifies troubleshooting
- *Estimated effort*: Small
- Subtasks:
  - [ ] Verify logger configuration (paths/handlers) in `core/logger.py` and `core/config.py` points to `logs/app.log`
  - [ ] Check handler attachment/propagation for root and component loggers; confirm `app` logger exists
  - [ ] Emit a simple startup log from `run_mhm.py`/service to confirm handler wiring
  - [ ] Ensure component logs still write to their own files while general app events go to `app.log`
  - [ ] Add a behavior test asserting a known startup line appears in `logs/app.log` under test mode

**Channel-Agnostic Command Registry Follow-ups**
- *What it means*: Finalize and monitor the new centralized command system and Discord integrations
- *Why it helps*: Ensures consistent behavior across channels and prevents regressions
- *Estimated effort*: Small/Medium
- Subtasks:
  - [ ] Add behavior tests for dynamic Discord app commands (registration, sync, callback wiring)
  - [ ] Add behavior tests for classic dynamic commands (skip `help`, ensure mapping works)
  - [ ] Verify unknown `/` and `!` prefixes fall back to parser and contextual chat
  - [ ] Document command list in QUICK_REFERENCE.md

**Legacy Code Removal** - Remove all marked legacy/compatibility code with clear marking and plans
- *What it means*: Remove legacy compatibility code per `LEGACY_CODE_REMOVAL_PLAN.md` (keep warnings in place until removal)
- *Why it helps*: Reduces complexity, eliminates legacy branches, improves maintainability
- *Estimated effort*: Medium
- *High-priority removals*:
  - Account Creator Dialog compatibility methods (by 2025-08-15)
  - User Profile Settings Widget legacy fallbacks (by 2025-08-15)
  - Discord Bot legacy methods (by 2025-08-15)

**Throttler Bug Fix** - Fix Service Utilities Throttler first-call behavior
- *What it means*: Ensure `last_run` is set on first call so throttling works from initial invocation
- *Why it helps*: Prevents over-frequency operations on first execution
- *Estimated effort*: Small

**Schedule Editor Validation – Prevent Dialog Closure**
- *What it means*: Validation error popups must not close the edit schedule dialog; allow user to fix and retry
- *Why it helps*: Prevents data loss and improves UX
- *Estimated effort*: Small
- *Status*: ⚠️ **OUTSTANDING** - Previous fix attempt may not have fully resolved the issue

**Check-in Flow Behavior & Stability**
- *What it means*: Ensure active check-ins expire correctly and legacy shims are not used in live flows
- *Why it helps*: Prevents stale states and confusing interactions during conversations
- *Estimated effort*: Small/Medium
- Subtasks:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [ ] Consider inactivity-based expiration (30–60 minutes) in addition to outbound-triggered expiry (optional)

## Medium Priority

**Review and Update ARCHITECTURE.md** - Check for outdated information
- *What it means*: Ensure architecture documentation reflects current system state
- *Why it helps*: Provides accurate technical reference for development
- *Estimated effort*: Small

**Review and Update QUICK_REFERENCE.md** - Check for outdated commands
- *What it means*: Ensure quick reference contains current commands and procedures
- *Why it helps*: Provides reliable quick access to common tasks
- *Estimated effort*: Small
- Subtasks:
  - [ ] Reflect new slash/bang commands and central command list
  - [ ] Note that `/checkin` is a flow; others are single-turn for now

### User Experience Improvements

**Enhanced Error Messages**
- *What it means*: Provide clearer, actionable dialog and system error messages everywhere users interact
- *Why it helps*: Reduces confusion and guides users to resolve problems faster
- *Estimated effort*: Small

**Improve Natural Language Processing Accuracy**
- *What it means*: Refine parsing patterns and thresholds to better recognize intents and entities
- *Why it helps*: More reliable command understanding and fewer misinterpretations
- *Estimated effort*: Medium

**Conversation Flow Management**
- *What it means*: Improve conversational state transitions and fallbacks to keep interactions smooth
- *Why it helps*: More predictable user experience and fewer dead-ends
- *Estimated effort*: Medium

### Performance Optimizations

**Optimize AI Response Times**
- *What it means*: Reduce latency for AI-backed responses via batching, caching, or configuration tuning
- *Why it helps*: Snappier interactions and better UX
- *Estimated effort*: Medium

**Improve Message Processing Efficiency**
- *What it means*: Profile and streamline message pipelines (I/O, parsing, scheduling)
- *Why it helps*: Lower CPU usage and faster processing
- *Estimated effort*: Medium

**Reduce Memory Usage**
- *What it means*: Identify hotspots (caches, data copies) and right-size buffers/limits
- *Why it helps*: Improves stability on constrained systems
- *Estimated effort*: Medium

## Low Priority

### Documentation

**Update User Guides**
- *What it means*: Refresh user-facing guides to reflect current features and workflows
- *Why it helps*: Reduces confusion and accelerates onboarding
- *Estimated effort*: Small

**Improve Code Documentation**
- *What it means*: Add/refresh docstrings and inline docs where clarity is lacking
- *Why it helps*: Speeds up development and AI assistance accuracy
- *Estimated effort*: Small

**Create Troubleshooting Guides**
- *What it means*: Document common issues and resolution steps for channels, UI, and data
- *Why it helps*: Faster recovery when issues occur
- *Estimated effort*: Small

### Testing

**Add More Comprehensive Tests**
- *What it means*: Expand behavior and integration coverage for under-tested modules
- *Why it helps*: Increases reliability and change safety
- *Estimated effort*: Large

**Improve Test Coverage**
- *What it means*: Systematically raise coverage by adding targeted unit tests
- *Why it helps*: Catches regressions earlier
- *Estimated effort*: Medium

**Add Integration Tests**
- *What it means*: Add cross-module workflow tests (user lifecycle, scheduling, messaging)
- *Why it helps*: Verifies real-world flows function correctly
- *Estimated effort*: Medium
- Subtasks:
  - [ ] End-to-end tests for `/checkin` flow via Discord and via plain text
  - [ ] End-to-end tests for `/status`, `/profile`, `/tasks` via Discord slash commands

**Scripts Directory Cleanup** - Clean up the scripts/ directory
- *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to ai_tools/
- *Why it helps*: Reduces confusion and keeps the codebase organized
- *Estimated effort*: Medium

**Gitignore Cleanup** - Review and clean up .gitignore file
- *What it means*: Remove outdated entries, add missing patterns, organize sections logically
- *Why it helps*: Ensures proper version control and prevents unnecessary files from being tracked
- *Estimated effort*: Small

**Improve AI Terminal Interaction Reliability** - Address issues with AI misunderstanding terminal output
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Fix Treeview Refresh** - Should refresh reflecting the changes, while maintaining current sorting
- *What it means*: Improve the message editing interface to automatically update the display when messages are changed
- *Why it helps*: Better user experience with immediate visual feedback
- *Estimated effort*: Small

**Fix "process already stopped" notification issue**
- *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
- *Why it helps*: Cleaner service management and better user experience
- *Estimated effort*: Small

**Add Performance Monitoring** - Track how long operations take
- *What it means*: The app keeps track of which operations are slow so you can improve them
- *Why it helps*: Helps you identify and fix performance problems before they become annoying
- *Estimated effort*: Medium

**Create Development Guidelines** - Establish coding standards and best practices
- *What it means*: Write down rules for how code should be written to keep it consistent
- *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance
- *Estimated effort*: Small
