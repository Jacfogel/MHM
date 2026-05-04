"""Unit tests for channel-neutral pagination helpers."""

import pytest

from core.pagination import PageRequest, paginate_items


@pytest.mark.unit
@pytest.mark.core
def test_page_request_uses_default_for_invalid_limit() -> None:
    request = PageRequest.from_values(
        limit="not-a-number",
        offset=0,
        default_limit=5,
        max_limit=25,
    )

    assert request.limit == 5


@pytest.mark.unit
@pytest.mark.core
def test_page_request_uses_zero_for_invalid_offset() -> None:
    request = PageRequest.from_values(
        limit=5,
        offset="bad-offset",
        default_limit=5,
        max_limit=25,
    )

    assert request.offset == 0


@pytest.mark.unit
@pytest.mark.core
def test_page_request_caps_limit() -> None:
    request = PageRequest.from_values(
        limit=100,
        offset=0,
        default_limit=5,
        max_limit=25,
    )

    assert request.limit == 25


@pytest.mark.unit
@pytest.mark.core
def test_paginate_items_handles_empty_results() -> None:
    page = paginate_items([], PageRequest(limit=5, offset=0))

    assert page.items == []
    assert page.total == 0
    assert page.has_more is False
    assert page.next_offset is None
    assert page.remaining_count == 0


@pytest.mark.unit
@pytest.mark.core
def test_paginate_items_reports_more_results() -> None:
    page = paginate_items([1, 2, 3, 4, 5], PageRequest(limit=2, offset=1))

    assert page.items == [2, 3]
    assert page.has_more is True
    assert page.next_offset == 3
    assert page.remaining_count == 2


@pytest.mark.unit
@pytest.mark.core
def test_paginate_items_handles_exact_final_page() -> None:
    page = paginate_items([1, 2, 3, 4, 5, 6], PageRequest(limit=3, offset=3))

    assert page.items == [4, 5, 6]
    assert page.has_more is False
    assert page.next_offset is None
    assert page.remaining_count == 0


@pytest.mark.unit
@pytest.mark.core
def test_paginate_items_handles_no_more_results_after_partial_page() -> None:
    page = paginate_items([1, 2, 3, 4, 5], PageRequest(limit=3, offset=3))

    assert page.items == [4, 5]
    assert page.has_more is False
    assert page.next_offset is None
    assert page.remaining_count == 0


@pytest.mark.unit
@pytest.mark.core
def test_paginate_items_handles_offset_past_available_results() -> None:
    page = paginate_items([1, 2, 3], PageRequest(limit=2, offset=10))

    assert page.items == []
    assert page.has_more is False
    assert page.next_offset is None
    assert page.remaining_count == 0
