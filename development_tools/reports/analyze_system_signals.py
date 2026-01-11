#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
System Signals Analysis Tool

Analyzes system health and status signals for the project.
This tool can be run independently or as part of audit workflows.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
# Check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
if __name__ != '__main__' and __package__ and '.' in __package__:
    # Running as part of a package, use relative imports
    from ..shared.standard_exclusions import should_exclude_file
    from ..shared.constants import PROJECT_DIRECTORIES
else:
    # Running directly or not as a package, use absolute imports
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools.shared.constants import PROJECT_DIRECTORIES

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


class SystemSignalsAnalyzer:
    """Analyze system health and status signals"""
    
    def __init__(self, project_root: Optional[Path] = None, config_path: Optional[str] = None):
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            # Correctly resolve to project root (parent.parent.parent from reports/)
            self.project_root = Path(__file__).parent.parent.parent
        
        # Load config if provided
        # Check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
        if __name__ != '__main__' and __package__ and '.' in __package__:
            from . import config
        else:
            from development_tools import config
        
        self.config = config  # Store reference for reuse
        
        if config_path:
            config.load_external_config(config_path)
        else:
            config.load_external_config()
        
        self.system_signals_config = config.get_system_signals_config()
    
    def analyze_system_signals(self) -> Dict[str, Any]:
        """Analyze comprehensive system signals"""
        signals = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._check_system_health(),
            'recent_activity': self._get_recent_activity(),
            'critical_alerts': self._identify_critical_alerts(),
            'performance_indicators': self._assess_performance_indicators()
        }
        return signals
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check comprehensive system health indicators with actionable insights"""
        health = {
            'overall_status': 'OK',
            'core_files': {},
            'key_directories': {},
            'last_audit': None,
            'audit_freshness': None,
            'test_coverage_status': 'Unknown',
            'documentation_sync_status': 'Unknown',
            'health_indicators': [],
            'recommendations': [],
            'warnings': [],
            'errors': [],
            'severity_levels': {
                'INFO': [],
                'WARNING': [],
                'CRITICAL': []
            }
        }
        
        # Check core files - use config or project.key_files, fallback to generic defaults
        core_files = self.system_signals_config.get('core_files', [])
        if not core_files:
            # Try to get from project.key_files in config
            core_files = self.config.get_project_key_files(['requirements.txt', 'pyproject.toml'])
        
        for file_path in core_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                health['core_files'][file_path] = 'OK'
            else:
                health['core_files'][file_path] = 'MISSING'
                health['warnings'].append(f"Missing core file: {file_path}")
                health['severity_levels']['CRITICAL'].append(f"Missing core file: {file_path}")
        
        # Check key directories
        for dir_name in PROJECT_DIRECTORIES:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                health['key_directories'][dir_name] = 'OK'
            else:
                health['key_directories'][dir_name] = 'MISSING'
                health['warnings'].append(f"Missing key directory: {dir_name}")
                health['severity_levels']['WARNING'].append(f"Missing key directory: {dir_name}")
        
        # Check for recent audit and calculate freshness
        audit_file = self.project_root / 'development_tools' / 'reports' / 'analysis_detailed_results.json'
        if audit_file.exists():
            try:
                stat = audit_file.stat()
                last_audit_time = datetime.fromtimestamp(stat.st_mtime)
                health['last_audit'] = last_audit_time.isoformat()
                
                # Calculate audit freshness with specific time ranges
                time_since_audit = datetime.now() - last_audit_time
                days_since_audit = time_since_audit.days
                hours_since_audit = time_since_audit.total_seconds() / 3600
                
                # Format with specific time ranges
                if hours_since_audit < 1:
                    health['audit_freshness'] = '<1 hour'
                    health['health_indicators'].append("Audit data is very recent (<1 hour)")
                elif hours_since_audit < 24:
                    health['audit_freshness'] = '<24 hours'
                    health['health_indicators'].append(f"Audit data is recent ({int(hours_since_audit)} hours ago)")
                elif hours_since_audit <= 72:  # 25-72 hours (1-3 days)
                    health['audit_freshness'] = '25-72 hours'
                    health['health_indicators'].append(f"Audit data is {days_since_audit} day(s) old")
                elif days_since_audit <= 10:
                    health['audit_freshness'] = '4-10 days'
                    health['severity_levels']['WARNING'].append(f"Audit data is {days_since_audit} days old")
                    health['recommendations'].append("Run `python development_tools/run_development_tools.py audit` to refresh metrics")
                elif days_since_audit <= 30:
                    health['audit_freshness'] = '11-30 days'
                    health['severity_levels']['WARNING'].append(f"Audit data is {days_since_audit} days old")
                    health['recommendations'].append("Run `python development_tools/run_development_tools.py audit --full` for comprehensive analysis")
                else:
                    health['audit_freshness'] = f'>{days_since_audit} days'
                    health['severity_levels']['WARNING'].append(f"Audit data is {days_since_audit} days old")
                    health['recommendations'].append("Run `python development_tools/run_development_tools.py audit --full` for comprehensive analysis")
                
                # Try to extract test coverage and documentation sync status from audit results
                try:
                    import json
                    with open(audit_file, 'r', encoding='utf-8') as f:
                        audit_data = json.load(f)
                    
                    # Check test coverage status
                    if 'results' in audit_data:
                        # Look for test coverage data
                        coverage_keys = ['run_test_coverage', 'analyze_test_coverage', 'generate_test_coverage_report']
                        for key in coverage_keys:
                            if key in audit_data['results']:
                                coverage_result = audit_data['results'][key]
                                if 'data' in coverage_result:
                                    coverage_data = coverage_result['data']
                                    if isinstance(coverage_data, dict):
                                        # Try to extract overall coverage
                                        overall = coverage_data.get('overall', {})
                                        if isinstance(overall, dict):
                                            coverage_pct = overall.get('overall_coverage', 0)
                                            if coverage_pct:
                                                if coverage_pct >= 80:
                                                    health['test_coverage_status'] = 'Good'
                                                    health['health_indicators'].append(f"Test coverage: {coverage_pct}%")
                                                elif coverage_pct >= 60:
                                                    health['test_coverage_status'] = 'Moderate'
                                                    health['severity_levels']['WARNING'].append(f"Test coverage is {coverage_pct}% (below 80% target)")
                                                    health['recommendations'].append("Consider expanding test coverage for better reliability")
                                                else:
                                                    health['test_coverage_status'] = 'Low'
                                                    health['severity_levels']['WARNING'].append(f"Test coverage is {coverage_pct}% (below 60%)")
                                                    health['recommendations'].append("Test coverage is low - prioritize adding tests for critical paths")
                                                break
                    
                    # Check documentation sync status
                    if 'results' in audit_data and 'analyze_documentation_sync' in audit_data['results']:
                        doc_sync_result = audit_data['results']['analyze_documentation_sync']
                        if 'data' in doc_sync_result:
                            doc_sync_data = doc_sync_result['data']
                            if isinstance(doc_sync_data, dict):
                                summary = doc_sync_data.get('summary', {})
                                total_issues = summary.get('total_issues', 0)
                                status = summary.get('status', 'UNKNOWN')
                                
                                if total_issues == 0 and status in ['PASS', 'OK']:
                                    health['documentation_sync_status'] = 'Synchronized'
                                    health['health_indicators'].append("Documentation is synchronized")
                                elif total_issues <= 5:
                                    health['documentation_sync_status'] = 'Minor Issues'
                                    health['severity_levels']['INFO'].append(f"Documentation has {total_issues} minor sync issue(s)")
                                    health['recommendations'].append("Run `python development_tools/run_development_tools.py doc-sync` to check details")
                                else:
                                    health['documentation_sync_status'] = 'Issues'
                                    health['severity_levels']['WARNING'].append(f"Documentation has {total_issues} sync issue(s)")
                                    health['recommendations'].append("Run `python development_tools/run_development_tools.py doc-fix` to address documentation issues")
                except Exception as e:
                    logger.debug(f"Failed to parse audit data for health indicators: {e}")
                    
            except Exception:
                health['last_audit'] = 'Unknown'
        else:
            health['warnings'].append("No recent audit data found")
            health['severity_levels']['WARNING'].append("No recent audit data found")
            health['recommendations'].append("Run `python development_tools/run_development_tools.py audit --quick` for initial health check")
        
        # Enhanced error log analysis
        error_log = self.project_root / 'logs' / 'errors.log'
        if error_log.exists():
            try:
                stat = error_log.stat()
                if stat.st_size > 0:
                    # Check if log was modified recently
                    time_since_error = datetime.now().timestamp() - stat.st_mtime
                    if time_since_error < 3600:  # Last hour
                        health['severity_levels']['CRITICAL'].append("Recent errors detected in logs/errors.log (last hour)")
                        health['recommendations'].append("Review logs/errors.log for recent error details")
                    elif time_since_error < 86400:  # Last 24 hours
                        health['severity_levels']['WARNING'].append("Errors detected in logs/errors.log (last 24 hours)")
                        health['recommendations'].append("Check logs/errors.log for recent errors")
                    
                    # Check log file size
                    size_mb = stat.st_size / (1024 * 1024)
                    if size_mb > 10:
                        health['severity_levels']['WARNING'].append(f"Error log file is large ({size_mb:.1f}MB) - consider rotation")
            except Exception:
                pass
        
        # Determine overall status based on severity levels
        if health['severity_levels']['CRITICAL']:
            health['overall_status'] = 'CRITICAL'
        elif health['severity_levels']['WARNING']:
            health['overall_status'] = 'ISSUES'
        elif health['warnings'] or health['errors']:
            health['overall_status'] = 'ISSUES'
        else:
            health['overall_status'] = 'OK'
            
        return health
    
    def _is_meaningful_change(self, file_path: str) -> bool:
        """
        Determine if a file change is meaningful (code, docs, config) vs non-meaningful (cache, logs, data).
        
        Returns True for meaningful changes, False for non-meaningful changes.
        """
        file_path_lower = file_path.lower()
        path_obj = Path(file_path)
        
        # Exclude lock files
        if file_path.endswith('.lock') or '.audit_in_progress.lock' in file_path:
            return False
        
        # Exclude cache files and directories
        if '.cache' in file_path_lower or '/cache/' in file_path_lower or '\\cache\\' in file_path_lower:
            return False
        
        # Exclude log files (unless they indicate errors - but we'll exclude all for simplicity)
        if file_path.endswith('.log') and 'logs/' in file_path_lower:
            return False
        
        # Exclude data files (JSON in data directories, but allow config JSON files)
        if file_path.endswith('.json'):
            # Allow config files in root/config directories
            if 'config/' in file_path_lower or file_path_lower.startswith('config/'):
                return True
            # Allow package.json, pyproject.toml companion files
            if 'package.json' in file_path_lower or 'tsconfig.json' in file_path_lower:
                return True
            # Exclude data directory JSON files
            if '/data/' in file_path_lower or '\\data\\' in file_path_lower:
                return False
            # Exclude JSON in user data directories
            if '/users/' in file_path_lower or '\\users\\' in file_path_lower:
                return False
        
        # Exclude generated files (already handled by should_exclude_file, but be explicit)
        if should_exclude_file(file_path, context='recent_changes'):
            return False
        
        # Prioritize meaningful file types
        meaningful_extensions = {'.py', '.md', '.mdc', '.toml', '.ini', '.cfg', '.yaml', '.yml'}
        if path_obj.suffix.lower() in meaningful_extensions:
            return True
        
        # Allow config files in root or config directories
        if 'config' in path_obj.parts or path_obj.name in ['requirements.txt', 'setup.py', 'pyproject.toml']:
            return True
        
        # Exclude test artifacts and temporary files
        if path_obj.name.startswith('.') and path_obj.name != '.gitignore':
            return False
        
        # Default: include other files (but they'll be lower priority)
        return True
    
    def _get_change_significance_score(self, file_path: str) -> int:
        """
        Score change significance: higher = more significant.
        Used for sorting: code > docs > config > other meaningful > non-meaningful.
        """
        if not self._is_meaningful_change(file_path):
            return 0
        
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()
        
        # Code files: highest priority
        if ext == '.py':
            return 100
        
        # Documentation: high priority
        if ext in {'.md', '.mdc'}:
            return 80
        
        # Config files: medium-high priority
        if ext in {'.toml', '.ini', '.cfg', '.yaml', '.yml'}:
            return 60
        if 'config' in path_obj.parts or path_obj.name in ['requirements.txt', 'setup.py', 'pyproject.toml']:
            return 60
        
        # Other meaningful files: medium priority
        return 40
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent activity indicators using git to detect actual changes."""
        activity = {
            'recent_changes': [],
            'git_status': 'Unknown',
            'last_commit': None,
            'uncommitted_changes': False
        }
        
        # Check git status first
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                activity['git_status'] = 'Clean' if not result.stdout.strip() else 'Modified'
                activity['uncommitted_changes'] = bool(result.stdout.strip())
        except Exception:
            activity['git_status'] = 'Unknown'
        
        # Get recent changes using git diff and git status
        try:
            changed_files = set()
            
            # Get uncommitted changes (working directory)
            try:
                status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                             capture_output=True, text=True, cwd=self.project_root)
                if status_result.returncode == 0:
                    for line in status_result.stdout.strip().split('\n'):
                        if line.strip():
                            # Git status format: "XY filename" where XY is status code
                            # X = staged status, Y = unstaged status
                            # D = deleted, M = modified, A = added, etc.
                            status_code = line.strip()[:2]
                            # Skip deleted files (D in either position)
                            if 'D' in status_code:
                                continue
                            
                            # Extract filename (skip status code)
                            parts = line.strip().split(None, 1)
                            if len(parts) >= 2:
                                file_path = parts[1]
                                # Handle renamed files (format: "old -> new")
                                if ' -> ' in file_path:
                                    file_path = file_path.split(' -> ')[1]
                                changed_files.add(file_path)
            except Exception as e:
                logger.debug(f"Failed to get git status: {e}")
            
            # Get files changed in last commit (if any)
            # Use --diff-filter to exclude deleted files
            try:
                diff_result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=d', 'HEAD~1', 'HEAD'], 
                                           capture_output=True, text=True, cwd=self.project_root)
                if diff_result.returncode == 0:
                    for line in diff_result.stdout.strip().split('\n'):
                        if line.strip():
                            changed_files.add(line.strip())
            except Exception:
                # If HEAD~1 doesn't exist (new repo), just use HEAD
                try:
                    diff_result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=d', 'HEAD'], 
                                               capture_output=True, text=True, cwd=self.project_root)
                    if diff_result.returncode == 0:
                        for line in diff_result.stdout.strip().split('\n'):
                            if line.strip():
                                changed_files.add(line.strip())
                except Exception:
                    pass
            
            # Filter and prioritize meaningful changes
            meaningful_changes = []
            for file_path in changed_files:
                # Normalize path separators
                file_path_normalized = file_path.replace('\\', '/')
                
                # Skip if file doesn't exist (deleted files)
                full_path = self.project_root / file_path_normalized
                if not full_path.exists():
                    continue
                
                # Skip if excluded by standard exclusions
                if should_exclude_file(file_path_normalized, context='recent_changes'):
                    continue
                
                # Check if meaningful
                if self._is_meaningful_change(file_path_normalized):
                    score = self._get_change_significance_score(file_path_normalized)
                    meaningful_changes.append((file_path_normalized, score))
            
            # Sort by significance (highest first), then limit to 10
            meaningful_changes.sort(key=lambda x: x[1], reverse=True)
            activity['recent_changes'] = [file_path for file_path, _ in meaningful_changes[:10]]
            
            # Fallback: If no git changes found, use mtime-based detection for last 24 hours
            if not activity['recent_changes']:
                recent_threshold = datetime.now() - timedelta(hours=24)
                all_files_with_scores = []
                
                for dir_name in PROJECT_DIRECTORIES:
                    dir_path = self.project_root / dir_name
                    if dir_path.exists():
                        for file_path in dir_path.rglob('*'):
                            if file_path.is_file():
                                rel_path = file_path.relative_to(self.project_root)
                                rel_path_str = str(rel_path).replace('\\', '/')
                                
                                if not should_exclude_file(rel_path_str, context='recent_changes'):
                                    if self._is_meaningful_change(rel_path_str):
                                        try:
                                            mtime = file_path.stat().st_mtime
                                            mtime_dt = datetime.fromtimestamp(mtime)
                                            
                                            if mtime_dt >= recent_threshold:
                                                score = self._get_change_significance_score(rel_path_str)
                                                all_files_with_scores.append((rel_path_str, score, mtime_dt))
                                        except (OSError, ValueError):
                                            continue
                
                # Sort by score (highest first), then by mtime (most recent first), limit to 10
                all_files_with_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
                activity['recent_changes'] = [file_path for file_path, _, _ in all_files_with_scores[:10]]
            
        except Exception as e:
            logger.debug(f"Error getting recent activity: {e}")
            activity['recent_changes'] = []
        
        return activity
    
    def _get_git_recent_threshold(self) -> datetime:
        """Get threshold for 'recent' based on git history"""
        try:
            import subprocess
            result = subprocess.run(['git', 'log', '-1', '--format=%ct'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                last_commit_timestamp = int(result.stdout.strip())
                last_commit_dt = datetime.fromtimestamp(last_commit_timestamp)
                # 6 hours before last commit (more practical for active development)
                threshold = last_commit_dt - timedelta(hours=6)
                return threshold
        except Exception:
            pass
        
        # Fallback to 24 hours ago if git is not available
        return datetime.now() - timedelta(hours=24)
    
    def _identify_critical_alerts(self) -> List[str]:
        """Identify critical system alerts"""
        alerts = []
        
        # Check for critical files
        # Use core_files from config, or fallback to generic
        critical_files = self.system_signals_config.get('core_files', [])
        if not critical_files:
            critical_files = self.config.get_project_key_files([])
        for file_path in critical_files:
            if not (self.project_root / file_path).exists():
                alerts.append(f"CRITICAL: Missing {file_path}")
        
        # Check for error logs
        error_log = self.project_root / 'logs' / 'errors.log'
        if error_log.exists():
            try:
                stat = error_log.stat()
                if stat.st_size > 0:
                    # Check if log was modified recently (last hour)
                    if datetime.now().timestamp() - stat.st_mtime < 3600:
                        alerts.append("CRITICAL: Recent errors in logs/errors.log")
            except Exception:
                pass
        
        return alerts
    
    def _assess_performance_indicators(self) -> Dict[str, Any]:
        """Assess system performance indicators"""
        indicators = {
            'log_file_sizes': {},
            'cache_status': 'Unknown',
            'memory_usage': 'Unknown'
        }
        
        # Check log file sizes
        logs_dir = self.project_root / 'logs'
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                try:
                    size_mb = log_file.stat().st_size / (1024 * 1024)
                    indicators['log_file_sizes'][log_file.name] = f"{size_mb:.1f}MB"
                except Exception:
                    pass
        
        # Check cache status
        cache_dir = self.project_root / 'ai' / 'cache'
        if cache_dir.exists():
            try:
                cache_files = list(cache_dir.rglob('*'))
                indicators['cache_status'] = f"{len(cache_files)} files"
            except Exception:
                indicators['cache_status'] = 'Error'
        
        return indicators


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze system signals for the project')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    analyzer = SystemSignalsAnalyzer()
    signals = analyzer.analyze_system_signals()
    
    if args.json:
        output = json.dumps(signals, indent=2)
    else:
        output = _format_human_readable(signals)
    
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"System signals analysis written to: {output_file}")
        # User-facing confirmation stays as print() for immediate visibility
        print(f"System signals analysis written to: {output_file}")
    else:
        # User-facing output stays as print() for immediate visibility
        print(output)


def _format_human_readable(signals: Dict[str, Any]) -> str:
    """Format signals for human reading"""
    lines = []
    lines.append("SYSTEM SIGNALS ANALYSIS")
    lines.append("=" * 50)
    lines.append(f"Generated: {signals['timestamp']}")
    lines.append("")
    
    # System Health
    health = signals['system_health']
    overall_status = health.get('overall_status', 'Unknown')
    status_emoji = {
        'OK': '✓',
        'ISSUES': '⚠',
        'CRITICAL': '✗'
    }.get(overall_status, '?')
    lines.append(f"System Health: {status_emoji} {overall_status}")
    lines.append("")
    
    # Health Indicators
    if health.get('health_indicators'):
        lines.append("Health Indicators:")
        for indicator in health['health_indicators']:
            lines.append(f"  ✓ {indicator}")
        lines.append("")
    
    # Severity-based issues
    severity_levels = health.get('severity_levels', {})
    if severity_levels.get('CRITICAL'):
        lines.append("CRITICAL ISSUES:")
        for issue in severity_levels['CRITICAL']:
            lines.append(f"  ✗ {issue}")
        lines.append("")
    
    if severity_levels.get('WARNING'):
        lines.append("WARNINGS:")
        for warning in severity_levels['WARNING']:
            lines.append(f"  ⚠ {warning}")
        lines.append("")
    
    if severity_levels.get('INFO'):
        lines.append("INFO:")
        for info in severity_levels['INFO']:
            lines.append(f"  ℹ {info}")
        lines.append("")
    
    # Recommendations
    if health.get('recommendations'):
        lines.append("RECOMMENDATIONS:")
        for i, rec in enumerate(health['recommendations'], 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
    
    # Audit freshness
    if health.get('audit_freshness'):
        lines.append(f"Audit Freshness: {health['audit_freshness']}")
        if health.get('last_audit'):
            lines.append(f"  Last Audit: {health['last_audit']}")
        lines.append("")
    
    # Test coverage status
    if health.get('test_coverage_status') != 'Unknown':
        lines.append(f"Test Coverage Status: {health['test_coverage_status']}")
        lines.append("")
    
    # Documentation sync status
    if health.get('documentation_sync_status') != 'Unknown':
        lines.append(f"Documentation Sync Status: {health['documentation_sync_status']}")
        lines.append("")
    
    # Legacy warnings/errors (for backward compatibility)
    if health.get('warnings') and not severity_levels.get('WARNING'):
        for warning in health['warnings']:
            lines.append(f"  WARNING: {warning}")
        lines.append("")
    if health.get('errors'):
        for error in health['errors']:
            lines.append(f"  ERROR: {error}")
        lines.append("")
    
    # Recent Activity
    activity = signals['recent_activity']
    lines.append(f"Git Status: {activity['git_status']}")
    if activity['recent_changes']:
        lines.append(f"Recent Changes ({len(activity['recent_changes'])} files):")
        for change in activity['recent_changes'][:5]:  # Show first 5
            lines.append(f"  - {change}")
        if len(activity['recent_changes']) > 5:
            lines.append(f"  ... and {len(activity['recent_changes']) - 5} more")
    lines.append("")
    
    # Critical Alerts
    if signals['critical_alerts']:
        lines.append("CRITICAL ALERTS:")
        for alert in signals['critical_alerts']:
            lines.append(f"  - {alert}")
        lines.append("")
    
    # Performance Indicators
    perf = signals['performance_indicators']
    if perf['log_file_sizes']:
        lines.append("Log File Sizes:")
        for log_name, size in perf['log_file_sizes'].items():
            lines.append(f"  - {log_name}: {size}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    from datetime import timedelta
    main()

