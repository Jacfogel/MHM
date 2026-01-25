"""
Expanded unit coverage for notebook and schedule entity extraction helpers.
"""

import re

import pytest

from communication.message_processing.command_parser import EnhancedCommandParser


@pytest.fixture(scope="module")
def command_parser():
    """Create EnhancedCommandParser instance once per module."""
    return EnhancedCommandParser()


def _extract_entities(command_parser, intent, pattern, message):
    match = re.search(pattern, message, re.IGNORECASE)
    assert match is not None, f"Pattern did not match: {pattern} -> {message}"
    return command_parser._extract_entities_rule_based(intent, match, message)


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.notebook
class TestCommandParserNotebookEntityExtraction:
    """Coverage expansion for notebook-focused entity extraction."""

    @pytest.mark.parametrize(
        "pattern, message, expected_title, expected_body",
        [
            (r"^n\s+(.+)$", "n Title: Body", "Title", "Body"),
            (r"^note\s+(.+)$", "note Title only", "Title only", None),
            (r"^note\s+(.+)$", "note Title: Body line", "Title", "Body line"),
            (
                r'create\s+note\s+titled\s+"([^"]+)"\s+with\s+body\s+"([^"]+)"',
                'create note titled "T1" with body "B1"',
                "T1",
                "B1",
            ),
            (
                r'create\s+note\s+titled\s+"([^"]+)"',
                'create note titled "T2"',
                "T2",
                None,
            ),
            (
                r'create\s+note\s+titled\s+([^\s]+)\s+with\s+body\s+"([^"]+)"',
                'create note titled T3 with body "B3"',
                "T3",
                "B3",
            ),
            (r"new\s+note:\s*(.+)", "new note: Quick idea", "Quick idea", None),
            (r"note:\s*(.+)", "note: Title: Body", "Title", "Body"),
            (r"new\s+note\s+(.+)", "new note Something", "Something", None),
            (r"note\s+(.+)", "note Title: Body with colon", "Title", "Body with colon"),
        ],
    )
    def test_extract_entities_create_note(
        self, command_parser, pattern, message, expected_title, expected_body
    ):
        entities = _extract_entities(command_parser, "create_note", pattern, message)

        assert entities.get("title") == expected_title
        assert entities.get("body") == expected_body

    @pytest.mark.parametrize(
        "pattern, message, expected_title",
        [
            (r"^qn\s*(.*)$", "qn", None),
            (r"^qnote\s*(.*)$", "qnote Quick", "Quick"),
            (r"^quicknote\s*(.*)$", "quicknote Fast", "Fast"),
            (r"^q\s+note\s*(.*)$", "q note Short", "Short"),
            (r"quick\s+note\s*(.*)$", "quick note Idea", "Idea"),
            (r"^qn\s*(.*)$", "qn   ", None),
        ],
    )
    def test_extract_entities_create_quick_note(
        self, command_parser, pattern, message, expected_title
    ):
        entities = _extract_entities(command_parser, "create_quick_note", pattern, message)

        assert entities.get("title") == expected_title
        assert entities.get("body") is None

    @pytest.mark.parametrize(
        "pattern, message, expected_limit",
        [
            (r"^recent(?:\s+(\d+))?$", "recent 10", 10),
            (r"^recent(?:\s+(\d+))?$", "recent", 5),
            (r"^r(?:\s+(\d+))?$", "r 2", 2),
            (r"^r(?:\s+(\d+))?$", "r", 5),
        ],
    )
    def test_extract_entities_list_recent_entries(
        self, command_parser, pattern, message, expected_limit
    ):
        entities = _extract_entities(
            command_parser, "list_recent_entries", pattern, message
        )

        assert entities.get("limit") == expected_limit

    @pytest.mark.parametrize(
        "pattern, message, expected_limit",
        [
            (r"^recentn(?:\s+(\d+))?$", "recentn 3", 3),
            (r"^recentn(?:\s+(\d+))?$", "recentn", 5),
            (r"^rnote(?:\s+(\d+))?$", "rnote 4", 4),
            (r"^rnote(?:\s+(\d+))?$", "rnote", 5),
        ],
    )
    def test_extract_entities_list_recent_notes(
        self, command_parser, pattern, message, expected_limit
    ):
        entities = _extract_entities(
            command_parser, "list_recent_notes", pattern, message
        )

        assert entities.get("limit") == expected_limit

    @pytest.mark.parametrize(
        "pattern, message, expected_tags",
        [
            (r"^tag\s+(\S+)\s+(.+)$", "tag n123 #work urgent", ["work", "urgent"]),
            (
                r"add\s+tags?\s+to\s+(\S+)\s+(.+)",
                "add tags to n123 #one #two three",
                ["one", "two", "three"],
            ),
            (r"^tag\s+(\S+)\s+(.+)$", "tag n123 urgent", ["urgent"]),
        ],
    )
    def test_extract_entities_add_tags(
        self, command_parser, pattern, message, expected_tags
    ):
        entities = _extract_entities(command_parser, "add_tags_to_entry", pattern, message)

        assert entities.get("tags") == expected_tags

    @pytest.mark.parametrize(
        "pattern, message, expected_tags",
        [
            (r"^untag\s+(\S+)\s+(.+)$", "untag n123 #old stale", ["old", "stale"]),
            (
                r"remove\s+tags?\s+from\s+(\S+)\s+(.+)",
                "remove tags from n123 #one #two",
                ["one", "two"],
            ),
            (r"^untag\s+(\S+)\s+(.+)$", "untag n123 stale", ["stale"]),
        ],
    )
    def test_extract_entities_remove_tags(
        self, command_parser, pattern, message, expected_tags
    ):
        entities = _extract_entities(
            command_parser, "remove_tags_from_entry", pattern, message
        )

        assert entities.get("tags") == expected_tags

    @pytest.mark.parametrize(
        "pattern, message, expected_title, expected_items, expected_tags",
        [
            (
                r"^l\s+(.+)$",
                "l Groceries: Milk, Bread",
                "Groceries",
                ["Milk", "Bread"],
                [],
            ),
            (
                r"^l\s+(.+)$",
                "l Chores: sweep; mop",
                "Chores",
                ["sweep", "mop"],
                [],
            ),
            (
                r"^l\s+(.+)$",
                "l Plans: one, two",
                "Plans",
                ["one", "two"],
                [],
            ),
            (r"^l\s+(.+)$", "l Tasks", "Tasks", [], []),
            (
                r"^l\s+(.+)$",
                "l Weekend #home #fun: clean",
                "Weekend",
                ["clean"],
                ["home", "fun"],
            ),
            (
                r"^l\s+(.+)$",
                "l Work #proj: update",
                "Work",
                ["update"],
                ["proj"],
            ),
        ],
    )
    def test_extract_entities_create_list(
        self,
        command_parser,
        pattern,
        message,
        expected_title,
        expected_items,
        expected_tags,
    ):
        entities = _extract_entities(command_parser, "create_list", pattern, message)

        assert entities.get("title") == expected_title
        assert entities.get("items") == expected_items
        assert entities.get("tags", []) == expected_tags

    @pytest.mark.parametrize(
        "intent, pattern, message, expected_index, expected_done",
        [
            ("toggle_list_item_done", r"^l\s+done\s+(\S+)\s+(\d+)$", "l done l123 2", 2, None),
            (
                "toggle_list_item_done",
                r"^l\s+done\s+(\S+)\s+(\d+)$",
                "l done l999 1",
                1,
                None,
            ),
            (
                "toggle_list_item_undone",
                r"^l\s+undone\s+(\S+)\s+(\d+)$",
                "l undone l123 3",
                3,
                False,
            ),
            (
                "toggle_list_item_undone",
                r"^l\s+undone\s+(\S+)\s+(\d+)$",
                "l undone l555 4",
                4,
                False,
            ),
        ],
    )
    def test_extract_entities_toggle_list_items(
        self, command_parser, intent, pattern, message, expected_index, expected_done
    ):
        entities = _extract_entities(command_parser, intent, pattern, message)

        assert entities.get("item_index") == expected_index
        if expected_done is None:
            assert "done" not in entities
        else:
            assert entities.get("done") is expected_done

    @pytest.mark.parametrize(
        "intent, pattern, message, expected_text",
        [
            ("append_to_entry", r"^append\s+(\S+)\s+(.+)$", "append n123 more text", "more text"),
            ("append_to_entry", r"^add\s+(\S+)\s+(.+)$", "add n123 extra", "extra"),
            ("set_entry_body", r"^set\s+(\S+)\s+(.+)$", "set n123 New body", "New body"),
            ("set_entry_body", r"^replace\s+(\S+)\s+(.+)$", "replace n123 Updated", "Updated"),
        ],
    )
    def test_extract_entities_entry_text_changes(
        self, command_parser, intent, pattern, message, expected_text
    ):
        entities = _extract_entities(command_parser, intent, pattern, message)

        assert entities.get("text") == expected_text
        if intent == "set_entry_body":
            assert entities.get("body") == expected_text

    @pytest.mark.parametrize(
        "pattern, message, expected_ref",
        [
            (r"^show\s+(.+)$", "show n123abc", "n123abc"),
            (r"^display\s+(.+)$", "display l999xyz", "l999xyz"),
            (r"^view\s+(.+)$", "view j555aaa", "j555aaa"),
        ],
    )
    def test_extract_entities_show_entry(
        self, command_parser, pattern, message, expected_ref
    ):
        entities = _extract_entities(command_parser, "show_entry", pattern, message)

        assert entities.get("entry_ref") == expected_ref

    @pytest.mark.parametrize(
        "pattern, message, expected_query",
        [
            (r"^search\s+(.+)$", "search meeting notes", "meeting notes"),
            (r"^s\s+(.+)$", "s travel plans", "travel plans"),
            (r"find\s+(.+)", "find urgent tasks", "urgent tasks"),
        ],
    )
    def test_extract_entities_search_entries(
        self, command_parser, pattern, message, expected_query
    ):
        entities = _extract_entities(command_parser, "search_entries", pattern, message)

        assert entities.get("query") == expected_query


@pytest.mark.unit
@pytest.mark.communication
class TestCommandParserScheduleAndAnalyticsExtraction:
    """Coverage expansion for schedule and analytics entity extraction."""

    @pytest.mark.parametrize(
        "intent, pattern, message, expected_entities",
        [
            (
                "show_schedule",
                r"schedule\s+for\s+(tasks?)",
                "schedule for tasks",
                {"category": "tasks"},
            ),
            (
                "show_schedule",
                r"show\s+schedule",
                "show schedule",
                {"category": "all"},
            ),
            (
                "update_schedule",
                r"turn\s+(on|off)\s+(?:my\s+)?(tasks?)\s+schedule",
                "turn on tasks schedule",
                {"action": "on", "category": "tasks"},
            ),
            (
                "update_schedule",
                r"enable\s+(?:my\s+)?(messages?)\s+schedule",
                "enable my messages schedule",
                {"action": "enable", "category": "messages"},
            ),
            (
                "add_schedule_period",
                r"add\s+(?:a\s+)?period\s+called\s+(\w+)\s+to\s+(?:my\s+)?(\w+)\s+schedule",
                "add a period called morning to my tasks schedule from 9am to 11am",
                {
                    "period_name": "morning",
                    "category": "tasks",
                    "start_time": "9am",
                    "end_time": "11am",
                },
            ),
            (
                "edit_schedule_period",
                r"edit\s+(?:the\s+)?(\w+)\s+period\s+in\s+(?:my\s+)?(\w+)\s+schedule",
                "edit morning period in my tasks schedule to 9am to 11am",
                {
                    "period_name": "morning",
                    "category": "tasks",
                    "new_start_time": "9am",
                    "new_end_time": "11am",
                },
            ),
        ],
    )
    def test_extract_entities_schedule(
        self, command_parser, intent, pattern, message, expected_entities
    ):
        entities = _extract_entities(command_parser, intent, pattern, message)

        for key, value in expected_entities.items():
            assert entities.get(key) == value

    @pytest.mark.parametrize(
        "intent, pattern, message, expected_days",
        [
            ("show_analytics", r"analytics\s+(?:for\s+)?(\d+)\s+days?", "analytics for 7 days", 7),
            ("mood_trends", r"mood\s+(?:for\s+)?(\d+)\s+days?", "mood for 14 days", 14),
            ("habit_analysis", r"habit\s+(?:for\s+)?(\d+)\s+days?", "habit for 30 days", 30),
            ("sleep_analysis", r"sleep\s+(?:for\s+)?(\d+)\s+days?", "sleep for 21 days", 21),
        ],
    )
    def test_extract_entities_analytics_days(
        self, command_parser, intent, pattern, message, expected_days
    ):
        entities = _extract_entities(command_parser, intent, pattern, message)

        assert entities.get("days") == expected_days
