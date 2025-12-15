"""
Core AIToolsService class.

Contains initialization and basic configuration methods.
Other functionality is provided via mixin classes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import config
from ... import config

# Import mixins
from .utilities import UtilitiesMixin
from .data_loading import DataLoadingMixin
from .tool_wrappers import ToolWrappersMixin, SCRIPT_REGISTRY
from .audit_orchestration import AuditOrchestrationMixin
from .report_generation import ReportGenerationMixin
from .commands import CommandsMixin

# Import COMMAND_TIERS from common (preserve existing dependency)
from ..common import COMMAND_TIERS


class AIToolsService(
    UtilitiesMixin,
    DataLoadingMixin,
    ToolWrappersMixin,
    AuditOrchestrationMixin,
    ReportGenerationMixin,
    CommandsMixin
):
    """Comprehensive AI tools runner optimized for AI collaboration."""
    
    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None, 
                 project_name: Optional[str] = None, key_files: Optional[List[str]] = None):
        # Load external config if path provided, or try to auto-load from default location
        if config_path:
            config.load_external_config(config_path)
        else:
            # Try to auto-load from development_tools/config/development_tools_config.json or project root
            config.load_external_config()
        
        # Use provided project_root or fall back to config
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        
        # Store config_path for reference
        self.config_path = config_path
        
        # Project-specific configuration (for portability)
        # Can be overridden by external config
        self.project_name = project_name or config.get_external_value('project.name', "Project")
        self.key_files = key_files or config.get_external_value('project.key_files', [])
        
        self.workflow_config = config.get_workflow_config() or {}
        
        # Store path validation result for status display
        self.path_validation_result: Optional[Dict[str, Any]] = None
        
        self.validation_config = config.get_ai_validation_config() or {}
        self.ai_config = config.get_ai_collaboration_config() or {}
        self.audit_config = config.get_quick_audit_config() or {}
        
        self.results_cache = {}
        self.docs_sync_results = None
        self.system_signals = None
        self.dev_tools_coverage_results = None
        self.module_dependency_summary = None
        self.todo_sync_result = None
        
        self.exclusion_config = {
            'include_tests': False,
            'include_dev_tools': False
        }
        
        self.docs_sync_summary = None
        self.legacy_cleanup_results = None
        self.legacy_cleanup_summary = None
        self.status_results = None
        self.status_summary = None
        self.current_audit_tier = None  # Track current audit tier (1=quick, 2=standard, 3=full)
        self._tools_run_in_current_tier = set()  # Track which tools were actually run in current tier
        self._tools_run_in_current_tier = set()  # Track which tools were actually run in current tier
    
    def set_exclusion_config(self, include_tests: bool = False, include_dev_tools: bool = False):
        """Set exclusion configuration for audit tools."""
        self.exclusion_config = {
            'include_tests': include_tests,
            'include_dev_tools': include_dev_tools
        }
