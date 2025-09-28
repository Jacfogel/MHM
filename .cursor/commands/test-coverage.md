# Regenerate Test Coverage Metrics

Update test coverage metrics and analysis to reflect current testing status across the MHM codebase.

## What This Does

- Runs comprehensive test coverage analysis
- Categorizes modules by coverage level
- Identifies modules needing more tests
- Updates TEST_COVERAGE_EXPANSION_PLAN.md with current metrics
- Provides actionable testing recommendations
- **Automatically cleans up** `.coverage` file from project root

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py coverage`

## Coverage Analysis

- **Overall Coverage**: System-wide test coverage percentage
- **Module Breakdown**: Coverage by individual modules
- **Missing Lines**: Specific lines not covered by tests
- **High Priority**: Modules with low coverage that need attention
- **Test Categories**: Unit, integration, behavior, and UI test status

## When to Use

- **After adding tests** - Update coverage metrics
- **Before refactoring** - Ensure adequate test coverage exists
- **Weekly maintenance** - Track testing progress
- **When debugging** - Identify untested code paths
- **Before releases** - Verify test coverage meets standards

## Output Categories

- **✅ GOOD COVERAGE**: 80%+ coverage, comprehensive tests
- **🟡 PARTIAL COVERAGE**: 50-79% coverage, some gaps
- **❌ LOW COVERAGE**: <50% coverage, needs attention
- **🔴 CRITICAL**: <20% coverage, high risk

## Key Metrics

- **Total Coverage**: Overall system test coverage percentage
- **Module Coverage**: Individual module coverage breakdown
- **Missing Lines**: Specific untested code locations
- **Test Distribution**: Unit vs integration vs behavior tests
- **Priority Modules**: Which modules need testing attention first

## Integration

Updates `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md` with:
- Current coverage statistics
- Module categorization
- Testing recommendations
- Priority action items
