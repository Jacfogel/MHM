"""
Presets and options: PREDEFINED_OPTIONS, get_predefined_options, get_timezone_options.
"""

import json
from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger("main")

PREDEFINED_OPTIONS = {
    "gender_identity": [
        "Male",
        "Female",
        "Non-binary",
        "Genderfluid",
        "Agender",
        "Bigender",
        "Demiboy",
        "Demigirl",
        "Genderqueer",
        "Two-spirit",
        "Other",
        "Prefer not to say",
    ],
    "health_conditions": [
        "ADHD",
        "Anxiety",
        "Depression",
        "Bipolar Disorder",
        "PTSD",
        "OCD",
        "Autism",
        "Chronic Pain",
        "Diabetes",
        "Asthma",
        "Sleep Disorders",
        "Eating Disorders",
        "Substance Use Disorder",
    ],
    "medications_treatments": [
        "Antidepressant",
        "Anti-anxiety medication",
        "Stimulant for ADHD",
        "Mood stabilizer",
        "Antipsychotic",
        "Sleep medication",
        "Therapy",
        "Counseling",
        "Support groups",
        "Exercise",
        "Meditation",
        "Yoga",
        "CPAP",
        "Inhaler",
        "Insulin",
    ],
    "reminders_needed": [
        "medications_treatments",
        "hydration",
        "movement/stretch breaks",
        "healthy meals/snacks",
        "mental health check-ins",
        "appointments",
        "exercise",
        "sleep schedule",
        "self-care activities",
    ],
    "loved_one_types": [
        "human",
        "dog",
        "cat",
        "bird",
        "fish",
        "reptile",
        "horse",
        "rabbit",
        "hamster",
        "guinea pig",
        "ferret",
        "other",
    ],
    "relationship_types": [
        "partner",
        "spouse",
        "parent",
        "child",
        "sibling",
        "friend",
        "roommate",
        "colleague",
        "therapist",
        "doctor",
        "teacher",
    ],
    "interests": [
        "Reading",
        "Writing",
        "Gaming",
        "Music",
        "Art",
        "Cooking",
        "Baking",
        "Gardening",
        "Hiking",
        "Swimming",
        "Running",
        "Yoga",
        "Meditation",
        "Photography",
        "Crafts",
        "Knitting",
        "Painting",
        "Drawing",
        "Sewing",
        "Woodworking",
        "Programming",
        "Math",
        "Science",
        "History",
        "Languages",
        "Travel",
    ],
    "activities_for_encouragement": [
        "exercise",
        "healthy eating",
        "sleep hygiene",
        "social activities",
        "hobbies",
        "work/projects",
        "self-care",
        "therapy appointments",
        "medication adherence",
        "stress management",
    ],
}

TIMEZONE_OPTIONS = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Regina",
    "America/Toronto",
    "America/Vancouver",
    "America/Edmonton",
    "America/Port_of_Spain",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Rome",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Kolkata",
    "Australia/Sydney",
    "Pacific/Auckland",
    "UTC",
]

_PRESETS_CACHE: dict | None = None


@handle_errors("loading presets JSON", default_return=PREDEFINED_OPTIONS)
def _load_presets_json() -> dict:
    """Load presets from resources/presets.json (cached)."""
    global _PRESETS_CACHE
    if _PRESETS_CACHE is not None:
        return _PRESETS_CACHE
    presets_path = Path(__file__).parent.parent / "resources" / "presets.json"
    try:
        with open(presets_path, encoding="utf-8") as f:
            _PRESETS_CACHE = json.load(f)
    except FileNotFoundError:
        logger.warning("presets.json not found - falling back to hard-coded options")
        _PRESETS_CACHE = PREDEFINED_OPTIONS
    return _PRESETS_CACHE


@handle_errors("getting predefined options", default_return=[])
def get_predefined_options(field: str) -> list:
    """Return predefined options for a personalization field."""
    presets = _load_presets_json()
    return presets.get(field, [])


@handle_errors("getting timezone options", default_return=[])
def get_timezone_options() -> list:
    """Get timezone options."""
    try:
        import pytz
        return pytz.all_timezones
    except ImportError:
        return TIMEZONE_OPTIONS
