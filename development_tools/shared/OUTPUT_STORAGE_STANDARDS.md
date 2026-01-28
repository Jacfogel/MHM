# Development Tools Output Storage Standards

> **File**: `development_tools/shared/OUTPUT_STORAGE_STANDARDS.md`
> **Purpose**: Document current output storage patterns and define standards for consistent tool output storage
> **Status**: Draft - Standards definition in progress

## Current Patterns Analysis

### Pattern 1: Using `create_output_file()` (Recommended)
**Location**: `development_tools/shared/file_rotation.py`
**Used by**: 
- Status files: `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`
- `analysis_detailed_results.json` (via `_save_additional_tool_results()`)

**Benefits**:
- Automatic file rotation and archiving
- Consistent path handling
- "Latest" pointer support

### Pattern 2: Direct JSON File Writing
**Used by**:
- `error_handling/error_handling_details.json`
- `config/analyze_config_results.json`
- `tests/coverage_dev_tools.json`
- `imports/.unused_imports_cache.json`

**Issues**:
- No automatic rotation
- Inconsistent path handling
- Manual timestamp management

### Pattern 3: Domain-Specific Directories
**Pattern**: Tools write to their own domain directory
- `error_handling/` - Error handling analysis results
- `config/` - Configuration validation results
- `tests/` - Test coverage results
- `imports/` - Import analysis results
- `reports/` - Consolidated reports and analysis results

**Benefits**:
- Clear organization by domain
- Easy to find related outputs

**Issues**:
- Inconsistent file naming
- Some use subdirectories, some don't

### Pattern 4: Human-Facing Documentation
**Location**: `development_docs/`
**Files**:
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
- `development_docs/LEGACY_REFERENCE_REPORT.md`
- `development_docs/UNUSED_IMPORTS_REPORT.md`
- `development_docs/DIRECTORY_TREE.md`

**Pattern**: Direct file writing, no rotation

## Proposed Standards

### Standard 1: Output File Types

1. **Status Reports** (AI-facing, root level)
   - Format: Markdown (`.md`) or Text (`.txt`)
   - Location: `development_tools/`
   - Method: `create_output_file()`
   - Examples: `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`

2. **Analysis Results** (JSON, domain-specific)
   - Format: JSON (`.json`)
   - Location: Domain-specific directory (e.g., `error_handling/`, `config/`, `tests/`)
   - Method: `create_output_file()` for consistency
   - Naming: `{tool_name}_results.json` or `{domain}_details.json`
   - Examples: `error_handling_details.json`, `analyze_config_results.json`

3. **Human Documentation** (Markdown, development_docs)
   - Format: Markdown (`.md`)
   - Location: `development_docs/`
   - Method: `create_output_file()` (with rotation disabled for docs)
   - Naming: `{DESCRIPTION}_DETAIL.md` or `{DESCRIPTION}_REPORT.md`
   - Examples: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`

4. **Cache Files** (JSON, temporary)
   - Format: JSON (`.json`)
   - Location: Domain-specific directory or `.cache/` subdirectory
   - Method: Direct write (no rotation needed for caches)
   - Naming: `.{tool_name}_cache.json` or `.{domain}_cache.json`
   - Examples: `.unused_imports_cache.json`

### Standard 2: File Naming Conventions

- **Status files**: `{NAME}.md` or `{NAME}.txt` (e.g., `development_tools/AI_STATUS.md`)
- **Analysis results**: `{tool_name}_results.json` or `{domain}_details.json`
- **Documentation**: `{DESCRIPTION}_DETAIL.md` or `{DESCRIPTION}_REPORT.md`
- **Cache files**: `.{tool_name}_cache.json` (hidden files)

### Standard 3: Directory Structure

```
development_tools/
├── AI_STATUS.md                    # Status report (root: development_tools/)
├── AI_PRIORITIES.md                # Status report (root: development_tools/)
├── consolidated_report.txt          # Status report (root: development_tools/)
├── reports/
│   ├── analysis_detailed_results.json  # Consolidated analysis cache
│   └── archive/                    # Archived reports
├── error_handling/
│   └── error_handling_details.json
├── config/
│   └── analyze_config_results.json
├── tests/
│   └── coverage_dev_tools.json
├── imports/
│   └── .unused_imports_cache.json
└── ...

development_docs/
├── FUNCTION_REGISTRY_DETAIL.md     # development_docs/
├── MODULE_DEPENDENCIES_DETAIL.md    # development_docs/
├── LEGACY_REFERENCE_REPORT.md       # development_docs/
└── ...
```

### Standard 4: Output Methods

**For all new tools and when refactoring existing tools**:

1. **Use `create_output_file()`** for:
   - Status reports
   - Analysis results that should be archived
   - Documentation files

2. **Direct file writing** (with proper error handling) for:
   - Cache files (temporary, no archiving needed)
   - Files that are overwritten each run (no history needed)

3. **JSON structure** for analysis results:
```json
{
  "generated_by": "tool_name - Tool Description",
  "last_generated": "YYYY-MM-DD HH:MM:SS",
  "source": "python development_tools/path/to/tool.py",
  "note": "This file is auto-generated. Do not edit manually.",
  "data": {
    // Tool-specific data
  }
}
```

### Standard 5: Path Resolution

- Always use `project_root` from config, never hardcode paths
- Use `Path` objects from `pathlib` for path manipulation
- Resolve paths relative to `project_root` or use absolute paths

## Implementation Plan

### Phase 1: Documentation (Current)
- [x] Document current patterns
- [x] Define standards
- [ ] Get approval/feedback

### Phase 2: Enhance `create_output_file()`
- [ ] Add support for JSON output with standard metadata
- [ ] Add option to disable rotation for documentation files
- [ ] Ensure consistent error handling

### Phase 3: Update Tools (Future)
- [ ] Update tools to use `create_output_file()` where appropriate
- [ ] Standardize JSON output format
- [ ] Update file naming to follow conventions
- [ ] Add tests for output storage

## Notes

- This is a living document - update as patterns evolve
- Tools should be updated incrementally, not all at once
- Document any exceptions to standards with rationale

