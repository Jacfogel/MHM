"""Shared formatting helpers for analytics command handlers."""

from typing import Any

import core.response_tracking as response_tracking
from core.error_handling import handle_errors


class AnalyticsFormattingMixin:
    """Formatting helpers shared by analytics command handlers."""

    @handle_errors("formatting basic analytics line", default_return="")
    def _format_basic_analytics_line(self, question: dict[str, Any]) -> str:
        """Format a single basic analytics line."""
        name = question.get("name", "Unknown")
        scale_max = question.get("scale_max")
        if "average" in question:
            avg = self._format_numeric_value(question.get("average", 0))
            min_val = self._format_numeric_value(question.get("min", 0))
            max_val = self._format_numeric_value(question.get("max", 0))
            count = question.get("count", 0)
            scale_suffix = f"/{int(scale_max)}" if scale_max else ""
            return (
                f"{name}: avg {avg}{scale_suffix} "
                f"(min {min_val}{scale_suffix}, max {max_val}{scale_suffix}) "
                f"over {count} answers"
            )
        if "average_hours" in question:
            avg = self._format_numeric_value(question.get("average_hours", 0))
            min_val = self._format_numeric_value(question.get("min_hours", 0))
            max_val = self._format_numeric_value(question.get("max_hours", 0))
            count = question.get("count", 0)
            return (
                f"{name}: avg {avg}h (min {min_val}h, max {max_val}h) "
                f"over {count} answers"
            )
        if "yes_rate" in question:
            yes_count = question.get("yes_count", 0)
            count = question.get("count", 0)
            yes_rate = question.get("yes_rate", 0)
            return f"{name}: Yes {yes_count}/{count} ({yes_rate}%)"
        count = question.get("count", 0)
        return f"{name}: {count} responses"

    @handle_errors("getting field scale", default_return=None)
    def _get_field_scale(self, field: str) -> int:
        """Determine the scale for a field."""
        scale_1_5_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
        ]

        if field in scale_1_5_fields:
            return 5
        return None

    @handle_errors("truncating response", default_return="")
    def _truncate_response(self, response: str, max_length: int = 1900) -> str:
        """Truncate response to fit Discord message limits."""
        if len(response) <= max_length:
            return response

        truncated = response[: max_length - 3] + "..."
        last_newline = truncated.rfind("\n")
        if last_newline > max_length * 0.8:
            truncated = response[:last_newline] + "\n\n... (response truncated)"

        return truncated

    @handle_errors("extracting check-in responses", default_return={})
    def _extract_checkin_responses(
        self, checkin: dict[str, Any], question_keys: set[str]
    ) -> dict[str, Any]:
        """Extract responses from current check-in records."""
        responses: dict[str, Any] = {}

        stored_responses = checkin.get("responses")
        if isinstance(stored_responses, dict):
            for key, value in stored_responses.items():
                if key in question_keys:
                    responses[key] = value

        for key in question_keys:
            if key in checkin and key not in responses:
                responses[key] = checkin[key]

        reserved_keys = {
            "timestamp",
            "questions_asked",
            "completed",
            "user_id",
            "responses",
            "date",
        }
        for key, value in checkin.items():
            if key in reserved_keys or key in responses:
                continue
            responses[key] = value

        return responses

    @handle_errors("ordering check-in keys", default_return=[])
    def _get_ordered_checkin_keys(
        self, checkin: dict[str, Any], responses: dict[str, Any]
    ) -> list[str]:
        """Preserve original check-in order when available."""
        ordered: list[str] = []
        questions_asked = checkin.get("questions_asked")
        if isinstance(questions_asked, list):
            for key in questions_asked:
                if key in responses and key not in ordered:
                    ordered.append(key)

        for key in sorted(responses.keys()):
            if key not in ordered:
                ordered.append(key)

        return ordered

    @handle_errors("getting check-in label", default_return="")
    def _get_checkin_label(
        self, key: str, question_defs: dict[str, dict[str, Any]]
    ) -> str:
        """Get a readable label for a check-in response key."""
        question_def = question_defs.get(key, {})
        if isinstance(question_def, dict):
            label = question_def.get("ui_display_name") or question_def.get("label")
            if label:
                return self._clean_checkin_label(str(label))
        return self._clean_checkin_label(key.replace("_", " ").strip().title())

    @handle_errors("cleaning check-in label", default_return="")
    def _clean_checkin_label(self, label: str) -> str:
        """Remove redundant suffixes from check-in labels."""
        suffixes = [
            " (1-5 scale)",
            " (1-10 scale)",
            " (yes/no)",
            " (yes-no)",
            " (time pair)",
        ]
        for suffix in suffixes:
            if label.endswith(suffix):
                label = label[: -len(suffix)]
        return label.strip()

    @handle_errors("getting question scale", default_return=None)
    def _get_question_scale(
        self, key: str, question_defs: dict[str, dict[str, Any]]
    ) -> int | float | None:
        """Return scale max for a question when available."""
        question_def = question_defs.get(key, {})
        if isinstance(question_def, dict):
            validation = question_def.get("validation") or {}
            qtype = question_def.get("type")
            max_value = validation.get("max")
            if (
                qtype
                and str(qtype).startswith("scale_")
                and isinstance(max_value, (int, float))
            ):
                if isinstance(max_value, float) and max_value.is_integer():
                    max_value = int(max_value)
                return max_value
        return self._get_field_scale(key)

    @handle_errors("formatting numeric value", default_return="")
    def _format_numeric_value(self, value: float) -> str:
        """Format numeric values with minimal trailing decimals."""
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.1f}"
        return str(int(value))

    @handle_errors("formatting check-in response value", default_return=None)
    def _format_checkin_response_value(
        self,
        key: str,
        value: Any,
        question_defs: dict[str, dict[str, Any]],
    ) -> str | None:
        """Format a check-in response value for display."""
        if value is None:
            return None
        if value == "SKIPPED":
            return "Skipped"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, str):
            value_str = value.strip()
            if not value_str:
                return None
            lower_value = value_str.lower()
            if lower_value in {"yes", "y", "true", "1"}:
                return "Yes"
            if lower_value in {"no", "n", "false", "0"}:
                return "No"
            try:
                numeric_value = float(value_str)
                scale = self._get_question_scale(key, question_defs)
                numeric_text = self._format_numeric_value(numeric_value)
                return f"{numeric_text}/{scale}" if scale else numeric_text
            except ValueError:
                return value_str
        if isinstance(value, dict):
            sleep_chunks = value.get("sleep_chunks")
            total_sleep_hours = value.get("total_sleep_hours")
            if isinstance(sleep_chunks, list) and sleep_chunks:
                chunk_ranges = []
                for chunk in sleep_chunks:
                    if not isinstance(chunk, dict):
                        continue
                    start = chunk.get("sleep_time")
                    end = chunk.get("wake_time")
                    if start and end:
                        chunk_ranges.append(f"{start}-{end}")
                if chunk_ranges:
                    if isinstance(total_sleep_hours, (int, float)):
                        return (
                            f"{'; '.join(chunk_ranges)} "
                            f"(total {self._format_numeric_value(float(total_sleep_hours))}h)"
                        )
                    return "; ".join(chunk_ranges)
            sleep_time = value.get("sleep_time")
            wake_time = value.get("wake_time")
            if sleep_time and wake_time:
                return f"{sleep_time}-{wake_time}"
            if not value:
                return None
            return ", ".join(f"{k}={v}" for k, v in value.items())
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else None
        if isinstance(value, (int, float)):
            scale = self._get_question_scale(key, question_defs)
            numeric_text = self._format_numeric_value(float(value))
            return f"{numeric_text}/{scale}" if scale else numeric_text
        return str(value)

    @handle_errors("building trend graph", default_return="")
    def _build_trend_graph(
        self,
        recent_data: list[dict[str, Any]],
        value_key: str,
        label: str,
        max_points: int = 7,
    ) -> str:
        """Build a simple ASCII trend graph for recent check-in values."""
        series = []
        for entry in recent_data or []:
            value = entry.get(value_key)
            if not isinstance(value, (int, float)):
                continue
            date_value = (
                entry.get("date")
                or response_tracking.checkin_runtime_timestamp(entry)
                or "Unknown"
            )
            date_label = (
                date_value[:10] if isinstance(date_value, str) else str(date_value)
            )
            series.append((date_label, float(value)))

        if not series:
            return ""

        series = list(reversed(series[:max_points]))
        lines = [f"{label} (last {len(series)} days):"]
        for date_label, value in series:
            bar_len = max(0, min(10, int(round(value * 2))))
            bar = "#" * bar_len
            lines.append(f"{date_label}: {bar} ({value:.1f})")
        return "\n".join(lines)
