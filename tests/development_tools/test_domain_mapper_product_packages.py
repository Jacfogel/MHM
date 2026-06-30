"""Policy: root product packages align with domain_mapper and local_module_prefixes."""

from __future__ import annotations

import configparser
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools import config
from development_tools.tests.domain_mapper import DomainMapper

# Top-level packages with __init__.py that are product code (not infra/meta).
PRODUCT_PACKAGE_ROOTS: frozenset[str] = frozenset(
    {
        "ai",
        "checkins",
        "communication",
        "core",
        "integrations",
        "messages",
        "notebook",
        "scheduler",
        "storage",
        "tasks",
        "ui",
        "user",
    }
)

_PREFIX_EXCLUDES: frozenset[str] = frozenset(
    {"data", "scripts", "tests", "development_tools"}
)


def _root_packages_with_init() -> set[str]:
    found: set[str] = set()
    for child in project_root.iterdir():
        if child.is_dir() and (child / "__init__.py").is_file():
            found.add(child.name)
    return found


@pytest.mark.unit
def test_product_packages_have_domain_mapper_entries() -> None:
    config.load_external_config()
    mapper = DomainMapper(project_root)
    mapped = set(mapper.SOURCE_TO_TEST_MAPPING.keys())
    missing = sorted(PRODUCT_PACKAGE_ROOTS - mapped)
    assert not missing, f"domain_mapper missing product packages: {missing}"


@pytest.mark.unit
def test_product_packages_in_local_module_prefixes() -> None:
    config.load_external_config()
    prefixes = set(config.get_constants_config().get("local_module_prefixes") or [])
    missing = sorted(PRODUCT_PACKAGE_ROOTS - prefixes)
    assert not missing, f"local_module_prefixes missing product packages: {missing}"


@pytest.mark.unit
def test_refactored_packages_resolve_source_domain() -> None:
    config.load_external_config()
    mapper = DomainMapper(project_root)
    for pkg in ("checkins", "messages", "storage"):
        sample = f"{pkg}/__init__.py"
        assert mapper.get_source_domain(sample) == pkg
        changed = mapper.get_changed_domains([sample])
        assert pkg in changed


@pytest.mark.unit
def test_coverage_ini_source_includes_all_product_domains() -> None:
    """coverage.ini [run] source= must list every product package plus development_tools."""
    cov_ini = project_root / "development_tools" / "tests" / "coverage.ini"
    assert cov_ini.is_file(), f"Missing {cov_ini}"
    parser = configparser.ConfigParser()
    parser.read(cov_ini)
    source = {
        s.strip()
        for s in parser.get("run", "source", fallback="").split(",")
        if s.strip()
    }
    expected = set(PRODUCT_PACKAGE_ROOTS) | {"development_tools"}
    missing = sorted(expected - source)
    assert not missing, f"coverage.ini source= missing: {missing}"


@pytest.mark.unit
def test_root_init_packages_covered_by_product_roots_or_excludes() -> None:
    """Every non-excluded root package with __init__.py is listed in PRODUCT_PACKAGE_ROOTS."""
    on_disk = _root_packages_with_init() - _PREFIX_EXCLUDES
    extra = sorted(on_disk - PRODUCT_PACKAGE_ROOTS)
    assert not extra, (
        "Add new product packages to PRODUCT_PACKAGE_ROOTS and domain_mapper config: "
        f"{extra}"
    )
