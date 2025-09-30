# Triage an Issue

## Overview
Investigate a failure or unexpected behaviour methodically before proposing fixes.

## Steps
1. Gather symptoms: logs, stack traces, failing commands, and recent changes.
2. Run a fast audit to capture current metrics.
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red }
   ```
3. Cross-reference troubleshooting guidance in `ai_development_docs/AI_REFERENCE.md`.
4. Identify the most likely root causes, list evidence, and outline verification steps.
5. Suggest a minimal, end-to-end plan that respects the no-legacy preference.

## Response Template
- Issue Summary: ...
- Observed Evidence: ...
- Working Hypotheses: ...
- Immediate Tests or Diagnostics: ...
- Recommended Fix Plan: ...
- Risks / Follow-up: ...
