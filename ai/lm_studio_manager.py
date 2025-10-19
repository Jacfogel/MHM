"""
LM Studio Status Detection Module

This module provides status detection for LM Studio:
- Check if LM Studio server is running
- Check if models are loaded
- Monitor connection status
"""

import subprocess
import requests

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import (
    LM_STUDIO_BASE_URL, 
    LM_STUDIO_API_KEY, 
    LM_STUDIO_MODEL,
    AI_CONNECTION_TEST_TIMEOUT
)

logger = get_component_logger('ai')

class LMStudioManager:
    """Detects LM Studio status and model availability"""
    
    def __init__(self):
        """Initialize LM Studio status detector"""
        self.is_running = False
        self.model_loaded = False
        
    
    @handle_errors("checking if LM Studio is running", default_return=False)
    def is_lm_studio_running(self) -> bool:
        """Check if LM Studio process is running"""
        try:
            # Check for LM Studio process
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq LM Studio.exe"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "LM Studio.exe" in result.stdout:
                logger.debug("LM Studio process is running")
                return True
            else:
                logger.debug("LM Studio process not found")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking LM Studio process: {e}")
            return False
    
    @handle_errors("checking LM Studio server status", default_return=False)
    def is_server_responding(self) -> bool:
        """Check if LM Studio server is responding on the configured port"""
        try:
            response = requests.get(
                f"{LM_STUDIO_BASE_URL}/models",
                headers={"Authorization": f"Bearer {LM_STUDIO_API_KEY}"},
                timeout=AI_CONNECTION_TEST_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.debug("LM Studio server is responding")
                return True
            else:
                logger.warning(f"LM Studio server returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.debug(f"LM Studio server not responding: {e}")
            return False
    
    @handle_errors("checking if model is loaded", default_return=False)
    def is_model_loaded(self) -> bool:
        """Check if the configured model is actually loaded (not just available) in LM Studio"""
        try:
            # First check if server is responding
            if not self.is_server_responding():
                logger.debug("LM Studio server not responding")
                return False
            
            # Try to make a simple completion request to test if a model is actually loaded
            # This is more reliable than just checking the models list
            try:
                test_payload = {
                    "model": LM_STUDIO_MODEL,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "temperature": 0.1
                }
                
                response = requests.post(
                    f"{LM_STUDIO_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=test_payload,
                    timeout=5  # Short timeout for quick test
                )
                
                if response.status_code == 200:
                    logger.info(f"Model {LM_STUDIO_MODEL} is loaded and responding")
                    return True
                elif response.status_code == 404:
                    logger.debug(f"Model {LM_STUDIO_MODEL} not found")
                    return False
                else:
                    logger.debug(f"Model test returned status {response.status_code}")
                    return False
                    
            except requests.exceptions.Timeout:
                logger.debug("Model test timed out - model may not be loaded")
                return False
            except Exception as e:
                logger.debug(f"Model test failed: {e}")
                return False
                
        except Exception as e:
            logger.debug(f"Error checking model status: {e}")
            return False
    
    
    
    @handle_errors("loading model automatically", default_return=False)
    def load_model_automatically(self) -> bool:
        """Automatically load the configured model if server is running but no model is loaded"""
        logger.info("Attempting to automatically load model...")
        
        # Check if server is responding
        if not self.is_server_responding():
            logger.warning("LM Studio server not responding - cannot load model")
            return False
        
        # Check if model is already loaded
        if self.is_model_loaded():
            logger.info("Model is already loaded")
            return True
        
        try:
            logger.info(f"Automatically loading model: {LM_STUDIO_MODEL}")
            
            # Make a simple completion request to trigger model loading
            # This is the same technique that worked when we tested it
            test_payload = {
                "model": LM_STUDIO_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{LM_STUDIO_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=test_payload,
                timeout=30  # Longer timeout for model loading
            )
            
            if response.status_code == 200:
                logger.info(f"Model {LM_STUDIO_MODEL} loaded successfully")
                return True
            else:
                logger.warning(f"Failed to load model: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("Model loading timed out - model may still be loading")
            return False
        except Exception as e:
            logger.error(f"Error loading model automatically: {e}")
            return False

    @handle_errors("checking LM Studio readiness", default_return=False)
    def is_ready(self) -> bool:
        """Check if LM Studio is ready (server running and model loaded)"""
        logger.debug("Checking LM Studio readiness...")
        
        # Check if server is responding
        if not self.is_server_responding():
            logger.debug("LM Studio server not responding")
            return False
        
        # Check if model is loaded
        if self.is_model_loaded():
            logger.debug("LM Studio is ready")
            return True
        
        # Server is running but no model loaded - try to load automatically
        logger.info("Server running but no model loaded - attempting automatic loading")
        if self.load_model_automatically():
            logger.info("Model loaded automatically")
            return True
        else:
            logger.warning("Failed to load model automatically")
            return False
    

# Global instance
_lm_studio_manager = None

def get_lm_studio_manager() -> LMStudioManager:
    """Get the global LM Studio manager instance"""
    global _lm_studio_manager
    if _lm_studio_manager is None:
        _lm_studio_manager = LMStudioManager()
    return _lm_studio_manager

@handle_errors("checking LM Studio status", default_return=False)
def is_lm_studio_ready() -> bool:
    """Check if LM Studio is ready for AI features"""
    manager = get_lm_studio_manager()
    return manager.is_ready()

@handle_errors("ensuring LM Studio is ready", default_return=False)
def ensure_lm_studio_ready() -> bool:
    """Ensure LM Studio is ready, attempting automatic model loading if needed"""
    manager = get_lm_studio_manager()
    return manager.is_ready()
