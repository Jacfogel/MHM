#!/usr/bin/env python3
"""
Test DNS Fallback Functionality

This script tests the enhanced DNS resolution with fallback servers
in the Discord bot to verify it's working correctly.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.logger import get_component_logger
from communication.communication_channels.discord.bot import DiscordBot

logger = get_component_logger('main')

def test_dns_fallback():
    """Test the enhanced DNS resolution with fallback servers"""
    print("Testing Enhanced DNS Resolution with Fallback Servers")
    print("=" * 60)
    
    # Create Discord bot instance
    discord_bot = DiscordBot()
    
    # Test DNS resolution for the problematic hostname
    hostname = "gateway-us-east1-a.discord.gg"
    print(f"\nTesting DNS resolution for: {hostname}")
    print("-" * 40)
    
    # Test the enhanced DNS resolution method
    result = discord_bot._check_dns_resolution(hostname)
    
    print(f"DNS Resolution Result: {'SUCCESS' if result else 'FAILED'}")
    
    # Show detailed error information
    if discord_bot._detailed_error_info.get('dns_error'):
        error_info = discord_bot._detailed_error_info['dns_error']
        print(f"\nDetailed Error Information:")
        print(f"  Hostname: {error_info.get('hostname')}")
        
        if 'primary_error' in error_info:
            primary = error_info['primary_error']
            print(f"  Primary DNS Error: {primary.get('error_message')}")
        
        if 'resolved_with' in error_info:
            print(f"  Resolved with: {error_info['resolved_with']}")
            print(f"  Resolved IP: {error_info['resolved_ip']}")
        
        if 'alternative_dns_failed' in error_info:
            print(f"  Alternative DNS servers tried: {error_info['alternative_dns_failed']}")
    
    # Test network connectivity
    print(f"\nTesting Network Connectivity")
    print("-" * 40)
    
    network_result = discord_bot._check_network_connectivity(hostname)
    print(f"Network Connectivity Result: {'SUCCESS' if network_result else 'FAILED'}")
    
    # Show network error information
    if discord_bot._detailed_error_info.get('network_error'):
        network_error = discord_bot._detailed_error_info['network_error']
        print(f"\nNetwork Error Information:")
        print(f"  Error Type: {network_error.get('error_type')}")
        print(f"  Error Message: {network_error.get('error_message')}")
        if 'endpoints_tried' in network_error:
            print(f"  Endpoints Tried: {len(network_error['endpoints_tried'])}")
    
    print("\n" + "=" * 60)
    return result and network_result

if __name__ == "__main__":
    success = test_dns_fallback()
    sys.exit(0 if success else 1) 