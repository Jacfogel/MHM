# AI Legacy Code Removal Guide - Quick Reference

> **Purpose**: Fast patterns for safely removing legacy code using search-and-close approach  
> **For context**: See `.cursor/rules/quality-standards.mdc` and `.cursor/rules/critical.mdc` for legacy code standards

## Quick Reference

**Process:** `--find` → Update → `--verify` → Remove → Test

**Commands:**
```powershell
python ai_development_tools/legacy_reference_cleanup.py --find "LegacyItemName"
python ai_development_tools/legacy_reference_cleanup.py --verify "LegacyItemName"
python ai_development_tools/ai_tools_runner.py legacy
```

## Standards

**Adding Legacy Code:**
- Mark with `# LEGACY COMPATIBILITY:` header
- Log usage when accessed
- Document removal plan
- Add detection patterns to `legacy_reference_cleanup.py`

**Removing Legacy Code:**
- Use search-and-close (not time windows)
- Verify all references updated before removal
- Run full test suite after removal
- Update changelogs

## Process

**1. Find:** `--find "legacy_item"` (checks imports, usage, tests, docs, config)

**2. Update:**
- **Active code/config** (HIGH): Replace with modern equivalent
- **Tests** (HIGH): Update or remove if testing legacy
- **Docs** (MEDIUM): Update for clarity (archive can stay)
- **Archive** (LOW): Leave as-is

**3. Verify:** `--verify "legacy_item"` (must show "READY", zero active code/config refs)

**4. Remove & Test:**
- Remove code and `LEGACY COMPATIBILITY` markers
- Update changelogs
- Run full test suite
- Verify service starts

## Checklist

Before removal:
- [ ] `--find` shows no active code/config references
- [ ] Tests updated or removed
- [ ] `--verify` shows "READY"
- [ ] Full test suite passes
- [ ] Service starts without errors

## Tools

**legacy_reference_cleanup.py:**
- `--find <ITEM>`: Find all references
- `--verify <ITEM>`: Check readiness with recommendations
- `--scan`: Scan for all legacy patterns
- `--clean`: Clean up (use `--dry-run` first)

**ai_tools_runner.py:** `legacy` (part of `audit --full`)

## Best Practices

1. One item at a time
2. Test after each update
3. Use the tools (don't manual search)
4. Verify thoroughly before removal
5. Document removal in changelogs

## Success Criteria

Ready when: `--verify` shows "READY", zero active code/config refs, tests passing, service runs
