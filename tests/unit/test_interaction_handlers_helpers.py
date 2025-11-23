"""
Unit tests for interaction handlers helper methods.

Tests for communication/command_handlers/interaction_handlers.py focusing on
helper methods and utility functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from communication.command_handlers.interaction_handlers import TaskManagementHandler


@pytest.mark.unit
@pytest.mark.communication
class TestTaskManagementHandlerHelpers:
    """Test helper methods in TaskManagementHandler."""

    def setup_method(self):
        """Set up test environment."""
        self.handler = TaskManagementHandler()

    def test_parse_relative_date_today(self):
        """Test _handle_create_task__parse_relative_date with 'today'."""
        result = self.handler._handle_create_task__parse_relative_date("today")
        expected = datetime.now().strftime('%Y-%m-%d')
        assert result == expected, "Should return today's date"

    def test_parse_relative_date_tomorrow(self):
        """Test _handle_create_task__parse_relative_date with 'tomorrow'."""
        result = self.handler._handle_create_task__parse_relative_date("tomorrow")
        expected = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        assert result == expected, "Should return tomorrow's date"

    def test_parse_relative_date_next_week(self):
        """Test _handle_create_task__parse_relative_date with 'next week'."""
        result = self.handler._handle_create_task__parse_relative_date("next week")
        expected = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        assert result == expected, "Should return date 7 days from now"

    def test_parse_relative_date_next_month(self):
        """Test _handle_create_task__parse_relative_date with 'next month'."""
        result = self.handler._handle_create_task__parse_relative_date("next month")
        today = datetime.now()
        if today.month == 12:
            expected = today.replace(year=today.year + 1, month=1).strftime('%Y-%m-%d')
        else:
            expected = today.replace(month=today.month + 1).strftime('%Y-%m-%d')
        assert result == expected, "Should return next month's date"

    def test_parse_relative_date_already_formatted(self):
        """Test _handle_create_task__parse_relative_date with already formatted date."""
        date_str = "2024-12-25"
        result = self.handler._handle_create_task__parse_relative_date(date_str)
        assert result == date_str, "Should return date as-is if already formatted"

    def test_parse_relative_date_case_insensitive(self):
        """Test _handle_create_task__parse_relative_date is case insensitive."""
        result_upper = self.handler._handle_create_task__parse_relative_date("TODAY")
        result_lower = self.handler._handle_create_task__parse_relative_date("today")
        assert result_upper == result_lower, "Should handle case insensitively"

    def test_apply_filters_due_soon(self):
        """Test _handle_list_tasks__apply_filters with 'due_soon' filter."""
        tasks = [
            {'title': 'Task 1', 'due_date': '2024-12-20'},
            {'title': 'Task 2', 'due_date': '2024-12-30'}
        ]
        
        with patch('communication.command_handlers.interaction_handlers.get_tasks_due_soon', return_value=[tasks[0]]):
            result = self.handler._handle_list_tasks__apply_filters("user", tasks, 'due_soon', None, None)
            assert len(result) == 1, "Should return only due soon tasks"
            assert result[0]['title'] == 'Task 1', "Should return correct task"

    def test_apply_filters_overdue(self):
        """Test _handle_list_tasks__apply_filters with 'overdue' filter."""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        tasks = [
            {'title': 'Overdue Task', 'due_date': yesterday},
            {'title': 'Future Task', 'due_date': tomorrow}
        ]
        
        result = self.handler._handle_list_tasks__apply_filters("user", tasks, 'overdue', None, None)
        assert len(result) == 1, "Should return only overdue tasks"
        assert result[0]['title'] == 'Overdue Task', "Should return correct task"

    def test_apply_filters_high_priority(self):
        """Test _handle_list_tasks__apply_filters with 'high_priority' filter."""
        tasks = [
            {'title': 'High Priority Task', 'priority': 'high'},
            {'title': 'Low Priority Task', 'priority': 'low'}
        ]
        
        result = self.handler._handle_list_tasks__apply_filters("user", tasks, 'high_priority', None, None)
        assert len(result) == 1, "Should return only high priority tasks"
        assert result[0]['title'] == 'High Priority Task', "Should return correct task"

    def test_apply_filters_priority_filter(self):
        """Test _handle_list_tasks__apply_filters with priority filter."""
        tasks = [
            {'title': 'High Task', 'priority': 'high'},
            {'title': 'Medium Task', 'priority': 'medium'},
            {'title': 'Low Task', 'priority': 'low'}
        ]
        
        result = self.handler._handle_list_tasks__apply_filters("user", tasks, None, 'medium', None)
        assert len(result) == 1, "Should return only medium priority tasks"
        assert result[0]['title'] == 'Medium Task', "Should return correct task"

    def test_apply_filters_tag_filter(self):
        """Test _handle_list_tasks__apply_filters with tag filter."""
        tasks = [
            {'title': 'Tagged Task', 'tags': ['work', 'urgent']},
            {'title': 'Other Task', 'tags': ['personal']}
        ]
        
        result = self.handler._handle_list_tasks__apply_filters("user", tasks, None, None, 'work')
        assert len(result) == 1, "Should return only tasks with matching tag"
        assert result[0]['title'] == 'Tagged Task', "Should return correct task"

    def test_apply_filters_combined(self):
        """Test _handle_list_tasks__apply_filters with combined filters."""
        tasks = [
            {'title': 'Task 1', 'priority': 'high', 'tags': ['work']},
            {'title': 'Task 2', 'priority': 'high', 'tags': ['personal']},
            {'title': 'Task 3', 'priority': 'low', 'tags': ['work']}
        ]
        
        result = self.handler._handle_list_tasks__apply_filters("user", tasks, None, 'high', 'work')
        assert len(result) == 1, "Should return tasks matching all filters"
        assert result[0]['title'] == 'Task 1', "Should return correct task"

    def test_sort_tasks_by_priority(self):
        """Test _handle_list_tasks__sort_tasks sorts by priority."""
        tasks = [
            {'title': 'Low Task', 'priority': 'low'},
            {'title': 'High Task', 'priority': 'high'},
            {'title': 'Medium Task', 'priority': 'medium'}
        ]
        
        result = self.handler._handle_list_tasks__sort_tasks(tasks)
        assert result[0]['title'] == 'High Task', "High priority should come first"
        assert result[1]['title'] == 'Medium Task', "Medium priority should come second"
        assert result[2]['title'] == 'Low Task', "Low priority should come last"

    def test_sort_tasks_by_due_date(self):
        """Test _handle_list_tasks__sort_tasks sorts by due date within same priority."""
        tasks = [
            {'title': 'Task 1', 'priority': 'high', 'due_date': '2024-12-25'},
            {'title': 'Task 2', 'priority': 'high', 'due_date': '2024-12-20'},
            {'title': 'Task 3', 'priority': 'high', 'due_date': '2024-12-30'}
        ]
        
        result = self.handler._handle_list_tasks__sort_tasks(tasks)
        assert result[0]['title'] == 'Task 2', "Earlier due date should come first"
        assert result[1]['title'] == 'Task 1', "Middle due date should come second"
        assert result[2]['title'] == 'Task 3', "Later due date should come last"

    def test_sort_tasks_with_none_due_date(self):
        """Test _handle_list_tasks__sort_tasks handles None due_date."""
        tasks = [
            {'title': 'Task 1', 'priority': 'high', 'due_date': None},
            {'title': 'Task 2', 'priority': 'high', 'due_date': '2024-12-20'}
        ]
        
        result = self.handler._handle_list_tasks__sort_tasks(tasks)
        assert result[0]['title'] == 'Task 2', "Task with due_date should come before None"
        assert result[1]['title'] == 'Task 1', "Task with None due_date should come last"

    def test_format_due_date_overdue(self):
        """Test _handle_list_tasks__format_due_date for overdue tasks."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        result = self.handler._handle_list_tasks__format_due_date(yesterday)
        assert "OVERDUE" in result, "Should indicate overdue status"
        assert yesterday in result, "Should include date"

    def test_format_due_date_today(self):
        """Test _handle_list_tasks__format_due_date for today."""
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.handler._handle_list_tasks__format_due_date(today)
        assert "TODAY" in result, "Should indicate due today"
        assert today in result, "Should include date"

    def test_format_due_date_future(self):
        """Test _handle_list_tasks__format_due_date for future dates."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        result = self.handler._handle_list_tasks__format_due_date(tomorrow)
        assert "due:" in result, "Should indicate due date"
        assert tomorrow in result, "Should include date"

    def test_format_due_date_none(self):
        """Test _handle_list_tasks__format_due_date with None."""
        result = self.handler._handle_list_tasks__format_due_date(None)
        assert result == "", "Should return empty string for None"

    def test_build_filter_info_all_filters(self):
        """Test _handle_list_tasks__build_filter_info with all filters."""
        result = self.handler._handle_list_tasks__build_filter_info('due_soon', 'high', 'work')
        assert len(result) == 3, "Should include all filter types"
        assert any('due_soon' in f for f in result), "Should include filter type"
        assert any('high' in f for f in result), "Should include priority"
        assert any('work' in f for f in result), "Should include tag"

    def test_build_filter_info_partial(self):
        """Test _handle_list_tasks__build_filter_info with partial filters."""
        result = self.handler._handle_list_tasks__build_filter_info('overdue', None, None)
        assert len(result) == 1, "Should include only provided filters"
        assert 'overdue' in result[0], "Should include filter type"

    def test_build_filter_info_none(self):
        """Test _handle_list_tasks__build_filter_info with no filters."""
        result = self.handler._handle_list_tasks__build_filter_info(None, None, None)
        assert result == [], "Should return empty list when no filters"

    def test_no_tasks_response_due_soon(self):
        """Test _handle_list_tasks__no_tasks_response for due_soon filter."""
        result = self.handler._handle_list_tasks__no_tasks_response('due_soon', None, None)
        assert isinstance(result.message, str), "Should return InteractionResponse"
        assert "due" in result.message.lower(), "Should mention due date"

    def test_no_tasks_response_overdue(self):
        """Test _handle_list_tasks__no_tasks_response for overdue filter."""
        result = self.handler._handle_list_tasks__no_tasks_response('overdue', None, None)
        assert "overdue" in result.message.lower(), "Should mention overdue"

    def test_no_tasks_response_priority(self):
        """Test _handle_list_tasks__no_tasks_response for priority filter."""
        result = self.handler._handle_list_tasks__no_tasks_response(None, 'high', None)
        assert "high" in result.message.lower(), "Should mention priority"

    def test_no_tasks_response_tag(self):
        """Test _handle_list_tasks__no_tasks_response for tag filter."""
        result = self.handler._handle_list_tasks__no_tasks_response(None, None, 'work')
        assert "work" in result.message.lower(), "Should mention tag"

    def test_no_tasks_response_default(self):
        """Test _handle_list_tasks__no_tasks_response with no filters."""
        result = self.handler._handle_list_tasks__no_tasks_response(None, None, None)
        assert "no active tasks" in result.message.lower(), "Should mention no active tasks"

    def test_get_task_candidates_by_exact_id(self):
        """Test _get_task_candidates with exact task_id."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._get_task_candidates(tasks, 'abc123')
        assert len(result) == 1, "Should return single match"
        assert result[0]['title'] == 'Task 1', "Should return correct task"

    def test_get_task_candidates_by_short_id(self):
        """Test _get_task_candidates with 8-character short id."""
        tasks = [
            {'task_id': 'abcdef1234567890', 'title': 'Task 1'},
            {'task_id': 'def4567890123456', 'title': 'Task 2'}
        ]
        
        result = self.handler._get_task_candidates(tasks, 'abcdef12')
        assert len(result) == 1, "Should return single match for short id"
        assert result[0]['title'] == 'Task 1', "Should return correct task"

    def test_get_task_candidates_by_number(self):
        """Test _get_task_candidates with task number."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._get_task_candidates(tasks, '1')
        assert len(result) == 1, "Should return single match for number"
        assert result[0]['title'] == 'Task 1', "Should return correct task"

    def test_get_task_candidates_by_exact_title(self):
        """Test _get_task_candidates with exact title match."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Buy groceries'},
            {'task_id': 'def456', 'title': 'Call mom'}
        ]
        
        result = self.handler._get_task_candidates(tasks, 'Buy groceries')
        assert len(result) == 1, "Should return single match for exact title"
        assert result[0]['title'] == 'Buy groceries', "Should return correct task"

    def test_get_task_candidates_by_partial_title(self):
        """Test _get_task_candidates with partial title match."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Buy groceries'},
            {'task_id': 'def456', 'title': 'Buy milk'}
        ]
        
        result = self.handler._get_task_candidates(tasks, 'groceries')
        assert len(result) >= 1, "Should return matches for partial title"
        assert any(t['title'] == 'Buy groceries' for t in result), "Should include matching task"

    def test_get_task_candidates_no_match(self):
        """Test _get_task_candidates with no matching tasks."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._get_task_candidates(tasks, 'nonexistent')
        assert result == [], "Should return empty list for no matches"

    def test_find_task_by_identifier_exact_id(self):
        """Test _handle_complete_task__find_task_by_identifier with exact task_id."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, 'abc123')
        assert result is not None, "Should find task"
        assert result['title'] == 'Task 1', "Should return correct task"

    def test_find_task_by_identifier_short_id(self):
        """Test _handle_complete_task__find_task_by_identifier with 8-character short id."""
        tasks = [
            {'task_id': 'abcdef1234567890', 'title': 'Task 1'},
            {'task_id': 'def4567890123456', 'title': 'Task 2'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, 'abcdef12')
        assert result is not None, "Should find task"
        assert result['title'] == 'Task 1', "Should return correct task"

    def test_find_task_by_identifier_number(self):
        """Test _handle_complete_task__find_task_by_identifier with task number."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, '2')
        assert result is not None, "Should find task"
        assert result['title'] == 'Task 2', "Should return correct task"

    def test_find_task_by_identifier_exact_title(self):
        """Test _handle_complete_task__find_task_by_identifier with exact title."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Buy groceries'},
            {'task_id': 'def456', 'title': 'Call mom'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, 'Buy groceries')
        assert result is not None, "Should find task"
        assert result['title'] == 'Buy groceries', "Should return correct task"

    def test_find_task_by_identifier_partial_title(self):
        """Test _handle_complete_task__find_task_by_identifier with partial title."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Buy groceries'},
            {'task_id': 'def456', 'title': 'Call mom'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, 'groceries')
        assert result is not None, "Should find task"
        assert result['title'] == 'Buy groceries', "Should return correct task"

    def test_find_task_by_identifier_no_match(self):
        """Test _handle_complete_task__find_task_by_identifier with no match."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1'},
            {'task_id': 'def456', 'title': 'Task 2'}
        ]
        
        result = self.handler._handle_complete_task__find_task_by_identifier(tasks, 'nonexistent')
        assert result is None, "Should return None for no match"

    def test_find_most_urgent_task_overdue(self):
        """Test _handle_complete_task__find_most_urgent_task prioritizes overdue tasks."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        tasks = [
            {'task_id': 'abc123', 'title': 'Future Task', 'priority': 'high', 'due_date': tomorrow},
            {'task_id': 'def456', 'title': 'Overdue Task', 'priority': 'low', 'due_date': yesterday}
        ]
        
        result = self.handler._handle_complete_task__find_most_urgent_task(tasks)
        assert result is not None, "Should find task"
        assert result['title'] == 'Overdue Task', "Should prioritize overdue task"

    def test_find_most_urgent_task_priority(self):
        """Test _handle_complete_task__find_most_urgent_task prioritizes by priority."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        tasks = [
            {'task_id': 'abc123', 'title': 'Low Priority', 'priority': 'low', 'due_date': tomorrow},
            {'task_id': 'def456', 'title': 'High Priority', 'priority': 'high', 'due_date': tomorrow}
        ]
        
        result = self.handler._handle_complete_task__find_most_urgent_task(tasks)
        assert result is not None, "Should find task"
        assert result['title'] == 'High Priority', "Should prioritize high priority"

    def test_find_most_urgent_task_due_today(self):
        """Test _handle_complete_task__find_most_urgent_task prioritizes tasks due today."""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        tasks = [
            {'task_id': 'abc123', 'title': 'Due Tomorrow', 'priority': 'high', 'due_date': tomorrow},
            {'task_id': 'def456', 'title': 'Due Today', 'priority': 'high', 'due_date': today}
        ]
        
        result = self.handler._handle_complete_task__find_most_urgent_task(tasks)
        assert result is not None, "Should find task"
        assert result['title'] == 'Due Today', "Should prioritize task due today"

    def test_find_most_urgent_task_empty_list(self):
        """Test _handle_complete_task__find_most_urgent_task with empty list."""
        result = self.handler._handle_complete_task__find_most_urgent_task([])
        assert result is None, "Should return None for empty list"

    def test_format_list_basic(self):
        """Test _handle_list_tasks__format_list formats tasks correctly."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1', 'priority': 'high', 'due_date': '2024-12-20'}
        ]
        
        result = self.handler._handle_list_tasks__format_list(tasks)
        assert isinstance(result, list), "Should return list"
        assert len(result) == 1, "Should format one task"
        assert 'Task 1' in result[0], "Should include task title"
        assert '🔴' in result[0], "Should include priority emoji"

    def test_format_list_with_tags(self):
        """Test _handle_list_tasks__format_list includes tags."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1', 'priority': 'medium', 'tags': ['work', 'urgent']}
        ]
        
        result = self.handler._handle_list_tasks__format_list(tasks)
        assert 'work' in result[0], "Should include tags"
        assert 'urgent' in result[0], "Should include all tags"

    def test_format_list_with_description(self):
        """Test _handle_list_tasks__format_list includes description."""
        tasks = [
            {'task_id': 'abc123', 'title': 'Task 1', 'priority': 'low', 'description': 'Test description'}
        ]
        
        result = self.handler._handle_list_tasks__format_list(tasks)
        assert 'Test description' in result[0], "Should include description"

    def test_format_list_limits_to_10(self):
        """Test _handle_list_tasks__format_list limits to 10 tasks."""
        tasks = [{'task_id': f'abc{i}', 'title': f'Task {i}', 'priority': 'medium'} for i in range(15)]
        
        result = self.handler._handle_list_tasks__format_list(tasks)
        assert len(result) == 10, "Should limit to 10 tasks"

