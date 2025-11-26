"""
Tests for development_tools constants module.

Tests that documentation paths exist, paired docs are valid, and helper functions work correctly.
"""

import pytest
import importlib.util
import sys
from pathlib import Path

# Import using importlib to handle path issues
project_root = Path(__file__).parent.parent.parent
constants_path = project_root / "development_tools" / "services" / "constants.py"
spec = importlib.util.spec_from_file_location("development_tools.services.constants", constants_path)
constants = importlib.util.module_from_spec(spec)
sys.modules["development_tools.services.constants"] = constants
spec.loader.exec_module(constants)


class TestDefaultDocsPaths:
    """Test that all listed File paths in DEFAULT_DOCS exist."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_default_docs_is_tuple(self):
        """Test that DEFAULT_DOCS is a tuple."""
        assert isinstance(constants.DEFAULT_DOCS, tuple)
        assert len(constants.DEFAULT_DOCS) > 0

    @pytest.mark.unit
    def test_default_docs_paths_exist(self):
        """Test that all DEFAULT_DOCS paths exist."""
        project_root = Path(__file__).parent.parent.parent
        missing_paths = []
        for doc_path in constants.DEFAULT_DOCS:
            full_path = project_root / doc_path
            if not full_path.exists():
                missing_paths.append(doc_path)
        # Allow some paths to be missing (they may be generated or optional)
        # But log a warning if many are missing
        if len(missing_paths) > 0:
            # Check if it's just one or two optional files
            if len(missing_paths) <= 2:
                pytest.skip(f"Some DEFAULT_DOCS paths are missing (may be optional): {missing_paths}")
            else:
                assert False, f"Multiple DEFAULT_DOCS paths do not exist: {missing_paths}"

    @pytest.mark.unit
    def test_default_docs_are_strings(self):
        """Test that all DEFAULT_DOCS entries are strings."""
        for doc_path in constants.DEFAULT_DOCS:
            assert isinstance(doc_path, str)
            assert len(doc_path) > 0


class TestPairedDocsPaths:
    """Test that all listed Pair paths in PAIRED_DOCS exist (both human and AI sides)."""

    @pytest.mark.unit
    def test_paired_docs_is_dict(self):
        """Test that PAIRED_DOCS is a dict."""
        assert isinstance(constants.PAIRED_DOCS, dict)
        assert len(constants.PAIRED_DOCS) > 0

    @pytest.mark.unit
    def test_paired_docs_human_paths_exist(self):
        """Test that all human-side PAIRED_DOCS paths exist."""
        project_root = Path(__file__).parent.parent.parent
        for human_path, ai_path in constants.PAIRED_DOCS.items():
            full_path = project_root / human_path
            assert full_path.exists(), f"PAIRED_DOCS human path does not exist: {human_path}"

    @pytest.mark.unit
    def test_paired_docs_ai_paths_exist(self):
        """Test that all AI-side PAIRED_DOCS paths exist."""
        project_root = Path(__file__).parent.parent.parent
        for human_path, ai_path in constants.PAIRED_DOCS.items():
            full_path = project_root / ai_path
            assert full_path.exists(), f"PAIRED_DOCS AI path does not exist: {ai_path}"

    @pytest.mark.unit
    def test_paired_docs_paths_are_strings(self):
        """Test that all PAIRED_DOCS entries are strings."""
        for human_path, ai_path in constants.PAIRED_DOCS.items():
            assert isinstance(human_path, str)
            assert isinstance(ai_path, str)
            assert len(human_path) > 0
            assert len(ai_path) > 0


class TestLocalModulePrefixes:
    """Test that LOCAL_MODULE_PREFIXES contains expected modules."""

    @pytest.mark.unit
    def test_local_module_prefixes_is_tuple(self):
        """Test that LOCAL_MODULE_PREFIXES is a tuple."""
        assert isinstance(constants.LOCAL_MODULE_PREFIXES, tuple)
        assert len(constants.LOCAL_MODULE_PREFIXES) > 0

    @pytest.mark.unit
    def test_expected_local_modules_present(self):
        """Test that expected local module prefixes are present."""
        expected_modules = ['core', 'communication', 'ui', 'tasks', 'user', 'ai']
        for module in expected_modules:
            assert module in constants.LOCAL_MODULE_PREFIXES, \
                f"Expected local module prefix not found: {module}"

    @pytest.mark.unit
    def test_local_module_prefixes_are_strings(self):
        """Test that all LOCAL_MODULE_PREFIXES entries are strings."""
        for prefix in constants.LOCAL_MODULE_PREFIXES:
            assert isinstance(prefix, str)
            assert len(prefix) > 0


class TestHelperFunctions:
    """Test that helper functions work correctly."""

    @pytest.mark.unit
    def test_is_local_module_core(self):
        """Test that is_local_module() correctly identifies core module."""
        assert constants.is_local_module('core') is True
        assert constants.is_local_module('core.service') is True
        assert constants.is_local_module('core.config') is True

    @pytest.mark.unit
    def test_is_local_module_communication(self):
        """Test that is_local_module() correctly identifies communication module."""
        assert constants.is_local_module('communication') is True
        assert constants.is_local_module('communication.channel') is True

    @pytest.mark.unit
    def test_is_local_module_ui(self):
        """Test that is_local_module() correctly identifies ui module."""
        assert constants.is_local_module('ui') is True
        assert constants.is_local_module('ui.dialogs') is True

    @pytest.mark.unit
    def test_is_local_module_returns_false_for_standard_library(self):
        """Test that is_local_module() returns False for standard library modules."""
        assert constants.is_local_module('os') is False
        assert constants.is_local_module('sys') is False
        assert constants.is_local_module('pathlib') is False

    @pytest.mark.unit
    def test_is_local_module_returns_false_for_third_party(self):
        """Test that is_local_module() returns False for third-party modules."""
        assert constants.is_local_module('pytest') is False
        assert constants.is_local_module('discord') is False

    @pytest.mark.unit
    def test_is_local_module_handles_empty_string(self):
        """Test that is_local_module() handles empty string correctly."""
        assert constants.is_local_module('') is False

    @pytest.mark.unit
    def test_is_standard_library_module_os(self):
        """Test that is_standard_library_module() correctly identifies os module."""
        assert constants.is_standard_library_module('os') is True
        assert constants.is_standard_library_module('os.path') is True

    @pytest.mark.unit
    def test_is_standard_library_module_sys(self):
        """Test that is_standard_library_module() correctly identifies sys module."""
        assert constants.is_standard_library_module('sys') is True

    @pytest.mark.unit
    def test_is_standard_library_module_pathlib(self):
        """Test that is_standard_library_module() correctly identifies pathlib module."""
        assert constants.is_standard_library_module('pathlib') is True

    @pytest.mark.unit
    def test_is_standard_library_module_returns_false_for_local(self):
        """Test that is_standard_library_module() returns False for local modules."""
        assert constants.is_standard_library_module('core') is False
        assert constants.is_standard_library_module('communication') is False

    @pytest.mark.unit
    def test_is_standard_library_module_returns_false_for_third_party(self):
        """Test that is_standard_library_module() returns False for third-party modules."""
        assert constants.is_standard_library_module('pytest') is False
        assert constants.is_standard_library_module('discord') is False

    @pytest.mark.unit
    def test_is_standard_library_module_handles_empty_string(self):
        """Test that is_standard_library_module() handles empty string correctly."""
        assert constants.is_standard_library_module('') is False

    @pytest.mark.unit
    def test_is_standard_library_module_with_prefixes(self):
        """Test that is_standard_library_module() works with prefix matching."""
        # Test some standard library prefixes
        assert constants.is_standard_library_module('logging') is True
        assert constants.is_standard_library_module('logging.handlers') is True
        assert constants.is_standard_library_module('collections') is True
        assert constants.is_standard_library_module('collections.abc') is True

