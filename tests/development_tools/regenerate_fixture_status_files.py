#!/usr/bin/env python3
"""Regenerate fixture status snapshots for development-tools tests."""

from __future__ import annotations

import shutil
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    project_root = Path(__file__).resolve().parents[2]
    fixture_root = project_root / "tests" / "fixtures" / "development_tools_demo"

    if not fixture_root.exists():
        logger.error(f"Fixture root not found: {fixture_root}")
        return 1

    sys.path.insert(0, str(project_root))
    from development_tools.reports.generate_consolidated_report import (
        generate_consolidated_reports,
    )

    generated = generate_consolidated_reports(project_root=str(fixture_root))

    source_to_target = {
        generated["ai_status"]: fixture_root / "AI_STATUS.md",
        generated["ai_priorities"]: fixture_root / "AI_PRIORITIES.md",
        generated["consolidated_report"]: fixture_root / "consolidated_report.txt",
    }

    for source, target in source_to_target.items():
        source_path = Path(source)
        if not source_path.exists():
            logger.error(f"Generated source file missing: {source_path}")
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        logger.info(f"Updated fixture snapshot: {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
