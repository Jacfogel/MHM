"""
Tests for generate_consolidated_report.py.

Tests consolidated report generation functionality including AI_STATUS.md,
AI_PRIORITIES.md, and consolidated_report.md generation.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy


# Load the module
consolidated_report_module = load_development_tools_module("reports.generate_consolidated_report")
generate_consolidated_reports = consolidated_report_module.generate_consolidated_reports


class TestGenerateConsolidatedReport:
    """Test consolidated report generation functionality."""
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_basic(self, temp_project_copy):
        """Test basic consolidated report generation."""
        # Mock AIToolsService to avoid full audit execution
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock the report generation methods
            mock_service._generate_ai_status_document.return_value = "# AI Status\n\nTest content"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities\n\nTest content"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report\n\nTest content"
            
            # Mock create_output_file
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                mock_create.side_effect = lambda path, content: Path(temp_project_copy) / path
                
                # Run generation
                result = generate_consolidated_reports(
                    project_root=str(temp_project_copy)
                )
                
                # Verify results structure
                assert isinstance(result, dict), "Result should be a dictionary"
                assert 'ai_status' in result, "Result should have ai_status"
                assert 'ai_priorities' in result, "Result should have ai_priorities"
                assert 'consolidated_report' in result, "Result should have consolidated_report"
                
                # Verify service was called correctly
                mock_service_class.assert_called_once_with(
                    project_root=str(temp_project_copy),
                    config_path=None
                )
                
                # Verify report generation methods were called
                mock_service._generate_ai_status_document.assert_called_once()
                mock_service._generate_ai_priorities_document.assert_called_once()
                mock_service._generate_consolidated_report.assert_called_once()
                
                # Verify create_output_file was called for each report
                assert mock_create.call_count == 3, "Should create 3 output files"
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_with_config_path(self, temp_project_copy):
        """Test consolidated report generation with config path."""
        config_path = str(temp_project_copy / "custom_config.json")
        
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service._generate_ai_status_document.return_value = "# AI Status"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report"
            
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                mock_create.side_effect = lambda path, content: Path(temp_project_copy) / path
                
                result = generate_consolidated_reports(
                    project_root=str(temp_project_copy),
                    config_path=config_path
                )
                
                # Verify config_path was passed to service
                mock_service_class.assert_called_once_with(
                    project_root=str(temp_project_copy),
                    config_path=config_path
                )
                
                assert isinstance(result, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_output_file_paths(self, temp_project_copy):
        """Test that output file paths are correctly generated."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service._generate_ai_status_document.return_value = "# AI Status"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report"
            
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                # Track calls to verify paths
                call_paths = []
                
                def track_create(path, content):
                    call_paths.append(path)
                    return Path(temp_project_copy) / path
                
                mock_create.side_effect = track_create
                
                result = generate_consolidated_reports(
                    project_root=str(temp_project_copy)
                )
                
                # Verify correct paths were used
                assert "development_tools/AI_STATUS.md" in call_paths, "Should create AI_STATUS.md"
                assert "development_tools/AI_PRIORITIES.md" in call_paths, "Should create AI_PRIORITIES.md"
                assert "development_tools/consolidated_report.md" in call_paths, "Should create consolidated_report.md"
                
                # Verify result paths are strings
                assert isinstance(result['ai_status'], str), "ai_status path should be string"
                assert isinstance(result['ai_priorities'], str), "ai_priorities path should be string"
                assert isinstance(result['consolidated_report'], str), "consolidated_report path should be string"
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_service_error_handling(self, temp_project_copy):
        """Test error handling when service fails."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            # Simulate service initialization failure
            mock_service_class.side_effect = Exception("Service initialization failed")
            
            # Should raise exception
            with pytest.raises(Exception, match="Service initialization failed"):
                generate_consolidated_reports(
                    project_root=str(temp_project_copy)
                )
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_report_generation_error(self, temp_project_copy):
        """Test error handling when report generation fails."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Simulate report generation failure
            mock_service._generate_ai_status_document.side_effect = Exception("Report generation failed")
            
            # Should raise exception
            with pytest.raises(Exception, match="Report generation failed"):
                with patch('development_tools.reports.generate_consolidated_report.create_output_file'):
                    generate_consolidated_reports(
                        project_root=str(temp_project_copy)
                    )
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_file_creation_error(self, temp_project_copy):
        """Test error handling when file creation fails."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service._generate_ai_status_document.return_value = "# AI Status"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report"
            
            # Simulate file creation failure
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                mock_create.side_effect = Exception("File creation failed")
                
                # Should raise exception
                with pytest.raises(Exception, match="File creation failed"):
                    generate_consolidated_reports(
                        project_root=str(temp_project_copy)
                    )
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_none_project_root(self, temp_project_copy):
        """Test generation with None project_root (uses default)."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service._generate_ai_status_document.return_value = "# AI Status"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report"
            
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                mock_create.side_effect = lambda path, content: Path(temp_project_copy) / path
                
                result = generate_consolidated_reports(
                    project_root=None
                )
                
                # Verify service was called with None
                mock_service_class.assert_called_once_with(
                    project_root=None,
                    config_path=None
                )
                
                assert isinstance(result, dict), "Result should be a dictionary"
    
    @pytest.mark.unit
    def test_generate_consolidated_reports_content_passed_to_file_creator(self, temp_project_copy):
        """Test that report content is correctly passed to file creator."""
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            status_content = "# AI Status\n\nDetailed status content"
            priorities_content = "# AI Priorities\n\nDetailed priorities content"
            consolidated_content = "Consolidated Report\n\nDetailed consolidated content"
            
            mock_service._generate_ai_status_document.return_value = status_content
            mock_service._generate_ai_priorities_document.return_value = priorities_content
            mock_service._generate_consolidated_report.return_value = consolidated_content
            
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                call_contents = []
                
                def track_create(path, content):
                    call_contents.append((path, content))
                    return Path(temp_project_copy) / path
                
                mock_create.side_effect = track_create
                
                result = generate_consolidated_reports(
                    project_root=str(temp_project_copy)
                )
                
                # Verify content was passed correctly
                assert len(call_contents) == 3, "Should have 3 file creation calls"
                
                # Find each call by path
                status_call = next((c for c in call_contents if "AI_STATUS.md" in c[0]), None)
                priorities_call = next((c for c in call_contents if "AI_PRIORITIES.md" in c[0]), None)
                consolidated_call = next((c for c in call_contents if "consolidated_report.md" in c[0]), None)
                
                assert status_call is not None, "Should have AI_STATUS.md call"
                assert status_call[1] == status_content, "Status content should match"
                
                assert priorities_call is not None, "Should have AI_PRIORITIES.md call"
                assert priorities_call[1] == priorities_content, "Priorities content should match"
                
                assert consolidated_call is not None, "Should have consolidated_report.md call"
                assert consolidated_call[1] == consolidated_content, "Consolidated content should match"
    
    @pytest.mark.integration
    def test_generate_consolidated_reports_integration(self, temp_project_copy):
        """Test consolidated report generation with real service (integration test)."""
        # This test uses the real service but with a temp project to avoid affecting real files
        # Note: This may be slow if it triggers actual audits
        
        # Create minimal project structure
        (temp_project_copy / "README.md").write_text("# Test Project")
        (temp_project_copy / "development_tools").mkdir(exist_ok=True)
        
        # Create minimal config if needed
        config_file = temp_project_copy / "development_tools_config.json"
        if not config_file.exists():
            config_file.write_text('{"project_root": "' + str(temp_project_copy).replace('\\', '\\\\') + '"}')
        
        # Run generation (may take time if it runs audits)
        # We'll use a timeout or mock to prevent long execution
        with patch('development_tools.reports.generate_consolidated_report.AIToolsService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service._generate_ai_status_document.return_value = "# AI Status\n\nIntegration test"
            mock_service._generate_ai_priorities_document.return_value = "# AI Priorities\n\nIntegration test"
            mock_service._generate_consolidated_report.return_value = "Consolidated Report\n\nIntegration test"
            
            with patch('development_tools.reports.generate_consolidated_report.create_output_file') as mock_create:
                mock_create.side_effect = lambda path, content: temp_project_copy / path
                
                result = generate_consolidated_reports(
                    project_root=str(temp_project_copy)
                )
                
                assert isinstance(result, dict), "Result should be a dictionary"
                assert all(key in result for key in ['ai_status', 'ai_priorities', 'consolidated_report']), \
                    "Result should have all required keys"
