# Code Review Checklist


> **File**: `.cursor/commands/review.md`
## Overview
Provide a focused review that surfaces blocking issues first. Use this for PRs, targeted module audits, or process reviews.

## Steps
1. Clarify the review scope (PR diff, module, or process) and desired outcome.
2. Evaluate implementation for correctness, clarity, security, and consistency.
3. Confirm tests/documentation are updated; reference relevant guides and run targeted tests when needed.
4. Highlight blockers vs. non-blockers clearly and point to supporting evidence (files, line numbers, logs).

## Response Template
#### Review Summary
- Approval: Yes/No (state blockers first)
- Key Risks: ...
- Testing Evidence: ...
- Documentation Updates: ...

#### Findings
1. [Severity] File:Line -> Issue & recommendation
2. ...

#### Suggested Improvements
- ...
