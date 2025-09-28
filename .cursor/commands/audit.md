# Run Comprehensive Audit

Run a comprehensive audit of the MHM codebase to get current system status, identify issues, and provide actionable insights.

## What This Does

- Scans all Python files for function complexity and patterns
- Analyzes module dependencies and relationships  
- Checks documentation synchronization status
- Identifies legacy references and cleanup opportunities
- Provides concise summary with key metrics and action items

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py audit`

## Output

- **System Health**: Overall codebase status and metrics
- **Critical Issues**: High-priority problems that need attention
- **Action Items**: Specific tasks to improve code quality
- **Documentation Status**: Sync status of paired documentation
- **Legacy References**: Outdated code patterns to clean up

## When to Use

- **Before major changes** - Understand current system state
- **After refactoring** - Verify improvements and identify next steps  
- **Weekly maintenance** - Regular health checks
- **When debugging** - Get comprehensive system overview
- **Before AI collaboration** - Provide context for AI assistants

## Key Metrics Provided

- Function complexity distribution
- Test coverage status
- Documentation sync status
- Legacy code patterns
- Module dependency health
- Recent activity summary

This audit follows the **Audit-First Protocol** - always run audit before creating documentation or making significant changes.
