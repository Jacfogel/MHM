"""
Tests for regenerate_coverage_metrics.py.

Tests coverage analysis, parsing, HTML generation, and artifact management.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the module using the helper
coverage_module = load_development_tools_module("regenerate_coverage_metrics")

CoverageMetricsRegenerator = coverage_module.CoverageMetricsRegenerator


class TestCoverageParsing:
    """Test coverage output parsing."""
    
    @pytest.mark.unit
    def test_parse_coverage_output_extracts_metrics(self, demo_project_root):
        """Test that coverage output is parsed correctly."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Sample coverage output
        sample_output = """Name                      Stmts   Miss  Cover
----------------------------------------------------
demo_module.py               20      5    75%
demo_module2.py              15      3    80%
----------------------------------------------------
TOTAL                        35      8    77%
"""
        
        coverage_data = regenerator.parse_coverage_output(sample_output)
        
        # Should extract module data
        assert len(coverage_data) > 0
        if 'demo_module.py' in coverage_data:
            assert coverage_data['demo_module.py']['coverage'] == 75
    
    @pytest.mark.unit
    def test_extract_overall_coverage(self, demo_project_root):
        """Test that overall coverage percentage is extracted."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        sample_output = """TOTAL                        100     20    80%
"""
        
        overall = regenerator.extract_overall_coverage(sample_output)
        
        # Should extract overall coverage
        assert 'overall_coverage' in overall
        assert overall['overall_coverage'] == 80.0
        assert overall['total_statements'] == 100
        assert overall['total_missed'] == 20


class TestCoverageCategorization:
    """Test module categorization by coverage."""
    
    @pytest.mark.unit
    def test_categorize_modules_by_coverage(self, demo_project_root):
        """Test that modules are categorized correctly."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        coverage_data = {
            'excellent_module.py': {'coverage': 85},
            'good_module.py': {'coverage': 70},
            'moderate_module.py': {'coverage': 50},
            'needs_work_module.py': {'coverage': 30},
            'critical_module.py': {'coverage': 10},
        }
        
        categories = regenerator.categorize_modules(coverage_data)
        
        # Should categorize correctly
        assert 'excellent' in categories
        assert 'good' in categories
        assert 'moderate' in categories
        assert 'needs_work' in categories
        assert 'critical' in categories
        
        assert 'excellent_module.py' in categories['excellent']
        assert 'good_module.py' in categories['good']
        assert 'moderate_module.py' in categories['moderate']
        assert 'needs_work_module.py' in categories['needs_work']
        assert 'critical_module.py' in categories['critical']


class TestCoverageSummary:
    """Test coverage summary generation."""
    
    @pytest.mark.unit
    def test_generate_coverage_summary_structure(self, demo_project_root):
        """Test that summary has expected structure."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        coverage_data = {
            'demo_module.py': {
                'statements': 20,
                'missed': 5,
                'coverage': 75,
                'covered': 15,
                'missing_lines': []
            }
        }
        
        overall_data = {
            'total_statements': 20,
            'total_missed': 5,
            'overall_coverage': 75.0
        }
        
        summary = regenerator.generate_coverage_summary(coverage_data, overall_data)
        
        # Should have expected content
        assert 'Overall Coverage' in summary
        assert '75' in summary or '75.0' in summary
        assert 'Total Statements' in summary


class TestCoverageAnalysis:
    """Test coverage analysis execution."""
    
    @pytest.mark.unit
    @pytest.mark.slow
    def test_run_coverage_analysis_executes_pytest(self, demo_project_root, temp_coverage_dir):
        """Test that coverage analysis runs pytest correctly."""
        regenerator = CoverageMetricsRegenerator(
            str(demo_project_root),
            parallel=False  # Disable parallel for simpler testing
        )
        
        # Mock subprocess to avoid actually running pytest
        with patch('subprocess.run') as mock_run:
            # Create mock result
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = """TOTAL                        100     20    80%
"""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Mock file operations
            with patch.object(regenerator, 'finalize_coverage_outputs'):
                results = regenerator.run_coverage_analysis()
                
                # Should return results structure
                assert isinstance(results, dict)
                assert 'modules' in results or 'overall' in results


class TestCoverageArtifacts:
    """Test coverage artifact management."""
    
    @pytest.mark.unit
    def test_configure_coverage_paths_from_config(self, demo_project_root, temp_output_dir):
        """Test that paths are loaded from coverage.ini."""
        # Create a mock coverage.ini
        config_file = demo_project_root / "coverage.ini"
        config_content = """[run]
data_file = .coverage

[html]
directory = htmlcov
"""
        config_file.write_text(config_content, encoding='utf-8')
        
        try:
            regenerator = CoverageMetricsRegenerator(str(demo_project_root))
            
            # Should use paths from config
            assert regenerator.coverage_data_file.name == '.coverage'
            assert regenerator.coverage_html_dir.name == 'htmlcov'
        finally:
            # Clean up
            if config_file.exists():
                config_file.unlink()
    
    @pytest.mark.unit
    def test_cleanup_coverage_shards(self, demo_project_root, temp_coverage_dir):
        """Test that coverage shard files are cleaned up."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Create some mock shard files
        shard1 = demo_project_root / ".coverage.1"
        shard2 = demo_project_root / ".coverage.2"
        shard1.write_text("test", encoding='utf-8')
        shard2.write_text("test", encoding='utf-8')
        
        try:
            # Run cleanup
            regenerator._cleanup_coverage_shards()
            
            # Shards should be removed
            assert not shard1.exists()
            assert not shard2.exists()
        finally:
            # Clean up if still exists
            if shard1.exists():
                shard1.unlink()
            if shard2.exists():
                shard2.unlink()


class TestCoverageJSON:
    """Test coverage JSON loading."""
    
    @pytest.mark.unit
    def test_load_coverage_json(self, demo_project_root, temp_output_dir):
        """Test loading coverage data from JSON."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Create a sample coverage JSON
        json_file = temp_output_dir / "coverage.json"
        json_data = {
            'files': {
                'demo_module.py': {
                    'summary': {
                        'num_statements': 20,
                        'covered_lines': 15,
                        'missing_lines': 5,
                        'percent_covered': 75.0
                    },
                    'missing_lines': [10, 11, 12, 13, 14]
                }
            }
        }
        json_file.write_text(json.dumps(json_data), encoding='utf-8')
        
        coverage_data = regenerator._load_coverage_json(json_file)
        
        # Should load coverage data
        assert len(coverage_data) > 0
        # The key might be normalized (backslashes on Windows)
        keys = list(coverage_data.keys())
        assert any('demo_module' in key for key in keys)


class TestCoveragePlanUpdate:
    """Test coverage plan file updates."""
    
    @pytest.mark.unit
    def test_update_coverage_plan_updates_file(self, demo_project_root, temp_output_dir):
        """Test that coverage plan file is updated."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        regenerator.coverage_plan_file = temp_output_dir / "TEST_COVERAGE_EXPANSION_PLAN.md"
        
        coverage_data = {
            'demo_module.py': {
                'statements': 20,
                'missed': 5,
                'coverage': 75,
                'covered': 15,
                'missing_lines': []
            }
        }
        
        overall_data = {
            'total_statements': 20,
            'total_missed': 5,
            'overall_coverage': 75.0
        }
        
        summary = regenerator.generate_coverage_summary(coverage_data, overall_data)
        success = regenerator.update_coverage_plan(summary)
        
        # Should update the file
        assert success is True
        assert regenerator.coverage_plan_file.exists()
        
        # File should contain summary content
        content = regenerator.coverage_plan_file.read_text(encoding='utf-8')
        assert 'Overall Coverage' in content or '75' in content

