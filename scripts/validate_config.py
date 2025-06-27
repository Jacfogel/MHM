#!/usr/bin/env python3
"""
MHM Configuration Validation Script

This script validates the MHM configuration without starting the full application.
Useful for checking configuration before deployment or troubleshooting issues.

Usage:
    python scripts/validate_config.py
    python scripts/validate_config.py --verbose
    python scripts/validate_config.py --fix-paths
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(description='Validate MHM Configuration')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed validation information')
    parser.add_argument('--fix-paths', action='store_true',
                       help='Automatically create missing directories')
    parser.add_argument('--exit-on-error', action='store_true',
                       help='Exit with error code if validation fails')
    
    args = parser.parse_args()
    
    try:
        # Import configuration validation
        from core.config import validate_all_configuration, print_configuration_report
        
        print("MHM Configuration Validation")
        print("=" * 50)
        
        # Run validation
        result = validate_all_configuration()
        
        # Print detailed report if verbose
        if args.verbose:
            print_configuration_report()
        else:
            # Print summary
            print(f"\nSUMMARY: {result['summary']}")
            
            if result['available_channels']:
                print(f"Available Channels: {', '.join(result['available_channels'])}")
            else:
                print("Available Channels: None")
            
            if result['errors']:
                print(f"\nERRORS ({len(result['errors'])}):")
                for i, error in enumerate(result['errors'], 1):
                    print(f"  {i}. {error}")
            
            if result['warnings']:
                print(f"\nWARNINGS ({len(result['warnings'])}):")
                for i, warning in enumerate(result['warnings'], 1):
                    print(f"  {i}. {warning}")
        
        # Handle fix-paths option
        if args.fix_paths and result['errors']:
            print("\nAttempting to fix path-related issues...")
            from core.config import validate_core_paths
            
            try:
                is_valid, errors, warnings = validate_core_paths()
                if is_valid:
                    print("✓ Path issues fixed successfully")
                else:
                    print("✗ Some path issues could not be fixed:")
                    for error in errors:
                        print(f"  - {error}")
            except Exception as e:
                print(f"✗ Error fixing paths: {e}")
        
        # Print recommendations
        if not result['valid']:
            print("\n" + "=" * 50)
            print("RECOMMENDATIONS:")
            print("1. Create a .env file in the MHM root directory")
            print("2. Configure at least one communication channel:")
            print("   - Email: EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD")
            print("   - Discord: DISCORD_BOT_TOKEN")
            print("3. Configure AI settings: LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL")
            print("4. See README.md for detailed setup instructions")
            print("=" * 50)
        
        # Exit with appropriate code
        if args.exit_on_error and not result['valid']:
            sys.exit(1)
        elif result['valid']:
            print("\n✓ Configuration validation passed!")
            sys.exit(0)
        else:
            print("\n✗ Configuration validation failed!")
            sys.exit(1)
            
    except ImportError as e:
        print(f"Error importing MHM modules: {e}")
        print("Make sure you're running this script from the MHM root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 