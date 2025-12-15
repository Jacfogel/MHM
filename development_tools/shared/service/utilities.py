"""
Utility functions for AIToolsService.

Contains pure utility functions that don't depend on instance state.
These can be used as mixin methods or standalone functions.
"""

import re
from typing import Any, Dict, List, Optional, Sequence

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def format_list_for_display(items: Sequence[str], limit: int = 3) -> str:
    """Return a concise, comma-separated list with optional overflow marker."""
    filtered = [item for item in items if item]

    if not filtered:
        return ''

    if len(filtered) <= limit:
        return ', '.join(filtered)

    visible = ', '.join(filtered[:limit])
    remaining = len(filtered) - limit
    return f"{visible}, ... +{remaining}"


def format_percentage(value: Any, decimals: int = 1) -> str:
    """Format a numeric value as a percentage string."""
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


def extract_first_int(text: str) -> Optional[int]:
    """Return the first integer found in the supplied text or None."""
    if not isinstance(text, str):
        return None

    match = re.search(r'(-?\d+)', text)

    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None

    return None


def parse_function_entry(text: str) -> Optional[Dict[str, Any]]:
    """Parse a function discovery bullet into structured data."""
    if not text:
        return None

    pattern = re.compile(
        r'^(?P<name>.+?) \(file: (?P<file>.+?), complexity: (?P<complexity>\d+)\)'
    )

    match = pattern.match(text.strip())

    if not match:
        return None

    try:
        complexity = int(match.group('complexity'))
    except ValueError:
        complexity = None

    return {
        'function': match.group('name').strip(),
        'file': match.group('file').strip(),
        'complexity': complexity,
    }


def create_standard_format_result(total_issues: int, files_affected: int, 
                                  files: Optional[Dict[str, int]] = None, 
                                  details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standard format result structure."""
    result = {
        'summary': {
            'total_issues': total_issues,
            'files_affected': files_affected
        },
        'details': details or {}
    }
    if files:
        result['files'] = files
    return result


# Mixin class for adding utility methods to AIToolsService
class UtilitiesMixin:
    """Mixin class providing utility methods to AIToolsService."""
    
    def _format_list_for_display(self, items: Sequence[str], limit: int = 3) -> str:
        """Return a concise, comma-separated list with optional overflow marker."""
        return format_list_for_display(items, limit)
    
    def _format_percentage(self, value: Any, decimals: int = 1) -> str:
        """Format a numeric value as a percentage string."""
        return format_percentage(value, decimals)
    
    def _extract_first_int(self, text: str) -> Optional[int]:
        """Return the first integer found in the supplied text or None."""
        return extract_first_int(text)
    
    def _parse_function_entry(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a function discovery bullet into structured data."""
        return parse_function_entry(text)
    
    def _create_standard_format_result(self, total_issues: int, files_affected: int, 
                                       files: Optional[Dict[str, int]] = None, 
                                       details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a standard format result structure."""
        return create_standard_format_result(total_issues, files_affected, files, details)
    
    def _extract_key_info(self, script_name: str, result: Dict[str, Any]):
        """Extract key information from script result."""
        if script_name not in self.results_cache:
            self.results_cache[script_name] = {}
        if 'analyze_functions' in script_name:
            self._extract_function_metrics(result)
        elif 'analyze_function_registry' in script_name:
            self._extract_documentation_metrics(result)
        elif 'decision_support' in script_name:
            self._extract_decision_insights(result)
        elif 'analyze_error_handling' in script_name:
            self._extract_error_handling_metrics(result)
        elif 'analyze_module_dependencies' in script_name:
            data = result.get('data')
            if data:
                self.module_dependency_summary = data
    
    def _extract_function_metrics(self, result: Dict[str, Any]):
        """Extract function-related metrics"""
        output = result.get('output', '')
        if not isinstance(output, str):
            return
        lines = output.split('\n')
        metrics: Dict[str, Any] = {}
        import re
        section_lookup = {
            'high_complexity_examples': 'HIGH COMPLEXITY',
            'critical_complexity_examples': 'CRITICAL COMPLEXITY',
            'undocumented_examples': 'UNDOCUMENTED'
        }
        section_limits = {
            'high_complexity_examples': 5,
            'critical_complexity_examples': 5,
            'undocumented_examples': 5
        }
        current_section = None
        for raw_line in lines:
            line = raw_line.rstrip()
            lower = line.lower()
            if 'found' in lower and 'functions' in lower:
                match = re.search(r'Found (\d+) functions', line)
                if match:
                    metrics['total_functions'] = int(match.group(1))
                continue
            if 'moderate complexity' in lower and '(' in line:
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['moderate_complexity'] = int(match.group(1))
                continue
            if line.strip().upper().startswith('HIGH COMPLEXITY'):
                current_section = 'high_complexity_examples'
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['high_complexity'] = int(match.group(1))
                continue
            if line.strip().upper().startswith('CRITICAL COMPLEXITY'):
                current_section = 'critical_complexity_examples'
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['critical_complexity'] = int(match.group(1))
                continue
            if line.strip().upper().startswith('UNDOCUMENTED'):
                current_section = 'undocumented_examples'
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['undocumented'] = int(match.group(1))
                continue
            if any(line.strip().upper().startswith(label) for label in section_lookup.values()):
                current_section = None
                continue
            if current_section:
                stripped = line.strip()
                if not stripped.startswith('- '):
                    continue
                if '...and' in stripped and 'more' in stripped:
                    continue
                entry = self._parse_function_entry(stripped[2:])
                if entry is None:
                    continue
                metrics.setdefault(current_section, [])
                if len(metrics[current_section]) < section_limits[current_section]:
                    metrics[current_section].append(entry)
        # Preserve standard format if already present, otherwise store metrics
        if 'analyze_functions' in self.results_cache and isinstance(self.results_cache['analyze_functions'], dict):
            existing = self.results_cache['analyze_functions']
            if 'details' in existing and isinstance(existing.get('details'), dict):
                existing['details'].update(metrics)
                self.results_cache['analyze_functions'] = existing
            else:
                self.results_cache['analyze_functions'].update(metrics)
        else:
            self.results_cache['analyze_functions'] = metrics
    
    def _extract_documentation_metrics(self, result: Dict[str, Any]):
        """Extract documentation-related metrics"""
        metrics: Dict[str, Any] = {}
        data = result.get('data')
        if isinstance(data, dict):
            fd_metrics_raw = self.results_cache.get('analyze_functions', {}) or {}
            if 'details' in fd_metrics_raw and isinstance(fd_metrics_raw.get('details'), dict):
                fd_metrics = fd_metrics_raw['details']
            else:
                fd_metrics = fd_metrics_raw
            total_functions = fd_metrics.get('total_functions')
            undocumented = fd_metrics.get('undocumented', 0)
            documented = None
            if total_functions is not None and total_functions > 0:
                documented = total_functions - undocumented
                coverage_pct = (documented / total_functions) * 100
                if 0 <= coverage_pct <= 100:
                    metrics['doc_coverage'] = f"{coverage_pct:.2f}%"
                else:
                    metrics['doc_coverage'] = 'Unknown'
            else:
                metrics['doc_coverage'] = 'Unknown'
            totals = data.get('totals')
            if isinstance(totals, dict):
                metrics['totals'] = totals
                registry_functions_found = totals.get('functions_found')
                if registry_functions_found is not None:
                    metrics['registry_functions_found'] = registry_functions_found
                if total_functions is not None:
                    metrics['total_functions'] = total_functions
                if documented is not None:
                    metrics['documented_functions'] = documented
                classes_found = totals.get('classes_found')
                if classes_found is not None:
                    metrics['classes_found'] = classes_found
                files_scanned = totals.get('files_scanned')
                if files_scanned is not None:
                    metrics['files_scanned'] = files_scanned
            missing = data.get('missing')
            if isinstance(missing, dict):
                metrics['missing_docs'] = missing.get('count')
                metrics['missing_items'] = missing.get('count')
                missing_files = missing.get('missing_files')
                if missing_files:
                    metrics['missing_files'] = missing_files
            extra = data.get('extra')
            if isinstance(extra, dict):
                metrics['extra_items'] = extra.get('count')
        else:
            output = result.get('output', '')
            if not isinstance(output, str):
                self.results_cache['analyze_function_registry'] = metrics
                return
            lines_out = output.split('\n')
            for line in lines_out:
                lower = line.lower()
                if 'coverage:' in lower:
                    import re
                    match = re.search(r'coverage:\s*(\d+\.?\d*)%', line, re.IGNORECASE)
                    if match:
                        metrics['doc_coverage'] = match.group(1) + '%'
                        continue
                    coverage_text = line.split(':')[-1].strip()
                    metrics['doc_coverage'] = coverage_text
                elif 'missing from registry:' in lower:
                    metrics['missing_docs'] = line.split(':')[-1].strip()
                elif 'missing items:' in lower:
                    import re
                    match = re.search(r'missing items:\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        metrics['missing_items'] = match.group(1)
        self.results_cache['analyze_function_registry'] = metrics
    
    def _extract_decision_insights(self, result: Dict[str, Any]):
        """Extract decision support insights and metrics (counts)."""
        output = result.get('output', '')
        if not isinstance(output, str):
            return
        lines = output.split('\n')
        insights: List[str] = []
        metrics: Dict[str, Any] = {}
        critical_examples: List[Dict[str, Any]] = []
        high_examples: List[Dict[str, Any]] = []
        current_section = None
        i = 0
        if lines and len(lines) > 0:
            logger.debug(f"decision_support output sample (first 10 lines): {lines[:10]}")
        while i < len(lines):
            raw_line = lines[i]
            line = raw_line.strip()
            lower = line.lower()
            if any(keyword in lower for keyword in ['[warn]', '[critical]', '[info]', '[complexity]', '[doc]', '[dupe]']):
                insights.append(line)
                if '[critical]' in lower and 'critical' in lower and 'complexity' in lower:
                    current_section = 'critical'
                elif '[high]' in lower and 'high' in lower and 'complexity' in lower:
                    current_section = 'high'
                elif '[moderate]' in lower:
                    current_section = None
            if line.startswith('Total functions:'):
                value = line.split(':', 1)[1].strip()
                try:
                    metrics['total_functions'] = int(value)
                except ValueError:
                    metrics['total_functions'] = value
            elif line.startswith('Moderate complexity:'):
                value = line.split(':', 1)[1].strip()
                try:
                    metrics['moderate_complexity'] = int(value)
                except ValueError:
                    metrics['moderate_complexity'] = value
            elif line.startswith('High complexity:'):
                value = line.split(':', 1)[1].strip()
                try:
                    metrics['high_complexity'] = int(value)
                except ValueError:
                    metrics['high_complexity'] = value
            elif line.startswith('Critical complexity:'):
                value = line.split(':', 1)[1].strip()
                try:
                    metrics['critical_complexity'] = int(value)
                except ValueError:
                    metrics['critical_complexity'] = value
            elif line.startswith('Undocumented functions:'):
                value = line.split(':', 1)[1].strip()
                try:
                    metrics['undocumented'] = int(value)
                except ValueError:
                    metrics['undocumented'] = value
            elif line.startswith('- ') and current_section in ('critical', 'high'):
                try:
                    func_line = line[2:].strip()
                    if '(' in func_line:
                        func_name = func_line.split('(')[0].strip()
                        paren_content = func_line[func_line.find('(')+1:func_line.rfind(')')]
                        file_match = None
                        complexity_match = None
                        if 'file:' in paren_content:
                            file_part = paren_content.split('file:')[1].split(',')[0].strip()
                            file_match = file_part
                        if 'complexity:' in paren_content:
                            complexity_part = paren_content.split('complexity:')[1].strip()
                            try:
                                complexity_match = int(complexity_part)
                            except ValueError:
                                pass
                        example = {
                            'name': func_name,
                            'function': func_name,
                            'file': file_match or 'unknown',
                            'complexity': complexity_match or 0
                        }
                        if current_section == 'critical':
                            critical_examples.append(example)
                        elif current_section == 'high':
                            high_examples.append(example)
                except Exception as e:
                    logger.debug(f"Failed to parse complexity example line: {line} - {e}")
            i += 1
        if insights:
            metrics['decision_support_items'] = len(insights)
            metrics['decision_support_sample'] = insights[:5]
        if critical_examples:
            metrics['critical_complexity_examples'] = critical_examples
        if high_examples:
            metrics['high_complexity_examples'] = high_examples
        self.results_cache['decision_support_metrics'] = metrics
        self.results_cache['decision_support'] = metrics
        if metrics:
            logger.debug(f"Extracted decision_support metrics: {list(metrics.keys())}")
        else:
            logger.warning("No metrics extracted from decision_support output - metrics dict is empty")
        if 'analyze_functions' not in self.results_cache:
            self.results_cache['analyze_functions'] = {}
        existing = self.results_cache['analyze_functions']
        if 'details' in existing and isinstance(existing.get('details'), dict):
            if critical_examples:
                existing['details']['critical_complexity_examples'] = critical_examples
            if high_examples:
                existing['details']['high_complexity_examples'] = high_examples
            self.results_cache['analyze_functions'] = existing
        else:
            if critical_examples:
                existing['critical_complexity_examples'] = critical_examples
            if high_examples:
                existing['high_complexity_examples'] = high_examples
            self.results_cache['analyze_functions'] = existing
    
    def _extract_error_handling_metrics(self, result: Dict[str, Any]):
        """Extract error handling coverage metrics"""
        data = result.get('data')
        if isinstance(data, dict):
            metrics = {
                'total_functions': data.get('total_functions', 0),
                'functions_with_error_handling': data.get('functions_with_error_handling', 0),
                'functions_missing_error_handling': data.get('functions_missing_error_handling', 0),
                'analyze_error_handling': data.get('analyze_error_handling') or data.get('error_handling_coverage', 0),
                'functions_with_decorators': data.get('functions_with_decorators', 0),
                'error_handling_quality': data.get('error_handling_quality', {}),
                'error_patterns': data.get('error_patterns', {}),
                'recommendations': data.get('recommendations', []),
                'worst_modules': data.get('worst_modules', []),
                'phase1_candidates': data.get('phase1_candidates', []),
                'phase1_total': data.get('phase1_total', 0),
                'phase1_by_priority': data.get('phase1_by_priority', {}),
                'phase2_exceptions': data.get('phase2_exceptions', []),
                'phase2_total': data.get('phase2_total', 0),
                'phase2_by_type': data.get('phase2_by_type', {})
            }
        else:
            output = result.get('output', '')
            if not isinstance(output, str):
                return
            metrics = {}
            lines = output.split('\n')
            import re
            for line in lines:
                if 'Total Functions:' in line:
                    match = re.search(r'Total Functions: (\d+)', line)
                    if match:
                        metrics['total_functions'] = int(match.group(1))
                elif 'Functions with Error Handling:' in line:
                    match = re.search(r'Functions with Error Handling: (\d+)', line)
                    if match:
                        metrics['functions_with_error_handling'] = int(match.group(1))
                elif 'Functions Missing Error Handling:' in line:
                    match = re.search(r'Functions Missing Error Handling: (\d+)', line)
                    if match:
                        metrics['functions_missing_error_handling'] = int(match.group(1))
                elif 'Error Handling Coverage:' in line:
                    match = re.search(r'Error Handling Coverage: ([\d.]+)%', line)
                    if match:
                        metrics['analyze_error_handling'] = float(match.group(1))
        self.results_cache['analyze_error_handling'] = metrics
    
    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Collect combined metrics for audit summary output."""
        combined: Dict[str, Any] = {}
        for cache_key in ('analyze_functions', 'analyze_function_registry', 'decision_support_metrics', 'analyze_error_handling'):
            cache = self.results_cache.get(cache_key)
            if isinstance(cache, dict):
                for key, value in cache.items():
                    if value is not None and value != '':
                        combined[key] = value
        return combined
    
    def show_help(self):
        """Show comprehensive help and the available command list."""
        from ..common import COMMAND_TIERS
        print("AI Development Tools Runner")
        print("=" * 50)
        print(f"Comprehensive AI collaboration tools for the {self.project_name} project")
        print()
        print("USAGE:")
        print("  python development_tools/run_development_tools.py <command> [options]")
        print()
        print("AVAILABLE COMMANDS:")
        print()
        # COMMAND_REGISTRY would need to be imported or passed
        # For now, this is a simplified version
        print("EXAMPLES:")
        print("  python development_tools/run_development_tools.py status")
        print("  python development_tools/run_development_tools.py audit --full")
        print("  python development_tools/run_development_tools.py docs")
        print("  python development_tools/run_development_tools.py unused-imports")
        print()
        print("For detailed command options:")
        print("  python development_tools/run_development_tools.py <command> --help")
