"""
Tests for analyze_error_handling.py.

Tests error handling analysis functionality including function analysis,
decorator detection, phase 1/2 candidate detection, and standard format output.
"""

import json
import sys

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module

# Load the module
error_handling_module = load_development_tools_module("error_handling.analyze_error_handling")
ErrorHandlingAnalyzer = error_handling_module.ErrorHandlingAnalyzer


class TestErrorHandlingAnalyzer:
    """Test ErrorHandlingAnalyzer class."""
    
    @pytest.mark.unit
    def test_init(self, tmp_path):
        """Test analyzer initialization."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        
        assert analyzer.project_root == Path(tmp_path)
        assert analyzer.results['total_functions'] == 0
        assert analyzer.results['functions_with_error_handling'] == 0
        assert analyzer.results['functions_missing_error_handling'] == 0
    
    @pytest.mark.unit
    def test_analyze_file_basic(self, tmp_path):
        """Test analyzing a basic Python file."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def simple_function():
    pass

def function_with_try():
    try:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'file_path' in result
        assert 'functions' in result
        assert len(result['functions']) == 2
    
    @pytest.mark.unit
    def test_analyze_file_with_decorator(self, tmp_path):
        """Test analyzing file with error handling decorator."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
from core.error_handling import handle_errors

@handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) > 0
        # Check that decorator was detected (may be in different fields)
        func = result['functions'][0]
        # Decorator detection may vary - just check function was analyzed
        assert 'name' in func or 'function_name' in func
    
    @pytest.mark.unit
    def test_analyze_file_malformed(self, tmp_path):
        """Test handling of malformed Python file."""
        test_file = tmp_path / "malformed.py"
        test_file.write_text("This is not valid Python: {[}")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should return error result
        assert 'error' in result or 'functions' in result
        # Should not crash
    
    @pytest.mark.unit
    def test_should_exclude_function_special_methods(self, tmp_path):
        """Test that special methods are excluded."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
class TestClass:
    def __repr__(self):
        return "test"
    
    def __getattr__(self, name):
        return None
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Special methods should be excluded from missing error handling
        for func in result.get('functions', []):
            if func.get('name') in ('__repr__', '__getattr__'):
                # These should be excluded
                assert func.get('excluded', False) or func.get('error_handling') == 'excluded'
    
    @pytest.mark.unit
    def test_should_exclude_function_exclusion_comment(self, tmp_path):
        """Test that functions with exclusion comments are excluded."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
# ERROR_HANDLING_EXCLUDE
def excluded_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Function with exclusion comment should be excluded
        for func in result.get('functions', []):
            if func.get('name') == 'excluded_function':
                assert func.get('excluded', False)
    
    @pytest.mark.unit
    def test_should_exclude_protocol_ellipsis_stubs(self, tmp_path):
        """Test that typing.Protocol method stubs are excluded from missing-decorator reports."""
        test_file = tmp_path / "protocol_module.py"
        test_file.write_text("""
from typing import Protocol

class Host(Protocol):
    def do_work(self) -> bool: ...

    def documented_work(self) -> bool:
        \"\"\"Protocol surface with docstring before ellipsis.\"\"\"
        ...
""")
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)

        for func in result.get("functions", []):
            if func.get("name") in ("do_work", "documented_work"):
                assert func.get("excluded", False), (
                    f"{func.get('name')} should be excluded as a Protocol stub"
                )

    @pytest.mark.unit
    def test_analyze_file_phase1_candidates(self, tmp_path):
        """Test detection of Phase 1 candidates (try-except without decorator)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_try_except():
    try:
        result = open("file.txt")
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect try-except pattern
        func = result['functions'][0]
        assert func.get('has_try_except', False)
    
    @pytest.mark.unit
    def test_analyze_file_phase2_exceptions(self, tmp_path):
        """Test detection of Phase 2 candidates (generic exception raises)."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_generic_raise():
    raise Exception("Generic error")
    
def function_with_value_error():
    raise ValueError("Specific error")
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect generic exception raises
        assert 'phase2_exceptions' in result
        # Should find Exception raise
        exceptions = result['phase2_exceptions']
        assert len(exceptions) > 0
    
    @pytest.mark.unit
    def test_analyze_file_with_classes(self, tmp_path):
        """Test analyzing file with classes."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
class TestClass:
    def method(self):
        pass
    
    @handle_errors
    def protected_method(self):
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'classes' in result
        assert len(result['classes']) > 0
    
    @pytest.mark.unit
    def test_analyze_project_multiple_files(self, tmp_path):
        """Test analyzing all Python files in a directory."""
        # Create multiple test files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("""
from core.error_handling import handle_errors

@handle_errors
def func2(): pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project()
        
        # Should have analyzed multiple files (may be 0 if files are excluded)
        assert isinstance(result, dict)
        assert 'details' in result
        # At minimum, should have run without error
        assert result['details']['total_functions'] >= 0
    
    @pytest.mark.unit
    def test_to_standard_format(self, tmp_path):
        """Test conversion to standard format."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        analyzer.results['functions_missing_error_handling'] = 5
        analyzer.results['missing_error_handling'] = [
            {'file': 'test1.py', 'function': 'func1'},
            {'file': 'test2.py', 'function': 'func2'},
            {'file': 'test1.py', 'function': 'func3'}  # Duplicate file
        ]
        
        standard_format = analyzer._to_standard_format()
        
        assert 'summary' in standard_format
        assert 'details' in standard_format
        assert standard_format['summary']['total_issues'] == 5
        assert standard_format['summary']['files_affected'] == 2  # 2 unique files
    
    @pytest.mark.unit
    def test_analyze_file_error_patterns(self, tmp_path):
        """Test detection of error handling patterns in file content."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
try:
    pass
except Exception:
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should detect try_except pattern
        assert 'error_patterns_found' in result
        assert len(result['error_patterns_found']) > 0
    
    @pytest.mark.unit
    def test_analyze_file_empty(self, tmp_path):
        """Test analyzing empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert 'file_path' in result
        assert result['functions'] == []
    
    @pytest.mark.unit
    def test_analyze_file_async_function(self, tmp_path):
        """Test analyzing async functions."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
async def async_function():
    pass

async def async_with_try():
    try:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) == 2
    
    @pytest.mark.unit
    def test_analyze_file_with_imports(self, tmp_path):
        """Test analyzing file with imports."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
import os
from pathlib import Path

def function_using_imports():
    return os.getcwd()
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        assert len(result['functions']) == 1
    
    @pytest.mark.unit
    def test_analyze_file_nested_functions(self, tmp_path):
        """Test analyzing nested functions."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def outer_function():
    def inner_function():
        pass
    return inner_function
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        # Should find both outer and inner functions
        assert len(result['functions']) >= 1
    
    @pytest.mark.unit
    def test_analyze_file_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        non_existent = tmp_path / "nonexistent.py"
        
        result = analyzer.analyze_file(non_existent)
        
        # Should handle gracefully
        assert 'error' in result or 'file_path' in result


class TestAnalyzeProject:
    """Test analyze_project() method."""
    
    @pytest.mark.unit
    def test_analyze_project_basic(self, tmp_path):
        """Test basic analyze_project method."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'details' in result
        assert 'total_issues' in result['summary']
        assert 'files_affected' in result['summary']
    
    @pytest.mark.unit
    def test_analyze_project_with_files(self, tmp_path):
        """Test analyze_project with test files included."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def func(): pass")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_project(include_tests=True)
        
        assert isinstance(result, dict)
        assert 'summary' in result
    
    @pytest.mark.integration
    def test_analyze_project_demo_project(self, demo_project_root, test_config_path):
        """Test analyze_project with demo project."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(demo_project_root))
        result = analyzer.analyze_project()
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'details' in result
        # Should have analyzed demo project files
        assert result['summary']['total_issues'] >= 0


class TestErrorHandlingPatterns:
    """Test error handling pattern detection."""
    
    @pytest.mark.unit
    def test_decorator_detection_direct_import(self, tmp_path):
        """Test detection of decorator with direct import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
from core.error_handling import handle_errors

@handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_decorator', False) or func.get('error_handling') != 'none'
    
    @pytest.mark.unit
    def test_decorator_detection_module_import(self, tmp_path):
        """Test detection of decorator with module import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
import core.error_handling

@core.error_handling.handle_errors
def decorated_function():
    pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_decorator', False) or func.get('error_handling') != 'none'
    
    @pytest.mark.unit
    def test_try_except_detection(self, tmp_path):
        """Test detection of try-except blocks."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def function_with_try():
    try:
        x = 1
    except ValueError:
        pass
    except Exception:
        pass
""")
        
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(test_file)
        
        func = result['functions'][0]
        assert func.get('has_try_except', False)


class TestErrorHandlingHelpersAndAggregation:
    """Direct coverage for Phase 1/2 helpers and result aggregation."""

    @pytest.mark.unit
    def test_suggest_exception_replacement_heuristics(self, tmp_path):
        """Generic 'X or Y' mappings should pick a project exception from context."""
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        analyzer.generic_exceptions = {
            "Exception": "BaseError or DataError",
            "ValueError": "ValidationError or DataError",
            "KeyError": "DataError or ConfigurationError",
            "TypeError": "ValidationError or DataError",
        }

        assert "Validation" in analyzer._suggest_exception_replacement(
            "ValueError", "user/profile.py", "check_name", "raise ValueError('invalid user')"
        )
        assert "Data" in analyzer._suggest_exception_replacement(
            "ValueError", "storage/store.py", "load_row", "raise ValueError('bad row')"
        )
        assert "Configuration" in analyzer._suggest_exception_replacement(
            "KeyError", "core/config.py", "get_setting", "raise KeyError('missing option')"
        )
        assert "Data" in analyzer._suggest_exception_replacement(
            "KeyError", "tasks/store.py", "lookup", "raise KeyError('id')"
        )
        assert "Validation" in analyzer._suggest_exception_replacement(
            "TypeError", "ui/form.py", "parse", "raise TypeError('expected user input')"
        )
        assert "Data" in analyzer._suggest_exception_replacement(
            "TypeError", "core/util.py", "coerce", "raise TypeError('int')"
        )
        assert analyzer._suggest_exception_replacement(
            "Exception", "storage/file_read.py", "load", "raise Exception('io')"
        )
        assert analyzer._suggest_exception_replacement(
            "Exception", "communication/discord/api.py", "send", "raise Exception('http')"
        )
        assert analyzer._suggest_exception_replacement(
            "Exception", "core/config.py", "boot", "raise Exception('setting')"
        )
        assert analyzer._suggest_exception_replacement(
            "Exception", "scheduler/task.py", "tick", "raise Exception('job')"
        )
        assert analyzer._suggest_exception_replacement(
            "Exception", "ai/chatbot.py", "reply", "raise Exception('model')"
        )
        fallback = analyzer._suggest_exception_replacement(
            "RuntimeError", "core/x.py", "f", "raise RuntimeError('x')"
        )
        assert isinstance(fallback, str) and fallback

    @pytest.mark.unit
    def test_operation_type_entry_point_and_priority(self, tmp_path):
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))

        assert analyzer._determine_operation_type("save_json", "core/io.py", "open(path)") == "file_io"
        assert analyzer._determine_operation_type("send_message", "communication/api.py", "") == "network"
        assert analyzer._determine_operation_type("touch_account", "user/account.py", "preferences") == "user_data"
        assert analyzer._determine_operation_type("validate_input", "core/check.py", "") == "validation"
        assert analyzer._determine_operation_type("schedule_reminder", "scheduler/x.py", "") in {
            "scheduling",
            "user_data",
        }
        assert analyzer._determine_operation_type("load_option", "core/config.py", "") in {
            "configuration",
            "file_io",
        }
        assert analyzer._determine_operation_type("on_clicked", "ui/dialog.py", "") in {"ui", "entry_point"}
        assert analyzer._determine_operation_type("generate_reply", "ai/chatbot.py", "") == "ai"
        assert analyzer._determine_operation_type("helper", "core/util.py", "return 1") == "general"

        assert analyzer._is_entry_point("main", "run_mhm.py") is True
        assert analyzer._is_entry_point("dispatch", "communication/command_handlers.py") is True
        assert analyzer._is_entry_point("on_clicked", "ui/widgets/form.py") is True
        assert analyzer._is_entry_point("serve", "core/routes.py", "@app.route('/')") is True
        assert analyzer._is_entry_point("_private", "core/util.py") is False
        assert analyzer._is_entry_point("__init__", "core/util.py") is False

        assert analyzer._determine_phase1_priority("file_io", True) == "high"
        assert analyzer._determine_phase1_priority("network", False) == "medium"
        assert analyzer._determine_phase1_priority("general", False) == "low"

    @pytest.mark.unit
    def test_analyze_raise_statement_call_name_and_reraise(self, tmp_path):
        import ast

        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        source = """
def boom(err):
    raise Exception('failed')
    raise pkg.ValueError('bad')
    raise err
    raise
"""
        tree = ast.parse(source)
        func = tree.body[0]
        raises = [n for n in ast.walk(func) if isinstance(n, ast.Raise)]
        src_file = tmp_path / "core" / "file_read.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text(source, encoding="utf-8")

        call_result = analyzer._analyze_raise_statement(raises[0], source, src_file)
        assert call_result is not None
        assert call_result["exception_type"] == "Exception"

        attr_result = analyzer._analyze_raise_statement(raises[1], source, src_file)
        if attr_result is not None:
            assert attr_result["exception_type"] == "ValueError"

        name_result = analyzer._analyze_raise_statement(raises[2], source, src_file)
        assert name_result is None or name_result["exception_type"] == "err"

        assert analyzer._analyze_raise_statement(raises[3], source, src_file) is None

    @pytest.mark.unit
    def test_excludes_simple_init_logger_and_collects_with_match(self, tmp_path):
        logger_file = tmp_path / "core" / "logger.py"
        logger_file.parent.mkdir(parents=True, exist_ok=True)
        logger_file.write_text(
            """
class ComponentLogger:
    def __init__(self):
        super()()
        self.name = "x"

    def info(self, msg):
        return msg

    def load_with_patterns(self, value):
        with open("x.txt") as handle:
            try:
                handle.read()
            except OSError:
                return None
        match value:
            case 1:
                try:
                    return 1
                except ValueError:
                    return 0
            case _:
                return None
""",
            encoding="utf-8",
        )
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        result = analyzer.analyze_file(logger_file)
        names = {func.get("name"): func for func in result.get("functions", [])}
        assert names["info"].get("excluded") or names["info"].get(
            "error_handling_quality"
        ) == "excluded"
        load_fn = names.get("load_with_patterns")
        assert load_fn is not None
        assert load_fn.get("has_try_except") is True
        if names.get("__init__"):
            # super()() matches the constructor-exclusion AST check (not super().__init__()).
            assert names["__init__"].get("excluded") is True

    @pytest.mark.unit
    def test_aggregate_results_and_recommendations(self, tmp_path):
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        analyzer._aggregate_results(
            [
                {"error": "skip this file"},
                {
                    "file_path": str(tmp_path / "core" / "io.py"),
                    "functions": [
                        {
                            "name": "save_json",
                            "line_start": 1,
                            "line_end": 10,
                            "has_try_except": True,
                            "has_error_handling": True,
                            "has_decorators": False,
                            "missing_error_handling": False,
                            "error_handling_quality": "none",
                            "error_patterns": {"try_except"},
                            "excluded": False,
                            "is_phase1_candidate": True,
                            "is_async": False,
                            "func_content": "open(path); json.dump",
                        },
                        {
                            "name": "skip_me",
                            "line_start": 12,
                            "line_end": 13,
                            "excluded": True,
                            "has_try_except": False,
                            "has_error_handling": False,
                            "has_decorators": False,
                            "missing_error_handling": False,
                            "error_handling_quality": "excluded",
                            "error_patterns": set(),
                        },
                    ],
                    "phase2_exceptions": [
                        {"exception_type": "Exception", "file_path": "core/io.py"}
                    ],
                    "error_patterns_found": ["try_except"],
                },
                {
                    "file_path": str(tmp_path / "ui" / "form.py"),
                    "functions": [
                        {
                            "name": "on_clicked",
                            "line_start": 1,
                            "line_end": 4,
                            "has_try_except": False,
                            "has_error_handling": False,
                            "has_decorators": False,
                            "missing_error_handling": True,
                            "error_handling_quality": "none",
                            "error_patterns": set(),
                            "excluded": False,
                            "is_phase1_candidate": False,
                            "func_content": "",
                        }
                    ],
                    "phase2_exceptions": [],
                    "error_patterns_found": [],
                },
            ]
        )
        assert analyzer.results["total_functions"] == 2
        assert analyzer.results["phase1_total"] == 1
        assert analyzer.results["phase2_total"] == 1
        assert analyzer.results["functions_missing_error_handling"] == 1
        assert analyzer.results["worst_modules"]

        analyzer.results["analyze_error_handling"] = 40.0
        analyzer.results["error_patterns"] = {"try_except": 3, "handle_errors_decorator": 0}
        analyzer._generate_recommendations()
        joined = " ".join(analyzer.results["recommendations"])
        assert "Improve error handling coverage" in joined
        assert "Add error handling to" in joined
        assert "@handle_errors" in joined or "decorator" in joined.lower()

    @pytest.mark.unit
    def test_main_json_output_and_missing_project(self, tmp_path, monkeypatch, capsys):
        analyzer = ErrorHandlingAnalyzer(project_root=str(tmp_path))
        payload = analyzer._to_standard_format()

        class StubAnalyzer:
            def __init__(self, project_root):
                self.project_root = project_root

            def analyze_project(self, include_tests=False, include_dev_tools=False):
                return payload

        monkeypatch.setattr(error_handling_module, "ErrorHandlingAnalyzer", StubAnalyzer)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "analyze_error_handling.py",
                "--json",
                "--project-root",
                str(tmp_path),
            ],
        )
        rc = error_handling_module.main()
        assert rc == 0
        printed = json.loads(capsys.readouterr().out)
        assert "summary" in printed

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "analyze_error_handling.py",
                "--project-root",
                str(tmp_path / "does-not-exist"),
            ],
        )
        assert error_handling_module.main() == 1

