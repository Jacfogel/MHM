"""Unit tests for shared external short IDs in core.ids."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from core.ids import (
    DEFAULT_SHORT_ID_LENGTH,
    TASK_PREFIX,
    display_short_id,
    format_short_id,
    generate_short_id,
    is_dashed_short_id,
    looks_like_short_id,
    parse_short_id,
)
from notebook.notebook_data_manager import _find_entry_by_ref
from notebook.notebook_schemas import Entry
from notebook.notebook_validation import is_valid_entry_reference, looks_like_structural_entry_ref

pytestmark = [pytest.mark.unit, pytest.mark.core]


@pytest.mark.unit
def test_generate_short_id_prefixes_for_notebook_and_task():
    uid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert generate_short_id(uid, "note").startswith("n")
    assert generate_short_id(uid, "list").startswith("l")
    assert generate_short_id(uid, "journal_entry").startswith("j")
    assert generate_short_id(uid, "task").startswith(TASK_PREFIX)
    for kind in ("note", "list", "journal_entry", "task"):
        sid = generate_short_id(uid, kind)
        assert "-" not in sid
        assert len(sid) == 1 + DEFAULT_SHORT_ID_LENGTH
        assert sid == generate_short_id(uid, kind)


@pytest.mark.unit
def test_parse_short_id_task_prefix():
    assert parse_short_id("tabc123") == ("t", "abc123")
    assert parse_short_id("TABCDEF") == ("t", "abcdef")
    assert looks_like_short_id("tabc123") is True
    assert looks_like_short_id("t" + "-" + "abc123") is False
    assert is_dashed_short_id("t" + "-" + "abc123") is True
    assert is_dashed_short_id("n" + "-" + "3f2a9c") is True


@pytest.mark.unit
def test_generate_parse_round_trip_notebook_and_task():
    uid = uuid4()
    for kind, prefix in (
        ("note", "n"),
        ("list", "l"),
        ("journal_entry", "j"),
        ("task", "t"),
    ):
        sid = generate_short_id(str(uid), kind)
        parsed = parse_short_id(sid)
        assert parsed == (prefix, str(uid).replace("-", "")[:DEFAULT_SHORT_ID_LENGTH])
        assert format_short_id(uid, kind) == sid


@pytest.mark.unit
def test_display_short_id_prefers_persisted():
    assert display_short_id(short_id="tcustom1", record_id=uuid4(), kind="task") == "tcustom1"
    uid = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    generated = display_short_id(record_id=uid, kind="task")
    assert generated.startswith("t")
    assert len(generated) == 7


@pytest.mark.unit
def test_notebook_rejects_task_short_id_as_entry_ref():
    assert is_valid_entry_reference("t3f2a9c") is False
    assert looks_like_structural_entry_ref("t3f2a9c") is True  # structural, not a title
    assert looks_like_short_id("t3f2a9c") is True


@pytest.mark.unit
@pytest.mark.notebook
def test_find_entry_by_persisted_short_id():
    eid = UUID("11111111-1111-4111-8111-111111111111")
    entry = Entry(
        id=eid,
        kind="note",
        title="Alpha",
        short_id="nabcdef",
        description="body",
    )
    assert _find_entry_by_ref([entry], "nabcdef") is entry
    assert _find_entry_by_ref([entry], "NABCDEF") is entry


@pytest.mark.unit
@pytest.mark.notebook
def test_find_entry_rejects_task_prefix_without_title_fallback():
    entry = Entry(
        id=UUID("22222222-2222-4222-8222-222222222222"),
        kind="note",
        title="tabc123 note title",
        description="body",
    )
    # Wrong-domain short id must not resolve via title contains
    assert _find_entry_by_ref([entry], "tabc123") is None


@pytest.mark.unit
@pytest.mark.notebook
def test_find_entry_exact_short_id_wins_over_ambiguous_fragment():
    first = Entry(
        id=UUID("aaaaaa11-1111-4111-8111-111111111111"),
        kind="note",
        title="First",
        short_id="n111aaa",
        description="a",
    )
    second = Entry(
        id=UUID("aaaaaa22-2222-4222-8222-222222222222"),
        kind="note",
        title="Second",
        short_id="n222bbb",
        description="b",
    )
    # Fragment collision still returns first (documented ambiguity)
    assert _find_entry_by_ref([first, second], "naaaaaa") is first
    # Exact persisted short_id wins
    assert _find_entry_by_ref([first, second], "n222bbb") is second
