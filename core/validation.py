"""
Validation utilities for MHM.
Contains functions for validating data formats and text processing.
"""

import re
from core.logger import get_logger
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

@handle_errors("validating email", default_return=False)
def is_valid_email(email):
    """Validate email format"""
    if not email:
        return False
    
    # Simple email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@handle_errors("validating phone", default_return=False)
def is_valid_phone(phone):
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove common separators and check for digits
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    return cleaned.isdigit() and len(cleaned) >= 10

@handle_errors("converting to title case", default_return="")
def title_case(text: str) -> str:
    """Convert text to title case, handling special cases"""
    if not text:
        return ""
    
    # Handle common abbreviations and special cases
    text = text.lower()
    
    # Common abbreviations that should stay lowercase
    abbreviations = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'is', 'it', 'of', 'on', 'or', 'the', 'to', 'up', 'via']
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # First word, last word, or not in abbreviations list should be capitalized
        if i == 0 or i == len(words) - 1 or word not in abbreviations:
            result.append(word.capitalize())
        else:
            result.append(word)
    
    return ' '.join(result) 