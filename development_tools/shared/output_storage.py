# TOOL_TIER: core

"""
Standardized output storage utility for development tools.

Provides consistent storage patterns for tool results and cache files,
with automatic archiving and rotation support.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full, now_timestamp_filename
from .file_rotation import FileRotator

logger = get_component_logger("development_tools")


def _get_domain_from_tool_name(tool_name: str, project_root: Path) -> str:
    """
    Determine the domain directory for a tool based on its name and SCRIPT_REGISTRY.

    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        project_root: Project root directory

    Returns:
        Domain directory name (e.g., 'functions', 'docs', 'error_handling')
    """
    # Import SCRIPT_REGISTRY to map tool names to paths
    try:
        from .service import SCRIPT_REGISTRY

        script_path = SCRIPT_REGISTRY.get(tool_name)
        if script_path:
            # Extract domain from path like 'functions/analyze_functions.py'
            domain = script_path.split("/")[0]
            return domain
    except (ImportError, AttributeError):
        pass

    # Fallback: try to infer from tool name patterns
    if "function" in tool_name:
        return "functions"
    elif "documentation" in tool_name or "doc" in tool_name:
        return "docs"
    elif "error" in tool_name or "handling" in tool_name:
        return "error_handling"
    elif "test" in tool_name or "coverage" in tool_name:
        return "tests"
    elif "import" in tool_name or "module" in tool_name or "dependency" in tool_name:
        return "imports"
    elif "legacy" in tool_name:
        return "legacy"
    elif "config" in tool_name:
        return "config"
    elif "ai_work" in tool_name or "ai" in tool_name:
        return "ai_work"
    elif "status" in tool_name or "signal" in tool_name or "decision" in tool_name:
        return "reports"
    else:
        # Default to 'reports' for unknown tools
        return "reports"


def _get_project_root() -> Path:
    """Get project root directory."""
    # Try to get from config
    try:
        from .. import config

        return Path(config.get_project_root())
    except (ImportError, AttributeError):
        # Fallback: assume we're in development_tools/shared/
        return Path(__file__).parent.parent.parent


def save_tool_result(
    tool_name: str,
    domain: Optional[str] = None,
    data: Dict[str, Any] = None,
    archive_count: int = 7,
    project_root: Optional[Path] = None,
) -> Path:
    """
    Save tool result to domain-specific JSON file with automatic archiving.

    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        data: Data to save (dict)
        archive_count: Number of archive versions to keep (default: 7, standardized retention)
        project_root: Project root directory. If None, auto-detected

    Returns:
        Path to the saved file
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()

    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)

    # Build file path: development_tools/{domain}/jsons/{tool}_results.json
    dev_tools_dir = project_root / "development_tools"
    jsons_dir = dev_tools_dir / domain / "jsons"
    jsons_dir.mkdir(parents=True, exist_ok=True)

    result_file = jsons_dir / f"{tool_name}_results.json"

    # Prepare data with metadata
    timestamp_str = now_timestamp_full()
    # If you want a machine-friendly timestamp, generate ISO from datetime (not from the readable string).
    timestamp_iso = datetime.now().isoformat(timespec="seconds")
    filename_timestamp = now_timestamp_filename()

    result_data = {
        "generated_by": f"{tool_name} - Development Tools",
        "last_generated": timestamp_str,
        "timestamp": timestamp_iso,
        "tool_name": tool_name,
        "domain": domain,
        "source": f"python development_tools/{domain}/{tool_name}.py",
        "note": "This file is auto-generated. Do not edit manually.",
        "data": data or {},
    }

    # Use create_output_file for rotation, but we need custom archiving for jsons/archive/
    # First, handle rotation if file exists
    if result_file.exists():
        archive_dir = jsons_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped archive
        archive_name = f"{tool_name}_results_{filename_timestamp}.json"
        archive_path = archive_dir / archive_name

        # Move existing file to archive
        import shutil

        shutil.move(str(result_file), str(archive_path))

        # Clean up old archives (keep last archive_count)
        rotator = FileRotator(base_dir=str(jsons_dir))
        rotator._cleanup_old_versions(f"{tool_name}_results", archive_count)

    # Write new file
    result_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)
            f.flush()  # Ensure data is written to disk
            if hasattr(f, "fileno"):
                try:
                    import os

                    os.fsync(f.fileno())  # Force sync to disk on Unix
                except (OSError, AttributeError):
                    pass  # fsync not available or not needed on Windows
        logger.info(
            f"Saved tool result: {result_file} (archive_count={archive_count}, data_size={len(str(result_data))} chars)"
        )
    except Exception as e:
        logger.error(f"Failed to write tool result file {result_file}: {e}")
        raise
    return result_file


def _validate_result_files_exist(
    data: Dict[str, Any], project_root: Path
) -> Dict[str, Any]:
    """
    Validate that files referenced in result data still exist, removing references to deleted files.

    This prevents stale data from deleted files appearing in reports.

    Args:
        data: Result data dictionary that may contain file references
        project_root: Project root directory for resolving file paths

    Returns:
        Validated data dictionary with deleted file references removed
    """
    if not isinstance(data, dict):
        return data

    validated_data = data.copy()

    # Check for common patterns in documentation analysis results
    # Pattern 1: 'files' dict mapping file paths to issue counts/lists
    if "files" in validated_data and isinstance(validated_data["files"], dict):
        original_files = validated_data["files"].copy()
        validated_files = {}
        removed_count = 0

        for file_path, issues in original_files.items():
            # Try to resolve file path relative to project root
            try:
                # Handle both forward and backslash paths
                normalized_path = file_path.replace("\\", "/")
                file_full_path = project_root / normalized_path

                if file_full_path.exists():
                    validated_files[file_path] = issues
                else:
                    removed_count += 1
                    if logger:
                        logger.debug(
                            f"Removed reference to deleted file from results: {file_path}"
                        )
            except Exception:
                # If path resolution fails, keep it (might be a special path)
                validated_files[file_path] = issues

        validated_data["files"] = validated_files

        # Update counts if they exist
        if removed_count > 0:
            if "file_count" in validated_data:
                validated_data["file_count"] = len(validated_files)
            if "total_issues" in validated_data:
                # Recalculate total issues from remaining files
                total = sum(
                    (
                        len(v)
                        if isinstance(v, list)
                        else (v if isinstance(v, (int, float)) else 0)
                    )
                    for v in validated_files.values()
                )
                validated_data["total_issues"] = total

    # Pattern 2: Nested structures (e.g., analyze_documentation_sync_results.json)
    # Recursively validate nested dicts that might contain file references
    for key, value in validated_data.items():
        if isinstance(value, dict) and key != "files":
            validated_data[key] = _validate_result_files_exist(value, project_root)

    return validated_data


def load_tool_result(
    tool_name: str,
    domain: Optional[str] = None,
    project_root: Optional[Path] = None,
    normalize: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Load tool result from domain-specific JSON file.

    Automatically validates that referenced files still exist, removing
    references to deleted files to prevent stale data in reports.

    Optionally normalizes data to standard format for consistent access.

    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        project_root: Project root directory. If None, auto-detected
        normalize: If True, normalize data to standard format (default: True)

    Returns:
        Data dict if file exists, None otherwise (with deleted file references removed,
        and normalized to standard format if normalize=True)
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()

    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)

    # Build file path
    dev_tools_dir = project_root / "development_tools"
    result_file = dev_tools_dir / domain / "jsons" / f"{tool_name}_results.json"

    if not result_file.exists():
        return None

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)

        data = result_data.get("data", result_data)

        # Validate that referenced files still exist (for documentation analysis tools)
        # Only validate for tools that reference file paths
        if domain in ("docs", "error_handling", "legacy") and isinstance(data, dict):
            data = _validate_result_files_exist(data, project_root)

        # Normalize to standard format if requested
        if normalize and isinstance(data, dict):
            from .result_format import normalize_to_standard_format
            try:
                data = normalize_to_standard_format(tool_name, data)
            except ValueError as e:
                logger.error(f"Invalid result format for {tool_name}: {e}")
                return None

        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load tool result from {result_file}: {e}")
        return None


def save_tool_cache(
    tool_name: str,
    domain: Optional[str] = None,
    data: Dict[str, Any] = None,
    project_root: Optional[Path] = None,
) -> Path:
    """
    Save tool cache file to domain-specific jsons/ directory.

    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        data: Data to save (dict)
        project_root: Project root directory. If None, auto-detected

    Returns:
        Path to the saved cache file
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()

    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)

    # Build file path: development_tools/{domain}/jsons/.{tool}_cache.json
    dev_tools_dir = project_root / "development_tools"
    jsons_dir = dev_tools_dir / domain / "jsons"
    jsons_dir.mkdir(parents=True, exist_ok=True)

    cache_file = jsons_dir / f".{tool_name}_cache.json"

    # Prepare cache data with metadata
    timestamp_str = now_timestamp_full()
    timestamp_iso = datetime.now().isoformat()

    cache_data = {
        "generated_by": f"{tool_name} - Development Tools",
        "last_generated": timestamp_str,
        "timestamp": timestamp_iso,
        "tool_name": tool_name,
        "domain": domain,
        "note": "This file is auto-generated. Do not edit manually.",
        "data": data or {},
    }

    # Write cache file (no rotation for cache files)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except (TypeError, ValueError, IOError) as e:
        logger.warning(f"Failed to write tool cache file {cache_file}: {e}")
        raise

    logger.debug(f"Saved tool cache: {cache_file}")
    return cache_file


def load_tool_cache(
    tool_name: str, domain: Optional[str] = None, project_root: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Load tool cache file from domain-specific jsons/ directory.

    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        project_root: Project root directory. If None, auto-detected

    Returns:
        Data dict if file exists, None otherwise
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()

    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)

    # Build file path
    dev_tools_dir = project_root / "development_tools"
    cache_file = dev_tools_dir / domain / "jsons" / f".{tool_name}_cache.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        return cache_data.get("data", cache_data)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load tool cache from {cache_file}: {e}")
        # Remove corrupted cache file to allow regeneration on next run.
        try:
            cache_file.unlink(missing_ok=True)
        except Exception:
            pass
        return None


def get_all_tool_results(
    project_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate all tool results from all domain jsons/ directories.

    Args:
        project_root: Project root directory. If None, auto-detected

    Returns:
        Dict mapping tool_name -> result_data
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()

    dev_tools_dir = project_root / "development_tools"
    all_results = {}

    # Known domain directories
    domains = [
        "functions",
        "docs",
        "error_handling",
        "tests",
        "imports",
        "legacy",
        "config",
        "ai_work",
        "reports",
        "shared",
    ]

    def _parse_result_timestamp(result_data: Dict[str, Any], result_file: Path) -> datetime:
        """Return a comparable timestamp for a tool result entry."""
        raw_ts = None
        if isinstance(result_data, dict):
            raw_ts = result_data.get("timestamp") or result_data.get("last_generated")
        if isinstance(raw_ts, str):
            try:
                return datetime.fromisoformat(raw_ts)
            except ValueError:
                try:
                    return datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
        try:
            return datetime.fromtimestamp(result_file.stat().st_mtime)
        except OSError:
            return datetime.min

    for domain in domains:
        jsons_dir = dev_tools_dir / domain / "jsons"
        if not jsons_dir.exists():
            continue

        # Find all _results.json files
        for result_file in jsons_dir.glob("*_results.json"):
            tool_name = result_file.stem.replace("_results", "")

            # Verify file exists and has non-zero size before attempting to read
            if not result_file.exists():
                logger.debug(f"Skipping missing result file: {result_file}")
                continue

            try:
                # Check file size to avoid reading empty files
                if result_file.stat().st_size == 0:
                    logger.debug(f"Skipping empty result file: {result_file}")
                    continue

                with open(result_file, "r", encoding="utf-8") as f:
                    result_data = json.load(f)
                if tool_name in all_results:
                    existing = all_results[tool_name]
                    existing_ts = _parse_result_timestamp(existing, result_file)
                    candidate_ts = _parse_result_timestamp(result_data, result_file)
                    if candidate_ts > existing_ts:
                        all_results[tool_name] = result_data
                else:
                    all_results[tool_name] = result_data
            except FileNotFoundError:
                # File was deleted between existence check and open - skip gracefully
                logger.debug(f"Result file disappeared: {result_file}")
                continue
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load result from {result_file}: {e}")
                continue

    return all_results
