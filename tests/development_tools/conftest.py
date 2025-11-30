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
        module_name: Name like 'documentation_sync_checker' (without .py)
    
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
    
    # Load shared package if needed
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
    
    # Load config if needed
    config_path = project_root / "development_tools" / "config" / "config.py"
    if config_path.exists() and "development_tools.config" not in sys.modules:
        config_spec = importlib.util.spec_from_file_location("development_tools.config", config_path)
        config_module = importlib.util.module_from_spec(config_spec)
        sys.modules["development_tools.config"] = config_module
        config_spec.loader.exec_module(config_module)
    
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

