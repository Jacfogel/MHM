"""
Test fixture for false negative detection.

This file contains known issues that analysis tools should detect:
1. Function missing error handling decorator (should be flagged)
2. Function missing docstring (should be flagged)
"""

def process_user_data(user_id, data):
    """Process user data with proper error handling."""
    # This function has try-except catching generic Exception - should be flagged as Phase 1 candidate
    try:
        result = data['value']
        return result * 2
    except Exception:
        return None

def calculate_total(items):
    # This function is missing a docstring - should be flagged
    total = 0
    for item in items:
        total += item.get('price', 0)
    return total

def fetch_external_data(url):
    """Fetch external data - missing error handling."""
    # This function has no error handling at all - should be flagged
    import requests
    response = requests.get(url)
    return response.json()

def simple_utility(value):
    """Simple utility function."""
    # This function is simple and may not need error handling
    return value.strip().lower()

