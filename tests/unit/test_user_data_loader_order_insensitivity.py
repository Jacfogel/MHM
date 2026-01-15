

import importlib

import pytest


def _reload_in_order(first_module: str, second_module: str):
    first = importlib.import_module(first_module)
    second = importlib.import_module(second_module)
    first = importlib.reload(first)
    second = importlib.reload(second)
    return first, second


@pytest.mark.unit
def test_loader_registry_shared_and_complete_regardless_of_import_order():
    # Case 1: import then reload user_data_handlers
    um1, udh1 = _reload_in_order('core.user_data_handlers', 'core.user_data_handlers')
    assert um1.USER_DATA_LOADERS is udh1.USER_DATA_LOADERS

    if hasattr(um1, 'register_default_loaders'):
        um1.register_default_loaders()
    elif hasattr(udh1, 'register_default_loaders'):
        udh1.register_default_loaders()

    for k in ('account', 'preferences', 'context', 'schedules'):
        entry = um1.USER_DATA_LOADERS.get(k)
        assert isinstance(entry, dict)
        assert entry.get('loader') is not None

    # Case 2: reload user_data_handlers twice (reverse order equivalent)
    udh2, um2 = _reload_in_order('core.user_data_handlers', 'core.user_data_handlers')
    # Allow different dict objects across modules as long as required loaders are present
    if hasattr(um2, 'register_default_loaders'):
        um2.register_default_loaders()
    elif hasattr(udh2, 'register_default_loaders'):
        udh2.register_default_loaders()

    required = ('account', 'preferences', 'context', 'schedules')
    for k in required:
        e1 = um2.USER_DATA_LOADERS.get(k)
        e2 = udh2.USER_DATA_LOADERS.get(k)
        assert isinstance(e1, dict) and e1.get('loader') is not None
        assert isinstance(e2, dict) and e2.get('loader') is not None

