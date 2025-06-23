#!/usr/bin/env python3
"""
Duplicate Message Cleanup Utility

This script scans all message files in the configured messages directory and removes
duplicate messages based on identical message content. It preserves the first
occurrence of each unique message and creates backups before making changes.

Usage: python cleanup_duplicate_messages.py [--dry-run] [--no-backup]
"""

import os
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))
from core.config import MESSAGES_BY_CATEGORY_DIR_PATH

def find_message_files():
    """Find all JSON message files in the configured messages directory."""
    message_files = []
    base_path = Path(MESSAGES_BY_CATEGORY_DIR_PATH)
    
    if not base_path.exists():
        print(f"Error: Message directory not found: {base_path}")
        return []
    
    # Recursively find all .json files
    for json_file in base_path.rglob("*.json"):
        message_files.append(json_file)
    
    return message_files

def check_duplicates_in_file(filepath):
    """Check for duplicate messages in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        if not messages:
            return False, 0, 0, data
        
        total_messages = len(messages)
        
        # Track unique messages by content
        seen_messages = {}
        unique_messages = []
        duplicates_found = []
        
        for i, msg in enumerate(messages):
            message_text = msg.get('message', '').strip()
            
            if message_text in seen_messages:
                # This is a duplicate
                duplicates_found.append({
                    'index': i,
                    'message': message_text,
                    'original_index': seen_messages[message_text]['index']
                })
            else:
                # First occurrence of this message
                seen_messages[message_text] = {
                    'index': i,
                    'message_obj': msg
                }
                unique_messages.append(msg)
        
        has_duplicates = len(duplicates_found) > 0
        duplicate_count = len(duplicates_found)
        
        if has_duplicates:
            data['messages'] = unique_messages
        
        return has_duplicates, total_messages, duplicate_count, data
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0, 0, None

def create_backup(filepath):
    """Create a backup of the file before modification."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup for {filepath}: {e}")
        return None

def clean_duplicates(args):
    """Main function to clean duplicates from all message files."""
    print(f"Scanning for message files in: {MESSAGES_BY_CATEGORY_DIR_PATH}")

    message_files = find_message_files()
    messages_base = Path(MESSAGES_BY_CATEGORY_DIR_PATH).resolve()
    
    if not message_files:
        print("No message files found.")
        return
    
    print(f"Found {len(message_files)} message files to check.")
    print()
    
    total_files_processed = 0
    total_files_with_duplicates = 0
    total_duplicates_removed = 0
    
    for filepath in message_files:
        print(f"Checking: {filepath.relative_to(messages_base)}")
        
        has_duplicates, total_count, duplicate_count, cleaned_data = check_duplicates_in_file(filepath)
        
        if has_duplicates:
            print(f"  Found {duplicate_count} duplicate(s) out of {total_count} messages")
            total_files_with_duplicates += 1
            total_duplicates_removed += duplicate_count
            
            if args.dry_run:
                print(f"  [DRY RUN] Would remove {duplicate_count} duplicates")
            else:
                # Create backup if requested
                if not args.no_backup:
                    backup_path = create_backup(filepath)
                    if backup_path:
                        print(f"  Backup created: {Path(backup_path).name}")
                
                # Write cleaned data
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
                    print(f"  Cleaned: {duplicate_count} duplicates removed")
                except Exception as e:
                    print(f"  Error writing cleaned file: {e}")
        else:
            print(f"  No duplicates found ({total_count} messages)")
        
        total_files_processed += 1
        print()
    
    # Summary
    print("=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files_processed}")
    print(f"Files with duplicates: {total_files_with_duplicates}")
    print(f"Total duplicates removed: {total_duplicates_removed}")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] No files were actually modified.")
    elif total_duplicates_removed > 0:
        print(f"\n✓ Successfully cleaned {total_duplicates_removed} duplicate messages!")
        if not args.no_backup:
            print("Backup files created for modified files.")
    else:
        print("\n✓ No duplicate messages found - all files are clean!")

def main():
    parser = argparse.ArgumentParser(
        description="Clean duplicate messages from all message files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_duplicate_messages.py              # Clean all duplicates with backups
  python cleanup_duplicate_messages.py --dry-run    # Preview what would be cleaned
  python cleanup_duplicate_messages.py --no-backup  # Clean without creating backups
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually modifying files'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup files (not recommended)'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("Running in DRY RUN mode - no files will be modified")
        print()
    
    try:
        clean_duplicates(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 