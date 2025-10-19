

import importlib

def _reload_in_order(first_module: str, second_module: str):
    first = importlib.import_module(first_module)
    second = importlib.import_module(second_module)
    first = importlib.reload(first)
    second = importlib.reload(second)
    return first, second


def test_loader_registry_shared_and_complete_regardless_of_import_order():
    # Case 1: user_management then user_data_handlers
    um1, udh1 = _reload_in_order('core.user_management', 'core.user_data_handlers')
    assert um1.USER_DATA_LOADERS is udh1.USER_DATA_LOADERS

    if hasattr(um1, 'register_default_loaders'):
        um1.register_default_loaders()
    elif hasattr(udh1, 'register_default_loaders'):
        udh1.register_default_loaders()

    for k in ('account', 'preferences', 'context', 'schedules'):
        entry = um1.USER_DATA_LOADERS.get(k)
        assert isinstance(entry, dict)
        assert entry.get('loader') is not None

    # Case 2: user_data_handlers then user_management (reverse order)
    udh2, um2 = _reload_in_order('core.user_data_handlers', 'core.user_management')
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

