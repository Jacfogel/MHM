# Task System Improvements Plan

> **File**: `development_docs/TASKS_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Plan for multi-phase task system enhancements (recurrence, templates, intelligence, and advanced workflows)  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-02-28 (User-priority Q&A: Discord primary, templates/follow-up/notes prioritize, Smart Suggestions defer)  
> **Parent**: [PLANS.md](development_docs/PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

**Use / fit**: Discord is the primary task interface; user doesn't use tasks much yet but wants them to work well. Discord commands and natural-language task creation are extremely important. Prioritize: recurring-task discoverability, templates, interactive follow-up with skip/flow-timeout, notes & attachments. Defer AI-based suggestions until AI overhaul.

---
### Canonical Task Data Model Migration

**Migrate tasks to canonical v2 task structure**
- *What it means*: Convert existing active and completed task records to the new task structure.
- *Why it helps*: Makes tasks consistent with notes, journal entries, and future events while preparing for SQLite.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Target structure*:
  - [ ] `id`
  - [ ] `short_id`
  - [ ] `kind`
  - [ ] `title`
  - [ ] `description`
  - [ ] `category`
  - [ ] `group`
  - [ ] `tags`
  - [ ] `priority`
  - [ ] `status`
  - [ ] `due`
  - [ ] `reminders`
  - [ ] `recurrence`
  - [ ] `completion`
  - [ ] `source`
  - [ ] `linked_item_ids`
  - [ ] `created_at`
  - [ ] `updated_at`
  - [ ] `archived_at`
  - [ ] `deleted_at`
  - [ ] `metadata`
- *Subtasks*:
  - [ ] Convert `task_id` to `id`.
  - [ ] Generate `short_id` using the no-dash `t####` style.
  - [ ] Set `kind` to `task`.
  - [ ] Preserve `title`.
  - [ ] Preserve `description`.
  - [ ] Normalize `category` as a broad user-facing category, not priority.
  - [ ] Add `group`, defaulting to empty string or a migrated value if available.
  - [ ] Add `tags`, defaulting to an empty list.
  - [ ] Normalize `priority` to allowed values such as `low`, `medium`, `high`.
  - [ ] Set `status` from task state, such as `active`, `completed`, `cancelled`, `archived`, or `deleted`.
  - [ ] Move `due_date` and `due_time` into `due.date` and `due.time`.
  - [ ] Move reminder-related fields into `reminders`.
  - [ ] Move recurrence-related fields into `recurrence`.
  - [ ] Move completion-related fields into `completion`.
  - [ ] Add `source` with best available channel/source metadata.
  - [ ] Add `linked_item_ids`, defaulting to an empty list.
  - [ ] Rename `last_updated` to `updated_at`.
  - [ ] Add `archived_at` and `deleted_at`, defaulting to null.
  - [ ] Use `metadata` only for fields that cannot be safely mapped and still need manual review.
  - [ ] Do not keep old task fields in canonical v2 records unless explicitly temporary.

**Consolidate active and completed task storage**
- *What it means*: Move toward one canonical task collection instead of separate active/completed task files.
- *Why it helps*: Completion is task state, not a separate storage type.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Decide whether the canonical v2 file is `tasks/tasks.json`.
  - [ ] Convert active and completed task records into one collection.
  - [ ] Use `status` and `completion.completed` to distinguish active vs completed tasks.
  - [ ] Stop writing new data to `active_tasks.json` and `completed_tasks.json` after migration.
  - [ ] If old files must still be readable during transition, mark that code as temporary compatibility.
  - [ ] Add a planned removal task for old active/completed task readers.
  - [ ] Add tests proving new task reads do not require the old split files after migration.

**Normalize task category, group, tags, and priority**
- *What it means*: Separate concepts that are currently partially mixed together.
- *Why it helps*: Prevents values like `high` from being treated as a category when they are really priority.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Treat `priority` as urgency/importance.
  - [ ] Treat `category` as a broad semantic category such as `health`, `home`, `family`, or `personal`.
  - [ ] Treat `group` as a user-facing organizational bucket.
  - [ ] Treat `tags` as flexible multi-label metadata.
  - [ ] Migrate old `category` values of `low`, `medium`, or `high` into `priority`.
  - [ ] Do not duplicate the same value across `category`, `group`, and `tags` unless there is a clear reason.
  - [ ] Add tests for priority-like legacy category values.

**Add task short IDs**
- *What it means*: Add mobile-friendly task IDs like `t6ca6` while preserving UUIDs as internal IDs.
- *Why it helps*: Makes Discord task commands easier to type and aligns tasks with notebook short IDs.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Implement centralized short ID generation if not already present.
  - [ ] Generate task short IDs from UUIDs.
  - [ ] Ensure no dash appears in short IDs.
  - [ ] Add lookup support by UUID and short ID.
  - [ ] Do not permanently support obsolete dashed short IDs unless real existing data requires it.
  - [ ] If dashed ID support is required temporarily, mark it as temporary compatibility with planned removal.

**Update task tests for v2 data**
- *What it means*: Update task tests to use and validate the v2 task structure.
- *Why it helps*: Makes the new structure the tested source of truth.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Update task fixtures to v2 structure.
  - [ ] Add migration tests from current active task examples.
  - [ ] Add migration tests from current completed task examples.
  - [ ] Add tests for `status`.
  - [ ] Add tests for `completion`.
  - [ ] Add tests for `due`.
  - [ ] Add tests for `reminders`.
  - [ ] Add tests for `recurrence`.
  - [ ] Remove or rewrite tests that only preserve old active/completed split behavior.

### **2025-08-25 - Comprehensive Task System Improvements** [IN PROGRESS]

**Status**: IN PROGRESS (since 2025-08-25; last updated 2026-02-28)  
**Priority**: High  
**Effort**: Large (Multi-phase implementation)  
**Dependencies**: None

**Objective**: Implement comprehensive improvements to the task management system to enhance user experience, productivity, and system intelligence.

**Background**: The current task system provides basic CRUD operations but lacks advanced features that would significantly improve user productivity and task management effectiveness. Users need recurring tasks, templates, smart suggestions, and better organization capabilities.

**Implementation Plan**:

#### **Phase 1: Foundation Improvements (High Impact, Low-Medium Effort)** **PARTIALLY COMPLETE** (since 2025-11-20)

**1. Recurring Tasks System** **COMPLETED** (prior sessions)
- **Status**: **COMPLETED** *(user has not tried; discoverability gap)*
- **Note**: Recurring tasks functionality implemented (recurrence_pattern, recurrence_interval, next_due_date, auto-creation, UI components). **Gap**: User does not know how to create or use recurring tasks via Discord; add documentation/discoverability.
- **Follow-up**: [ ] Document how to create recurring tasks via Discord; [ ] Verify Discord command/flow supports recurrence.
- **Testing**: `tests/unit/test_recurring_tasks.py` and related task tests exist; verify coverage via `pytest tests/ -k recurring` (last verified 2026-02-28)

**2. Task Templates & Quick Actions** [WARNING] **PLANNED**
- **Why it matters**: Reduces friction for common task creation patterns
- **Implementation**:
  - [ ] Pre-defined task templates (medication, exercise, appointments, chores)
  - [ ] Quick-add buttons for common tasks
  - [ ] Template categories (health, work, personal, household)
  - [ ] Custom user templates with saved preferences
  - [ ] Template management UI

**3. Smart Task Suggestions** [WARNING] **DEFERRED**
- **Use / fit**: Defer until AI overhaul. AI-powered suggestions blocked by AI overhaul.
- **Why it matters**: Helps users discover what they might need to do based on patterns
- **Implementation**:
  - [ ] AI-powered task suggestions based on time patterns
  - [ ] Suggestions based on recent task completion history
  - [ ] User goal and preference-based suggestions
  - [ ] "Suggested for you" section in task list
  - [ ] One-click task creation from suggestions

**4. Natural Language Task Creation** [WARNING] **PLANNED** — *prioritize*
- **Use / fit**: Discord commands extremely important; user adds tasks via Discord only.
- **Why it matters**: Makes task creation more intuitive and faster
- **Implementation**:
  - [ ] Natural language parsing for task creation
  - [ ] Support for "Remind me to take medication every morning at 8am"
  - [ ] Support for "I need to call the dentist this week"
  - [ ] Support for "Schedule a task for cleaning the kitchen every Sunday"
  - [ ] Smart parsing of natural language into structured task data

**4a. Interactive Task Creation Follow-up Questions** [WARNING] **PLANNED** — *prioritize*
- **Use / fit**: User wants follow-up prompts with skip buttons and flow timeouts. Generally adds details at creation or not at all.
- **Why it matters**: Allows users to provide additional task information (due date, priority, reminders) without requiring all details upfront
- **Implementation**:
  - [ ] Implement follow-up question system in conversation manager/command handler
  - [ ] After initial task creation, ask for optional information:
    - [ ] Due date (with 2-3 quick selectable options + custom input + skip)
    - [ ] Priority level (with 2-3 quick selectable options + custom input + skip)
    - [ ] Reminder preferences (with 2-3 quick selectable options + custom input + skip)
  - [ ] Provide skip option for individual questions and "skip all" option; **flow timeouts** so prompts don't hang indefinitely
  - [ ] Store task with minimal info initially, update as user provides additional details
  - [ ] Integrate with command parser to recognize task creation commands
  - [ ] Add conversation state tracking for multi-turn task creation flow
- **Dependencies**: Conversation manager enhancements, command handler improvements
- **Notes**: This is a larger feature that requires integration between AI chatbot, conversation manager, and command handlers

#### **Phase 2: Intelligence & Workflow Improvements (Medium Impact, Medium Effort)** [WARNING] **PLANNED**

**5. Task Dependencies & Prerequisites** [WARNING] **PLANNED** — *eventually quite important*
- **Use / fit**: User often has tasks that depend on others; important but can sequence after Phase 1.
- **Why it matters**: Many tasks have logical dependencies that affect completion
- **Implementation**:
  - [ ] "Blocked by" and "Blocks" relationships between tasks
  - [ ] Visual dependency chains in task list
  - [ ] Automatic unblocking when prerequisites are completed
  - [ ] Smart task ordering suggestions

**6. Context-Aware Task Reminders** [WARNING] **PLANNED** — *eventually quite important*
- **Use / fit**: Mood-aware, location-based, calendar-linked reminders eventually; time-based enough for now. Overlaps with PLANS Mood-Aware Support.
- **Why it matters**: Reminders are more effective when delivered at the right moment
- **Implementation**:
  - [ ] Location-based reminders (when near relevant places)
  - [ ] Time-based context (morning routines, evening wind-down)
  - [ ] Mood-aware suggestions (easier tasks when energy is low)
  - [ ] Integration with external calendar events

**7. Batch Task Operations** [WARNING] **PLANNED** — *later, if tasks work well*
- **Use / fit**: Not often needed yet; may want if task usage grows.
- **Why it matters**: Reduces friction when managing multiple related tasks
- **Implementation**:
  - [ ] Select multiple tasks for bulk operations
  - [ ] Batch complete, delete, or update tasks
  - [ ] Bulk priority changes
  - [ ] Mass tag assignment

**8. Task Time Tracking** [WARNING] **DEFERRED**
- **Use / fit**: Maybe eventually; completion itself enough for now.
- **Why it matters**: Helps users estimate task duration and plan their time better
- **Implementation**:
  - [ ] Start/stop timer for tasks
  - [ ] Estimated vs actual time tracking
  - [ ] Time-based task suggestions
  - [ ] Productivity insights based on time data

**9. Task Notes & Attachments** [WARNING] **PLANNED** — *prioritize*
- **Use / fit**: User would like notes and attachments (links, screenshots, docs).
- **Why it matters**: Keeps all relevant information with the task
- **Implementation**:
  - [ ] Rich text notes for tasks
  - [ ] File attachments (images, documents)
  - [ ] Voice notes for quick task capture
  - [ ] Link attachments (URLs, references)

**10. Task Difficulty & Energy Tracking** [WARNING] **PLANNED** — *eventually quite important*
- **Use / fit**: Eventually quite; overlaps with PLANS Mood-Aware Support (gentler when low, mood-appropriate actions).
- **Why it matters**: Helps users match tasks to their current energy levels
- **Implementation**:
  - [ ] Self-rated task difficulty (1-5 scale)
  - [ ] Energy level tracking when completing tasks
  - [ ] Smart task scheduling based on energy patterns
  - [ ] "Low energy mode" with easier task suggestions

#### **Phase 3: Advanced Features (Medium Impact, High Effort)** [WARNING] **FUTURE CONSIDERATION**

**Use / fit**: Phase 3 can wait. User cares about: priority escalation for overdue, task sync/backup, calendar view. Other items long-term.

**11. Priority Escalation System** [WARNING] **FUTURE CONSIDERATION** — *user cares*
- **Why it matters**: Prevents tasks from being forgotten when they become urgent
- **Implementation**:
  - [ ] Automatic priority increase for overdue tasks
  - [ ] Escalation notifications ("This task is now 3 days overdue")
  - [ ] Smart escalation timing (not too aggressive, not too passive)
  - [ ] Visual indicators for escalated tasks
  - [ ] **Note**: To be optional and configurable

**12. Enhanced Task Analytics** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users understand their patterns and improve productivity
- **Implementation**:
  - [ ] Completion rate trends over time
  - [ ] Peak productivity hours identification
  - [ ] Task category performance analysis
  - [ ] Streak tracking for recurring tasks
  - [ ] Predictive completion estimates

**13. AI Task Optimization** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users work more efficiently
- **Implementation**:
  - [ ] Task order optimization suggestions
  - [ ] Break down complex tasks into subtasks
  - [ ] Suggest task combinations for efficiency
  - [ ] Identify potential task conflicts
  - [ ] **Note**: To be optional and configurable

**14. Advanced Task Views** [WARNING] **FUTURE CONSIDERATION** — *user cares: calendar view*
- **Why it matters**: Different views help users organize and focus on what matters
- **Implementation**:
  - [ ] Calendar view (daily, weekly, monthly)
  - [ ] Kanban board view (To Do, In Progress, Done)
  - [ ] Timeline view for project-based tasks
  - [ ] Focus mode (hide completed tasks, show only today)

**15. Smart Task Grouping** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users see related tasks together
- **Implementation**:
  - [ ] Auto-grouping by location, time, or category
  - [ ] Project-based task grouping
  - [ ] Smart tags based on task content
  - [ ] Dynamic task lists based on criteria

**16. Task Sync & Backup** [WARNING] **FUTURE CONSIDERATION** — *user cares*
- **Why it matters**: Ensures tasks are never lost and accessible everywhere
- **Implementation**:
  - [ ] Cloud sync for task data
  - [ ] Automatic backups
  - [ ] Cross-device task access
  - [ ] Export/import task data

**17. Task Performance Optimization** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Faster task operations improve user experience
- **Implementation**:
  - [ ] Lazy loading for large task lists
  - [ ] Efficient task search and filtering
  - [ ] Optimized reminder scheduling
  - [ ] Background task processing

**Success Criteria**:
- Recurring tasks discoverable and usable via Discord (document how to create/use)
- Task templates reduce task creation time for common patterns
- Natural language task creation via Discord is intuitive and accurate
- Interactive follow-up has skip options and flow timeouts
- All improvements maintain backward compatibility
- System performance remains optimal

**Risk Assessment**:
- **High Impact**: Affects core task management functionality
- **Mitigation**: Incremental implementation with thorough testing
- **Rollback**: Maintain backward compatibility throughout implementation

---

**Note**: Phase 2-4 task-system items referenced elsewhere in PLANS are tracked here. Individual Task Reminders and Recurring Tasks are already completed; remaining items should be updated in this file.
