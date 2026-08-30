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
            ("remind me to take medication every morning at 8am", "take medication"),
            ("create task to water plants every 2 weeks", "water plants"),
            ("i should pick up groceries tonight", "pick up groceries"),
            ("dont forget to email the school", "email the school"),
            ("don't forget to email the school", "email the school"),
            ("please create a task for laundry", "laundry"),
            ("i have to pay rent", "pay rent"),
            ("remember to submit forms", "submit forms"),
            ("i gotta call mom", "call mom"),
            ("gotta pick up groceries", "pick up groceries"),
            ("need to pick up groceries", "pick up groceries"),
            ("put laundry on my list", "laundry"),
            ("add laundry to my list", "laundry"),
            ("make a reminder to call the school", "call the school"),
            ("i still need to pay rent", "pay rent"),
            ("i also need to email the school", "email the school"),
            ("i'm supposed to call the school", "call the school"),
            ("i am supposed to call the school", "call the school"),
            ("i've got to take meds", "take meds"),
            ("ive gotta call mom", "call mom"),
            ("don't let me forget to take meds", "take meds"),
            ("dont let me forget to take meds", "take meds"),
            ("make sure i take meds", "take meds"),
            ("make sure to submit forms", "submit forms"),
        ],
    )
    def test_create_task_patterns(self, command_parser, message, expected_title):
        result = _rule_parse(command_parser, message)

        assert result.method == "rule_based"
        assert result.parsed_command.intent == "create_task"
        assert result.parsed_command.entities.get("title") == expected_title

    @pytest.mark.parametrize(
        "message, expect_confirm",
        [
            ("i should pick up groceries tonight", True),
            ("i gotta call mom", True),
            ("i need to stretch", True),
            ("i still need to pay rent", True),
            ("i'm supposed to call the school", True),
            ("dont forget to email the school", False),
            ("add laundry to my list", False),
            ("remind me to drink water", False),
            ("don't let me forget to take meds", False),
        ],
    )
    def test_soft_create_task_sets_confirm(
        self, command_parser, message, expect_confirm
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "create_task"
        assert bool(result.parsed_command.entities.get("confirm")) is expect_confirm

    def test_create_task_captures_url_as_link(self, command_parser):
        result = _rule_parse(
            command_parser,
            "remind me to fill out this form https://example.com/form tomorrow",
        )
        assert result.parsed_command.intent == "create_task"
        assert result.parsed_command.entities.get("title") == "fill out this form"
        assert result.parsed_command.entities.get("links") == [
            {"url": "https://example.com/form"}
        ]
        assert result.parsed_command.entities.get("due_date") == "tomorrow"

    @pytest.mark.parametrize(
        "message, expected_title, expected_pattern, expected_interval, expected_due_time",
        [
            (
                "remind me to take medication every morning at 8am",
                "take medication",
                "daily",
                1,
                "8am",
            ),
            (
                "create task to water plants every 2 weeks",
                "water plants",
                "weekly",
                2,
                None,
            ),
            (
                "new task to take out trash every Sunday",
                "take out trash",
                "weekly",
                1,
                None,
            ),
        ],
    )
    def test_create_task_recurring_natural_language_patterns(
        self,
        command_parser,
        message,
        expected_title,
        expected_pattern,
        expected_interval,
        expected_due_time,
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "create_task"
        entities = result.parsed_command.entities
        assert entities.get("title") == expected_title
        assert entities.get("recurrence_pattern") == expected_pattern
        assert entities.get("recurrence_interval") == expected_interval
        if expected_due_time is not None:
            assert entities.get("due_time") == expected_due_time

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
            "what is on my list",
            "what's on my list",
            "whats on my list",
            "what is on my todo",
            "what is on the task list",
            "show my list",
            "show my task list",
            "show my todo",
            "show my to-do",
            "whats left",
            "what's left",
            "what do i still need to do",
            "what's on my plate",
            "show overdue tasks",
            "overdue tasks",
            "what's due",
            "whats due",
            "what is due",
            "what's overdue",
            "what do i have due",
        ],
    )
    def test_list_tasks_patterns(self, command_parser, message):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "list_tasks"

    @pytest.mark.parametrize(
        "message, expected_group",
        [
            ("show tasks in group work", "work"),
            ("list tasks group:medical", "medical"),
            ("tasks in group chores", "chores"),
        ],
    )
    def test_list_tasks_group_filter_patterns(
        self, command_parser, message, expected_group
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "list_tasks"
        assert result.parsed_command.entities.get("group") == expected_group

    @pytest.mark.parametrize(
        "message, expected_filter",
        [
            ("show overdue tasks", "overdue"),
            ("overdue tasks", "overdue"),
            ("what's overdue", "overdue"),
            ("what's due", "due_soon"),
            ("whats due", "due_soon"),
            ("what is due", "due_soon"),
            ("what do i have due", "due_soon"),
        ],
    )
    def test_list_tasks_due_filter_patterns(
        self, command_parser, message, expected_filter
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "list_tasks"
        assert result.parsed_command.entities.get("filter") == expected_filter

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
            ("mark dentist done", "dentist"),
            ("mark the dentist task done", "dentist"),
            ("i completed the dentist task", "dentist"),
            ("can you complete my dentist task", "dentist"),
            ("i already did the dentist", "dentist"),
            ("take dentist off my list", "dentist"),
            ("cross off dentist", "dentist"),
            ("check off the dentist task", "dentist"),
            ("scratch dentist off my list", "dentist"),
            ("i'm done with laundry", "laundry"),
            ("i am done with the dentist", "dentist"),
            ("i got the dishes done", "dishes"),
            ("mark that done", "that"),
            ("cross that off", "that"),
            ("i'm done with that", "that"),
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
            ("update task 1 note Room 204 bring card", "1", None, None, None),
            ("update the dentist task to high priority", "dentist", "high", None, None),
            ("make that due tomorrow", "that", None, None, "tomorrow"),
            ("can you make that due tomorrow", "that", None, None, "tomorrow"),
            ("that's urgent", "that", "urgent", None, None),
            ("that's high priority", "that", "high", None, None),
            ("make that urgent", "that", "urgent", None, None),
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
        if "note room 204" in message.lower():
            assert entities.get("description") == "room 204 bring card"

    @pytest.mark.parametrize(
        "message",
        ["that's okay", "that's a lot", "I can't deal with that"],
    )
    def test_emotional_that_is_not_update_task(self, command_parser, message):
        result = _rule_parse(command_parser, message)
        intent = result.parsed_command.intent
        assert intent != "update_task"
        assert intent != "complete_task"


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestCommandParserAppendNoteToTaskPatterns:
    @pytest.mark.parametrize(
        "message, expected_identifier, expected_note",
        [
            (
                "append note to task 1 call back before 5pm",
                "1",
                "call back before 5pm",
            ),
            (
                "add note to task 2 insurance form on counter",
                "2",
                "insurance form on counter",
            ),
            (
                "append note to call dentist phone 555-1234",
                "call dentist phone",
                "555-1234",
            ),
            (
                "add a note to the dentist task: they need X-rays",
                "dentist",
                "they need x-rays",
            ),
            (
                "add a note to task 3: insurance form on counter",
                "3",
                "insurance form on counter",
            ),
            (
                "add a note to that: bring the insurance card",
                "that",
                "bring the insurance card",
            ),
        ],
    )
    def test_append_note_to_task_patterns(
        self, command_parser, message, expected_identifier, expected_note
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "append_note_to_task"
        entities = result.parsed_command.entities
        assert entities.get("task_identifier") == expected_identifier
        assert entities.get("note_text") == expected_note


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestCommandParserTaskLinkPatterns:
    @pytest.mark.parametrize(
        "message, expected_identifier, expected_url, expected_label",
        [
            (
                "add link to task 1 https://example.com/form",
                "1",
                "https://example.com/form",
                None,
            ),
            (
                "add a link to the dentist task: https://example.com/form",
                "dentist",
                "https://example.com/form",
                None,
            ),
            (
                "add the portal link to the dentist task: https://example.com/form",
                "dentist",
                "https://example.com/form",
                "portal",
            ),
            (
                "save this link on task 2 https://example.com/a",
                "2",
                "https://example.com/a",
                None,
            ),
            (
                "add link to task 1 https://example.com/Form",
                "1",
                "https://example.com/Form",
                None,
            ),
        ],
    )
    def test_add_link_to_task_patterns(
        self,
        command_parser,
        message,
        expected_identifier,
        expected_url,
        expected_label,
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "add_link_to_task"
        entities = result.parsed_command.entities
        assert entities.get("task_identifier") == expected_identifier
        assert entities.get("link_url") == expected_url
        assert entities.get("link_label") == expected_label

    def test_remove_link_from_task_pattern(self, command_parser):
        result = _rule_parse(
            command_parser, "remove link from task 1 https://example.com/form"
        )
        assert result.parsed_command.intent == "remove_link_from_task"
        assert result.parsed_command.entities.get("task_identifier") == "1"
        assert (
            result.parsed_command.entities.get("link_url") == "https://example.com/form"
        )

    def test_add_note_still_does_not_match_add_link(self, command_parser):
        result = _rule_parse(
            command_parser, "add a note to the dentist task: they need X-rays"
        )
        assert result.parsed_command.intent == "append_note_to_task"


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
@pytest.mark.user
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

    def test_bare_how_am_i_doing_is_not_status_intent(self, command_parser):
        """Wellness phrasing should reach contextual chat, not the system status dashboard."""
        result = _rule_parse(command_parser, "how am i doing")

        assert result.parsed_command.intent != "status"


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
            ("jot down that I talked to the doctor", "create_note"),
            ("can you jot down that I talked to the doctor", "create_note"),
            ("write down the wifi password", "create_note"),
            ("make a note of the gate code", "create_note"),
            ("note to self: buy oat milk", "create_note"),
            ("remember that my favorite tea is chamomile", "create_note"),
            ("add a note about the meeting", "create_note"),
            ("keep in mind that the gate code is 1234", "create_note"),
            ("write this down: wifi is on the fridge", "create_note"),
            ("put this in my notes: appointment at 3", "create_note"),
            ("don't let me forget that the gate code is 1234", "create_note"),
            ("qn Quick", "create_quick_note"),
            ("qnote Fast", "create_quick_note"),
            ("quicknote Rapid", "create_quick_note"),
            ("q note Short", "create_quick_note"),
            ("quick note Idea", "create_quick_note"),
            ("quick notes Idea", "create_quick_note"),
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
        "message, expected_title, expected_description",
        [
            (
                "jot down that I talked to the doctor",
                "i talked to the doctor",
                "i talked to the doctor",
            ),
            (
                "write down the wifi password",
                "the wifi password",
                "the wifi password",
            ),
            (
                "make a note of the gate code",
                "the gate code",
                "the gate code",
            ),
            (
                "note to self: buy oat milk",
                "buy oat milk",
                "buy oat milk",
            ),
            (
                "remember that my favorite tea is chamomile",
                "my favorite tea is chamomile",
                "my favorite tea is chamomile",
            ),
            (
                "jot down that I talked to the doctor about sleep and they want melatonin",
                "i talked to the doctor about sleep and",
                "i talked to the doctor about sleep and they want melatonin",
            ),
            (
                "add a note about the meeting",
                "the meeting",
                "the meeting",
            ),
            (
                "keep in mind that the gate code is 1234",
                "the gate code is 1234",
                "the gate code is 1234",
            ),
            (
                "write this down: wifi is on the fridge",
                "wifi is on the fridge",
                "wifi is on the fridge",
            ),
            (
                "don't let me forget that the gate code is 1234",
                "the gate code is 1234",
                "the gate code is 1234",
            ),
        ],
    )
    def test_notebook_capture_phrases_save_body(
        self, command_parser, message, expected_title, expected_description
    ):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == "create_note"
        entities = result.parsed_command.entities
        assert entities.get("title") == expected_title
        assert entities.get("description") == expected_description

    def test_i_remember_that_is_not_create_note(self, command_parser):
        result = _rule_parse(
            command_parser, "I remember that I felt sad yesterday"
        )

        assert result.parsed_command.intent != "create_note"

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
            ("show my notes", "list_recent_notes"),
            ("show notes", "list_recent_notes"),
            ("what's in my notebook", "list_recent_notes"),
            ("what is in my notebook", "list_recent_notes"),
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
            ("edit n123abc", "edit_entry"),
            ("editn MeetingNotes", "edit_entry"),
            ("edit note Meeting Notes", "edit_entry"),
            ("edit entry GroceryList", "edit_entry"),
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
            ("group n123abc work", "set_entry_group"),
            ("group n123abc personal", "set_entry_group"),
            ("setgroup GroceryList home", "set_entry_group"),
            ("set group GroceryList home", "set_entry_group"),
            ("group work", "list_entries_by_group"),
            ("group Quick Notes", "list_entries_by_group"),
            ("tag urgent", "list_entries_by_tag"),
        ],
    )
    def test_notebook_list_patterns(self, command_parser, message, expected_intent):
        result = _rule_parse(command_parser, message)

        assert result.parsed_command.intent == expected_intent

    @pytest.mark.parametrize(
        "message, expected_intent, expected_entities",
        [
            (
                "group n123abc home",
                "set_entry_group",
                {"entry_ref": "n123abc", "group": "home"},
            ),
            (
                "setgroup MeetingNotes work",
                "set_entry_group",
                {"entry_ref": "meetingnotes", "group": "work"},
            ),
            (
                "group Quick Notes",
                "list_entries_by_group",
                {"group": "quick notes"},
            ),
            (
                "group GroceryList home",
                "list_entries_by_group",
                {"group": "grocerylist home"},
            ),
            (
                "group home",
                "list_entries_by_group",
                {"group": "home"},
            ),
        ],
    )
    def test_notebook_group_command_disambiguation(
        self, command_parser, message, expected_intent, expected_entities
    ):
        """Bare multi-word !group lists; set requires short-id/UUID or setgroup."""
        result = _rule_parse(command_parser, message)
        assert result.parsed_command.intent == expected_intent
        for key, value in expected_entities.items():
            assert result.parsed_command.entities.get(key) == value
