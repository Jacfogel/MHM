# AI Legacy Code Removal Guide

> **File**: `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md`
> **Audience**: AI collaborators and developers cleaning up deprecated code paths
> **Purpose**: Routing and constraints for using the legacy cleanup tools and safely removing legacy code
> **Style**: Minimal, reference-only, tool-focused

> For detailed explanations, rationale, and examples, see:
> - Section 3.5 "Automated tools" in `DOCUMENTATION_GUIDE.md`
> - Section 3 "Generated Outputs" and section 4 "Key Scripts" in `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`

## Quick Reference

**Goal:** Use the legacy cleanup tools to identify and safely remove deprecated code, config, and documentation without breaking production behavior.

**Core commands:**

```powershell
# Targeted search for a single item
python development_tools/legacy_reference_cleanup.py --find "LegacyItemName"

# Verify readiness for removal
python development_tools/legacy_reference_cleanup.py --verify "LegacyItemName"

# Run the integrated legacy scan via the tool runner
python development_tools/ai_tools_runner.py legacy
```

For the full audit workflow that also produces `development_docs/LEGACY_REFERENCE_REPORT.md`, use `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`, especially section 2 "Fast Mode vs Full Mode" and section 3 "Generated Outputs".

## 1. Standards

Use this guide only after you understand the general documentation and development rules:

- Documentation and pairing rules: see section 3 "Documentation Synchronization Checklist" in `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`.
- Development workflow and safety: see section 1 "Safety First" and section 3 "Standard Development Cycle" in `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`.

**When adding legacy code (temporary compatibility only):**

- Mark code with a clear `# LEGACY COMPATIBILITY:` header.
- Log usage when the legacy path is exercised.
- Add, or update, a removal plan in the relevant docs or changelog.
- Add specific detection patterns to `legacy_reference_cleanup.py` (no broad patterns like `"legacy"`).

**When preparing to remove legacy code:**

- Use search-and-close, not time-based assumptions:
  - Prove there are no remaining active references in code or config.
- Do not remove legacy code until:
  - Tests are updated or removed as appropriate.
  - Documentation and config are aligned.
  - The system starts and passes the agreed test suite.

## 2. Process

Use the legacy cleanup tool as a structured workflow rather than ad hoc search.

1. **Find** – map out references

   ```powershell
   python development_tools/legacy_reference_cleanup.py --find "LegacyItemName"
   ```

   - Scans Python and Markdown files.
   - Categorizes references (active code, tests, documentation, config, archive).
   - For behavior details, see the `LegacyReferenceCleanup.find_all_references` / `scan_for_legacy_references` flow in `development_tools/legacy_reference_cleanup.py`.

2. **Update** – fix all high-impact references

   - **Active code / config (HIGH)**: replace with the modern path or configuration.
   - **Tests (HIGH)**: update tests to target the new behavior or delete tests that exclusively cover legacy paths.
   - **Documentation (MEDIUM)**: update to describe the new behavior; archive references can remain for history.
   - **Archive (LOW)**: usually keep as-is unless causing confusion.

3. **Verify** – confirm the system is ready

   ```powershell
   python development_tools/legacy_reference_cleanup.py --verify "LegacyItemName"
   ```

   - Confirms there are no remaining active code/config references.
   - Summarizes documentation and archive references for clarity.
   - Produces recommendations and a readiness flag.

4. **Remove & Test** – only after verification is clean

   - Remove the legacy code and `LEGACY COMPATIBILITY` markers.
   - Run the standard test suite (see section 4 "Test Layout and Discovery" in `ai_development_docs/AI_TESTING_GUIDE.md`).
   - Start the service and confirm normal behavior.
   - Update changelogs or relevant docs to record the removal.

## 3. Checklist

Use this as a quick, pre-removal gate.

Before you delete a legacy item:

- [ ] `--find` shows no active code or config references.
- [ ] Tests referencing the item are updated or removed.
- [ ] `--verify` reports the item as ready for removal.
- [ ] The standard test suite passes after your changes.
- [ ] The service starts and runs without errors.
- [ ] Relevant documentation and changelogs mention the removal where appropriate.

## 4. Tools

These tools underlie this guide. For detailed behavior and additional commands, see `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` (section 1 "Main Entry Point", section 3 "Generated Outputs", and section 4 "Key Scripts").

- `development_tools/legacy_reference_cleanup.py`:
  - `--scan`: scan for all legacy patterns.
  - `--find <ITEM>`: search for references to a specific legacy item.
  - `--verify <ITEM>`: verify removal readiness and summarize references.
  - `--clean`: clean up legacy references (always use `--dry-run` first).

- `development_tools/ai_tools_runner.py`:
  - `legacy`: integrated legacy scan, and in some modes, report regeneration.
  - `audit` / `audit --full`: broader audits that also generate `development_docs/LEGACY_REFERENCE_REPORT.md` and related outputs.

## 5. Best Practices

- Work on **one legacy item at a time**.
- Run `--find` and `--verify` before touching code, then again after updates.
- Prefer using the provided tools instead of manual search; they are tuned to MHM’s legacy patterns.
- When in doubt, keep archive references and historical docs; prioritize removing active code and config paths.
- Document removals in the changelog or relevant docs so future audits know what changed.

## 6. Success Criteria

A legacy item is considered fully removed when:

- `--verify` shows the item as ready for removal.
- There are zero active code/config references in the report.
- Tests and config no longer mention the legacy path (except where deliberately archived).
- The service starts and passes the agreed test suite.
- Documentation and changelog entries reflect the new, non-legacy behavior.
