"""Channel-neutral pagination helpers."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.error_handling import handle_errors


T = TypeVar("T")


@dataclass(frozen=True)
class PageRequest:
    """Normalized pagination request."""

    limit: int
    offset: int

    @classmethod
    @handle_errors("building pagination request", default_return=None, user_friendly=False)
    def from_values(
        cls,
        *,
        limit: object,
        offset: object,
        default_limit: int,
        max_limit: int | None = None,
    ) -> "PageRequest":
        """Build a request from untrusted pagination inputs."""
        return cls(
            limit=coerce_limit(limit, default_limit, max_limit),
            offset=coerce_offset(offset),
        )


@dataclass(frozen=True)
class PageResult(Generic[T]):
    """Result of applying a page request to a sequence."""

    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool
    next_offset: int | None

    @property
    @handle_errors("calculating remaining page count", default_return=0, user_friendly=False)
    def remaining_count(self) -> int:
        """Number of items after this page."""
        return max(self.total - (self.offset + self.limit), 0)


def coerce_limit(
    value: object, default: int, maximum: int | None = None
) -> int:
    """Return a bounded positive integer for pagination limits."""
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    if maximum is not None:
        return min(parsed, maximum)
    return parsed


def coerce_offset(value: object) -> int:
    """Return a non-negative integer for pagination offsets."""
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


@handle_errors(
    "paginating items",
    default_return=PageResult(
        items=[],
        total=0,
        limit=0,
        offset=0,
        has_more=False,
        next_offset=None,
    ),
    user_friendly=False,
)
def paginate_items(
    items: Sequence[T],
    request: PageRequest,
) -> PageResult[T]:
    """Apply a normalized page request to a sequence."""
    total = len(items)
    page_items = list(items[request.offset : request.offset + request.limit])
    has_more = request.offset + request.limit < total
    next_offset = request.offset + request.limit if has_more else None
    return PageResult(
        items=page_items,
        total=total,
        limit=request.limit,
        offset=request.offset,
        has_more=has_more,
        next_offset=next_offset,
    )
