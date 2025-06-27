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
from core.logger import get_logger
from core.config import SCHEDULER_INTERVAL

logger = get_logger(__name__)

# Throttler class
class Throttler:
    def __init__(self, interval):
        self.interval = interval
        self.last_run = None

    def should_run(self):
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
    pass

# Global throttler instance
throttler = Throttler(SCHEDULER_INTERVAL)

def create_reschedule_request(user_id, category):
    """Create a reschedule request flag file for the service to pick up"""
    try:
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
        
    except Exception as e:
        logger.error(f"Failed to create reschedule request for user {user_id}, category {category}: {e}")

def is_service_running():
    """Check if the MHM service is currently running"""
    try:
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
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
        return False  # Assume not running if we can't check

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

def load_and_localize_datetime(datetime_str, timezone_str='America/Regina'):
    """Load and localize a datetime string to a specific timezone"""
    try:
        tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        aware_datetime = tz.localize(naive_datetime)
        logger.debug(f"Localized datetime '{datetime_str}' to timezone '{timezone_str}': '{aware_datetime}'")
        return aware_datetime
    except Exception as e:
        logger.error(f"Error loading and localizing datetime '{datetime_str}' to timezone '{timezone_str}': {e}", exc_info=True)
        raise 