import pytest
import os
import core.config
from core.user_data_handlers import get_user_data
import logging

logger = logging.getLogger("mhm_tests")

def test_debug_file_paths(mock_user_data):
    """Debug test to check if the issue is with file paths."""
    user_id = mock_user_data['user_id']
    
    logger.debug(f"User ID: {user_id}")
    logger.debug(f"User directory: {mock_user_data['user_dir']}")
    logger.debug(f"Core config USER_INFO_DIR_PATH: {core.config.USER_INFO_DIR_PATH}")
    
    # Check if user directory exists
    logger.debug(f"User directory exists: {os.path.exists(mock_user_data['user_dir'])}")
    
    # Check if account.json exists
    account_file = os.path.join(mock_user_data['user_dir'], 'account.json')
    logger.debug(f"Account file: {account_file}")
    logger.debug(f"Account file exists: {os.path.exists(account_file)}")
    
    # Check if the user directory is in the right place
    expected_user_dir = os.path.join(core.config.USER_INFO_DIR_PATH, user_id)
    logger.debug(f"Expected user directory: {expected_user_dir}")
    logger.debug(f"Expected user directory exists: {os.path.exists(expected_user_dir)}")
    
    # List contents of USER_INFO_DIR_PATH
    if os.path.exists(core.config.USER_INFO_DIR_PATH):
        logger.debug(f"Contents of USER_INFO_DIR_PATH: {os.listdir(core.config.USER_INFO_DIR_PATH)}")
    
    # Check if the paths match
    logger.debug(f"Paths match: {mock_user_data['user_dir'] == expected_user_dir}")
    
    # Try to get user data
    result = get_user_data(user_id, 'account')
    logger.debug(f"get_user_data result: {result}")
    
    # Check if the account file is readable
    if os.path.exists(account_file):
        try:
            with open(account_file, 'r') as f:
                content = f.read()
                logger.debug(f"Account file content length: {len(content)}")
                logger.debug(f"Account file content preview: {content[:200]}...")
        except Exception as e:
            logger.error(f"Error reading account file: {e}")
    
    assert True  # Always pass for debugging
