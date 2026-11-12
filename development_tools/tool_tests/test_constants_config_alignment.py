"""
Alignment tests: constants / config derived_prefix_excludes, test_markers, path_drift.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_get_constants_config_derived_prefix_excludes():
    from development_tools import config

    config.load_external_config()
    cc = config.get_constants_config()
    assert "derived_prefix_excludes" in cc
    dpe = cc["derived_prefix_excludes"]
    assert set(dpe) == {"scan", "core", "project"}
    assert "notebook" in dpe["scan"]
    assert "tests" in dpe["core"] and "tests" not in dpe["scan"]


@pytest.mark.unit
def test_get_path_drift_config_normalizes_lists():
    from development_tools import config

    config.load_external_config()
    pd = config.get_path_drift_config()
    assert isinstance(pd.get("legacy_documentation_files"), list)
    assert isinstance(pd.get("ignored_path_patterns"), list)


@pytest.mark.unit
def test_constants_test_markers_match_get_test_markers_config():
    """Single canonical source: get_test_markers_config; constants re-exports same values."""
    from development_tools import config

    config.load_external_config()
    from development_tools.shared.constants import (
        TEST_CATEGORY_MARKERS,
        TEST_MARKER_AI_PATH_TOKENS,
        TEST_MARKER_DIRECTORY_MAP,
        TEST_MARKER_TRANSIENT_PATH_MARKERS,
    )

    tm = config.get_test_markers_config()
    assert tuple(tm["categories"]) == TEST_CATEGORY_MARKERS
    assert tm["directory_to_marker"] == TEST_MARKER_DIRECTORY_MAP
    assert tuple(tm["transient_data_path_markers"]) == TEST_MARKER_TRANSIENT_PATH_MARKERS
    assert tuple(tm["ai_path_tokens"]) == TEST_MARKER_AI_PATH_TOKENS


@pytest.mark.unit
def test_deprecated_constants_test_marker_keys_warn_once():
    import sys
    import warnings

    import development_tools.config as dt_config

    dt_config.load_external_config()
    mod = sys.modules["development_tools.config.config"]
    previous_warned = mod._warned_deprecated_test_marker_keys
    prev_get = mod._get_external_value

    try:
        mod._warned_deprecated_test_marker_keys = False  # type: ignore[attr-defined]

        def fake_get(key: str, default):
            if key == "constants":
                return {
                    "test_category_markers": ["unit"],
                    "paired_docs": {},
                }
            return default

        mod._get_external_value = fake_get  # type: ignore[attr-defined]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mod.get_constants_config()
            assert any(x.category is DeprecationWarning for x in w)
        with warnings.catch_warnings(record=True) as w2:
            warnings.simplefilter("always")
            mod.get_constants_config()
            assert not w2
    finally:
        mod._get_external_value = prev_get  # type: ignore[attr-defined]
        mod._warned_deprecated_test_marker_keys = previous_warned  # type: ignore[attr-defined]


@pytest.mark.unit
def test_ignored_path_patterns_include_config_fragments():
    from development_tools import config

    config.load_external_config()
    from development_tools.shared.constants import IGNORED_PATH_PATTERNS

    assert "paths" in IGNORED_PATH_PATTERNS
    pd = config.get_path_drift_config()
    for frag in pd.get("ignored_path_patterns", []):
        assert frag in IGNORED_PATH_PATTERNS
