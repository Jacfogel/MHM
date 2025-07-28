#!/usr/bin/env python3
"""
Master tool to generate and update all documentation files automatically.
Runs both function registry and module dependencies generators.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import config

def run_generator(script_name: str, description: str) -> bool:
    """Run a documentation generator script."""
    print(f"\nRunning {description}...")
    print("=" * 60)
    
    try:
        script_path = Path(__file__).parent / script_name
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"[SUCCESS] {description} completed successfully!")
            return True
        else:
            print(f"[ERROR] {description} failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] {description} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] {description} failed with error: {e}")
        return False

def generate_all_documentation():
    """Generate all documentation files."""
    print("Starting Documentation Generation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run function registry generator
    success1 = run_generator('generate_function_registry.py', 'Function Registry Generator')
    
    # Run module dependencies generator
    success2 = run_generator('generate_module_dependencies.py', 'Module Dependencies Generator')
    
    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    
    if success1 and success2:
        print("[SUCCESS] All documentation generated successfully!")
        print("\n[FILES] Generated Files:")
        print("   - FUNCTION_REGISTRY_DETAIL.md")
        print("   - MODULE_DEPENDENCIES_DETAIL.md")
        print("\n[NEXT] Next Steps:")
        print("   - Review the generated documentation")
        print("   - Commit changes to version control")
        print("   - Update CHANGELOG.md if needed")
    else:
        print("[ERROR] Some documentation generation failed!")
        if not success1:
            print("   - FUNCTION_REGISTRY_DETAIL.md generation failed")
        if not success2:
            print("   - MODULE_DEPENDENCIES_DETAIL.md generation failed")
        print("\n[TROUBLESHOOT] Troubleshooting:")
        print("   - Check for syntax errors in Python files")
        print("   - Ensure all required modules are available")
        print("   - Check file permissions")

def show_usage():
    """Show usage information."""
    print("Documentation Generator - MHM Project")
    print("=" * 40)
    print("\nUsage:")
    print("  python generate_documentation.py          # Generate all documentation")
    print("  python generate_documentation.py --help   # Show this help")
    print("\nIndividual Generators:")
    print("  python generate_function_registry.py      # Generate FUNCTION_REGISTRY_DETAIL.md only")
    print("  python generate_module_dependencies.py    # Generate MODULE_DEPENDENCIES_DETAIL.md only")
    print("\nWhat it does:")
    print("  - Scans all Python files in the project")
    print("  - Extracts function/class information and dependencies")
    print("  - Generates comprehensive documentation")
    print("  - Excludes scripts/ directory as requested")
    print("  - Updates timestamps and statistics")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_usage()
    else:
        generate_all_documentation() 