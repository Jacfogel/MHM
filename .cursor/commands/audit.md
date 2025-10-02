# Run Comprehensive System Audit

## Overview
Execute the audit toolchain to capture current health metrics before making significant changes.

## Steps
1. Run the fast audit (skips coverage by default).
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red; exit 1 }
   ```
2. If you need coverage data, rerun with the full option.
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit --full
   if ($LASTEXITCODE -ne 0) { Write-Host "Full audit failed" -ForegroundColor Red }
   ```
3. Review the generated outputs:
   - `ai_development_tools/AI_STATUS.md`
   - `ai_development_tools/AI_PRIORITIES.md`
   - `ai_development_tools/consolidated_report.txt`
   - `ai_development_tools/ai_audit_detailed_results.json`
   - `development_docs/LEGACY_REFERENCE_REPORT.md` (if regenerated)

Use the detailed report for evidence and rely on the summary files for quick context. Cross-check any concerns with `ai_development_docs/AI_REFERENCE.md` when diagnosing issues.

**Note**: Documentation coverage metrics now use production context exclusions for accurate percentages (typically 90-95% range).

## Response Template
Use this structure when reporting audit results:

#### System Overview
- Total Functions: ...
- Complexity Distribution: ...
- Documentation Coverage: ...
- System Health: ...

#### Critical Issues
- ...

#### Key Metrics
- Function Complexity: ...
- Test Coverage: ...
- Error Handling Coverage: ...
- Legacy References: ...
- Documentation Sync: ...

#### Immediate Action Items
1. ...
2. ...
3. ...

#### Next Steps
- ...
