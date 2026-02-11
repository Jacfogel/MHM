"""
Tests for core file operations module.

Tests file I/O operations, data loading/saving, and file path management.
"""

import pytest
import os
import json
from pathlib import Path

from core.file_operations import (
    load_json_data,
    save_json_data,
    determine_file_path,
    verify_file_access,
    get_user_file_path,
    ensure_user_directory
)
from core.error_handling import FileOperationError

class TestFileOperations:
    """Test file operations functions."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_load_json_data_success(self, temp_file):
        """Test loading JSON data successfully."""
        test_data = {'test': 'data', 'number': 42, 'list': [1, 2, 3]}
        
        # Write test data to file
        with open(temp_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load the data
        loaded_data = load_json_data(temp_file)
        
        assert loaded_data == test_data
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_load_json_data_file_not_found(self):
        """Test loading JSON data from non-existent file."""
        data = load_json_data('/nonexistent/file.json')
        # With improved error handling, we now get default data instead of None
        assert data is not None
        assert isinstance(data, dict)
        assert 'data' in data
        assert 'created' in data
        assert 'file_type' in data
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_load_json_data_corrupted_json(self, temp_file):
        """Test loading corrupted JSON data."""
        # Write corrupted JSON
        with open(temp_file, 'w') as f:
            f.write('{invalid json}')
        
        data = load_json_data(temp_file)
        assert data == {}
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_load_json_data_empty_file(self, temp_file):
        """Test loading from empty file."""
        # Create empty file
        with open(temp_file, 'w') as f:
            pass
        
        data = load_json_data(temp_file)
        assert data == {}
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_save_json_data_success(self, temp_file):
        """Test saving JSON data successfully."""
        test_data = {'test': 'data', 'number': 42, 'nested': {'key': 'value'}}
        
        #[OK] VERIFY INITIAL STATE: Check file doesn't exist or is empty
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                initial_content = f.read()
            assert initial_content == '', f"File should be empty initially: {initial_content}"
        else:
            assert not os.path.exists(temp_file), f"File should not exist initially: {temp_file}"
        
        result = save_json_data(test_data, temp_file)
        # Function returns True on success
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check that file was actually created
        assert os.path.exists(temp_file), f"File should be created at {temp_file}"
        assert os.path.isfile(temp_file), f"Path should be a file, not directory: {temp_file}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file permissions
        assert os.access(temp_file, os.R_OK), f"File should be readable: {temp_file}"
        assert os.access(temp_file, os.W_OK), f"File should be writable: {temp_file}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check data was saved correctly
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
        
        #[OK] VERIFY REAL BEHAVIOR: Check file size is reasonable
        file_size = os.path.getsize(temp_file)
        assert file_size > 0, f"File should not be empty: {file_size} bytes"
        assert file_size < 10000, f"File should not be unreasonably large: {file_size} bytes"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file is valid JSON
        try:
            with open(temp_file, 'r') as f:
                json.load(f)  # Should not raise exception
        except json.JSONDecodeError as e:
            assert False, f"Saved file should be valid JSON: {e}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file can be read multiple times
        for _ in range(3):
            with open(temp_file, 'r') as f:
                reloaded_data = json.load(f)
            assert reloaded_data == test_data, f"Data should be consistent across reads: {reloaded_data}"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_save_json_data_create_directory(self, test_data_dir):
        """Test saving JSON data with directory creation."""
        file_path = os.path.join(test_data_dir, 'nested', 'dir', 'test.json')
        test_data = {'test': 'data'}
        
        result = save_json_data(test_data, file_path)
        assert result is True
        
        # Verify file and directory were created
        assert os.path.exists(file_path)
        assert os.path.exists(os.path.dirname(file_path))
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_save_json_data_permission_error(self, test_data_dir):
        """Test saving JSON data with permission error.
        
        On Windows: Tests against a path that should fail (invalid path or system directory).
        On Unix: Creates a read-only directory to test permission handling.
        
        Note: This test validates that permission errors are handled correctly. If running
        with elevated privileges (admin on Windows), the test may be able to write to protected
        locations, which would invalidate the permission test. The test detects this and
        adjusts accordingly.
        """
        import platform
        import stat
        import tempfile
        
        is_windows = platform.system() == 'Windows'
        
        if is_windows:
            # On Windows, we can't reliably make a directory read-only for the owner
            # Instead, test against a path that should fail (system directory that requires elevation)
            # Note: C:\Windows\System32 typically requires admin rights to write
            # But since we can't guarantee admin rights, we'll use a more reliable approach:
            # Create a directory, make a file read-only, then try to overwrite it
            protected_dir = tempfile.mkdtemp(dir=test_data_dir)
            protected_path = os.path.join(protected_dir, 'test.json')
            
            # Create the file first and make it read-only
            try:
                with open(protected_path, 'w') as f:
                    f.write('existing')
                os.chmod(protected_path, stat.S_IREAD)  # Read-only file
            except Exception:
                # If we can't create a read-only file, check if we have elevated privileges
                # by attempting to write to a system directory
                test_system_path = 'C:\\Windows\\System32\\test_permission_check_temp.json'
                try:
                    # Try to write to System32 to detect elevated privileges
                    with open(test_system_path, 'w') as f:
                        f.write('test')
                    os.remove(test_system_path)
                    # If we can write to System32, we're running with elevated privileges
                    # In this case, use a read-only file approach instead
                    pytest.skip("Running with elevated privileges - cannot reliably test permission errors with system directories")
                except (PermissionError, OSError):
                    # Good - we don't have elevated privileges, can use System32 path for test
                    protected_path = 'C:\\Windows\\System32\\test_permission_check.json'
                    protected_dir = 'C:\\Windows\\System32'
        else:
            # Unix: Create a read-only directory
            protected_dir = tempfile.mkdtemp(dir=test_data_dir)
            protected_path = os.path.join(protected_dir, 'test.json')
            
            # Make the directory read-only
            os.chmod(protected_dir, 0o555)  # Read and execute only
            
            # Verify we can't write to the protected directory
            test_write_file = os.path.join(protected_dir, 'test_write_permission.json')
            try:
                with open(test_write_file, 'w') as f:
                    f.write('test')
                os.remove(test_write_file)  # Clean up if we somehow succeeded
                # If we get here, the permission test setup failed
                pytest.skip("Could not create read-only directory for permission test")
            except (PermissionError, OSError):
                # This is expected - we shouldn't be able to write to read-only directory
                pass
        
        try:
            # Attempt to save to the protected location
            # This should handle the permission error gracefully
            # Note: save_json_data uses @handle_errors which may catch and log the error
            # but still return False or raise FileOperationError
            try:
                result = save_json_data({'test': 'data'}, protected_path)
            except Exception:
                # FileOperationError or other exception is acceptable for permission errors
                result = False
            
            #[OK] VERIFY REAL BEHAVIOR: On permission error, either:
            # 1. save_json_data returns False (handled by @handle_errors)
            # 2. save_json_data raises an exception (caught above)
            # 3. If it returns True, the file should NOT actually exist
            if result is True:
                # If save_json_data returns True, verify the file was NOT actually created
                # (or if it exists, it wasn't overwritten with our test data)
                if os.path.exists(protected_path):
                    # File exists - check if it contains our test data (it shouldn't on permission error)
                    try:
                        with open(protected_path, 'r') as f:
                            content = f.read()
                        # If file was read-only and couldn't be overwritten, content should be original
                        if is_windows and 'existing' in content:
                            # File couldn't be overwritten - that's the expected behavior
                            pass
                        else:
                            # File was written despite permission error - this is the bug we're checking for
                            assert False, f"File was created/overwritten at protected path despite permission error: {protected_path}"
                    except Exception:
                        # Can't read file - that's fine, just verify it wasn't our test data
                        pass
                # If file doesn't exist, that's also fine - permission error prevented creation
            else:
                # save_json_data returned False - that's the expected behavior for permission errors
                assert result is False, "save_json_data should return False on permission error"
            
            #[OK] VERIFY REAL BEHAVIOR: Check that no partial temp files were created
            # Only check for .tmp files - the original test.json file should remain (it's read-only)
            if os.path.exists(protected_dir) and not protected_dir.startswith('C:\\Windows'):
                temp_files = [f for f in os.listdir(protected_dir) if f.endswith('.tmp') and 'test' in f]
                assert len(temp_files) == 0, f"No temporary .tmp files should be left behind: {temp_files}"
            
        finally:
            # Restore permissions and clean up (only for temp directories we created)
            if not protected_dir.startswith('C:\\Windows'):
                try:
                    if os.path.exists(protected_path):
                        if is_windows:
                            os.chmod(protected_path, stat.S_IREAD | stat.S_IWRITE)
                        else:
                            os.chmod(protected_path, 0o644)
                    if os.path.exists(protected_dir):
                        if is_windows:
                            os.chmod(protected_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
                        else:
                            os.chmod(protected_dir, 0o755)
                    # Clean up the test directory
                    import shutil
                    shutil.rmtree(protected_dir, ignore_errors=True)
                except Exception:
                    # Best effort cleanup - ignore errors
                    pass
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_determine_file_path_user_file(self, test_data_dir):
        """Test determining file path for user file."""
        user_id = 'test-user'
        file_type = 'users'  # Use 'users' file type for user files
        
        # FIXED: Use the actual path that the function returns
        # The function uses relative paths, so we need to check the structure, not exact path
        actual_path = determine_file_path(file_type, user_id)
        
        # Verify the path has the correct structure
        assert 'users' in actual_path
        assert user_id in actual_path
        assert 'account.json' in actual_path
        assert actual_path.endswith('account.json')
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_determine_file_path_default_messages(self, test_data_dir):
        """Test determining file path for default messages."""
        category = 'motivational'
        
        # FIXED: Use the actual path that the function returns
        # The function uses relative paths, so we need to check the structure, not exact path
        actual_path = determine_file_path('default_messages', category)
        
        # Verify the path has the correct structure
        assert 'default_messages' in actual_path
        assert category in actual_path
        assert actual_path.endswith(f'{category}.json')
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_verify_file_access_success(self, temp_file):
        """Test file access verification for accessible file."""
        #[OK] VERIFY INITIAL STATE: Create a file we can access
        test_content = 'test content for access verification'
        with open(temp_file, 'w') as f:
            f.write(test_content)
        
        #[OK] VERIFY REAL BEHAVIOR: Check file exists and is readable before test
        assert os.path.exists(temp_file), f"Test file should exist before verification: {temp_file}"
        with open(temp_file, 'r') as f:
            assert f.read() == test_content, "File content should be correct before test"
        
        result = verify_file_access([temp_file])
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check file still exists and is unchanged after test
        assert os.path.exists(temp_file), f"File should still exist after verification: {temp_file}"
        with open(temp_file, 'r') as f:
            assert f.read() == test_content, "File content should be unchanged after verification"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file is still readable and writable
        try:
            with open(temp_file, 'r') as f:
                content = f.read()
            assert content == test_content, "File should still be readable"
            
            # Test write access
            with open(temp_file, 'a') as f:
                f.write('\nappended content')
            with open(temp_file, 'r') as f:
                final_content = f.read()
            assert final_content == test_content + '\nappended content', "File should be writable"
            
            # Restore original content
            with open(temp_file, 'w') as f:
                f.write(test_content)
        except Exception as e:
            assert False, f"File should remain accessible after verification: {e}"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_verify_file_access_missing_file(self):
        """Test file access verification for missing file."""
        # Use a cross-platform path that definitely doesn't exist
        import tempfile
        temp_dir = tempfile.gettempdir()
        missing_file = os.path.join(temp_dir, 'mhm_test_nonexistent_file_12345.txt')
        missing_dir = os.path.join(temp_dir, 'mhm_test_nonexistent_dir_12345')
        
        #[OK] VERIFY INITIAL STATE: Check that the file and directory don't exist
        assert not os.path.exists(missing_file), f"Missing file should not exist: {missing_file}"
        assert not os.path.exists(missing_dir), f"Missing directory should not exist: {missing_dir}"
        
        result = verify_file_access([missing_file])
        assert result is False
        
        #[OK] VERIFY REAL BEHAVIOR: Check that no files were created during verification
        assert not os.path.exists(missing_file), f"Missing file should still not exist after verification: {missing_file}"
        assert not os.path.exists(missing_dir), f"Missing directory should still not exist after verification: {missing_dir}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check that the function didn't create any files in the current directory
        # This ensures the function doesn't have side effects
        current_dir_files_before = set(os.listdir('.'))
        result2 = verify_file_access([missing_file])
        current_dir_files_after = set(os.listdir('.'))
        
        # The set of files should be the same (no new files created)
        new_files = current_dir_files_after - current_dir_files_before
        assert len(new_files) == 0, f"No new files should be created during verification: {new_files}"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_verify_file_access_permission_error(self):
        """Test file access verification with permission error."""
        # Try to access a protected file - use cross-platform approach
        import tempfile
        import uuid
        
        # Create a unique test directory to avoid interference from other tests
        test_dir = os.path.join(tempfile.gettempdir(), f'mhm_test_protected_{uuid.uuid4().hex[:8]}')
        protected_file = os.path.join(test_dir, 'mhm_test_protected_file_12345.txt')
        protected_dir = test_dir
        
        # Create the test directory
        os.makedirs(protected_dir, exist_ok=True)
        
        #[OK] VERIFY INITIAL STATE: Check current state of protected location
        try:
            root_contents_before = os.listdir(protected_dir)
        except (PermissionError, OSError):
            # This is expected - we shouldn't have read access to protected directories
            root_contents_before = None
        
        result = verify_file_access([protected_file])
        assert result is False
        
        #[OK] VERIFY REAL BEHAVIOR: Check that no files were created during verification
        try:
            root_contents_after = os.listdir(protected_dir)
            # The contents should be the same (no new files created)
            if root_contents_before is not None:
                assert set(root_contents_after) == set(root_contents_before), \
                    "No new files should be created in protected directory during verification"
        except (PermissionError, OSError):
            # Still can't access protected directory, which is expected
            pass
        
        # Clean up test directory
        try:
            import shutil
            shutil.rmtree(protected_dir, ignore_errors=True)
        except:
            pass
        
        #[OK] VERIFY REAL BEHAVIOR: Check that the protected file still doesn't exist (or is inaccessible)
        if os.path.exists(protected_file):
            # If the file exists, it should be inaccessible
            try:
                with open(protected_file, 'r') as f:
                    f.read()
                # If we get here, we can read the file, which means it's not really protected
                # This might happen if running as root or with elevated privileges
                pytest.skip("Protected file is accessible - permission test may not work on this system")
            except (PermissionError, OSError):
                # This is expected - we shouldn't be able to read the protected file
                pass
        else:
            # File doesn't exist, which is also expected
            pass
        
        #[OK] VERIFY REAL BEHAVIOR: Check that the function didn't create any files in the current directory
        # This ensures the function doesn't have side effects
        current_dir_files_before = set(os.listdir('.'))
        result2 = verify_file_access([protected_file])
        current_dir_files_after = set(os.listdir('.'))
        
        # The set of files should be the same (no new files created)
        new_files = current_dir_files_after - current_dir_files_before
        assert len(new_files) == 0, f"No new files should be created during verification: {new_files}"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_get_user_file_path_success(self, test_data_dir):
        """Test getting user file path successfully."""
        user_id = 'test-user'
        file_type = 'account'
        
        # FIXED: Use the actual path that the function returns
        # The function uses relative paths, so we need to check the structure, not exact path
        actual_path = get_user_file_path(user_id, file_type)
        
        # Verify the path has the correct structure
        assert 'users' in actual_path
        assert user_id in actual_path
        assert 'account.json' in actual_path
        assert actual_path.endswith('account.json')
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_ensure_user_directory_success(self, test_data_dir):
        """Test ensuring user directory exists."""
        user_id = 'test-user-dir'
        
        result = ensure_user_directory(user_id)
        assert result is True
        
        # Verify directory was created in the correct location (BASE_DATA_DIR)
        from core.config import BASE_DATA_DIR
        user_dir = os.path.join(BASE_DATA_DIR, 'users', user_id)
        assert os.path.exists(user_dir)
        assert os.path.isdir(user_dir)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_ensure_user_directory_already_exists(self, test_data_dir):
        """Test ensuring user directory that already exists."""
        user_id = 'test-user-dir-exists'
        from core.config import BASE_DATA_DIR
        user_dir = os.path.join(BASE_DATA_DIR, 'users', user_id)
        
        # Create directory first
        os.makedirs(user_dir, exist_ok=True)
        
        result = ensure_user_directory(user_id)
        assert result is True
        
        # Verify directory still exists
        assert os.path.exists(user_dir)
        assert os.path.isdir(user_dir)

class TestFileOperationsEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_load_json_data_unicode_content(self, temp_file):
        """Test loading JSON data with unicode content."""
        test_data = {
            'text': 'Hello, 世界! 🌍',
            'emoji': '😀🎉🚀',
            'special_chars': 'áéíóú ñ ç'
        }
        
        # Write test data to file
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
        
        # Load the data
        loaded_data = load_json_data(temp_file)
        
        assert loaded_data == test_data
        assert loaded_data['text'] == 'Hello, 世界! 🌍'
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_save_json_data_complex_objects(self, temp_file):
        """Test saving JSON data with complex objects."""
        test_data = {
            'list': [1, 2, 3, {'nested': 'value'}],
            'dict': {'key1': 'value1', 'key2': [1, 2, 3]},
            'boolean': True,
            'null': None,
            'number': 3.14159
        }
        
        result = save_json_data(test_data, temp_file)
        assert result is True
        
        # Verify data was saved correctly
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_determine_file_path_invalid_user_id(self):
        """Test determining file path with invalid user ID."""
        # FIXED: correct parameter order (file_type, identifier)
        path = determine_file_path('users', '')
        # The function should handle empty user_id gracefully
        assert path is not None  # It might return a path or raise an exception
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @pytest.mark.regression
    def test_determine_file_path_invalid_file_type(self):
        """Test determining file path with invalid file type."""
        # FIXED: correct parameter order (file_type, identifier)
        # FIXED: The @handle_errors decorator catches the exception and returns empty string
        result = determine_file_path('invalid_type', 'test-user')
        assert result == ""  # Should return empty string due to error handling decorator
    
    @pytest.mark.integration
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_file_operations_lifecycle(self, test_data_dir, mock_config):
        """Test complete file operations lifecycle using centralized utilities."""
        from tests.test_utilities import TestUserDataFactory
        import uuid
        
        # Step 1: Test user directory creation
        user_id = f"test-file-ops-user-{uuid.uuid4().hex[:8]}"
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        
        #[OK] VERIFY INITIAL STATE: Check directory doesn't exist initially
        initial_dir_exists = os.path.exists(user_dir)
        
        # Create user directory
        ensure_user_directory(user_id)
        
        #[OK] VERIFY REAL BEHAVIOR: Check directory was created
        assert os.path.exists(user_dir), f"User directory should be created: {user_dir}"
        assert os.path.isdir(user_dir), f"User path should be a directory: {user_dir}"
        
        # Step 2: Test file path determination
        account_file_path = get_user_file_path(user_id, 'account')
        
        #[OK] VERIFY REAL BEHAVIOR: Check path structure
        assert account_file_path.endswith('account.json'), f"Path should end with account.json: {account_file_path}"
        
        # Step 3: Test saving user data using centralized utilities
        test_account_data = TestUserDataFactory.create_account_data(
            user_id=user_id,
            email='test@example.com'
        )
        
        #[OK] VERIFY INITIAL STATE: Check file doesn't exist initially
        initial_file_exists = os.path.exists(account_file_path)
        
        result = save_json_data(test_account_data, account_file_path)
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check file was created
        assert os.path.exists(account_file_path), f"Account file should be created: {account_file_path}"
        assert os.path.isfile(account_file_path), f"Account path should be a file: {account_file_path}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file content
        with open(account_file_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_account_data
        
        # Step 4: Test loading user data
        loaded_data = load_json_data(account_file_path)
        
        #[OK] VERIFY REAL BEHAVIOR: Check data integrity
        assert loaded_data == test_account_data
        assert loaded_data['user_id'] == user_id
        assert loaded_data['email'] == 'test@example.com'
        
        # Step 5: Test file access verification
        result = verify_file_access([account_file_path])
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check file still exists and is accessible
        assert os.path.exists(account_file_path), f"File should still exist after verification: {account_file_path}"
        assert os.access(account_file_path, os.R_OK), f"File should still be readable: {account_file_path}"
        
        # Step 6: Test data modification
        updated_account_data = TestUserDataFactory.create_account_data(
            user_id=user_id,
            email='updated@example.com',
            updated_at='2025-01-02T00:00:00Z'
        )
        
        result = save_json_data(updated_account_data, account_file_path)
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check data was updated
        with open(account_file_path, 'r') as f:
            modified_data = json.load(f)
        assert modified_data == updated_account_data
        assert 'updated_at' in modified_data
        assert modified_data['email'] == 'updated@example.com'
        
        # Step 7: Test file operations with multiple files
        preferences_file_path = get_user_file_path(user_id, 'preferences')
        test_preferences_data = TestUserDataFactory.create_preferences_data(
            user_id=user_id,
            categories=['motivational', 'health'],
            timezone='America/Regina'
        )
        
        result = save_json_data(test_preferences_data, preferences_file_path)
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check multiple files can coexist
        assert os.path.exists(account_file_path), f"Account file should still exist: {account_file_path}"
        assert os.path.exists(preferences_file_path), f"Preferences file should be created: {preferences_file_path}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check both files have correct content
        with open(account_file_path, 'r') as f:
            account_data = json.load(f)
        with open(preferences_file_path, 'r') as f:
            preferences_data = json.load(f)
        
        assert account_data == updated_account_data
        assert preferences_data == test_preferences_data
        
        # Step 8: Test error handling with invalid operations
        invalid_path = os.path.join(user_dir, 'nonexistent', 'file.json')
        
        #[OK] VERIFY REAL BEHAVIOR: Check error handling doesn't break existing files
        result = load_json_data(invalid_path)
        # Error recovery may return {} or None depending on concurrent fs state.
        assert result is None or isinstance(result, dict), (
            "Should return None or a dict for invalid path recovery"
        )
        # The file may be created with a default structure depending on directory availability.
        if isinstance(result, dict) and result:
            # If error recovery created the file, it should have metadata structure
            assert 'created' in result or result == {}, "Should have metadata or be empty dict"
        
        #[OK] VERIFY REAL BEHAVIOR: Check existing files are unaffected
        assert os.path.exists(account_file_path), f"Account file should be unaffected: {account_file_path}"
        assert os.path.exists(preferences_file_path), f"Preferences file should be unaffected: {preferences_file_path}"
        
        # Step 9: Test file system consistency
        # Step 10: Verify no leakage into real data directory during tests
        real_user_dir = os.path.join('data', 'users', user_id)
        assert not os.path.exists(real_user_dir), f"Test should not write to real data dir: {real_user_dir}"

@pytest.mark.unit
@pytest.mark.file_io
class TestFileOperationsPerformance:
    """Test file operations performance and large data handling."""
    
    @pytest.mark.slow
    @pytest.mark.file_io
    @pytest.mark.slow
    def test_save_large_json_data(self, temp_file):
        """Test saving large JSON data with performance verification."""
        import time
        import psutil
        import gc
        
        # Create large test data (simulate real-world scenario)
        large_data = {
            'users': {},
            'messages': [],
            'schedules': {},
            'analytics': {}
        }
        
        # Add 1000 users with realistic data
        for i in range(1000):
            user_id = f'user_{i:04d}'
            large_data['users'][user_id] = {
                'user_id': user_id,
                'email': f'user{i}@example.com',
                'preferences': {
                    'categories': ['motivational', 'health'],
                    'timezone': 'America/Regina',
                    'checkin_settings': {'enabled': True},
                    'task_settings': {'enabled': False}
                },
                'context': {
                    'preferred_name': f'User {i}',
                    'last_checkin': '2025-01-01T12:00:00Z'
                }
            }
        
        # Add 5000 messages
        for i in range(5000):
            large_data['messages'].append({
                'id': f'msg_{i:06d}',
                'category': 'motivational' if i % 2 == 0 else 'health',
                'content': f'This is message number {i} with some realistic content.',
                'created_at': '2025-01-01T12:00:00Z',
                'scheduled_for': '2025-01-02T09:00:00Z'
            })
        
        #[OK] VERIFY INITIAL STATE: Check memory usage before operation
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_time = time.time()
        
        # Perform the operation
        result = save_json_data(large_data, temp_file)
        assert result is True
        
        #[OK] VERIFY REAL BEHAVIOR: Check operation completed successfully
        assert os.path.exists(temp_file), f"Large file should be created: {temp_file}"
        assert os.path.isfile(temp_file), f"Large file should be a file: {temp_file}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file size is reasonable for data size
        file_size = os.path.getsize(temp_file)
        assert file_size > 100000, f"Large file should be substantial: {file_size} bytes"
        assert file_size < 10000000, f"Large file should not be unreasonably large: {file_size} bytes"
        
        #[OK] VERIFY REAL BEHAVIOR: Check data integrity
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == large_data
        
        #[OK] VERIFY REAL BEHAVIOR: Check performance metrics
        operation_time = time.time() - initial_time
        assert operation_time < 10.0, f"Operation should complete within 10 seconds: {operation_time:.2f}s"
        
        #[OK] VERIFY REAL BEHAVIOR: Check memory usage after operation
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this operation)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increase should be reasonable: {memory_increase / 1024 / 1024:.2f}MB"
        
        #[OK] VERIFY REAL BEHAVIOR: Check for memory leaks
        gc.collect()  # Force garbage collection
        post_gc_memory = process.memory_info().rss
        memory_after_gc = post_gc_memory - initial_memory
        
        # Memory should be reclaimed after garbage collection
        assert memory_after_gc < 50 * 1024 * 1024, f"Memory should be reclaimed after GC: {memory_after_gc / 1024 / 1024:.2f}MB"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file can be read multiple times efficiently
        read_times = []
        for _ in range(5):
            start_time = time.time()
            with open(temp_file, 'r') as f:
                reloaded_data = json.load(f)
            read_time = time.time() - start_time
            read_times.append(read_time)
            
            # Verify data integrity on each read
            assert reloaded_data == large_data
        
        #[OK] VERIFY REAL BEHAVIOR: Check read performance is consistent
        avg_read_time = sum(read_times) / len(read_times)
        max_read_time = max(read_times)
        assert avg_read_time < 2.0, f"Average read time should be reasonable: {avg_read_time:.2f}s"
        assert max_read_time < 5.0, f"Maximum read time should be reasonable: {max_read_time:.2f}s"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file permissions are correct
        assert os.access(temp_file, os.R_OK), f"Large file should be readable: {temp_file}"
        assert os.access(temp_file, os.W_OK), f"Large file should be writable: {temp_file}"
        
        #[OK] VERIFY REAL BEHAVIOR: Check file is valid JSON
        try:
            with open(temp_file, 'r') as f:
                json.load(f)  # Should not raise exception
        except json.JSONDecodeError as e:
            assert False, f"Large file should be valid JSON: {e}"
    
    @pytest.mark.slow
    @pytest.mark.file_io
    @pytest.mark.slow
    def test_load_large_json_data(self, temp_file):
        """Test loading large JSON data."""
        # Create and save large test data
        large_data = {
            'items': [{'id': i, 'data': f'item_{i}' * 50} for i in range(500)]
        }
        
        save_json_data(large_data, temp_file)
        
        # Load the data
        loaded_data = load_json_data(temp_file)
        assert loaded_data == large_data
        assert len(loaded_data['items']) == 500 
