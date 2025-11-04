"""Core functionality package for the MHM application.

Contains foundational modules for configuration, logging, error handling,
service management, user data operations, scheduling, and system utilities.
"""

# Main public API - package-level exports for easier refactoring
# Logger exports
from .logger import (
    get_component_logger,
    setup_logging,
    ComponentLogger,
    BackupDirectoryRotatingFileHandler,
    ExcludeLoggerNamesFilter,
    TestContextFormatter,
    setup_third_party_error_logging,
    suppress_noisy_logging,
    set_console_log_level,
    toggle_verbose_logging,
    get_verbose_mode,
    set_verbose_mode,
    get_logger,
)

# Error handling exports
from .error_handling import (
    handle_errors,
    MHMError,
    DataError,
    FileOperationError,
    ConfigurationError,
    CommunicationError,
    SchedulerError,
    UserInterfaceError,
    AIError,
    ValidationError,
    RecoveryError,
)

# User data handlers exports
from .user_data_handlers import (
    get_user_data,
    save_user_data,
    save_user_data_transaction,
    get_all_user_ids,
    update_user_account,
    update_user_preferences,
    update_user_schedules,
    update_user_context,
    update_channel_preferences,
    register_data_loader,
)

# Config exports - commonly used constants and functions
# Note: We import the module rather than individual constants to avoid
# exposing too many items. Users can do: from core import config; config.BASE_DATA_DIR
from . import config

# File operations exports (no circular dependencies)
from .file_operations import (
    load_json_data,
    save_json_data,
    determine_file_path,
    verify_file_access,
)

# Message management exports (no circular dependencies)
from .message_management import (
    get_recent_messages,
    store_sent_message,
    get_message_categories,
    load_user_messages,
    add_message,
    archive_old_messages,
)

# Response tracking exports (no circular dependencies)
from .response_tracking import (
    get_recent_responses,
    store_chat_interaction,
    get_recent_checkins,
    is_user_checkins_enabled,
)

# User data validation exports (no circular dependencies)
from .user_data_validation import (
    validate_schedule_periods,
    is_valid_email,  # Medium usage
)

# Error handling additional exports (medium usage)
from .error_handling import handle_network_error

# Config constants exports (medium usage)
# Note: Some config constants are imported directly, so we export commonly used ones
from .config import (
    DISCORD_BOT_TOKEN,
    EMAIL_SMTP_SERVER,
    EMAIL_IMAP_SERVER,
    EMAIL_SMTP_USERNAME,
    LM_STUDIO_BASE_URL,
    LM_STUDIO_API_KEY,
    LM_STUDIO_MODEL,
    SCHEDULER_INTERVAL,
    get_available_channels,
)

# UI management exports (medium usage)
from .ui_management import (
    collect_period_data_from_widgets,
    load_period_widgets_for_category,
)

# User management additional exports (medium usage)
from .user_management import (
    ensure_all_categories_have_schedules,
    get_user_id_by_identifier,
)

# Schema validation exports (medium usage)
from .schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
    validate_messages_file_dict,
)

# Schema models exports (public API)
from .schemas import (
    AccountModel,
    ChannelModel,
    PreferencesModel,
    CategoryScheduleModel,
    FeaturesModel,
    PeriodModel,
    MessagesFileModel,
    MessageModel,
    SchedulesModel,
)

# Config additional constants exports (low usage)
from .config import (
    CONTEXT_CACHE_TTL,
    DISCORD_APPLICATION_ID,
    EMAIL_SMTP_PASSWORD,
)

# Config additional functions exports (public API)
from .config import (
    validate_all_configuration,
    validate_and_raise_if_invalid,
    get_backups_dir,
    ensure_user_directory,
    validate_email_config,
    validate_discord_config,
    validate_minimum_config,
    get_channel_class_mapping,
    validate_core_paths,
    validate_ai_configuration,
    validate_communication_channels,
    validate_logging_configuration,
    validate_scheduler_configuration,
    validate_file_organization_settings,
    validate_environment_variables,
    print_configuration_report,
)

# Error handling additional classes and functions (public API)
from .error_handling import (
    ErrorHandler,
    ErrorRecoveryStrategy,
    ConfigurationRecovery,
)

# Config validation error class (public API)
from .config import ConfigValidationError

# Service classes exports (public API)
# Note: Some service items may have circular dependencies
from .service import (
    MHMService,
    InitializationError,
)

# Service utilities exports (public API)
from .service_utilities import (
    Throttler,
    InvalidTimeFormatError,
    create_reschedule_request,
    is_service_running,
    get_service_processes,
    is_headless_service_running,
    is_ui_service_running,
    wait_for_network,
    load_and_localize_datetime,
)

# Headless service exports (public API)
from .headless_service import HeadlessServiceManager

# File operations additional exports (public API)
from .file_operations import create_user_files

# File auditor exports (public API)
from .file_auditor import (
    FileAuditor,
    start_auditor,
    stop_auditor,
    record_created,
)

# Schedule utilities exports (public API)
# Note: schedule_utilities may have dependencies on schedule_management
from .schedule_utilities import (
    get_active_schedules,
    is_schedule_active,
    get_current_active_schedules,
)

# Auto cleanup exports (public API)
from .auto_cleanup import (
    get_last_cleanup_timestamp,
    update_cleanup_timestamp,
    should_run_cleanup,
    perform_cleanup,
    auto_cleanup_if_needed,
    archive_old_messages_for_all_users,
    get_cleanup_status,
)

# Backup manager exports (public API)
from .backup_manager import BackupManager

# Check-in dynamic manager class exports (public API)
from .checkin_dynamic_manager import DynamicCheckinManager

# Check-in analytics exports (high usage)
from .checkin_analytics import CheckinAnalytics

# Error handling additional exports (high usage)
from .error_handling import handle_ai_error

# Config function exports (high usage)
from .config import get_user_data_dir, get_user_file_path

# Dynamic check-in manager exports (high usage)
from .checkin_dynamic_manager import dynamic_checkin_manager

# Schedule management exports - lazy import due to circular dependencies (medium usage)
# Note: schedule_management has circular dependencies with user package
# Functions available: get_schedule_time_periods, set_schedule_periods (high usage),
# clear_schedule_periods_cache (medium usage), add_schedule_period (low usage)
# Note: add_schedule_period has circular dependencies, documented as lazy import

# User data manager exports (high usage)
# Note: user_data_manager may have circular dependencies
# Attempting direct import - if this causes circular import errors, this will be
# documented as lazy import in comments
from .user_data_manager import (
    update_user_index,
    rebuild_user_index,
    UserDataManager,
    update_message_references,
    backup_user_data,
    export_user_data,
    delete_user_completely,
    get_user_data_summary,
    get_user_info_for_data_manager,
    build_user_index,
    get_user_summary,
    get_all_user_summaries,
    get_user_analytics_summary,
)

# User management exports (high usage)
# Note: user_management may have circular dependencies
# Attempting direct import - if this causes circular import errors, this will be
# documented as lazy import in comments
from .user_management import (
    get_user_categories,
    clear_user_caches,
    register_default_loaders,
    get_available_data_types,
    get_data_type_info,
    create_default_schedule_periods,
    migrate_legacy_schedules_structure,
    ensure_category_has_default_schedule,
)

# Service exports - lazy import due to circular dependencies (medium usage)
# Note: service has circular dependencies with scheduler
# Functions available: get_scheduler_manager (medium usage), MHMService, InitializationError
# Use: from core.service import get_scheduler_manager

# User management exports - lazy import to avoid circular dependencies
# Note: Some user_management functions have circular dependencies
# Functions available via direct import: get_user_categories (high usage), 
# ensure_all_categories_have_schedules, get_user_id_by_identifier (medium usage)
# Other functions: clear_user_caches (use: from core.user_management import clear_user_caches)

# User data manager exports - lazy import to avoid circular dependencies  
# Note: user_data_manager may have circular dependencies
# Functions available via direct import: update_user_index (high usage)
# Other functions: rebuild_user_index (use: from core.user_data_manager import rebuild_user_index)

# Scheduler exports - lazy import due to circular dependencies (medium usage)
# Note: SchedulerManager and add_schedule_period have circular dependencies
# Use lazy import pattern for these items
def __getattr__(name: str):
    """Lazy import handler for items with circular dependencies"""
    if name == 'SchedulerManager':
        from .scheduler import SchedulerManager
        return SchedulerManager
    elif name == 'add_schedule_period':
        from .schedule_management import add_schedule_period
        return add_schedule_period
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Logger
    'get_component_logger',
    'setup_logging',
    'ComponentLogger',
    'BackupDirectoryRotatingFileHandler',
    'ExcludeLoggerNamesFilter',
    'TestContextFormatter',
    'setup_third_party_error_logging',
    'suppress_noisy_logging',
    'set_console_log_level',
    'toggle_verbose_logging',
    'get_verbose_mode',
    'set_verbose_mode',
    'get_logger',
    # Error handling
    'handle_errors',
    'MHMError',
    'DataError',
    'FileOperationError',
    'ConfigurationError',
    'CommunicationError',
    'SchedulerError',
    'UserInterfaceError',
    'AIError',
    'ValidationError',
    'RecoveryError',
    # User data handlers
    'get_user_data',
    'save_user_data',
    'save_user_data_transaction',
    'get_all_user_ids',
    'update_user_account',
    'update_user_preferences',
    'update_user_schedules',
    'update_user_context',
    'update_channel_preferences',
    'register_data_loader',
    # File operations
    'load_json_data',
    'save_json_data',
    'determine_file_path',
    'verify_file_access',
    # Message management
    'get_recent_messages',
    'store_sent_message',
    'get_message_categories',
    'load_user_messages',
    # Response tracking
    'get_recent_responses',
    'store_chat_interaction',
    'get_recent_checkins',
    'is_user_checkins_enabled',
    # User data validation
    'validate_schedule_periods',
    'is_valid_email',  # Medium usage
    # Error handling additional (medium usage)
    'handle_network_error',
    # Config constants (medium usage)
    'DISCORD_BOT_TOKEN',
    'EMAIL_SMTP_SERVER',
    'EMAIL_IMAP_SERVER',
    'EMAIL_SMTP_USERNAME',
    'LM_STUDIO_BASE_URL',
    'LM_STUDIO_API_KEY',
    'LM_STUDIO_MODEL',
    'SCHEDULER_INTERVAL',
    'get_available_channels',
    # UI management (medium usage)
    'collect_period_data_from_widgets',
    'load_period_widgets_for_category',
    # User management additional (medium usage)
    'ensure_all_categories_have_schedules',
    'get_user_id_by_identifier',
    # Schedule management - lazy import (circular dependencies)
    'add_schedule_period',
    # Scheduler - lazy import (circular dependencies)
    'SchedulerManager',
    # Schema validation (medium usage)
    'validate_account_dict',
    'validate_preferences_dict',
    'validate_schedules_dict',
    'validate_messages_file_dict',
    # Schema models (public API)
    'AccountModel',
    'ChannelModel',
    'PreferencesModel',
    'CategoryScheduleModel',
    'FeaturesModel',
    'PeriodModel',
    'MessagesFileModel',
    'MessageModel',
    'SchedulesModel',
    # Config additional constants (low usage)
    'CONTEXT_CACHE_TTL',
    'DISCORD_APPLICATION_ID',
    'EMAIL_SMTP_PASSWORD',
    # Config additional functions (public API)
    'validate_all_configuration',
    'validate_and_raise_if_invalid',
    'get_backups_dir',
    'ensure_user_directory',
    'validate_email_config',
    'validate_discord_config',
    'validate_minimum_config',
    'get_channel_class_mapping',
    'validate_core_paths',
    'validate_ai_configuration',
    'validate_communication_channels',
    'validate_logging_configuration',
    'validate_scheduler_configuration',
    'validate_file_organization_settings',
    'validate_environment_variables',
    'print_configuration_report',
    # Error handling additional classes and functions (public API)
    'ErrorHandler',
    'ErrorRecoveryStrategy',
    'ConfigurationRecovery',
    # Config validation error class (public API)
    'ConfigValidationError',
    # Service classes (public API)
    'MHMService',
    'InitializationError',
    # Service utilities (public API)
    'Throttler',
    'InvalidTimeFormatError',
    'create_reschedule_request',
    'is_service_running',
    'get_service_processes',
    'is_headless_service_running',
    'is_ui_service_running',
    'wait_for_network',
    'load_and_localize_datetime',
    # Headless service (public API)
    'HeadlessServiceManager',
    # File operations additional (public API)
    'create_user_files',
    # File auditor (public API)
    'FileAuditor',
    'start_auditor',
    'stop_auditor',
    'record_created',
    # Schedule utilities (public API)
    'get_active_schedules',
    'is_schedule_active',
    'get_current_active_schedules',
    # Auto cleanup (public API)
    'get_last_cleanup_timestamp',
    'update_cleanup_timestamp',
    'should_run_cleanup',
    'perform_cleanup',
    'auto_cleanup_if_needed',
    'archive_old_messages_for_all_users',
    'get_cleanup_status',
    # Backup manager (public API)
    'BackupManager',
    # Check-in dynamic manager class (public API)
    'DynamicCheckinManager',
    # Check-in analytics (high usage)
    'CheckinAnalytics',
    # Error handling additional (high usage)
    'handle_ai_error',
    # Config functions (high usage)
    'get_user_data_dir',
    'get_user_file_path',
    # Dynamic check-in manager (high usage)
    'dynamic_checkin_manager',
    # Schedule management (high usage) - lazy import due to circular dependencies
    # Note: get_schedule_time_periods, set_schedule_periods not in __all__ due to circular dependencies
    # Use: from core.schedule_management import get_schedule_time_periods, set_schedule_periods
    # User data manager (high usage and public API)
    'update_user_index',
    'rebuild_user_index',
    'UserDataManager',
    'update_message_references',
    'backup_user_data',
    'export_user_data',
    'delete_user_completely',
    'get_user_data_summary',
    'get_user_info_for_data_manager',
    'build_user_index',
    'get_user_summary',
    'get_all_user_summaries',
    'get_user_analytics_summary',
    # User management (high usage and public API)
    'get_user_categories',
    'clear_user_caches',
    'register_default_loaders',
    'get_available_data_types',
    'get_data_type_info',
    'create_default_schedule_periods',
    'migrate_legacy_schedules_structure',
    'ensure_category_has_default_schedule',
    # Modules (for module-level access: from core import config)
    'config',
    # Legacy module names (for backward compatibility)
    'auto_cleanup',
    'backup_manager',
    'checkin_analytics',
    'checkin_dynamic_manager',
    'error_handling',
    'file_auditor',
    'file_operations',
    'headless_service',
    'logger',
    'message_management',
    'response_tracking',
    'schedule_management',
    'schedule_utilities',
    'scheduler',
    'service',
    'service_utilities',
    'ui_management',
    'user_data_handlers',
    'user_data_manager',
    'user_data_validation',
    'user_management',
]
