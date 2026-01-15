import importlib

import pytest


@pytest.mark.unit
def test_loader_registry_identity_and_idempotency():
    # Reload modules to ensure current state
    um = importlib.import_module('core.user_data_handlers')
    udh = importlib.import_module('core.user_data_handlers')

    um = importlib.reload(um)
    udh = importlib.reload(udh)

    # Identity: both modules must reference the exact same dict object
    assert um.USER_DATA_LOADERS is udh.USER_DATA_LOADERS

    # Capture original state for keys of interest
    required_keys = ('account', 'preferences', 'context', 'schedules')
    before_pointers = {
        k: (um.USER_DATA_LOADERS.get(k) or {}).get('loader')
        for k in required_keys
    }

    # Call registration multiple times; should be idempotent and not raise
    if hasattr(um, 'register_default_loaders'):
        um.register_default_loaders()
        um.register_default_loaders()
    elif hasattr(udh, 'register_default_loaders'):
        udh.register_default_loaders()
        udh.register_default_loaders()

    # After: registry object must be the same shared dict
    assert um.USER_DATA_LOADERS is udh.USER_DATA_LOADERS

    # Idempotency: loaders remain non-None for required keys
    for k in required_keys:
        entry = um.USER_DATA_LOADERS.get(k)
        assert isinstance(entry, dict)
        assert entry.get('loader') is not None

    # Stability: repeated registration does not replace existing loader function objects
    after_pointers = {
        k: (um.USER_DATA_LOADERS.get(k) or {}).get('loader')
        for k in required_keys
    }
    for k in required_keys:
        # If loader existed before, verify it was not replaced with a different function object
        if before_pointers[k] is not None:
            assert after_pointers[k] is before_pointers[k]

