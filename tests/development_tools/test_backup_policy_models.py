"""Tests for development_tools/shared/backup_policy_models.py."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


policy_models = load_development_tools_module("shared.backup_policy_models")


@pytest.mark.unit
def test_as_int_validates_type_and_minimum():
    assert policy_models._as_int(3, "x", 0) == 3
    with pytest.raises(ValueError, match="must be an integer"):
        policy_models._as_int("3", "x", 0)
    with pytest.raises(ValueError, match="must be >= 0"):
        policy_models._as_int(-1, "x", 0)


@pytest.mark.unit
def test_parse_category_valid_and_invalid_inputs():
    parsed = policy_models._parse_category(
        "B",
        {
            "description": "Engineering artifacts",
            "max_age_days": 30,
            "min_keep": 2,
            "max_keep": 10,
            "local_retention_enabled": False,
        },
    )
    assert parsed.key == "B"
    assert parsed.max_age_days == 30
    assert parsed.local_retention_enabled is False

    with pytest.raises(ValueError, match="must be an object"):
        policy_models._parse_category("B", [])
    with pytest.raises(ValueError, match="min_keep must be <= max_keep"):
        policy_models._parse_category("B", {"min_keep": 5, "max_keep": 1})


@pytest.mark.unit
def test_parse_artifact_rule_happy_path_and_validation():
    categories = {
        "B": policy_models.RetentionCategory(
            key="B",
            description="Engineering",
            max_age_days=90,
            min_keep=1,
            max_keep=10,
            local_retention_enabled=True,
        )
    }

    rule = policy_models._parse_artifact_rule(
        {
            "name": "reports",
            "paths": ["development_tools/reports/*.json", "  "],
            "category": "B",
            "ownership": "development_tools",
            "producer": "audit",
            "trigger": "audit",
        },
        categories,
    )
    assert rule.name == "reports"
    assert rule.category == "B"
    assert rule.paths == ["development_tools/reports/*.json"]

    with pytest.raises(ValueError, match="name is required"):
        policy_models._parse_artifact_rule({"paths": ["x"], "category": "B"}, categories)
    with pytest.raises(ValueError, match="non-empty list"):
        policy_models._parse_artifact_rule(
            {"name": "x", "paths": [], "category": "B"}, categories
        )
    with pytest.raises(ValueError, match="unknown category"):
        policy_models._parse_artifact_rule(
            {"name": "x", "paths": ["a"], "category": "Z"}, categories
        )
    with pytest.raises(ValueError, match="ownership must be one of"):
        policy_models._parse_artifact_rule(
            {"name": "x", "paths": ["a"], "category": "B", "ownership": "custom"},
            categories,
        )


@pytest.mark.unit
def test_merge_policy_dict_preserves_defaults_and_overrides():
    merged = policy_models._merge_policy_dict(
        {
            "categories": {"B": {"min_keep": 99}, "Z": {"description": "Custom"}},
            "artifact_rules": [{"name": "r1"}],
            "restore_drill": {"temp_restore_root": "tmp/custom"},
            "ownership_map": {"ops": "Operations team"},
        }
    )

    assert merged["categories"]["B"]["min_keep"] == 99
    assert merged["categories"]["A"]["description"]  # default preserved
    assert merged["categories"]["Z"]["description"] == "Custom"
    assert merged["artifact_rules"] == [{"name": "r1"}]
    assert merged["restore_drill"]["temp_restore_root"] == "tmp/custom"
    assert merged["ownership_map"]["ops"] == "Operations team"


@pytest.mark.unit
def test_load_backup_policy_parses_full_config(monkeypatch):
    raw_policy = {
        "categories": {
            "B": {
                "description": "Engineering artifacts",
                "max_age_days": 45,
                "min_keep": 2,
                "max_keep": 15,
            }
        },
        "artifact_rules": [
            {
                "name": "reports",
                "paths": ["development_tools/reports/*.json"],
                "category": "B",
                "ownership": "development_tools",
            }
        ],
        "restore_drill": {
            "temp_restore_root": "development_tools/reports/restore_tmp",
            "report_json_path": "development_tools/reports/jsons/drill.json",
            "report_markdown_path": "development_tools/reports/drill.md",
            "verification_checks": {"required_paths": ["users"], "min_file_count": 1},
        },
        "ownership_map": {"development_tools": "Eng"},
    }

    monkeypatch.setattr(policy_models.config, "load_external_config", lambda: None)
    monkeypatch.setattr(policy_models.config, "get_backup_policy_config", lambda: raw_policy)

    policy = policy_models.load_backup_policy()

    assert "B" in policy.categories
    assert len(policy.artifact_rules) == 1
    assert policy.restore_drill.report_markdown_path.endswith("drill.md")
    assert policy.ownership_map["development_tools"] == "Eng"


@pytest.mark.unit
def test_load_backup_policy_raises_for_invalid_shapes(monkeypatch):
    monkeypatch.setattr(policy_models.config, "load_external_config", lambda: None)

    monkeypatch.setattr(
        policy_models.config, "get_backup_policy_config", lambda: {"categories": {"": {}}}
    )
    with pytest.raises(ValueError, match="contains an empty key"):
        policy_models.load_backup_policy()

    monkeypatch.setattr(
        policy_models.config,
        "get_backup_policy_config",
        lambda: {
            "artifact_rules": ["not-an-object"],
            "restore_drill": {"temp_restore_root": "tmp", "report_json_path": "a.json"},
        },
    )
    with pytest.raises(ValueError, match="Each artifact rule must be an object"):
        policy_models.load_backup_policy()

    monkeypatch.setattr(
        policy_models.config,
        "get_backup_policy_config",
        lambda: {
            "artifact_rules": [],
            "restore_drill": {
                "temp_restore_root": "",
                "report_json_path": "x.json",
            },
        },
    )
    with pytest.raises(ValueError, match="temp_restore_root is required"):
        policy_models.load_backup_policy()

    monkeypatch.setattr(
        policy_models.config,
        "get_backup_policy_config",
        lambda: {
            "artifact_rules": [],
            "restore_drill": {
                "temp_restore_root": "tmp",
                "report_json_path": "",
            },
        },
    )
    with pytest.raises(ValueError, match="report_json_path is required"):
        policy_models.load_backup_policy()


@pytest.mark.unit
def test_load_backup_policy_verification_checks_must_be_dict(monkeypatch):
    monkeypatch.setattr(policy_models.config, "load_external_config", lambda: None)
    monkeypatch.setattr(
        policy_models.config,
        "get_backup_policy_config",
        lambda: {
            "artifact_rules": [],
            "restore_drill": {
                "temp_restore_root": "tmp",
                "report_json_path": "x.json",
                "verification_checks": [],
            },
        },
    )
    with pytest.raises(ValueError, match="verification_checks must be an object"):
        policy_models.load_backup_policy()


@pytest.mark.unit
def test_resolve_policy_path_relative_and_absolute(tmp_path):
    absolute = (tmp_path / "x" / "policy.json").resolve()
    assert policy_models.resolve_policy_path(tmp_path, str(absolute)) == absolute
    rel = policy_models.resolve_policy_path(tmp_path, "development_tools/config/policy.json")
    assert rel == (tmp_path / "development_tools/config/policy.json").resolve()
