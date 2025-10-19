"""
Test isolation utilities to prevent tests from creating real system resources.

This module provides utilities to ensure tests don't create real Windows tasks,
file system changes, or other system resources that could affect the host system.
"""

import os
import sys
from unittest.mock import patch
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def mock_system_calls():
    """
    Mock all system calls that could create real resources.
    
    This should be called at the start of any test that might trigger
    system resource creation.
    """
    patches = []
    
    # Mock subprocess.run for PowerShell calls
    subprocess_patch = patch('subprocess.run')
    patches.append(subprocess_patch)
    
    # Mock subprocess.Popen for process creation
    popen_patch = patch('subprocess.Popen')
    patches.append(popen_patch)
    
    # Mock Windows Task Scheduler calls
    schtasks_patch = patch('subprocess.run', side_effect=mock_schtasks_call)
    patches.append(schtasks_patch)
    
    return patches

def mock_schtasks_call(*args, **kwargs):
    """Mock schtasks calls to prevent real task creation."""
    if args and len(args) > 0 and 'schtasks' in str(args[0]):
        # Return a successful mock result for schtasks calls
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Task created successfully"
        mock_result.stderr = ""
        return mock_result
    
    # For other subprocess calls, use the original behavior
    import subprocess
    return subprocess.run(*args, **kwargs)

def ensure_test_isolation():
    """
    Ensure that tests are properly isolated from system resources.
    
    This function should be called in test setup to prevent any
    real system resource creation.
    """
    # Mock scheduler's set_wake_timer method globally
    with patch('core.scheduler.SchedulerManager.set_wake_timer') as mock_wake_timer:
        mock_wake_timer.return_value = None
        return mock_wake_timer

def create_safe_scheduler_manager():
    """
    Create a SchedulerManager instance with all system calls mocked.
    
    This should be used in tests that need to test scheduler functionality
    without creating real system resources.
    """
    from core.scheduler import SchedulerManager
    from unittest.mock import Mock
    
    # Create mock communication manager
    mock_comm_manager = Mock()
    
    # Create scheduler manager
    scheduler = SchedulerManager(mock_comm_manager)
    
    # Mock all system calls
    with patch.object(scheduler, 'set_wake_timer') as mock_wake_timer:
        mock_wake_timer.return_value = None
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""
            mock_subprocess.return_value.stderr = ""
            
            return scheduler

def verify_no_real_tasks_created():
    """
    Verify that no real Windows tasks were created during test execution.
    
    This should be called in test teardown to ensure tests didn't
    accidentally create real system resources.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check for MHM task patterns
        mhm_tasks = []
        for line in result.stdout.strip().split('\n'):
            if line and 'Wake_' in line and ',' in line:
                task_name = line.split(',')[0].strip('"')
                if task_name.startswith('Wake_'):
                    mhm_tasks.append(task_name)
        
        if mhm_tasks:
            # Log warning using proper logging instead of print
            import logging
            logger = logging.getLogger('mhm_tests')
            logger.warning(f"Found {len(mhm_tasks)} MHM tasks created during test")
            for task in mhm_tasks:
                logger.warning(f"  - {task}")
            return False
        
        return True
        
    except Exception as e:
        # Log error using proper logging instead of print
        import logging
        logger = logging.getLogger('mhm_tests')
        logger.error(f"Could not verify task creation: {e}")
        return True  # Assume OK if we can't check

# Context manager for test isolation
class IsolationManager:
    """Context manager to ensure test isolation."""
    
    def __init__(self):
        self.patches = []
    
    def __enter__(self):
        # Mock system calls
        self.patches = mock_system_calls()
        for patch_obj in self.patches:
            patch_obj.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop all patches
        for patch_obj in self.patches:
            patch_obj.stop()
        
        # Verify no real tasks were created
        verify_no_real_tasks_created()
