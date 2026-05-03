"""notebook_service re-exports notebook_data_manager entry points."""

import pytest

import notebook.notebook_data_manager as ndm
import notebook.notebook_service as ns


@pytest.mark.unit
@pytest.mark.notebook
def test_notebook_service_functions_are_data_manager_aliases():
    assert ns.create_note is ndm.create_note
    assert ns.search_entries is ndm.search_entries
    assert ns.get_entry is ndm.get_entry
    assert ns.list_recent is ndm.list_recent
