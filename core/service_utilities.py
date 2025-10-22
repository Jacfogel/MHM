# service_utilities.py
"""
Service utilities for MHM.
Contains functions for service management, network operations, and datetime handling.
"""

import os
import json
import time
import socket
import psutil
from datetime import datetime
import pytz
from core.logger import get_component_logger
try:
    from core.file_auditor import record_created as _record_created
except Exception:
    _record_created = None
from core.config import SCHEDULER_INTERVAL
from core.error_handling import handle_errors

logger = get_component_logger('main')
service_logger = get_component_logger('main')

# Throttler class
class Throttler:
    """
    A utility class for throttling operations based on time intervals.
    
    Prevents operations from running too frequently by tracking the last execution time.
    """
    
    @handle_errors("initializing throttler", default_return=None)
    def __init__(self, interval):
        """
        Initialize the throttler with a specified interval.
        
        Args:
            interval: Time interval in seconds between allowed operations
        """
        self.interval = interval
        self.last_run = None

    @handle_errors("checking if throttler should run", default_return=False)
    def should_run(self):
        """
        Check if enough time has passed since the last run to allow another execution.
        """
        current_time = datetime.now()

        if self.last_run is None:
            # Set first-run timestamp so we actually throttle subsequent calls
            self.last_run = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return True

        try:
            last_run_date = datetime.strptime(self.last_run, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # If parsing fails, allow run and reset timestamp
            self.last_run = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return True

        time_since_last_run = (current_time - last_run_date).total_seconds()
        if time_since_last_run >= self.interval:
            self.last_run = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return True

        return False

class InvalidTimeFormatError(Exception):
    """
    Exception raised when time format is invalid.
    
    Used for time parsing and validation operations.
    """
    pass

# Global throttler instance
throttler = Throttler(SCHEDULER_INTERVAL)

@handle_errors("creating reschedule request", default_return=False)
def create_reschedule_request(user_id: str, category: str) -> bool:
    """
    Create a reschedule request file that the service will pick up.
    
    Args:
        user_id: The user ID
        category: The category to reschedule
        
    Returns:
        bool: True if request was created successfully
    """
    # First check if service is running - if not, no need to reschedule
    # The service will pick up changes on next startup
    if not is_service_running():
        logger.debug(f"Service not running - schedule changes will be picked up on next startup")
        return
        
    # Create request data
    request_data = {
        'user_id': user_id,
        'category': category,
        'timestamp': time.time(),
        'source': 'ui_schedule_editor'
    }
    
    # Create unique filename
    timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
    filename = f"reschedule_request_{user_id}_{category}_{timestamp}.flag"
    
    # Determine base directory for flag files
    # In tests, redirect to tests/data/flags to avoid touching real service watchers/logs
    if os.environ.get("MHM_TESTING") == "1":
        # Use configurable test data directory
        from core.config import get_backups_dir
        base_dir = os.path.join(os.path.dirname(get_backups_dir()), "flags")
        os.makedirs(base_dir, exist_ok=True)
    else:
        # Project root (service watches here) - use configurable approach
        base_dir = os.getenv('MHM_FLAGS_DIR', os.path.dirname(os.path.dirname(__file__)))
    request_file = os.path.join(base_dir, filename)

    # Write the request file
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, indent=2)

    logger.info(f"Created reschedule request: {filename}")
    try:
        if _record_created:
            _record_created(request_file, reason="create_reschedule_request", extra={'user_id': user_id, 'category': category, 'source': request_data['source']})
    except Exception:
        pass

@handle_errors("checking if service is running", default_return=False)
def is_service_running():
    """Check if the MHM service is currently running"""
    # Look for python processes running service.py
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('service.py' in arg for arg in cmdline):
                if proc.is_running():
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return False

@handle_errors("checking service process details", default_return=[])
def get_service_processes():
    """Get detailed information about all MHM service processes"""
    service_processes = []
    seen_processes = set()  # Track processes to avoid duplicates
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'environ']):
        try:
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('service.py' in arg for arg in cmdline) and not any('run_headless_service.py' in arg for arg in cmdline):
                if proc.is_running():
                    # Create a unique identifier for this process to avoid duplicates
                    process_key = f"{proc.info['pid']}_{proc.info['create_time']}"
                    if process_key in seen_processes:
                        continue
                    seen_processes.add(process_key)
                    
                    # Determine if this is a UI-managed or headless service
                    # UI-managed: has 'ui' in the path (launched by UI)
                    # Headless: runs core/service.py directly without 'ui' in path
                    full_cmdline = ' '.join(cmdline)
                    is_ui_managed = 'ui' in full_cmdline and 'service.py' in full_cmdline
                    is_headless = ('core/service.py' in full_cmdline or 'core\\service.py' in full_cmdline or full_cmdline.endswith('core/service.py') or full_cmdline.endswith('core\\service.py')) and not is_ui_managed
                    
                    # Check for environment markers to better identify service type
                    try:
                        environ = proc.info.get('environ', {})
                        if environ and 'MHM_HEADLESS_SERVICE' in environ:
                            is_headless = True
                            is_ui_managed = False
                    except (psutil.AccessDenied, KeyError):
                        pass  # Can't access environment, use cmdline detection
                    
                    service_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline,
                        'create_time': proc.info['create_time'],
                        'is_ui_managed': is_ui_managed,
                        'is_headless': is_headless,
                        'process_type': 'ui_managed' if is_ui_managed else 'headless' if is_headless else 'unknown'
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return service_processes

@handle_errors("checking if headless service is running", default_return=False)
def is_headless_service_running():
    """Check if a headless MHM service is currently running"""
    processes = get_service_processes()
    return any(proc['is_headless'] for proc in processes)

@handle_errors("checking if UI service is running", default_return=False)
def is_ui_service_running():
    """Check if a UI-managed MHM service is currently running"""
    processes = get_service_processes()
    return any(proc['is_ui_managed'] for proc in processes)

@handle_errors("waiting for network", default_return=False)
def wait_for_network(timeout=60):
    """Wait for the network to be available, retrying every 5 seconds up to a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Attempt to connect to a common DNS server (Google DNS as an example)
            socket.create_connection(("8.8.8.8", 53))
            logger.debug("Network is available.")
            return True
        except OSError:
            logger.warning("Network not available, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
    logger.error("Network not available after waiting.")
    return False

@handle_errors("loading and localizing datetime")
def load_and_localize_datetime(datetime_str, timezone_str='America/Regina'):
    """
    Load and localize a datetime string to a specific timezone.
    
    Args:
        datetime_str: Datetime string in format "YYYY-MM-DD HH:MM"
        timezone_str: Timezone string (default: 'America/Regina')
        
    Returns:
        datetime: Timezone-aware datetime object
        
    Raises:
        InvalidTimeFormatError: If datetime_str format is invalid
    """
    try:
        tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        aware_datetime = tz.localize(naive_datetime)
        logger.debug(f"Localized datetime '{datetime_str}' to timezone '{timezone_str}': '{aware_datetime}'")
        return aware_datetime
    except ValueError as e:
        raise InvalidTimeFormatError(f"Invalid datetime format '{datetime_str}': {e}")
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise InvalidTimeFormatError(f"Unknown timezone '{timezone_str}': {e}")

 