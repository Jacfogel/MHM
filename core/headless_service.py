# headless_service.py - Safe Headless Service Management
"""
Safe headless service management that works alongside UI service management.
This module provides headless-specific service detection and management
that doesn't interfere with the UI service management system.
"""

import os
import sys
import time
import subprocess
from typing import Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.service_utilities import (
    get_service_processes, 
    is_headless_service_running, 
    is_ui_service_running
)

logger = get_component_logger('headless_service')

class HeadlessServiceManager:
    """Manages headless MHM service operations safely alongside UI management."""
    
    def __init__(self):
        """Initialize the headless service manager."""
        self.service_process: Optional[subprocess.Popen] = None
        self.running = False
        
    @handle_errors("checking headless service status", default_return=(False, None))
    def get_headless_service_status(self):
        """Get status of headless service processes."""
        processes = get_service_processes()
        headless_processes = [proc for proc in processes if proc['is_headless']]
        
        if headless_processes:
            # Return the most recent headless process
            latest_process = max(headless_processes, key=lambda p: p['create_time'])
            return True, latest_process['pid']
        
        return False, None
    
    @handle_errors("checking if headless service can start", default_return=False)
    def can_start_headless_service(self):
        """Check if it's safe to start a headless service."""
        # Check if there's already a headless service running
        is_headless_running, _ = self.get_headless_service_status()
        if is_headless_running:
            logger.info("Headless service is already running - will restart existing services")
            return True  # Allow restart of existing services
        
        # Check if there's a UI service running
        if is_ui_service_running():
            logger.info("UI service is running - will stop UI services before starting headless")
            # Need to stop UI services first to avoid conflicts
        
        return True
    
    @handle_errors("starting headless service", default_return=False)
    def start_headless_service(self):
        """Start the headless MHM service safely."""
        if not self.can_start_headless_service():
            return False
        
        # Check if we need to restart existing services
        is_headless_running, _ = self.get_headless_service_status()
        if is_headless_running:
            logger.info("Restarting existing headless services...")
            if not self.stop_headless_service():
                logger.error("Failed to stop existing headless services")
                return False
            # Give services time to shut down
            time.sleep(3)
        
        # Double-check that no service processes are still running
        processes = get_service_processes()
        if processes:
            logger.warning(f"Found {len(processes)} existing service processes, cleaning up...")
            for proc in processes:
                try:
                    import psutil
                    p = psutil.Process(proc['pid'])
                    p.terminate()
                    logger.info(f"Terminated existing service process {proc['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(2)  # Give processes time to terminate
        
        # Check if UI services are running and stop them
        if is_ui_service_running():
            logger.info("Stopping UI services before starting headless service...")
            if not self.stop_ui_services():
                logger.error("Failed to stop UI services")
                return False
            # Give services time to shut down
            time.sleep(3)
        
        try:
            # Get the path to the service script
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            service_path = os.path.join(script_dir, 'core', 'service.py')
            
            # Ensure we use the venv Python explicitly
            venv_python = os.path.join(script_dir, '.venv', 'Scripts', 'python.exe')
            if os.path.exists(venv_python):
                python_executable = venv_python
            else:
                python_executable = sys.executable
            
            logger.info(f"Starting headless service with Python: {python_executable}")
            logger.info(f"Service path: {service_path}")
            
            # Set up environment to ensure venv is used and prevent duplicate processes
            env = os.environ.copy()
            venv_scripts_dir = os.path.join(script_dir, '.venv', 'Scripts')
            if os.path.exists(venv_scripts_dir):
                # Put venv first in PATH to ensure it's used
                env['PATH'] = venv_scripts_dir + os.pathsep + env.get('PATH', '')
                # Add explicit marker to prevent duplicate service detection
                env['MHM_HEADLESS_SERVICE'] = '1'
                env['MHM_SERVICE_TYPE'] = 'headless'
            
            # Start the service process
            if os.name == 'nt':  # Windows
                self.service_process = subprocess.Popen([
                    python_executable, service_path
                ], env=env, cwd=script_dir, creationflags=subprocess.CREATE_NO_WINDOW)
            else:  # Unix/Linux/Mac
                self.service_process = subprocess.Popen([
                    python_executable, service_path
                ], env=env, cwd=script_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.running = True
            logger.info(f"Headless service started with PID: {self.service_process.pid}")
            
            # Give it a moment to initialize
            time.sleep(3)
            
            # Verify the service started successfully
            is_running, pid = self.get_headless_service_status()
            if is_running:
                logger.info(f"Headless service verified running with PID: {pid}")
                return True
            else:
                logger.error("Headless service failed to start properly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start headless service: {e}")
            return False
    
    @handle_errors("stopping UI services", default_return=False)
    def stop_ui_services(self):
        """Stop UI-managed services using the service's built-in shutdown mechanism."""
        try:
            # Use the service's built-in shutdown file mechanism
            shutdown_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shutdown_request.flag')
            with open(shutdown_file, 'w') as f:
                f.write(f"UI_SHUTDOWN_REQUESTED_{time.time()}")
            
            logger.info("Created shutdown request file for UI services")
            
            # Wait for graceful shutdown (service checks for this file every 2 seconds)
            max_wait = 30  # seconds
            wait_time = 0
            while wait_time < max_wait:
                if not is_ui_service_running():
                    logger.info("UI services stopped gracefully")
                    return True
                
                time.sleep(1)
                wait_time += 1
            
            logger.warning("UI services did not stop gracefully within timeout")
            return True  # Consider it successful even if timeout
            
        except Exception as e:
            logger.error(f"Error stopping UI services: {e}")
            return False

    @handle_errors("stopping headless service", default_return=False)
    def stop_headless_service(self):
        """Stop the headless MHM service safely using the service's built-in shutdown mechanism."""
        is_running, pid = self.get_headless_service_status()
        if not is_running:
            logger.info("No headless service running to stop")
            return True
        
        logger.info(f"Stopping headless service (PID: {pid})")
        
        try:
            # Use the service's built-in shutdown file mechanism
            shutdown_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shutdown_request.flag')
            with open(shutdown_file, 'w') as f:
                f.write(f"HEADLESS_SHUTDOWN_REQUESTED_{time.time()}")
            
            logger.info("Created shutdown request file for headless service")
            
            # Wait for graceful shutdown (service checks for this file every 2 seconds)
            max_wait = 30  # seconds
            wait_time = 0
            while wait_time < max_wait:
                is_still_running, _ = self.get_headless_service_status()
                if not is_still_running:
                    logger.info("Headless service stopped gracefully")
                    self.running = False
                    return True
                
                time.sleep(1)
                wait_time += 1
            
            # If graceful shutdown failed, try to terminate the process
            logger.warning("Graceful shutdown timed out, attempting to terminate process")
            if self.service_process and self.service_process.poll() is None:
                self.service_process.terminate()
                time.sleep(2)
                if self.service_process.poll() is None:
                    self.service_process.kill()
            
            self.running = False
            return True
            
        except Exception as e:
            logger.error(f"Error stopping headless service: {e}")
            return False
    
    @handle_errors("getting service information", default_return={})
    def get_service_info(self):
        """Get comprehensive information about all MHM services."""
        processes = get_service_processes()
        
        # Debug output
        logger.debug(f"Found {len(processes)} service processes")
        for proc in processes:
            logger.debug(f"Process {proc['pid']}: {proc['process_type']} - {' '.join(proc['cmdline'])}")
        
        info = {
            'total_services': len(processes),
            'headless_services': [p for p in processes if p['is_headless']],
            'ui_services': [p for p in processes if p['is_ui_managed']],
            'unknown_services': [p for p in processes if p['process_type'] == 'unknown'],
            'can_start_headless': self.can_start_headless_service(),
            'is_headless_running': is_headless_service_running(),
            'is_ui_running': is_ui_service_running()
        }
        
        return info

    @handle_errors("sending test message", default_return=False)
    def send_test_message(self, user_id: str, category: str):
        """Send a test message using the service's built-in test message system."""
        try:
            # Use the service's test message request file mechanism
            base_dir = os.path.dirname(os.path.dirname(__file__))
            request_file = os.path.join(base_dir, f'test_message_request_{int(time.time())}.flag')
            
            request_data = {
                'user_id': user_id,
                'category': category,
                'source': 'headless_service',
                'timestamp': time.time()
            }
            
            with open(request_file, 'w') as f:
                import json
                json.dump(request_data, f)
            
            logger.info(f"Created test message request for user {user_id}, category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")
            return False

    @handle_errors("rescheduling messages", default_return=False)
    def reschedule_messages(self, user_id: str, category: str):
        """Reschedule messages using the service's built-in reschedule system."""
        try:
            # Use the service's reschedule request file mechanism
            base_dir = os.path.dirname(os.path.dirname(__file__))
            request_file = os.path.join(base_dir, f'reschedule_request_{int(time.time())}.flag')
            
            request_data = {
                'user_id': user_id,
                'category': category,
                'source': 'headless_service',
                'timestamp': time.time()
            }
            
            with open(request_file, 'w') as f:
                import json
                json.dump(request_data, f)
            
            logger.info(f"Created reschedule request for user {user_id}, category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reschedule messages: {e}")
            return False

@handle_errors("main headless service function")
def main():
    """Main entry point for headless service management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MHM Headless Service Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'info'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    manager = HeadlessServiceManager()
    
    if args.action == 'start':
        if manager.start_headless_service():
            print("Headless service started successfully")
            sys.exit(0)
        else:
            print("Failed to start headless service")
            sys.exit(1)
    
    elif args.action == 'stop':
        if manager.stop_headless_service():
            print("Headless service stopped successfully")
            sys.exit(0)
        else:
            print("Failed to stop headless service")
            sys.exit(1)
    
    elif args.action == 'status':
        is_running, pid = manager.get_headless_service_status()
        if is_running:
            print(f"Headless service is running (PID: {pid})")
        else:
            print("Headless service is not running")
    
    elif args.action == 'info':
        info = manager.get_service_info()
        print(f"Total MHM services: {info['total_services']}")
        print(f"Headless services: {len(info['headless_services'])}")
        print(f"UI services: {len(info['ui_services'])}")
        print(f"Can start headless: {info['can_start_headless']}")
        print(f"Headless running: {info['is_headless_running']}")
        print(f"UI running: {info['is_ui_running']}")

if __name__ == "__main__":
    main()
