#!/usr/bin/env python3
"""
Test Coverage Metrics Regenerator for MHM

This script regenerates test coverage metrics and updates the 
TEST_COVERAGE_EXPANSION_PLAN.md with current data.

Usage:
    python ai_tools/regenerate_coverage_metrics.py [--update-plan] [--output-file]
"""

import re
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.logger import get_component_logger
    logger = get_component_logger(__name__)
except ImportError:
    # Fallback logging if core.logger not available
    logger = None

class CoverageMetricsRegenerator:
    """Regenerates test coverage metrics for MHM."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.coverage_plan_file = self.project_root / "development_docs" / "TEST_COVERAGE_EXPANSION_PLAN.md"
        
        # Core modules to track coverage for
        self.core_modules = [
            'core',
            'communication', 
            'ui',
            'tasks',
            'user',
            'ai'
        ]
        
    def run_coverage_analysis(self) -> Dict[str, Dict[str, any]]:
        """Run pytest coverage analysis and extract metrics."""
        if logger:
            logger.info("Running pytest coverage analysis...")
        
        try:
            # Run coverage analysis with proper configuration
            coverage_output = self.project_root / "ai_development_tools" / "coverage.json"
            cmd = [
                sys.executable, '-m', 'pytest',
                '--cov=core',
                '--cov=communication', 
                '--cov=ui',
                '--cov=tasks',
                '--cov=user',
                '--cov=ai',
                '--cov-report=term-missing',
                f'--cov-report=json:{coverage_output}',
                '--cov-config=coverage.ini',
                '--tb=no',
                '-q',
                '--maxfail=5',  # Stop after 5 failures
                'tests/'  # Run all tests like the plan
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                if logger:
                    logger.warning("Coverage analysis had issues, but continuing...")
            
            # Clean up .coverage file from root directory
            coverage_file = self.project_root / ".coverage"
            if coverage_file.exists():
                coverage_file.unlink()
                if logger:
                    logger.info("Cleaned up .coverage file from project root")
                
            # Parse coverage output
            coverage_data = self.parse_coverage_output(result.stdout)
            
            # Get overall coverage
            overall_coverage = self.extract_overall_coverage(result.stdout)
            
            return {
                'modules': coverage_data,
                'overall': overall_coverage
            }
            
        except Exception as e:
            logger.error(f"Error running coverage analysis: {e}")
            return {}
    
    def parse_coverage_output(self, output: str) -> Dict[str, Dict[str, any]]:
        """Parse the coverage output to extract module-specific metrics."""
        coverage_data = {}
        
        # Split output into sections
        sections = output.split('Name')
        if len(sections) < 2:
            return coverage_data
            
        coverage_section = sections[1]
        lines = coverage_section.strip().split('\n')
        
        for line in lines:
            if '---' in line or not line.strip():
                continue
                
            # Parse coverage line
            parts = line.split()
            if len(parts) >= 4:
                try:
                    module_name = parts[0]
                    statements = int(parts[1])
                    missed = int(parts[2])
                    coverage = int(parts[3].rstrip('%'))
                    
                    # Extract missing line numbers if available
                    missing_lines = []
                    if len(parts) > 4:
                        missing_part = ' '.join(parts[4:])
                        missing_lines = self.extract_missing_lines(missing_part)
                    
                    coverage_data[module_name] = {
                        'statements': statements,
                        'missed': missed,
                        'coverage': coverage,
                        'missing_lines': missing_lines,
                        'covered': statements - missed
                    }
                    
                except (ValueError, IndexError):
                    continue
                    
        return coverage_data
    
    def extract_missing_lines(self, missing_part: str) -> List[str]:
        """Extract missing line numbers from coverage output."""
        missing_lines = []
        
        # Look for patterns like "1-5, 10, 15-20"
        line_patterns = [
            r'(\d+)-(\d+)',  # Range like "1-5"
            r'(\d+)',        # Single line like "10"
        ]
        
        for pattern in line_patterns:
            matches = re.findall(pattern, missing_part)
            for match in matches:
                if len(match) == 2:  # Range
                    start, end = int(match[0]), int(match[1])
                    missing_lines.extend([str(i) for i in range(start, end + 1)])
                else:  # Single line
                    missing_lines.append(match[0])
                    
        return missing_lines
    
    def extract_overall_coverage(self, output: str) -> Dict[str, any]:
        """Extract overall coverage metrics."""
        overall_data = {
            'total_statements': 0,
            'total_missed': 0,
            'overall_coverage': 0
        }
        
        # Look for TOTAL line
        total_pattern = r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%'
        match = re.search(total_pattern, output)
        
        if match:
            overall_data['total_statements'] = int(match.group(1))
            overall_data['total_missed'] = int(match.group(2))
            overall_data['overall_coverage'] = int(match.group(3))
            
        return overall_data
    
    def categorize_modules(self, coverage_data: Dict[str, Dict[str, any]]) -> Dict[str, List[str]]:
        """Categorize modules by coverage level."""
        categories = {
            'excellent': [],      # 80%+
            'good': [],           # 60-79%
            'moderate': [],       # 40-59%
            'needs_work': [],     # 20-39%
            'critical': []        # <20%
        }
        
        for module_name, data in coverage_data.items():
            coverage = data['coverage']
            
            if coverage >= 80:
                categories['excellent'].append(module_name)
            elif coverage >= 60:
                categories['good'].append(module_name)
            elif coverage >= 40:
                categories['moderate'].append(module_name)
            elif coverage >= 20:
                categories['needs_work'].append(module_name)
            else:
                categories['critical'].append(module_name)
                
        return categories
    
    def generate_coverage_summary(self, coverage_data: Dict[str, Dict[str, any]], 
                                overall_data: Dict[str, any]) -> str:
        """Generate a coverage summary for the plan."""
        summary_lines = []
        
        # Overall coverage
        summary_lines.append(f"### **Overall Coverage: {overall_data['overall_coverage']}%**")
        summary_lines.append(f"- **Total Statements**: {overall_data['total_statements']:,}")
        summary_lines.append(f"- **Covered Statements**: {overall_data['total_statements'] - overall_data['total_missed']:,}")
        summary_lines.append(f"- **Uncovered Statements**: {overall_data['total_missed']:,}")
        summary_lines.append(f"- **Goal**: Expand to **80%+ coverage** for comprehensive reliability\n")
        
        # Coverage by category
        categories = self.categorize_modules(coverage_data)
        
        summary_lines.append("### **Coverage Summary by Category**")
        
        for category, modules in categories.items():
            if modules:
                avg_coverage = sum(coverage_data[m]['coverage'] for m in modules) / len(modules)
                summary_lines.append(f"- **{category.title()} ({avg_coverage:.0f}% avg)**: {len(modules)} modules")
                
        summary_lines.append("")
        
        # Detailed module breakdown
        summary_lines.append("### **Detailed Module Coverage**")
        
        # Sort modules by coverage (lowest first)
        sorted_modules = sorted(coverage_data.items(), key=lambda x: x[1]['coverage'])
        
        for module_name, data in sorted_modules:
            status_emoji = "*" if data['coverage'] >= 80 else "!" if data['coverage'] >= 60 else "X"
            summary_lines.append(f"- **{status_emoji} {module_name}**: {data['coverage']}% ({data['covered']}/{data['statements']} lines)")
            
        return '\n'.join(summary_lines)
    
    def update_coverage_plan(self, coverage_summary: str) -> bool:
        """Update the TEST_COVERAGE_EXPANSION_PLAN.md with new metrics."""
        if not self.coverage_plan_file.exists():
            logger.error(f"Coverage plan file not found: {self.coverage_plan_file}")
            return False
            
        try:
            with open(self.coverage_plan_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and replace the current status section
            current_status_pattern = r'(## 📊 \*\*Current Status\*\*.*?)(?=## 🎯|\Z)'
            
            new_status_section = f"## 📊 **Current Status**\n\n{coverage_summary}\n"
            
            if re.search(current_status_pattern, content, re.DOTALL):
                # Replace existing status section
                updated_content = re.sub(current_status_pattern, new_status_section, content, flags=re.DOTALL)
            else:
                # Add new status section after the header
                header_pattern = r'(# Test Coverage Expansion Plan.*?\n)'
                match = re.search(header_pattern, content, re.DOTALL)
                if match:
                    insert_pos = match.end()
                    updated_content = content[:insert_pos] + '\n' + new_status_section + content[insert_pos:]
                else:
                    # Fallback: add at beginning
                    updated_content = new_status_section + '\n\n' + content
            
            # Update the last updated timestamp
            timestamp_pattern = r'(> \*\*Last Updated\*\*: ).*'
            current_time = self.get_current_timestamp()
            updated_content = re.sub(timestamp_pattern, f'\\1{current_time}', updated_content)
            
            # Write updated content
            with open(self.coverage_plan_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            logger.info(f"Updated coverage plan: {self.coverage_plan_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating coverage plan: {e}")
            return False
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in the format used by the plan."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def run(self, update_plan: bool = False) -> Dict[str, any]:
        """Run the coverage metrics regeneration."""
        logger.info("Starting coverage metrics regeneration...")
        
        # Run coverage analysis
        coverage_results = self.run_coverage_analysis()
        
        if not coverage_results:
            logger.error("Failed to get coverage data")
            return {}
        
        # Generate summary
        coverage_summary = self.generate_coverage_summary(
            coverage_results['modules'], 
            coverage_results['overall']
        )
        
        # Print summary (headers removed - added by consolidated report)
        print(coverage_summary)
        
        # Update plan if requested
        if update_plan:
            success = self.update_coverage_plan(coverage_summary)
            if success:
                print("\n* Coverage plan updated successfully!")
            else:
                print("\n* Failed to update coverage plan")
        
        return coverage_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Regenerate test coverage metrics")
    parser.add_argument('--update-plan', action='store_true', 
                       help='Update TEST_COVERAGE_EXPANSION_PLAN.md with new metrics')
    parser.add_argument('--output-file', help='Output file for coverage report (optional)')
    
    args = parser.parse_args()
    
    regenerator = CoverageMetricsRegenerator()
    results = regenerator.run(update_plan=args.update_plan)
    
    if args.output_file and results:
        # Save detailed results to JSON file
        output_path = Path(args.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(results, f, indent=2)
        print(f"\n📊 Detailed coverage data saved to: {output_path}")


if __name__ == "__main__":
    main()
