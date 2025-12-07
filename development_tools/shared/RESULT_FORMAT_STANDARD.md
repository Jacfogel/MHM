# Analysis Tool Result Format Standard

> **File**: `development_tools/shared/RESULT_FORMAT_STANDARD.md`
> **Purpose**: Define standardized result format for all analysis tools
> **Status**: Draft - Proposal for standardization

## Current Result Formats

### Format 1: File-Based Analysis Tools
**Used by**: `analyze_ascii_compliance`, `analyze_heading_numbering`, `analyze_missing_addresses`, `analyze_unconverted_links`

```json
{
  "files": {
    "file_path": issue_count
  },
  "file_count": int,
  "total_issues": int
}
```

### Format 2: Path Drift Analysis
**Used by**: `analyze_path_drift`

```json
{
  "files": {
    "file_path": issue_count
  },
  "total_issues": int,
  "detailed_issues": {
    "file_path": ["issue1", "issue2", ...]
  }
}
```

### Format 3: Unused Imports
**Used by**: `analyze_unused_imports`

```json
{
  "files_scanned": int,
  "files_with_issues": int,
  "total_unused": int,
  "by_category": {
    "category_name": count
  },
  "status": "GOOD" | "NEEDS_ATTENTION" | "CRITICAL"
}
```

### Format 4: Aggregated Results
**Used by**: `analyze_documentation_sync`

```json
{
  "status": "PASS" | "FAIL" | "UNKNOWN",
  "total_issues": int,
  "paired_doc_issues": int,
  "path_drift_issues": int,
  "ascii_compliance_issues": int,
  "heading_numbering_issues": int,
  "missing_address_issues": int,
  "unconverted_link_issues": int,
  "path_drift_files": [file_path, ...],
  "paired_docs": {...},
  "path_drift": {...},
  "ascii_compliance": {...},
  "heading_numbering": {...}
}
```

## Proposed Standard Format

### Standard Structure

```json
{
  "summary": {
    "total_issues": int,           // Required: Total number of issues found
    "files_affected": int,         // Required: Number of files with issues (0 if not file-based)
    "status": str                  // Optional: Overall status ("GOOD", "NEEDS_ATTENTION", "CRITICAL", "PASS", "FAIL")
  },
  "files": {                       // Optional: For file-based tools
    "file_path": issue_count       // Map of file paths to issue counts
  },
  "details": {                     // Optional: Tool-specific detailed data
    // Tool-specific fields (e.g., detailed_issues, by_category, etc.)
  }
}
```

### Migration Strategy

**Phase 1: Backward Compatibility (Current)**
- Keep existing formats
- Update unified helper to handle all current formats
- Add format detection/conversion helpers

**Phase 2: Gradual Migration**
- New tools use standard format
- Update tools incrementally when refactoring
- Maintain backward compatibility in consumers

**Phase 3: Full Standardization**
- All tools use standard format
- Remove format conversion code
- Simplify unified helper

### Benefits

1. **Consistency**: All tools report issues in the same way
2. **Reusability**: Unified helper works for all tools
3. **Extensibility**: Tool-specific data in `details` section
4. **Status Reports**: Easier to aggregate and display

### Field Mappings

**File-based tools** (Format 1 → Standard):
- `total_issues` → `summary.total_issues`
- `file_count` → `summary.files_affected`
- `files` → `files` (unchanged)

**Path drift** (Format 2 → Standard):
- `total_issues` → `summary.total_issues`
- `len(files)` → `summary.files_affected`
- `files` → `files` (unchanged)
- `detailed_issues` → `details.detailed_issues`

**Unused imports** (Format 3 → Standard):
- `total_unused` → `summary.total_issues`
- `files_with_issues` → `summary.files_affected`
- `status` → `summary.status`
- `by_category` → `details.by_category`
- `files_scanned` → `details.files_scanned`

## Implementation Notes

- The unified helper `_load_mtime_cached_tool_results()` should be updated to:
  1. Accept a format converter function
  2. Normalize results to standard format
  3. Support backward compatibility with old formats

- Status report generators should:
  1. Check for standard format first
  2. Fall back to old format detection
  3. Gradually migrate to standard format only

