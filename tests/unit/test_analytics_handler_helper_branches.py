"""Targeted unit coverage for analytics handler helper branches."""

from __future__ import annotations

import pytest

from communication.command_handlers.analytics_handler import AnalyticsHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


@pytest.mark.unit
@pytest.mark.communication
class TestAnalyticsHandlerHelperBranches:
    def setup_method(self):
        self.handler = AnalyticsHandler()

    def test_public_show_wrappers_delegate(self, monkeypatch):
        monkeypatch.setattr(
            self.handler,
            "_handle_show_analytics",
            lambda user_id, entities: InteractionResponse("ok", True),
        )
        assert self.handler.handle_show_analytics("u1", {}).message == "ok"
        assert self.handler.handle_show_status("u1", {}).message == "ok"

    def test_show_analytics_no_categories_branch(self, monkeypatch):
        class _FakeAnalytics:
            def get_basic_analytics(self, user_id, days):
                return {"total_checkins": 4, "categories": {}}

        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: _FakeAnalytics(),
        )
        result = self.handler._handle_show_analytics("u1", {"days": 7})
        assert "No answered questions found" in result.message

    def test_show_analytics_exception_branch(self, monkeypatch):
        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        seen = []
        monkeypatch.setattr(
            "core.error_handling.handle_ai_error",
            lambda exc, context, user_id: seen.append((str(exc), context, user_id)),
        )
        result = self.handler._handle_show_analytics("u1", {"days": 7})
        assert "trouble showing your analytics" in result.message
        assert seen and seen[0][1] == "showing analytics"

    def test_energy_trends_error_and_insight_branches(self, monkeypatch):
        class _FakeAnalytics:
            def __init__(self, payload):
                self._payload = payload

            def get_energy_trends(self, user_id, days):
                return self._payload

        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: _FakeAnalytics({"error": "no data"}),
        )
        no_data = self.handler._handle_energy_trends("u1", {"days": 14})
        assert "don't have enough energy data" in no_data.message

        payload_high = {
            "average_energy": 4.2,
            "min_energy": 2,
            "max_energy": 5,
            "trend": "improving",
            "energy_distribution": {"high": 3},
            "recent_data": [{"date": "2026-02-01", "energy": 4.0}],
        }
        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: _FakeAnalytics(payload_high),
        )
        high = self.handler._handle_energy_trends("u1", {"days": 14})
        assert "consistently high" in high.message
        assert "Trend Graph" in high.message

        payload_low = {
            "average_energy": 1.9,
            "min_energy": 1,
            "max_energy": 3,
            "trend": "declining",
            "energy_distribution": {},
            "recent_data": [],
        }
        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: _FakeAnalytics(payload_low),
        )
        low = self.handler._handle_energy_trends("u1", {"days": 14})
        assert "energy levels have been low" in low.message

    def test_clean_label_scale_and_numeric_helpers(self):
        cleaned = self.handler._clean_checkin_label("Sleep Quality (1-5 scale)")
        assert cleaned == "Sleep Quality"

        q_defs = {"mood": {"type": "scale_1_5", "validation": {"max": 5.0}}}
        assert self.handler._get_question_scale("mood", q_defs) == 5
        assert self.handler._get_question_scale("sleep_hours", q_defs) is None

        assert self.handler._format_numeric_value(3.0) == "3"
        assert self.handler._format_numeric_value(3.25) == "3.2"

    def test_format_checkin_response_value_branches(self):
        q_defs = {"mood": {"type": "scale_1_5", "validation": {"max": 5}}}

        assert self.handler._format_checkin_response_value("mood", None, q_defs) is None
        assert self.handler._format_checkin_response_value("mood", "SKIPPED", q_defs) == "Skipped"
        assert self.handler._format_checkin_response_value("mood", True, q_defs) == "Yes"
        assert self.handler._format_checkin_response_value("mood", False, q_defs) == "No"
        assert self.handler._format_checkin_response_value("mood", "  ", q_defs) is None
        assert self.handler._format_checkin_response_value("mood", "yes", q_defs) == "Yes"
        assert self.handler._format_checkin_response_value("mood", "No", q_defs) == "No"
        assert self.handler._format_checkin_response_value("mood", "4", q_defs) == "4/5"
        assert self.handler._format_checkin_response_value("mood", "text", q_defs) == "text"

        sleep_chunks = {
            "sleep_chunks": [{"sleep_time": "22:00", "wake_time": "06:00"}],
            "total_sleep_hours": 8.0,
        }
        assert (
            self.handler._format_checkin_response_value("sleep", sleep_chunks, q_defs)
            == "22:00-06:00 (total 8h)"
        )
        assert (
            self.handler._format_checkin_response_value(
                "sleep", {"sleep_time": "23:00", "wake_time": "07:00"}, q_defs
            )
            == "23:00-07:00"
        )
        assert self.handler._format_checkin_response_value("sleep", {}, q_defs) is None
        assert (
            self.handler._format_checkin_response_value("sleep", {"x": 1, "y": 2}, q_defs)
            == "x=1, y=2"
        )
        assert self.handler._format_checkin_response_value("misc", ["a", 1], q_defs) == "a, 1"
        assert self.handler._format_checkin_response_value("misc", [], q_defs) is None
        assert self.handler._format_checkin_response_value("mood", 2, q_defs) == "2/5"
        assert self.handler._format_checkin_response_value("misc", object(), q_defs).startswith("<object object")

    def test_build_trend_graph_filters_and_limits(self):
        graph = self.handler._build_trend_graph(
            recent_data=[
                {"date": "2026-02-01", "mood": 2},
                {"timestamp": "2026-02-02 01:02:03", "mood": 3.5},
                {"date": "2026-02-03", "mood": "bad"},
                {"date": 12345, "mood": 1},
            ],
            value_key="mood",
            label="Mood trend",
            max_points=3,
        )
        assert "Mood trend (last 3 days):" in graph
        assert "2026-02-02" in graph
        assert "12345" in graph
        assert "bad" not in graph

        assert self.handler._build_trend_graph([], "mood", "Mood trend") == ""

    def test_handle_dispatches_energy_and_task_stats_intents(self, monkeypatch):
        monkeypatch.setattr(
            self.handler, "_handle_energy_trends", lambda user_id, entities: InteractionResponse("energy ok", True)
        )
        monkeypatch.setattr(
            self.handler, "_handle_task_stats", lambda user_id, entities: InteractionResponse("stats ok", True)
        )

        energy_resp = self.handler.handle(
            "u1", ParsedCommand(intent="energy_trends", entities={}, confidence=1.0, original_message="energy")
        )
        stats_resp = self.handler.handle(
            "u1", ParsedCommand(intent="task_stats", entities={}, confidence=1.0, original_message="stats")
        )
        assert energy_resp.message == "energy ok"
        assert stats_resp.message == "stats ok"

    def test_format_checkin_response_value_additional_dict_branches(self):
        q_defs = {}
        # Non-dict chunk entry should be skipped (line 719 path).
        value = {"sleep_chunks": [{"sleep_time": "22:00", "wake_time": "06:00"}, "bad"]}
        assert self.handler._format_checkin_response_value("sleep", value, q_defs) == "22:00-06:00"
        # Chunk ranges without total should join directly (line 730 path).
        value_no_total = {"sleep_chunks": [{"sleep_time": "21:00", "wake_time": "05:00"}]}
        assert self.handler._format_checkin_response_value("sleep", value_no_total, q_defs) == "21:00-05:00"

    def test_handle_checkin_analysis_success_and_exception(self, monkeypatch):
        class _FakeAnalytics:
            def get_mood_trends(self, user_id, days):
                return {"average_mood": 4.0, "min_mood": 2, "max_mood": 5, "trend": "improving"}

        class _FakeDynamic:
            def get_all_questions(self, user_id):
                return {"mood": {"label": "Mood"}}

        monkeypatch.setattr(
            "core.response_tracking.get_checkins_by_days",
            lambda user_id, days: [{"id": i} for i in range(7)],
        )
        monkeypatch.setattr("core.checkin_analytics.CheckinAnalytics", lambda: _FakeAnalytics())
        monkeypatch.setattr("core.checkin_dynamic_manager.dynamic_checkin_manager", _FakeDynamic())
        monkeypatch.setattr(
            self.handler,
            "_extract_checkin_responses",
            lambda checkin, keys: {"mood": "good"},
        )
        response = self.handler._handle_checkin_analysis("u1", {"days": 7})
        assert "Check-in Analysis" in response.message
        assert "consistent with check-ins" in response.message
        assert "mood has been improving" in response.message

        seen = []
        monkeypatch.setattr(
            "core.response_tracking.get_checkins_by_days",
            lambda user_id, days: (_ for _ in ()).throw(RuntimeError("explode")),
        )
        monkeypatch.setattr(
            "core.error_handling.handle_ai_error",
            lambda exc, context, user_id: seen.append((str(exc), context, user_id)),
        )
        error_response = self.handler._handle_checkin_analysis("u1", {"days": 7})
        assert "trouble analyzing your check-ins" in error_response.message
        assert seen and seen[0][1] == "analyzing check-ins"

    def test_completion_rate_error_and_exception_paths(self, monkeypatch):
        class _FakeAnalytics:
            def __init__(self, payload):
                self._payload = payload

            def get_completion_rate(self, user_id, days):
                return self._payload

        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: _FakeAnalytics({"error": "no data"}),
        )
        no_data = self.handler._handle_completion_rate("u1", {"days": 30})
        assert "don't have enough check-in data" in no_data.message

        monkeypatch.setattr(
            "core.checkin_analytics.CheckinAnalytics",
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        seen = []
        monkeypatch.setattr(
            "core.error_handling.handle_ai_error",
            lambda exc, context, user_id: seen.append((str(exc), context, user_id)),
        )
        error = self.handler._handle_completion_rate("u1", {"days": 30})
        assert "trouble calculating your completion rate" in error.message
        assert seen and seen[0][1] == "calculating completion rate"

    def test_task_analytics_branches(self, monkeypatch):
        class _FakeAnalytics:
            def __init__(self, payload):
                self._payload = payload

            def get_task_weekly_stats(self, user_id, days):
                return self._payload

        monkeypatch.setattr(
            "tasks.get_user_task_stats",
            lambda user_id: {"active_count": 0, "completed_count": 0, "total_count": 0},
        )
        monkeypatch.setattr("tasks.load_active_tasks", lambda user_id: [])
        monkeypatch.setattr("tasks.load_completed_tasks", lambda user_id: [])
        monkeypatch.setattr("core.checkin_analytics.CheckinAnalytics", lambda: _FakeAnalytics({"error": "none"}))
        response_zero = self.handler._handle_task_analytics("u1", {"days": 30})
        assert "No detailed task completion data available" in response_zero.message
        assert "No active tasks - great job" in response_zero.message

        monkeypatch.setattr(
            "tasks.get_user_task_stats",
            lambda user_id: {"active_count": 6, "completed_count": 2, "total_count": 8},
        )
        monkeypatch.setattr("core.checkin_analytics.CheckinAnalytics", lambda: _FakeAnalytics({"Task A": {"completion_rate": 90, "completed_days": 9, "total_days": 10}}))
        response_many = self.handler._handle_task_analytics("u1", {"days": 30})
        assert "consider prioritizing" in response_many.message
        assert "making good progress" in response_many.message

    def test_task_analytics_and_task_stats_exception_paths(self, monkeypatch):
        monkeypatch.setattr(
            "tasks.get_user_task_stats",
            lambda user_id: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        seen = []
        monkeypatch.setattr(
            "core.error_handling.handle_ai_error",
            lambda exc, context, user_id: seen.append((str(exc), context, user_id)),
        )
        task_analytics_error = self.handler._handle_task_analytics("u1", {"days": 30})
        assert "trouble showing your task analytics" in task_analytics_error.message
        assert any(ctx == "showing task analytics" for _, ctx, _ in seen)

        task_stats_error = self.handler._handle_task_stats("u1", {"days": 30})
        assert "trouble showing your task statistics" in task_stats_error.message
        assert any(ctx == "showing task statistics" for _, ctx, _ in seen)

    def test_task_stats_success_and_basic_line_variants(self, monkeypatch):
        monkeypatch.setattr(
            "tasks.get_user_task_stats",
            lambda user_id: {"active_count": 3, "completed_count": 2, "total_count": 5},
        )
        monkeypatch.setattr(
            "tasks.load_active_tasks",
            lambda user_id: [{"priority": "high"}, {"priority": "medium"}, {"priority": "low"}],
        )
        monkeypatch.setattr(
            "tasks.load_completed_tasks",
            lambda user_id: [{"title": "Done 1"}, {"title": "Done 2"}],
        )
        result = self.handler._handle_task_stats("u1", {"days": 14})
        assert "Task Statistics" in result.message
        assert "Active Task Priorities" in result.message
        assert "Recently Completed" in result.message

        hours_line = self.handler._format_basic_analytics_line(
            {"name": "Sleep", "average_hours": 7.5, "min_hours": 6, "max_hours": 9, "count": 5}
        )
        yes_line = self.handler._format_basic_analytics_line(
            {"name": "Walk", "yes_count": 4, "count": 5, "yes_rate": 80}
        )
        count_line = self.handler._format_basic_analytics_line({"name": "Misc", "count": 3})
        assert "avg 7.5h" in hours_line
        assert "Yes 4/5 (80%)" in yes_line
        assert count_line == "Misc: 3 responses"

    def test_truncate_response_newline_friendly_path(self):
        # Ensure last_newline > max_length*0.8 so the alternate truncation branch runs.
        response = "x" * 90 + "\n" + "tail" * 30
        truncated = self.handler._truncate_response(response, max_length=100)
        assert "... (response truncated)" in truncated
