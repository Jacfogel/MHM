"""
Main AI Functionality Test Runner

Orchestrates and executes all AI functionality tests from separate test modules.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# CRITICAL: Set environment variables BEFORE any imports that might initialize loggers
# This ensures test logs go to tests/logs/ instead of logs/
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
os.environ["MHM_TESTING"] = "1"
os.environ["TEST_VERBOSE_LOGS"] = "1"  # Enable actual log file writing in test mode
os.environ["TEST_CONSOLIDATED_LOGGING"] = "1"  # Enable consolidated logging mode
# Route all logs to tests/logs/ directory (absolute path for reliability)
tests_logs_dir = os.path.join(project_root, "tests", "logs")
os.makedirs(tests_logs_dir, exist_ok=True)  # Ensure directory exists
os.environ["LOGS_DIR"] = tests_logs_dir
os.environ["TEST_LOGS_DIR"] = tests_logs_dir

import shutil
from core.service_utilities import now_filename_timestamp, now_readable_timestamp

# Add project root to path (already set above)
sys.path.insert(0, project_root)

# Import logging utilities after path is set


def setup_consolidated_ai_test_logging():
    """Set up consolidated test logging - all component logs go to a single file, like the test suite.

    This replicates the logging setup from tests/conftest.py's setup_consolidated_test_logging fixture.
    All component logs go to test_consolidated.log, test execution logs go to test_run.log.
    """
    # Create a single consolidated log file for all test logging
    consolidated_log_file = Path(tests_logs_dir) / "test_consolidated.log"
    consolidated_log_file.parent.mkdir(exist_ok=True)

    # Ensure test_run.log exists
    test_run_log_file = Path(tests_logs_dir) / "test_run.log"
    if not test_run_log_file.exists():
        test_run_log_file.touch()

    # Write headers FIRST before any logging starts
    timestamp = now_readable_timestamp()

    # Write headers to both log files
    def write_log_header(log_file, log_name, description):
        header_text = (
            f"{'='*80}\n"
            f"# {log_name} STARTED: {timestamp}\n"
            f"# {description}\n"
            f"{'='*80}\n\n"
        )
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(header_text)

    write_log_header(
        consolidated_log_file,
        "AI FUNCTIONALITY TEST RUN",
        "Component Logging Active - Real component logs from application components are captured here",
    )
    write_log_header(
        test_run_log_file,
        "AI FUNCTIONALITY TEST RUN",
        "Test Execution Logging Active - Test execution and framework logs are captured here",
    )

    # Create handler for component logs (no test context)
    component_handler = logging.FileHandler(
        str(consolidated_log_file), mode="a", encoding="utf-8"
    )
    component_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    component_handler.setFormatter(component_formatter)

    # Create handler for test execution logs (with test context)
    test_handler = logging.FileHandler(
        str(test_run_log_file), mode="a", encoding="utf-8"
    )
    try:
        from core.logger import PytestContextLogFormatter

        test_formatter = PytestContextLogFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    except ImportError:
        # Fallback if PytestContextLogFormatter not available
        test_formatter = logging.Formatter(
            "%(asctime)s - [AI-TEST] - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    test_handler.setFormatter(test_formatter)

    # Configure all existing loggers
    root_logger = logging.getLogger()
    # Clear any existing handlers
    for h in root_logger.handlers[:]:
        try:
            h.close()
        except Exception:
            pass
        root_logger.removeHandler(h)

    # Configure all loggers in the logger dict
    for logger_name in logging.Logger.manager.loggerDict:
        try:
            logger_obj = logging.getLogger(logger_name)

            # Clear existing handlers
            for h in logger_obj.handlers[:]:
                try:
                    h.close()
                except Exception:
                    pass
                logger_obj.removeHandler(h)

            # Set appropriate log level
            if logger_name.startswith("mhm."):
                # Component loggers always use DEBUG level to capture all logs
                level = logging.DEBUG
                logger_obj.setLevel(level)
                logger_obj.addHandler(component_handler)
                logger_obj.propagate = False
            else:
                # Test execution loggers: 0=WARNING, 1=INFO, 2=DEBUG
                verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                if verbose_logs == "2":
                    level = logging.DEBUG
                elif verbose_logs == "1":
                    level = logging.INFO
                else:
                    level = logging.WARNING
                logger_obj.setLevel(level)
                logger_obj.addHandler(test_handler)
                logger_obj.propagate = True

        except Exception:
            # Never fail tests due to logging configuration issues
            continue

    # Also configure the root logger to prevent it from creating duplicate handlers
    root_logger.setLevel(logging.WARNING)
    root_logger.propagate = False

    # Clean up any individual log files that were created
    individual_log_files = [
        "app.log",
        "errors.log",
        "ai.log",
        "discord.log",
        "user_activity.log",
        "communication_manager.log",
        "email.log",
        "ui.log",
        "file_ops.log",
        "scheduler.log",
        "schedule_utilities.log",
        "analytics.log",
        "message.log",
        "backup.log",
        "checkin_dynamic.log",
    ]

    for log_file_name in individual_log_files:
        log_file = Path(tests_logs_dir) / log_file_name
        if log_file.exists():
            try:
                # Copy content to consolidated log if it has useful content
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if len(content) > 0:
                        with open(consolidated_log_file, "a", encoding="utf-8") as cf:
                            cf.write(f"\n# Content from {log_file_name}:\n{content}\n")

                # Remove the individual file
                log_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors


# Set up consolidated logging BEFORE any other imports
setup_consolidated_ai_test_logging()

# Create a test execution logger for the test runner itself
test_logger = logging.getLogger("ai_functionality_tests")
test_logger.setLevel(logging.DEBUG)
# Get the test_run.log handler (it was set up by setup_consolidated_ai_test_logging)
# We need to add it manually since the logger is created after setup
test_run_log_file = Path(tests_logs_dir) / "test_run.log"
test_handler = logging.FileHandler(str(test_run_log_file), mode="a", encoding="utf-8")
try:
    from core.logger import PytestContextLogFormatter

    test_formatter = PytestContextLogFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
except ImportError:
    test_formatter = logging.Formatter(
        "%(asctime)s - [AI-TEST] - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
test_handler.setFormatter(test_formatter)
test_logger.addHandler(test_handler)
test_logger.propagate = False

# Now import modules after logging is configured
from tests.test_utilities import setup_test_data_environment


class AITestResultsCollector:
    """Collects test results from all test modules"""

    def __init__(self):
        self.results = []
        self.performance_metrics = []

    def _rotate_result_files(self, results_dir, max_files=10):
        """Rotate test result files, keeping only the most recent max_files"""
        try:
            import glob

            # Find all timestamped result files
            pattern = os.path.join(results_dir, "ai_functionality_test_results_*.md")
            result_files = glob.glob(pattern)

            # Sort by modification time (newest first)
            result_files.sort(key=os.path.getmtime, reverse=True)

            # Keep only the most recent max_files (excluding latest.md)
            files_to_keep = result_files[:max_files]
            files_to_delete = result_files[max_files:]

            # Delete old files
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Could not delete old result file {file_path}: {e}")

            if files_to_delete:
                print(
                    f"Rotated test results: kept {len(files_to_keep)}, deleted {len(files_to_delete)} old files"
                )
        except Exception as e:
            print(f"Warning: Could not rotate result files: {e}")

    def generate_report(self, project_root):
        """Generate test report with performance metrics"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        partial = sum(1 for r in self.results if r["status"] == "PARTIAL")

        print(f"Total Tests: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[PARTIAL] Partial: {partial}")
        print(f"[FAIL] Failed: {failed}")
        print()

        # Performance summary
        perf_tests = [r for r in self.results if r.get("response_time") is not None]
        if perf_tests:
            avg_time = sum(r["response_time"] for r in perf_tests) / len(perf_tests)
            min_time = min(r["response_time"] for r in perf_tests)
            max_time = max(r["response_time"] for r in perf_tests)
            print("PERFORMANCE METRICS:")
            print(f"  Tests with timing: {len(perf_tests)}")
            print(f"  Average response time: {avg_time:.2f}s")
            print(f"  Min response time: {min_time:.2f}s")
            print(f"  Max response time: {max_time:.2f}s")
            print()

        if failed > 0:
            print("FAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    # Safely encode test name for Windows console
                    try:
                        safe_name = (
                            r["test_name"]
                            .encode("ascii", errors="replace")
                            .decode("ascii")
                        )
                    except:
                        safe_name = r["test_name"]
                    print(f"  - {r['test_id']}: {safe_name}")
                    if r["issues"]:
                        # Safely encode issues for Windows console
                        try:
                            safe_issues = (
                                r["issues"]
                                .encode("ascii", errors="replace")
                                .decode("ascii")
                            )
                        except:
                            safe_issues = "[Issues contain non-displayable characters]"
                        print(f"    Issues: {safe_issues}")
            print()

        if partial > 0:
            print("PARTIAL TESTS (needs review):")
            for r in self.results:
                if r["status"] == "PARTIAL":
                    # Safely encode test name for Windows console
                    try:
                        safe_name = (
                            r["test_name"]
                            .encode("ascii", errors="replace")
                            .decode("ascii")
                        )
                    except:
                        safe_name = r["test_name"]
                    print(f"  - {r['test_id']}: {safe_name}")
                    if r["notes"]:
                        # Safely encode notes for Windows console
                        try:
                            safe_notes = (
                                r["notes"]
                                .encode("ascii", errors="replace")
                                .decode("ascii")
                            )
                        except:
                            safe_notes = "[Notes contain non-displayable characters]"
                        print(f"    Notes: {safe_notes}")
            print()

        # Write detailed report
        results_dir = os.path.join(project_root, "tests", "ai", "results")
        os.makedirs(results_dir, exist_ok=True)

        # Rotate old result files (keep only last 10)
        self._rotate_result_files(results_dir, max_files=10)

        timestamp = now_filename_timestamp()
        report_file = os.path.join(
            results_dir, f"ai_functionality_test_results_{timestamp}.md"
        )
        latest_report = os.path.join(
            results_dir, "ai_functionality_test_results_latest.md"
        )

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# AI Functionality Test Results\n\n")
            f.write(f"**Test Date**: {datetime.now().isoformat()}\n\n")
            f.write(
                f"**Summary**: {passed} passed, {partial} partial, {failed} failed out of {total} tests\n\n"
            )

            if perf_tests:
                f.write("## Performance Metrics\n\n")
                f.write(f"- **Tests with timing data**: {len(perf_tests)}\n")
                f.write(f"- **Average response time**: {avg_time:.2f}s\n")
                f.write(f"- **Min response time**: {min_time:.2f}s\n")
                f.write(f"- **Max response time**: {max_time:.2f}s\n\n")

            f.write("## Detailed Results\n\n")

            # Sort results by test_id (numerical order: T-1.1, T-1.2, T-2.1, etc.)
            def sort_key(r):
                """Extract numeric parts from test_id for proper sorting"""
                test_id = r.get("test_id", "")
                if not test_id or not test_id.startswith("T-"):
                    return (999, 999)  # Put invalid IDs at the end
                try:
                    # Split T-X.Y into (X, Y) for numeric sorting
                    parts = test_id[2:].split(".")
                    if len(parts) == 2:
                        return (int(parts[0]), int(parts[1]))
                    elif len(parts) == 1:
                        return (int(parts[0]), 0)
                    else:
                        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                except (ValueError, IndexError):
                    return (999, 999)  # Put invalid formats at the end

            sorted_results = sorted(self.results, key=sort_key)

            for r in sorted_results:
                status_symbol = {
                    "PASS": "[OK]",
                    "FAIL": "[ERROR]",
                    "PARTIAL": "[WARNING]",
                }.get(r["status"], "[UNKNOWN]")
                f.write(f"### {status_symbol} {r['test_id']}: {r['test_name']}\n\n")
                f.write(f"- **Status**: {r['status']}\n")
                if r.get("prompt"):
                    # Safely handle Unicode in prompt (files use UTF-8, so this should work)
                    prompt = r["prompt"]
                    f.write(f"- **Prompt**: `{prompt}`\n")
                if r.get("response"):
                    # Safely handle Unicode in response (files use UTF-8, so this should work)
                    response = r["response"]
                    if len(response) > 500:
                        response = response[:500] + "... (truncated)"
                    f.write(f"- **Response**: `{response}`\n")
                    f.write(f"- **Response Length**: {len(r['response'])} characters\n")
                if r.get("response_time") is not None:
                    f.write(f"- **Response Time**: {r['response_time']:.2f}s\n")
                if r.get("metrics"):
                    f.write(f"- **Metrics**: {r['metrics']}\n")
                if r.get("context_info"):
                    context = r["context_info"]
                    # Only show fields with meaningful values (not False, 0, empty lists, empty strings, or None)
                    meaningful_context = {
                        k: v
                        for k, v in context.items()
                        if k != "context_keys"
                        and v not in (False, 0, [], "", None)
                        and not (isinstance(v, (list, dict, str)) and len(v) == 0)
                    }

                    # Only show context_keys if they exist and are not empty
                    context_keys = context.get("context_keys", [])
                    if context_keys:
                        meaningful_context["context_keys"] = context_keys

                    if meaningful_context:
                        f.write(f"- **Context Available**:\n")
                        for key, value in meaningful_context.items():
                            f.write(f"  - {key}: {value}\n")
                if r["notes"]:
                    f.write(f"- **Notes**: {r['notes']}\n")
                if r["issues"]:
                    f.write(f"- **Issues**: {r['issues']}\n")
                if r.get("manual_review_notes"):
                    f.write(f"- **Manual Review Notes**: {r['manual_review_notes']}\n")
                f.write(f"- **Timestamp**: {r['timestamp']}\n\n")

        # Copy to latest
        import shutil

        shutil.copy(report_file, latest_report)

        print()
        print("=" * 60)
        print("TEST RESULTS OUTPUT")
        print("=" * 60)
        print(f"Detailed report (timestamped): {report_file}")
        print(f"Latest report (always current): {latest_report}")
        print("=" * 60)

        return {
            "total": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "performance": (
                {
                    "tests_with_timing": len(perf_tests),
                    "avg_time": avg_time if perf_tests else None,
                    "min_time": min_time if perf_tests else None,
                    "max_time": max_time if perf_tests else None,
                }
                if perf_tests
                else None
            ),
        }


def main():
    """Run all AI functionality tests"""
    # Log test run start
    test_logger.info("=" * 80)
    test_logger.info("AI Functionality Test Run Started")
    test_logger.info("=" * 80)

    # Environment variables are already set at module level (before logger initialization)
    # Set up test data environment
    from tests.test_utilities import cleanup_test_data_environment

    test_dir, test_data_dir, _ = setup_test_data_environment()

    # Set test data directory
    os.environ["TEST_DATA_DIR"] = test_data_dir

    test_logs_dir_actual = os.environ.get("LOGS_DIR", "not set")
    test_logger.info(f"Test logs directory: {test_logs_dir_actual}")
    test_logger.info(f"Using test data directory: {test_data_dir}")

    print(f"Test logs directory: {test_logs_dir_actual}")
    print(f"Using test data directory: {test_data_dir}")
    print()

    # Create results collector
    collector = AITestResultsCollector()
    test_logger.info(
        f"Starting test execution with {len(['core', 'integration', 'errors', 'cache', 'performance', 'quality'])} test modules"
    )

    # Import and run test modules
    try:
        # Core tests
        test_logger.info("Running core tests...")
        from tests.ai.test_ai_core import TestAICore

        core_tests = TestAICore(test_data_dir, collector)
        core_tests.test_basic_response_generation()
        core_tests.test_contextual_response_generation()
        core_tests.test_mode_detection()
        core_tests.test_command_variations()

        # Integration tests
        test_logger.info("Running integration tests...")
        from tests.ai.test_ai_integration import TestAIIntegration

        integration_tests = TestAIIntegration(test_data_dir, collector)
        integration_tests.test_context_with_checkins()
        integration_tests.test_conversation_history_in_context()
        integration_tests.test_conversation_history()

        # Error handling tests
        test_logger.info("Running error handling tests...")
        from tests.ai.test_ai_errors import TestAIErrors

        error_tests = TestAIErrors(test_data_dir, collector)
        error_tests.test_error_handling()
        error_tests.test_api_error_scenarios()

        # Cache tests
        test_logger.info("Running cache tests...")
        from tests.ai.test_ai_cache import TestAICache

        cache_tests = TestAICache(test_data_dir, collector)
        cache_tests.test_cache_basic()
        cache_tests.test_cache_comprehensive()

        # Performance tests
        test_logger.info("Running performance tests...")
        from tests.ai.test_ai_performance import TestAIPerformance

        perf_tests = TestAIPerformance(test_data_dir, collector)
        perf_tests.test_performance_metrics()

        # Quality and edge case tests
        test_logger.info("Running quality and edge case tests...")
        from tests.ai.test_ai_quality import TestAIQuality

        quality_tests = TestAIQuality(test_data_dir, collector)
        quality_tests.test_response_quality()
        quality_tests.test_edge_cases()

        # Advanced tests (multi-turn, coherence, personality, error recovery)
        test_logger.info("Running advanced tests...")
        from tests.ai.test_ai_advanced import TestAIAdvanced

        advanced_tests = TestAIAdvanced(test_data_dir, collector)
        advanced_tests.test_multi_turn_conversations()
        advanced_tests.test_personality_consistency()
        advanced_tests.test_error_recovery_scenarios()

        test_logger.info("All test modules completed")

        # Generate report
        summary = collector.generate_report(project_root)

        test_logger.info("=" * 80)
        test_logger.info(
            f"Test Summary: {summary['passed']} passed, {summary['partial']} partial, {summary['failed']} failed out of {summary['total']} tests"
        )
        if summary.get("performance"):
            perf = summary["performance"]
            test_logger.info(
                f"Performance: {perf.get('tests_with_timing', 0)} tests timed, avg: {perf.get('avg_time', 0):.2f}s"
            )
        test_logger.info("=" * 80)

        print("=" * 60)
        if summary["failed"] == 0:
            print("[PASS] ALL TESTS PASSED OR PARTIAL")
        else:
            print(
                f"[PARTIAL] {summary['failed']} TESTS FAILED - Review report for details"
            )
        print("=" * 60)

        return_code = 0 if summary["failed"] == 0 else 1
        test_logger.info(f"Test run completed with return code: {return_code}")
        return return_code

    except Exception as e:
        error_msg = f"Test execution failed: {str(e)}"
        test_logger.error(error_msg, exc_info=True)
        print(f"[FAIL] {error_msg}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Clean up test data directory
        try:
            cleanup_test_data_environment(test_dir)
            cleanup_msg = f"Cleaned up test data directory: {test_dir}"
            test_logger.info(cleanup_msg)
            print(f"\n{cleanup_msg}")
        except Exception as cleanup_error:
            error_msg = f"Could not clean up test data directory: {cleanup_error}"
            test_logger.warning(error_msg)
            print(f"\nWarning: {error_msg}")

        # Clean up test users from tests/data/users/ directory
        # All test users should be cleaned up after tests run
        try:
            test_users_dir = os.path.join(project_root, "tests", "data", "users")
            if os.path.exists(test_users_dir):
                # Remove all user directories (all users in tests/data/users/ are test users)
                for item in os.listdir(test_users_dir):
                    item_path = os.path.join(test_users_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
                    except Exception:
                        pass  # Ignore cleanup errors for individual items

                # Also clean up user_index.json if it exists
                user_index_file = os.path.join(
                    project_root, "tests", "data", "user_index.json"
                )
                if os.path.exists(user_index_file):
                    try:
                        os.remove(user_index_file)
                    except Exception:
                        pass

                cleanup_msg = "Cleaned up test users from tests/data/users/"
                test_logger.info(cleanup_msg)
                print(f"{cleanup_msg}")
        except Exception as cleanup_error:
            error_msg = (
                f"Could not clean up test users from tests/data/users/: {cleanup_error}"
            )
            test_logger.warning(error_msg)
            print(f"\nWarning: {error_msg}")


if __name__ == "__main__":
    sys.exit(main())
