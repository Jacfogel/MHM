"""Lazy dependency boundary for the Qt admin shell."""

from importlib import import_module


def load_attr(module_name: str, attr_name: str):
    """Load a project attribute lazily for UI shell delegation."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return getattr(import_module(module_name), attr_name)


DataError = load_attr("core.error_handling", "DataError")
handle_errors = load_attr("core.error_handling", "handle_errors")


@handle_errors("preparing launch environment from UI", re_raise=True)
def prepare_launch_environment(*args, **kwargs):
    """Lazy wrapper for launch environment preparation."""
    return load_attr("core.launch_env", "prepare_launch_environment")(*args, **kwargs)


@handle_errors("resolving Python interpreter from UI", re_raise=True)
def resolve_python_interpreter(*args, **kwargs):
    """Lazy wrapper for Python interpreter resolution."""
    return load_attr("core.launch_env", "resolve_python_interpreter")(*args, **kwargs)


@handle_errors("getting current datetime for UI", re_raise=True)
def now_datetime_full(*args, **kwargs):
    """Lazy wrapper for timezone-aware current datetime."""
    return load_attr("core.time_utilities", "now_datetime_full")(*args, **kwargs)


@handle_errors("getting current timestamp for UI", re_raise=True)
def now_timestamp_full(*args, **kwargs):
    """Lazy wrapper for full timestamp generation."""
    return load_attr("core.time_utilities", "now_timestamp_full")(*args, **kwargs)


@handle_errors("parsing timestamp for UI", re_raise=True)
def parse_timestamp_full(*args, **kwargs):
    """Lazy wrapper for full timestamp parsing."""
    return load_attr("core.time_utilities", "parse_timestamp_full")(*args, **kwargs)


@handle_errors("setting up UI logging", re_raise=True)
def setup_logging(*args, **kwargs):
    """Lazy wrapper for logger setup."""
    return load_attr("core.logger", "setup_logging")(*args, **kwargs)


@handle_errors("getting UI component logger", re_raise=True)
def get_component_logger(*args, **kwargs):
    """Lazy wrapper for component logger lookup."""
    return load_attr("core.logger", "get_component_logger")(*args, **kwargs)


@handle_errors("validating configuration for UI", re_raise=True)
def validate_all_configuration(*args, **kwargs):
    """Lazy wrapper for configuration validation."""
    return load_attr("core.config", "validate_all_configuration")(*args, **kwargs)


@handle_errors("getting service flag directory for UI", re_raise=True)
def get_flags_dir(*args, **kwargs):
    """Lazy wrapper for service flag directory lookup."""
    return load_attr("core.service_utilities", "get_flags_dir")(*args, **kwargs)


@handle_errors("creating user context for UI", re_raise=True)
def UserContext(*args, **kwargs):
    """Lazy wrapper for user context construction."""
    return load_attr("user.user_context", "UserContext")(*args, **kwargs)


@handle_errors("listing user ids for UI", re_raise=True)
def get_all_user_ids(*args, **kwargs):
    """Lazy wrapper for user id listing."""
    return load_attr("core", "get_all_user_ids")(*args, **kwargs)


@handle_errors("reading user data for UI", re_raise=True)
def get_user_data(*args, **kwargs):
    """Lazy wrapper for user data reads."""
    return load_attr("core", "get_user_data")(*args, **kwargs)


@handle_errors("saving user data for UI", re_raise=True)
def save_user_data(*args, **kwargs):
    """Lazy wrapper for user data writes."""
    return load_attr("core", "save_user_data")(*args, **kwargs)


@handle_errors("formatting title case for UI", re_raise=True)
def shared_title_case(*args, **kwargs):
    """Lazy wrapper for title casing user-facing labels."""
    return load_attr("storage.user_data_validation", "_shared__title_case")(
        *args, **kwargs
    )


@handle_errors("creating generated admin panel UI", re_raise=True)
def Ui_ui_app_mainwindow(*args, **kwargs):
    """Lazy wrapper for the generated admin panel UI class."""
    generated_class = load_attr(
        "ui.generated.admin_panel_pyqt", "Ui_ui_app_mainwindow"
    )
    return generated_class(*args, **kwargs)
