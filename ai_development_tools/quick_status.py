#!/usr/bin/env python3
"""
Quick Status Tool - Concise, actionable information for AI collaboration

Provides a quick overview of the codebase status with focus on actionable items.
Optimized for AI assistants to get essential information quickly.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import config

class QuickStatus:
    """Quick status checker for AI collaboration."""
    
    def __init__(self):
        self.project_root = config.get_project_root()
        self.ai_config = config.get_ai_collaboration_config()
    
    def get_quick_status(self) -> Dict:
        """Get quick status overview"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._check_system_health(),
            'documentation_status': self._check_documentation_status(),
            'critical_issues': self._identify_critical_issues(),
            'action_items': self._generate_action_items(),
            'recent_activity': self._get_recent_activity()
        }
        return status
    
    def _check_system_health(self) -> Dict:
        """Check basic system health"""
        health = {
            'core_files': {},
            'key_directories': {},
            'overall_status': 'OK'
        }
        
        # Check core files
        core_files = ['run_mhm.py', 'core/service.py', 'core/config.py', 'requirements.txt']
        for file_path in core_files:
            full_path = self.project_root / file_path
            health['core_files'][file_path] = 'OK' if full_path.exists() else 'MISSING'
        
        # Check key directories
        key_dirs = ['core', 'ui', 'tests', 'ai_development_tools']
        for dir_path in key_dirs:
            full_path = self.project_root / dir_path
            health['key_directories'][dir_path] = 'OK' if full_path.exists() else 'MISSING'
        
        # Overall status
        missing_files = sum(1 for status in health['core_files'].values() if status == 'MISSING')
        missing_dirs = sum(1 for status in health['key_directories'].values() if status == 'MISSING')
        
        if missing_files > 0 or missing_dirs > 0:
            health['overall_status'] = 'ISSUES'
        
        return health
    
    def _check_documentation_status(self) -> Dict:
        """Check documentation status"""
        docs = {
            'coverage': 'Unknown',
            'recent_audit': None,
            'key_files': {}
        }
        
        # Check for recent audit results
        audit_file = Path(__file__).parent / 'ai_audit_detailed_results.json'
        if audit_file.exists():
            try:
                with open(audit_file, 'r') as f:
                    audit_data = json.load(f)
                    docs['recent_audit'] = audit_data.get('timestamp')
                    
                    # Extract coverage info if available
                    if 'results' in audit_data:
                        for script_name, result in audit_data['results'].items():
                            if script_name == 'audit_function_registry' and result.get('success'):
                                # Try to extract coverage from output
                                output = result.get('output', '')
                                if 'coverage:' in output.lower():
                                    for line in output.split('\n'):
                                        if 'coverage:' in line.lower():
                                            docs['coverage'] = line.split(':')[-1].strip()
                                            break
            except:
                pass
        
        # Check key documentation files
        key_docs = [
            'README.md', 'ai_development_docs/AI_CHANGELOG.md', 'development_docs/CHANGELOG_DETAIL.md', 
            'TODO.md', 'development_docs/FUNCTION_REGISTRY_DETAIL.md', 'development_docs/MODULE_DEPENDENCIES_DETAIL.md'
        ]
        for doc_file in key_docs:
            full_path = self.project_root / doc_file
            docs['key_files'][doc_file] = 'OK' if full_path.exists() else 'MISSING'
        
        return docs
    
    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that need immediate attention"""
        issues = []
        
        # Check system health
        health = self._check_system_health()
        if health['overall_status'] == 'ISSUES':
            missing_files = [f for f, status in health['core_files'].items() if status == 'MISSING']
            if missing_files:
                issues.append(f"Missing core files: {', '.join(missing_files)}")
        
        # Check documentation coverage
        docs = self._check_documentation_status()
        if docs['coverage'] != 'Unknown':
            try:
                coverage = float(docs['coverage'].replace('%', ''))
                if coverage < 90:
                    issues.append(f"Low documentation coverage: {coverage}%")
            except:
                pass
        
        # Check for missing documentation files
        missing_docs = [f for f, status in docs['key_files'].items() if status == 'MISSING']
        if missing_docs:
            issues.append(f"Missing documentation files: {', '.join(missing_docs[:3])}")
        
        return issues
    
    def _generate_action_items(self) -> List[str]:
        """Generate actionable items for improvement"""
        actions = []
        
        # Documentation improvements
        docs = self._check_documentation_status()
        if docs['coverage'] != 'Unknown':
            try:
                coverage = float(docs['coverage'].replace('%', ''))
                if coverage < 95:
                    actions.append(f"Improve documentation coverage (currently {coverage}%)")
            except:
                pass
        
        # System improvements
        health = self._check_system_health()
        missing_files = [f for f, status in health['core_files'].items() if status == 'MISSING']
        if missing_files:
            actions.append(f"Restore missing core files: {', '.join(missing_files)}")
        
        # Add general maintenance items
        if not docs['recent_audit']:
            actions.append("Run comprehensive audit to assess current state")
        
        return actions
    
    def _get_recent_activity(self) -> Dict:
        """Get information about recent activity"""
        activity = {
            'last_audit': None,
            'recent_changes': []
        }
        
        # Check for recent audit
        audit_file = Path(__file__).parent / 'ai_audit_detailed_results.json'
        if audit_file.exists():
            try:
                with open(audit_file, 'r') as f:
                    audit_data = json.load(f)
                    activity['last_audit'] = audit_data.get('timestamp')
            except:
                pass
        
        # Check for recent changes in key files
        key_files = ['ai_development_docs/AI_CHANGELOG.md', '../TODO.md']
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    mtime = full_path.stat().st_mtime
                    mtime_dt = datetime.fromtimestamp(mtime)
                    if (datetime.now() - mtime_dt).days < 7:  # Modified in last 7 days
                        activity['recent_changes'].append(f"{file_path} modified recently")
                except:
                    pass
        
        return activity
    
    def print_concise_status(self):
        """Print comprehensive status for AI consumption"""
        status = self.get_quick_status()
        
        # Remove headers - they'll be added by the consolidated report
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System Health
        health = status['system_health']
        print(f"[SYSTEM] Status: {health['overall_status']}")
        if health['overall_status'] == 'ISSUES':
            missing_files = [f for f, s in health['core_files'].items() if s == 'MISSING']
            if missing_files:
                print(f"  Missing: {', '.join(missing_files)}")
        print()
        
        # Documentation Status
        docs = status['documentation_status']
        print(f"[DOCS] Coverage: {docs['coverage']}")
        if docs['recent_audit']:
            print(f"  Last audit: {docs['recent_audit'][:19]}")
        
        # Check for missing documentation files
        missing_docs = [f for f, s in docs['key_files'].items() if s == 'MISSING']
        if missing_docs:
            print(f"  Missing docs: {', '.join(missing_docs[:3])}")
        print()
        
        # Critical Issues
        if status['critical_issues']:
            print("[CRITICAL ISSUES]")
            for issue in status['critical_issues']:
                print(f"  {issue}")
            print()
        
        # Action Items
        if status['action_items']:
            print("[PRIORITY ACTIONS]")
            for i, action in enumerate(status['action_items'][:3], 1):  # Top 3 with numbering
                print(f"  {i}. {action}")
            print()
        
        # Recent Activity
        activity = status['recent_activity']
        if activity['recent_changes']:
            print("[RECENT ACTIVITY]")
            for change in activity['recent_changes']:
                print(f"  {change}")
            print()
        
        # Quick Recommendations
        print("[QUICK COMMANDS]")
        print("  Status: python ai_development_tools/ai_tools_runner.py status")
        print("  Full audit: python ai_development_tools/ai_tools_runner.py audit")
        print("  Quick check: python ai_development_tools/quick_status.py concise")
    
    def print_json_status(self):
        """Print status as JSON for programmatic consumption"""
        status = self.get_quick_status()
        print(json.dumps(status, indent=2))

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python quick_status.py [concise|json]")
        print("  concise - Print concise status for AI consumption")
        print("  json    - Print status as JSON")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    status_checker = QuickStatus()
    
    if command == 'concise':
        status_checker.print_concise_status()
    elif command == 'json':
        status_checker.print_json_status()
    else:
        print(f"Unknown command: {command}")
        print("Use 'concise' or 'json'")
        sys.exit(1)

if __name__ == '__main__':
    main() 