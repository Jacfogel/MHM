"""Guardrails that keep message bodies out of runtime logs."""

import ast
from pathlib import Path

import pytest


pytestmark = [pytest.mark.unit, pytest.mark.core]

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_ROOTS = ("ai", "communication", "core", "messages")
_LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}
_CONTENT_NAMES = {
    "ai_response",
    "content",
    "message",
    "message_preview",
    "message_to_send",
    "response_data",
    "selected_message_content",
    "test_message",
    "user_message",
}
_SAFE_TRANSFORMS = {"len", "type"}


class _RawContentReference(ast.NodeVisitor):
    """Find message variables unless they are used only for length or type metadata."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_TRANSFORMS:
            return
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in {"body", "content", "message", "text"}:
            self.names.add(node.attr)
        # Do not treat identifiers such as message.author.id as message content.

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _CONTENT_NAMES:
            self.names.add(node.id)


def test_runtime_log_calls_do_not_include_message_content() -> None:
    """Reject direct logging of inbound, generated, or persisted message bodies."""
    violations: list[str] = []
    for root_name in _RUNTIME_ROOTS:
        for path in (_PROJECT_ROOT / root_name).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in _LOG_METHODS:
                    continue
                finder = _RawContentReference()
                for value in [*node.args, *(item.value for item in node.keywords)]:
                    finder.visit(value)
                if finder.names:
                    relative = path.relative_to(_PROJECT_ROOT)
                    names = ", ".join(sorted(finder.names))
                    violations.append(f"{relative}:{node.lineno} ({names})")

    assert violations == [], "Message content reaches log calls:\n" + "\n".join(violations)
