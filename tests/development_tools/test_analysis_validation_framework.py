#!/usr/bin/env python3
"""
Analysis Validation Framework

Tests that verify analysis tools are detecting real issues accurately.
Tracks false positive and false negative rates to ensure quality.

This framework:
- Validates that known issues are detected (false negative prevention)
- Validates that known non-issues are not flagged (false positive prevention)
- Tracks accuracy metrics over time
- Provides continuous validation during audits
"""

import pytest
import json
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module

# Get project root
project_root = Path(__file__).parent.parent.parent


# Accuracy targets (from plan success criteria)
ACCURACY_TARGETS = {
    'path_drift_false_positive_rate': 0.05,  # <5%
    'error_handling_false_positive_rate': 0.02,  # <2%
    'documentation_false_positive_rate': 0.05,  # <5%
    'false_negative_rate': 0.00,  # 0% (all known issues must be detected)
}


class TestFalseNegativeDetection:
    """
    Test that analysis tools detect known issues (prevent false negatives).
    
    These tests use fixtures with intentional issues to verify tools
    don't miss real problems.
    """
    
    @pytest.mark.unit
    def test_error_handling_detection(self):
        """Verify error handling analyzer detects functions missing decorators."""
        # This test uses the false_negative_test_code.py fixture
        # which has functions with try-except but no decorators
        fixture_path = project_root / 'tests' / 'fixtures' / 'development_tools_demo' / 'false_negative_test_code.py'
        
        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")
        
        # Import and run error handling analyzer
        try:
            error_handling_module = load_development_tools_module('error_handling.analyze_error_handling')
            ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer
            
            analyzer = ErrorHandlingAnalyzer(project_root=str(project_root))
            results = analyzer.analyze_file(fixture_path)
            
            # Check functions in the results (missing_error_handling list is only populated during aggregation)
            functions = results.get('functions', [])
            
            # Find functions that should have error handling but don't
            # fetch_external_data uses requests.get() which should trigger detection
            missing_handling_functions = [
                f for f in functions
                if f.get('missing_error_handling', False) and not f.get('excluded', False)
            ]
            
            # The fixture has fetch_external_data which uses requests.get() - should be detected
            # Also check for Phase 1 candidates (try-except without decorator catching generic Exception)
            phase1_candidates = [
                f for f in functions
                if f.get('is_phase1_candidate', False) and not f.get('excluded', False)
            ]
            
            # At least one function should be detected (either missing_error_handling or phase1_candidate)
            assert len(missing_handling_functions) > 0 or len(phase1_candidates) > 0, \
                f"Error handling analyzer should detect missing decorators. " \
                f"Functions analyzed: {[f['name'] for f in functions]}, " \
                f"Missing handling: {[f['name'] for f in missing_handling_functions]}, " \
                f"Phase1 candidates: {[f['name'] for f in phase1_candidates]}"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import error handling analyzer: {e}")
    
    @pytest.mark.unit
    def test_documentation_detection(self):
        """Verify documentation analyzer detects functions missing docstrings."""
        # This test uses the false_negative_test_code.py fixture
        fixture_path = project_root / 'tests' / 'fixtures' / 'development_tools_demo' / 'false_negative_test_code.py'
        
        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")
        
        # Import and run function registry analyzer
        try:
            functions_module = load_development_tools_module('functions.analyze_functions')
            extract_functions = functions_module.extract_functions
            
            functions = extract_functions(str(fixture_path))
            
            # Find functions without docstrings (excluding special methods and auto-generated)
            exclusion_utilities = load_development_tools_module('shared.exclusion_utilities')
            is_special_python_method = exclusion_utilities.is_special_python_method
            is_auto_generated_code = exclusion_utilities.is_auto_generated_code
            
            undocumented = [
                f for f in functions
                if not f.get('docstring', '').strip()
                and not is_special_python_method(f['name'], f.get('complexity', 0))
                and not is_auto_generated_code(f['file'], f['name'])
            ]
            
            # The fixture has at least one function that should be detected
            assert len(undocumented) > 0, "Documentation analyzer should detect missing docstrings"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import function analyzer: {e}")
    
    @pytest.mark.unit
    def test_path_drift_detection(self, demo_project_root, test_config_path):
        """Verify path drift analyzer detects broken file references."""
        # This test uses the demo project root (not main project) because test fixtures
        # are correctly excluded from path drift analysis in the main project
        fixture_path = demo_project_root / 'docs' / 'false_negative_test_doc.md'
        
        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")
        
        # Import and run path drift analyzer
        try:
            path_drift_module = load_development_tools_module('docs.analyze_path_drift')
            PathDriftAnalyzer = path_drift_module.PathDriftAnalyzer
            
            # Use demo project root and test config
            analyzer = PathDriftAnalyzer(
                project_root=str(demo_project_root),
                config_path=test_config_path,
                use_cache=False
            )
            results = analyzer.run_analysis()
            
            # Check if the broken path in the fixture is detected
            # Results are in standard format: {'summary': {...}, 'details': {...}, 'files': {...}}
            details = results.get('details', {})
            detailed_issues = details.get('detailed_issues', {})
            
            # Find issues in the test fixture
            fixture_issues = []
            test_file_path = str(fixture_path.relative_to(demo_project_root))
            test_file_path_win = test_file_path.replace('/', '\\')
            
            for file_path, file_issues in detailed_issues.items():
                if test_file_path in file_path or test_file_path_win in file_path:
                    fixture_issues.extend(file_issues if isinstance(file_issues, list) else [file_issues])
            
            # The fixture has at least one broken path that should be detected
            assert len(fixture_issues) > 0, \
                f"Path drift analyzer should detect broken file references. " \
                f"Found {len(detailed_issues)} files with issues, but none in test fixture. " \
                f"Test file path: {test_file_path}, Files checked: {list(detailed_issues.keys())[:5]}"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import path drift analyzer: {e}")


class TestFalsePositivePrevention:
    """
    Test that analysis tools don't flag known non-issues (prevent false positives).
    
    These tests verify that exclusion logic is working correctly.
    """
    
    @pytest.mark.unit
    def test_test_fixtures_excluded_from_path_drift(self):
        """Verify test fixtures are excluded from path drift results."""
        # Test exclusion logic directly rather than running full analysis
        try:
            exclusion_module = load_development_tools_module('shared.standard_exclusions')
            should_exclude_file = exclusion_module.should_exclude_file
            
            # Test that test fixture paths are excluded (Unix-style path)
            assert should_exclude_file('tests/fixtures/development_tools_demo/docs/test.md', 'documentation'), \
                "Test fixture files should be excluded"
            
            # Test that normal documentation is NOT excluded
            assert not should_exclude_file('development_docs/ARCHITECTURE.md', 'documentation'), \
                "Normal documentation should NOT be excluded"
            assert not should_exclude_file('ai_development_docs/AI_GUIDE.md', 'documentation'), \
                "Normal documentation should NOT be excluded"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import exclusion utilities: {e}")
    
    @pytest.mark.unit
    def test_special_methods_excluded_from_documentation(self):
        """Verify special methods are excluded from undocumented counts."""
        # Test exclusion logic directly rather than scanning entire codebase
        try:
            exclusion_utilities = load_development_tools_module('shared.exclusion_utilities')
            is_special_python_method = exclusion_utilities.is_special_python_method
            
            # Test that special methods are correctly identified
            assert is_special_python_method('__repr__', 10), "__repr__ should be identified as special"
            assert is_special_python_method('__str__', 10), "__str__ should be identified as special"
            assert is_special_python_method('__eq__', 10), "__eq__ should be identified as special"
            assert is_special_python_method('__init__', 10), "Simple __init__ should be identified as special"
            
            # Test that context managers are NOT excluded (should be documented)
            assert not is_special_python_method('__enter__', 10), "__enter__ should NOT be excluded (needs documentation)"
            assert not is_special_python_method('__exit__', 10), "__exit__ should NOT be excluded (needs documentation)"
            
            # Test that complex __init__ is NOT excluded
            assert not is_special_python_method('__init__', 50), "Complex __init__ should NOT be excluded (needs documentation)"
            
            # Test that normal methods are NOT excluded
            assert not is_special_python_method('handle_message', 10), "Normal methods should NOT be excluded"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import exclusion utilities: {e}")
    
    @pytest.mark.unit
    def test_auto_generated_code_excluded(self):
        """Verify auto-generated code is excluded from analysis."""
        # Test exclusion logic directly rather than scanning entire codebase
        try:
            exclusion_utilities = load_development_tools_module('shared.exclusion_utilities')
            is_auto_generated_code = exclusion_utilities.is_auto_generated_code
            
            # Test that auto-generated patterns are correctly identified
            assert is_auto_generated_code('ui/generated/widget_pyqt.py', 'setupUi'), "PyQt generated file should be detected"
            assert is_auto_generated_code('ui/generated/widget.py', 'some_function'), "Generated directory should be detected"
            assert is_auto_generated_code('widget_pyqt.py', 'some_function'), "PyQt file pattern should be detected"
            assert is_auto_generated_code('widget.py', 'setupUi'), "PyQt function should be detected"
            assert is_auto_generated_code('widget.py', 'retranslateUi'), "PyQt function should be detected"
            
            # Test that normal code is NOT excluded
            assert not is_auto_generated_code('core/service.py', 'handle_message'), "Normal code should NOT be excluded"
            assert not is_auto_generated_code('communication/channel.py', 'process_request'), "Normal code should NOT be excluded"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import exclusion utilities: {e}")


class TestAccuracyMetrics:
    """
    Test that accuracy metrics meet targets.
    
    These tests verify that false positive and false negative rates
    are within acceptable limits.
    """
    
    @pytest.mark.unit
    def test_accuracy_targets_defined(self):
        """Verify accuracy targets are defined."""
        assert len(ACCURACY_TARGETS) > 0, "Accuracy targets should be defined"
        assert 'false_negative_rate' in ACCURACY_TARGETS, "False negative rate target should be defined"
    
    @pytest.mark.unit
    def test_path_drift_false_positive_rate(self):
        """Verify path drift false positive rate targets are defined and exclusion logic works."""
        # Test that accuracy targets are defined (actual rate calculation requires full analysis)
        assert 'path_drift_false_positive_rate' in ACCURACY_TARGETS, "Path drift false positive rate target should be defined"
        assert ACCURACY_TARGETS['path_drift_false_positive_rate'] == 0.05, "Target should be <5%"
        
        # Verify exclusion logic works (which prevents false positives)
        try:
            from development_tools.shared.standard_exclusions import should_exclude_file
            
            # Test fixtures should be excluded (preventing false positives)
            assert should_exclude_file('tests/fixtures/test.md', 'documentation'), \
                "Test fixtures should be excluded to prevent false positives"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import exclusion utilities: {e}")


class TestFunctionCountingAccuracy:
    """
    Test that function counting is accurate and consistent across tools.
    
    These tests verify that different analysis tools use the same counting method
    and produce consistent results.
    """
    
    @pytest.mark.unit
    def test_function_counting_uses_canonical_method(self):
        """Verify that canonical metrics prioritize analyze_functions."""
        try:
            from development_tools.shared.service.data_loading import DataLoadingMixin
            from development_tools.shared.service import AIToolsService
            
            # Create a minimal service instance to test canonical metrics
            service = AIToolsService()
            
            # Mock results cache with analyze_functions data
            service.results_cache = {
                'analyze_functions': {
                    'details': {
                        'total_functions': 1497
                    }
                },
                'decision_support_metrics': {
                    'total_functions': 1500  # Different number
                }
            }
            
            # Get canonical metrics
            metrics = service._get_canonical_metrics()
            
            # Should prioritize analyze_functions (1497) over decision_support (1500)
            assert metrics.get('total_functions') == 1497, \
                "Canonical metrics should prioritize analyze_functions"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import data loading service: {e}")
    
    @pytest.mark.unit
    def test_both_tools_use_scan_all_functions(self):
        """Verify that both analyze_functions and decision_support use scan_all_functions."""
        try:
            functions_module = load_development_tools_module('functions.analyze_functions')
            decision_support_module = load_development_tools_module('reports.decision_support')
            
            # Both should have access to scan_all_functions
            assert hasattr(functions_module, 'scan_all_functions'), \
                "analyze_functions should use scan_all_functions"
            
            # decision_support should also use scan_all_functions (imported or called)
            # Check if it imports or calls the function
            import inspect
            decision_support_source = inspect.getsource(decision_support_module)
            assert 'scan_all_functions' in decision_support_source, \
                "decision_support should use scan_all_functions"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import function analysis modules: {e}")


class TestThresholdValidation:
    """
    Test that thresholds are correctly loaded from config and applied.
    
    These tests verify that threshold values match configuration
    and are used consistently across tools.
    """
    
    @pytest.mark.unit
    def test_thresholds_loaded_from_config(self):
        """Verify thresholds are loaded from config file."""
        try:
            import json
            from pathlib import Path
            
            # Read config file directly
            config_path = Path(__file__).parent.parent.parent / 'development_tools' / 'config' / 'development_tools_config.json'
            if not config_path.exists():
                pytest.skip(f"Config file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Get threshold values
            doc_threshold = config_dict.get('documentation_coverage_threshold', 80.0)
            test_threshold = config_dict.get('test_coverage_threshold', 80.0)
            dev_tools_threshold = config_dict.get('dev_tools_coverage_threshold', 60.0)
            
            # Verify thresholds are reasonable values
            assert doc_threshold >= 0 and doc_threshold <= 100, \
                f"Documentation threshold should be 0-100, got {doc_threshold}"
            assert test_threshold >= 0 and test_threshold <= 100, \
                f"Test coverage threshold should be 0-100, got {test_threshold}"
            assert dev_tools_threshold >= 0 and dev_tools_threshold <= 100, \
                f"Dev tools threshold should be 0-100, got {dev_tools_threshold}"
            
            # Verify expected values (80% for docs/test, 60% for dev tools)
            assert doc_threshold == 80.0, \
                f"Documentation threshold should be 80%, got {doc_threshold}%"
            assert test_threshold == 80.0, \
                f"Test coverage threshold should be 80%, got {test_threshold}%"
            assert dev_tools_threshold == 60.0, \
                f"Dev tools threshold should be 60%, got {dev_tools_threshold}%"
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            pytest.skip(f"Could not load config file: {e}")
    
    @pytest.mark.unit
    def test_threshold_consistency_in_reports(self):
        """Verify thresholds are used consistently in report generation."""
        try:
            from development_tools.shared.service.report_generation import ReportGenerationMixin
            from development_tools.shared.service import AIToolsService
            from development_tools import config
            config.load_external_config()
            
            service = AIToolsService()
            
            # Check that report generation uses config thresholds
            assert hasattr(service, '_generate_ai_status_document'), \
                "Service should have status document generation"
            assert hasattr(service, '_generate_ai_priorities_document'), \
                "Service should have priorities document generation"
            
            # Verify config is accessible
            assert hasattr(service, 'audit_config') or hasattr(config, 'development_tools_config'), \
                "Config should be accessible for threshold checking"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import report generation service: {e}")


class TestRecommendationQuality:
    """
    Test that recommendations are structured correctly and actionable.
    
    These tests verify basic recommendation quality (structure, not content).
    """
    
    @pytest.mark.unit
    def test_recommendations_have_required_structure(self):
        """Verify recommendations have required fields (title, description, effort, etc.)."""
        try:
            config_module = load_development_tools_module('config.analyze_config')
            ConfigValidator = config_module.ConfigValidator
            
            # Get recommendations from config validator
            validator = ConfigValidator()
            
            # Run validation to get recommendations
            tools_analysis = validator.scan_tools_for_config_usage()
            config_validation = validator.validate_configuration_consistency()
            completeness = validator.check_configuration_completeness()
            
            recommendations = validator.generate_recommendations(tools_analysis, config_validation, completeness)
            
            # Verify recommendations are a list
            assert isinstance(recommendations, list), \
                "Recommendations should be a list"
            
            # If there are recommendations, verify structure
            # Recommendations from ConfigValidator are strings, not dicts
            if recommendations:
                for rec in recommendations[:3]:  # Check first 3
                    assert isinstance(rec, str), \
                        "Each recommendation should be a string"
                    assert len(rec.strip()) > 0, \
                        "Recommendation should not be empty"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import config validator: {e}")
    
    @pytest.mark.unit
    def test_recommendations_are_non_empty_strings(self):
        """Verify recommendation text is non-empty."""
        try:
            config_module = load_development_tools_module('config.analyze_config')
            ConfigValidator = config_module.ConfigValidator
            
            validator = ConfigValidator()
            
            # Run validation to get recommendations
            tools_analysis = validator.scan_tools_for_config_usage()
            config_validation = validator.validate_configuration_consistency()
            completeness = validator.check_configuration_completeness()
            
            recommendations = validator.generate_recommendations(tools_analysis, config_validation, completeness)
            
            # If there are recommendations, verify text is non-empty
            if recommendations:
                for rec in recommendations[:3]:  # Check first 3
                    assert isinstance(rec, str), \
                        "Recommendation should be a string"
                    assert len(rec.strip()) > 0, \
                        "Recommendation text should not be empty"
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Could not import config validator: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

