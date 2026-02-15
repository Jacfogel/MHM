"""Tests for development-tools demo fixture status snapshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest


@pytest.mark.unit
def test_fixture_status_files_have_valid_metadata() -> None:
    """
    Fixture status snapshots should have parseable metadata and no hard timestamp coupling.
    """
    fixture_root = Path("tests/fixtures/development_tools_demo")
    files = [
        fixture_root / "AI_STATUS.md",
        fixture_root / "AI_PRIORITIES.md",
        fixture_root / "consolidated_report.md",
    ]

    for file_path in files:
        assert file_path.exists(), f"Missing fixture status file: {file_path}"
        text = file_path.read_text(encoding="utf-8")

        assert "> **Generated**: This file is auto-generated." in text
        marker = "> **Last Generated**: "
        assert marker in text, f"Missing timestamp metadata in {file_path}"

        timestamp = text.split(marker, 1)[1].splitlines()[0].strip()
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
