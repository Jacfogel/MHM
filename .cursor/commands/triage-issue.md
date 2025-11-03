# Triage an Issue

## Overview
Investigate failures methodically before proposing fixes.

## Steps
1. Capture symptoms (logs, stack traces, commands, recent changes).
2. Run a fast audit if metrics are stale:
   ```powershell
   python -m ai_development_tools.ai_tools_runner audit
   ```
3. Consult `ai_development_docs/AI_REFERENCE.md` for likely causes.
4. Develop hypotheses with evidence and outline verification steps.
5. Propose a minimal fix plan that matches the "no unnecessary legacy" rule.

## Response Template
- Issue Summary: ...
- Evidence Collected: ...
- Hypotheses: ...
- Diagnostics Planned: ...
- Recommended Fix Plan: ...
- Risks / Follow-up: ...
