# TOOL_TIER: supporting

"""
File rotation utility for AI development tools.
Provides file rotation, backup, and archiving functionality.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


class FileRotator:
    """Handles file rotation, backup, and archiving for AI development tools."""
    
    def __init__(self, base_dir: str = "development_tools"):
        self.base_dir = Path(base_dir)
        # If base_dir is development_tools/, archive goes to reports/archive
        if self.base_dir.name == "development_tools" or str(self.base_dir).endswith(os.sep + "development_tools"):
            self.archive_dir = self.base_dir / "reports" / "archive"
        else:
            self.archive_dir = self.base_dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Default rotation settings
        self.max_versions = 7  # Default: keep 7 versions
        self.rotation_suffix = "%Y-%m-%d_%H%M%S"  # Timestamp format
        self._rotation_counter = 0  # Counter to ensure unique filenames
    
    def rotate_file(self, file_path: Union[str, Path], max_versions: int = None) -> str:
        """
        Rotate a file by backing up existing versions and creating a new one.
        
        Args:
            file_path: Path to the file to rotate
            max_versions: Maximum number of backup versions to keep (defaults to 7)
            
        Returns:
            Path to the new file (same as input)
        """
        # Skip rotation if disabled (e.g., during tests)
        if os.environ.get('DISABLE_LOG_ROTATION') == '1':
            return str(file_path)
            
        if max_versions is None:
            max_versions = self.max_versions
            
        file_path = Path(file_path)
        
        # If file doesn't exist, return the path
        if not file_path.exists():
            return str(file_path)
        
        # Create timestamp for this rotation
        # Add counter to ensure uniqueness even if rotations happen in the same second
        timestamp = datetime.now().strftime(self.rotation_suffix)
        self._rotation_counter += 1
        archive_name = f"{file_path.stem}_{timestamp}_{self._rotation_counter:04d}{file_path.suffix}"
        archive_path = self.archive_dir / archive_name
        
        # If file already exists (shouldn't happen with counter, but be safe), append counter
        counter = 1
        while archive_path.exists():
            archive_name = f"{file_path.stem}_{timestamp}_{self._rotation_counter:04d}_{counter}{file_path.suffix}"
            archive_path = self.archive_dir / archive_name
            counter += 1
        
        shutil.move(str(file_path), str(archive_path))
        
        # Log the rotation
        if logger:
            logger.debug(f"Rotated file {file_path} to {archive_path}")
        
        # Clean up old versions if we have too many
        self._cleanup_old_versions(file_path.stem, max_versions)
        
        return str(file_path)
    
    def _cleanup_old_versions(self, base_name: str, max_versions: int):
        """Remove old versions beyond max_versions limit."""
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        # Filter to ensure we only get files that match the expected pattern
        filtered_files = [f for f in existing_files if f.name.startswith(f"{base_name}_")]
        
        if len(filtered_files) > max_versions:
            # Sort by modification time (oldest first)
            filtered_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest files beyond the limit
            files_to_remove = filtered_files[:-max_versions]
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except (OSError, FileNotFoundError):
                    # File may have been removed already, ignore
                    pass
    
    def get_latest_archive(self, base_name: str) -> Optional[Path]:
        """Get the most recent archived version of a file."""
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        if not existing_files:
            return None
        
        # Return the most recently modified file
        return max(existing_files, key=lambda x: x.stat().st_mtime)
    
    def list_archives(self, base_name: str) -> list:
        """List all archived versions of a file."""
        # Match files that start with base_name followed by underscore and timestamp
        # Pattern should match: base_name_YYYY-MM-DD_HHMMSS.ext
        pattern = f"{base_name}_*"
        existing_files = list(self.archive_dir.glob(pattern))
        
        # Filter to ensure we only get files that match the expected pattern
        # (base_name followed by underscore, not just any file starting with base_name)
        filtered_files = [f for f in existing_files if f.name.startswith(f"{base_name}_")]
        
        # Sort by modification time (newest first)
        filtered_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return filtered_files


def create_output_file(file_path: Union[str, Path], content: str, rotate: bool = True, max_versions: int = None, project_root: Optional[Path] = None) -> Path:
    """
    Create an output file with optional rotation.
    
    Args:
        file_path: Path to the output file (relative to project_root if project_root provided)
        content: Content to write to the file
        rotate: Whether to rotate existing files
        max_versions: Maximum number of backup versions to keep
        project_root: Optional project root to resolve relative paths against
        
    Returns:
        Path object pointing to the created file
    """
    # Initialize logger early for debugging
    from core.logger import get_component_logger
    logger = get_component_logger("development_tools")
    
    # Check if this is a status file or static documentation file write during audit/test (defensive check)
    file_name = Path(file_path).name if isinstance(file_path, (str, Path)) else str(file_path)
    file_path_str = str(file_path)
    
    # Log ALL file writes to see what's happening (temporary debugging)
    # Check multiple ways to catch DIRECTORY_TREE writes
    is_directory_tree = (
        'DIRECTORY_TREE' in file_name.upper() or 
        'DIRECTORY_TREE' in file_path_str.upper() or
        file_name.upper() == 'DIRECTORY_TREE.MD' or
        'directory_tree.md' in file_path_str.lower()
    )
    if is_directory_tree:
        logger.warning(f"[SAFEGUARD-DEBUG] create_output_file called for DIRECTORY_TREE: file_path={file_path}, file_name={file_name}, project_root={project_root}, type(file_path)={type(file_path)}")
    status_files = ['AI_STATUS.md', 'AI_PRIORITIES.md', 'consolidated_report.txt']
    # Static documentation files that should only be generated via 'docs' command, not during audits
    static_docs_files = ['DIRECTORY_TREE.md', 'FUNCTION_REGISTRY_DETAIL.md', 'MODULE_DEPENDENCIES_DETAIL.md']
    
    # Resolve the full output path to check if we're writing to real project or test directory
    resolved_path = file_path
    if isinstance(file_path, str):
        resolved_path = Path(file_path)
    elif not isinstance(resolved_path, Path):
        resolved_path = Path(str(resolved_path))
    
    # Resolve relative paths against project_root if provided
    if project_root is not None:
        project_root_path = Path(project_root) if not isinstance(project_root, Path) else project_root
        if not resolved_path.is_absolute():
            resolved_path = project_root_path / resolved_path
    try:
        resolved_path = resolved_path.resolve()
    except (OSError, RuntimeError):
        # If resolve fails, use as-is (but ensure it's a Path object)
        if not isinstance(resolved_path, Path):
            resolved_path = Path(str(resolved_path))
    
    # Check if we're writing to a test directory (should allow) or real project (should protect)
    def _is_test_directory(path: Path) -> bool:
        """Check if path is within a test directory."""
        try:
            path_str = str(path).replace('\\', '/').lower()
            test_indicators = [
                '/tests/', '/test/', '/tmp/', '/temp/', '/pytest-', '/pytest_of_',
                'tests/data/', 'tests/fixtures/', 'tests/temp/', 'demo_project',
                'appdata/local/temp', 'appdata/local/tmp',  # Windows temp directories
                'pytest-', 'pytest_of_',  # pytest temp directories (case-insensitive)
            ]
            # Check for common temp directory patterns (but be more specific)
            if any(indicator in path_str for indicator in test_indicators):
                return True
            # Check if path is in a typical Windows temp location (AppData\Local\Temp)
            if 'appdata' in path_str and ('temp' in path_str or 'tmp' in path_str):
                return True
            # Check if path contains pytest temp directory patterns
            if 'pytest' in path_str and ('temp' in path_str or 'tmp' in path_str):
                return True
            return False
        except Exception:
            # If we can't determine, be conservative and assume it's not a test directory
            return False
    
    # Get the real project root from config to check if we're writing to it
    is_real_project = False
    resolved_path_resolved = resolved_path  # Initialize for use in audit check
    try:
        from ..config import config
        real_project_root = Path(config.get_project_root()).resolve()
        # Ensure resolved_path is a Path object
        if not isinstance(resolved_path, Path):
            resolved_path = Path(str(resolved_path))
        # Check if output is within real project AND not in a test directory
        # Use resolved_path.parents to check if real_project_root is an ancestor
        try:
            resolved_path_resolved = resolved_path.resolve()
        except (OSError, RuntimeError):
            resolved_path_resolved = resolved_path
        
        is_real_project = (
            (real_project_root in resolved_path_resolved.parents or 
             resolved_path_resolved.parent == real_project_root or
             str(resolved_path_resolved).startswith(str(real_project_root)))
            and not _is_test_directory(resolved_path_resolved)
        )
    except (AttributeError, ImportError, Exception) as e:
        # If we can't determine real project root, check if it's a test directory
        # If not a test directory, assume we are writing to real project (safe default)
        try:
            if not isinstance(resolved_path, Path):
                resolved_path = Path(str(resolved_path))
            resolved_path_resolved = resolved_path  # Ensure it's defined
            is_real_project = not _is_test_directory(resolved_path)
        except Exception:
            # If all checks fail, default to protecting (safe default)
            is_real_project = True
    
    # Check static documentation files (should not be regenerated during audits or tests on real project)
    # Log at INFO level to ensure visibility (DEBUG may be filtered)
    # Always log when we're checking static docs (even if condition fails, so we can debug)
    if file_name in static_docs_files:
        logger.info(f"[SAFEGUARD] Checking static doc file: {file_name}, is_real_project: {is_real_project}, resolved_path: {resolved_path_resolved}")
        # ALWAYS check for audit lock files when dealing with static docs, regardless of is_real_project
        # This is a safety measure - if we're writing a static doc, we should check if audit is in progress
        # The path detection might fail, but lock file detection is more reliable
        check_project_root_for_lock = None
        if project_root is not None:
            check_project_root_for_lock = Path(project_root) if not isinstance(project_root, Path) else project_root
        else:
            try:
                check_project_root_for_lock = resolved_path_resolved.parent
                # Walk up to find project root
                current = check_project_root_for_lock
                for _ in range(5):
                    if (current / '.git').exists() or (current / 'pyproject.toml').exists() or (current / 'setup.py').exists():
                        check_project_root_for_lock = current
                        break
                    if current.parent == current:
                        break
                    current = current.parent
            except Exception:
                pass
        
        if check_project_root_for_lock:
            try:
                check_project_root_for_lock = Path(check_project_root_for_lock).resolve()
                # Check for lock files directly
                lock_files = [
                    check_project_root_for_lock / '.audit_in_progress.lock',
                    check_project_root_for_lock / '.coverage_in_progress.lock',
                    check_project_root_for_lock / '.coverage_dev_tools_in_progress.lock'
                ]
                logger.info(f"[SAFEGUARD] Checking lock files in: {check_project_root_for_lock}")
                for lock_file in lock_files:
                    exists = lock_file.exists()
                    logger.info(f"[SAFEGUARD] Lock file {lock_file.name}: {'EXISTS' if exists else 'NOT FOUND'}")
                    if exists:
                        logger.warning(f"[SAFEGUARD] BLOCKING {file_name}: Found audit/coverage lock file: {lock_file}")
                        raise RuntimeError(f"Cannot write {file_name} during audit - static documentation should only be generated via 'docs' command")
            except RuntimeError:
                raise
            except Exception as e:
                logger.warning(f"[SAFEGUARD] Error checking lock files: {e}")
    
    if file_name in static_docs_files and is_real_project:
        
        # Check if audit is in progress - try multiple methods to be robust
        audit_in_progress = False
        check_project_root = None
        try:
            # Determine project root for audit check
            if project_root is not None:
                check_project_root = Path(project_root) if not isinstance(project_root, Path) else project_root
            else:
                # Try to infer from resolved_path
                try:
                    check_project_root = resolved_path_resolved.parent
                    # Walk up to find project root (look for common markers like .git, pyproject.toml, etc.)
                    current = check_project_root
                    for _ in range(5):  # Limit depth to avoid infinite loops
                        if (current / '.git').exists() or (current / 'pyproject.toml').exists() or (current / 'setup.py').exists():
                            check_project_root = current
                            break
                        if current.parent == current:  # Reached filesystem root
                            break
                        current = current.parent
                except Exception as e:
                    logger.debug(f"Failed to infer project root from path: {e}")
                    pass
            
            if check_project_root:
                try:
                    check_project_root = Path(check_project_root).resolve()
                    logger.debug(f"Using check_project_root: {check_project_root}")
                except (OSError, RuntimeError) as e:
                    logger.debug(f"Failed to resolve check_project_root: {e}")
                    pass
                
                # Method 0: Direct file-based check (most reliable for subprocesses)
                # Check for lock files directly without imports
                try:
                    lock_files = [
                        check_project_root / '.audit_in_progress.lock',
                        check_project_root / '.coverage_in_progress.lock',
                        check_project_root / '.coverage_dev_tools_in_progress.lock'
                    ]
                    # Also try config-based paths
                    try:
                        from ..config import config
                        audit_lock_path = config.get_external_value('paths.audit_lock_file', '.audit_in_progress.lock')
                        coverage_lock_path = config.get_external_value('paths.coverage_lock_file', '.coverage_in_progress.lock')
                        lock_files.extend([
                            check_project_root / audit_lock_path,
                            check_project_root / coverage_lock_path
                        ])
                    except (ImportError, AttributeError):
                        pass
                    
                    logger.info(f"[SAFEGUARD] Checking lock files in: {check_project_root}")
                    for lock_file in lock_files:
                        exists = lock_file.exists()
                        logger.info(f"[SAFEGUARD] Lock file {lock_file.name}: {'EXISTS' if exists else 'NOT FOUND'}")
                        if exists:
                            audit_in_progress = True
                            logger.warning(f"[SAFEGUARD] Found audit/coverage lock file: {lock_file}")
                            break
                except Exception as e:
                    logger.warning(f"[SAFEGUARD] File-based lock check failed: {e}", exc_info=True)
                
                # Method 1: Try direct import (works if in same process)
                if not audit_in_progress:
                    try:
                        from .service.audit_orchestration import _is_audit_in_progress
                        audit_in_progress = _is_audit_in_progress(check_project_root)
                        logger.info(f"[SAFEGUARD] Direct import check: audit_in_progress={audit_in_progress}")
                    except (ImportError, AttributeError) as e:
                        logger.info(f"[SAFEGUARD] Direct import failed: {e}, trying sys.modules")
                        # Method 2: Try checking sys.modules
                        import sys
                        if 'development_tools.shared.service.audit_orchestration' in sys.modules:
                            audit_module = sys.modules['development_tools.shared.service.audit_orchestration']
                            if hasattr(audit_module, '_is_audit_in_progress'):
                                audit_in_progress = audit_module._is_audit_in_progress(check_project_root)
                                logger.info(f"[SAFEGUARD] sys.modules check: audit_in_progress={audit_in_progress}")
                        else:
                            logger.info("[SAFEGUARD] audit_orchestration module not in sys.modules")
            else:
                logger.warning(f"[SAFEGUARD] No check_project_root determined for {file_name}")
        except Exception as e:
            # If check fails, log but don't block (defensive - don't break if we can't check)
            logger.warning(f"[SAFEGUARD] Failed to check audit status for {file_name}: {e}", exc_info=True)
            audit_in_progress = False
        
        if audit_in_progress:
            logger.warning(f"[SAFEGUARD] BLOCKING {file_name} generation: Audit in progress. Use 'docs' command to regenerate static documentation.")
            raise RuntimeError(f"Cannot write {file_name} during audit - static documentation should only be generated via 'docs' command")
        else:
            logger.info(f"[SAFEGUARD] Allowing {file_name} generation (audit not in progress)")
        
        # Check if we're in a test environment (should not write to real project)
        if os.environ.get('MHM_TESTING') == '1' or os.environ.get('PYTEST_CURRENT_TEST'):
            from core.logger import get_component_logger
            logger = get_component_logger("development_tools")
            logger.debug(f"Skipping {file_name} generation: Test environment detected and writing to real project. Tests should use temporary directories.")
            raise RuntimeError(f"Cannot write {file_name} during tests to real project - use temporary directories for testing")
    
    # Check status files (existing logic)
    if file_name in status_files:
        # During tests, ensure we're not writing to the real project root
        # Check if we're in a test environment and writing to real project
        if os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('MHM_TESTING') == '1':
            # Determine the actual path we'll be writing to
            write_path = None
            if project_root is not None:
                project_root_path = Path(project_root) if not isinstance(project_root, Path) else project_root
                # Resolve the full path we'll write to
                if isinstance(file_path, str):
                    file_path_obj = Path(file_path)
                else:
                    file_path_obj = file_path
                if not file_path_obj.is_absolute():
                    write_path = project_root_path / file_path_obj
                else:
                    write_path = file_path_obj
            else:
                # Use resolved_path if available, otherwise try to resolve file_path
                try:
                    write_path = resolved_path.resolve() if hasattr(resolved_path, 'resolve') else Path(resolved_path)
                except:
                    try:
                        write_path = Path(file_path).resolve()
                    except:
                        write_path = Path(file_path)
            
            # Only block if we're writing to the actual project root (not just any non-test directory)
            # Check if write_path is within the real project root
            if write_path:
                try:
                    # Get the real project root from config
                    from ..config import config
                    real_project_root = Path(config.get_project_root()).resolve()
                    write_path_resolved = write_path.resolve() if hasattr(write_path, 'resolve') else Path(write_path)
                    
                    # Check if write_path is within real project root AND not a test directory
                    is_in_real_project = (
                        real_project_root in write_path_resolved.parents or
                        str(write_path_resolved).startswith(str(real_project_root))
                    )
                    
                    if is_in_real_project and not _is_test_directory(write_path_resolved):
                        # We're in a test but writing to real project - block it
                        logger.warning(f"[TEST ISOLATION] Blocking {file_name} write to real project during test. Path: {write_path_resolved}. Use temporary directories.")
                        raise RuntimeError(f"Cannot write {file_name} to real project during tests - use temporary directories for test isolation")
                except (ImportError, AttributeError):
                    # If we can't determine real project root, fall back to test directory check
                    if not _is_test_directory(write_path):
                        logger.debug(f"[TEST ISOLATION] Cannot determine real project root, but path {write_path} doesn't look like a test directory. Allowing write.")
                        # Don't block if we can't determine - be lenient
                    pass
                except RuntimeError:
                    # Re-raise our blocking exception
                    raise
                except Exception as e:
                    # If check fails, log but don't block (defensive - don't break tests)
                    logger.debug(f"[TEST ISOLATION] Error checking test isolation for {file_name}: {e}")
                    pass
        
        # Check if audit is in progress by looking for the global flag in operations module
        try:
            import sys
            if 'development_tools.shared.operations' in sys.modules:
                operations_module = sys.modules['development_tools.shared.operations']
                # Check both in-memory flag and file-based lock (for cross-process protection)
                # Use the helper function if available, otherwise fall back to direct check
                if hasattr(operations_module, '_is_audit_in_progress'):
                    # Use helper function that checks both in-memory and file-based lock
                    # Use project_root parameter if provided, otherwise try to infer from file_path
                    check_project_root = None
                    if project_root is not None:
                        # Use provided project_root parameter (most reliable)
                        check_project_root = Path(project_root).resolve()
                    else:
                        # Try to infer from file_path (fallback)
                        try:
                            inferred_root = Path(file_path).resolve()
                            # Go up to project root (file_path is like project_root/development_tools/AI_STATUS.md)
                            while inferred_root.name != 'development_tools' and inferred_root.parent != inferred_root:
                                inferred_root = inferred_root.parent
                            if inferred_root.name == 'development_tools':
                                inferred_root = inferred_root.parent
                            check_project_root = inferred_root
                        except Exception as e:
                            from core.logger import get_component_logger
                            debug_logger = get_component_logger("development_tools")
                            debug_logger.warning(f"Failed to infer project root from file_path for {file_name}: {e}")
                    
                    if check_project_root:
                        try:
                            is_in_progress = operations_module._is_audit_in_progress(check_project_root)
                            # Check result logged only if blocking (see warning below)
                        except Exception as e:
                            # If check fails, assume not in progress (defensive - don't block if we can't check)
                            from core.logger import get_component_logger
                            debug_logger = get_component_logger("development_tools")
                            debug_logger.warning(f"Failed to check audit status for {file_name}: {e}")
                            is_in_progress = False
                    else:
                        # Can't determine project root, assume not in progress (defensive)
                        is_in_progress = False
                elif hasattr(operations_module, '_AUDIT_IN_PROGRESS_GLOBAL') and operations_module._AUDIT_IN_PROGRESS_GLOBAL:
                    is_in_progress = True
                else:
                    is_in_progress = False
                
                if is_in_progress:
                    from core.logger import get_component_logger
                    logger = get_component_logger("development_tools")
                    logger.warning(f"create_output_file() called to write {file_name} during audit! Blocking write to prevent mid-audit status file changes.")
                    import traceback
                    call_stack = ''.join(traceback.format_stack())
                    logger.debug(f"Call stack for blocked {file_name} write attempt:\n{call_stack}")
                    # Raise exception to prevent the write
                    raise RuntimeError(f"Cannot write {file_name} during audit - status files should only be written at the end of audit")
        except RuntimeError:
            # Re-raise our blocking exception
            raise
        except Exception:
            # If check fails, continue (defensive check only - don't block if we can't check)
            pass
    
    # Status files are logged at DEBUG level when actually written (see operations.py for audit context)
    
    # Ensure file_path is a Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    else:
        file_path = Path(file_path)
    
    # Resolve relative paths against project_root if provided
    if project_root is not None:
        if not file_path.is_absolute():
            file_path = project_root / file_path
        else:
            # If absolute, use as-is
            pass
    else:
        # Try to get project_root from config if not provided
        try:
            from ..config import config
            config_project_root = config.get_project_root()
            if config_project_root and not file_path.is_absolute():
                file_path = Path(config_project_root) / file_path
        except (ImportError, AttributeError):
            # If config not available, use path as-is
            pass
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotate if requested and file exists
    if rotate and file_path.exists():
        # For files in development_tools/, use reports/archive instead of archive
        file_path_obj = Path(file_path)
        # Check if file is directly in development_tools/ (not in a subdirectory)
        if file_path_obj.parent.name == "development_tools" or str(file_path_obj.parent).endswith(os.sep + "development_tools"):
            base_dir = file_path_obj.parent / "reports"
        else:
            base_dir = file_path_obj.parent
        # Ensure base_dir is a Path object before converting to string
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        rotator = FileRotator(base_dir=str(base_dir))
        rotated_path = rotator.rotate_file(str(file_path), max_versions)
        # Ensure rotated_path is converted back to Path
        file_path = Path(rotated_path) if isinstance(rotated_path, str) else rotated_path
    
    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def append_to_log(log_file: str, content: str, max_size_mb: int = 10) -> str:
    """
    Append content to a log file with size-based rotation.
    
    Args:
        log_file: Path to the log file
        content: Content to append
        max_size_mb: Maximum size in MB before rotation
        
    Returns:
        Path to the log file
    """
    log_path = Path(log_file)
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and is too large
    if log_path.exists() and log_path.stat().st_size > max_size_mb * 1024 * 1024:
        rotator = FileRotator()
        rotator.rotate_file(str(log_path))
    
    # Append content with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {content}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return str(log_path)
