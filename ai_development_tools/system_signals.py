#!/usr/bin/env python3
"""
System Signals Tool

Generates system health and status signals for the MHM project.
This tool can be run independently or as part of audit workflows.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from .services.standard_exclusions import should_exclude_file
    from .services.constants import PROJECT_DIRECTORIES
except ImportError:
    from ai_development_tools.services.standard_exclusions import should_exclude_file
    from ai_development_tools.services.constants import PROJECT_DIRECTORIES

from core.logger import get_component_logger

logger = get_component_logger("ai_development_tools")


class SystemSignalsGenerator:
    """Generate system health and status signals"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
    def generate_system_signals(self) -> Dict[str, Any]:
        """Generate comprehensive system signals"""
        signals = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._check_system_health(),
            'recent_activity': self._get_recent_activity(),
            'critical_alerts': self._identify_critical_alerts(),
            'performance_indicators': self._assess_performance_indicators()
        }
        return signals
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check basic system health indicators"""
        health = {
            'overall_status': 'OK',
            'core_files': {},
            'key_directories': {},
            'last_audit': None,
            'warnings': [],
            'errors': []
        }
        
        # Check core files
        core_files = [
            'run_mhm.py', 'run_headless_service.py', 'run_tests.py',
            'core/service.py', 'core/config.py', 'core/logger.py',
            'requirements.txt', 'pyproject.toml'
        ]
        
        for file_path in core_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                health['core_files'][file_path] = 'OK'
            else:
                health['core_files'][file_path] = 'MISSING'
                health['warnings'].append(f"Missing core file: {file_path}")
        
        # Check key directories
        for dir_name in PROJECT_DIRECTORIES:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                health['key_directories'][dir_name] = 'OK'
            else:
                health['key_directories'][dir_name] = 'MISSING'
                health['warnings'].append(f"Missing key directory: {dir_name}")
        
        # Check for recent audit
        audit_file = self.project_root / 'ai_development_tools' / 'ai_audit_detailed_results.json'
        if audit_file.exists():
            try:
                stat = audit_file.stat()
                health['last_audit'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                health['last_audit'] = 'Unknown'
        else:
            health['warnings'].append("No recent audit data found")
        
        # Determine overall status
        if health['warnings'] or health['errors']:
            health['overall_status'] = 'ISSUES'
        else:
            health['overall_status'] = 'OK'
            
        return health
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent activity indicators"""
        activity = {
            'recent_changes': [],
            'git_status': 'Unknown',
            'last_commit': None,
            'uncommitted_changes': False
        }
        
        try:
            # Get recent file changes (last 24 hours)
            recent_threshold = self._get_git_recent_threshold()
            recent_files = []
            all_files_with_times = []
            
            for dir_name in PROJECT_DIRECTORIES:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    for file_path in dir_path.rglob('*'):
                        if file_path.is_file() and not should_exclude_file(file_path, context='recent_changes'):
                            try:
                                mtime = file_path.stat().st_mtime
                                mtime_dt = datetime.fromtimestamp(mtime)
                                rel_path = file_path.relative_to(self.project_root)
                                
                                # Store file with timestamp for sorting
                                all_files_with_times.append((str(rel_path), mtime_dt))
                                
                                # Check if within recent threshold
                                if mtime_dt >= recent_threshold:
                                    recent_files.append(str(rel_path))
                            except (OSError, ValueError):
                                continue
            
            # If no files within threshold, show 15 most recent files with timestamps
            if not recent_files and all_files_with_times:
                # Sort by modification time (most recent first) and take top 15
                all_files_with_times.sort(key=lambda x: x[1], reverse=True)
                recent_files = [f"{file_path} ({mtime_dt.strftime('%Y-%m-%d %H:%M')})" 
                              for file_path, mtime_dt in all_files_with_times[:15]]
            else:
                # Sort by modification time (most recent first) and limit
                recent_files = sorted(set(recent_files))[:15]
            
            activity['recent_changes'] = recent_files
            
        except Exception as e:
            activity['recent_changes'] = []
        
        # Check git status
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                activity['git_status'] = 'Clean' if not result.stdout.strip() else 'Modified'
                activity['uncommitted_changes'] = bool(result.stdout.strip())
        except Exception:
            activity['git_status'] = 'Unknown'
        
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
        critical_files = ['core/service.py', 'core/config.py', 'run_mhm.py']
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
    
    parser = argparse.ArgumentParser(description='Generate system signals for MHM project')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    generator = SystemSignalsGenerator()
    signals = generator.generate_system_signals()
    
    if args.json:
        output = json.dumps(signals, indent=2)
    else:
        output = _format_human_readable(signals)
    
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"System signals written to: {output_file}")
        # User-facing confirmation stays as print() for immediate visibility
        print(f"System signals written to: {output_file}")
    else:
        # User-facing output stays as print() for immediate visibility
        print(output)


def _format_human_readable(signals: Dict[str, Any]) -> str:
    """Format signals for human reading"""
    lines = []
    lines.append("SYSTEM SIGNALS")
    lines.append("=" * 50)
    lines.append(f"Generated: {signals['timestamp']}")
    lines.append("")
    
    # System Health
    health = signals['system_health']
    lines.append(f"System Health: {health['overall_status']}")
    if health['warnings']:
        for warning in health['warnings']:
            lines.append(f"  WARNING: {warning}")
    if health['errors']:
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
