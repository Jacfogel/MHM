"""Unit tests for shared Discord item form field parsing."""

import pytest


@pytest.mark.unit
@pytest.mark.communication
def test_parse_modal_tags_comma_and_hash():
    from communication.communication_channels.discord.item_form_shared import (
        parse_modal_tags,
    )

    assert parse_modal_tags("health, work, #urgent") == ["health", "work", "urgent"]


@pytest.mark.unit
@pytest.mark.communication
def test_entities_from_shared_fields_merges_title_tags():
    from communication.communication_channels.discord.item_form_shared import (
        entities_from_shared_fields,
    )

    entities = entities_from_shared_fields(
        title="Call dentist #health",
        description="Insurance follow-up",
        group="medical",
        due_phrase="tomorrow",
    )
    assert entities["title"] == "Call dentist"
    assert "health" in entities["tags"]
    assert entities["group"] == "medical"
    assert entities["due_date"] == "tomorrow"
    assert entities["description"] == "Insurance follow-up"
