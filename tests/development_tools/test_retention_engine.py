"""Tests for development_tools.shared.retention_engine."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from development_tools.shared.backup_policy_models import (
    ArtifactRule,
    BackupPolicy,
    RestoreDrillConfig,
    RetentionCategory,
)
from development_tools.shared.retention_engine import (
    _pattern_matches,
    apply_retention_plan,
    build_retention_plan,
)


def _build_policy(
    *,
    max_age_days: int | None = None,
    min_keep: int = 0,
    max_keep: int = 0,
    local_retention_enabled: bool = True,
    rules: list[ArtifactRule] | None = None,
) -> BackupPolicy:
    category = RetentionCategory(
        key="B",
        description="Engineering artifacts",
        max_age_days=max_age_days,
        min_keep=min_keep,
        max_keep=max_keep,
        local_retention_enabled=local_retention_enabled,
    )
    return BackupPolicy(
        categories={"B": category},
        artifact_rules=rules or [],
        restore_drill=RestoreDrillConfig(
            temp_restore_root="tmp",
            report_json_path="report.json",
            verification_checks={},
        ),
        ownership_map={},
    )


def _touch_file(path: Path, age_days: float = 0.0, size_bytes: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size_bytes)
    if age_days <= 0:
        return
    ts = time.time() - (age_days * 86400.0)
    path.touch()
    import os

    os.utime(path, (ts, ts))


@pytest.mark.unit
def test_pattern_matches_handles_relative_and_absolute_paths(tmp_path: Path) -> None:
    target = tmp_path / "logs" / "artifact.log"
    _touch_file(target)

    relative_matches = _pattern_matches(tmp_path, "logs/*.log")
    absolute_matches = _pattern_matches(tmp_path, str(target))

    assert target in relative_matches
    assert absolute_matches == [target]


@pytest.mark.unit
def test_build_retention_plan_applies_count_limit(tmp_path: Path) -> None:
    target_dir = tmp_path / "artifacts"
    _touch_file(target_dir / "newest.log", age_days=0.1)
    _touch_file(target_dir / "middle.log", age_days=1.0)
    _touch_file(target_dir / "oldest.log", age_days=2.0)

    rule = ArtifactRule(
        name="logs",
        paths=["artifacts/*.log"],
        category="B",
        ownership="development_tools",
    )
    policy = _build_policy(max_age_days=None, min_keep=0, max_keep=2, rules=[rule])

    plan = build_retention_plan(tmp_path, policy, target_category="B")
    action_paths = {Path(item["file_path"]).name for item in plan["actions"]}

    assert plan["summary"]["planned_actions"] == 1
    assert action_paths == {"oldest.log"}
    assert plan["actions"][0]["reason"] == "count>2"


@pytest.mark.unit
def test_build_retention_plan_applies_age_limit(tmp_path: Path) -> None:
    target_dir = tmp_path / "archives"
    _touch_file(target_dir / "fresh.json", age_days=1.0)
    _touch_file(target_dir / "stale.json", age_days=40.0)

    rule = ArtifactRule(
        name="archives",
        paths=["archives/*.json"],
        category="B",
        ownership="development_tools",
    )
    policy = _build_policy(max_age_days=30, min_keep=0, max_keep=10, rules=[rule])

    plan = build_retention_plan(tmp_path, policy, target_category="B")

    assert plan["summary"]["planned_actions"] == 1
    assert Path(plan["actions"][0]["file_path"]).name == "stale.json"
    assert plan["actions"][0]["reason"] == "age>30d"


@pytest.mark.unit
def test_build_retention_plan_respects_disabled_local_retention(tmp_path: Path) -> None:
    _touch_file(tmp_path / "reports" / "status.md", age_days=100.0)
    rule = ArtifactRule(
        name="reports",
        paths=["reports/*.md"],
        category="B",
        ownership="development_tools",
    )
    policy = _build_policy(
        max_age_days=1,
        min_keep=0,
        max_keep=1,
        local_retention_enabled=False,
        rules=[rule],
    )

    plan = build_retention_plan(tmp_path, policy, target_category="B")

    assert plan["summary"]["planned_actions"] == 0
    assert plan["rules"][0]["status"] == "retention_disabled"


@pytest.mark.unit
def test_build_retention_plan_filters_by_owner_and_category(tmp_path: Path) -> None:
    _touch_file(tmp_path / "owned" / "keep.log", age_days=30.0)
    _touch_file(tmp_path / "external" / "skip.log", age_days=30.0)

    eligible_rule = ArtifactRule(
        name="owned",
        paths=["owned/*.log"],
        category="B",
        ownership="development_tools",
    )
    wrong_owner_rule = ArtifactRule(
        name="external",
        paths=["external/*.log"],
        category="B",
        ownership="core",
    )
    wrong_category_rule = ArtifactRule(
        name="wrong_category",
        paths=["external/*.log"],
        category="A",
        ownership="development_tools",
    )

    policy = _build_policy(
        max_age_days=1,
        min_keep=0,
        max_keep=1,
        rules=[eligible_rule, wrong_owner_rule, wrong_category_rule],
    )
    policy = BackupPolicy(
        categories={
            "A": RetentionCategory(
                key="A",
                description="Recovery",
                max_age_days=1,
                min_keep=0,
                max_keep=1,
                local_retention_enabled=True,
            ),
            "B": policy.categories["B"],
        },
        artifact_rules=policy.artifact_rules,
        restore_drill=policy.restore_drill,
        ownership_map=policy.ownership_map,
    )

    plan = build_retention_plan(tmp_path, policy, target_category="B")

    assert plan["summary"]["rules_scanned"] == 1
    assert plan["rules"][0]["rule"] == "owned"


@pytest.mark.unit
def test_apply_retention_plan_dry_run_marks_would_delete() -> None:
    plan = {
        "actions": [
            {"file_path": "C:/tmp/one.log", "reason": "count>1"},
            {"file_path": "C:/tmp/two.log", "reason": "age>7d"},
        ]
    }

    result = apply_retention_plan(plan, dry_run=True)

    assert result["summary"]["attempted"] == 2
    assert result["summary"]["deleted"] == 0
    assert all(item["status"] == "would_delete" for item in result["actions"])


@pytest.mark.unit
def test_apply_retention_plan_deletes_and_skips_missing(tmp_path: Path) -> None:
    existing = tmp_path / "delete_me.log"
    _touch_file(existing, size_bytes=8)
    missing = tmp_path / "missing.log"

    plan = {
        "actions": [
            {"file_path": str(existing), "reason": "count>1"},
            {"file_path": str(missing), "reason": "age>1d"},
        ]
    }

    result = apply_retention_plan(plan, dry_run=False)
    status_by_path = {item["file_path"]: item["status"] for item in result["actions"]}

    assert result["summary"]["attempted"] == 2
    assert result["summary"]["deleted"] == 1
    assert result["summary"]["failed"] == 0
    assert result["summary"]["freed_bytes"] == 8
    assert not existing.exists()
    assert status_by_path[str(existing)] == "deleted"
    assert status_by_path[str(missing)] == "skipped_missing"
