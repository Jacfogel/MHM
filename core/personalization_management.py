# personalization_management.py
"""
Personalization management utilities for MHM.
Contains functions for user personalization data operations.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.logger import get_logger
from core.config import get_user_file_path, ensure_user_directory
from core.file_operations import load_json_data, save_json_data
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

# Cache for personalization data
_personalization_cache = {}
_cache_timeout = 30  # Cache for 30 seconds

def load_user_personalization_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Load user personalization data from user_context.json."""
    if not user_id:
        return None
    
    try:
        # Load from user_context.json instead of personalizations.json
        context_file = get_user_file_path(user_id, 'user_context')
        context_data = load_json_data(context_file)
        if not context_data:
            logger.warning(f"No user context data found for user {user_id}")
            return None
        
        # Extract personalization fields from context data
        personalization_data = {
            "preferred_name": context_data.get("preferred_name", ""),
            "pronouns": context_data.get("pronouns", []),
            "date_of_birth": context_data.get("date_of_birth", ""),
            "custom_fields": context_data.get("custom_fields", {}),
            "interests": context_data.get("interests", []),
            "goals": context_data.get("goals", []),
            "loved_ones": context_data.get("loved_ones", []),
            "activities_for_encouragement": context_data.get("activities_for_encouragement", []),
            "notes_for_ai": context_data.get("notes_for_ai", [])
        }
        
        return personalization_data
        
    except Exception as e:
        logger.error(f"Error loading personalization data for user {user_id}: {e}")
        return None

def save_user_personalization_data(user_id: str, personalization_data: Dict[str, Any]) -> bool:
    """Save user personalization data to user_context.json."""
    if not user_id or not personalization_data:
        return False
    
    try:
        # Load existing context data
        context_file = get_user_file_path(user_id, 'user_context')
        context_data = load_json_data(context_file) or {}
        
        # Update with new personalization data
        context_data.update({
            "preferred_name": personalization_data.get("preferred_name", ""),
            "pronouns": personalization_data.get("pronouns", []),
            "date_of_birth": personalization_data.get("date_of_birth", ""),
            "custom_fields": personalization_data.get("custom_fields", {}),
            "interests": personalization_data.get("interests", []),
            "goals": personalization_data.get("goals", []),
            "loved_ones": personalization_data.get("loved_ones", []),
            "activities_for_encouragement": personalization_data.get("activities_for_encouragement", []),
            "notes_for_ai": personalization_data.get("notes_for_ai", []),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Save back to user_context.json
        save_json_data(context_data, context_file)
        logger.info(f"Saved personalization data for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving personalization data for user {user_id}: {e}")
        return False

def create_default_personalization_data() -> Dict[str, Any]:
    """Create default personalization data structure."""
    return {
        "pronouns": [],
        "date_of_birth": "",
        "timezone": "",
        "health_conditions": [],
        "medications_treatments": [],
        "reminders_needed": [],
        "loved_ones": [],
        "interests": [],
        "activities_for_encouragement": [],
        "notes_for_ai": [],
        "goals": [],
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@handle_errors("getting personalization field", default_return=None)
def get_personalization_field(user_id: str, field: str) -> Any:
    """Get a specific field from personalization data."""
    if not user_id or not field:
        logger.error("get_personalization_field called with invalid parameters")
        return None
    
    personalization_data = load_user_personalization_data(user_id)
    if personalization_data is None:
        return None
    
    return personalization_data.get(field)

@handle_errors("updating personalization field")
def update_personalization_field(user_id: str, field: str, value: Any) -> bool:
    """Update a specific field in personalization data."""
    if not user_id or not field:
        logger.error("update_personalization_field called with invalid parameters")
        return False
    
    personalization_data = load_user_personalization_data(user_id)
    if personalization_data is None:
        personalization_data = create_default_personalization_data()
    
    personalization_data[field] = value
    return save_user_personalization_data(user_id, personalization_data)

@handle_errors("adding item to personalization list")
def add_personalization_item(user_id: str, field: str, item: Any) -> bool:
    """Add an item to a list field in personalization data."""
    if not user_id or not field:
        logger.error("add_personalization_item called with invalid parameters")
        return False
    
    personalization_data = load_user_personalization_data(user_id)
    if personalization_data is None:
        personalization_data = create_default_personalization_data()
    
    if field not in personalization_data:
        personalization_data[field] = []
    
    if not isinstance(personalization_data[field], list):
        logger.error(f"Field {field} is not a list")
        return False
    
    if item not in personalization_data[field]:
        personalization_data[field].append(item)
        return save_user_personalization_data(user_id, personalization_data)
    
    return True  # Item already exists

@handle_errors("removing item from personalization list")
def remove_personalization_item(user_id: str, field: str, item: Any) -> bool:
    """Remove an item from a list field in personalization data."""
    if not user_id or not field:
        logger.error("remove_personalization_item called with invalid parameters")
        return False
    
    personalization_data = load_user_personalization_data(user_id)
    if personalization_data is None:
        return False
    
    if field not in personalization_data or not isinstance(personalization_data[field], list):
        return False
    
    if item in personalization_data[field]:
        personalization_data[field].remove(item)
        return save_user_personalization_data(user_id, personalization_data)
    
    return True  # Item doesn't exist

@handle_errors("clearing personalization cache")
def clear_personalization_cache(user_id: str = None) -> None:
    """Clear the personalization cache for a specific user or all users."""
    global _personalization_cache
    
    if user_id:
        cache_key = f"personalization_{user_id}"
        if cache_key in _personalization_cache:
            del _personalization_cache[cache_key]
            logger.debug(f"Cleared personalization cache for user {user_id}")
    else:
        _personalization_cache.clear()
        logger.debug("Cleared all personalization cache")

# Predefined options for various fields
PREDEFINED_OPTIONS = {
    "pronouns": [
        "she/her", "he/him", "they/them", "she/they", "he/they", 
        "any pronouns", "prefer not to say"
    ],
    "health_conditions": [
        "ADHD", "Anxiety", "Depression", "Bipolar Disorder", "PTSD", 
        "OCD", "Autism", "Chronic Pain", "Diabetes", "Asthma",
        "Sleep Disorders", "Eating Disorders", "Substance Use Disorder"
    ],
    "medications_treatments": [
        "Antidepressant", "Anti-anxiety medication", "Stimulant for ADHD",
        "Mood stabilizer", "Antipsychotic", "Sleep medication",
        "Therapy", "Counseling", "Support groups", "Exercise",
        "Meditation", "Yoga", "CPAP", "Inhaler", "Insulin"
    ],
    "reminders_needed": [
        "medications_treatments", "hydration", "movement/stretch breaks",
        "healthy meals/snacks", "mental health check-ins", "appointments",
        "exercise", "sleep schedule", "self-care activities"
    ],
    "loved_one_types": [
        "human", "dog", "cat", "bird", "fish", "reptile", "horse",
        "rabbit", "hamster", "guinea pig", "ferret", "other"
    ],
    "relationship_types": [
        "partner", "spouse", "parent", "child", "sibling", "friend",
        "roommate", "colleague", "therapist", "doctor", "teacher"
    ],
    "interests": [
        "Reading", "Writing", "Gaming", "Music", "Art", "Cooking",
        "Baking", "Gardening", "Hiking", "Swimming", "Running",
        "Yoga", "Meditation", "Photography", "Crafts", "Knitting",
        "Painting", "Drawing", "Sewing", "Woodworking", "Programming",
        "Math", "Science", "History", "Languages", "Travel"
    ],
    "activities_for_encouragement": [
        "exercise", "healthy eating", "sleep hygiene", "social activities",
        "hobbies", "work/projects", "self-care", "therapy appointments",
        "medication adherence", "stress management"
    ]
}

# Timezone options (common ones)
TIMEZONE_OPTIONS = [
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Regina", "America/Toronto", "America/Vancouver", "America/Edmonton",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
    "Pacific/Auckland", "UTC"
]

def get_predefined_options(field: str) -> List[str]:
    """Get predefined options for a specific field."""
    return PREDEFINED_OPTIONS.get(field, [])

def get_timezone_options() -> List[str]:
    """Get timezone options."""
    return TIMEZONE_OPTIONS

def validate_personalization_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate personalization data structure and content."""
    errors = []
    
    # Required fields and their expected types
    required_string_fields = ["date_of_birth", "timezone"]
    required_list_fields = [
        "pronouns", "health_conditions", "medications_treatments", "reminders_needed",
        "loved_ones", "interests", "activities_for_encouragement", "notes_for_ai", "goals"
    ]
    
    # Check string fields
    for field in required_string_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], str):
            errors.append(f"Field {field} must be a string")
    
    # Check list fields
    for field in required_list_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], list):
            errors.append(f"Field {field} must be a list")
    
    # Validate date_of_birth format if provided
    if data.get("date_of_birth"):
        try:
            datetime.strptime(data["date_of_birth"], "%Y-%m-%d")
        except ValueError:
            errors.append("date_of_birth must be in YYYY-MM-DD format")
    
    # Validate loved_ones structure
    loved_ones = data.get("loved_ones", [])
    for i, loved_one in enumerate(loved_ones):
        if not isinstance(loved_one, dict):
            errors.append(f"loved_one at index {i} must be a dictionary")
            continue
        if "name" not in loved_one:
            errors.append(f"loved_one at index {i} missing required 'name' field")
        if "type" not in loved_one:
            errors.append(f"loved_one at index {i} missing required 'type' field")
    
    return len(errors) == 0, errors 