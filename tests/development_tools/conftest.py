"""Pytest configuration for development_tools tests."""

import sys
import shutil
import importlib.util
from pathlib import Path
from datetime import datetime
import uuid
import pytest
import logging

# Override core-dependent fixtures from parent conftest.py with no-op versions
# These fixtures are not needed for development tools tests which don't use core modules

@pytest.fixture(scope="session", autouse=True)
def initialize_loader_import_order():
    """No-op override: development tools tests don't need core user data loader initialization."""
    yield

@pytest.fixture(scope="session", autouse=True)
def register_user_data_loaders_session():
    """No-op override: development tools tests don't need core user data loader registration."""
    yield

@pytest.fixture(scope="session", autouse=True)
def verify_user_data_loader_registry():
    """No-op override: development tools tests don't need core user data loader verification."""
    yield

@pytest.fixture(scope="session", autouse=True)
def shim_get_user_data_to_invoke_loaders():
    """No-op override: development tools tests don't need core user data shim."""
    yield

@pytest.fixture(scope="session", autouse=True)
def verify_required_loaders_present():
    """No-op override: development tools tests don't need core user data loader verification."""
    yield

@pytest.fixture(scope="function", autouse=True)
def mock_config():
    """No-op override: development tools tests don't need core.config mocking."""
    yield

@pytest.fixture(scope="function", autouse=True)
def ensure_mock_config_applied():
    """No-op override: development tools tests don't need core.config verification."""
    yield

@pytest.fixture(scope="function", autouse=True)
def fix_user_data_loaders():
    """No-op override: development tools tests don't need core user data loader fixes."""
    yield

@pytest.fixture(scope="function", autouse=True)
def clear_user_caches_between_tests():
    """No-op override: development tools tests don't need core user cache clearing."""
    yield

@pytest.fixture(scope="function", autouse=True)
def cleanup_conversation_manager():
    """No-op override: development tools tests don't need conversation manager cleanup."""
    yield

@pytest.fixture(scope="function", autouse=True)
def cleanup_communication_threads():
    """No-op override: development tools tests don't need communication thread cleanup."""
    yield

@pytest.fixture(scope="session", autouse=True)
def cleanup_communication_manager():
    """No-op override: development tools tests don't need CommunicationManager cleanup."""
    yield

# Track test start times for duration calculation (for debugging)
_dev_tools_test_start_times = {}

def pytest_runtest_setup(item):
    """Log when a development_tools test starts with timestamp (DEBUG level only)."""
    test_id = item.nodeid
    start_time = datetime.now()
    _dev_tools_test_start_times[test_id] = start_time
    timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
    # Use DEBUG level to reduce log noise - only visible with TEST_VERBOSE_LOGS=2
    try:
        from tests.conftest import test_logger
        test_logger.debug(f"[DEV-TOOLS-TEST-START] {timestamp} - {test_id}")
    except ImportError:
        # Fallback if parent conftest logger not available
        logger = logging.getLogger("mhm_tests")
        logger.debug(f"[DEV-TOOLS-TEST-START] {timestamp} - {test_id}")

def pytest_runtest_teardown(item, nextitem):
    """Log when a development_tools test ends with timestamp and duration (DEBUG level only)."""
    test_id = item.nodeid
    end_time = datetime.now()
    timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Calculate duration if we have start time
    duration = None
    if test_id in _dev_tools_test_start_times:
        start_time = _dev_tools_test_start_times[test_id]
        duration_seconds = (end_time - start_time).total_seconds()
        duration = f"{duration_seconds:.3f}s"
        del _dev_tools_test_start_times[test_id]
    
    # Use DEBUG level to reduce log noise - only visible with TEST_VERBOSE_LOGS=2
    try:
        from tests.conftest import test_logger
        if duration:
            test_logger.debug(f"[DEV-TOOLS-TEST-END] {timestamp} - {test_id} (duration: {duration})")
        else:
            test_logger.debug(f"[DEV-TOOLS-TEST-END] {timestamp} - {test_id}")
    except ImportError:
        # Fallback if parent conftest logger not available
        logger = logging.getLogger("mhm_tests")
        if duration:
            logger.debug(f"[DEV-TOOLS-TEST-END] {timestamp} - {test_id} (duration: {duration})")
        else:
            logger.debug(f"[DEV-TOOLS-TEST-END] {timestamp} - {test_id}")

def pytest_sessionfinish(session, exitstatus):
    """Print verification summary after development tools audit tier tests complete."""
    # Only print summary if we're running audit tier tests
    audit_tier_tests = [
        'test_audit_tier_comprehensive.py',
        'test_audit_tier_e2e_verification.py'
    ]
    if any(test_file in str(item.fspath) for item in session.items for test_file in audit_tier_tests):
        try:
            from tests.development_tools.test_verification_summary import print_verification_summary
            print_verification_summary()
        except Exception:
            pass  # Don't fail if summary can't be printed


# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def load_development_tools_module(module_name: str):
    """
    Load a development_tools module using importlib.
    
    This helper ensures parent packages are loaded first to handle
    relative imports correctly.
    
    Args:
        module_name: Name like 'analyze_documentation_sync' (without .py)
    
    Returns:
        The loaded module
    """
    # Load parent packages first
    dt_init = project_root / "development_tools" / "__init__.py"
    if dt_init.exists() and "development_tools" not in sys.modules:
        dt_spec = importlib.util.spec_from_file_location("development_tools", dt_init)
        if dt_spec is not None and dt_spec.loader is not None:
            dt_module = importlib.util.module_from_spec(dt_spec)
            sys.modules["development_tools"] = dt_module
            dt_spec.loader.exec_module(dt_module)

    # Load config module FIRST (before shared modules that depend on it)
    # Config is at development_tools/config/config.py
    config_path = project_root / "development_tools" / "config" / "config.py"
    if config_path.exists():
        # Load config package first
        config_init = project_root / "development_tools" / "config" / "__init__.py"
        if config_init.exists() and "development_tools.config" not in sys.modules:
            config_pkg_spec = importlib.util.spec_from_file_location("development_tools.config", config_init)
            if config_pkg_spec is not None and config_pkg_spec.loader is not None:
                config_pkg = importlib.util.module_from_spec(config_pkg_spec)
                sys.modules["development_tools.config"] = config_pkg
                config_pkg_spec.loader.exec_module(config_pkg)

        # Load config module
        if "development_tools.config.config" not in sys.modules:
            config_spec = importlib.util.spec_from_file_location("development_tools.config.config", config_path)
            if config_spec is not None and config_spec.loader is not None:
                config_module = importlib.util.module_from_spec(config_spec)
                sys.modules["development_tools.config.config"] = config_module
                config_spec.loader.exec_module(config_module)
                # Make config available for "from development_tools.config import config" and "from development_tools import config"
                if "development_tools.config" in sys.modules:
                    setattr(sys.modules["development_tools.config"], "config", config_module)
                if "development_tools" in sys.modules:
                    setattr(sys.modules["development_tools"], "config", config_module)
    
    # Load shared package if needed (after config)
    shared_init = project_root / "development_tools" / "shared" / "__init__.py"
    if shared_init.exists() and "development_tools.shared" not in sys.modules:
        shared_spec = importlib.util.spec_from_file_location("development_tools.shared", shared_init)
        if shared_spec is not None and shared_spec.loader is not None:
            shared_module = importlib.util.module_from_spec(shared_spec)
            sys.modules["development_tools.shared"] = shared_module
            shared_spec.loader.exec_module(shared_module)
    
    # Load service package if needed (after shared)
    # IMPORTANT: Load service submodules BEFORE __init__.py (since __init__.py imports them)
    service_init = project_root / "development_tools" / "shared" / "service" / "__init__.py"
    if service_init.exists() and "development_tools.shared.service" not in sys.modules:
        # Ensure parent packages exist in sys.modules
        if "development_tools.shared" not in sys.modules:
            shared_init = project_root / "development_tools" / "shared" / "__init__.py"
            if shared_init.exists():
                shared_spec = importlib.util.spec_from_file_location("development_tools.shared", shared_init)
                if shared_spec is not None and shared_spec.loader is not None:
                    shared_module = importlib.util.module_from_spec(shared_spec)
                    shared_module.__package__ = "development_tools"
                    sys.modules["development_tools.shared"] = shared_module
                    shared_spec.loader.exec_module(shared_module)

        # Create the service package module first (needed for relative imports to work)
        service_spec = importlib.util.spec_from_file_location("development_tools.shared.service", service_init)
        if service_spec is not None and service_spec.loader is not None:
            service_module = importlib.util.module_from_spec(service_spec)
            service_module.__package__ = "development_tools.shared.service"
            service_module.__path__ = [str(project_root / "development_tools" / "shared" / "service")]
            sys.modules["development_tools.shared.service"] = service_module

            # Load submodules in dependency order BEFORE executing __init__.py
            # Load order: utilities (no deps), data_loading (uses utilities),
            # tool_wrappers (needs core for SCRIPT_REGISTRY), then core (uses all mixins), then others
            service_submodules = ["utilities", "data_loading", "tool_wrappers", "audit_orchestration", "report_generation", "commands", "core"]
            for submod_name in service_submodules:
                submod_path = project_root / "development_tools" / "shared" / "service" / f"{submod_name}.py"
                if submod_path.exists():
                    full_submod_name = f"development_tools.shared.service.{submod_name}"
                    if full_submod_name not in sys.modules:
                        submod_spec = importlib.util.spec_from_file_location(full_submod_name, submod_path)
                        if submod_spec is not None and submod_spec.loader is not None:
                            submod = importlib.util.module_from_spec(submod_spec)
                            submod.__package__ = "development_tools.shared.service"
                            sys.modules[full_submod_name] = submod
                            submod_spec.loader.exec_module(submod)

            # Now execute __init__.py (which imports from the submodules that are now loaded)
            service_spec.loader.exec_module(service_module)
    
    # Load required shared modules that tools depend on
    shared_modules = ["standard_exclusions", "constants", "common", "cli_interface"]
    for svc_name in shared_modules:
        svc_path = project_root / "development_tools" / "shared" / f"{svc_name}.py"
        full_name = f"development_tools.shared.{svc_name}"
        if svc_path.exists() and full_name not in sys.modules:
            svc_spec = importlib.util.spec_from_file_location(full_name, svc_path)
            if svc_spec is not None and svc_spec.loader is not None:
                svc_module = importlib.util.module_from_spec(svc_spec)
                sys.modules[full_name] = svc_module
                svc_spec.loader.exec_module(svc_module)

    # Load compatibility cleanup package if needed (for fix_legacy_references imports)
    legacy_init = project_root / "development_tools" / "legacy" / "__init__.py"
    if legacy_init.exists() and "development_tools.legacy" not in sys.modules:
        legacy_spec = importlib.util.spec_from_file_location("development_tools.legacy", legacy_init)
        if legacy_spec is not None and legacy_spec.loader is not None:
            legacy_module = importlib.util.module_from_spec(legacy_spec)
            sys.modules["development_tools.legacy"] = legacy_module
            legacy_spec.loader.exec_module(legacy_module)

    # Load compatibility cleanup submodules if needed (for fix_legacy_references)
    if "development_tools.legacy" in sys.modules:
        legacy_modules = ["analyze_legacy_references", "generate_legacy_reference_report"]
        for legacy_mod_name in legacy_modules:
            legacy_mod_path = project_root / "development_tools" / "legacy" / f"{legacy_mod_name}.py"
            full_legacy_name = f"development_tools.legacy.{legacy_mod_name}"
            if legacy_mod_path.exists() and full_legacy_name not in sys.modules:
                legacy_mod_spec = importlib.util.spec_from_file_location(full_legacy_name, legacy_mod_path)
                if legacy_mod_spec is not None and legacy_mod_spec.loader is not None:
                    legacy_mod = importlib.util.module_from_spec(legacy_mod_spec)
                    sys.modules[full_legacy_name] = legacy_mod
                    legacy_mod_spec.loader.exec_module(legacy_mod)

    # Load imports package if needed (for generate_module_dependencies imports)
    imports_init = project_root / "development_tools" / "imports" / "__init__.py"
    if imports_init.exists() and "development_tools.imports" not in sys.modules:
        imports_spec = importlib.util.spec_from_file_location("development_tools.imports", imports_init)
        if imports_spec is not None and imports_spec.loader is not None:
            imports_module = importlib.util.module_from_spec(imports_spec)
            sys.modules["development_tools.imports"] = imports_module
            imports_spec.loader.exec_module(imports_module)
            # Make config available for "from . import config" imports
            if "development_tools.config" in sys.modules:
                setattr(imports_module, "config", sys.modules["development_tools.config"])
            elif "development_tools.config.config" in sys.modules:
                setattr(imports_module, "config", sys.modules["development_tools.config.config"])

    # Load reports package if needed (for system_signals and quick_status imports)
    reports_init = project_root / "development_tools" / "reports" / "__init__.py"
    if reports_init.exists() and "development_tools.reports" not in sys.modules:
        reports_spec = importlib.util.spec_from_file_location("development_tools.reports", reports_init)
        if reports_spec is not None and reports_spec.loader is not None:
            reports_module = importlib.util.module_from_spec(reports_spec)
            sys.modules["development_tools.reports"] = reports_module
            reports_spec.loader.exec_module(reports_module)
            # Make config available for "from . import config" imports
            if "development_tools.config" in sys.modules:
                setattr(reports_module, "config", sys.modules["development_tools.config"])
            elif "development_tools.config.config" in sys.modules:
                setattr(reports_module, "config", sys.modules["development_tools.config.config"])

    # Load functions package if needed (for generate_function_registry imports)
    functions_init = project_root / "development_tools" / "functions" / "__init__.py"
    if functions_init.exists() and "development_tools.functions" not in sys.modules:
        functions_spec = importlib.util.spec_from_file_location("development_tools.functions", functions_init)
        if functions_spec is not None and functions_spec.loader is not None:
            functions_module = importlib.util.module_from_spec(functions_spec)
            sys.modules["development_tools.functions"] = functions_module
            functions_spec.loader.exec_module(functions_module)
            # Make config available for "from . import config" imports
            if "development_tools.config" in sys.modules:
                setattr(functions_module, "config", sys.modules["development_tools.config"])
            elif "development_tools.config.config" in sys.modules:
                setattr(functions_module, "config", sys.modules["development_tools.config.config"])

    # Load docs package if needed (for analyze_path_drift and other docs tools)
    docs_init = project_root / "development_tools" / "docs" / "__init__.py"
    if docs_init.exists() and "development_tools.docs" not in sys.modules:
        docs_spec = importlib.util.spec_from_file_location("development_tools.docs", docs_init)
        if docs_spec is not None and docs_spec.loader is not None:
            docs_module = importlib.util.module_from_spec(docs_spec)
            sys.modules["development_tools.docs"] = docs_module
            docs_spec.loader.exec_module(docs_module)
    
    # Special handling for service package (needs submodules loaded first)
    if module_name == "shared.service":
        # Service package is already loaded in fixture setup, just return it
        if "development_tools.shared.service" in sys.modules:
            return sys.modules["development_tools.shared.service"]
        # If not loaded yet, trigger the loading logic from fixture setup
        # (This should have been loaded already, but handle it just in case)
        service_init = project_root / "development_tools" / "shared" / "service" / "__init__.py"
        if service_init.exists():
            # This will trigger the service package loading in the fixture setup
            # But we need to ensure it's loaded here too
            if "development_tools.shared.service" not in sys.modules:
                # Load using the same logic as fixture setup
                # (This is a fallback - normally it's loaded earlier)
                pass  # Will fall through to normal loading below
    
    # Now load the requested module
    # Handle dotted module names (e.g., "shared.file_rotation" or "shared.service")
    if "." in module_name:
        parts = module_name.split(".")
        # Check if it's a package (directory with __init__.py) or a module (file)
        package_dir = project_root / "development_tools" / "/".join(parts)
        package_init = package_dir / "__init__.py"
        module_file = package_dir.with_suffix(".py")
        
        if package_init.exists():
            # It's a package - check if it's the service package (needs special handling)
            if module_name == "shared.service" and "development_tools.shared.service" not in sys.modules:
                # Service package needs submodules loaded first - this should have been done in fixture setup
                # But if we're here, do it now
                if "development_tools.shared" not in sys.modules:
                    shared_init = project_root / "development_tools" / "shared" / "__init__.py"
                    if shared_init.exists():
                        shared_spec = importlib.util.spec_from_file_location("development_tools.shared", shared_init)
                        if shared_spec is not None and shared_spec.loader is not None:
                            shared_module = importlib.util.module_from_spec(shared_spec)
                            shared_module.__package__ = "development_tools"
                            sys.modules["development_tools.shared"] = shared_module
                            shared_spec.loader.exec_module(shared_module)

                # Create service package module
                service_spec = importlib.util.spec_from_file_location("development_tools.shared.service", package_init)
                if service_spec is not None and service_spec.loader is not None:
                    service_module = importlib.util.module_from_spec(service_spec)
                    service_module.__package__ = "development_tools.shared.service"
                    service_module.__path__ = [str(package_dir)]
                    sys.modules["development_tools.shared.service"] = service_module

                    # Load submodules first
                    service_submodules = ["utilities", "data_loading", "tool_wrappers", "audit_orchestration", "report_generation", "commands", "core"]
                    for submod_name in service_submodules:
                        submod_path = package_dir / f"{submod_name}.py"
                        if submod_path.exists():
                            full_submod_name = f"development_tools.shared.service.{submod_name}"
                            if full_submod_name not in sys.modules:
                                submod_spec = importlib.util.spec_from_file_location(full_submod_name, submod_path)
                                if submod_spec is not None and submod_spec.loader is not None:
                                    submod = importlib.util.module_from_spec(submod_spec)
                                    submod.__package__ = "development_tools.shared.service"
                                    sys.modules[full_submod_name] = submod
                                    submod_spec.loader.exec_module(submod)

                    # Now execute __init__.py
                    service_spec.loader.exec_module(service_module)
                    return service_module
            
            # It's a package - load the __init__.py
            module_path = package_init
            full_module_name = f"development_tools.{module_name}"
        elif module_file.exists():
            # It's a regular module file
            module_path = module_file
            full_module_name = f"development_tools.{module_name}"
        else:
            raise ImportError(f"Module '{module_name}' not found as package ({package_init}) or file ({module_file})")
    else:
        # Try root first, then check subdirectories
        module_path = project_root / "development_tools" / f"{module_name}.py"
        
        # Check common subdirectories if not found in root
        if not module_path.exists():
            subdirs = ["reports", "functions", "docs", "legacy", "ai_work", "tests", "imports", "error_handling", "config", "shared"]
            for subdir in subdirs:
                candidate = project_root / "development_tools" / subdir / f"{module_name}.py"
                if candidate.exists():
                    module_path = candidate
                    full_module_name = f"development_tools.{subdir}.{module_name}"
                    break
            else:
                full_module_name = f"development_tools.{module_name}"
        else:
            full_module_name = f"development_tools.{module_name}"
    
    spec = importlib.util.spec_from_file_location(full_module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module '{full_module_name}' at {module_path}")
    module = importlib.util.module_from_spec(spec)
    # Set package correctly based on module location
    if "." in full_module_name:
        # For subdirectory modules like "development_tools.legacy.fix_legacy_references"
        # or packages like "development_tools.shared.service"
        module.__package__ = ".".join(full_module_name.split(".")[:-1])
    else:
        module.__package__ = "development_tools"
    sys.modules[full_module_name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def demo_project_root():
    """Return the path to the synthetic fixture project."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    return fixture_path.resolve()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for generated files."""
    tmp_root = project_root / "tests" / "data" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmpdir = tmp_root / f"devtools_output_{uuid.uuid4().hex}"
    tmpdir.mkdir(parents=True, exist_ok=True)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_project_copy(demo_project_root):
    """Create a temporary copy of the demo project for destructive tests."""
    tmp_root = project_root / "tests" / "data" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    base_dir = tmp_root / f"devtools_project_{uuid.uuid4().hex}"
    copy_path = base_dir / "demo_project"
    try:
        # Handle race conditions in parallel execution where files might be deleted
        # during copytree by retrying with error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.copytree(demo_project_root, copy_path, dirs_exist_ok=True)
                break
            except (OSError, shutil.Error):
                if attempt == max_retries - 1:
                    raise
                # Wait a bit and retry (files might be locked or deleted in parallel)
                import time
                time.sleep(0.1 * (attempt + 1))
                # Remove partial copy if it exists
                if copy_path.exists():
                    try:
                        shutil.rmtree(copy_path, ignore_errors=True)
                    except Exception:
                        pass
        # Ensure tests start from a clean fixture snapshot and don't rely on stale status files.
        for status_file in ["AI_STATUS.md", "AI_PRIORITIES.md", "consolidated_report.md"]:
            (copy_path / status_file).unlink(missing_ok=True)
            (copy_path / "development_tools" / status_file).unlink(missing_ok=True)

        yield copy_path
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory for test documentation pairs."""
    tmp_root = project_root / "tests" / "data" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmpdir = tmp_root / f"devtools_docs_{uuid.uuid4().hex}"
    tmpdir.mkdir(parents=True, exist_ok=True)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_coverage_dir():
    """Create a temporary directory for coverage artifacts."""
    tmp_root = project_root / "tests" / "data" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmpdir = tmp_root / f"devtools_cov_{uuid.uuid4().hex}"
    tmpdir.mkdir(parents=True, exist_ok=True)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def test_config_path():
    """Return path to test-specific config that doesn't exclude tests/fixtures/."""
    config_path = Path(__file__).parent / "test_config.json"
    return str(config_path.resolve())


@pytest.fixture(autouse=True, scope="session")
def cleanup_fixture_artifacts():
    """
    Clean up runtime artifacts from fixture directory after all tests.
    
    This ensures logs, archives, and other runtime artifacts don't accumulate
    in the test fixture directory. The fixture directory should only contain
    the actual test data files (result JSONs).
    """
    yield  # Run all tests first
    
    # Clean up after all tests complete
    # Construct path directly to avoid scope mismatch with function-scoped fixtures
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    fixture_dev_tools = fixture_path / "development_tools"
    if not fixture_dev_tools.exists():
        return
    
    # Remove log directories
    for log_dir in [fixture_dev_tools / "logs", fixture_dev_tools / "tests" / "logs"]:
        if log_dir.exists():
            shutil.rmtree(log_dir, ignore_errors=True)
    
    # Remove archive directories
    for jsons_dir in fixture_dev_tools.rglob("jsons"):
        archive_dir = jsons_dir / "archive"
        if archive_dir.exists():
            shutil.rmtree(archive_dir, ignore_errors=True)
    
    # Remove status files (these are generated by tests)
    for status_file in ["AI_STATUS.md", "AI_PRIORITIES.md", "consolidated_report.md"]:
        status_path = fixture_dev_tools / status_file
        if status_path.exists():
            status_path.unlink(missing_ok=True)
