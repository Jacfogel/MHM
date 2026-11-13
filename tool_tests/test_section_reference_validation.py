"""Read-only section inventories distinguish broken links from review hints."""

import pytest
import json
from types import SimpleNamespace

from development_tools.docs.section_reference_validation import (
    heading_inventory,
    scan_section_references,
)


@pytest.mark.unit
def test_heading_anchors_include_duplicates_code_and_unicode():
    headings = heading_inventory(
        "## 1. `Code` & Café\n## 1. `Code` & Café\n~~~\n## Fake\n~~~\n"
        '<a id="custom"></a>\n'
    )
    assert set(headings) == {"1-code--café", "1-code--café-1", "custom"}


@pytest.mark.unit
def test_inventory_reports_exact_targets_without_modifying_sources(tmp_path):
    target = tmp_path / "guide.md"
    target.write_text("## 2. Rules\n", encoding="utf-8")
    source = tmp_path / "source.md"
    content = (
        "[Navigation](guide.md)\n"
        'See section 2. "Rules" in [Guide](guide.md).\n'
        "[Good](guide.md#2-rules) [Broken](guide.md#old)\n"
        "[Remote](https://example.com/guide.md#old)\n"
        "```md\n[Example](guide.md#old)\n```\n"
        "> **Pair**: [Guide](guide.md#old)\n"
        "`[Inline example](guide.md#old)`\n"
        "[Local](#own)\n## Own\n"
    )
    source.write_text(content, encoding="utf-8")
    records = scan_section_references(tmp_path, ["source.md"])
    assert [r["status"] for r in records] == [
        "unanchored_section_reference", "resolved", "unresolved_anchor", "resolved"
    ]
    assert records[0]["candidate_headings"] == ["2. Rules"]
    assert records[0]["line"] == 2
    assert records[1]["heading"] == "2. Rules"
    assert source.read_text(encoding="utf-8") == content


@pytest.mark.unit
def test_inventory_skips_history_generated_and_outside_root(tmp_path):
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "old.md").write_text("[Old](#gone)")
    (tmp_path / "generated.md").write_text(
        "> **Purpose**: Auto-generated report\n[Bad](#gone)"
    )
    (tmp_path / "source.md").write_text("[Outside](../outside.md#gone)")
    assert scan_section_references(tmp_path, [
        "archive/old.md", "generated.md", "source.md", "../outside.md"
    ]) == []


@pytest.mark.unit
def test_cli_inventory_is_advisory_and_json_serializable(tmp_path, monkeypatch, capsys):
    from development_tools.docs import analyze_documentation_sync as module

    (tmp_path / "source.md").write_text("[Broken](#gone)")
    checker = SimpleNamespace(
        project_root=tmp_path, paired_docs={},
        run_checks=lambda: {"summary": {"status": "PASS", "total_issues": 0}, "details": {}},
    )
    monkeypatch.setattr(module, "DocumentationSyncChecker", lambda: checker)
    monkeypatch.setattr("sys.argv", ["doc-sync", "--json", "--check-section-links",
                                    "--section-path", "source.md"])
    module.main()
    result = json.loads(capsys.readouterr().out)
    assert result["summary"]["status"] == "PASS"
    assert result["summary"]["section_reference_hint_count"] == 1
    assert result["details"]["section_references"][0]["status"] == "unresolved_anchor"
