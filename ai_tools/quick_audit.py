#!/usr/bin/env python3
"""
quick_audit.py
One-click comprehensive audit: runs all AI tools and provides a complete summary.
This is the AI's go-to tool for getting the full picture before making decisions.
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime

# Import config
sys.path.insert(0, str(Path(__file__).parent))
import config

def run_script(script_name: str) -> dict:
    """Run a script and capture its output."""
    try:
        result = subprocess.run(
            [sys.executable, f"ai_tools/{script_name}"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'script': script_name
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'script': script_name
        }

def print_summary(results: list):
    """Print a comprehensive summary of all audit results."""
    print("\n" + "="*80)
    print("🚀 QUICK AUDIT SUMMARY")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful Audits: {len(successful)}")
    for result in successful:
        print(f"  - {result['script']}")
    
    if failed:
        print(f"\n❌ Failed Audits: {len(failed)}")
        for result in failed:
            print(f"  - {result['script']}: {result['error']}")
    
    print("\n📊 KEY INSIGHTS:")
    for result in successful:
        if 'function_discovery' in result['script']:
            print("  - Function discovery completed")
        elif 'decision_support' in result['script']:
            print("  - Decision support analysis completed")
        elif 'audit_function_registry' in result['script']:
            print("  - Function registry audit completed")
        elif 'audit_module_dependencies' in result['script']:
            print("  - Module dependencies audit completed")
        elif 'analyze_documentation' in result['script']:
            print("  - Documentation overlap analysis completed")
    
    print("\n💡 NEXT STEPS:")
    print("  1. Review the detailed output from each audit above")
    print("  2. Use decision_support.py for actionable insights")
    print("  3. Run validate_ai_work.py before presenting any documentation")
    print("  4. Check TRIGGER.md for best practices")
    
    if config.QUICK_AUDIT['save_results']:
        results_file = config.QUICK_AUDIT['results_file']
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")

def main():
    print("🔍 Running comprehensive AI audit...")
    
    # Define the audit scripts to run
    audit_scripts = [
        'function_discovery.py',
        'decision_support.py', 
        'audit_function_registry.py',
        'audit_module_dependencies.py',
        'analyze_documentation.py'
    ]
    
    results = []
    for script in audit_scripts:
        print(f"\n📋 Running {script}...")
        result = run_script(script)
        results.append(result)
        
        if result['success']:
            print(f"✅ {script} completed successfully")
            if result['output']:
                print(result['output'])
        else:
            print(f"❌ {script} failed: {result['error']}")
    
    print_summary(results)
    print("\n🎯 Quick audit complete! Use this information for informed decision-making.")

if __name__ == "__main__":
    main() 