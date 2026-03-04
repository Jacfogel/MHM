# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""Backup inventory helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from core.logger import get_component_logger

from .backup_policy_models import ArtifactRule, BackupPolicy

logger = get_component_logger("development_tools")


def _pattern_matches(project_root: Path, pattern: str) -> List[Path]:
    path_pattern = Path(pattern)
    if path_pattern.is_absolute():
        if path_pattern.exists():
            return [path_pattern]
        return list(path_pattern.parent.glob(path_pattern.name))
    return list(project_root.glob(pattern))


def _collect_files_for_rule(project_root: Path, rule: ArtifactRule) -> List[Path]:
    files: List[Path] = []
    seen: Set[str] = set()
    for pattern in rule.paths:
        for match in _pattern_matches(project_root, pattern):
            if match.is_file():
                key = str(match.resolve()).lower()
                if key not in seen:
                    seen.add(key)
                    files.append(match)
            elif match.is_dir():
                for child in match.rglob("*"):
                    if not child.is_file():
                        continue
                    key = str(child.resolve()).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    files.append(child)
    return files


def build_backup_inventory(project_root: Path, policy: BackupPolicy) -> Dict[str, object]:
    """Create inventory summary from backup policy and filesystem state."""
    entries: List[Dict[str, object]] = []
    for rule in policy.artifact_rules:
        files = _collect_files_for_rule(project_root, rule)
        latest_modified = None
        if files:
            latest = max(files, key=lambda p: p.stat().st_mtime)
            latest_modified = datetime.fromtimestamp(latest.stat().st_mtime).isoformat(
                timespec="seconds"
            )
        category = policy.categories.get(rule.category)
        entries.append(
            {
                "name": rule.name,
                "enabled": rule.enabled,
                "category": rule.category,
                "category_description": category.description if category else "",
                "ownership": rule.ownership,
                "portable": rule.portable,
                "producer": rule.producer,
                "trigger": rule.trigger,
                "restore_path": rule.restore_path,
                "paths": list(rule.paths),
                "file_count": len(files),
                "latest_modified": latest_modified,
                "notes": rule.notes,
            }
        )

    rules_with_files = 0
    for entry in entries:
        file_count = entry.get("file_count")
        if isinstance(file_count, int) and file_count > 0:
            rules_with_files += 1

    inventory = {
        "summary": {
            "total_rules": len(policy.artifact_rules),
            "enabled_rules": sum(1 for r in policy.artifact_rules if r.enabled),
            "rules_with_files": rules_with_files,
        },
        "categories": {
            key: {
                "description": category.description,
                "max_age_days": category.max_age_days,
                "min_keep": category.min_keep,
                "max_keep": category.max_keep,
                "local_retention_enabled": category.local_retention_enabled,
            }
            for key, category in policy.categories.items()
        },
        "ownership_map": policy.ownership_map,
        "rules": entries,
    }
    logger.debug(
        f"Backup inventory generated: {inventory['summary']['total_rules']} rules, "
        f"{inventory['summary']['rules_with_files']} with matching files"
    )
    return inventory
