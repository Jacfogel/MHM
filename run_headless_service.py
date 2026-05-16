#!/usr/bin/env python3
"""
MHM Headless Service Launcher
Safe headless service management that works alongside UI service management.

Launcher output policy (logging vs print): see HOW_TO_RUN.md section 1.6.
"""

import argparse
import sys
from typing import Any

from core.error_handling import handle_errors
from core.headless_service import HeadlessServiceManager
from core.logger import get_component_logger, setup_logging


@handle_errors("building headless service command parser", default_return=None)
def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for headless service operations."""
    parser = argparse.ArgumentParser(
        prog="run_headless_service.py",
        description="Manage the MHM headless background service.",
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("start", help="Start the headless service")
    subparsers.add_parser("stop", help="Stop the headless service")
    subparsers.add_parser("status", help="Check if headless service is running")
    subparsers.add_parser("info", help="Show detailed service information")

    test_parser = subparsers.add_parser(
        "test",
        help="Send a test message request to the running service",
    )
    test_parser.add_argument("user_id", help="User ID to send the test message to")
    test_parser.add_argument("category", help="Message category to test")

    reschedule_parser = subparsers.add_parser(
        "reschedule",
        help="Send a reschedule request to the running service",
    )
    reschedule_parser.add_argument("user_id", help="User ID to reschedule")
    reschedule_parser.add_argument("category", help="Message category to reschedule")

    return parser


@handle_errors("printing service process details", default_return=None)
def _print_service_details(label: str, services: list[dict[str, Any]]) -> None:
    """Print process details for a list of detected services."""
    if not services:
        return

    print(f"\n{label}:")
    for service in services:
        print(f"  PID: {service['pid']}")
        print(f"  Command: {' '.join(service['cmdline'])}")
        print(f"  Created: {service['create_time']}")


@handle_errors("running headless service launcher", default_return=1)
def main(argv: list[str] | None = None) -> int:
    """Main entry point for headless service launcher."""
    setup_logging()
    logger = get_component_logger("headless_launcher")

    parser = _build_parser()
    if parser is None:
        print("[ERROR] Failed to build command parser")
        return 1
    args = parser.parse_args(argv)

    manager = HeadlessServiceManager()

    if args.action == "start":
        print("Starting headless MHM service...")
        if manager.start_headless_service():
            logger.info("Headless service started successfully")
            print("[SUCCESS] Headless service started successfully")
            print("The service is now running in the background.")
            print("Use 'python run_headless_service.py status' to check status.")
            print("Use 'python run_headless_service.py stop' to stop the service.")
            return 0

        logger.error("Failed to start headless service")
        print("[ERROR] Failed to start headless service")
        print("Check the logs for more information.")
        return 1

    if args.action == "stop":
        print("Stopping headless MHM service...")
        if manager.stop_headless_service():
            logger.info("Headless service stopped successfully")
            print("[SUCCESS] Headless service stopped successfully")
            return 0

        logger.warning(
            "Headless service stop requested, but service may not have been running"
        )
        print("[ERROR] Failed to stop headless service")
        print("The service may not have been running.")
        return 1

    if args.action == "status":
        is_running, pid = manager.get_headless_service_status()
        if is_running:
            print(f"[RUNNING] Headless service is running (PID: {pid})")
        else:
            print("[STOPPED] Headless service is not running")
        return 0

    if args.action == "info":
        info = manager.get_service_info()
        print("MHM Service Information:")
        print(f"  Total services: {info['total_services']}")
        print(f"  Headless services: {len(info['headless_services'])}")
        print(f"  UI services: {len(info['ui_services'])}")
        print(f"  Can start headless: {info['can_start_headless']}")
        print(f"  Headless running: {info['is_headless_running']}")
        print(f"  UI running: {info['is_ui_running']}")

        _print_service_details("Headless Service Details", info["headless_services"])
        _print_service_details("UI Service Details", info["ui_services"])
        return 0

    if args.action == "test":
        print(
            f"Sending test message to user {args.user_id}, category {args.category}..."
        )

        if manager.send_test_message(args.user_id, args.category):
            logger.info(
                f"Test message request sent for user={args.user_id}, category={args.category}"
            )
            print("[SUCCESS] Test message request sent")
            print("The service will process the request and send the message.")
            return 0

        logger.error(
            f"Failed to send test message request for user={args.user_id}, category={args.category}"
        )
        print("[ERROR] Failed to send test message request")
        return 1

    if args.action == "reschedule":
        print(
            f"Rescheduling messages for user {args.user_id}, category {args.category}..."
        )

        if manager.reschedule_messages(args.user_id, args.category):
            logger.info(
                f"Reschedule request sent for user={args.user_id}, category={args.category}"
            )
            print("[SUCCESS] Reschedule request sent")
            print("The service will process the request and reschedule messages.")
            return 0

        logger.error(
            f"Failed to send reschedule request for user={args.user_id}, category={args.category}"
        )
        print("[ERROR] Failed to send reschedule request")
        return 1

    logger.error(f"Unknown headless service action: {args.action}")
    print(f"[ERROR] Unknown action: {args.action}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
