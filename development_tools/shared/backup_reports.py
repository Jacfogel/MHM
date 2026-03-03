# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""Report utilities for backup policy operations."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.logger import get_component_logger

from .file_rotation import create_output_file

logger = get_component_logger("development_tools")


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _resolve_output_path(project_root: Path, configured_path: str) -> Path:
    candidate = Path(configured_path)
    if candidate.is_absolute():
        return candidate
    return (project_root / candidate).resolve()


def write_json_report(
    project_root: Path, configured_path: str, payload: Dict[str, object], rotate: bool = True
) -> Path:
    output_path = _resolve_output_path(project_root, configured_path)
    content = json.dumps(payload, indent=2)
    create_output_file(
        output_path,
        content,
        rotate=rotate,
        max_versions=7,
        project_root=project_root,
    )
    return output_path


def build_inventory_markdown(inventory: Dict[str, object]) -> str:
    summary = _as_dict(inventory.get("summary", {}))
    lines = [
        "# Backup Inventory Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        f"- Total rules: {summary.get('total_rules', 0)}",
        f"- Enabled rules: {summary.get('enabled_rules', 0)}",
        f"- Rules with files: {summary.get('rules_with_files', 0)}",
        "",
        "## Rules",
    ]
    for entry in _as_list(inventory.get("rules", [])):
        lines.extend(
            [
                f"- {entry.get('name', 'unknown')}",
                f"  - category: {entry.get('category', '')}",
                f"  - ownership: {entry.get('ownership', '')}",
                f"  - trigger: {entry.get('trigger', '')}",
                f"  - producer: {entry.get('producer', '')}",
                f"  - files: {entry.get('file_count', 0)}",
                f"  - latest_modified: {entry.get('latest_modified', 'n/a')}",
            ]
        )
    return "\n".join(lines) + "\n"


def build_retention_markdown(plan: Dict[str, object], result: Dict[str, object]) -> str:
    summary = _as_dict(plan.get("summary", {}))
    run_summary = _as_dict(result.get("summary", {}))
    lines = [
        "# Backup Retention Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Plan Summary",
        f"- Target category: {summary.get('target_category', '')}",
        f"- Owner: {summary.get('owner', '')}",
        f"- Rules scanned: {summary.get('rules_scanned', 0)}",
        f"- Planned actions: {summary.get('planned_actions', 0)}",
        "",
        "## Execution Summary",
        f"- Dry run: {run_summary.get('dry_run', True)}",
        f"- Attempted: {run_summary.get('attempted', 0)}",
        f"- Deleted: {run_summary.get('deleted', 0)}",
        f"- Failed: {run_summary.get('failed', 0)}",
        f"- Freed bytes: {run_summary.get('freed_bytes', 0)}",
        "",
        "## Actions",
    ]
    for action in _as_list(result.get("actions", [])):
        lines.append(
            f"- [{action.get('status', 'unknown')}] {action.get('file_path', '')} ({action.get('reason', '')})"
        )
    return "\n".join(lines) + "\n"


def build_restore_drill_markdown(report: Dict[str, object]) -> str:
    summary = _as_dict(report.get("summary", {}))
    verification = _as_dict(report.get("verification", {}))
    lines = [
        "# Backup Restore Drill Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        f"- Success: {summary.get('success', False)}",
        f"- Backup path: {summary.get('backup_path', '')}",
        f"- Restore destination: {summary.get('restore_destination', '')}",
        f"- Restored file count: {summary.get('restored_file_count', 0)}",
        "",
        "## Verification",
        f"- required_paths_ok: {verification.get('required_paths_ok', False)}",
        f"- min_file_count_ok: {verification.get('min_file_count_ok', False)}",
    ]
    missing_paths_value = verification.get("missing_required_paths", [])
    missing_paths = (
        [str(path) for path in missing_paths_value]
        if isinstance(missing_paths_value, list)
        else []
    )
    if missing_paths:
        lines.append(f"- missing_required_paths: {', '.join(missing_paths)}")
    if summary.get("error"):
        lines.extend(["", "## Error", f"- {summary['error']}"])
    return "\n".join(lines) + "\n"


def write_markdown_report(
    project_root: Path, configured_path: str, content: str, rotate: bool = True
) -> Path:
    output_path = _resolve_output_path(project_root, configured_path)
    create_output_file(
        output_path,
        content,
        rotate=rotate,
        max_versions=7,
        project_root=project_root,
    )
    return output_path
