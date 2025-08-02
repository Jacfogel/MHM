#!/usr/bin/env python3
"""
Test Utilities for MHM
Centralized test helper functions to eliminate redundancy across test files
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_management import create_new_user, save_user_account_data, save_user_preferences_data
from core.file_operations import ensure_user_directory


class TestUserFactory:
    """Factory for creating test users with different configurations"""
    
    @staticmethod
    def create_basic_user(user_id: str, enable_checkins: bool = True, enable_tasks: bool = True) -> bool:
        """
        Create a test user with basic functionality enabled
        
        Args:
            user_id: Unique identifier for the test user
            enable_checkins: Whether to enable check-ins for this user
            enable_tasks: Whether to enable task management for this user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating basic user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_discord_user(user_id: str, discord_user_id: str = None) -> bool:
        """
        Create a test user specifically configured for Discord testing
        
        Args:
            user_id: Unique identifier for the test user
            discord_user_id: Discord user ID (defaults to user_id if not provided)
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            if discord_user_id is None:
                discord_user_id = user_id
            
            # Create the user data structure that matches what the system expects
            from core.user_data_handlers import save_user_data
            from core.config import get_user_data_dir
            import os
            
            # Create user directory if it doesn't exist
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create account data with Discord-specific information
            account_data = {
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": discord_user_id,
                "created_at": "2025-01-01 00:00:00",
                "updated_at": "2025-01-01 00:00:00",
                "features": {
                    "automated_messages": "enabled",
                    "checkins": "enabled",
                    "task_management": "enabled"
                },
                "timezone": "UTC"
            }
            
            # Create preferences data
            preferences_data = {
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
                "notification_settings": {
                    "morning_reminders": True,
                    "evening_reminders": False,
                    "task_reminders": True,
                    "checkin_reminders": True
                }
            }
            
            # Create context data
            context_data = {
                "preferred_name": f"Discord User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "custom_fields": {
                    "reminders_needed": [],
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Technology", "Gaming"],
                "goals": ["Improve mental health", "Stay organized"],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": [],
                "created_at": "2025-01-01 00:00:00",
                "last_updated": "2025-01-01 00:00:00"
            }
            
            # Save all data using the centralized save function
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })  # Now validation should work correctly
            
            # Check if all data types were saved successfully
            success = all(result.values())
            
            if success:
                # Update user index
                try:
                    from core.user_data_manager import update_user_index
                    update_user_index(user_id)
                except Exception as e:
                    print(f"Warning: Failed to update user index for {user_id}: {e}")
            
            return success
            
        except Exception as e:
            print(f"Error creating Discord user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_full_featured_user(user_id: str) -> bool:
        """
        Create a test user with all features enabled and comprehensive data
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # Create the user data structure that matches what the system expects
            from core.user_data_handlers import save_user_data
            from core.config import get_user_data_dir
            import os
            
            # Create user directory if it doesn't exist
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create account data with all features enabled
            account_data = {
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "created_at": "2025-01-01 00:00:00",
                "updated_at": "2025-01-01 00:00:00",
                "features": {
                    "automated_messages": "enabled",
                    "checkins": "enabled",
                    "task_management": "enabled"
                },
                "timezone": "America/New_York"
            }
            
            # Create comprehensive preferences data
            preferences_data = {
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
                    "auto_categorize": True
                },
                "notification_settings": {
                    "morning_reminders": True,
                    "evening_reminders": True,
                    "task_reminders": True,
                    "checkin_reminders": True,
                    "motivational_messages": True
                }
            }
            
            # Create comprehensive context data
            context_data = {
                "preferred_name": f"Full Featured User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "1990-01-01",
                "custom_fields": {
                    "reminders_needed": ["Take medication", "Drink water", "Take breaks"],
                    "health_conditions": ["Anxiety", "Depression"],
                    "medications_treatments": ["Therapy", "Medication A"],
                    "allergies_sensitivities": ["Pollen"]
                },
                "interests": ["Technology", "Gaming", "Reading", "Music"],
                "goals": ["Improve mental health", "Stay organized", "Exercise regularly", "Read more books"],
                "loved_ones": ["Family", "Friends"],
                "activities_for_encouragement": ["Going for walks", "Reading", "Playing games"],
                "notes_for_ai": ["Prefers gentle reminders", "Responds well to humor", "Likes detailed explanations"],
                "created_at": "2025-01-01 00:00:00",
                "last_updated": "2025-01-01 00:00:00"
            }
            
            # Save all data using the centralized save function
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })  # Now validation should work correctly
            
            # Check if all data types were saved successfully
            success = all(result.values())
            
            if success:
                # Update user index
                try:
                    from core.user_data_manager import update_user_index
                    update_user_index(user_id)
                except Exception as e:
                    print(f"Warning: Failed to update user index for {user_id}: {e}")
            
            return success
            
        except Exception as e:
            print(f"Error creating full featured user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_email_user(user_id: str, email: str = None, test_data_dir: str = None) -> str:
        """
        Create a test user specifically configured for email testing
        
        Args:
            user_id: Unique identifier for the test user
            email: Email address for the test user (defaults to user_id@example.com)
            test_data_dir: Optional test data directory to use for configuration
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
            
            # If test_data_dir is provided, patch the configuration during user creation
            if test_data_dir:
                from unittest.mock import patch
                import core.config
                with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
                     patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(test_data_dir, "users")):
                    actual_user_id = create_new_user(user_data)
            else:
                # Create the user using the proper function
                actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return actual_user_id
            else:
                return None
            
        except Exception as e:
            print(f"Error creating email test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_custom_fields(user_id: str, custom_fields: Dict[str, Any] = None) -> bool:
        """
        Create a test user with custom fields for testing custom field functionality
        
        Args:
            user_id: Unique identifier for the test user
            custom_fields: Dictionary of custom fields to add to user context
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating custom fields test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_telegram_user(user_id: str, telegram_username: str = None) -> bool:
        """
        Create a test user specifically configured for Telegram testing
        
        Args:
            user_id: Unique identifier for the test user
            telegram_username: Telegram username for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            if telegram_username is None:
                telegram_username = f"test_user_{user_id}"
            
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
                    "type": "telegram",
                    "contact": telegram_username
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
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating Telegram test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_schedules(user_id: str, schedule_config: Dict[str, Any] = None) -> bool:
        """
        Create a test user with comprehensive schedule configuration
        
        Args:
            user_id: Unique identifier for the test user
            schedule_config: Custom schedule configuration
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
                return False
            
            # Add schedule data using the correct function
            from core.user_management import save_user_schedules_data
            schedule_success = save_user_schedules_data(actual_user_id, schedule_config)
            
            return schedule_success
        except Exception as e:
            print(f"Error creating scheduled test user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_minimal_user(user_id: str) -> bool:
        """
        Create a minimal test user with only basic messaging enabled
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # Create the user data structure that matches what the system expects
            from core.user_data_handlers import save_user_data
            from core.config import get_user_data_dir
            import os
            
            # Create user directory if it doesn't exist
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create minimal account data
            account_data = {
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "created_at": "2025-01-01 00:00:00",
                "updated_at": "2025-01-01 00:00:00",
                "features": {
                    "automated_messages": "enabled",
                    "checkins": "disabled",
                    "task_management": "disabled"
                },
                "timezone": "UTC"
            }
            
            # Create minimal preferences data
            preferences_data = {
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {},
                "task_management": {},
                "timezone": "",
                "ai_settings": {
                    "model": "deepseek-llm-7b-chat",
                    "temperature": 0.7
                }
            }
            
            # Create minimal context data
            context_data = {
                "preferred_name": "",
                "pronouns": [],
                "date_of_birth": "",
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "reminders_needed": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": [],
                "created_at": "2025-01-01 00:00:00",
                "last_updated": "2025-01-01 00:00:00"
            }
            
            # Save all data using the centralized save function
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })
            
            # Check if all data types were saved successfully
            success = all(result.values())
            
            if success:
                # Update user index
                try:
                    from core.user_data_manager import update_user_index
                    update_user_index(user_id)
                except Exception as e:
                    print(f"Warning: Failed to update user index for {user_id}: {e}")
            
            return success
            
        except Exception as e:
            print(f"Error creating minimal user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_complex_checkins(user_id: str) -> bool:
        """
        Create a test user with complex check-in configurations
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
                    "questions": {
                        "mood": {
                            "enabled": True,
                            "label": "Mood (1-5 scale)"
                        },
                        "energy_level": {
                            "enabled": True,
                            "label": "Energy level (1-5 scale)"
                        },
                        "hydrated": {
                            "enabled": False,
                            "label": "Staying hydrated (yes/no)"
                        },
                        "brushed_teeth": {
                            "enabled": True,
                            "label": "Brushed teeth (yes/no)"
                        },
                        "sleep_quality": {
                            "enabled": True,
                            "label": "Sleep quality (1-5 scale)"
                        },
                        "stress_level": {
                            "enabled": True,
                            "label": "Stress level (1-5 scale)"
                        },
                        "anxiety_level": {
                            "enabled": True,
                            "label": "Anxiety level (1-5 scale)"
                        },
                        "sleep_hours": {
                            "enabled": False,
                            "label": "Hours of sleep (number)"
                        },
                        "medication": {
                            "enabled": False,
                            "label": "Took medication (yes/no)"
                        },
                        "breakfast": {
                            "enabled": False,
                            "label": "Had breakfast (yes/no)"
                        },
                        "exercise": {
                            "enabled": False,
                            "label": "Did exercise (yes/no)"
                        },
                        "social_interaction": {
                            "enabled": False,
                            "label": "Had social interaction (yes/no)"
                        },
                        "reflection_notes": {
                            "enabled": False,
                            "label": "Brief reflection/notes (text)"
                        }
                    }
                },
                "task_settings": {
                    "enabled": False,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Complex Check-in User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["Daily check-ins", "Mood tracking"],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Mental health", "Self-reflection"],
                "goals": ["Track mood patterns", "Improve self-awareness"],
                "loved_ones": [],
                "activities_for_encouragement": ["Journaling", "Meditation"],
                "notes_for_ai": ["Prefers detailed check-ins", "Likes mood tracking"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating user with complex check-ins {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_health_focus(user_id: str) -> bool:
        """
        Create a test user focused on health and wellness features
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
                    "questions": {
                        "mood": {"enabled": True, "label": "Mood (1-5 scale)"},
                        "energy_level": {"enabled": True, "label": "Energy level (1-5 scale)"},
                        "sleep_quality": {"enabled": True, "label": "Sleep quality (1-5 scale)"},
                        "stress_level": {"enabled": True, "label": "Stress level (1-5 scale)"},
                        "medication": {"enabled": True, "label": "Took medication (yes/no)"},
                        "exercise": {"enabled": True, "label": "Did exercise (yes/no)"},
                        "hydrated": {"enabled": True, "label": "Staying hydrated (yes/no)"}
                    }
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "high",
                    "reminder_enabled": True,
                    "health_reminders": True
                },
                "preferred_name": f"Health User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["Take medication", "Exercise", "Stay hydrated"],
                "custom_fields": {
                    "health_conditions": ["Anxiety", "Depression"],
                    "medications_treatments": ["Therapy", "Medication"],
                    "allergies_sensitivities": []
                },
                "interests": ["Health", "Wellness", "Exercise"],
                "goals": ["Improve mental health", "Stay active", "Maintain medication schedule"],
                "loved_ones": ["Family", "Therapist"],
                "activities_for_encouragement": ["Exercise", "Meditation", "Walking"],
                "notes_for_ai": ["Health-focused user", "Prefers gentle health reminders"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating health focus test user {user_id}: {e}")

    
    @staticmethod
    def create_user_with_task_focus(user_id: str) -> bool:
        """
        Create a test user focused on task management and productivity
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
                    "default_priority": "medium",
                    "reminder_enabled": True,
                    "auto_categorize": True,
                    "default_reminder_time": "19:00",
                    "productivity_tracking": True
                },
                "preferred_name": f"Productivity User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["Complete tasks", "Review goals", "Plan next day"],
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "allergies_sensitivities": []
                },
                "interests": ["Productivity", "Organization", "Technology"],
                "goals": ["Stay organized", "Complete daily tasks", "Improve productivity"],
                "loved_ones": [],
                "activities_for_encouragement": ["Task planning", "Goal setting", "Time management"],
                "notes_for_ai": ["Prefers structured task reminders", "Likes productivity tips"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating task-focused user {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_disabilities(user_id: str) -> bool:
        """
        Create a test user with accessibility and disability considerations
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
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
                    "questions": {
                        "mood": {"enabled": True, "label": "Mood (1-5 scale)"},
                        "energy_level": {"enabled": True, "label": "Energy level (1-5 scale)"},
                        "medication": {"enabled": True, "label": "Took medication (yes/no)"},
                        "accessibility_needs": {"enabled": True, "label": "Accessibility needs met (yes/no)"},
                        "pain_level": {"enabled": True, "label": "Pain level (1-5 scale)"}
                    }
                },
                "task_settings": {
                    "enabled": True,
                    "default_priority": "medium",
                    "reminder_enabled": True
                },
                "preferred_name": f"Accessibility User {user_id}",
                "gender_identity": ["they/them"],
                "date_of_birth": "",
                "reminders_needed": ["Take medication", "Accessibility breaks", "Therapy appointments"],
                "custom_fields": {
                    "health_conditions": ["ADHD", "Anxiety"],
                    "medications_treatments": ["Medication A", "Therapy"],
                    "allergies_sensitivities": []
                },
                "interests": ["Accessibility", "Technology", "Advocacy"],
                "goals": ["Improve accessibility", "Manage ADHD", "Stay organized"],
                "loved_ones": [],
                "activities_for_encouragement": ["Accessibility advocacy", "Self-care", "Organization"],
                "notes_for_ai": ["Prefers clear, simple instructions", "Needs frequent reminders", "Responds well to accessibility-focused support"]
            }
            
            # Create the user using the proper function
            actual_user_id = create_new_user(user_data)
            
            if actual_user_id:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error creating user with disabilities {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_limited_data(user_id: str) -> bool:
        """
        Create a test user with minimal data (like real users who don't fill out much)
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # Create the user data structure that matches what the system expects
            from core.user_data_handlers import save_user_data
            from core.config import get_user_data_dir
            import os
            
            # Create user directory if it doesn't exist
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create minimal account data
            account_data = {
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "chat_id": "",
                "phone": "",
                "email": f"{user_id}@example.com",
                "discord_user_id": "",
                "created_at": "2025-01-01 00:00:00",
                "updated_at": "2025-01-01 00:00:00",
                "features": {
                    "automated_messages": "enabled",
                    "checkins": "disabled",
                    "task_management": "disabled"
                },
                "timezone": "UTC"
            }
            
            # Create minimal preferences data (like real users)
            preferences_data = {
                "categories": ["motivational"],
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {},
                "task_management": {},
                "timezone": "",
                "ai_settings": {
                    "model": "deepseek-llm-7b-chat",
                    "temperature": 0.7
                }
            }
            
            # Create minimal context data (like real users)
            context_data = {
                "preferred_name": "",
                "pronouns": [],
                "date_of_birth": "",
                "custom_fields": {
                    "health_conditions": [],
                    "medications_treatments": [],
                    "reminders_needed": []
                },
                "interests": [],
                "goals": [],
                "loved_ones": [],
                "activities_for_encouragement": [],
                "notes_for_ai": [],
                "created_at": "2025-01-01 00:00:00",
                "last_updated": "2025-01-01 00:00:00"
            }
            
            # Save all data using the centralized save function
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })
            
            # Check if all data types were saved successfully
            success = all(result.values())
            
            if success:
                # Update user index
                try:
                    from core.user_data_manager import update_user_index
                    update_user_index(user_id)
                except Exception as e:
                    print(f"Warning: Failed to update user index for {user_id}: {e}")
            
            return success
            
        except Exception as e:
            print(f"Error creating user with limited data {user_id}: {e}")
            return False
    
    @staticmethod
    def create_user_with_inconsistent_data(user_id: str) -> bool:
        """
        Create a test user with inconsistent or partially filled data (like real users)
        
        Args:
            user_id: Unique identifier for the test user
            
        Returns:
            bool: True if user was created successfully, False otherwise
        """
        try:
            # Create the user data structure that matches what the system expects
            from core.user_data_handlers import save_user_data
            from core.config import get_user_data_dir
            import os
            
            # Create user directory if it doesn't exist
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create account data with some inconsistencies
            account_data = {
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "chat_id": "",
                "phone": "3062619228",  # Has phone but no email
                "email": "",  # Empty email
                "discord_user_id": "",
                "created_at": "2025-01-01 00:00:00",
                "updated_at": "2025-01-01 00:00:00",
                "features": {
                    "automated_messages": "enabled",
                    "checkins": "enabled",
                    "task_management": "disabled"
                },
                "timezone": "America/Regina"
            }
            
            # Create preferences with some inconsistencies
            preferences_data = {
                "categories": ["health", "motivational"],  # Has categories
                "channel": {
                    "type": "email"
                },
                "checkin_settings": {
                    "questions": {
                        "mood": {"enabled": True, "label": "Mood (1-5 scale)"},
                        "energy_level": {"enabled": True, "label": "Energy level (1-5 scale)"}
                    }
                },
                "task_management": {},  # Empty task management
                "timezone": "",  # Empty timezone
                "ai_settings": {
                    "model": "deepseek-llm-7b-chat",
                    "temperature": 0.7
                },
                "test_field": None  # Extra field like real users
            }
            
            # Create context with some inconsistencies
            context_data = {
                "preferred_name": "",  # Empty preferred name
                "pronouns": [],  # Empty pronouns
                "date_of_birth": "",  # Empty date of birth
                "custom_fields": {
                    "health_conditions": [],  # Empty health conditions
                    "medications_treatments": [],  # Empty medications
                    "reminders_needed": []  # Empty reminders
                },
                "interests": [],  # Empty interests
                "goals": [],  # Empty goals
                "loved_ones": [],  # Empty loved ones
                "activities_for_encouragement": [],  # Empty activities
                "notes_for_ai": [],  # Empty notes
                "created_at": "2025-01-01 00:00:00",
                "last_updated": "2025-01-01 00:00:00"
            }
            
            # Save all data using the centralized save function
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })
            
            # Check if all data types were saved successfully
            success = all(result.values())
            
            if success:
                # Update user index
                try:
                    from core.user_data_manager import update_user_index
                    update_user_index(user_id)
                except Exception as e:
                    print(f"Warning: Failed to update user index for {user_id}: {e}")
            
            return success
            
        except Exception as e:
            print(f"Error creating user with inconsistent data {user_id}: {e}")
            return False


class TestDataManager:
    """Manages test data directories and cleanup"""
    
    @staticmethod
    def setup_test_environment() -> tuple:
        """
        Create isolated test environment with temporary directories
        
        Returns:
            tuple: (test_dir, test_data_dir, test_test_data_dir)
        """
        # Create temporary test directory
        test_dir = tempfile.mkdtemp(prefix="mhm_test_")
        test_data_dir = os.path.join(test_dir, "data")
        test_test_data_dir = os.path.join(test_dir, "tests", "data")
        
        # Create directory structure
        os.makedirs(test_data_dir, exist_ok=True)
        os.makedirs(test_test_data_dir, exist_ok=True)
        os.makedirs(os.path.join(test_data_dir, "users"), exist_ok=True)
        os.makedirs(os.path.join(test_test_data_dir, "users"), exist_ok=True)
        
        # Create test user index
        user_index = {
            "test-user-basic": {
                "internal_username": "test-user-basic",
                "active": True,
                "channel_type": "discord",
                "enabled_features": ["messages"],
                "last_interaction": "2025-01-01T00:00:00",
                "last_updated": "2025-01-01T00:00:00"
            },
            "test-user-full": {
                "internal_username": "test-user-full", 
                "active": True,
                "channel_type": "discord",
                "enabled_features": ["messages", "tasks", "checkins"],
                "last_interaction": "2025-01-01T00:00:00",
                "last_updated": "2025-01-01T00:00:00"
            }
        }
        
        with open(os.path.join(test_data_dir, "user_index.json"), "w") as f:
            json.dump(user_index, f, indent=2)
        
        return test_dir, test_data_dir, test_test_data_dir
    
    @staticmethod
    def cleanup_test_environment(test_dir: str) -> None:
        """
        Clean up test environment and remove temporary files
        
        Args:
            test_dir: Path to the test directory to clean up
        """
        try:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
        except Exception as e:
            print(f"Warning: Could not clean up test directory {test_dir}: {e}")


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
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
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
def create_test_user(user_id: str, user_type: str = "basic", **kwargs) -> bool:
    """
    Convenience function to create test users with different configurations
    
    Args:
        user_id: Unique identifier for the test user
        user_type: Type of user to create. Options:
            - "basic": Basic user with configurable features
            - "discord": Discord-specific user
            - "email": Email-specific user
            - "telegram": Telegram-specific user
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
        **kwargs: Additional arguments passed to the specific creation method
        
    Returns:
        bool: True if user was created successfully, False otherwise
    """
    try:
        if user_type == "basic":
            enable_checkins = kwargs.get('enable_checkins', True)
            enable_tasks = kwargs.get('enable_tasks', True)
            return TestUserFactory.create_basic_user(user_id, enable_checkins, enable_tasks)
        
        elif user_type == "discord":
            discord_user_id = kwargs.get('discord_user_id')
            return TestUserFactory.create_discord_user(user_id, discord_user_id)
        
        elif user_type == "email":
            email = kwargs.get('email')
            return TestUserFactory.create_email_user(user_id, email)
        
        elif user_type == "telegram":
            telegram_username = kwargs.get('telegram_username')
            return TestUserFactory.create_telegram_user(user_id, telegram_username)
        
        elif user_type == "full":
            return TestUserFactory.create_full_featured_user(user_id)
        
        elif user_type == "minimal":
            return TestUserFactory.create_minimal_user(user_id)
        
        elif user_type == "health":
            return TestUserFactory.create_user_with_health_focus(user_id)
        
        elif user_type == "task":
            return TestUserFactory.create_user_with_task_focus(user_id)
        
        elif user_type == "disability":
            return TestUserFactory.create_user_with_disabilities(user_id)
        
        elif user_type == "complex_checkins":
            return TestUserFactory.create_user_with_complex_checkins(user_id)
        
        elif user_type == "limited_data":
            return TestUserFactory.create_user_with_limited_data(user_id)
        
        elif user_type == "inconsistent":
            return TestUserFactory.create_user_with_inconsistent_data(user_id)
        
        elif user_type == "custom_fields":
            custom_fields = kwargs.get('custom_fields')
            return TestUserFactory.create_user_with_custom_fields(user_id, custom_fields)
        
        elif user_type == "scheduled":
            schedule_config = kwargs.get('schedule_config')
            return TestUserFactory.create_user_with_schedules(user_id, schedule_config)
        
        else:
            print(f"Unknown user type: {user_type}")
            return False
            
    except Exception as e:
        print(f"Error creating test user {user_id} of type {user_type}: {e}")
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
            print(f"Error creating corrupted user data for {user_id}: {e}")
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
