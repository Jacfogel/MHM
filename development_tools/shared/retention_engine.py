# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""Retention planning and enforcement for backup artifacts."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from core.logger import get_component_logger

from .backup_policy_models import ArtifactRule, BackupPolicy

logger = get_component_logger("development_tools")


@dataclass(frozen=True)
class RetentionAction:
    rule_name: str
    file_path: str
    reason: str
    age_days: float
    size_bytes: int


def _pattern_matches(project_root: Path, pattern: str) -> list[Path]:
    path_pattern = Path(pattern)
    if path_pattern.is_absolute():
        if path_pattern.exists():
            return [path_pattern]
        return list(path_pattern.parent.glob(path_pattern.name))
    return list(project_root.glob(pattern))


def _collect_files_for_rule(project_root: Path, rule: ArtifactRule) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
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
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _calculate_actions_for_rule(
    rule: ArtifactRule,
    files: list[Path],
    max_age_days: int | None,
    min_keep: int,
    max_keep: int,
) -> list[RetentionAction]:
    if not files:
        return []
    now_ts = time.time()
    protected_count = min(min_keep, len(files))
    protected_files = set(files[:protected_count])
    retained_files = list(files)
    actions: list[RetentionAction] = []

    if max_age_days is not None:
        cutoff_ts = now_ts - (max_age_days * 24 * 3600)
        for file_path in files:
            if file_path in protected_files:
                continue
            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                continue
            if mtime < cutoff_ts and file_path in retained_files:
                age_days = (now_ts - mtime) / 86400.0
                actions.append(
                    RetentionAction(
                        rule_name=rule.name,
                        file_path=str(file_path),
                        reason=f"age>{max_age_days}d",
                        age_days=age_days,
                        size_bytes=file_path.stat().st_size,
                    )
                )
                retained_files.remove(file_path)

    if max_keep > 0 and len(retained_files) > max_keep:
        overflow = len(retained_files) - max_keep
        removable = [f for f in retained_files if f not in protected_files]
        removable.sort(key=lambda p: p.stat().st_mtime)
        for file_path in removable[:overflow]:
            if file_path not in retained_files:
                continue
            mtime = file_path.stat().st_mtime
            age_days = (now_ts - mtime) / 86400.0
            actions.append(
                RetentionAction(
                    rule_name=rule.name,
                    file_path=str(file_path),
                    reason=f"count>{max_keep}",
                    age_days=age_days,
                    size_bytes=file_path.stat().st_size,
                )
            )
            retained_files.remove(file_path)

    unique_actions: dict[str, RetentionAction] = {}
    for action in actions:
        unique_actions[action.file_path.lower()] = action
    return list(unique_actions.values())


def build_retention_plan(
    project_root: Path,
    policy: BackupPolicy,
    target_category: str = "B",
    owner: str = "development_tools",
) -> dict[str, object]:
    """Build retention plan for matching rules."""
    planned_actions: list[RetentionAction] = []
    rule_summaries: list[dict[str, object]] = []

    category = policy.categories.get(target_category)
    if category is None:
        raise ValueError(f"Unknown target category: {target_category}")

    for rule in policy.artifact_rules:
        if not rule.enabled:
            continue
        if rule.category != target_category:
            continue
        if rule.ownership != owner:
            continue

        files = _collect_files_for_rule(project_root, rule)
        if not category.local_retention_enabled:
            rule_summaries.append(
                {
                    "rule": rule.name,
                    "category": rule.category,
                    "files_scanned": len(files),
                    "actions_planned": 0,
                    "status": "retention_disabled",
                }
            )
            continue

        actions = _calculate_actions_for_rule(
            rule=rule,
            files=files,
            max_age_days=category.max_age_days,
            min_keep=category.min_keep,
            max_keep=category.max_keep,
        )
        planned_actions.extend(actions)
        rule_summaries.append(
            {
                "rule": rule.name,
                "category": rule.category,
                "files_scanned": len(files),
                "actions_planned": len(actions),
                "status": "ok",
            }
        )

    plan = {
        "summary": {
            "target_category": target_category,
            "owner": owner,
            "rules_scanned": len(rule_summaries),
            "planned_actions": len(planned_actions),
            "planned_bytes": sum(action.size_bytes for action in planned_actions),
        },
        "rules": rule_summaries,
        "actions": [
            {
                "rule_name": action.rule_name,
                "file_path": action.file_path,
                "reason": action.reason,
                "age_days": round(action.age_days, 2),
                "size_bytes": action.size_bytes,
            }
            for action in sorted(
                planned_actions, key=lambda item: (item.rule_name, item.file_path)
            )
        ],
    }
    return plan


def apply_retention_plan(plan: dict[str, object], dry_run: bool = True) -> dict[str, object]:
    """Apply retention plan by deleting selected files."""
    results = {
        "summary": {
            "dry_run": dry_run,
            "attempted": 0,
            "deleted": 0,
            "failed": 0,
            "freed_bytes": 0,
        },
        "actions": [],
    }
    actions = plan.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        file_path = str(action.get("file_path", ""))
        if not file_path:
            continue
        results["summary"]["attempted"] += 1
        entry = dict(action)
        if dry_run:
            entry["status"] = "would_delete"
            results["actions"].append(entry)
            continue
        path_obj = Path(file_path)
        try:
            if path_obj.exists() and path_obj.is_file():
                size_bytes = path_obj.stat().st_size
                path_obj.unlink()
                entry["status"] = "deleted"
                results["summary"]["deleted"] += 1
                results["summary"]["freed_bytes"] += size_bytes
            else:
                entry["status"] = "skipped_missing"
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)
            results["summary"]["failed"] += 1
        results["actions"].append(entry)
    return results
