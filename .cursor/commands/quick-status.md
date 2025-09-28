# Get Quick System Status

Get a concise overview of the current MHM system status, recent activity, and immediate action items.

## What This Does

- Provides system health overview
- Shows recent development activity
- Identifies critical issues needing attention
- Lists immediate action items
- Gives quick metrics summary

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py status`

## Status Overview

- **System Health**: Overall codebase status (✅ Healthy / ⚠️ Issues / ❌ Critical)
- **Recent Activity**: Recent changes and development progress
- **Critical Issues**: High-priority problems requiring attention
- **Action Items**: Immediate tasks to improve system quality
- **Quick Metrics**: Key statistics and progress indicators

## When to Use

- **Daily check-ins** - Quick system health check
- **Before starting work** - Understand current state
- **After changes** - Verify system stability
- **When debugging** - Get quick context
- **AI collaboration** - Provide current system context

## Key Information Provided

- **Test Status**: Current test pass/fail status
- **Documentation Status**: Sync status of paired docs
- **Recent Changes**: Latest commits and modifications
- **Critical Issues**: Problems that need immediate attention
- **Next Steps**: Recommended actions to take

## Output Format

- **Concise Summary**: Key metrics and status
- **Action Items**: Specific tasks to address
- **Health Indicators**: Visual status indicators
- **Recent Activity**: Timeline of recent changes
- **Quick Stats**: Important numbers and percentages

## Integration

Uses data from:
- Recent git activity
- Test results
- Documentation sync status
- Audit findings
- System health checks
