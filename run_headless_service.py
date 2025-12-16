#!/usr/bin/env python3
"""
MHM Headless Service Launcher
Safe headless service management that works alongside UI service management.
"""

import sys

from core.headless_service import HeadlessServiceManager
from core.logger import setup_logging, get_component_logger
from core.error_handling import handle_errors

@handle_errors("running headless service launcher", default_return=None)
def main():
    """Main entry point for headless service launcher."""
    # Set up logging
    setup_logging()
    logger = get_component_logger('headless_launcher')
    
    if len(sys.argv) < 2:
        print("Usage: python run_headless_service.py <start|stop|status|info|test|reschedule>")
        print("  start      - Start the headless service")
        print("  stop       - Stop the headless service")
        print("  status     - Check if headless service is running")
        print("  info       - Show detailed service information")
        print("  test       - Send a test message (requires user_id and category)")
        print("  reschedule - Reschedule messages (requires user_id and category)")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    manager = HeadlessServiceManager()
    
    if action == 'start':
        print("Starting headless MHM service...")
        if manager.start_headless_service():
            print("[SUCCESS] Headless service started successfully")
            print("The service is now running in the background.")
            print("Use 'python run_headless_service.py status' to check status.")
            print("Use 'python run_headless_service.py stop' to stop the service.")
        else:
            print("[ERROR] Failed to start headless service")
            print("Check the logs for more information.")
            sys.exit(1)
    
    elif action == 'stop':
        print("Stopping headless MHM service...")
        if manager.stop_headless_service():
            print("[SUCCESS] Headless service stopped successfully")
        else:
            print("[ERROR] Failed to stop headless service")
            print("The service may not have been running.")
    
    elif action == 'status':
        is_running, pid = manager.get_headless_service_status()
        if is_running:
            print(f"[RUNNING] Headless service is running (PID: {pid})")
        else:
            print("[STOPPED] Headless service is not running")
    
    elif action == 'info':
        info = manager.get_service_info()
        print("MHM Service Information:")
        print(f"  Total services: {info['total_services']}")
        print(f"  Headless services: {len(info['headless_services'])}")
        print(f"  UI services: {len(info['ui_services'])}")
        print(f"  Can start headless: {info['can_start_headless']}")
        print(f"  Headless running: {info['is_headless_running']}")
        print(f"  UI running: {info['is_ui_running']}")
        
        if info['headless_services']:
            print("\nHeadless Service Details:")
            for service in info['headless_services']:
                print(f"  PID: {service['pid']}")
                print(f"  Command: {' '.join(service['cmdline'])}")
                print(f"  Created: {service['create_time']}")
        
        if info['ui_services']:
            print("\nUI Service Details:")
            for service in info['ui_services']:
                print(f"  PID: {service['pid']}")
                print(f"  Command: {' '.join(service['cmdline'])}")
                print(f"  Created: {service['create_time']}")
    
    elif action == 'test':
        if len(sys.argv) < 4:
            print("[ERROR] Test message requires user_id and category")
            print("Usage: python run_headless_service.py test <user_id> <category>")
            sys.exit(1)
        
        user_id = sys.argv[2]
        category = sys.argv[3]
        print(f"Sending test message to user {user_id}, category {category}...")
        
        if manager.send_test_message(user_id, category):
            print("[SUCCESS] Test message request sent")
            print("The service will process the request and send the message.")
        else:
            print("[ERROR] Failed to send test message request")
            sys.exit(1)
    
    elif action == 'reschedule':
        if len(sys.argv) < 4:
            print("[ERROR] Reschedule requires user_id and category")
            print("Usage: python run_headless_service.py reschedule <user_id> <category>")
            sys.exit(1)
        
        user_id = sys.argv[2]
        category = sys.argv[3]
        print(f"Rescheduling messages for user {user_id}, category {category}...")
        
        if manager.reschedule_messages(user_id, category):
            print("[SUCCESS] Reschedule request sent")
            print("The service will process the request and reschedule messages.")
        else:
            print("[ERROR] Failed to send reschedule request")
            sys.exit(1)
    
    else:
        print(f"[ERROR] Unknown action: {action}")
        print("Valid actions: start, stop, status, info, test, reschedule")
        sys.exit(1)

if __name__ == "__main__":
    main()
