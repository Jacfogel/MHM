import itertools
from unittest.mock import MagicMock, patch

import pytest

from core.service_utilities import wait_for_network


@pytest.mark.unit
def test_wait_for_network_closes_connection_on_success():
    mock_connection = MagicMock()
    with patch("core.service_utilities.socket.create_connection", return_value=mock_connection):
        assert wait_for_network(timeout=0.1) is True

    mock_connection.close.assert_called_once()


@pytest.mark.unit
def test_wait_for_network_skips_close_when_connection_fails():
    time_values = itertools.chain([0, 0, 2], itertools.repeat(2))
    with patch("core.service_utilities.socket.create_connection", side_effect=OSError("network down")) as mock_create, \
            patch("core.service_utilities.time.sleep", return_value=None), \
            patch("core.service_utilities.time.time", side_effect=lambda: next(time_values)):
        assert wait_for_network(timeout=1) is False

    mock_create.return_value.close.assert_not_called()
