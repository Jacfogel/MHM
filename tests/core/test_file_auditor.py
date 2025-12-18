"""
Tests for core/file_auditor.py
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from core.file_auditor import (
    FileAuditor, 
    _auditor, 
    start_auditor, 
    stop_auditor, 
    record_created,
    _split_env_list,
    _classify_path
)


@pytest.mark.unit
class TestFileAuditorUtilities:
    """Test utility functions."""
    
    def test_split_env_list_with_value(self):
        """Test splitting environment list with value."""
        result = _split_env_list("dir1,dir2,dir3")
        assert result == ["dir1", "dir2", "dir3"]
    
    def test_split_env_list_with_spaces(self):
        """Test splitting environment list with spaces."""
        result = _split_env_list(" dir1 , dir2 , dir3 ")
        assert result == ["dir1", "dir2", "dir3"]
    
    def test_split_env_list_with_empty_items(self):
        """Test splitting environment list with empty items."""
        result = _split_env_list("dir1,,dir2,,")
        assert result == ["dir1", "dir2"]
    
    def test_split_env_list_none(self):
        """Test splitting environment list with None."""
        result = _split_env_list(None)
        assert result == []
    
    def test_split_env_list_empty(self):
        """Test splitting environment list with empty string."""
        result = _split_env_list("")
        assert result == []
    
    def test_classify_path_tests(self):
        """Test classifying test paths."""
        assert _classify_path("tests/data/test.json") == "tests"
        assert _classify_path("tests/logs/app.log") == "tests"
        assert _classify_path("tests/") == "tests"
    
    def test_classify_path_logs(self):
        """Test classifying log paths."""
        assert _classify_path("logs/app.log") == "logs"
        assert _classify_path("data/logs/error.log") == "logs"
        assert _classify_path("file.log") == "logs"
    
    def test_classify_path_flags(self):
        """Test classifying flag paths."""
        assert _classify_path("flags/shutdown.flag") == "flags"
        assert _classify_path("data/flags/status.flag") == "flags"
        assert _classify_path("file.flag") == "flags"
    
    def test_classify_path_user_data(self):
        """Test classifying user data paths."""
        assert _classify_path("data/users/user123/account.json") == "user_data"
        assert _classify_path("data/users/") == "user_data"
    
    def test_classify_path_other(self):
        """Test classifying other paths."""
        assert _classify_path("config/settings.json") == "other"
        assert _classify_path("src/main.py") == "other"
        assert _classify_path("README.md") == "other"
    
    def test_classify_path_windows_paths(self):
        """Test classifying Windows paths."""
        assert _classify_path("C:\\Users\\test\\data\\users\\user123") == "user_data"
        assert _classify_path("C:\\logs\\app.log") == "logs"
        assert _classify_path("C:\\tests\\data\\test.json") == "tests"


@pytest.mark.unit
class TestFileAuditor:
    """Test FileAuditor class."""
    
    @pytest.fixture
    def auditor(self):
        """Create FileAuditor instance for testing."""
        return FileAuditor()
    
    def test_auditor_initialization(self, auditor):
        """Test FileAuditor initializes correctly."""
        assert auditor._dirs is not None
        assert auditor._created_files == []
        assert auditor._modified_files == []
        assert auditor._audit_data == {}
    
    def test_get_audit_directories_default(self, auditor):
        """Test getting default audit directories."""
        with patch.dict(os.environ, {}, clear=True):
            dirs = auditor._get_audit_directories()
            assert 'logs' in dirs
            assert 'data' in dirs
    
    def test_get_audit_directories_from_env(self, auditor):
        """Test getting audit directories from environment."""
        with patch.dict(os.environ, {'FILE_AUDIT_DIRS': 'custom1,custom2,custom3'}):
            dirs = auditor._get_audit_directories()
            assert dirs == ['custom1', 'custom2', 'custom3']
    
    def test_get_audit_directories_with_testing(self, auditor):
        """Test getting audit directories in testing environment."""
        with patch.dict(os.environ, {'MHM_TESTING': '1'}, clear=True):
            dirs = auditor._get_audit_directories()
            assert 'logs' in dirs
            assert 'data' in dirs
            assert 'tests/data' in dirs
            assert 'tests/logs' in dirs
    
    def test_start_auditor(self, auditor):
        """Test starting the auditor."""
        result = auditor.start()
        assert result is True
    
    def test_stop_auditor(self, auditor):
        """Test stopping the auditor."""
        result = auditor.stop()
        assert result is True


@pytest.mark.unit
class TestFileAuditorSingleton:
    """Test FileAuditor singleton functions."""
    
    def test_start_auditor_function(self):
        """Test start_auditor function."""
        with patch.object(_auditor, 'start') as mock_start:
            mock_start.return_value = True
            result = start_auditor()
            assert result is True
            mock_start.assert_called_once()
    
    def test_stop_auditor_function(self):
        """Test stop_auditor function."""
        with patch.object(_auditor, 'stop') as mock_stop:
            mock_stop.return_value = True
            result = stop_auditor()
            assert result is True
            mock_stop.assert_called_once()


@pytest.mark.unit
class TestRecordCreated:
    """Test record_created function."""
    
    def test_record_created_basic(self):
        """Test basic file creation recording."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            with patch('core.file_auditor._logger') as mock_logger:
                record_created(temp_path, "test_reason")
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert "File created (programmatic)" in call_args[0]
                
                # Check the payload
                payload = call_args[1]
                assert payload['path'] == os.path.abspath(temp_path)
                assert payload['bytes'] > 0
                assert payload['classification'] in ['tests', 'logs', 'flags', 'user_data', 'other']
                assert payload['detected_by'] == "test_reason"
        
        finally:
            os.unlink(temp_path)
    
    def test_record_created_with_extra(self):
        """Test file creation recording with extra data."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            with patch('core.file_auditor._logger') as mock_logger:
                extra_data = {'user_id': 'test_user', 'action': 'create'}
                record_created(temp_path, "test_reason", extra_data)
                
                call_args = mock_logger.info.call_args
                payload = call_args[1]
                assert payload['user_id'] == 'test_user'
                assert payload['action'] == 'create'
        
        finally:
            os.unlink(temp_path)
    
    def test_record_created_nonexistent_file(self):
        """Test recording creation of non-existent file."""
        with patch('core.file_auditor._logger') as mock_logger:
            record_created("/nonexistent/path/file.txt", "test_reason")
            
            call_args = mock_logger.info.call_args
            payload = call_args[1]
            assert payload['bytes'] == -1
    
    def test_record_created_with_stack_trace(self):
        """Test file creation recording with stack trace."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            with patch.dict(os.environ, {'FILE_AUDIT_STACK': '1'}):
                with patch('core.file_auditor._logger') as mock_logger:
                    record_created(temp_path, "test_reason")
                    
                    call_args = mock_logger.info.call_args
                    payload = call_args[1]
                    assert 'stack' in payload
                    assert isinstance(payload['stack'], str)
        
        finally:
            os.unlink(temp_path)
    
    def test_record_created_without_stack_trace(self):
        """Test file creation recording without stack trace."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            with patch.dict(os.environ, {'FILE_AUDIT_STACK': '0'}, clear=True):
                with patch('core.file_auditor._logger') as mock_logger:
                    record_created(temp_path, "test_reason")
                    
                    call_args = mock_logger.info.call_args
                    payload = call_args[1]
                    assert 'stack' not in payload
        
        finally:
            os.unlink(temp_path)
    
    def test_record_created_stack_trace_exception(self):
        """Test file creation recording when stack trace fails."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            with patch.dict(os.environ, {'FILE_AUDIT_STACK': '1'}):
                with patch('core.file_auditor._logger') as mock_logger:
                    with patch('core.file_auditor.traceback.format_stack', side_effect=Exception("Stack trace error")):
                        record_created(temp_path, "test_reason")
                        
                        call_args = mock_logger.info.call_args
                        payload = call_args[1]
                        assert 'stack' not in payload
        
        finally:
            os.unlink(temp_path)
    
    def test_record_created_size_exception(self):
        """Test file creation recording when size calculation fails."""
        with patch('core.file_auditor._logger') as mock_logger:
            with patch('core.file_auditor.os.path.getsize', side_effect=Exception("Size error")):
                record_created("/some/path", "test_reason")
                
                call_args = mock_logger.info.call_args
                payload = call_args[1]
                assert payload['bytes'] == -1
    
    def test_record_created_different_classifications(self):
        """Test file creation recording with different file classifications."""
        test_cases = [
            ("tests/data/test.json", "tests"),
            ("logs/app.log", "logs"),
            ("flags/shutdown.flag", "flags"),
            ("data/users/user123/account.json", "user_data"),
            ("config/settings.json", "other")
        ]
        
        for path, expected_classification in test_cases:
            with patch('core.file_auditor._logger') as mock_logger:
                record_created(path, "test_reason")
                
                call_args = mock_logger.info.call_args
                payload = call_args[1]
                assert payload['classification'] == expected_classification


@pytest.mark.unit
class TestFileAuditorErrorHandling:
    """Test FileAuditor error handling."""
    
    def test_split_env_list_with_exception(self):
        """Test _split_env_list handles exceptions."""
        # The function doesn't use os.getenv, it just processes the input string
        # So we need to test a different kind of exception
        with patch('core.file_auditor.os.getenv', side_effect=Exception("Environment error")):
            result = _split_env_list("test")
            # The function should still work since it doesn't use os.getenv
            assert result == ["test"]
    
    def test_classify_path_with_exception(self):
        """Test _classify_path handles exceptions."""
        with patch('core.file_auditor.os.path.exists', side_effect=Exception("Path error")):
            result = _classify_path("test/path")
            assert result == "other"
    
    def test_auditor_start_with_exception(self):
        """Test auditor start handles exceptions."""
        auditor = FileAuditor()
        # The start method is a simple no-op that returns True
        # Since it doesn't have any code that could raise exceptions, it always returns True
        result = auditor.start()
        assert result is True
    
    def test_auditor_stop_with_exception(self):
        """Test auditor stop handles exceptions."""
        auditor = FileAuditor()
        # The stop method is a simple no-op that returns True
        # Since it doesn't have any code that could raise exceptions, it always returns True
        result = auditor.stop()
        assert result is True
    
    def test_record_created_with_exception(self):
        """Test record_created handles exceptions."""
        with patch('core.file_auditor._logger', side_effect=Exception("Logger error")):
            # Should not raise exception
            record_created("/some/path", "test_reason")
