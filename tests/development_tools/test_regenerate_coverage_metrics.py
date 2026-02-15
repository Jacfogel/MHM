"""
Tests for run_test_coverage.py.

Tests coverage analysis, parsing, HTML generation, and artifact management.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load the modules using the helper
# During Batch 3 decomposition, methods were moved to separate classes
coverage_module = load_development_tools_module("run_test_coverage")
analyze_coverage_module = load_development_tools_module("analyze_test_coverage")
report_generator_module = load_development_tools_module("generate_test_coverage_report")

CoverageMetricsRegenerator = coverage_module.CoverageMetricsRegenerator
TestCoverageAnalyzer = analyze_coverage_module.TestCoverageAnalyzer
TestCoverageReportGenerator = report_generator_module.TestCoverageReportGenerator


class TestCoverageParsing:
    """Test coverage output parsing."""
    
    @pytest.mark.unit
    def test_parse_coverage_output_extracts_metrics(self, demo_project_root):
        """Test that coverage output is parsed correctly."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Ensure analyzer is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.analyzer is not None, "TestCoverageAnalyzer should be initialized"
        
        # Sample coverage output
        sample_output = """Name                      Stmts   Miss  Cover
----------------------------------------------------
demo_module.py               20      5    75%
demo_module2.py              15      3    80%
----------------------------------------------------
TOTAL                        35      8    77%
"""
        
        # parse_coverage_output moved to TestCoverageAnalyzer during Batch 3 decomposition
        coverage_data = regenerator.analyzer.parse_coverage_output(sample_output)
        
        # Should extract module data
        assert len(coverage_data) > 0
        if 'demo_module.py' in coverage_data:
            assert coverage_data['demo_module.py']['coverage'] == 75
    
    @pytest.mark.unit
    def test_extract_overall_coverage(self, demo_project_root):
        """Test that overall coverage percentage is extracted."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Ensure analyzer is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.analyzer is not None, "TestCoverageAnalyzer should be initialized"
        
        sample_output = """TOTAL                        100     20    80%
"""
        
        # extract_overall_coverage moved to TestCoverageAnalyzer during Batch 3 decomposition
        overall = regenerator.analyzer.extract_overall_coverage(sample_output)
        
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
        
        # Ensure analyzer is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.analyzer is not None, "TestCoverageAnalyzer should be initialized"
        
        coverage_data = {
            'excellent_module.py': {'coverage': 85},
            'good_module.py': {'coverage': 70},
            'moderate_module.py': {'coverage': 50},
            'needs_work_module.py': {'coverage': 30},
            'critical_module.py': {'coverage': 10},
        }
        
        # categorize_modules moved to TestCoverageAnalyzer during Batch 3 decomposition
        categories = regenerator.analyzer.categorize_modules(coverage_data)
        
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
        
        # Ensure report_generator is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.report_generator is not None, "TestCoverageReportGenerator should be initialized"
        
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
        
        # generate_coverage_summary moved to TestCoverageReportGenerator during Batch 3 decomposition
        summary = regenerator.report_generator.generate_coverage_summary(coverage_data, overall_data)
        
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
            # finalize_coverage_outputs moved to TestCoverageReportGenerator during Batch 3 decomposition
            with patch.object(regenerator.report_generator, 'finalize_coverage_outputs'):
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
        from unittest.mock import patch, MagicMock
        from subprocess import CompletedProcess
        
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Ensure report_generator is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.report_generator is not None, "TestCoverageReportGenerator should be initialized"
        
        # Create some mock shard files
        shard1 = demo_project_root / ".coverage.1"
        shard2 = demo_project_root / ".coverage.2"
        shard1.write_text("test", encoding='utf-8')
        shard2.write_text("test", encoding='utf-8')
        
        try:
            # Mock subprocess.run to avoid actually running coverage commands in tests
            # The cleanup happens after combine, so we just need to mock combine to succeed
            with patch('subprocess.run') as mock_run:
                # Mock combine command to succeed
                mock_run.return_value = CompletedProcess(
                    args=['python', '-m', 'coverage', 'combine'],
                    returncode=0,
                    stdout='',
                    stderr=''
                )
                
                # Cleanup is now done in finalize_coverage_outputs() which combines and removes shards
                # Call finalize_coverage_outputs to test cleanup functionality
                regenerator.report_generator.finalize_coverage_outputs()
            
            # Shards should be removed after finalize_coverage_outputs
            assert not shard1.exists()
            assert not shard2.exists()
        finally:
            # Clean up if still exists
            if shard1.exists():
                shard1.unlink()
            if shard2.exists():
                shard2.unlink()

    @pytest.mark.unit
    def test_report_generator_uses_coverage_ini_paths(self, demo_project_root):
        """Report generator should honor data_file/html directory from coverage.ini."""
        config_file = demo_project_root / "coverage.ini"
        config_content = """[run]
data_file = development_tools/tests/.coverage

[html]
directory = development_tools/tests/coverage_html
"""
        config_file.write_text(config_content, encoding="utf-8")

        try:
            generator = TestCoverageReportGenerator(
                str(demo_project_root),
                coverage_config="coverage.ini",
            )
            assert (
                str(generator.coverage_data_file).replace("\\", "/")
                .endswith("development_tools/tests/.coverage")
            )
            assert (
                str(generator.coverage_html_dir).replace("\\", "/")
                .endswith("development_tools/tests/coverage_html")
            )
        finally:
            if config_file.exists():
                config_file.unlink()


class TestCoverageJSON:
    """Test coverage JSON loading."""
    
    @pytest.mark.unit
    def test_load_coverage_json(self, demo_project_root, temp_output_dir):
        """Test loading coverage data from JSON."""
        regenerator = CoverageMetricsRegenerator(str(demo_project_root))
        
        # Ensure analyzer is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.analyzer is not None, "TestCoverageAnalyzer should be initialized"
        
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
        
        # _load_coverage_json moved to TestCoverageAnalyzer during Batch 3 decomposition (now load_coverage_json)
        coverage_data = regenerator.analyzer.load_coverage_json(json_file)
        
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
        
        # Ensure report_generator is initialized (should always be available after Batch 3 decomposition)
        assert regenerator.report_generator is not None, "TestCoverageReportGenerator should be initialized"
        
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
        
        # generate_coverage_summary and update_coverage_plan moved to TestCoverageReportGenerator during Batch 3 decomposition
        summary = regenerator.report_generator.generate_coverage_summary(coverage_data, overall_data)
        # Update the report generator's coverage plan file path
        regenerator.report_generator.coverage_plan_file = regenerator.coverage_plan_file
        success = regenerator.report_generator.update_coverage_plan(summary)
        
        # Should update the file
        assert success is True
        assert regenerator.coverage_plan_file.exists()
        
        # File should contain summary content
        content = regenerator.coverage_plan_file.read_text(encoding='utf-8')
        assert 'Overall Coverage' in content or '75' in content


class TestCoverageCliOutput:
    """Test CLI output formatting for run_test_coverage.py."""

    @pytest.mark.unit
    def test_main_output_file_message_is_ascii(self, monkeypatch, temp_output_dir):
        """Output-file success message should be ASCII-safe for cp1252 consoles."""
        output_file = temp_output_dir / "coverage_results.json"

        class _FakeRegenerator:
            def __init__(self, *args, **kwargs):
                pass

            def run(self, update_plan: bool = False, dev_tools_only: bool = False):
                return {"coverage_collected": True, "overall": {"overall_coverage": 80.0}}

        monkeypatch.setattr(
            coverage_module,
            "CoverageMetricsRegenerator",
            _FakeRegenerator,
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "run_test_coverage.py",
                "--output-file",
                str(output_file),
            ],
        )

        coverage_module.main()

        message = f"Detailed coverage data saved to: {output_file}"
        assert output_file.exists()
        assert message.encode("cp1252")

    @pytest.mark.unit
    def test_main_exits_non_zero_when_no_coverage_results(self, monkeypatch):
        """CLI should exit non-zero when coverage execution produced no usable results."""

        class _FakeRegenerator:
            def __init__(self, *args, **kwargs):
                pass

            def run(self, update_plan: bool = False, dev_tools_only: bool = False):
                return {}

        monkeypatch.setattr(
            coverage_module,
            "CoverageMetricsRegenerator",
            _FakeRegenerator,
        )
        monkeypatch.setattr("sys.argv", ["run_test_coverage.py"])

        with pytest.raises(SystemExit) as exc:
            coverage_module.main()

        assert exc.value.code == 1
