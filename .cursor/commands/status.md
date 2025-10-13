# Get Quick System Status

## Overview
Obtain a concise snapshot of the project state before starting new work or after changes.

## Steps
1. Run the status command.
   ```powershell
   python ai_development_tools/ai_tools_runner.py status
   if ($LASTEXITCODE -ne 0) { Write-Host "Status check failed" -ForegroundColor Red }
   ```
2. If findings look unusual, follow up with a fast audit:
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red }
   ```
3. Review `ai_development_tools/AI_STATUS.md` and `ai_development_tools/AI_PRIORITIES.md` for the latest context.

## Response Template
#### System Status
- Overall Health: ...
- Recent Activity: ...
- Critical Issues: ...
- Unused Imports: ...

#### Immediate Actions
1. ...
2. ...
3. ...

#### Notes
- Startup Test: ...
- Additional Comments: ...
