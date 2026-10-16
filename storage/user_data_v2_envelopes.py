"""
Canonical v2 on-disk envelope validation dispatcher.

Task and notebook persistence models live in ``tasks.task_schemas`` and
``notebook.notebook_schemas``. Message and check-in persistence models live in
``messages.message_schemas`` and ``checkins.checkin_schemas``. Shared item
primitives are in ``user_data_v2_base``.
"""

from __future__ import annotations

from typing import Any

from checkins.checkin_schemas import validate_checkins_v2_document
from messages.message_schemas import (
    validate_deliveries_v2_document,
    validate_messages_v2_document,
)
from notebook.notebook_validation import validate_notebook_v2_document
from tasks.task_validation import validate_tasks_v2_document
from core.profile_v2_schemas import (
    validate_account_v2_document,
    validate_chat_interactions_v2_document,
    validate_context_v2_document,
    validate_preferences_v2_document,
    validate_schedules_v2_document,
    validate_tags_v2_document,
)

# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_v2_document(document_type: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 document and return normalized data plus validation errors."""
    if document_type == "tasks":
        return validate_tasks_v2_document(data)
    if document_type == "notebook":
        return validate_notebook_v2_document(data)
    if document_type == "checkins":
        return validate_checkins_v2_document(data)
    if document_type == "messages":
        return validate_messages_v2_document(data)
    if document_type == "deliveries":
        return validate_deliveries_v2_document(data)
    if document_type == "account":
        return validate_account_v2_document(data)
    if document_type == "preferences":
        return validate_preferences_v2_document(data)
    if document_type == "schedules":
        return validate_schedules_v2_document(data)
    if document_type == "context":
        return validate_context_v2_document(data)
    if document_type == "tags":
        return validate_tags_v2_document(data)
    if document_type == "chat_interactions":
        return validate_chat_interactions_v2_document(data)
    return data, [f"Unknown v2 document type: {document_type}"]
