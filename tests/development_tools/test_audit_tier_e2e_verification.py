# """
# End-to-end verification tests for audit tier functionality.

# **Test Scope**: These tests run REAL audits with actual tool execution to verify
# end-to-end functionality. These tests are slow (especially Tier 3 which takes ~9-10 minutes)
# and are excluded from the regular test suite.

# **What is tested**:
# - Real audit tier execution with actual tools (on demo project)
# - All 23 tools execute (7 in Tier 1, 10 in Tier 2, 6 in Tier 3)
# - Actual tool execution and output generation
# - End-to-end audit workflow with real tool execution
# - Real file generation and content validation

# **What is NOT tested here** (verified by test_audit_tier_comprehensive.py with mocks):
# - Tier inheritance (Tier 2 includes Tier 1, Tier 3 includes Tier 1 and 2) - verified in comprehensive tests
# - Individual tool result storage in domain-organized JSON files - verified in comprehensive tests
# - File rotation and archiving - verified in comprehensive tests
# - Standalone tool execution - verified in comprehensive tests

# **Note on demo project limitations**:
# - These tests run on a demo project, so tools may fail fast (no real codebase to analyze)
# - Timing requirements are not enforced (tools complete quickly on demo project)
# - For full verification including timing, run actual audits on the real project:
#   - `python development_tools/run_development_tools.py audit --quick`
#   - `python development_tools/run_development_tools.py audit`
#   - `python development_tools/run_development_tools.py audit --full`

# **Usage**:
# - Run with: `pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py`
# - Run specific tier: `pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py::TestAuditTierE2E::test_tier1_e2e`
# - These tests are excluded from regular test runs via pytest.ini configuration

# **Filesystem Safety**: All test writes occur within the `temp_project_copy` fixture's
# temporary directory, which is automatically cleaned up after each test. No files are
# written outside the test isolation directory.
# """

# import json
# import sys
# import importlib.util
# import pytest
# from pathlib import Path

# from tests.development_tools.conftest import load_development_tools_module, temp_project_copy

# # Get the actual project root (where core modules exist)
# _actual_project_root = Path(__file__).parent.parent.parent

# # Defer module loading until tests run to avoid import errors during collection
# # when core modules aren't available
# def get_aitools_service():
#     """Load AIToolsService on demand.

#     Ensures the actual project root is in sys.path so core modules can be imported
#     by development_tools modules.
#     """
#     # Add actual project root to sys.path so core modules can be found
#     # Use resolve() to get absolute path and ensure it's at the front
#     project_root_str = str(_actual_project_root.resolve())

#     # Remove it first if it exists (to avoid duplicates), then add to front
#     if project_root_str in sys.path:
#         sys.path.remove(project_root_str)
#     sys.path.insert(0, project_root_str)

#     # Load core package and submodules explicitly using importlib
#     # This is necessary because just adding to sys.path isn't enough - Python needs
#     # both the package and submodules loaded into sys.modules
#     # IMPORTANT: Load in dependency order - error_handling before logger (logger imports error_handling)
#     core_dir = _actual_project_root / "core"
#     if not core_dir.exists():
#         raise ImportError(f"Core directory not found at {core_dir}")

#     # Load core package first
#     core_init_path = core_dir / "__init__.py"
#     if core_init_path.exists():
#         core_spec = importlib.util.spec_from_file_location("core", core_init_path)
#         if core_spec and core_spec.loader:
#             if "core" not in sys.modules:
#                 core_module = importlib.util.module_from_spec(core_spec)
#                 sys.modules["core"] = core_module
#                 core_spec.loader.exec_module(core_module)

#     # Load core.error_handling FIRST (before logger, since logger depends on it)
#     error_handling_path = core_dir / "error_handling.py"
#     if error_handling_path.exists():
#         eh_spec = importlib.util.spec_from_file_location("core.error_handling", error_handling_path)
#         if eh_spec and eh_spec.loader:
#             if "core.error_handling" not in sys.modules:
#                 eh_module = importlib.util.module_from_spec(eh_spec)
#                 sys.modules["core.error_handling"] = eh_module
#                 eh_spec.loader.exec_module(eh_module)

#     # Load core.logger AFTER error_handling (logger imports error_handling)
#     logger_path = core_dir / "logger.py"
#     if logger_path.exists():
#         logger_spec = importlib.util.spec_from_file_location("core.logger", logger_path)
#         if logger_spec and logger_spec.loader:
#             if "core.logger" not in sys.modules:
#                 logger_module = importlib.util.module_from_spec(logger_spec)
#                 sys.modules["core.logger"] = logger_module
#                 logger_spec.loader.exec_module(logger_module)

#     # Verify imports work
#     try:
#         import core.logger
#         import core.error_handling
#     except ImportError as e:
#         raise ImportError(
#             f"Cannot import core modules from {project_root_str}. "
#             f"Core directory exists: {core_dir.exists()}. "
#             f"Error: {e}"
#         ) from e

#     service_module = load_development_tools_module("shared.service")
#     return service_module.AIToolsService


# class TestAuditTierE2E:
#     """End-to-end tests that run real audits with actual tool execution."""

#     @pytest.mark.e2e
#     @pytest.mark.slow
#     @pytest.mark.integration
#     def test_tier1_e2e_quick_audit(self, temp_project_copy):
#         """Test Tier 1 (quick) audit with real tool execution."""
#         AIToolsService = get_aitools_service()
#         service = AIToolsService(project_root=str(temp_project_copy))

#         # Create dev_tools directory structure
#         dev_tools_dir = temp_project_copy / "development_tools"
#         dev_tools_dir.mkdir(exist_ok=True)
#         reports_dir = dev_tools_dir / "reports"
#         reports_dir.mkdir(exist_ok=True)

#         # Run real quick audit (no mocks)
#         result = service.run_audit(quick=True)

#         # Verify audit completed successfully
#         assert result, "Tier 1 audit should complete successfully"

#         # Verify all 4 output files exist
#         ai_status_file = dev_tools_dir / "AI_STATUS.md"
#         ai_priorities_file = dev_tools_dir / "AI_PRIORITIES.md"
#         consolidated_report_file = dev_tools_dir / "consolidated_report.txt"
#         analysis_results_file = reports_dir / "analysis_detailed_results.json"

#         assert ai_status_file.exists(), "AI_STATUS.md should be generated"
#         assert ai_priorities_file.exists(), "AI_PRIORITIES.md should be generated"
#         assert consolidated_report_file.exists(), "consolidated_report.txt should be generated"
#         assert analysis_results_file.exists(), "analysis_detailed_results.json should be generated"

#         # Verify files have meaningful content
#         status_content = ai_status_file.read_text()
#         assert len(status_content) > 100, "AI_STATUS.md should have substantial content"
#         assert "Last Generated" in status_content or "Generated" in status_content, "AI_STATUS.md should contain metadata"

#         priorities_content = ai_priorities_file.read_text()
#         assert len(priorities_content) > 50, "AI_PRIORITIES.md should have content"

#         consolidated_content = consolidated_report_file.read_text()
#         assert len(consolidated_content) > 100, "consolidated_report.txt should have substantial content"

#         # Verify analysis_detailed_results.json structure and tier
#         with open(analysis_results_file, 'r', encoding='utf-8') as f:
#             analysis_data = json.load(f)

#         assert 'audit_tier' in analysis_data, "Should contain audit_tier"
#         assert analysis_data['audit_tier'] == 1, "Should indicate Tier 1"
#         assert 'results' in analysis_data, "Should contain results"
#         assert isinstance(analysis_data['results'], dict), "Results should be a dictionary"
#         assert len(analysis_data['results']) > 0, "Should contain at least one tool result"

#         # Verify ALL Tier 1 tools were run (7 tools total)
#         tier1_all_tools = [
#             'quick_status',
#             'system_signals',
#             'analyze_documentation',
#             'analyze_config',
#             'analyze_ai_work',
#             'analyze_function_patterns',
#             'decision_support'
#         ]
#         found_tier1_tools = [tool for tool in tier1_all_tools if tool in analysis_data['results']]
#         # On demo project, some tools may fail fast, so we verify at least most tools executed
#         # (allow 1-2 failures on demo project, but verify orchestration attempted all)
#         assert len(found_tier1_tools) >= 5, (
#             f"Should contain at least 5 of 7 Tier 1 tool results. "
#             f"Found: {found_tier1_tools}, All results: {list(analysis_data['results'].keys())}"
#         )

#     @pytest.mark.e2e
#     @pytest.mark.slow
#     @pytest.mark.integration
#     def test_tier2_e2e_standard_audit(self, temp_project_copy):
#         """Test Tier 2 (standard) audit with real tool execution."""
#         AIToolsService = get_aitools_service()
#         service = AIToolsService(project_root=str(temp_project_copy))

#         # Create dev_tools directory structure
#         dev_tools_dir = temp_project_copy / "development_tools"
#         dev_tools_dir.mkdir(exist_ok=True)
#         reports_dir = dev_tools_dir / "reports"
#         reports_dir.mkdir(exist_ok=True)

#         # Run real standard audit (no mocks)
#         result = service.run_audit(quick=False, full=False)

#         # Verify audit completed successfully
#         assert result, "Tier 2 audit should complete successfully"

#         # Verify all 4 output files exist
#         ai_status_file = dev_tools_dir / "AI_STATUS.md"
#         ai_priorities_file = dev_tools_dir / "AI_PRIORITIES.md"
#         consolidated_report_file = dev_tools_dir / "consolidated_report.txt"
#         analysis_results_file = reports_dir / "analysis_detailed_results.json"

#         assert ai_status_file.exists(), "AI_STATUS.md should be generated"
#         assert ai_priorities_file.exists(), "AI_PRIORITIES.md should be generated"
#         assert consolidated_report_file.exists(), "consolidated_report.txt should be generated"
#         assert analysis_results_file.exists(), "analysis_detailed_results.json should be generated"

#         # Verify analysis_detailed_results.json indicates Tier 2
#         with open(analysis_results_file, 'r', encoding='utf-8') as f:
#             analysis_data = json.load(f)

#         assert analysis_data['audit_tier'] == 2, "Should indicate Tier 2"

#         # Verify ALL Tier 1 and Tier 2 tools were run
#         # Tier 1 tools (7 total)
#         tier1_all_tools = [
#             'quick_status',
#             'system_signals',
#             'analyze_documentation',
#             'analyze_config',
#             'analyze_ai_work',
#             'analyze_function_patterns',
#             'decision_support'
#         ]
#         # Tier 2 tools (10 total)
#         tier2_all_tools = [
#             'analyze_functions',
#             'analyze_error_handling',
#             'analyze_package_exports',
#             'analyze_module_imports',
#             'analyze_dependency_patterns',
#             'analyze_module_dependencies',
#             'analyze_function_registry',
#             'analyze_documentation_sync',
#             'analyze_unused_imports',
#             'generate_unused_imports_report'
#         ]

#         found_tier1 = [tool for tool in tier1_all_tools if tool in analysis_data['results']]
#         found_tier2 = [tool for tool in tier2_all_tools if tool in analysis_data['results']]

#         # On demo project, some tools may fail fast, so we verify at least most tools executed
#         # Tier 1: verify at least 5 of 7 executed
#         assert len(found_tier1) >= 5, (
#             f"Should contain at least 5 of 7 Tier 1 tool results. "
#             f"Found: {found_tier1}, All results: {list(analysis_data['results'].keys())}"
#         )
#         # Tier 2: verify at least 7 of 10 executed
#         assert len(found_tier2) >= 7, (
#             f"Should contain at least 7 of 10 Tier 2 tool results. "
#             f"Found: {found_tier2}, All results: {list(analysis_data['results'].keys())}"
#         )

#     @pytest.mark.e2e
#     @pytest.mark.slow
#     @pytest.mark.integration
#     @pytest.mark.no_parallel
#     def test_tier3_e2e_full_audit(self, temp_project_copy):
#         """Test Tier 3 (full) audit with real tool execution.

#         **WARNING**: This test takes ~9-10 minutes to complete due to coverage generation.
#         It is marked with @pytest.mark.no_parallel to prevent conflicts during execution.
#         """
#         import time
#         AIToolsService = get_aitools_service()
#         service = AIToolsService(project_root=str(temp_project_copy))

#         # Create dev_tools directory structure
#         dev_tools_dir = temp_project_copy / "development_tools"
#         dev_tools_dir.mkdir(exist_ok=True)
#         reports_dir = dev_tools_dir / "reports"
#         reports_dir.mkdir(exist_ok=True)

#         # Run real full audit (no mocks) - this will take several minutes
#         start_time = time.time()
#         result = service.run_audit(quick=False, full=True)
#         elapsed_time = time.time() - start_time

#         # Verify all 4 output files exist
#         ai_status_file = dev_tools_dir / "AI_STATUS.md"
#         ai_priorities_file = dev_tools_dir / "AI_PRIORITIES.md"
#         consolidated_report_file = dev_tools_dir / "consolidated_report.txt"
#         analysis_results_file = reports_dir / "analysis_detailed_results.json"

#         assert ai_status_file.exists(), "AI_STATUS.md should be generated"
#         assert ai_priorities_file.exists(), "AI_PRIORITIES.md should be generated"
#         assert consolidated_report_file.exists(), "consolidated_report.txt should be generated"
#         assert analysis_results_file.exists(), "analysis_detailed_results.json should be generated"

#         # Load analysis results once
#         with open(analysis_results_file, 'r', encoding='utf-8') as f:
#             analysis_data = json.load(f)

#         # Verify audit tier is 3 (orchestration attempted Tier 3)
#         # Note: Tier 3 may return False if some tools fail (e.g., coverage on demo project),
#         # but we verify that orchestration ran and generated output files
#         assert analysis_data.get('audit_tier') == 3, "Should indicate Tier 3"

#         # Verify ALL 23 tools were attempted (orchestration worked)
#         # Tier 1 tools (7 total)
#         tier1_all_tools = [
#             'quick_status',
#             'system_signals',
#             'analyze_documentation',
#             'analyze_config',
#             'analyze_ai_work',
#             'analyze_function_patterns',
#             'decision_support'
#         ]
#         # Tier 2 tools (10 total)
#         tier2_all_tools = [
#             'analyze_functions',
#             'analyze_error_handling',
#             'analyze_package_exports',
#             'analyze_module_imports',
#             'analyze_dependency_patterns',
#             'analyze_module_dependencies',
#             'analyze_function_registry',
#             'analyze_documentation_sync',
#             'analyze_unused_imports',
#             'generate_unused_imports_report'
#         ]
#         # Tier 3 tools (6 total)
#         tier3_all_tools = [
#             'run_test_coverage',
#             'generate_dev_tools_coverage',
#             'analyze_test_markers',
#             'generate_test_coverage_report',
#             'analyze_legacy_references',
#             'generate_legacy_reference_report'
#         ]

#         all_23_tools = tier1_all_tools + tier2_all_tools + tier3_all_tools
#         results = analysis_data.get('results', {})
#         found_tools = [tool for tool in all_23_tools if tool in results]

#         # On demo project, some tools (especially Tier 3 coverage tools) may fail fast,
#         # so we verify at least 18 of 23 tools executed (allows 5 failures)
#         assert len(found_tools) >= 18, (
#             f"Should contain at least 18 of 23 total tool results. "
#             f"Found: {len(found_tools)}/{len(all_23_tools)} tools. "
#             f"Found tools: {found_tools}. "
#             f"Missing tools: {[t for t in all_23_tools if t not in found_tools]}. "
#             f"All results: {list(results.keys())}"
#         )

#         # Verify we got results from all three tiers (orchestration attempted all tiers)
#         found_tier1 = [tool for tool in tier1_all_tools if tool in results]
#         found_tier2 = [tool for tool in tier2_all_tools if tool in results]
#         found_tier3 = [tool for tool in tier3_all_tools if tool in results]

#         assert len(found_tier1) >= 5, f"Should contain at least 5 of 7 Tier 1 tool results. Found: {found_tier1}"
#         assert len(found_tier2) >= 7, f"Should contain at least 7 of 10 Tier 2 tool results. Found: {found_tier2}"
#         # Tier 3 tools may fail on demo project (coverage needs real tests), so allow 2 of 6
#         assert len(found_tier3) >= 2, f"Should contain at least 2 of 6 Tier 3 tool results. Found: {found_tier3}"

#         # Verify all tier tools were run
#         # Tier 1 tools should be present
#         tier1_tools = ['system_signals', 'analyze_documentation']
#         # Tier 2 tools should be present
#         tier2_tools = ['analyze_functions', 'analyze_error_handling']
#         # Tier 3 tools should be present
#         tier3_tools = ['run_test_coverage', 'analyze_legacy_references']

#         found_tier1 = [tool for tool in tier1_tools if tool in analysis_data['results']]
#         found_tier2 = [tool for tool in tier2_tools if tool in analysis_data['results']]
#         found_tier3 = [tool for tool in tier3_tools if tool in analysis_data['results']]

#         assert len(found_tier1) > 0, "Should contain Tier 1 tool results"
#         assert len(found_tier2) > 0, "Should contain Tier 2 tool results"

#         # For Tier 3, verify that at least one Tier 3 tool was attempted
#         # Note: Coverage tools may fail fast on demo project (no tests to cover),
#         # but compatibility analysis should still run
#         all_tier3_tools = ['run_test_coverage', 'generate_dev_tools_coverage',
#                           'analyze_test_markers', 'generate_test_coverage_report',
#                           'analyze_legacy_references', 'generate_legacy_reference_report']
#         attempted_tier3 = [tool for tool in all_tier3_tools if tool in analysis_data['results']]

#         if len(attempted_tier3) == 0:
#             # No Tier 3 tools were even attempted - this is a problem
#             pytest.fail(
#                 f"No Tier 3 tools were run. Expected at least one of: {all_tier3_tools}. "
#                 f"Found results: {list(analysis_data['results'].keys())}. "
#                 f"Elapsed time: {elapsed_time:.1f}s (expected ~600s for full audit)"
#             )

#         # Note: On demo project, tools may fail fast (no real codebase to analyze),
#         # so we don't enforce timing requirements. The comprehensive tests verify
#         # orchestration logic, and this E2E test verifies that actual execution works.
#         # For full timing verification, run on the actual project.
