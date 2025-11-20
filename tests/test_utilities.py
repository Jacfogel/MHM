#!/usr/bin/env python3
"""
Test Utilities for MHM
Centralized test helper functions to eliminate redundancy across test files
"""

import os
import tempfile
import shutil
import json
import logging
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Do not modify sys.path; rely on package imports

from core.user_management import create_new_user
from core.user_data_handlers import save_user_data
from core.file_operations import ensure_user_directory

# Setup logger for test utilities
logger = logging.getLogger(__name__)


class TestUserFactory:
    """Factory for creating test users with different configurations"""
    
    # Cache for pre-created user data structures to avoid recreating identical data
    _user_data_cache: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def _get_cache_key(enable_checkins: bool = None, enable_tasks: bool = None, user_type: str = "basic", **kwargs) -> str:
        """Generate a cache key for user data structures (configuration only, not user_id)."""
        # For user types with fixed configurations, use just the type
        if user_type in ("minimal", "full", "discord", "email", "health", "task", "complex_checkins", "disability", "limited_data", "inconsistent"):
            return f"{user_type}"
        # For basic users, include checkins and tasks in the key
        return f"{user_type}:checkins={enable_checkins}:tasks={enable_tasks}"
    
    @staticmethod
    def _get_cached_user_data(cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached user data structure if available."""
        return TestUserFactory._user_data_cache.get(cache_key)
    
    @staticmethod
    def _cache_user_data(cache_key: str, user_data: Dict[str, Any]):
        """Cache a user data structure for reuse."""
        # Use deepcopy to ensure the cached template is independent
        TestUserFactory._user_data_cache[cache_key] = copy.deepcopy(user_data)
    
    @staticmethod
    def clear_cache():
        """Clear the user data cache (useful for test cleanup)."""
        TestUserFactory._user_data_cache.clear()
    
    @staticmethod
    def create_basic_user(user_id: str, enable_checkins: bool = True, enable_tasks: bool = True, test_data_dir: str = None) -> bool:
        """
        Create a test user with basic functionality enabled
        
        Args:
            user_id: Unique identifier for the test user
            enable_checkins: Whether to enable check-ins for this user
            enable_tasks: Whether to enable task management for this user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # test_data_dir is now required - all tests should use the modern approach
            if not test_data_dir:
                raise ValueError("test_data_dir parameter is required - use modern test approach")
            return TestUserFactory.create_basic_user__with_test_dir(user_id, enable_checkins, enable_tasks, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating basic user {user_id}: {e}")
            return False
    
    @staticmethod
    def _create_user_files_directly__directory_structure(test_data_dir: str, user_id: str) -> tuple[str, str]:
        """Create the user directory structure and return paths."""
        # Create test users directory
        test_users_dir = os.path.join(test_data_dir, "users")
        os.makedirs(test_users_dir, exist_ok=True)
        
        # Generate UUID for the user
        import uuid
        actual_user_id = str(uuid.uuid4())
        
        # Create user directory
        user_dir = os.path.join(test_users_dir, actual_user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        return actual_user_id, user_dir
    
    @staticmethod
    def _create_user_files_directly__account_data(actual_user_id: str, user_id: str, user_data: dict) -> dict:
        """Create account data structure."""
        return {
            "user_id": actual_user_id,
            "internal_username": user_id,
            "account_status": "active",
            "chat_id": user_data.get('chat_id', ''),
            "phone": user_data.get('phone', ''),
            "email": user_data.get('email', ''),
            "discord_user_id": user_data.get('discord_user_id', ''),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "features": {
                "automated_messages": "enabled" if user_data.get('categories') else "disabled",
                "checkins": "enabled" if user_data.get('checkin_settings', {}).get('enabled', False) else "disabled",
                "task_management": "enabled" if user_data.get('task_settings', {}).get('enabled', False) else "disabled"
            },
            "timezone": user_data.get("timezone", "")
        }
    
    @staticmethod
    def _create_user_files_directly__preferences_data(user_data: dict) -> dict:
        """Create preferences data structure."""
        preferences_data = {
            "categories": user_data.get('categories', []),
            "channel": {
                "type": user_data.get('channel', {}).get('type', 'email')
            },
            "checkin_settings": user_data.get('checkin_settings', {}),
            "task_settings": user_data.get('task_settings', {})
        }
        
        # Remove redundant enabled flags from preferences since they're in account.json features
        if 'checkin_settings' in preferences_data and 'enabled' in preferences_data['checkin_settings']:
            del preferences_data['checkin_settings']['enabled']
        if 'task_settings' in preferences_data and 'enabled' in preferences_data['task_settings']:
            del preferences_data['task_settings']['enabled']
        
        return preferences_data
    
    @staticmethod
    def _create_user_files_directly__context_data(user_data: dict) -> dict:
        """Create user context data structure."""
        return {
            "preferred_name": user_data.get('preferred_name', ''),
            "gender_identity": user_data.get('gender_identity', []),
            "date_of_birth": user_data.get('date_of_birth', ''),
            "custom_fields": {
                "reminders_needed": user_data.get('reminders_needed', []),
                "health_conditions": user_data.get('custom_fields', {}).get('health_conditions', []),
                "medications_treatments": user_data.get('custom_fields', {}).get('medications_treatments', []),
                "allergies_sensitivities": user_data.get('custom_fields', {}).get('allergies_sensitivities', [])
            },
            "interests": user_data.get('interests', []),
            "goals": user_data.get('goals', []),
            "loved_ones": user_data.get('loved_ones', []),
            "activities_for_encouragement": user_data.get('activities_for_encouragement', []),
            "notes_for_ai": user_data.get('notes_for_ai', []),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _create_user_files_directly__save_json(file_path: str, data: dict):
        """Save data to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _create_user_files_directly__schedules_data(categories: list) -> dict:
        """Create default schedule periods for categories."""
        if not categories:
            return {}
        
        schedules_data = {}
        for category in categories:
            schedules_data[category] = {
                "periods": {
                    "Morning": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    },
                    "Afternoon": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "13:00",
                        "end_time": "17:00"
                    },
                    "Evening": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "21:00"
                    }
                }
            }
        return schedules_data
    
    @staticmethod
    def _create_user_files_directly__message_files(user_dir: str, categories: list):
        """Create message directory and default message files."""
        # Ensure user directory exists before creating messages subdirectory (race condition fix)
        os.makedirs(user_dir, exist_ok=True)
        messages_dir = os.path.join(user_dir, "messages")
        os.makedirs(messages_dir, exist_ok=True)
        
        for category in categories:
            category_file = os.path.join(messages_dir, f"{category}.json")
            if not os.path.exists(category_file):
                # Ensure parent directory exists before writing (race condition fix)
                os.makedirs(os.path.dirname(category_file), exist_ok=True)
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
        
        # Create sent_messages.json
        sent_messages_file = os.path.join(messages_dir, "sent_messages.json")
        if not os.path.exists(sent_messages_file):
            # Ensure parent directory exists before writing (race condition fix)
            os.makedirs(os.path.dirname(sent_messages_file), exist_ok=True)
            with open(sent_messages_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def create_basic_user__update_index(test_data_dir: str, user_id: str, actual_user_id: str):
        """Update user index to map internal_username to UUID.
        
        Uses file locking to prevent race conditions in parallel test execution.
        """
        from core.file_locking import safe_json_read, safe_json_write
        
        user_index_file = os.path.join(test_data_dir, "user_index.json")
        
        # Read existing index with file locking
        user_index = safe_json_read(user_index_file, default={})
        
        # Add the new user to the index
        user_index[user_id] = actual_user_id
        
        # Save the updated index with file locking
        safe_json_write(user_index_file, user_index, indent=2)
    
    @staticmethod
    def _create_user_files_directly(user_id: str, user_data: Dict[str, Any], test_data_dir: str) -> str:
        """Helper function to create user files directly in test directory"""
        # Create user directory structure
        actual_user_id, user_dir = TestUserFactory._create_user_files_directly__directory_structure(test_data_dir, user_id)
        
        # Create data structures
        account_data = TestUserFactory._create_user_files_directly__account_data(actual_user_id, user_id, user_data)
        preferences_data = TestUserFactory._create_user_files_directly__preferences_data(user_data)
        context_data = TestUserFactory._create_user_files_directly__context_data(user_data)
        
        # Save main files
        account_file = os.path.join(user_dir, "account.json")
        preferences_file = os.path.join(user_dir, "preferences.json")
        context_file = os.path.join(user_dir, "user_context.json")
        
        TestUserFactory._create_user_files_directly__save_json(account_file, account_data)
        TestUserFactory._create_user_files_directly__save_json(preferences_file, preferences_data)
        TestUserFactory._create_user_files_directly__save_json(context_file, context_data)
        
        # Create schedules if categories exist
        categories = user_data.get('categories', [])
        if categories:
            schedules_data = TestUserFactory._create_user_files_directly__schedules_data(categories)
            schedules_file = os.path.join(user_dir, "schedules.json")
            TestUserFactory._create_user_files_directly__save_json(schedules_file, schedules_data)
        
        # Create message files
        TestUserFactory._create_user_files_directly__message_files(user_dir, categories)
        
        # Update user index
        TestUserFactory.create_basic_user__update_index(test_data_dir, user_id, actual_user_id)
        
        return actual_user_id
    
    @staticmethod
    def create_basic_user__with_test_dir(user_id: str, enable_checkins: bool = True, enable_tasks: bool = True, test_data_dir: str = None) -> bool:
        """Create basic user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            # Cache key excludes user_id to allow reuse across tests with same configuration
            cache_key = TestUserFactory._get_cache_key(enable_checkins, enable_tasks, "basic")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # AND ensure checkin/task settings match current parameters (for correctness)
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Test User {user_id}"
                # Ensure checkin and task settings match current parameters
                user_data["checkin_settings"]["enabled"] = enable_checkins
                user_data["task_settings"]["enabled"] = enable_tasks
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "",
                    "email": f"{user_id}@example.com",
                    "discord_user_id": "",
                    "timezone": "UTC",
                    "categories": ["motivational", "health"],
                    "channel": {
                        "type": "discord"
                    },
                    "checkin_settings": {
                        "enabled": enable_checkins,
                        "frequency": "daily",
                        "reminder_time": "09:00"
                    },
                    "task_settings": {
                        "enabled": enable_tasks,
                        "default_priority": "medium",
                        "reminder_enabled": True
                    },
                    "preferred_name": f"Test User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "",
                    "reminders_needed": [],
                    "custom_fields": {
                        "health_conditions": [],
                        "medications_treatments": [],
                        "allergies_sensitivities": []
                    },
                    "interests": ["Technology", "Gaming"],
                    "goals": ["Improve mental health", "Stay organized"],
                    "loved_ones": [],
                    "activities_for_encouragement": [],
                    "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating basic user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_minimal_user(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a minimal test user with only essential data structures.
        Use this for tests that don't need full user data (faster than create_basic_user).
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (required)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            if not test_data_dir:
                raise ValueError("test_data_dir parameter is required")
            
            # Create minimal user data - only essential fields
            user_data = {
                "internal_username": user_id,
                "email": f"{user_id}@example.com",
                "timezone": "UTC",
                "categories": [],  # No categories for minimal user
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": False
                },
                "task_settings": {
                    "enabled": False
                },
                "preferred_name": f"Minimal User {user_id}"
            }
            
            # Use helper function to create files (will skip schedules and messages since no categories)
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating minimal user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_discord_user(user_id: str, discord_user_id: str = None, test_data_dir: str = None) -> bool:
        """
        Create a test user specifically configured for Discord testing
        
        Args:
            user_id: Unique identifier for the test user
            discord_user_id: Discord user ID (defaults to user_id if not provided)
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # test_data_dir is now required - all tests should use the modern approach
            if not test_data_dir:
                raise ValueError("test_data_dir parameter is required - use modern test approach")
            return TestUserFactory.create_discord_user__with_test_dir(user_id, discord_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating discord user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_discord_user__with_test_dir(user_id: str, discord_user_id: str = None, test_data_dir: str = None) -> bool:
        """Create discord user with test directory by directly saving files"""
        try:
            if discord_user_id is None:
                discord_user_id = user_id
            
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="discord")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["discord_user_id"] = discord_user_id
                user_data["preferred_name"] = f"Discord User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "",
                    "email": f"{user_id}@example.com",
                    "discord_user_id": discord_user_id,
                    "timezone": "UTC",
                    "categories": ["motivational", "health"],
                    "channel": {
                        "type": "discord"
                    },
                    "checkin_settings": {
                        "enabled": True,
                        "frequency": "daily",
                        "reminder_time": "09:00"
                    },
                    "task_settings": {
                        "enabled": True,
                        "default_priority": "medium",
                        "reminder_enabled": True
                    },
                    "preferred_name": f"Discord User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "",
                    "reminders_needed": [],
                    "custom_fields": {
                        "health_conditions": [],
                        "medications_treatments": [],
                        "allergies_sensitivities": []
                    },
                    "interests": ["Technology", "Gaming"],
                    "goals": ["Improve mental health", "Stay organized"],
                    "loved_ones": [],
                    "activities_for_encouragement": [],
                    "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating discord user with test dir {user_id}: {e}")
            return False
    

            

    
    @staticmethod
    def create_full_featured_user(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with all features enabled and comprehensive data
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_full_featured_user__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_full_featured_user__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating full featured user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_full_featured_user__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create full featured user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="full")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Full Featured User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "",
                    "email": f"{user_id}@example.com",
                    "discord_user_id": "",
                    "timezone": "America/New_York",
                    "categories": ["motivational", "health", "fun_facts", "quotes_to_ponder", "word_of_the_day"],
                    "channel": {
                        "type": "discord"
                    },
                    "checkin_settings": {
                        "enabled": True,
                        "frequency": "daily",
                        "reminder_time": "09:00",
                        "custom_questions": ["How are you feeling?", "Did you eat today?", "Did you take your medication?"]
                    },
                    "task_settings": {
                        "enabled": True,
                        "default_priority": "high",
                        "reminder_enabled": True,
                        "auto_escalation": True
                    },
                    "preferred_name": f"Full Featured User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "1990-01-01",
                    "reminders_needed": ["medication", "appointments", "exercise"],
                    "custom_fields": {
                        "health_conditions": ["ADHD", "Depression"],
                        "medications_treatments": ["Adderall", "Therapy"],
                        "allergies_sensitivities": ["Peanuts"]
                    },
                    "interests": ["Technology", "Gaming", "Reading", "Cooking"],
                    "goals": ["Improve mental health", "Stay organized", "Build better habits"],
                    "loved_ones": ["Family", "Friends"],
                    "activities_for_encouragement": ["Exercise", "Socializing", "Creative projects"],
                    "notes_for_ai": ["Prefers gentle encouragement", "Responds well to humor"]
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Update user index to map internal_username to UUID (critical for UUID resolution)
            TestUserFactory.create_basic_user__update_index(test_data_dir, user_id, actual_user_id)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating full featured user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_full_featured_user__impl(user_id: str) -> bool:
        """Internal implementation of full featured user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "America/New_York",
                "categories": ["motivational", "health", "fun_facts", "quotes_to_ponder", "word_of_the_day"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00",
                    "custom_questions": ["How are you feeling?", "Did you eat today?", "Did you take your medication?"]
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True,
                    "auto_escalation": True
                },
                "preferred_name": f"Full Featured User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "1990-01-01",
                "reminders_needed": ["medication", "appointments", "exercise"],
                "custom_fields": {
                    "health_conditions": ["ADHD", "Depression"],
                    "medications_treatments": ["Adderall", "Therapy"],
                    "allergies_sensitivities": ["Peanuts"]
                },
                "interests": ["Technology", "Gaming", "Reading", "Cooking"],
                "goals": ["Improve mental health", "Stay organized", "Build better habits"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Socializing", "Creative projects"],
                "notes_for_ai": ["Prefers gentle encouragement", "Responds well to humor"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating full featured user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_email_user(user_id: str, email: str = None, test_data_dir: str = None) -> str:
        """
        Create a test user specifically configured for email testing
        
        Args:
            user_id: Unique identifier for the test user
            email: Email address (defaults to user_id@example.com if not provided)
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            str: User ID if user was created successfully, None otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_email_user__with_test_dir(user_id, email, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_email_user__impl(user_id, email)
            
        except Exception as e:
            logger.error(f"Error creating email user {user_id}: {e}")
            return None
    
    @staticmethod
    def create_email_user__with_test_dir(user_id: str, email: str = None, test_data_dir: str = None) -> str:
        """Create email user with test directory by directly saving files"""
        try:
            if email is None:
                email = f"{user_id}@example.com"
            
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="email")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = email
                user_data["preferred_name"] = f"Email User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "",
                    "email": email,
                    "discord_user_id": "",
                    "timezone": "UTC",
                    "categories": ["motivational", "health"],
                    "channel": {
                        "type": "email"
                    },
                    "checkin_settings": {
                        "enabled": True,
                        "frequency": "daily",
                        "reminder_time": "09:00"
                    },
                    "task_settings": {
                        "enabled": True,
                        "default_priority": "medium",
                        "reminder_enabled": True
                    },
                    "preferred_name": f"Email User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "",
                    "reminders_needed": [],
                    "custom_fields": {
                        "health_conditions": [],
                        "medications_treatments": [],
                        "allergies_sensitivities": []
                    },
                    "interests": ["Technology", "Reading"],
                    "goals": ["Improve mental health", "Stay organized"],
                    "loved_ones": [],
                    "activities_for_encouragement": [],
                    "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.verify_email_user_creation__with_test_dir(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating email user with test dir {user_id}: {e}")
            return None
    
    @staticmethod
    def create_email_user__impl(user_id: str, email: str = None) -> str:
        """Internal implementation of email user creation"""
        try:
            if email is None:
                email = f"{user_id}@example.com"
            
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": email,
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Email User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Reading"],
                "goals": ["Improve mental health", "Stay organized"],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            return actual_user_id
            
        except Exception as e:
            logger.error(f"Error creating email user {user_id}: {e}")
            return None
    
    @staticmethod
    def create_user_with_custom_fields(user_id: str, custom_fields: Dict[str, Any] = None, test_data_dir: str = None) -> bool:
        """
        Create a test user with custom fields for testing custom field functionality
        
        Args:
            user_id: Unique identifier for the test user
            custom_fields: Dictionary of custom fields to add to user context
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, temporarily patch the config to use it
            if test_data_dir:
                from unittest.mock import patch
                import core.config
                
                # Create test users directory
                test_users_dir = os.path.join(test_data_dir, "users")
                os.makedirs(test_users_dir, exist_ok=True)
                
                # Temporarily patch the config to use test directory
                with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
                     patch.object(core.config, "USER_INFO_DIR_PATH", test_users_dir):
                    return TestUserFactory.create_user_with_custom_fields__impl(user_id, custom_fields)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_custom_fields__impl(user_id, custom_fields)
            
        except Exception as e:
            logger.error(f"Error creating custom fields test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_custom_fields__impl(user_id: str, custom_fields: Dict[str, Any] = None) -> bool:
        """Internal implementation of custom fields user creation"""
        try:
            if custom_fields is None:
                custom_fields = {
                    "health_conditions": ["ADHD", "Depression"],
                    "medications_treatments": ["Medication A", "Therapy"],
                    "reminders_needed": ["Take medication", "Exercise"]
                }
            
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Test User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": custom_fields.get("reminders_needed", []),
                "custom_fields": {
                    "health_conditions": custom_fields.get("health_conditions", []),
                    "medications_treatments": custom_fields.get("medications_treatments", []),
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Gaming"],
                "goals": ["Improve executive functioning", "Stay organized"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Reading"],
                "notes_for_ai": ["Prefers gentle reminders", "Responds well to encouragement"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if not actual_user_id:
                logger.error(f"create_new_user returned None for user {user_id}")
                return False
            
            # Ensure user index is updated (race condition fix for parallel execution)
            from core.user_data_manager import update_user_index
            import time
            max_retries = 3
            for attempt in range(max_retries):
                success = update_user_index(actual_user_id)
                if success:
                    break
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # Brief delay before retry
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom fields test user {user_id}: {e}")
            return False
    

    
    @staticmethod
    def create_user_with_schedules(user_id: str, schedule_config: Dict[str, Any] = None, test_data_dir: str = None) -> bool:
        """
        Create a test user with comprehensive schedule configuration
        
        Args:
            user_id: Unique identifier for the test user
            schedule_config: Custom schedule configuration
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, temporarily patch the config to use it
            if test_data_dir:
                from unittest.mock import patch
                import core.config
                
                # Create test users directory
                test_users_dir = os.path.join(test_data_dir, "users")
                os.makedirs(test_users_dir, exist_ok=True)
                
                # Temporarily patch the config to use test directory
                with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
                     patch.object(core.config, "USER_INFO_DIR_PATH", test_users_dir):
                    return TestUserFactory.create_user_with_schedules__impl(user_id, schedule_config)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_schedules__impl(user_id, schedule_config)
            
        except Exception as e:
            logger.error(f"Error creating schedules test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_schedules__impl(user_id: str, schedule_config: Dict[str, Any] = None) -> bool:
        """Internal implementation of schedules user creation"""
        try:
            if schedule_config is None:
                schedule_config = {
                    "motivational": {
                        "periods": {
                            "Default": {
                                "active": True,
                                "days": ["ALL"],
                                "start_time": "18:00",
                                "end_time": "21:30"
                            }
                        }
                    },
                    "health": {
                        "periods": {
                            "Default": {
                                "active": True,
                                "days": ["ALL"],
                                "start_time": "18:00",
                                "end_time": "20:00"
                            }
                        }
                    }
                }
            
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Test User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Gaming"],
                "goals": ["Improve mental health", "Stay organized"],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if not actual_user_id:
                logger.error(f"create_new_user returned None for user {user_id}")
                return False
            
            # Ensure user directory exists before proceeding
            from core.config import get_user_data_dir
            import os
            user_dir = get_user_data_dir(actual_user_id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir, exist_ok=True)
                import time
                time.sleep(0.1)  # Brief delay to ensure directory is created
            
            # Ensure user index is updated (race condition fix for parallel execution)
            from core.user_data_manager import update_user_index
            import time
            max_retries = 3
            for attempt in range(max_retries):
                success = update_user_index(actual_user_id)
                if success:
                    break
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # Brief delay before retry
            
            # Ensure user account and preferences files are fully written before saving schedules
            # This is important for cross-file invariants that might validate schedules
            # Schedule validation may require preferences with categories to exist
            time.sleep(0.2)  # Brief delay to ensure account file is flushed
            
            # Ensure preferences with categories exist (required for schedule validation)
            # Schedule validation may require that schedule categories match preference categories
            from core.user_data_handlers import get_user_data, save_user_data
            categories = user_data.get('categories', ['motivational', 'health'])
            
            # Always save preferences first to ensure they exist for validation
            # create_new_user should have created preferences, but ensure they exist with categories
            pref_result = save_user_data(actual_user_id, {
                'preferences': {
                    'categories': categories,
                    'channel': user_data.get('channel', {'type': 'discord'})
                }
            }, auto_create=True)
            
            if not pref_result.get('preferences', False):
                logger.warning(f"Failed to save preferences for user {user_id} before schedules. Result: {pref_result}")
                # Try once more with a delay
                import time
                time.sleep(0.2)
                pref_result = save_user_data(actual_user_id, {
                    'preferences': {
                        'categories': categories,
                        'channel': user_data.get('channel', {'type': 'discord'})
                    }
                }, auto_create=True)
                if not pref_result.get('preferences', False):
                    logger.error(f"Failed to save preferences for user {user_id} after retry. Result: {pref_result}")
                    return False
            
            # Verify preferences were saved - retry with longer delays
            prefs_data = {}
            for attempt in range(5):
                prefs_data = get_user_data(actual_user_id, 'preferences', auto_create=True)
                if prefs_data and 'preferences' in prefs_data and prefs_data.get('preferences', {}).get('categories'):
                    break
                if attempt < 4:
                    time.sleep(0.2)  # Longer delay for file system operations
            
            if not prefs_data or 'preferences' not in prefs_data or not prefs_data.get('preferences', {}).get('categories'):
                # Check if preferences file exists
                from core.config import get_user_file_path
                import os
                prefs_file = get_user_file_path(actual_user_id, 'preferences')
                file_exists = os.path.exists(prefs_file) if prefs_file else False
                logger.warning(f"Preferences with categories not found for user {user_id} after save. Got: {prefs_data}, File exists: {file_exists}, File path: {prefs_file}")
                # If file exists but data isn't loading, try reading directly
                if file_exists:
                    try:
                        from core.file_operations import load_json_data
                        direct_data = load_json_data(prefs_file)
                        logger.debug(f"Direct file read: {direct_data}")
                    except Exception as e:
                        logger.debug(f"Error reading preferences file directly: {e}")
                return False
            
            time.sleep(0.2)  # Brief delay to ensure preferences are flushed
            
            # Ensure schedule categories match preference categories (required for validation)
            # Extract categories from schedule_config
            schedule_categories = list(schedule_config.keys()) if schedule_config else []
            pref_categories = prefs_data.get('preferences', {}).get('categories', [])
            
            # If schedule has categories not in preferences, add them
            # Also ensure we use the categories from schedule_config if provided, otherwise use user_data categories
            if schedule_categories:
                # Use schedule categories as the source of truth
                final_categories = list(set(pref_categories + schedule_categories))
            else:
                # Use user_data categories
                final_categories = categories
            
            if set(schedule_categories) != set(pref_categories):
                updated_prefs = prefs_data.get('preferences', {}).copy()
                updated_prefs['categories'] = final_categories
                pref_result = save_user_data(actual_user_id, {'preferences': updated_prefs}, auto_create=True)
                if not pref_result.get('preferences', False):
                    logger.warning(f"Failed to update preferences with schedule categories for user {user_id}")
                else:
                    # Verify update
                    for verify_attempt in range(3):
                        prefs_data = get_user_data(actual_user_id, 'preferences', auto_create=True)
                        if prefs_data and 'preferences' in prefs_data:
                            updated_pref_categories = prefs_data.get('preferences', {}).get('categories', [])
                            if set(schedule_categories).issubset(set(updated_pref_categories)):
                                break
                        if verify_attempt < 2:
                            time.sleep(0.1)
                time.sleep(0.2)  # Brief delay to ensure preferences are flushed
            
            # Add schedule data using the correct function
            # Retry in case of race conditions with file writes in parallel execution
            schedule_success = False
            last_result = {}
            for attempt in range(5):
                result = save_user_data(actual_user_id, {'schedules': schedule_config}, auto_create=True, validate_data=True)
                last_result = result
                schedule_success = result.get('schedules', False)
                if schedule_success:
                    break
                if attempt < 4:
                    time.sleep(0.2)  # Increased delay before retry
            
            if not schedule_success:
                # Try with validate_data=False as a last resort (for test purposes)
                logger.warning(f"Failed to save schedule data for user {user_id} after 5 attempts with validation. Result: {last_result}. Trying without validation.")
                result_no_validate = save_user_data(actual_user_id, {'schedules': schedule_config}, auto_create=True, validate_data=False)
                schedule_success = result_no_validate.get('schedules', False)
                if schedule_success:
                    logger.info(f"Schedule save succeeded without validation for user {user_id}")
                else:
                    logger.warning(f"Failed to save schedule data for user {user_id} even without validation. Result: {result_no_validate}")
            
            return schedule_success
        except Exception as e:
            logger.error(f"Error creating scheduled test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_minimal_user(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a minimal test user with only basic messaging enabled
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_minimal_user__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_minimal_user__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating minimal user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_minimal_user_and_get_id(user_id: str, test_data_dir: str = None) -> tuple[bool, str]:
        """
        Create a minimal test user and return the actual UUID
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            tuple[bool, str]: (success, actual_user_id) where actual_user_id is the UUID
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_minimal_user__with_test_dir_and_get_id(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                actual_user_id = TestUserFactory.create_minimal_user__impl_and_get_id(user_id)
                return (actual_user_id is not None, actual_user_id)
            
        except Exception as e:
            logger.error(f"Error creating minimal user {user_id}: {e}")
            return (False, None)
    
    @staticmethod
    def create_minimal_user__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create minimal user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="minimal")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Minimal User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "",
                    "email": f"{user_id}@example.com",
                    "discord_user_id": "",
                    "timezone": "UTC",
                    "categories": ["motivational"],
                    "channel": {
                        "type": "email"
                    },
                    "checkin_settings": {
                        "enabled": False,
                        "frequency": "daily",
                        "reminder_time": "09:00"
                    },
                    "task_settings": {
                        "enabled": False,
                        "default_priority": "medium",
                        "reminder_enabled": True
                    },
                    "preferred_name": f"Minimal User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "",
                    "reminders_needed": [],
                    "custom_fields": {
                        "health_conditions": [],
                        "medications_treatments": [],
                        "allergies_sensitivities": []
                    },
                    "interests": [],
                    "goals": [],
                    "loved_ones": [],
                    "activities_for_encouragement": [],
                    "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating minimal user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_minimal_user__with_test_dir_and_get_id(user_id: str, test_data_dir: str = None) -> tuple[bool, str]:
        """Create minimal user with test directory and return the actual UUID"""
        try:
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Minimal User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            
            # Verify user creation with proper configuration patching
            success = TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            return (success, actual_user_id)
            
        except Exception as e:
            logger.error(f"Error creating minimal user with test dir {user_id}: {e}")
            return (False, None)
    
    @staticmethod
    def create_minimal_user__impl(user_id: str) -> bool:
        """Internal implementation of minimal user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Minimal User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating minimal user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_complex_checkins(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with complex check-in configurations
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_complex_checkins__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_complex_checkins__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating complex checkins user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_complex_checkins__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create complex checkins user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="complex_checkins")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Complex Checkins User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00",
                    "custom_questions": ["How are you feeling?", "Did you eat today?", "Did you take your medication?", "How did you sleep?", "Did you exercise?"]
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Complex Checkins User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["medication", "meals", "sleep"],
                "custom_fields": {
                    "health_conditions": ["Depression", "Anxiety"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": []
                },
                "interests": ["Health", "Wellness", "Self-care"],
                "goals": ["Improve mental health", "Build healthy habits", "Track progress"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Socializing", "Creative projects"],
                "notes_for_ai": ["Prefers detailed check-ins", "Health-focused approach"]
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating complex checkins user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_complex_checkins__impl(user_id: str) -> bool:
        """Internal implementation of complex checkins user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00",
                    "custom_questions": ["How are you feeling?", "Did you eat today?", "Did you take your medication?", "How did you sleep?", "Did you exercise?"]
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Complex Checkins User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["medication", "meals", "sleep"],
                "custom_fields": {
                    "health_conditions": ["Depression", "Anxiety"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": []
                },
                "interests": ["Health", "Wellness", "Self-care"],
                "goals": ["Improve mental health", "Build healthy habits", "Track progress"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Socializing", "Creative projects"],
                "notes_for_ai": ["Prefers detailed check-ins", "Health-focused approach"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating complex checkins user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_health_focus(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with health-focused features and data
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_health_focus__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_health_focus__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating health focus user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_health_focus__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create health focus user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="health")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Health Focus User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["health", "motivational"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00",
                    "custom_questions": ["How are you feeling today?", "Did you take your medication?", "How did you sleep?"]
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True
                },
                "preferred_name": f"Health Focus User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "1990-01-01",
                "reminders_needed": ["medication", "appointments", "exercise", "sleep"],
                "custom_fields": {
                    "health_conditions": ["Anxiety", "Depression"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": ["Pollen"]
                },
                "interests": ["Health", "Exercise", "Meditation"],
                "goals": ["Improve mental health", "Build healthy habits", "Manage stress"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Meditation", "Socializing"],
                "notes_for_ai": ["Prefers gentle encouragement", "Health-focused approach"]
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating health focus user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_health_focus__impl(user_id: str) -> bool:
        """Internal implementation of health focus user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["health", "motivational"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00",
                    "custom_questions": ["How are you feeling today?", "Did you take your medication?", "How did you sleep?"]
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True
                },
                "preferred_name": f"Health Focus User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "1990-01-01",
                "reminders_needed": ["medication", "appointments", "exercise", "sleep"],
                "custom_fields": {
                    "health_conditions": ["Anxiety", "Depression"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": ["Pollen"]
                },
                "interests": ["Health", "Exercise", "Meditation"],
                "goals": ["Improve mental health", "Build healthy habits", "Manage stress"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Exercise", "Meditation", "Socializing"],
                "notes_for_ai": ["Prefers gentle encouragement", "Health-focused approach"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating health focus user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_task_focus(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with task management focus
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_task_focus__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_task_focus__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating task focus user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_task_focus__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create task focus user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="task")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Task Focus User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True,
                    "auto_escalation": True
                },
                "preferred_name": f"Task Focus User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["deadlines", "meetings", "follow-ups"],
                "custom_fields": {
                    "health_conditions": ["ADHD"],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Productivity", "Organization", "Technology"],
                "goals": ["Improve productivity", "Stay organized", "Meet deadlines"],
                "loved_ones": [],
                "activities_for_encouragement": ["Planning", "Organization", "Time management"],
                "notes_for_ai": ["Task-focused approach", "Prefers clear deadlines"]
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating task focus user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_task_focus__impl(user_id: str) -> bool:
        """Internal implementation of task focus user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True,
                    "auto_escalation": True
                },
                "preferred_name": f"Task Focus User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["deadlines", "meetings", "follow-ups"],
                "custom_fields": {
                    "health_conditions": ["ADHD"],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Productivity", "Organization", "Technology"],
                "goals": ["Improve productivity", "Stay organized", "Meet deadlines"],
                "loved_ones": [],
                "activities_for_encouragement": ["Planning", "Organization", "Time management"],
                "notes_for_ai": ["Task-focused approach", "Prefers clear deadlines"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating task focus user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_disabilities(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with disability-focused features and data
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_disabilities__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_disabilities__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating disability user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_disabilities__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create disability user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="disability")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["email"] = f"{user_id}@example.com"
                user_data["preferred_name"] = f"Disability User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Disability User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["medication", "appointments", "accessibility"],
                "custom_fields": {
                    "health_conditions": ["ADHD", "Autism"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Gaming", "Art"],
                "goals": ["Improve executive functioning", "Build routines", "Stay organized"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Creative projects", "Socializing", "Exercise"],
                "notes_for_ai": ["Prefers clear instructions", "Needs routine reminders"]
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating disability user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_disabilities__impl(user_id: str) -> bool:
        """Internal implementation of disability user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational", "health"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Disability User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["medication", "appointments", "accessibility"],
                "custom_fields": {
                    "health_conditions": ["ADHD", "Autism"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Gaming", "Art"],
                "goals": ["Improve executive functioning", "Build routines", "Stay organized"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Creative projects", "Socializing", "Exercise"],
                "notes_for_ai": ["Prefers clear instructions", "Needs routine reminders"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating disability user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_limited_data(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with minimal data for testing edge cases
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_limited_data__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_limited_data__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating limited data user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_limited_data__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create limited data user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="limited_data")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                # Limited data users should have empty preferred_name (not a generated name)
                user_data["preferred_name"] = ""
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": "",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": "",
                "gender_identity": [],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating limited data user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_limited_data__impl(user_id: str) -> bool:
        """Internal implementation of limited data user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "",
                "email": "",
                "discord_user_id": "",
                "timezone": "UTC",
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "enabled": False,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": "",
                "gender_identity": [],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating limited data user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_inconsistent_data(user_id: str, test_data_dir: str = None) -> bool:
        """
        Create a test user with inconsistent data for testing edge cases
        
        Args:
            user_id: Unique identifier for the test user
            test_data_dir: Test data directory to use (if None, uses real user directory)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # If test_data_dir is provided, use direct file creation
            if test_data_dir:
                return TestUserFactory.create_user_with_inconsistent_data__with_test_dir(user_id, test_data_dir)
            else:
                # Use real user directory (for backward compatibility)
                return TestUserFactory.create_user_with_inconsistent_data__impl(user_id)
            
        except Exception as e:
            logger.error(f"Error creating inconsistent data user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_inconsistent_data__with_test_dir(user_id: str, test_data_dir: str = None) -> bool:
        """Create inconsistent data user with test directory by directly saving files"""
        try:
            # Check cache first to avoid recreating identical user data structures
            cache_key = TestUserFactory._get_cache_key(user_type="inconsistent")
            cached_data = TestUserFactory._get_cached_user_data(cache_key)
            
            if cached_data:
                # Use cached data structure but update user_id-specific fields
                # Use deepcopy to avoid modifying the cached template
                user_data = copy.deepcopy(cached_data)
                user_data["internal_username"] = user_id
                user_data["preferred_name"] = f"Inconsistent User {user_id}"
            else:
                # Create user data in the format expected by create_new_user
                user_data = {
                    "internal_username": user_id,
                    "chat_id": "",
                    "phone": "3062619228",
                    "email": "",
                    "discord_user_id": "",
                    "timezone": "America/Regina",
                    "categories": ["motivational"],
                    "channel": {
                        "type": "discord"
                    },
                    "checkin_settings": {
                        "enabled": True,
                        "frequency": "daily",
                        "reminder_time": "09:00"
                    },
                    "task_settings": {
                        "enabled": True,
                        "default_priority": "medium",
                        "reminder_enabled": True
                    },
                    "preferred_name": f"Inconsistent User {user_id}",
                    "gender_identity": ["they/them"],
                    "date_of_birth": "",
                    "reminders_needed": [],
                    "custom_fields": {
                        "health_conditions": [],
                        "medications_treatments": [],
                        "allergies_sensitivities": []
                    },
                    "interests": ["Technology"],
                    "goals": ["Stay organized"],
                    "loved_ones": [],
                    "activities_for_encouragement": [],
                    "notes_for_ai": []
                }
                # Cache the template (without user_id-specific fields) for reuse
                template_data = user_data.copy()
                TestUserFactory._cache_user_data(cache_key, template_data)
            
            # Use helper function to create files
            actual_user_id = TestUserFactory._create_user_files_directly(user_id, user_data, test_data_dir)
            # Verify user creation with proper configuration patching
            return TestUserFactory.create_basic_user__verify_creation(user_id, actual_user_id, test_data_dir)
            
        except Exception as e:
            logger.error(f"Error creating inconsistent data user with test dir {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_inconsistent_data__impl(user_id: str) -> bool:
        """Internal implementation of inconsistent data user creation"""
        try:
            # Use the proper create_new_user function to generate UUID and register user
            from core.user_management import create_new_user
            
            # Create user data in the format expected by create_new_user
            user_data = {
                "internal_username": user_id,
                "chat_id": "",
                "phone": "3062619228",
                "email": "",
                "discord_user_id": "",
                "timezone": "America/Regina",
                "categories": ["motivational"],
                "channel": {
                    "type": "discord"
                },
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "reminder_time": "09:00"
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Inconsistent User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": [],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology"],
                "goals": ["Stay organized"],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": []
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error creating inconsistent data user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_test_user_data(user_id: str, test_data_dir: str) -> Dict[str, Any]:
        """Get user data from test directory"""
        try:
            # First try to find the user by internal username in the user index
            user_index_file = os.path.join(test_data_dir, "user_index.json")
            if os.path.exists(user_index_file):
                with open(user_index_file, 'r', encoding='utf-8') as f:
                    user_index = json.load(f)
                
                if user_id in user_index:
                    actual_user_id = user_index[user_id]
                    user_dir = os.path.join(test_data_dir, "users", actual_user_id)
                    
                    # Load all user data files
                    result = {}
                    
                    # Load account data
                    account_file = os.path.join(user_dir, "account.json")
                    if os.path.exists(account_file):
                        with open(account_file, 'r', encoding='utf-8') as f:
                            result['account'] = json.load(f)
                    
                    # Load preferences data
                    preferences_file = os.path.join(user_dir, "preferences.json")
                    if os.path.exists(preferences_file):
                        with open(preferences_file, 'r', encoding='utf-8') as f:
                            result['preferences'] = json.load(f)
                    
                    # Load context data
                    context_file = os.path.join(user_dir, "user_context.json")
                    if os.path.exists(context_file):
                        with open(context_file, 'r', encoding='utf-8') as f:
                            result['context'] = json.load(f)
                    
                    # Load schedules data
                    schedules_file = os.path.join(user_dir, "schedules.json")
                    if os.path.exists(schedules_file):
                        with open(schedules_file, 'r', encoding='utf-8') as f:
                            result['schedules'] = json.load(f)
                    
                    return result
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting test user data for {user_id}: {e}")
            return {}
    
    @staticmethod
    def get_test_user_id_by_internal_username(internal_username: str, test_data_dir: str) -> Optional[str]:
        """Get user ID by internal username from test directory"""
        try:
            user_index_file = os.path.join(test_data_dir, "user_index.json")
            if os.path.exists(user_index_file):
                # Use safe_json_read to prevent race conditions in parallel execution
                from core.file_locking import safe_json_read
                user_index = safe_json_read(user_index_file, default={})
                
                return user_index.get(internal_username)
            
            # Fallback: scan user directories when index is missing or out-of-date
            users_dir = os.path.join(test_data_dir, "users")
            if os.path.exists(users_dir):
                from core.file_locking import safe_json_read  # reuse helper
                for entry in os.listdir(users_dir):
                    user_dir = os.path.join(users_dir, entry)
                    account_file = os.path.join(user_dir, "account.json")
                    if not os.path.exists(account_file):
                        continue
                    account_data = safe_json_read(account_file, default={})
                    if account_data.get("internal_username") == internal_username:
                        # Update the index so future lookups are fast and consistent
                        TestUserFactory.create_basic_user__update_index(test_data_dir, internal_username, entry)
                        return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting test user ID for {internal_username}: {e}")
            return None
    
    @staticmethod
    def create_basic_user__verify_creation(user_id: str, actual_user_id: str, test_data_dir: str) -> bool:
        """Helper function to verify user creation with proper configuration patching"""
        # CRITICAL FIX: Patch the configuration to use the test data directory
        # This ensures that system functions can find the created users
        from unittest.mock import patch
        import core.config
        
        with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
             patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(test_data_dir, 'users')):
            
            # Verify the user was created successfully by trying to find it
            from core.user_management import get_user_id_by_identifier
            found_user_id = get_user_id_by_identifier(user_id)
            
            if found_user_id:
                return True
            else:
                logger.warning(f"User {user_id} was created but not found by get_user_id_by_identifier")
                return actual_user_id is not None

    @staticmethod
    def verify_email_user_creation__with_test_dir(user_id: str, actual_user_id: str, test_data_dir: str) -> str:
        """Helper function to verify email user creation with proper configuration patching"""
        # CRITICAL FIX: Patch the configuration to use the test data directory
        # This ensures that system functions can find the created users
        from unittest.mock import patch
        import core.config
        
        with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
             patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(test_data_dir, 'users')):
            
            # Verify the user was created successfully by trying to find it
            from core.user_management import get_user_id_by_identifier
            found_user_id = get_user_id_by_identifier(user_id)
            
            if found_user_id:
                return actual_user_id
            else:
                logger.warning(f"Email user {user_id} was created but not found by get_user_id_by_identifier")
                return actual_user_id if actual_user_id else None


class TestDataManager:
    """Manages test data directories and cleanup"""
    
    @staticmethod
    def setup_test_environment() -> tuple:
        """
        Create isolated test environment with temporary directories.
        Optimized: Uses session-scoped base tmp directory (created once).
        
        Returns:
            tuple: (test_dir, test_data_dir, test_test_data_dir)
        """
        # Create temporary test directory
        # Use per-test path under tests/data instead of system temp
        from tests.conftest import tests_data_dir  # reuse base
        import uuid, os
        base_tmp = os.path.join(tests_data_dir, 'tmp')
        # Base tmp directory should already exist from session fixture, but ensure it exists
        os.makedirs(base_tmp, exist_ok=True)
        test_dir = os.path.join(base_tmp, f"mhm_test_{uuid.uuid4().hex}")
        os.makedirs(test_dir, exist_ok=True)
        test_data_dir = os.path.join(test_dir, "data")
        test_test_data_dir = os.path.join(test_dir, "tests", "data")
        
        # Create directory structure (batch creation for efficiency)
        dirs_to_create = [
            test_data_dir,
            test_test_data_dir,
            os.path.join(test_data_dir, "users"),
            os.path.join(test_test_data_dir, "users")
        ]
        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)
        
        # Create test user index with flat lookup structure
        # Use file locking to prevent race conditions in parallel test execution
        from core.file_locking import safe_json_write
        
        user_index = {
            "last_updated": "2025-01-01T00:00:00",
            "test-user-basic": "test-user-basic",  # username → UUID
            "test-user-full": "test-user-full"      # username → UUID
        }
        
        safe_json_write(os.path.join(test_data_dir, "user_index.json"), user_index, indent=2)
        
        return test_dir, test_data_dir, test_test_data_dir
    
    @staticmethod
    def cleanup_test_environment(test_dir: str) -> None:
        """
        Clean up test environment and remove temporary files
        
        Args:
            test_dir: Path to the test directory to clean up
        """
        try:
            if not test_dir:
                return
            # Prefer letting the per-test factory and session cleanup handle removal.
            # As a fallback, remove with ignore_errors to avoid intermittent failures on Windows.
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Could not clean up test directory {test_dir}: {e}")


class TestUserDataFactory:
    """Factory for creating specific test user data structures"""
    
    @staticmethod
    def create_account_data(user_id: str, **overrides) -> Dict[str, Any]:
        """
        Create standard account data structure with optional overrides
        
        Args:
            user_id: User identifier
            **overrides: Optional field overrides
            
        Returns:
            Dict containing account data
        """
        base_data = {
            "user_id": user_id,
            "internal_username": user_id,
            "account_status": "active",
            "name": f"Test User {user_id}",
            "pronouns": "they/them",
            "timezone": "UTC",
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2025-01-01 00:00:00"
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_preferences_data(user_id: str, **overrides) -> Dict[str, Any]:
        """
        Create standard preferences data structure with optional overrides
        
        Args:
            user_id: User identifier
            **overrides: Optional field overrides
            
        Returns:
            Dict containing preferences data
        """
        base_data = {
            "categories": ["motivational", "health"],
            "channel": {"type": "discord"},
            "notification_settings": {
                "morning_reminders": True,
                "task_reminders": True,
                "checkin_reminders": True
            }
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_schedules_data(**overrides) -> Dict[str, Any]:
        """
        Create standard schedules data structure with optional overrides
        
        Args:
            **overrides: Optional field overrides
            
        Returns:
            Dict containing schedules data
        """
        base_data = {
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_context_data(**overrides) -> Dict[str, Any]:
        """
        Create standard context data structure with optional overrides
        
        Args:
            **overrides: Optional field overrides
            
        Returns:
            Dict containing context data
        """
        base_data = {
            "preferred_name": "Test User",
            "timezone": "UTC",
            "language": "en",
            "created_date": "2025-01-01"
        }
        base_data.update(overrides)
        return base_data


# Convenience functions for backward compatibility
def create_test_user(user_id: str, user_type: str = "basic", test_data_dir: str = None, **kwargs) -> bool:
    """
    Convenience function to create test users with different configurations
    
    Args:
        user_id: Unique identifier for the test user
        user_type: Type of user to create. Options:
            - "basic": Basic user with configurable features
            - "discord": Discord-specific user
            - "email": Email-specific user

            - "full": Full featured user with all capabilities
            - "minimal": Minimal user with only messaging
            - "health": Health-focused user
            - "task": Task/productivity-focused user
            - "disability": User with accessibility considerations
            - "complex_checkins": User with complex check-in configurations
            - "limited_data": User with minimal data (like real users)
            - "inconsistent": User with inconsistent/partial data
            - "custom_fields": User with custom field configurations
            - "scheduled": User with custom schedule configurations
        test_data_dir: Test data directory to use (required for modern test approach)
        **kwargs: Additional arguments passed to the specific creation method
        
    Returns:
        bool: True if user was created successfully, False otherwise
    """
    try:
        if user_type == "basic":
            enable_checkins = kwargs.get('enable_checkins', True)
            enable_tasks = kwargs.get('enable_tasks', True)
            return TestUserFactory.create_basic_user(user_id, enable_checkins, enable_tasks, test_data_dir)
        
        elif user_type == "discord":
            discord_user_id = kwargs.get('discord_user_id')
            return TestUserFactory.create_discord_user(user_id, discord_user_id, test_data_dir)
        
        elif user_type == "email":
            email = kwargs.get('email')
            return TestUserFactory.create_email_user(user_id, email, test_data_dir)
        

        
        elif user_type == "full":
            return TestUserFactory.create_full_featured_user(user_id, test_data_dir)
        
        elif user_type == "minimal":
            return TestUserFactory.create_minimal_user(user_id, test_data_dir)
        
        elif user_type == "health":
            return TestUserFactory.create_user_with_health_focus(user_id, test_data_dir)
        
        elif user_type == "task":
            return TestUserFactory.create_user_with_task_focus(user_id, test_data_dir)
        
        elif user_type == "disability":
            return TestUserFactory.create_user_with_disabilities(user_id, test_data_dir)
        
        elif user_type == "complex_checkins":
            return TestUserFactory.create_user_with_complex_checkins(user_id, test_data_dir)
        
        elif user_type == "limited_data":
            return TestUserFactory.create_user_with_limited_data(user_id, test_data_dir)
        
        elif user_type == "inconsistent":
            return TestUserFactory.create_user_with_inconsistent_data(user_id, test_data_dir)
        
        elif user_type == "custom_fields":
            custom_fields = kwargs.get('custom_fields')
            return TestUserFactory.create_user_with_custom_fields(user_id, custom_fields, test_data_dir)
        
        elif user_type == "scheduled":
            schedule_config = kwargs.get('schedule_config')
            return TestUserFactory.create_user_with_schedules(user_id, schedule_config, test_data_dir)
        
        else:
            logger.error(f"Unknown user type: {user_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating test user {user_id} of type {user_type}: {e}")
        return False


def setup_test_data_environment() -> tuple:
    """
    Convenience function to set up test data environment
    
    Returns:
        tuple: (test_dir, test_data_dir, test_test_data_dir)
    """
    return TestDataManager.setup_test_environment()


def cleanup_test_data_environment(test_dir: str) -> None:
    """
    Convenience function to clean up test data environment
    
    Args:
        test_dir: Path to the test directory to clean up
    """
    TestDataManager.cleanup_test_environment(test_dir)


class TestDataFactory:
    """Factory for creating test data for various scenarios"""
    
    @staticmethod
    def create_corrupted_user_data(user_id: str, corruption_type: str = "invalid_json") -> bool:
        """
        Create a user with corrupted data for testing error handling
        
        Args:
            user_id: Unique identifier for the test user
            corruption_type: Type of corruption ("invalid_json", "missing_file", "empty_file")
            
        Returns:
            bool: True if corrupted user was created successfully, False otherwise
        """
        try:
            from core.config import get_user_data_dir
            import os
            
            # Create user directory
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            if corruption_type == "invalid_json":
                # Create file with invalid JSON
                with open(os.path.join(user_dir, "account.json"), 'w') as f:
                    f.write("invalid json content")
                with open(os.path.join(user_dir, "preferences.json"), 'w') as f:
                    f.write("{ invalid json }")
                with open(os.path.join(user_dir, "user_context.json"), 'w') as f:
                    f.write("not json at all")
                    
            elif corruption_type == "missing_file":
                # Create only some files, leave others missing
                with open(os.path.join(user_dir, "account.json"), 'w') as f:
                    json.dump({"user_id": user_id}, f)
                # Don't create preferences.json or user_context.json
                
            elif corruption_type == "empty_file":
                # Create empty files
                with open(os.path.join(user_dir, "account.json"), 'w') as f:
                    f.write("")
                with open(os.path.join(user_dir, "preferences.json"), 'w') as f:
                    f.write("")
                with open(os.path.join(user_dir, "user_context.json"), 'w') as f:
                    f.write("")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating corrupted user data for {user_id}: {e}")
            return False
    
    @staticmethod
    def create_test_schedule_data(categories: List[str] = None) -> Dict[str, Any]:
        """
        Create test schedule data for testing schedule management
        
        Args:
            categories: List of categories to create schedules for
            
        Returns:
            Dict containing schedule data
        """
        if categories is None:
            categories = ["motivational", "health"]
        
        schedule_data = {}
        for category in categories:
            schedule_data[category] = {
                "periods": {
                    "Default": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "21:30"
                    }
                }
            }
        
        return schedule_data
    
    @staticmethod
    def create_test_task_data(task_count: int = 3) -> List[Dict[str, Any]]:
        """
        Create test task data for testing task management
        
        Args:
            task_count: Number of tasks to create
            
        Returns:
            List of task dictionaries
        """
        import uuid
        from datetime import datetime, timedelta
        
        tasks = []
        for i in range(task_count):
            task = {
                "task_id": str(uuid.uuid4()),
                "title": f"Test Task {i+1}",
                "description": f"Description for test task {i+1}",
                "priority": "medium",
                "status": "active",
                "due_date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            tasks.append(task)
        
        return tasks
    
    @staticmethod
    def create_test_message_data(category: str = "motivational", message_count: int = 5) -> List[Dict[str, Any]]:
        """
        Create test message data for testing message management
        
        Args:
            category: Message category
            message_count: Number of messages to create
            
        Returns:
            List of message dictionaries
        """
        import uuid
        from datetime import datetime, timedelta
        
        messages = []
        for i in range(message_count):
            message = {
                "message_id": str(uuid.uuid4()),
                "content": f"Test message {i+1} for {category}",
                "category": category,
                "created_at": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
                "sent": False,
                "scheduled_for": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
            }
            messages.append(message)
        
        return messages


class TestLogPathMocks:
    """Helper class for creating complete log path mocks for tests"""
    
    @staticmethod
    def create_complete_log_paths_mock(base_dir: str) -> Dict[str, str]:
        """
        Create a complete mock dictionary for _get_log_paths_for_environment()
        that includes all required keys including ai_dev_tools_file.
        
        Args:
            base_dir: Base directory for logs (e.g., test_data_dir / "logs")
            
        Returns:
            Dict with all log path keys required by the logger system
        """
        from pathlib import Path
        base_path = Path(base_dir)
        
        return {
            'base_dir': str(base_path),
            'backup_dir': str(base_path / "backups"),
            'archive_dir': str(base_path / "archive"),
            'main_file': str(base_path / "app.log"),
            'discord_file': str(base_path / "discord.log"),
            'ai_file': str(base_path / "ai.log"),
            'user_activity_file': str(base_path / "user_activity.log"),
            'errors_file': str(base_path / "errors.log"),
            'communication_manager_file': str(base_path / "communication_manager.log"),
            'email_file': str(base_path / "email.log"),
            'ui_file': str(base_path / "ui.log"),
            'file_ops_file': str(base_path / "file_ops.log"),
            'scheduler_file': str(base_path / "scheduler.log"),
            'schedule_utilities_file': str(base_path / "schedule_utilities.log"),
            'analytics_file': str(base_path / "analytics.log"),
            'message_file': str(base_path / "message.log"),
            'backup_file': str(base_path / "backup.log"),
            'checkin_dynamic_file': str(base_path / "checkin_dynamic.log"),
            'ai_dev_tools_file': str(base_path / "ai_dev_tools.log"),
        }
