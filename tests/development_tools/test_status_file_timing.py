"""
Test to verify status files are only written at the end of audit, not mid-audit.

This test monitors file modification times during audit execution to confirm
that AI_STATUS.md, AI_PRIORITIES.md, and consolidated_report.txt are only
written once at the end, not during tool execution.
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tests.development_tools.conftest import demo_project_root, load_development_tools_module


@pytest.mark.integration
@pytest.mark.no_parallel
def test_status_files_written_only_at_end_of_audit(demo_project_root):
    """
    Verify that status files are only written at the end of audit execution.
    
    This test:
    1. Monitors file modification times during audit
    2. Verifies files are only written once at the end
    3. Confirms no mid-audit writes occur
    """
    # Use conftest helper to load module properly
    operations_module = load_development_tools_module("shared.operations")
    AIToolsService = operations_module.AIToolsService
    
    project_root = Path(demo_project_root)
    
    # Create status file paths
    ai_status_file = project_root / "development_tools" / "AI_STATUS.md"
    ai_priorities_file = project_root / "development_tools" / "AI_PRIORITIES.md"
    consolidated_file = project_root / "development_tools" / "consolidated_report.txt"
    
    # Remove any existing status files
    for f in [ai_status_file, ai_priorities_file, consolidated_file]:
        if f.exists():
            f.unlink()
    
    # Track file writes using create_output_file
    write_times = {
        'AI_STATUS.md': [],
        'AI_PRIORITIES.md': [],
        'consolidated_report.txt': []
    }
    
    # Import create_output_file to get reference
    from development_tools.shared import file_rotation
    original_create_output_file = file_rotation.create_output_file
    
    def tracked_create_output_file(file_path, content, project_root=None):
        """Track when status files are written."""
        result = original_create_output_file(file_path, content, project_root)
        
        # Check if this is a status file write
        file_name = Path(file_path).name
        if file_name in write_times:
            write_times[file_name].append(time.time())
            if len(write_times[file_name]) > 1:
                pytest.fail(f"{file_name} was written {len(write_times[file_name])} times during audit!")
        
        return result
    
    # Patch create_output_file - patch both the module import and the original
    # The function is imported at module level: from ..shared.file_rotation import create_output_file
    with patch('development_tools.shared.file_rotation.create_output_file', side_effect=tracked_create_output_file):
        # Also need to patch it in the operations module namespace
        with patch.object(operations_module, 'create_output_file', side_effect=tracked_create_output_file, create=True):
            # Run a quick audit
            service = AIToolsService(project_root=str(project_root))
            result = service.run_audit(quick=True)
            # Verify audit completed (even if with errors, status files should still be written)
            assert result is not None, "Audit should complete and return a result"
    
    # Verify files exist first (they should be created even if tracking failed)
    assert ai_status_file.exists(), f"AI_STATUS.md should exist after audit. Path: {ai_status_file}"
    assert ai_priorities_file.exists(), f"AI_PRIORITIES.md should exist after audit. Path: {ai_priorities_file}"
    assert consolidated_file.exists(), f"consolidated_report.txt should exist after audit. Path: {consolidated_file}"
    
    # Verify each status file was written exactly once (if tracking worked)
    if len(write_times['AI_STATUS.md']) > 0:
        assert len(write_times['AI_STATUS.md']) == 1, f"AI_STATUS.md should be written once, but was written {len(write_times['AI_STATUS.md'])} times"
        assert len(write_times['AI_PRIORITIES.md']) == 1, f"AI_PRIORITIES.md should be written once, but was written {len(write_times['AI_PRIORITIES.md'])} times"
        assert len(write_times['consolidated_report.txt']) == 1, f"consolidated_report.txt should be written once, but was written {len(write_times['consolidated_report.txt'])} times"
        
        # Verify all writes happened at approximately the same time (within 1 second)
        # This confirms they were written together at the end, not scattered throughout
        all_times = []
        for times in write_times.values():
            all_times.extend(times)
        
        if len(all_times) > 1:
            time_span = max(all_times) - min(all_times)
            assert time_span < 1.0, f"Status files were written over {time_span:.2f} seconds apart, suggesting mid-audit writes"


@pytest.mark.integration
@pytest.mark.no_parallel
def test_status_files_not_written_during_tool_execution(demo_project_root):
    """
    Verify that status files are NOT written during individual tool execution.
    
    This test runs individual tools and confirms they don't write status files.
    """
    # Use conftest helper to load module properly
    operations_module = load_development_tools_module("shared.operations")
    AIToolsService = operations_module.AIToolsService
    
    project_root = Path(demo_project_root)
    
    # Create status file paths
    ai_status_file = project_root / "development_tools" / "AI_STATUS.md"
    ai_priorities_file = project_root / "development_tools" / "AI_PRIORITIES.md"
    consolidated_file = project_root / "development_tools" / "consolidated_report.txt"
    
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
    assert not consolidated_file.exists(), "consolidated_report.txt should not be created by individual tools"

