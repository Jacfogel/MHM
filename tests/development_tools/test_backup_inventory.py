"""Tests for development_tools/shared/backup_inventory.py."""


import pytest

from tests.development_tools.conftest import load_development_tools_module


backup_inventory_module = load_development_tools_module("shared.backup_inventory")
policy_models_module = load_development_tools_module("shared.backup_policy_models")

ArtifactRule = policy_models_module.ArtifactRule
BackupPolicy = policy_models_module.BackupPolicy
RestoreDrillConfig = policy_models_module.RestoreDrillConfig
RetentionCategory = policy_models_module.RetentionCategory


def _build_policy(rules):
    categories = {
        "B": RetentionCategory(
            key="B",
            description="Engineering artifacts",
            max_age_days=90,
            min_keep=2,
            max_keep=10,
            local_retention_enabled=True,
        )
    }
    return BackupPolicy(
        categories=categories,
        artifact_rules=rules,
        restore_drill=RestoreDrillConfig(
            temp_restore_root="tmp",
            report_json_path="report.json",
            report_markdown_path=None,
            verification_checks={},
        ),
        ownership_map={"development_tools": "owner"},
    )


@pytest.mark.unit
def test_pattern_matches_supports_relative_and_absolute_globs(tmp_path):
    """Pattern matching should work for project-relative and absolute patterns."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    target = docs_dir / "a.md"
    target.write_text("x", encoding="utf-8")

    relative = backup_inventory_module._pattern_matches(tmp_path, "docs/*.md")
    absolute = backup_inventory_module._pattern_matches(
        tmp_path, str(docs_dir / "*.md")
    )

    assert target in relative
    assert target in absolute


@pytest.mark.unit
def test_collect_files_for_rule_deduplicates_file_matches(tmp_path):
    """Collecting files should avoid duplicates when patterns overlap."""
    report_dir = tmp_path / "development_tools" / "reports"
    report_dir.mkdir(parents=True)
    json_file = report_dir / "analysis.json"
    json_file.write_text("{}", encoding="utf-8")

    rule = ArtifactRule(
        name="reports",
        paths=[
            "development_tools/reports",
            "development_tools/reports/*.json",
            str(json_file),
        ],
        category="B",
    )

    files = backup_inventory_module._collect_files_for_rule(tmp_path, rule)

    assert len(files) == 1
    assert files[0] == json_file


@pytest.mark.unit
def test_build_backup_inventory_populates_summary_and_rule_fields(tmp_path):
    """Inventory should report counts, categories, and latest modified timestamps."""
    reports_dir = tmp_path / "development_tools" / "reports"
    reports_dir.mkdir(parents=True)
    existing = reports_dir / "analysis.json"
    existing.write_text("{}", encoding="utf-8")

    rules = [
        ArtifactRule(
            name="reports",
            paths=["development_tools/reports/*.json"],
            category="B",
            enabled=True,
            producer="audit",
            trigger="audit",
            restore_path="development_tools/reports/",
            notes="Keep recent report artifacts",
        ),
        ArtifactRule(
            name="missing",
            paths=["development_tools/reports/*.does-not-exist"],
            category="B",
            enabled=False,
        ),
    ]
    policy = _build_policy(rules)

    inventory = backup_inventory_module.build_backup_inventory(tmp_path, policy)

    assert inventory["summary"]["total_rules"] == 2
    assert inventory["summary"]["enabled_rules"] == 1
    assert inventory["summary"]["rules_with_files"] == 1
    assert inventory["categories"]["B"]["description"] == "Engineering artifacts"

    report_rule = next(rule for rule in inventory["rules"] if rule["name"] == "reports")
    missing_rule = next(rule for rule in inventory["rules"] if rule["name"] == "missing")

    assert report_rule["file_count"] == 1
    assert isinstance(report_rule["latest_modified"], str)
    assert "T" in report_rule["latest_modified"]
    assert report_rule["restore_path"] == "development_tools/reports/"
    assert report_rule["notes"] == "Keep recent report artifacts"

    assert missing_rule["file_count"] == 0
    assert missing_rule["latest_modified"] is None
