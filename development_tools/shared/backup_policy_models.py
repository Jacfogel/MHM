# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Typed backup policy models and validation.

All project-specific behavior must be sourced from development_tools config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_component_logger

try:
    from .. import config
except ImportError:
    from development_tools import config

logger = get_component_logger("development_tools")


@dataclass(frozen=True)
class RetentionCategory:
    key: str
    description: str
    max_age_days: Optional[int]
    min_keep: int
    max_keep: int
    local_retention_enabled: bool = True


@dataclass(frozen=True)
class ArtifactRule:
    name: str
    paths: List[str]
    category: str
    enabled: bool = True
    ownership: str = "development_tools"
    portable: bool = True
    producer: str = "unspecified"
    trigger: str = "manual"
    restore_path: str = ""
    notes: str = ""


@dataclass(frozen=True)
class RestoreDrillConfig:
    temp_restore_root: str
    report_json_path: str
    report_markdown_path: Optional[str] = None
    verification_checks: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackupPolicy:
    categories: Dict[str, RetentionCategory]
    artifact_rules: List[ArtifactRule]
    restore_drill: RestoreDrillConfig
    ownership_map: Dict[str, str]


DEFAULT_BACKUP_POLICY: Dict[str, Any] = {
    "categories": {
        "A": {
            "description": "Recovery-critical runtime data",
            "max_age_days": 30,
            "min_keep": 4,
            "max_keep": 10,
            "local_retention_enabled": True,
        },
        "B": {
            "description": "Engineering artifacts",
            "max_age_days": 90,
            "min_keep": 7,
            "max_keep": 30,
            "local_retention_enabled": True,
        },
        "C": {
            "description": "Git-canonical tracked assets",
            "max_age_days": None,
            "min_keep": 0,
            "max_keep": 0,
            "local_retention_enabled": False,
        },
    },
    "artifact_rules": [],
    "restore_drill": {
        "temp_restore_root": "development_tools/reports/backup_drills",
        "report_json_path": "development_tools/reports/jsons/backup_restore_drill_report.json",
        "verification_checks": {
            "required_paths": ["users"],
            "min_file_count": 1,
        },
    },
    "ownership_map": {
        "core": "User backup creation/restore + runtime backup scheduling",
        "development_tools": "Engineering artifact retention/inventory/reporting",
        "git": "Canonical source history for tracked code/docs/changelogs",
    },
}


def _as_int(value: Any, field_name: str, minimum: int = 0) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    return value


def _parse_category(key: str, data: Dict[str, Any]) -> RetentionCategory:
    if not isinstance(data, dict):
        raise ValueError(f"Category '{key}' must be an object")
    description = str(data.get("description", "")).strip()
    max_age_days = data.get("max_age_days")
    if max_age_days is not None:
        max_age_days = _as_int(max_age_days, f"categories.{key}.max_age_days", 0)
    min_keep = _as_int(data.get("min_keep", 0), f"categories.{key}.min_keep", 0)
    max_keep = _as_int(data.get("max_keep", 0), f"categories.{key}.max_keep", 0)
    if max_keep and min_keep > max_keep:
        raise ValueError(f"categories.{key}.min_keep must be <= max_keep")
    local_retention_enabled = bool(data.get("local_retention_enabled", True))
    return RetentionCategory(
        key=key,
        description=description,
        max_age_days=max_age_days,
        min_keep=min_keep,
        max_keep=max_keep,
        local_retention_enabled=local_retention_enabled,
    )


def _parse_artifact_rule(data: Dict[str, Any], categories: Dict[str, RetentionCategory]) -> ArtifactRule:
    if not isinstance(data, dict):
        raise ValueError("Each artifact rule must be an object")
    name = str(data.get("name", "")).strip()
    if not name:
        raise ValueError("artifact_rules[].name is required")
    raw_paths = data.get("paths", [])
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError(f"artifact_rules[{name}].paths must be a non-empty list")
    paths = [str(item) for item in raw_paths if str(item).strip()]
    if not paths:
        raise ValueError(f"artifact_rules[{name}].paths has no usable entries")
    category = str(data.get("category", "")).strip()
    if category not in categories:
        raise ValueError(f"artifact_rules[{name}] references unknown category '{category}'")
    ownership = str(data.get("ownership", "development_tools")).strip().lower()
    if ownership not in {"core", "development_tools", "git"}:
        raise ValueError(
            f"artifact_rules[{name}].ownership must be one of core/development_tools/git"
        )
    return ArtifactRule(
        name=name,
        paths=paths,
        category=category,
        enabled=bool(data.get("enabled", True)),
        ownership=ownership,
        portable=bool(data.get("portable", True)),
        producer=str(data.get("producer", "unspecified")),
        trigger=str(data.get("trigger", "manual")),
        restore_path=str(data.get("restore_path", "")),
        notes=str(data.get("notes", "")),
    )


def _merge_policy_dict(raw_policy: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {
        "categories": dict(DEFAULT_BACKUP_POLICY["categories"]),
        "artifact_rules": list(DEFAULT_BACKUP_POLICY["artifact_rules"]),
        "restore_drill": dict(DEFAULT_BACKUP_POLICY["restore_drill"]),
        "ownership_map": dict(DEFAULT_BACKUP_POLICY["ownership_map"]),
    }
    if not isinstance(raw_policy, dict):
        return merged
    if isinstance(raw_policy.get("categories"), dict):
        for key, value in raw_policy["categories"].items():
            base = dict(merged["categories"].get(key, {}))
            if isinstance(value, dict):
                base.update(value)
                merged["categories"][key] = base
    if isinstance(raw_policy.get("artifact_rules"), list):
        merged["artifact_rules"] = raw_policy["artifact_rules"]
    if isinstance(raw_policy.get("restore_drill"), dict):
        restore_drill = dict(merged["restore_drill"])
        restore_drill.update(raw_policy["restore_drill"])
        merged["restore_drill"] = restore_drill
    if isinstance(raw_policy.get("ownership_map"), dict):
        ownership_map = dict(merged["ownership_map"])
        ownership_map.update(raw_policy["ownership_map"])
        merged["ownership_map"] = ownership_map
    return merged


def load_backup_policy() -> BackupPolicy:
    """
    Load and validate backup policy from development_tools config.

    Raises:
        ValueError: if the policy shape is invalid.
    """
    config.load_external_config()
    raw_policy = config.get_backup_policy_config()
    merged = _merge_policy_dict(raw_policy)

    raw_categories = merged.get("categories", {})
    if not isinstance(raw_categories, dict) or not raw_categories:
        raise ValueError("backup_policy.categories must be a non-empty object")
    categories: Dict[str, RetentionCategory] = {}
    for key, value in raw_categories.items():
        category_key = str(key).strip()
        if not category_key:
            raise ValueError("backup_policy.categories contains an empty key")
        categories[category_key] = _parse_category(category_key, value)

    raw_rules = merged.get("artifact_rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError("backup_policy.artifact_rules must be a list")
    rules = [_parse_artifact_rule(rule, categories) for rule in raw_rules]

    raw_drill = merged.get("restore_drill", {})
    if not isinstance(raw_drill, dict):
        raise ValueError("backup_policy.restore_drill must be an object")
    temp_restore_root = str(raw_drill.get("temp_restore_root", "")).strip()
    report_json_path = str(raw_drill.get("report_json_path", "")).strip()
    report_markdown_path_raw = raw_drill.get("report_markdown_path")
    report_markdown_path = (
        str(report_markdown_path_raw).strip() if report_markdown_path_raw else None
    )
    if not temp_restore_root:
        raise ValueError("backup_policy.restore_drill.temp_restore_root is required")
    if not report_json_path:
        raise ValueError("backup_policy.restore_drill.report_json_path is required")
    verification_checks = raw_drill.get("verification_checks", {})
    if verification_checks is None:
        verification_checks = {}
    if not isinstance(verification_checks, dict):
        raise ValueError(
            "backup_policy.restore_drill.verification_checks must be an object"
        )
    restore_drill = RestoreDrillConfig(
        temp_restore_root=temp_restore_root,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        verification_checks=verification_checks,
    )

    raw_ownership_map = merged.get("ownership_map", {})
    if not isinstance(raw_ownership_map, dict):
        raise ValueError("backup_policy.ownership_map must be an object")
    ownership_map = {str(k): str(v) for k, v in raw_ownership_map.items()}

    policy = BackupPolicy(
        categories=categories,
        artifact_rules=rules,
        restore_drill=restore_drill,
        ownership_map=ownership_map,
    )
    logger.debug(
        f"Loaded backup policy: {len(policy.categories)} categories, "
        f"{len(policy.artifact_rules)} artifact rules"
    )
    return policy


def resolve_policy_path(project_root: Path, configured_path: str) -> Path:
    """Resolve a policy path relative to project_root when needed."""
    candidate = Path(configured_path)
    if candidate.is_absolute():
        return candidate
    return (project_root / candidate).resolve()
