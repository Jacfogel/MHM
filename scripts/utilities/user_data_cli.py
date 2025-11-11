#!/usr/bin/env python3
"""
User Data CLI Tool - Command line interface for enhanced user data management
"""

import argparse
import json
import sys
import os
# Add project root to path (scripts/utilities -> project root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.user_data_manager import (
    user_data_manager, 
    update_message_references, 
    backup_user_data, 
    get_user_data_summary,
    update_user_index,
    rebuild_user_index
)
from core.user_data_handlers import get_all_user_ids
from core.logger import get_component_logger

logger = get_component_logger('main')

def format_size(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def cmd_update_references(args):
    """Update message references for a user"""
    if args.user_id == "all":
        user_ids = get_all_user_ids()
        success_count = 0
        for user_id in user_ids:
            if user_id and update_message_references(user_id):
                success_count += 1
        print(f"Updated message references for {success_count}/{len(user_ids)} users")
    else:
        if update_message_references(args.user_id):
            print(f"✅ Updated message references for user {args.user_id}")
        else:
            print(f"❌ Failed to update references for user {args.user_id}")

def cmd_backup_user(args):
    """Create a backup of user data"""
    try:
        backup_path = backup_user_data(args.user_id, include_messages=args.include_messages)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def cmd_summary(args):
    """Show user data summary"""
    if args.user_id == "all":
        user_ids = get_all_user_ids()
        print(f"\n📊 Data Summary for All Users ({len(user_ids)} users)")
        print("=" * 60)
        
        total_size = 0
        total_files = 0
        
        for user_id in user_ids:
            if not user_id:
                continue
                
            summary = get_user_data_summary(user_id)
            if "error" in summary:
                print(f"❌ {user_id}: Error - {summary['error']}")
                continue
                
            total_size += summary["total_size"]
            total_files += summary["total_files"]
            
            print(f"\n👤 User: {user_id}")
            print(f"   Files: {summary['total_files']}, Size: {format_size(summary['total_size'])}")
            
            # Show message categories
            if summary["messages"]:
                categories = list(summary["messages"].keys())
                print(f"   Categories: {', '.join(categories)}")
        
        print(f"\n📈 TOTALS: {total_files} files, {format_size(total_size)}")
        
    else:
        summary = get_user_data_summary(args.user_id)
        if "error" in summary:
            print(f"❌ Error: {summary['error']}")
            return
            
        print(f"\n📊 Data Summary for User: {args.user_id}")
        print("=" * 50)
        
        # Profile info
        profile = summary["profile"]
        print(f"👤 Profile: {'✅' if profile['exists'] else '❌'} ({format_size(profile['size'])})")
        
        # Preferences
        prefs = summary["preferences"]
        print(f"⚙️  Preferences: {'✅' if prefs['exists'] else '❌'} ({format_size(prefs['size'])})")
        
        # Schedules
        schedules = summary["schedules"]
        print(f"📅 Schedules: {'✅' if schedules['exists'] else '❌'} ({format_size(schedules['size'])}, {schedules['periods']} periods)")
        
        # Messages
        print(f"💬 Messages:")
        if summary["messages"]:
            for category, info in summary["messages"].items():
                print(f"   {category}: {info['message_count']} messages ({format_size(info['size'])})")
        else:
            print("   No message files found")
        
        # Sent messages
        sent = summary["sent_messages"]
        print(f"📤 Sent Messages: {'✅' if sent['exists'] else '❌'} ({format_size(sent['size'])}, {sent['count']} messages)")
        
        # Logs
        print(f"📋 Logs:")
        if summary["logs"]:
            for log_type, info in summary["logs"].items():
                print(f"   {log_type}: {info['entry_count']} entries ({format_size(info['size'])})")
        else:
            print("   No log files found")
        
        print(f"\n📈 TOTAL: {summary['total_files']} files, {format_size(summary['total_size'])}")

def cmd_index(args):
    """Manage user index"""
    if args.action == "rebuild":
        if rebuild_user_index():
            print("✅ User index rebuilt successfully")
        else:
            print("❌ Failed to rebuild user index")
    elif args.action == "update":
        if args.user_id == "all":
            user_ids = get_all_user_ids()
            success_count = 0
            for user_id in user_ids:
                if user_id and update_user_index(user_id):
                    success_count += 1
            print(f"Updated index for {success_count}/{len(user_ids)} users")
        else:
            if update_user_index(args.user_id):
                print(f"✅ Updated index for user {args.user_id}")
            else:
                print(f"❌ Failed to update index for user {args.user_id}")

def cmd_list_users(args):
    """List all users with basic info"""
    user_ids = get_all_user_ids()
    print(f"\n👥 Found {len(user_ids)} users:")
    print("=" * 60)
    
    for user_id in user_ids:
        if not user_id:
            continue
        
        # Try to get basic user info
        from core.utils import load_user_info_data
        user_info = load_user_info_data(user_id)
        
        if user_info:
            username = user_info.get("internal_username", "N/A")
            name = user_info.get("preferred_name", "N/A")
            active = "🟢" if user_info.get("active", False) else "🔴"
            print(f"{active} {user_id[:8]}... | {username} | {name}")
        else:
            print(f"❓ {user_id[:8]}... | No profile data")

def main():
    parser = argparse.ArgumentParser(description="User Data Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Update references command
    ref_parser = subparsers.add_parser("update-refs", help="Update message file references")
    ref_parser.add_argument("user_id", help="User ID or 'all' for all users")
    ref_parser.set_defaults(func=cmd_update_references)
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create user data backup")
    backup_parser.add_argument("user_id", help="User ID to backup")
    backup_parser.add_argument("--no-messages", dest="include_messages", action="store_false", 
                              help="Exclude message files from backup")
    backup_parser.set_defaults(func=cmd_backup_user)
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show user data summary")
    summary_parser.add_argument("user_id", help="User ID or 'all' for all users")
    summary_parser.set_defaults(func=cmd_summary)
    
    # Index management command
    index_parser = subparsers.add_parser("index", help="Manage user index")
    index_parser.add_argument("action", choices=["rebuild", "update"], help="Index action")
    index_parser.add_argument("--user-id", default="all", help="User ID for update action")
    index_parser.set_defaults(func=cmd_index)
    
    # List users command
    list_parser = subparsers.add_parser("list", help="List all users")
    list_parser.set_defaults(func=cmd_list_users)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"CLI error: {e}", exc_info=True)

if __name__ == "__main__":
    main() 