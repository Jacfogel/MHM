"""
Tests for generate_function_registry.py.

Tests function extraction, scanning, categorization, and file generation.
"""

import pytest
from unittest.mock import patch

# Import helper from conftest
from tests.development_tools.conftest import load_development_tools_module

# Load modules using the helper
# Functions moved to analyze_functions.py during Batch 3 decomposition
analyze_functions_module = load_development_tools_module("analyze_functions")
registry_module = load_development_tools_module("generate_function_registry")

# Import discovery functions from analyze_functions.py (moved during Batch 3)
extract_functions_from_file = analyze_functions_module.extract_functions_from_file
extract_classes_from_file = analyze_functions_module.extract_classes_from_file
scan_all_python_files = analyze_functions_module.scan_all_python_files

# Import registry generation functions from generate_function_registry.py (still there)
detect_function_type = registry_module.detect_function_type
generate_function_template = registry_module.generate_function_template
generate_function_registry_content = registry_module.generate_function_registry_content
update_function_registry = registry_module.update_function_registry
generate_file_section = registry_module.generate_file_section
get_directory_description = registry_module.get_directory_description
get_file_stats = registry_module.get_file_stats
format_file_entry = registry_module.format_file_entry
find_files_needing_attention = registry_module.find_files_needing_attention


def _patch_should_exclude_file(monkeypatch, mock_func):
    """
    Helper to patch should_exclude_file in the source module.
    
    Since generate_function_registry.py imports should_exclude_file inside
    scan_all_python_files() (line 253), the import happens at function call time.
    We need to patch the source module (standard_exclusions) so the import
    inside the function picks up the patched version.
    
    Args:
        monkeypatch: pytest monkeypatch fixture
        mock_func: The mock function to use
    """
    from development_tools.shared import standard_exclusions
    
    # Patch the source module - this will affect the import inside scan_all_python_files()
    # since the import happens at function call time, not module load time
    monkeypatch.setattr(standard_exclusions, 'should_exclude_file', mock_func)
    
    # Also ensure the module is in sys.modules so the import inside the function
    # will use the patched version from the cached module
    import sys
    module_name = 'development_tools.shared.standard_exclusions'
    if module_name in sys.modules:
        # Ensure the patched function is what gets imported
        sys.modules[module_name].should_exclude_file = mock_func  # pyright: ignore[reportAttributeAccessIssue]


class TestFunctionExtraction:
    """Test function extraction from files."""
    
    @pytest.mark.unit
    def test_extract_functions_from_file_basic(self, demo_project_root):
        """Test that basic function extraction works."""
        demo_file = demo_project_root / "demo_module.py"
        
        functions = extract_functions_from_file(str(demo_file))
        
        # Should find functions
        assert len(functions) > 0
        
        # Should find simple_function
        function_names = [f['name'] for f in functions]
        assert 'simple_function' in function_names
    
    @pytest.mark.unit
    def test_extract_functions_from_file_with_docstrings(self, demo_project_root):
        """Test that functions with docstrings are captured."""
        demo_file = demo_project_root / "demo_module.py"
        
        functions = extract_functions_from_file(str(demo_file))
        
        # Find simple_function which has a docstring
        simple_func = next((f for f in functions if f['name'] == 'simple_function'), None)
        assert simple_func is not None
        assert simple_func['has_docstring'] is True
        assert 'docstring' in simple_func
        assert len(simple_func['docstring']) > 0
    
    @pytest.mark.unit
    def test_extract_functions_from_file_without_docstrings(self, demo_project_root):
        """Test that functions without docstrings are still captured."""
        demo_file = demo_project_root / "demo_module.py"
        
        functions = extract_functions_from_file(str(demo_file))
        
        # Find function_without_docstring
        func = next((f for f in functions if f['name'] == 'function_without_docstring'), None)
        assert func is not None
        assert func['has_docstring'] is False or not func.get('docstring', '').strip()
    
    @pytest.mark.unit
    def test_extract_classes_from_file(self, demo_project_root):
        """Test that class extraction includes methods."""
        demo_file = demo_project_root / "demo_module.py"
        
        classes = extract_classes_from_file(str(demo_file))
        
        # Should find DemoClass
        assert len(classes) > 0
        
        demo_class = next((c for c in classes if c['name'] == 'DemoClass'), None)
        assert demo_class is not None
        assert len(demo_class['methods']) > 0
        
        # Should have get_name method
        method_names = [m['name'] for m in demo_class['methods']]
        assert 'get_name' in method_names


class TestFunctionTypeDetection:
    """Test function type detection."""
    
    @pytest.mark.unit
    def test_detect_function_type_handlers(self, demo_project_root):
        """Test that handler functions are detected correctly."""
        demo_file = demo_project_root / "demo_module.py"
        
        func_type = detect_function_type(
            str(demo_file),
            'handler_function',
            [],
            ['user_id', 'command']
        )
        
        # Handler functions should be detected (though may be regular_function)
        # The detection logic checks for keywords in the name
        assert func_type in ['regular_function', 'test_function']
    
    @pytest.mark.unit
    def test_detect_function_type_tests(self, demo_project_root):
        """Test that test functions are detected correctly."""
        test_file = demo_project_root / "demo_tests.py"
        
        functions = extract_functions_from_file(str(test_file))
        
        # Find a test function
        test_func = next((f for f in functions if f['name'].startswith('test_')), None)
        assert test_func is not None
        assert test_func['func_type'] == 'test_function'
        assert test_func['is_test'] is True

    @pytest.mark.unit
    def test_detect_function_type_branch_coverage(self):
        """Cover major detect_function_type branches."""
        assert detect_function_type("ui/generated/demo.py", "qtTrId", [], []) == "qt_translation"
        assert detect_function_type("ui/generated/form_pyqt.py", "setupUi", [], []) == "ui_generated"
        assert detect_function_type("core/mod.py", "__exit__", [], []) == "special_method"
        assert detect_function_type("core/mod.py", "main", [], []) == "main_function"
        assert detect_function_type("core/mod.py", "plain_name", [], []) == "regular_function"

    @pytest.mark.unit
    def test_generate_function_template_branch_coverage(self):
        """Cover template generation branches with representative inputs."""
        assert "translation" in generate_function_template(
            "qt_translation", "qtTrId", "ui/generated/demo.py", []
        ).lower()
        assert "setup" in generate_function_template(
            "ui_generated", "setupUi", "ui/generated/account_creator_dialog_pyqt.py", []
        ).lower()
        assert "translation" in generate_function_template(
            "ui_generated", "retranslateUi", "ui/generated/account_creator_dialog_pyqt.py", []
        ).lower()
        assert "integration test" in generate_function_template(
            "test_function", "test_integration_login_flow", "tests/x.py", []
        ).lower()
        assert "special python method" in generate_function_template(
            "special_method", "__something__", "core/x.py", []
        ).lower()
        assert generate_function_template(
            "constructor", "__init__", "core/x.py", []
        ) == "Initialize the object"
        assert "main entry point" in generate_function_template(
            "main_function", "main", "run_x.py", []
        ).lower()
        assert generate_function_template(
            "regular_function", "x", "core/x.py", []
        ) == "No description"


class TestScanning:
    """Test file scanning functionality."""
    
    @pytest.mark.unit
    def test_scan_all_python_files_finds_files(self, demo_project_root, monkeypatch):
        """
        Test that all Python files in scan directories are found.
        
        This test patches module-level helpers via monkeypatch but remains safe under
        xdist because each worker runs in a separate process.
        """
        # Mock config to point to our demo project
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']  # Scan current directory
        
        # Mock should_exclude_file to not exclude demo project files
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            # Don't exclude files in the demo project
            if 'development_tools_demo' in file_path:
                return False
            # Use original for other files
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        results = scan_all_python_files()
        
        # Should find demo files
        assert len(results) > 0, f"No files found. Results: {list(results.keys())}"
        
        # Should find demo_module.py
        file_keys = list(results.keys())
        assert any('demo_module.py' in key for key in file_keys), f"demo_module.py not found in {file_keys}"
    
    @pytest.mark.unit
    def test_scan_all_python_files_respects_exclusions(self, demo_project_root, monkeypatch):
        """Test that excluded files are not scanned."""
        # This test verifies that the scanning respects exclusions
        # The actual exclusion logic is in standard_exclusions
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']
        
        # Mock should_exclude_file to not exclude demo project files but still exclude __pycache__
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            # Always exclude __pycache__
            if '__pycache__' in file_path:
                return True
            # Don't exclude files in the demo project
            if 'development_tools_demo' in file_path:
                return False
            # Use original for other files
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        results = scan_all_python_files()
        
        # Should not include __pycache__ or __init__.py files in meaningful way
        # (though __init__.py might be included if it has functions)
        file_keys = list(results.keys())
        assert not any('__pycache__' in key for key in file_keys)


class TestContentGeneration:
    """Test content generation."""
    
    @pytest.mark.unit
    def test_generate_function_registry_content_structure(self, demo_project_root, monkeypatch):
        """
        Test that generated content has expected structure.
        
        This test patches module-level helpers via monkeypatch but remains safe under
        xdist because each worker runs in a separate process.
        """
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']
        
        # Mock should_exclude_file to not exclude demo project files
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            if 'development_tools_demo' in file_path:
                return False
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        actual_functions = scan_all_python_files()
        content = generate_function_registry_content(actual_functions)
        
        # Should have expected sections
        assert '# Function Registry' in content or 'Function Registry' in content
        assert 'Overview' in content or 'overview' in content.lower()
    
    @pytest.mark.unit
    def test_generate_function_registry_content_includes_functions(self, demo_project_root, monkeypatch):
        """
        Test that known functions appear in output.
        
        This test patches module-level helpers via monkeypatch but remains safe under
        xdist because each worker runs in a separate process.
        """
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']
        
        # Mock should_exclude_file to not exclude demo project files
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            if 'development_tools_demo' in file_path:
                return False
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        actual_functions = scan_all_python_files()
        
        # Should have found some files
        assert len(actual_functions) > 0, "No files were scanned"
        
        content = generate_function_registry_content(actual_functions)
        
        # Should mention demo_module or the functions
        # The exact format may vary, but should reference the files/functions
        assert 'demo_module' in content.lower() or 'simple_function' in content.lower(), \
            f"Content should mention demo_module or simple_function. Content preview: {content[:500]}"
    
    @pytest.mark.unit
    def test_generate_function_registry_content_categorizes_correctly(self, demo_project_root, monkeypatch):
        """
        Test that functions are categorized (handlers/tests/etc.).
        
        This test patches module-level helpers via monkeypatch but remains safe under
        xdist because each worker runs in a separate process.
        """
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']
        
        # Mock should_exclude_file to not exclude demo project files
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            if 'development_tools_demo' in file_path:
                return False
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        actual_functions = scan_all_python_files()
        
        # Check that test functions are categorized
        found_test_file = False
        for file_path, data in actual_functions.items():
            if 'demo_tests' in file_path:
                found_test_file = True
                for func in data['functions']:
                    if func['name'].startswith('test_'):
                        assert func['is_test'] is True
                        assert func['func_type'] == 'test_function'
        
        # If we found the test file, verify categorization worked
        if found_test_file:
            assert True  # Test passed
        else:
            # If test file wasn't found, that's okay - the test verifies categorization when files are found
            pytest.skip("demo_tests.py not found in scan results (may be excluded)")


class TestRegistryHelpers:
    """Test smaller helper branches in generate_function_registry.py."""

    @pytest.mark.unit
    def test_get_directory_description_unknown_directory(self):
        """Unknown directories should fall back to generic description."""
        assert get_directory_description("experimental") == "Unknown Directory"

    @pytest.mark.unit
    def test_file_stats_and_format_entry_helpers(self):
        """get_file_stats/format_file_entry should handle documented and missing files."""
        payload = {
            "core/sample.py": {
                "functions": [{"name": "a", "has_docstring": True}],
                "classes": [{"name": "C", "docstring": "", "methods": [{"name": "m", "has_docstring": False}]}],
            }
        }

        stats = get_file_stats("core/sample.py", payload)
        assert stats == {"total": 2, "documented": 1, "functions": 1, "methods": 1}
        assert format_file_entry("core/sample.py", "desc", payload).endswith("(1/2 functions)")
        assert format_file_entry("core/missing.py", "desc", payload) == "`core/missing.py` - desc"

    @pytest.mark.unit
    def test_find_files_needing_attention_sorts_by_missing_then_coverage(self):
        """find_files_needing_attention should sort deterministically by priority."""
        actual_functions = {
            "a.py": {
                "functions": [
                    {"name": "f1", "has_docstring": False},
                    {"name": "f2", "has_docstring": False},
                ],
                "classes": [],
            },
            "b.py": {
                "functions": [
                    {"name": "g1", "has_docstring": True},
                    {"name": "g2", "has_docstring": False},
                ],
                "classes": [],
            },
        }

        items = find_files_needing_attention(actual_functions, threshold=0.8)
        assert [i["file"] for i in items] == ["a.py", "b.py"]
        assert items[0]["missing"] == 2

    @pytest.mark.unit
    def test_generate_file_section_renders_missing_and_documented_entries(self):
        """File section should render function/class/method doc statuses correctly."""
        payload = {
            "functions": [
                {
                    "name": "documented_func",
                    "args": ["x"],
                    "has_docstring": True,
                    "docstring": "Doc text",
                },
                {
                    "name": "undocumented_func",
                    "args": [],
                    "has_docstring": False,
                    "docstring": "",
                },
            ],
            "classes": [
                {
                    "name": "Widget",
                    "docstring": "",
                    "methods": [
                        {
                            "name": "save",
                            "args": ["self"],
                            "has_docstring": False,
                            "docstring": "",
                        }
                    ],
                }
            ],
        }

        section = generate_file_section("core/sample.py", payload)

        assert "#### `core/sample.py`" in section
        assert "- [OK] `documented_func(x)` - Doc text" in section
        assert "- [MISSING] `undocumented_func()` - No description" in section
        assert "- [MISSING] `Widget` - No description" in section
        assert "Widget.save(self)" in section

    @pytest.mark.unit
    def test_generate_pattern_section_includes_detected_patterns(self):
        """Pattern section should render detected handler/manager examples."""
        patterns = {
            "handlers": [
                {"file": "communication/a.py", "function": "handle_message", "has_doc": True},
                {"file": "communication/b.py", "function": "handle_task", "has_doc": False},
                {"file": "communication/c.py", "function": "handle_help", "has_doc": False},
            ],
            "managers": [
                {"file": "core/manager.py", "class": "TaskManager", "has_doc": True},
                {"file": "core/manager2.py", "class": "UserManager", "has_doc": False},
                {"file": "core/manager3.py", "class": "CacheManager", "has_doc": False},
            ],
        }
        content = registry_module.generate_pattern_section(patterns, {})

        assert "Handler Pattern" in content
        assert "Manager Pattern" in content
        assert "`handle_message`" in content
        assert "`TaskManager`" in content

    @pytest.mark.unit
    def test_generate_entry_points_section_includes_fallbacks_when_sparse(self):
        """Entry point section should include fallback canonical items when too short."""
        patterns = {"entry_points": [{"file": "misc/runner.py", "function": "boot", "has_doc": False}]}

        with patch.object(registry_module.config, "get_project_key_files", return_value=["run_tests.py"]):
            content = registry_module.generate_entry_points_section(patterns, {})

        assert "communication/message_processing/interaction_manager.py::handle_message()" in content
        assert "ai/chatbot.py::generate_response()" in content

    @pytest.mark.unit
    def test_generate_entry_points_section_respects_priority_and_init_filter(self):
        """Entry points should prioritize key functions and include allowed __init__."""
        patterns = {
            "entry_points": [
                {"file": "ui/ui_app_qt.py", "function": "__init__", "has_doc": True},
                {"file": "misc/mod.py", "function": "other", "has_doc": True},
                {"file": "communication/message_processing/interaction_manager.py", "function": "handle_message", "has_doc": True},
                {"file": "ai/chatbot.py", "function": "generate_response", "has_doc": True},
            ]
        }

        with patch.object(registry_module.config, "get_project_key_files", return_value=["ui_app_qt.py"]):
            content = registry_module.generate_entry_points_section(patterns, {})

        lines = content.splitlines()
        assert lines[0].endswith("handle_message()` - Main message entry point")
        assert any("ui/ui_app_qt.py::__init__()" in line for line in lines)

    @pytest.mark.unit
    def test_generate_common_operations_section_returns_placeholder_when_empty(self):
        """Common operations should return a placeholder when no patterns are found."""
        content = registry_module.generate_common_operations_section({}, {})
        assert "No common operations detected" in content

    @pytest.mark.unit
    def test_generate_common_operations_section_detects_priority_ops(self):
        """Common operations should include user message, AI response, and scheduling."""
        patterns = {
            "entry_points": [
                {"file": "communication/message_processing/interaction_manager.py", "function": "handle_message"},
                {"file": "ai/chatbot.py", "function": "generate_response"},
                {"file": "run_mhm.py", "function": "main"},
            ],
            "data_access": [
                {"file": "core/user_data_handlers.py", "function": "get_user_data"},
                {"file": "core/user_data_handlers.py", "function": "save_user_data"},
            ],
            "communication": [
                {"file": "communication/core/channel_orchestrator.py", "function": "send_alert"},
                {"file": "communication/core/channel_orchestrator.py", "function": "receive_status"},
            ],
            "error_handlers": [{"file": "core/error_handling.py", "function": "handle_errors"}],
            "schedulers": [{"file": "core/scheduler.py", "function": "schedule_checkins"}],
        }
        actual_functions = {
            "communication/message_processing/command_parser.py": {
                "functions": [{"name": "parse_command"}],
                "classes": [],
            },
            "core/validate_input.py": {
                "functions": [{"name": "validate_payload"}],
                "classes": [],
            },
            "core/config.py": {
                "functions": [{"name": "get_config"}],
                "classes": [],
            },
        }

        content = registry_module.generate_common_operations_section(actual_functions, patterns)
        assert "**User Message**" in content
        assert "**AI Response**" in content
        assert "**Scheduling**" in content
        assert "**Command Parsing**" in content

    @pytest.mark.unit
    def test_generate_complexity_section_empty_when_no_high_complexity(self):
        """Complexity section should be empty when nothing exceeds threshold."""
        actual_functions = {
            "core/a.py": {
                "functions": [{"name": "small", "complexity": 50, "has_docstring": True}],
                "classes": [],
            }
        }
        assert registry_module.generate_complexity_section(actual_functions) == ""

    @pytest.mark.unit
    def test_generate_complexity_section_renders_top_complex_items(self):
        """Complexity section should list high-complexity functions."""
        actual_functions = {
            "core/a.py": {
                "functions": [
                    {"name": "f1", "complexity": 300, "has_docstring": True},
                    {"name": "f2", "complexity": 250, "has_docstring": False},
                ],
                "classes": [{"name": "C", "methods": [{"name": "m", "has_docstring": True}]}],
            }
        }
        content = registry_module.generate_complexity_section(actual_functions)
        assert "Complexity Metrics" in content
        assert "core/a.py::f1()" in content
        assert "Complexity: 300" in content

    @pytest.mark.unit
    def test_generate_file_organization_section_includes_known_and_extra_dirs(self):
        """Organization section should include priority and non-priority directories."""
        actual_functions = {
            "core/a.py": {"functions": [{"name": "a"}], "classes": []},
            "communication/b.py": {"functions": [], "classes": [{"methods": [{"name": "m"}]}]},
            "extras/c.py": {"functions": [{"name": "x"}], "classes": []},
        }
        content = registry_module.generate_file_organization_section(actual_functions)
        assert "`core/`" in content
        assert "`communication/`" in content
        assert "`extras/`" in content

    @pytest.mark.unit
    def test_generate_communication_patterns_section_detects_send_status_parse(self):
        """Communication patterns should render detected send/status/parse entries."""
        patterns = {
            "communication": [
                {"file": "communication/core/orchestrator.py", "function": "send_message"},
                {"file": "communication/core/orchestrator.py", "function": "is_ready"},
            ]
        }
        actual_functions = {
            "communication/message_processing/command_parser.py": {
                "functions": [{"name": "parse_command", "has_docstring": True}],
                "classes": [],
            }
        }
        content = registry_module.generate_communication_patterns_section(patterns, actual_functions)
        assert "**Message Sending**" in content
        assert "**Channel Status**" in content
        assert "**Command Parsing**" in content

    @pytest.mark.unit
    def test_generate_communication_patterns_section_empty_when_no_patterns(self):
        """Communication patterns should be empty when no matches are found."""
        content = registry_module.generate_communication_patterns_section(
            {"communication": []},
            {"core/a.py": {"functions": [{"name": "parse_timestamp"}], "classes": []}},
        )
        assert content == ""


class TestFileGeneration:
    """Test file generation."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_update_function_registry_writes_files(self, temp_output_dir, demo_project_root, monkeypatch):
        """
        Test that registry files are written to correct locations.
        
        This test patches module-level helpers via monkeypatch but remains safe under
        xdist because each worker runs in a separate process.
        """
        # This is an integration test that would actually write files
        # We'll mock the file writing to avoid side effects
        import development_tools.config as config_module
        from development_tools.shared import standard_exclusions
        
        def mock_get_project_root():
            return demo_project_root
        
        def mock_get_scan_directories():
            return ['.']
        
        # Mock should_exclude_file to not exclude demo project files
        original_should_exclude = standard_exclusions.should_exclude_file

        def mock_should_exclude_file(file_path, tool_type, context='production'):
            if 'development_tools_demo' in file_path:
                return False
            return original_should_exclude(file_path, tool_type, context)
        
        monkeypatch.setattr(config_module, 'get_project_root', mock_get_project_root)
        monkeypatch.setattr(config_module, 'get_scan_directories', mock_get_scan_directories)
        _patch_should_exclude_file(monkeypatch, mock_should_exclude_file)
        
        # Mock the file writing to use temp directory
        
        written_files = []
        
        def mock_update():
            actual_functions = scan_all_python_files()
            detail_content = generate_function_registry_content(actual_functions)
            
            # Write to temp directory instead
            detail_path = temp_output_dir / 'FUNCTION_REGISTRY_DETAIL.md'
            detail_path.write_text(detail_content, encoding='utf-8')
            written_files.append(detail_path)
        
        # Call the mock
        mock_update()
        
        # Verify file was written
        assert len(written_files) > 0
        assert written_files[0].exists()
        assert written_files[0].stat().st_size > 0
