# core/network_probe.py
"""
Minimal network reachability checks without importing service_utilities or error_handling.

Keeps import graph simple for error recovery and channel startup paths.
"""

import logging
import socket
import time

_probe_log = logging.getLogger("mhm.network_probe")


def wait_for_network(timeout: float | int = 60) -> bool:
    """Wait for the network to be available, retrying every 5 seconds up to a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        connection = None
        try:
            connection = socket.create_connection(("8.8.8.8", 53))
            _probe_log.debug("Network is available.")
            return True
        except OSError:
            _probe_log.info("Network not available yet, retrying...")
            time.sleep(5)
        finally:
            if connection is not None:
                try:
                    connection.close()
                except OSError:
                    _probe_log.debug(
                        "Error closing network probe socket", exc_info=True
                    )
    _probe_log.error("Network not available after waiting.")
    return False
