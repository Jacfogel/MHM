"""Pytest configuration for development_tools tests."""

import sys
import shutil
import tempfile
import importlib.util
from pathlib import Path
import pytest

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
            config_pkg = importlib.util.module_from_spec(config_pkg_spec)
            sys.modules["development_tools.config"] = config_pkg
            config_pkg_spec.loader.exec_module(config_pkg)
        
        # Load config module
        if "development_tools.config.config" not in sys.modules:
            config_spec = importlib.util.spec_from_file_location("development_tools.config.config", config_path)
            config_module = importlib.util.module_from_spec(config_spec)
            sys.modules["development_tools.config.config"] = config_module
            config_spec.loader.exec_module(config_module)
            # Make config available as development_tools.config for imports like "from development_tools.config import config"
            if "development_tools.config" in sys.modules:
                sys.modules["development_tools.config"].config = config_module
            # Also add to development_tools package for "from development_tools import config"
            if "development_tools" in sys.modules:
                sys.modules["development_tools"].config = config_module
    
    # Load shared package if needed (after config)
    shared_init = project_root / "development_tools" / "shared" / "__init__.py"
    if shared_init.exists() and "development_tools.shared" not in sys.modules:
        shared_spec = importlib.util.spec_from_file_location("development_tools.shared", shared_init)
        shared_module = importlib.util.module_from_spec(shared_spec)
        sys.modules["development_tools.shared"] = shared_module
        shared_spec.loader.exec_module(shared_module)
    
    # Load required shared modules that tools depend on
    shared_modules = ["standard_exclusions", "constants", "common"]
    for svc_name in shared_modules:
        svc_path = project_root / "development_tools" / "shared" / f"{svc_name}.py"
        full_name = f"development_tools.shared.{svc_name}"
        if svc_path.exists() and full_name not in sys.modules:
            svc_spec = importlib.util.spec_from_file_location(full_name, svc_path)
            svc_module = importlib.util.module_from_spec(svc_spec)
            sys.modules[full_name] = svc_module
            svc_spec.loader.exec_module(svc_module)
    
    # Load legacy package if needed (for fix_legacy_references imports)
    legacy_init = project_root / "development_tools" / "legacy" / "__init__.py"
    if legacy_init.exists() and "development_tools.legacy" not in sys.modules:
        legacy_spec = importlib.util.spec_from_file_location("development_tools.legacy", legacy_init)
        legacy_module = importlib.util.module_from_spec(legacy_spec)
        sys.modules["development_tools.legacy"] = legacy_module
        legacy_spec.loader.exec_module(legacy_module)
    
    # Load legacy submodules if needed (for fix_legacy_references)
    if "development_tools.legacy" in sys.modules:
        legacy_modules = ["analyze_legacy_references", "generate_legacy_reference_report"]
        for legacy_mod_name in legacy_modules:
            legacy_mod_path = project_root / "development_tools" / "legacy" / f"{legacy_mod_name}.py"
            full_legacy_name = f"development_tools.legacy.{legacy_mod_name}"
            if legacy_mod_path.exists() and full_legacy_name not in sys.modules:
                legacy_mod_spec = importlib.util.spec_from_file_location(full_legacy_name, legacy_mod_path)
                legacy_mod = importlib.util.module_from_spec(legacy_mod_spec)
                sys.modules[full_legacy_name] = legacy_mod
                legacy_mod_spec.loader.exec_module(legacy_mod)
    
    # Load imports package if needed (for generate_module_dependencies imports)
    imports_init = project_root / "development_tools" / "imports" / "__init__.py"
    if imports_init.exists() and "development_tools.imports" not in sys.modules:
        imports_spec = importlib.util.spec_from_file_location("development_tools.imports", imports_init)
        imports_module = importlib.util.module_from_spec(imports_spec)
        sys.modules["development_tools.imports"] = imports_module
        imports_spec.loader.exec_module(imports_module)
        # Make config available for "from . import config" imports
        if "development_tools.config" in sys.modules:
            imports_module.config = sys.modules["development_tools.config"]
        elif "development_tools.config.config" in sys.modules:
            imports_module.config = sys.modules["development_tools.config.config"]
    
    # Load reports package if needed (for system_signals and quick_status imports)
    reports_init = project_root / "development_tools" / "reports" / "__init__.py"
    if reports_init.exists() and "development_tools.reports" not in sys.modules:
        reports_spec = importlib.util.spec_from_file_location("development_tools.reports", reports_init)
        reports_module = importlib.util.module_from_spec(reports_spec)
        sys.modules["development_tools.reports"] = reports_module
        reports_spec.loader.exec_module(reports_module)
        # Make config available for "from . import config" imports
        if "development_tools.config" in sys.modules:
            reports_module.config = sys.modules["development_tools.config"]
        elif "development_tools.config.config" in sys.modules:
            reports_module.config = sys.modules["development_tools.config.config"]
    
    # Load functions package if needed (for generate_function_registry imports)
    functions_init = project_root / "development_tools" / "functions" / "__init__.py"
    if functions_init.exists() and "development_tools.functions" not in sys.modules:
        functions_spec = importlib.util.spec_from_file_location("development_tools.functions", functions_init)
        functions_module = importlib.util.module_from_spec(functions_spec)
        sys.modules["development_tools.functions"] = functions_module
        functions_spec.loader.exec_module(functions_module)
        # Make config available for "from . import config" imports
        if "development_tools.config" in sys.modules:
            functions_module.config = sys.modules["development_tools.config"]
        elif "development_tools.config.config" in sys.modules:
            functions_module.config = sys.modules["development_tools.config.config"]
    
    # Now load the requested module
    # Handle dotted module names (e.g., "shared.file_rotation")
    if "." in module_name:
        parts = module_name.split(".")
        module_path = project_root / "development_tools" / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        full_module_name = f"development_tools.{module_name}"
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
    module = importlib.util.module_from_spec(spec)
    # Set package correctly based on module location
    if "." in full_module_name:
        # For subdirectory modules like "development_tools.legacy.fix_legacy_references"
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
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_copy(demo_project_root):
    """Create a temporary copy of the demo project for destructive tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        copy_path = Path(tmpdir) / "demo_project"
        shutil.copytree(demo_project_root, copy_path)
        yield copy_path


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory for test documentation pairs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_coverage_dir():
    """Create a temporary directory for coverage artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

