#!/usr/bin/env python3
"""
Simple script to rebuild the user index after directory cleanup.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.user_data_manager import rebuild_user_index
from core.logger import setup_logging, get_logger

def main():
    """Rebuild the user index."""
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting user index rebuild...")
    
    try:
        success = rebuild_user_index()
        if success:
            logger.info("✅ User index rebuilt successfully!")
        else:
            logger.error("❌ Failed to rebuild user index")
            return 1
    except Exception as e:
        logger.error(f"❌ Error rebuilding user index: {e}")
        return 1
    
    logger.info("User index rebuild completed!")
    return 0

if __name__ == "__main__":
    exit(main()) 