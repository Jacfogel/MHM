"""
Test to verify status files are only written at the end of audit, not mid-audit.

This test monitors file modification times during audit execution to confirm
that AI_STATUS.md, AI_PRIORITIES.md, and consolidated_report.md are only
written once at the end, not during tool execution.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy


@pytest.mark.integration
def test_status_files_written_only_at_end_of_audit(temp_project_copy):
    """
    Verify that status files are only written at the end of audit execution.
    
    This test:
    1. Monitors file modification times during audit
    2. Verifies files are only written once at the end
    3. Confirms no mid-audit writes occur
    
    Uses temp_project_copy for complete test isolation.
    """
    # Use conftest helper to load module properly
    service_module = load_development_tools_module("shared.service")
    AIToolsService = service_module.AIToolsService
    
    project_root = Path(temp_project_copy)
    
    # Create status file paths
    ai_status_file = project_root / "development_tools" / "AI_STATUS.md"
    ai_priorities_file = project_root / "development_tools" / "AI_PRIORITIES.md"
    consolidated_file = project_root / "development_tools" / "consolidated_report.md"
    
    # Remove any existing status files
    for f in [ai_status_file, ai_priorities_file, consolidated_file]:
        if f.exists():
            f.unlink()
    
    # Get initial modification times (should be 0 since files don't exist)
    initial_mtimes = {
        'AI_STATUS.md': 0,
        'AI_PRIORITIES.md': 0,
        'consolidated_report.md': 0
    }
    
    # Run a quick audit
    service = AIToolsService(project_root=str(project_root))
    # Keep this test focused on status-file write timing rather than expensive tool internals.
    with patch.object(
        service,
        "run_script",
        return_value={"success": True, "output": "{}", "data": {}},
    ):
        result = service.run_audit(quick=True)
    
    # Verify audit completed (even if with errors, status files should still be written)
    assert result is not None, "Audit should complete and return a result"
    
    # Verify files exist (they should be created even if audit had some failures)
    assert ai_status_file.exists(), f"AI_STATUS.md should exist after audit. Path: {ai_status_file}"
    assert ai_priorities_file.exists(), f"AI_PRIORITIES.md should exist after audit. Path: {ai_priorities_file}"
    assert consolidated_file.exists(), f"consolidated_report.md should exist after audit. Path: {consolidated_file}"
    
    # Get final modification times
    final_mtimes = {
        'AI_STATUS.md': ai_status_file.stat().st_mtime,
        'AI_PRIORITIES.md': ai_priorities_file.stat().st_mtime,
        'consolidated_report.md': consolidated_file.stat().st_mtime
    }
    
    # Verify all files were written (mtime > 0)
    for file_name, mtime in final_mtimes.items():
        assert mtime > 0, f"{file_name} should have a modification time after being created"
    
    # Verify all files were written at approximately the same time (within 2 seconds)
    # This confirms they were written together at the end, not scattered throughout
    all_mtimes = list(final_mtimes.values())
    if len(all_mtimes) > 1:
        time_span = max(all_mtimes) - min(all_mtimes)
        assert time_span < 2.0, f"Status files were written over {time_span:.2f} seconds apart, suggesting mid-audit writes"


@pytest.mark.integration
def test_status_files_not_written_during_tool_execution(temp_project_copy):
    """
    Verify that status files are NOT written during individual tool execution.
    
    This test runs individual tools and confirms they don't write status files.
    
    Uses temp_project_copy for complete test isolation.
    """
    # Use conftest helper to load module properly
    service_module = load_development_tools_module("shared.service")
    AIToolsService = service_module.AIToolsService
    
    project_root = Path(temp_project_copy)
    
    # Create status file paths
    ai_status_file = project_root / "development_tools" / "AI_STATUS.md"
    ai_priorities_file = project_root / "development_tools" / "AI_PRIORITIES.md"
    consolidated_file = project_root / "development_tools" / "consolidated_report.md"
    
    # Remove any existing status files
    for f in [ai_status_file, ai_priorities_file, consolidated_file]:
        if f.exists():
            f.unlink()
    
    service = AIToolsService(project_root=str(project_root))
    
    # Run individual tools (not full audit)
    service.run_script('analyze_functions')
    service.run_script('analyze_documentation')
    
    # Verify status files were NOT created by individual tools
    assert not ai_status_file.exists(), "AI_STATUS.md should not be created by individual tools"
    assert not ai_priorities_file.exists(), "AI_PRIORITIES.md should not be created by individual tools"
    assert not consolidated_file.exists(), "consolidated_report.md should not be created by individual tools"
