#!/usr/bin/env python3
"""
Quick Status Tool - Concise, actionable information for AI collaboration

Provides a quick overview of the codebase status with focus on actionable items.
Optimized for AI assistants to get essential information quickly.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("ai_development_tools")

class QuickStatus:
    """Quick status checker for AI collaboration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        # Note: ai_config functionality removed for simplicity
    
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
        """Get information about recent activity using shared utilities."""
        # Handle both relative and absolute imports
        try:
            from .services.common import should_exclude_file
        except ImportError:
            # Running directly, use absolute imports
            from ai_development_tools.services.common import should_exclude_file
        
        activity = {
            'last_audit': None,
            'recent_changes': set()  # Use set to avoid duplicates
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
        
        # Get git-based "recent" threshold (24 hours before last commit)
        recent_threshold = self._get_git_recent_threshold()
        
        # Check for recent changes in key directories
        # Import constants from services
        from ai_development_tools.services.constants import PROJECT_DIRECTORIES
        from ai_development_tools.services.standard_exclusions import (
            ALL_GENERATED_FILES, 
            STANDARD_EXCLUSION_PATTERNS
        )
        
        key_directories = list(PROJECT_DIRECTORIES)
        
        # Additional files to exclude (beyond standard exclusions)
        additional_excluded_files = set(ALL_GENERATED_FILES)
        
        # Additional patterns to exclude (beyond standard exclusions)
        additional_excluded_patterns = set(STANDARD_EXCLUSION_PATTERNS)
        
        for dir_path in key_directories:
            full_dir_path = self.project_root / dir_path
            if full_dir_path.exists() and full_dir_path.is_dir():
                try:
                    # Walk through all files in the directory
                    for file_path in full_dir_path.rglob('*'):
                        if file_path.is_file():
                            # Convert to relative path for exclusion checking
                            rel_path = file_path.relative_to(self.project_root)
                            rel_path_str = str(rel_path).replace('\\', '/')
                            
                            # Skip if file should be excluded by standard exclusions
                            if should_exclude_file(rel_path_str):
                                continue
                                
                            # Skip if file is in additional excluded files list
                            if rel_path_str in additional_excluded_files:
                                continue
                                
                            # Skip if file matches additional excluded patterns
                            if any(rel_path_str.startswith(pattern.rstrip('*')) or 
                                   rel_path_str.endswith(pattern.lstrip('*')) or
                                   pattern in rel_path_str for pattern in additional_excluded_patterns):
                                continue
                                
                            # Check if modified since git threshold
                            try:
                                mtime = file_path.stat().st_mtime
                                mtime_dt = datetime.fromtimestamp(mtime)
                                if mtime_dt >= recent_threshold:
                                    activity['recent_changes'].add(rel_path_str)
                            except:
                                pass
                except:
                    pass
        
        # Convert set to sorted list and limit to reasonable number
        activity['recent_changes'] = sorted(list(activity['recent_changes']), reverse=True)[:15]
        
        return activity
    
    def _get_git_recent_threshold(self) -> datetime:
        """Get git-based threshold for 'recent' changes (24 hours before last commit)."""
        try:
            import subprocess
            # Get the last commit date
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0 and result.stdout.strip():
                last_commit_str = result.stdout.strip()
                # Parse the commit date and make it timezone-aware
                last_commit = datetime.fromisoformat(last_commit_str.replace(' ', 'T'))
                # Make it timezone-naive for comparison with file timestamps
                if last_commit.tzinfo is not None:
                    last_commit = last_commit.replace(tzinfo=None)
                # Return 24 hours before the last commit
                return last_commit - timedelta(hours=24)
        except Exception:
            pass
        
        # Fallback to 7 days ago if git fails
        return datetime.now() - timedelta(days=7)
    
    def print_concise_status(self):
        """Print comprehensive status for AI consumption"""
        status = self.get_quick_status()
        
        logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # User-facing output stays as print() for immediate visibility
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System Health
        health = status['system_health']
        logger.info(f"[SYSTEM] Status: {health['overall_status']}")
        print(f"[SYSTEM] Status: {health['overall_status']}")
        if health['overall_status'] == 'ISSUES':
            missing_files = [f for f, s in health['core_files'].items() if s == 'MISSING']
            if missing_files:
                logger.warning(f"Missing core files: {', '.join(missing_files)}")
                print(f"  Missing: {', '.join(missing_files)}")
        print()
        
        # Documentation Status
        docs = status['documentation_status']
        logger.info(f"[DOCS] Coverage: {docs['coverage']}")
        print(f"[DOCS] Coverage: {docs['coverage']}")
        if docs['recent_audit']:
            logger.info(f"Last audit: {docs['recent_audit'][:19]}")
            print(f"  Last audit: {docs['recent_audit'][:19]}")
        
        # Check for missing documentation files
        missing_docs = [f for f, s in docs['key_files'].items() if s == 'MISSING']
        if missing_docs:
            logger.warning(f"Missing documentation files: {', '.join(missing_docs[:3])}")
            print(f"  Missing docs: {', '.join(missing_docs[:3])}")
        print()
        
        # Critical Issues
        if status['critical_issues']:
            logger.warning(f"Critical issues found: {len(status['critical_issues'])}")
            print("[CRITICAL ISSUES]")
            for issue in status['critical_issues']:
                logger.warning(f"  {issue}")
                print(f"  {issue}")
            print()
        
        # Action Items
        if status['action_items']:
            logger.info(f"Action items: {len(status['action_items'])}")
            print("[PRIORITY ACTIONS]")
            for i, action in enumerate(status['action_items'][:3], 1):  # Top 3 with numbering
                logger.info(f"  {i}. {action}")
                print(f"  {i}. {action}")
            print()
        
        # Recent Activity
        activity = status['recent_activity']
        if activity['recent_changes']:
            logger.info(f"Recent changes: {len(activity['recent_changes'])} files")
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
        logger.info("Generating JSON status output")
        # JSON output stays as print() for programmatic consumption
        print(json.dumps(status, indent=2))

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # Usage messages go to stdout for user visibility
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
        logger.error(f"Unknown command: {command}")
        # User-facing error messages stay as print() for immediate visibility
        print(f"Unknown command: {command}")
        print("Use 'concise' or 'json'")
        sys.exit(1)

if __name__ == '__main__':
    main() 