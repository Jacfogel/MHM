#!/usr/bin/env python3

from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_internal_username
from core.user_data_handlers import get_user_data

def test_user_creation():
    print("Testing user creation...")
    
    # Test basic user creation
    success = TestUserFactory.create_basic_user('test_debug_user')
    print(f"Creation success: {success}")
    
    # Check if user was found
    user_id = get_user_id_by_internal_username('test_debug_user')
    print(f"Found user_id: {user_id}")
    
    if user_id:
        # Load user data
        data = get_user_data(user_id)
        print(f"Data keys: {list(data.keys()) if data else None}")
        
        if data:
            print(f"Has account: {'account' in data}")
            print(f"Has preferences: {'preferences' in data}")
            print(f"Has context: {'context' in data}")
            
            if 'account' in data:
                print(f"Account features: {data['account'].get('features', {})}")
            if 'preferences' in data:
                print(f"Preferences channel: {data['preferences'].get('channel', {})}")
        else:
            print("No data loaded")
    else:
        print("User not found")

if __name__ == "__main__":
    test_user_creation() 