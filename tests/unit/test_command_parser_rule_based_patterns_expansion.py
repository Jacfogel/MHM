"""
Expanded unit coverage for rule-based command parsing patterns.

These tests exercise the pattern routing without invoking AI parsing.
"""

import pytest

from communication.message_processing.command_parser import EnhancedCommandParser


@pytest.fixture(scope="module")
def command_parser():
    """Create EnhancedCommandParser instance once per module."""
    return EnhancedCommandParser()


def _rule_parse(command_parser, message: str):
    return command_parser._rule_based_parse(message)


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestCommandParserTaskPatterns:
    @pytest.mark.parametrize(
        "message, expected_title",
        [
            ("nt buy milk", "buy milk"),
            ("ntask call mom", "call mom"),
            ("newt clean room", "clean room"),
            ("newtask file taxes", "file taxes"),
            ("ct finish report", "finish report"),
            ("ctask review notes", "review notes"),
            ("createtask pay rent", "pay rent"),
            ("createt plan trip", "plan trip"),
            ("task update docs", "update docs"),
            ("create task to fix bug", "fix bug"),
            ("add a task to vacuum", "vacuum"),
            ("new task to buy eggs", "buy eggs"),
            ("i need to stretch", "stretch"),
            ("remind me to drink water", "drink water"),
            ("call dentist tomorrow", "dentist"),
            ("buy groceries next week", "groceries"),
            ("schedule meeting on monday", "meeting"),
            ("create task about planning", "about planning"),
            ("add task to write tests", "write tests"),
            ("new task to submit report", "submit report"),
        ],
    )
    def test_create_task_patterns(self, command_parser, message, expected_title):
        result = _rule_parse(command_parser, message)

        assert result.method == "rule_based"
        assert result.parsed_command.intent == "create_task"
        assert result.parsed_command.entities.get("title") == expected_title

    @pytest.mark.parametrize(
        "message",
        [
            "show my tasks",
            "show tasks",
            "list my tasks",
            "list tasks",
            "what are my tasks",
            "what are tasks",
            "my tasks",
            "tasks due",
            "what do i have to do today",
            "what are my tasks for tomorrow",
            "show me my tasks",
        ],
    )
    def test_list_tasks_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "list_tasks"

    @pytest.mark.parametrize(
        "message, expected_identifier",
        [
            ("complete 1", "1"),
            ("complete task 2", "2"),
            ("done task 3", "3"),
            ("finished task 4", "4"),
            ("mark task 5 complete", "5"),
            ("complete teeth", "teeth"),
            ("done laundry", "laundry"),
            ("finished bugfix", "bugfix"),
        ],
    )
    def test_complete_task_patterns(self, command_parser, message, expected_identifier):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "complete_task"
        assert result.parsed_command.entities.get("task_identifier") == expected_identifier

    @pytest.mark.parametrize(
        "message, expected_identifier",
        [
            ("delete task 1", "1"),
            ("delete 2", "2"),
            ("remove task 3", "3"),
            ("remove 4", "4"),
            ("cancel task 5", "5"),
            ("cancel 6", "6"),
        ],
    )
    def test_delete_task_patterns(self, command_parser, message, expected_identifier):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "delete_task"
        assert result.parsed_command.entities.get("task_identifier") == expected_identifier

    @pytest.mark.parametrize(
        "message, expected_identifier, expected_priority, expected_title, expected_due",
        [
            ("update task 1 priority high", "1", "high", None, None),
            ("change task 2 priority low", "2", "low", None, None),
            ("edit task 3 due date tomorrow", "3", None, None, "tomorrow"),
            ("update task 4 title New Title", "4", None, "new title", None),
            ("change task 5 rename to Fix bug", "5", None, "fix bug", None),
            ("edit task 6 priority urgent due next week", "6", "urgent", None, "next week"),
            ("update task 7 title \"Plan trip\"", "7", None, "plan trip", None),
            ("change task 8 rename to \"Review notes\"", "8", None, "review notes", None),
            ("edit task 9 due friday", "9", None, None, "friday"),
            ("update task 10 priority medium", "10", "medium", None, None),
        ],
    )
    def test_update_task_patterns(
        self,
        command_parser,
        message,
        expected_identifier,
        expected_priority,
        expected_title,
        expected_due,
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "update_task"
        entities = result.parsed_command.entities
        assert entities.get("task_identifier") == expected_identifier
        if expected_priority is not None:
            assert entities.get("priority") == expected_priority
        if expected_title is not None:
            assert entities.get("title") == expected_title
        if expected_due is not None:
            assert entities.get("due_date") == expected_due

@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.checkins
class TestCommandParserCheckinPatterns:
    @pytest.mark.parametrize(
        "message",
        [
            "start check-in",
            "start checkin",
            "begin check-in",
            "i want to check in",
            "i want to have a check in",
            "let me check in",
            "daily check-in",
            "check in",
            "checkin",
            "checkin now",
            "can i check in",
            "can i have a checkin",
        ],
    )
    def test_start_checkin_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "start_checkin"

    @pytest.mark.parametrize(
        "message",
        [
            "checkin status",
            "show checkins",
            "how am i doing overall",
            "checkin progress",
        ],
    )
    def test_checkin_status_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "checkin_status"

    @pytest.mark.parametrize(
        "message",
        [
            "checkin history",
            "checkin-history",
            "show my checkin history",
            "my checkin history",
            "checkin records",
            "past checkins",
            "checkin log",
            "tell me about my checkin history",
        ],
    )
    def test_checkin_history_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "checkin_history"

    def test_checkin_history_entities(self, command_parser):
        result = _rule_parse(command_parser, "checkin history last 2 weeks")
        assert result.parsed_command.intent == "checkin_history"
        assert result.parsed_command.entities.get("days") == 14

        result = _rule_parse(command_parser, "checkin-history last 7 days")
        assert result.parsed_command.intent == "checkin_history"
        assert result.parsed_command.entities.get("days") == 7

        result = _rule_parse(command_parser, "checkin history last month")
        assert result.parsed_command.intent == "checkin_history"
        assert result.parsed_command.entities.get("days") == 30

        result = _rule_parse(command_parser, "checkin-history last 3 checkins")
        assert result.parsed_command.intent == "checkin_history"
        assert result.parsed_command.entities.get("limit") == 3

        result = _rule_parse(command_parser, "last 3 checkins")
        assert result.parsed_command.intent == "checkin_history"
        assert result.parsed_command.entities.get("limit") == 3

    @pytest.mark.parametrize(
        "message",
        [
            "checkin analysis",
            "checkin analytics",
            "analyze my checkins",
            "checkin insights",
            "checkin trends",
            "analyze checkin responses",
            "checkin-analysis",
        ],
    )
    def test_checkin_analysis_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "checkin_analysis"

    @pytest.mark.parametrize(
        "message",
        [
            "completion rate",
            "what is my completion rate",
            "completion percentage",
        ],
    )
    def test_completion_rate_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "completion_rate"


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.user_management
class TestCommandParserProfilePatterns:
    @pytest.mark.parametrize(
        "message",
        [
            "show profile",
            "show my profile",
            "my profile",
            "view profile",
            "display my profile",
        ],
    )
    def test_show_profile_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "show_profile"

    @pytest.mark.parametrize(
        "message",
        [
            "update profile",
            "change profile",
            "edit profile",
        ],
    )
    def test_update_profile_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "update_profile"

    @pytest.mark.parametrize(
        "message",
        [
            "profile stats",
            "my statistics",
            "my stats",
            "show my stats",
        ],
    )
    def test_profile_stats_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "profile_stats"


@pytest.mark.unit
@pytest.mark.communication
class TestCommandParserHelpPatterns:
    @pytest.mark.parametrize(
        "message, expected_intent",
        [
            ("help", "help"),
            ("help tasks", "help"),
            ("help checkin", "help"),
            ("help profile", "help"),
            ("what can you do", "help"),
            ("how do i use this", "help"),
            ("how do i create a task", "help"),
            ("how do i create tasks", "help"),
            ("how to create a task", "help"),
            ("how to create tasks", "help"),
            ("commands", "commands"),
            ("available commands", "commands"),
            ("list commands", "commands"),
            ("examples", "examples"),
            ("examples tasks", "examples"),
            ("show examples", "examples"),
            ("give me examples", "examples"),
            ("status", "status"),
            ("system status", "status"),
            ("my status", "status"),
            ("messages", "messages"),
            ("show messages", "messages"),
            ("message history", "messages"),
            ("recent messages", "messages"),
        ],
    )
    def test_help_and_misc_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.scheduler
class TestCommandParserSchedulePatterns:
    @pytest.mark.parametrize(
        "message, expected_category",
        [
            ("show schedule", "all"),
            ("show my schedule", "all"),
            ("schedule for tasks", "tasks"),
            ("schedule for checkins", "checkins"),
        ],
    )
    def test_show_schedule_patterns(self, command_parser, message, expected_category):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "show_schedule"
        assert result.parsed_command.entities.get("category") == expected_category

    @pytest.mark.parametrize(
        "message, expected_action, expected_category",
        [
            ("update schedule", None, None),
            ("enable tasks schedule", "enable", "tasks"),
            ("turn on tasks schedule", "on", "tasks"),
            ("turn off checkins schedule", "off", "checkins"),
        ],
    )
    def test_update_schedule_patterns(
        self, command_parser, message, expected_action, expected_category
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "update_schedule"
        if expected_action:
            assert result.parsed_command.entities.get("action") == expected_action
        if expected_category:
            assert result.parsed_command.entities.get("category") == expected_category

    @pytest.mark.parametrize(
        "message, expected_period, expected_category",
        [
            ("add a period called morning to my tasks schedule from 9am to 11am", "morning", "tasks"),
        ],
    )
    def test_add_schedule_period_patterns(
        self,
        command_parser,
        message,
        expected_period,
        expected_category,
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "add_schedule_period"
        entities = result.parsed_command.entities
        assert entities.get("period_name") == expected_period
        assert entities.get("category") == expected_category

@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.analytics
class TestCommandParserAnalyticsPatterns:
    @pytest.mark.parametrize(
        "message, expected_days",
        [
            ("show analytics", 30),
            ("show-analytics", 30),
            ("show my analytics", 30),
            ("analytics for 7 days", 7),
            ("show trends", 30),
            ("show-trends", 30),
            ("mood trends", 30),
            ("mood trends 14 days", 14),
            ("mood for 10 days", 10),
            ("mood history", 30),
            ("mood graphs", 30),
            ("mood-graphs", 30),
            ("mood trends last month", 30),
            ("energy trends", 30),
            ("energy trends 14 days", 14),
            ("energy for 7 days", 7),
            ("energy history", 30),
            ("energy graphs", 30),
            ("energy-graphs", 30),
            ("energy trends last week", 7),
            ("quant summary", 30),
            ("habit analysis", 30),
            ("habit-analysis", 30),
            ("habit analysis last 2 weeks", 14),
            ("habit trends", 30),
            ("habit history", 30),
            ("habit for 21 days", 21),
            ("sleep analysis", 30),
            ("sleep-analysis", 30),
            ("sleep analysis last 3 months", 90),
            ("sleep trends", 30),
            ("sleep history", 30),
            ("sleep for 5 days", 5),
            ("wellness score", 30),
            ("wellness for 3 days", 3),
        ],
    )
    def test_analytics_patterns(self, command_parser, message, expected_days):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent in {
            "show_analytics",
            "mood_trends",
            "energy_trends",
            "quant_summary",
            "habit_analysis",
            "sleep_analysis",
            "wellness_score",
        }
        assert result.parsed_command.entities.get("days") == expected_days


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.notebook
class TestCommandParserNotebookPatterns:
    @pytest.mark.parametrize(
        "message, expected_intent",
        [
            ("nn Title", "create_note"),
            ("newnote Title", "create_note"),
            ("n Title: Body", "create_note"),
            ("note Title", "create_note"),
            ("create note titled \"Idea\" with body \"Body\"", "create_note"),
            ("create note titled \"Idea\"", "create_note"),
            ("create note titled Idea with body \"Body\"", "create_note"),
            ("create note about Things", "create_note"),
            ("new note: Quick idea", "create_note"),
            ("note: Another idea", "create_note"),
            ("qn Quick", "create_quick_note"),
            ("qnote Fast", "create_quick_note"),
            ("quicknote Rapid", "create_quick_note"),
            ("q note Short", "create_quick_note"),
            ("quick note Idea", "create_quick_note"),
            ("j Journal entry", "create_journal"),
            ("journal Entry", "create_journal"),
            ("newjournal Entry", "create_journal"),
            ("create journal entry Today", "create_journal"),
        ],
    )
    def test_notebook_create_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent

    @pytest.mark.parametrize(
        "message, expected_intent",
        [
            ("recent", "list_recent_entries"),
            ("recent 3", "list_recent_entries"),
            ("r", "list_recent_entries"),
            ("r 5", "list_recent_entries"),
            ("recentn", "list_recent_notes"),
            ("recentn 2", "list_recent_notes"),
            ("rnote 4", "list_recent_notes"),
            ("rnotes 6", "list_recent_notes"),
            ("shown 7", "list_recent_notes"),
            ("shownotes 8", "list_recent_notes"),
        ],
    )
    def test_recent_list_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent

    @pytest.mark.parametrize(
        "message, expected_intent",
        [
            ("show n123", "show_entry"),
            ("display l456", "show_entry"),
            ("view j789", "show_entry"),
            ("append n111 Add text", "append_to_entry"),
            ("add n222 More text", "append_to_entry"),
            ("set n333 Replace body", "set_entry_body"),
            ("replace n444 Updated body", "set_entry_body"),
            ("tag n555 #work", "add_tags_to_entry"),
            ("untag n777 #old", "remove_tags_from_entry"),
            ("search notes", "search_entries"),
            ("s urgent", "search_entries"),
            ("find ideas", "search_entries"),
            ("pin n123", "pin_entry"),
            ("unpin n456", "unpin_entry"),
            ("archive n789", "archive_entry"),
            ("unarchive n321", "unarchive_entry"),
        ],
    )
    def test_notebook_action_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent

    @pytest.mark.parametrize(
        "message, expected_intent",
        [
            ("l Groceries: Milk, Bread", "create_list"),
            ("list Chores: sweep; mop", "create_list"),
            ("newlist Errands", "create_list"),
            ("l new Projects", "create_list"),
            ("new list Tasks", "create_list"),
            ("group n123 work", "set_entry_group"),
            ("group n123 personal", "set_entry_group"),
            ("group work", "list_entries_by_group"),
            ("tag urgent", "list_entries_by_tag"),
        ],
    )
    def test_notebook_list_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent
