#!/usr/bin/env python3
"""
Discord Connectivity Diagnostic Script

This script provides detailed diagnostics for Discord connectivity issues,
including DNS resolution, network connectivity, and Discord-specific status.
"""

import sys
import os
import time
import socket
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.logger import get_component_logger
from bot.discord_bot import DiscordBot, DiscordConnectionStatus
from bot.communication_manager import CommunicationManager

logger = get_component_logger('main')

class DiscordConnectivityDiagnostic:
    """Comprehensive Discord connectivity diagnostic tool"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'recommendations': []
        }
    
    def test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution for Discord-related domains"""
        logger.info("Testing DNS resolution...")
        
        test_domains = [
            "discord.com",
            "gateway.discord.gg",
            "gateway-us-east1-a.discord.gg",
            "gateway-us-east1-b.discord.gg",
            "gateway-us-east1-c.discord.gg",
            "gateway-us-east1-d.discord.gg"
        ]
        
        dns_results = {}
        all_successful = True
        
        for domain in test_domains:
            try:
                start_time = time.time()
                ip_address = socket.gethostbyname(domain)
                resolve_time = time.time() - start_time
                
                dns_results[domain] = {
                    'status': 'success',
                    'ip_address': ip_address,
                    'resolve_time': round(resolve_time, 3),
                    'error': None
                }
                logger.info(f"✓ {domain} -> {ip_address} ({resolve_time:.3f}s)")
                
            except socket.gaierror as e:
                dns_results[domain] = {
                    'status': 'failed',
                    'ip_address': None,
                    'resolve_time': None,
                    'error': f"DNS Error {e.errno}: {e.strerror}"
                }
                all_successful = False
                logger.error(f"✗ {domain}: DNS Error {e.errno} - {e.strerror}")
            
            except Exception as e:
                dns_results[domain] = {
                    'status': 'failed',
                    'ip_address': None,
                    'resolve_time': None,
                    'error': f"Unexpected error: {str(e)}"
                }
                all_successful = False
                logger.error(f"✗ {domain}: Unexpected error - {e}")
        
        return {
            'overall_status': 'success' if all_successful else 'failed',
            'domains': dns_results,
            'successful_resolutions': sum(1 for r in dns_results.values() if r['status'] == 'success'),
            'total_domains': len(test_domains)
        }
    
    def test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity to Discord servers"""
        logger.info("Testing network connectivity...")
        
        test_endpoints = [
            ("discord.com", 443),
            ("gateway.discord.gg", 443),
            ("gateway-us-east1-a.discord.gg", 443),
            ("gateway-us-east1-b.discord.gg", 443),
            ("gateway-us-east1-c.discord.gg", 443),
            ("gateway-us-east1-d.discord.gg", 443)
        ]
        
        connectivity_results = {}
        all_successful = True
        
        for hostname, port in test_endpoints:
            try:
                start_time = time.time()
                sock = socket.create_connection((hostname, port), timeout=10)
                connect_time = time.time() - start_time
                sock.close()
                
                connectivity_results[f"{hostname}:{port}"] = {
                    'status': 'success',
                    'connect_time': round(connect_time, 3),
                    'error': None
                }
                logger.info(f"✓ {hostname}:{port} - Connected ({connect_time:.3f}s)")
                
            except socket.timeout:
                connectivity_results[f"{hostname}:{port}"] = {
                    'status': 'timeout',
                    'connect_time': None,
                    'error': 'Connection timeout'
                }
                all_successful = False
                logger.error(f"✗ {hostname}:{port} - Connection timeout")
                
            except socket.gaierror as e:
                connectivity_results[f"{hostname}:{port}"] = {
                    'status': 'dns_error',
                    'connect_time': None,
                    'error': f"DNS Error {e.errno}: {e.strerror}"
                }
                all_successful = False
                logger.error(f"✗ {hostname}:{port} - DNS Error {e.errno}: {e.strerror}")
                
            except ConnectionRefusedError:
                connectivity_results[f"{hostname}:{port}"] = {
                    'status': 'refused',
                    'connect_time': None,
                    'error': 'Connection refused'
                }
                all_successful = False
                logger.error(f"✗ {hostname}:{port} - Connection refused")
                
            except Exception as e:
                connectivity_results[f"{hostname}:{port}"] = {
                    'status': 'error',
                    'connect_time': None,
                    'error': f"Unexpected error: {str(e)}"
                }
                all_successful = False
                logger.error(f"✗ {hostname}:{port} - Unexpected error: {e}")
        
        return {
            'overall_status': 'success' if all_successful else 'failed',
            'endpoints': connectivity_results,
            'successful_connections': sum(1 for r in connectivity_results.values() if r['status'] == 'success'),
            'total_endpoints': len(test_endpoints)
        }
    
    def test_discord_bot_status(self) -> Dict[str, Any]:
        """Test Discord bot status and health"""
        logger.info("Testing Discord bot status...")
        
        try:
            # Create Discord bot instance
            discord_bot = DiscordBot()
            
            # Get detailed health status
            health_status = discord_bot.get_health_status()
            status_summary = discord_bot.get_connection_status_summary()
            
            # Test health check
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                health_check_result = loop.run_until_complete(discord_bot.health_check())
                loop.close()
            except Exception as e:
                health_check_result = False
                logger.error(f"Health check failed: {e}")
            
            return {
                'overall_status': 'success' if health_check_result else 'failed',
                'health_check_result': health_check_result,
                'status_summary': status_summary,
                'detailed_status': health_status,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Discord bot status test failed: {e}")
            return {
                'overall_status': 'failed',
                'health_check_result': False,
                'status_summary': 'Error testing bot status',
                'detailed_status': {},
                'error': str(e)
            }
    
    def test_communication_manager(self) -> Dict[str, Any]:
        """Test communication manager Discord status"""
        logger.info("Testing communication manager Discord status...")
        
        try:
            comm_manager = CommunicationManager()
            discord_status = comm_manager.get_discord_connectivity_status()
            
            if discord_status:
                return {
                    'overall_status': 'success',
                    'discord_status': discord_status,
                    'error': None
                }
            else:
                return {
                    'overall_status': 'failed',
                    'discord_status': None,
                    'error': 'No Discord status available'
                }
                
        except Exception as e:
            logger.error(f"Communication manager test failed: {e}")
            return {
                'overall_status': 'failed',
                'discord_status': None,
                'error': str(e)
            }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # DNS recommendations
        dns_test = self.results['tests'].get('dns_resolution', {})
        if dns_test.get('overall_status') == 'failed':
            recommendations.append("DNS resolution issues detected. Check your internet connection and DNS settings.")
            recommendations.append("Try using alternative DNS servers (8.8.8.8, 1.1.1.1, 208.67.222.222)")
        
        # Network connectivity recommendations
        network_test = self.results['tests'].get('network_connectivity', {})
        if network_test.get('overall_status') == 'failed':
            recommendations.append("Network connectivity issues detected. Check your firewall and network settings.")
            recommendations.append("Ensure outbound connections to port 443 are allowed.")
        
        # Discord bot recommendations
        bot_test = self.results['tests'].get('discord_bot_status', {})
        if bot_test.get('overall_status') == 'failed':
            recommendations.append("Discord bot health check failed. Check bot token and permissions.")
            recommendations.append("Verify the bot is properly configured in Discord Developer Portal.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("All connectivity tests passed. Discord should be working normally.")
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all diagnostic tests"""
        logger.info("Starting Discord connectivity diagnostics...")
        
        # Run DNS resolution test
        self.results['tests']['dns_resolution'] = self.test_dns_resolution()
        
        # Run network connectivity test
        self.results['tests']['network_connectivity'] = self.test_network_connectivity()
        
        # Run Discord bot status test
        self.results['tests']['discord_bot_status'] = self.test_discord_bot_status()
        
        # Run communication manager test
        self.results['tests']['communication_manager'] = self.test_communication_manager()
        
        # Generate summary
        self.results['summary'] = {
            'total_tests': len(self.results['tests']),
            'passed_tests': sum(1 for test in self.results['tests'].values() if test.get('overall_status') == 'success'),
            'overall_status': 'success' if all(test.get('overall_status') == 'success' for test in self.results['tests'].values()) else 'failed'
        }
        
        # Generate recommendations
        self.results['recommendations'] = self.generate_recommendations()
        
        return self.results
    
    def print_results(self):
        """Print formatted results to console"""
        print("\n" + "="*60)
        print("DISCORD CONNECTIVITY DIAGNOSTIC RESULTS")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['summary']['overall_status'].upper()}")
        print(f"Tests Passed: {self.results['summary']['passed_tests']}/{self.results['summary']['total_tests']}")
        print()
        
        # DNS Resolution Results
        print("DNS RESOLUTION TEST:")
        print("-" * 30)
        dns_test = self.results['tests']['dns_resolution']
        print(f"Status: {dns_test['overall_status'].upper()}")
        print(f"Successful: {dns_test['successful_resolutions']}/{dns_test['total_domains']}")
        for domain, result in dns_test['domains'].items():
            status_symbol = "✓" if result['status'] == 'success' else "✗"
            print(f"  {status_symbol} {domain}: {result.get('ip_address', result.get('error', 'Unknown'))}")
        print()
        
        # Network Connectivity Results
        print("NETWORK CONNECTIVITY TEST:")
        print("-" * 30)
        network_test = self.results['tests']['network_connectivity']
        print(f"Status: {network_test['overall_status'].upper()}")
        print(f"Successful: {network_test['successful_connections']}/{network_test['total_endpoints']}")
        for endpoint, result in network_test['endpoints'].items():
            status_symbol = "✓" if result['status'] == 'success' else "✗"
            print(f"  {status_symbol} {endpoint}: {result.get('connect_time', result.get('error', 'Unknown'))}")
        print()
        
        # Discord Bot Status
        print("DISCORD BOT STATUS:")
        print("-" * 30)
        bot_test = self.results['tests']['discord_bot_status']
        print(f"Status: {bot_test['overall_status'].upper()}")
        print(f"Health Check: {'PASS' if bot_test['health_check_result'] else 'FAIL'}")
        print(f"Summary: {bot_test['status_summary']}")
        if bot_test.get('error'):
            print(f"Error: {bot_test['error']}")
        print()
        
        # Recommendations
        print("RECOMMENDATIONS:")
        print("-" * 30)
        for i, recommendation in enumerate(self.results['recommendations'], 1):
            print(f"{i}. {recommendation}")
        print()
        
        print("="*60)

def main():
    """Main diagnostic function"""
    try:
        diagnostic = DiscordConnectivityDiagnostic()
        results = diagnostic.run_all_tests()
        diagnostic.print_results()
        
        # Save results to file
        diagnostics_dir = os.path.join(os.path.dirname(__file__), 'diagnostics')
        os.makedirs(diagnostics_dir, exist_ok=True)
        output_file = os.path.join(diagnostics_dir, f"discord_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Detailed results saved to: {output_file}")
        
        # Return appropriate exit code
        return 0 if results['summary']['overall_status'] == 'success' else 1
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        print(f"Diagnostic failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 