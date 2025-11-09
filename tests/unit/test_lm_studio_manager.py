"""
LM Studio Manager Tests

Tests for ai/lm_studio_manager.py:
- LMStudioManager class
- Process detection
- Server status checking
- Model loading detection
- Automatic model loading
- Readiness checking
- Factory functions
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import subprocess
import requests

from ai.lm_studio_manager import (
    LMStudioManager,
    get_lm_studio_manager,
    is_lm_studio_ready,
    ensure_lm_studio_ready
)


class TestLMStudioManager:
    """Test LMStudioManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create an LMStudioManager instance"""
        return LMStudioManager()
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_initialization(self, manager):
        """Test: LMStudioManager initializes correctly"""
        # Assert
        assert manager.is_running is False, "Should initialize is_running to False"
        assert manager.model_loaded is False, "Should initialize model_loaded to False"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_running_process_found(self, manager):
        """Test: is_lm_studio_running returns True when process found"""
        # Arrange
        mock_result = Mock()
        mock_result.stdout = "LM Studio.exe    12345   1234   5678"
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            # Act
            result = manager.is_lm_studio_running()
            
            # Assert
            assert result is True, "Should return True when process found"
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert call_args[0] == ["tasklist", "/FI", "IMAGENAME eq LM Studio.exe"], "Should call tasklist with correct arguments"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_running_process_not_found(self, manager):
        """Test: is_lm_studio_running returns False when process not found"""
        # Arrange
        mock_result = Mock()
        mock_result.stdout = "No tasks are running which match the specified criteria."
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            # Act
            result = manager.is_lm_studio_running()
            
            # Assert
            assert result is False, "Should return False when process not found"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_running_subprocess_error(self, manager):
        """Test: is_lm_studio_running handles subprocess errors gracefully"""
        # Arrange
        with patch('subprocess.run', side_effect=Exception("Subprocess error")):
            # Act
            result = manager.is_lm_studio_running()
            
            # Assert
            assert result is False, "Should return False on error"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_running_timeout(self, manager):
        """Test: is_lm_studio_running handles timeout gracefully"""
        # Arrange
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("tasklist", 10)):
            # Act
            result = manager.is_lm_studio_running()
            
            # Assert
            assert result is False, "Should return False on timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_server_responding_success(self, manager):
        """Test: is_server_responding returns True when server responds"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                    with patch('ai.lm_studio_manager.AI_CONNECTION_TEST_TIMEOUT', 5):
                        # Act
                        result = manager.is_server_responding()
                        
                        # Assert
                        assert result is True, "Should return True when server responds"
                        mock_get.assert_called_once()
                        call_kwargs = mock_get.call_args[1]
                        assert 'headers' in call_kwargs, "Should include headers"
                        assert 'timeout' in call_kwargs, "Should include timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_server_responding_non_200(self, manager):
        """Test: is_server_responding returns False for non-200 status"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('requests.get', return_value=mock_response):
            with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                    with patch('ai.lm_studio_manager.AI_CONNECTION_TEST_TIMEOUT', 5):
                        # Act
                        result = manager.is_server_responding()
                        
                        # Assert
                        assert result is False, "Should return False for non-200 status"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_server_responding_connection_error(self, manager):
        """Test: is_server_responding handles connection errors gracefully"""
        # Arrange
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Connection error")):
            with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                    with patch('ai.lm_studio_manager.AI_CONNECTION_TEST_TIMEOUT', 5):
                        # Act
                        result = manager.is_server_responding()
                        
                        # Assert
                        assert result is False, "Should return False on connection error"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_server_responding_timeout(self, manager):
        """Test: is_server_responding handles timeout gracefully"""
        # Arrange
        with patch('requests.get', side_effect=requests.exceptions.Timeout("Timeout")):
            with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                    with patch('ai.lm_studio_manager.AI_CONNECTION_TEST_TIMEOUT', 5):
                        # Act
                        result = manager.is_server_responding()
                        
                        # Assert
                        assert result is False, "Should return False on timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_model_loaded_server_not_responding(self, manager):
        """Test: is_model_loaded returns False when server not responding"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=False):
            # Act
            result = manager.is_model_loaded()
            
            # Assert
            assert result is False, "Should return False when server not responding"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_model_loaded_success(self, manager):
        """Test: is_model_loaded returns True when model is loaded"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch('requests.post', return_value=mock_response) as mock_post:
                with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                    with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                            # Act
                            result = manager.is_model_loaded()
                            
                            # Assert
                            assert result is True, "Should return True when model is loaded"
                            mock_post.assert_called_once()
                            call_kwargs = mock_post.call_args[1]
                            assert 'json' in call_kwargs, "Should include JSON payload"
                            assert 'timeout' in call_kwargs, "Should include timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_model_loaded_model_not_found(self, manager):
        """Test: is_model_loaded returns False when model not found"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch('requests.post', return_value=mock_response):
                with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                    with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                            # Act
                            result = manager.is_model_loaded()
                            
                            # Assert
                            assert result is False, "Should return False when model not found"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_model_loaded_timeout(self, manager):
        """Test: is_model_loaded handles timeout gracefully"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch('requests.post', side_effect=requests.exceptions.Timeout("Timeout")):
                with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                    with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                            # Act
                            result = manager.is_model_loaded()
                            
                            # Assert
                            assert result is False, "Should return False on timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_model_loaded_other_error(self, manager):
        """Test: is_model_loaded handles other errors gracefully"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch('requests.post', side_effect=Exception("Test error")):
                with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                    with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                            # Act
                            result = manager.is_model_loaded()
                            
                            # Assert
                            assert result is False, "Should return False on error"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_server_not_responding(self, manager):
        """Test: load_model_automatically returns False when server not responding"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=False):
            # Act
            result = manager.load_model_automatically()
            
            # Assert
            assert result is False, "Should return False when server not responding"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_already_loaded(self, manager):
        """Test: load_model_automatically returns True when model already loaded"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=True):
                # Act
                result = manager.load_model_automatically()
                
                # Assert
                assert result is True, "Should return True when model already loaded"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_success(self, manager):
        """Test: load_model_automatically loads model successfully"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch('requests.post', return_value=mock_response) as mock_post:
                    with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                            with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                                # Act
                                result = manager.load_model_automatically()
                                
                                # Assert
                                assert result is True, "Should return True on success"
                                mock_post.assert_called_once()
                                call_kwargs = mock_post.call_args[1]
                                assert 'json' in call_kwargs, "Should include JSON payload"
                                assert call_kwargs['timeout'] == 30, "Should use longer timeout for loading"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_failure(self, manager):
        """Test: load_model_automatically returns False on failure"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch('requests.post', return_value=mock_response):
                    with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                            with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                                # Act
                                result = manager.load_model_automatically()
                                
                                # Assert
                                assert result is False, "Should return False on failure"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_timeout(self, manager):
        """Test: load_model_automatically handles timeout gracefully"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch('requests.post', side_effect=requests.exceptions.Timeout("Timeout")):
                    with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                            with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                                # Act
                                result = manager.load_model_automatically()
                                
                                # Assert
                                assert result is False, "Should return False on timeout"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_load_model_automatically_error(self, manager):
        """Test: load_model_automatically handles errors gracefully"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch('requests.post', side_effect=Exception("Test error")):
                    with patch('ai.lm_studio_manager.LM_STUDIO_BASE_URL', 'http://localhost:1234'):
                        with patch('ai.lm_studio_manager.LM_STUDIO_API_KEY', 'test_key'):
                            with patch('ai.lm_studio_manager.LM_STUDIO_MODEL', 'test_model'):
                                # Act
                                result = manager.load_model_automatically()
                                
                                # Assert
                                assert result is False, "Should return False on error"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_ready_server_not_responding(self, manager):
        """Test: is_ready returns False when server not responding"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=False):
            # Act
            result = manager.is_ready()
            
            # Assert
            assert result is False, "Should return False when server not responding"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_ready_model_loaded(self, manager):
        """Test: is_ready returns True when model is loaded"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=True):
                # Act
                result = manager.is_ready()
                
                # Assert
                assert result is True, "Should return True when model is loaded"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_ready_auto_load_success(self, manager):
        """Test: is_ready attempts auto-load and returns True on success"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch.object(manager, 'load_model_automatically', return_value=True):
                    # Act
                    result = manager.is_ready()
                    
                    # Assert
                    assert result is True, "Should return True when auto-load succeeds"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_ready_auto_load_failure(self, manager):
        """Test: is_ready returns False when auto-load fails"""
        # Arrange
        with patch.object(manager, 'is_server_responding', return_value=True):
            with patch.object(manager, 'is_model_loaded', return_value=False):
                with patch.object(manager, 'load_model_automatically', return_value=False):
                    # Act
                    result = manager.is_ready()
                    
                    # Assert
                    assert result is False, "Should return False when auto-load fails"


class TestGetLMStudioManager:
    """Test get_lm_studio_manager factory function"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_get_lm_studio_manager_returns_instance(self):
        """Test: get_lm_studio_manager returns LMStudioManager instance"""
        # Act
        manager = get_lm_studio_manager()
        
        # Assert
        assert isinstance(manager, LMStudioManager), "Should return LMStudioManager instance"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_get_lm_studio_manager_singleton(self):
        """Test: get_lm_studio_manager returns same instance on multiple calls"""
        # Act
        manager1 = get_lm_studio_manager()
        manager2 = get_lm_studio_manager()
        
        # Assert
        assert manager1 is manager2, "Should return same instance (singleton)"
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_get_lm_studio_manager_resets_on_none(self):
        """Test: get_lm_studio_manager creates new instance if global is None"""
        # Arrange
        import ai.lm_studio_manager
        original_manager = ai.lm_studio_manager._lm_studio_manager
        ai.lm_studio_manager._lm_studio_manager = None
        
        try:
            # Act
            manager = get_lm_studio_manager()
            
            # Assert
            assert isinstance(manager, LMStudioManager), "Should create new instance"
        finally:
            # Restore
            ai.lm_studio_manager._lm_studio_manager = original_manager


class TestIsLMStudioReady:
    """Test is_lm_studio_ready function"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_ready_true(self):
        """Test: is_lm_studio_ready returns True when ready"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = True
        
        with patch('ai.lm_studio_manager.get_lm_studio_manager', return_value=mock_manager):
            # Act
            result = is_lm_studio_ready()
            
            # Assert
            assert result is True, "Should return True when ready"
            mock_manager.is_ready.assert_called_once()
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_is_lm_studio_ready_false(self):
        """Test: is_lm_studio_ready returns False when not ready"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = False
        
        with patch('ai.lm_studio_manager.get_lm_studio_manager', return_value=mock_manager):
            # Act
            result = is_lm_studio_ready()
            
            # Assert
            assert result is False, "Should return False when not ready"


class TestEnsureLMStudioReady:
    """Test ensure_lm_studio_ready function"""
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_ensure_lm_studio_ready_true(self):
        """Test: ensure_lm_studio_ready returns True when ready"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = True
        
        with patch('ai.lm_studio_manager.get_lm_studio_manager', return_value=mock_manager):
            # Act
            result = ensure_lm_studio_ready()
            
            # Assert
            assert result is True, "Should return True when ready"
            mock_manager.is_ready.assert_called_once()
    
    @pytest.mark.ai
    @pytest.mark.unit
    def test_ensure_lm_studio_ready_false(self):
        """Test: ensure_lm_studio_ready returns False when not ready"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = False
        
        with patch('ai.lm_studio_manager.get_lm_studio_manager', return_value=mock_manager):
            # Act
            result = ensure_lm_studio_ready()
            
            # Assert
            assert result is False, "Should return False when not ready"

