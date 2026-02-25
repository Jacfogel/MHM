"""Tests for docs/fix_documentation.py dispatcher behavior."""

from types import SimpleNamespace

import pytest
import argparse

from tests.development_tools.conftest import load_development_tools_module


@pytest.mark.unit
def test_main_returns_1_when_no_fix_flags_selected(monkeypatch):
    """Dispatcher should print help and exit non-zero when no operations are selected."""
    module = load_development_tools_module("docs.fix_documentation")

    def fake_parse_args(self):
        return SimpleNamespace(
            add_addresses=False,
            fix_ascii=False,
            number_headings=False,
            convert_links=False,
            all=False,
            full=False,
            dry_run=False,
        )

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse_args)

    result = module.main()

    assert result == 1


@pytest.mark.unit
def test_main_runs_add_addresses_with_dry_run(monkeypatch):
    """Dispatcher should call add-addresses fixer with requested dry-run mode."""
    module = load_development_tools_module("docs.fix_documentation")

    def fake_parse_args(self):
        return SimpleNamespace(
            add_addresses=True,
            fix_ascii=False,
            number_headings=False,
            convert_links=False,
            all=False,
            full=False,
            dry_run=True,
        )

    class DummyAddressFixer:
        def __init__(self):
            self.called = False

        def fix_add_addresses(self, dry_run=False):
            self.called = True
            assert dry_run is True
            return {"updated": 0, "skipped": 2, "errors": 0}

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse_args)
    monkeypatch.setattr(module, "DocumentationAddressFixer", DummyAddressFixer)

    result = module.main()

    assert result == 0


@pytest.mark.unit
def test_main_runs_all_fixers_with_full_alias(monkeypatch):
    """`--full` should behave like `--all` and execute all fixer paths."""
    module = load_development_tools_module("docs.fix_documentation")
    calls = []

    def fake_parse_args(self):
        return SimpleNamespace(
            add_addresses=False,
            fix_ascii=False,
            number_headings=False,
            convert_links=False,
            all=False,
            full=True,
            dry_run=False,
        )

    class DummyAddressFixer:
        def fix_add_addresses(self, dry_run=False):
            calls.append(("addresses", dry_run))
            return {"updated": 1, "skipped": 0, "errors": 0}

    class DummyASCIIFixer:
        def fix_ascii(self, dry_run=False):
            calls.append(("ascii", dry_run))
            return {"files_updated": 1, "replacements_made": 1, "errors": 0}

    class DummyHeadingFixer:
        def fix_number_headings(self, dry_run=False):
            calls.append(("headings", dry_run))
            return {"files_updated": 1, "issues_fixed": 1, "errors": 0}

    class DummyLinkFixer:
        def fix_convert_links(self, dry_run=False):
            calls.append(("links", dry_run))
            return {"files_updated": 1, "changes_made": 1, "errors": 0}

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse_args)
    monkeypatch.setattr(module, "DocumentationAddressFixer", DummyAddressFixer)
    monkeypatch.setattr(module, "DocumentationASCIIFixer", DummyASCIIFixer)
    monkeypatch.setattr(module, "DocumentationHeadingFixer", DummyHeadingFixer)
    monkeypatch.setattr(module, "DocumentationLinkFixer", DummyLinkFixer)

    result = module.main()

    assert result == 0
    assert [name for name, _ in calls] == ["addresses", "ascii", "headings", "links"]


@pytest.mark.unit
def test_main_returns_1_when_any_fixer_reports_errors(monkeypatch):
    """Dispatcher should return non-zero aggregate status when errors are reported."""
    module = load_development_tools_module("docs.fix_documentation")

    def fake_parse_args(self):
        return SimpleNamespace(
            add_addresses=False,
            fix_ascii=True,
            number_headings=False,
            convert_links=False,
            all=False,
            full=False,
            dry_run=False,
        )

    class DummyASCIIFixer:
        def fix_ascii(self, dry_run=False):
            assert dry_run is False
            return {"files_updated": 1, "replacements_made": 1, "errors": 2}

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse_args)
    monkeypatch.setattr(module, "DocumentationASCIIFixer", DummyASCIIFixer)

    result = module.main()

    assert result == 1
