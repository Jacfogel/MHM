#!/usr/bin/env python3
"""
Analyze path drift issues to understand what needs to be fixed
"""

from ai_development_tools.documentation_sync_checker import DocumentationSyncChecker

def analyze_drift_issues():
    checker = DocumentationSyncChecker()
    drift = checker.check_path_drift()
    
    print("=== PATH DRIFT ISSUES ANALYSIS ===")
    print(f"Total files with issues: {len([k for k, v in drift.items() if v])}")
    print(f"Total issues: {sum(len(v) for v in drift.values())}")
    print()
    
    # Sort by number of issues
    sorted_files = sorted(drift.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("=== TOP 10 FILES WITH MOST ISSUES ===")
    for file, issues in sorted_files[:10]:
        if issues:
            print(f"\n{file} ({len(issues)} issues):")
            # Show first 5 issues
            for issue in issues[:5]:
                print(f"  - {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")
    
    print("\n=== ISSUE TYPES ANALYSIS ===")
    issue_types = {}
    for file, issues in drift.items():
        if issues:
            for issue in issues:
                if "Missing file:" in issue:
                    issue_types["Missing files"] = issue_types.get("Missing files", 0) + 1
                elif "outdated module:" in issue:
                    issue_types["Outdated modules"] = issue_types.get("Outdated modules", 0) + 1
                else:
                    issue_types["Other"] = issue_types.get("Other", 0) + 1
    
    for issue_type, count in issue_types.items():
        print(f"{issue_type}: {count}")

if __name__ == "__main__":
    analyze_drift_issues()
