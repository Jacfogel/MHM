from unittest.mock import Mock, patch

import pytest

from ui import scheduler_actions


pytestmark = [pytest.mark.ui, pytest.mark.unit]


def test_run_full_scheduler_sets_delivery_factory_and_runs():
    delivery_factory = Mock()
    run_full = Mock(return_value=True)
    set_factory = Mock()

    def fake_load_attr(_module_name, attr_name):
        return {
            "run_full_scheduler_standalone": run_full,
            "set_scheduler_delivery_factory": set_factory,
        }[attr_name]

    with patch("ui.scheduler_actions._load_attr", side_effect=fake_load_attr):
        assert scheduler_actions.run_full_scheduler(delivery_factory) is True

    set_factory.assert_called_once_with(delivery_factory)
    run_full.assert_called_once_with()


def test_run_user_scheduler_delegates_selected_user():
    run_user = Mock(return_value=True)

    with patch("ui.scheduler_actions._load_attr", return_value=run_user):
        assert scheduler_actions.run_user_scheduler("test-user") is True

    run_user.assert_called_once_with("test-user")


def test_run_category_scheduler_delegates_user_and_category():
    run_category = Mock(return_value=True)

    with patch("ui.scheduler_actions._load_attr", return_value=run_category):
        assert scheduler_actions.run_category_scheduler("test-user", "health") is True

    run_category.assert_called_once_with("test-user", "health")
