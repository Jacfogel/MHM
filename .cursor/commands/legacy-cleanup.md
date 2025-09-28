# Scan for Legacy References

Identify and clean up legacy code patterns, outdated references, and deprecated functionality in the MHM codebase.

## What This Does

- Scans for legacy compatibility markers
- Identifies outdated import patterns
- Finds deprecated function calls
- Detects old directory references
- Provides cleanup recommendations

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py legacy`

## Legacy Patterns Detected

- **Legacy Compatibility Markers**: `# LEGACY COMPATIBILITY:` comments
- **Old Import Patterns**: `from bot.`, `import bot.` references
- **Deprecated Functions**: `get_last_10_messages`, `channel_registry`
- **Old Directory References**: `bot/` directory references
- **Legacy Wrappers**: `LegacyChannelWrapper` usage

## When to Use

- **Before refactoring** - Identify legacy code to address
- **Weekly maintenance** - Regular legacy cleanup
- **After major changes** - Check for new legacy patterns
- **When debugging** - Find outdated code causing issues
- **Before releases** - Clean up technical debt

## Cleanup Strategy

1. **Monitor Usage**: Track when legacy code paths are accessed
2. **Add Warnings**: Log when legacy interfaces are used
3. **Plan Removal**: Document removal timeline and conditions
4. **Safe Migration**: Ensure replacement functionality exists
5. **Remove Legacy**: Delete legacy code when safe

## Output

- **Files Affected**: List of files with legacy patterns
- **Pattern Types**: Categories of legacy code found
- **Usage Tracking**: How often legacy patterns are accessed
- **Removal Plan**: Recommended cleanup timeline
- **Replacement Mapping**: What to replace legacy code with

## Integration

Updates `development_docs/LEGACY_REFERENCE_REPORT.md` with:
- Current legacy reference status
- Files needing attention
- Cleanup recommendations
- Usage monitoring data
