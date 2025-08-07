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
import requests
from datetime import datetime, timedelta
import pytz
from typing import Optional
from core.logger import get_logger, get_component_logger
from core.config import SCHEDULER_INTERVAL
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)
service_logger = get_component_logger('main')

# Throttler class
class Throttler:
    """
    A utility class for throttling operations based on time intervals.
    
    Prevents operations from running too frequently by tracking the last execution time.
    """
    
    def __init__(self, interval):
        """
        Initialize the throttler with a specified interval.
        
        Args:
            interval: Time interval in seconds between allowed operations
        """
        self.interval = interval
        self.last_run = None

    def should_run(self):
        """
        Check if enough time has passed since the last run to allow another execution.
        
        Returns:
            bool: True if the operation should run, False if it should be throttled
        """
        current_time = datetime.now()
        
        if self.last_run is None:
            return True
        
        # Parse human-readable timestamp format
        try:
            last_run_date = datetime.strptime(self.last_run, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # If parsing fails, allow run
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

@handle_errors("creating reschedule request")
def create_reschedule_request(user_id, category):
    """Create a reschedule request flag file for the service to pick up"""
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
    
    # Get the base directory (where the service looks for flag files)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    request_file = os.path.join(base_dir, filename)
    
    # Write the request file
    with open(request_file, 'w') as f:
        json.dump(request_data, f)
    
    logger.info(f"Created reschedule request: {filename}")

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

def title_case(text):
    """
    Convert text to title case with proper handling of special cases.
    
    Args:
        text: The text to convert to title case
        
    Returns:
        str: Text converted to title case
    """
    if not text:
        return text
    
    # Handle common abbreviations and special cases
    special_words = {
        'ai': 'AI',
        'api': 'API',
        'ui': 'UI',
        'ux': 'UX',
        'mhm': 'MHM',
        'id': 'ID',
        'url': 'URL',
        'http': 'HTTP',
        'https': 'HTTPS',
        'json': 'JSON',
        'xml': 'XML',
        'csv': 'CSV',
        'pdf': 'PDF',
        'sql': 'SQL',
        'html': 'HTML',
        'css': 'CSS',
        'js': 'JS',
        'php': 'PHP',
        'python': 'Python',
        'java': 'Java',
        'c++': 'C++',
        'c#': 'C#',
        'dotnet': '.NET',
        'asp': 'ASP',
        'jsp': 'JSP',
        'xml': 'XML',
        'yaml': 'YAML',
        'toml': 'TOML',
        'ini': 'INI',
        'cfg': 'CFG',
        'conf': 'CONF',
        'log': 'LOG',
        'tmp': 'TMP',
        'temp': 'TEMP',
        'etc': 'ETC',
        'usr': 'USR',
        'var': 'VAR',
        'bin': 'BIN',
        'lib': 'LIB',
        'src': 'SRC',
        'doc': 'DOC',
        'docs': 'DOCS',
        'test': 'TEST',
        'tests': 'TESTS',
        'backup': 'BACKUP',
        'backups': 'BACKUPS',
        'config': 'CONFIG',
        'configs': 'CONFIGS',
        'data': 'DATA',
        'files': 'FILES',
        'images': 'IMAGES',
        'media': 'MEDIA',
        'audio': 'AUDIO',
        'video': 'VIDEO',
        'photos': 'PHOTOS',
        'pictures': 'PICTURES',
        'downloads': 'DOWNLOADS',
        'uploads': 'UPLOADS',
        'cache': 'CACHE',
        'caches': 'CACHES',
        'logs': 'LOGS',
        'temp': 'TEMP',
        'tmp': 'TMP',
        'etc': 'ETC',
        'usr': 'USR',
        'var': 'VAR',
        'bin': 'BIN',
        'lib': 'LIB',
        'src': 'SRC',
        'doc': 'DOC',
        'docs': 'DOCS',
        'test': 'TEST',
        'tests': 'TESTS',
        'backup': 'BACKUP',
        'backups': 'BACKUPS',
        'config': 'CONFIG',
        'configs': 'CONFIGS',
        'data': 'DATA',
        'files': 'FILES',
        'images': 'IMAGES',
        'media': 'MEDIA',
        'audio': 'AUDIO',
        'video': 'VIDEO',
        'photos': 'PHOTOS',
        'pictures': 'PICTURES',
        'downloads': 'DOWNLOADS',
        'uploads': 'UPLOADS',
        'cache': 'CACHE',
        'caches': 'CACHES',
        'logs': 'LOGS'
    }
    
    # Split text into words
    words = text.split()
    title_words = []
    
    for i, word in enumerate(words):
        # Convert to lowercase for comparison
        word_lower = word.lower()
        
        # Check if it's a special word
        if word_lower in special_words:
            title_words.append(special_words[word_lower])
        else:
            # Apply normal title case
            title_words.append(word.title())
    
    return ' '.join(title_words) 