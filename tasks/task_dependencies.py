"""Pure helpers for maintaining task dependency relationships."""

from __future__ import annotations

from typing import Any


def task_id(task: dict[str, Any]) -> str:
    """Return the canonical ID used in dependency records."""
    # ERROR_HANDLING_EXCLUDE: Pure in-memory helper; guarded callers own failures.
    return str(task.get("id") or "").strip()


def _matches(task: dict[str, Any], reference: str) -> bool:
    """Match a non-empty reference against the task's full or short ID, ignoring case."""
    # ERROR_HANDLING_EXCLUDE: Pure in-memory helper; guarded callers own failures.
    candidate = str(reference or "").strip().casefold()
    return bool(candidate) and candidate in {
        task_id(task).casefold(),
        str(task.get("short_id") or "").strip().casefold(),
    }


def normalize_dependency_references(value: Any) -> list[str] | None:
    """Normalize a list of dependency references, or reject a non-list payload."""
    # ERROR_HANDLING_EXCLUDE: Pure validation helper returns invalid input as data.
    if not isinstance(value, list):
        return None
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            return None
        reference = item.strip()
        key = reference.casefold()
        if not reference or key in seen:
            continue
        seen.add(key)
        normalized.append(reference)
    return normalized


def _resolved_ids(
    tasks: list[dict[str, Any]], target_id: str, references: Any
) -> tuple[list[str] | None, str | None]:
    """Resolve active prerequisites to unique task IDs or return a validation error."""
    # ERROR_HANDLING_EXCLUDE: Pure validation helper returns errors as data.
    normalized = normalize_dependency_references(references)
    if normalized is None:
        return None, "Dependencies must be a list of task IDs"

    resolved: list[str] = []
    for reference in normalized:
        match = next((task for task in tasks if _matches(task, reference)), None)
        if match is None:
            return None, f"Dependency task '{reference}' is not active"
        dependency_id = task_id(match)
        if dependency_id == target_id:
            return None, "A task cannot block itself"
        if dependency_id not in resolved:
            resolved.append(dependency_id)
    return resolved, None


def _has_path(
    graph: dict[str, list[str]], start: str, destination: str, seen: set[str]
) -> bool:
    """Check whether following prerequisites reaches the destination, recording visited IDs."""
    # ERROR_HANDLING_EXCLUDE: Bounded recursive graph walk has guarded callers.
    if start == destination:
        return True
    if start in seen:
        return False
    seen.add(start)
    return any(_has_path(graph, item, destination, seen) for item in graph.get(start, []))


def apply_dependencies(
    tasks: list[dict[str, Any]], target: dict[str, Any], references: Any
) -> tuple[bool, str | None]:
    """Set one task's prerequisites and rebuild inverse relationships in place."""
    # ERROR_HANDLING_EXCLUDE: Pure mutation helper returns errors as data.
    resolved, reason = validate_dependencies(tasks, target, references)
    if resolved is None:
        return False, reason

    target["blocked_by"] = resolved
    rebuild_inverse_relationships(tasks)
    return True, None


def validate_dependencies(
    tasks: list[dict[str, Any]], target: dict[str, Any], references: Any
) -> tuple[list[str] | None, str | None]:
    """Resolve and validate prerequisites without mutating the task graph."""
    # ERROR_HANDLING_EXCLUDE: Pure validation helper returns errors as data.
    target_id = task_id(target)
    resolved, reason = _resolved_ids(tasks, target_id, references)
    if resolved is None:
        return None, reason

    graph = {
        task_id(task): [
            str(item).strip()
            for item in task.get("blocked_by", [])
            if isinstance(item, str) and str(item).strip()
        ]
        for task in tasks
        if task_id(task)
    }
    graph[target_id] = resolved
    if any(_has_path(graph, dependency_id, target_id, set()) for dependency_id in resolved):
        return None, "That dependency would create a circular task relationship"
    return resolved, None


def rebuild_inverse_relationships(tasks: list[dict[str, Any]]) -> None:
    """Drop stale prerequisite IDs and derive every task's ``blocks`` list."""
    # ERROR_HANDLING_EXCLUDE: Pure in-memory helper; guarded callers own failures.
    by_id = {task_id(task): task for task in tasks if task_id(task)}
    for task in tasks:
        current_id = task_id(task)
        cleaned: list[str] = []
        for dependency_id in task.get("blocked_by", []):
            dependency_id = str(dependency_id or "").strip()
            if (
                dependency_id
                and dependency_id != current_id
                and dependency_id in by_id
                and dependency_id not in cleaned
            ):
                cleaned.append(dependency_id)
        task["blocked_by"] = cleaned
        task["blocks"] = []

    for dependent in tasks:
        dependent_id = task_id(dependent)
        for dependency_id in dependent.get("blocked_by", []):
            blocker = by_id.get(dependency_id)
            if blocker is not None and dependent_id not in blocker["blocks"]:
                blocker["blocks"].append(dependent_id)


def remove_dependency_references(
    tasks: list[dict[str, Any]], removed_ids: set[str]
) -> None:
    """Unblock tasks whose prerequisites were completed or deleted."""
    # ERROR_HANDLING_EXCLUDE: Pure in-memory helper; guarded callers own failures.
    for task in tasks:
        task["blocked_by"] = [
            dependency_id
            for dependency_id in task.get("blocked_by", [])
            if dependency_id not in removed_ids
        ]
    rebuild_inverse_relationships(tasks)


def clear_dependencies(tasks: list[dict[str, Any]]) -> None:
    """Clear inverse edges while retaining prerequisite templates for restore/repeat."""
    # ERROR_HANDLING_EXCLUDE: Pure in-memory helper; guarded callers own failures.
    for task in tasks:
        task["blocks"] = []
