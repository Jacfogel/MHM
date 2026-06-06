from collections.abc import Callable
from importlib import import_module


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
logger = _lazy_dependencies.get_component_logger("ui")


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


@handle_errors("running full scheduler from UI action", default_return=False)
def run_full_scheduler(delivery_factory: Callable[[], object]) -> bool:
    """Run the full scheduler with the UI communication delivery factory."""
    run_full_scheduler_standalone = _load_attr(
        "scheduler.manager", "run_full_scheduler_standalone"
    )
    set_scheduler_delivery_factory = _load_attr(
        "scheduler.manager", "set_scheduler_delivery_factory"
    )

    logger.info("UI: Running full scheduler for all users")
    set_scheduler_delivery_factory(delivery_factory)
    return bool(run_full_scheduler_standalone())


@handle_errors("running user scheduler from UI action", default_return=False)
def run_user_scheduler(user_id: str) -> bool:
    """Run the scheduler for one selected user."""
    run_user_scheduler_standalone = _load_attr(
        "scheduler.manager", "run_user_scheduler_standalone"
    )

    logger.info(f"UI: Running scheduler for user {user_id}")
    return bool(run_user_scheduler_standalone(user_id))


@handle_errors("running category scheduler from UI action", default_return=False)
def run_category_scheduler(user_id: str, category: str) -> bool:
    """Run the scheduler for one selected user/category pair."""
    run_category_scheduler_standalone = _load_attr(
        "scheduler.manager", "run_category_scheduler_standalone"
    )

    logger.info(
        f"UI: Running category scheduler for user {user_id}, category {category}"
    )
    return bool(run_category_scheduler_standalone(user_id, category))
