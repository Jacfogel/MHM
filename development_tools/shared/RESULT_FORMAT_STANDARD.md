# Analysis Tool Result Format Standard

> **File**: `development_tools/shared/RESULT_FORMAT_STANDARD.md`
> **Purpose**: Define standardized result format for all analysis tools
> **Status**: Enforced

## Standard Format

All analysis tools must emit JSON in this structure:

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

## Compliance Notes

- Consumers assume `summary` is present and includes `total_issues` and `files_affected`.
- Tool results are validated on read; non-standard shapes are treated as errors.
- Tool-specific fields should live under `details` to avoid collisions.
