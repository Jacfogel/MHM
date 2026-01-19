"""
Behavior tests for message_analytics module.

Tests real behavior and side effects for message analytics functionality.
Focuses on frequency analysis, delivery success tracking, and message patterns.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

# Do not modify sys.path; rely on package imports

from core.message_analytics import MessageAnalytics
from core.time_utilities import TIMESTAMP_FULL, format_timestamp


@pytest.mark.behavior
class TestMessageAnalyticsInitializationBehavior:
    """Test MessageAnalytics initialization with real behavior verification."""

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.critical
    def test_analytics_initialization_real_behavior(self):
        """REAL BEHAVIOR TEST: Test MessageAnalytics can be initialized."""
        # [OK] VERIFY REAL BEHAVIOR: Analytics can be created
        analytics = MessageAnalytics()
        assert analytics is not None, "MessageAnalytics should be created successfully"
        assert isinstance(analytics, MessageAnalytics), "Should be correct type"


@pytest.mark.behavior
class TestMessageAnalyticsFrequencyBehavior:
    """Test message frequency analysis with real behavior verification."""

    @pytest.fixture
    def analytics(self):
        """Create MessageAnalytics instance for testing."""
        return MessageAnalytics()

    @pytest.fixture
    def mock_messages(self):
        """Create mock sent message data."""
        base_date = datetime.now() - timedelta(days=30)
        messages = []

        # Create messages across different categories and time periods
        categories = ["motivational", "health", "task"]
        time_periods = ["morning", "afternoon", "evening"]

        for i in range(30):
            date = base_date + timedelta(days=i)
            category = categories[i % len(categories)]
            time_period = time_periods[i % len(time_periods)]

            messages.append(
                {
                    "message_id": f"msg-{i}",
                    "message": f"Test message {i}",
                    "category": category,
                    "timestamp": format_timestamp(date, TIMESTAMP_FULL),
                    "delivery_status": "sent",
                    "time_period": time_period,
                }
            )

        return messages

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.critical
    def test_message_frequency_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test message frequency with no message data."""
        # [OK] VERIFY REAL BEHAVIOR: No data returns error
        with patch("core.message_analytics.get_recent_messages", return_value=[]):
            result = analytics.get_message_frequency("test_user", days=30)

        assert "error" in result, "Should return error when no data available"
        assert "period_days" in result, "Should have period_days"
        assert result["total_messages"] == 0, "Should have zero messages"

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.regression
    def test_message_frequency_with_data_real_behavior(self, analytics, mock_messages):
        """REAL BEHAVIOR TEST: Test message frequency analysis with valid data."""
        # [OK] VERIFY REAL BEHAVIOR: Analysis works with valid data
        with patch(
            "core.message_analytics.get_recent_messages", return_value=mock_messages
        ):
            result = analytics.get_message_frequency("test_user", days=30)

        # [OK] VERIFY REAL BEHAVIOR: Result has expected structure
        assert "error" not in result, "Should not have error with valid data"
        assert "period_days" in result, "Should have period_days"
        assert "total_messages" in result, "Should have total_messages"
        assert "average_per_day" in result, "Should have average_per_day"
        assert "category_counts" in result, "Should have category_counts"
        assert "time_period_counts" in result, "Should have time_period_counts"

        # [OK] VERIFY REAL BEHAVIOR: Values are reasonable
        assert result["period_days"] == 30, "Should have correct period"
        assert result["total_messages"] == 30, "Should have correct total messages"
        assert result["average_per_day"] > 0, "Average per day should be positive"
        assert len(result["category_counts"]) > 0, "Should have category counts"
        assert len(result["time_period_counts"]) > 0, "Should have time period counts"

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.regression
    def test_message_frequency_category_filter_real_behavior(
        self, analytics, mock_messages
    ):
        """REAL BEHAVIOR TEST: Test message frequency with category filter."""
        # [OK] VERIFY REAL BEHAVIOR: Category filter works correctly
        motivational_messages = [
            msg for msg in mock_messages if msg["category"] == "motivational"
        ]

        with patch(
            "core.message_analytics.get_recent_messages",
            return_value=motivational_messages,
        ):
            result = analytics.get_message_frequency(
                "test_user", days=30, category="motivational"
            )

        assert "error" not in result, "Should not have error with filtered data"
        assert result["total_messages"] == len(
            motivational_messages
        ), "Should have correct filtered count"
        assert all(
            cat == "motivational" for cat in result["category_counts"].keys()
        ), "Should only have motivational category"


@pytest.mark.behavior
class TestMessageAnalyticsDeliveryBehavior:
    """Test message delivery success rate analysis with real behavior verification."""

    @pytest.fixture
    def analytics(self):
        """Create MessageAnalytics instance for testing."""
        return MessageAnalytics()

    @pytest.fixture
    def mock_messages_mixed_status(self):
        """Create mock sent message data with mixed delivery statuses."""
        base_date = datetime.now() - timedelta(days=30)
        messages = []

        statuses = ["sent", "sent", "sent", "failed", "sent"]  # 80% success rate

        for i in range(25):
            date = base_date + timedelta(days=i)
            status = statuses[i % len(statuses)]

            messages.append(
                {
                    "message_id": f"msg-{i}",
                    "message": f"Test message {i}",
                    "category": "motivational",
                    "timestamp": format_timestamp(date, TIMESTAMP_FULL),
                    "delivery_status": status,
                    "time_period": "morning",
                }
            )

        return messages

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.regression
    def test_delivery_success_rate_real_behavior(
        self, analytics, mock_messages_mixed_status
    ):
        """REAL BEHAVIOR TEST: Test delivery success rate calculation."""
        # [OK] VERIFY REAL BEHAVIOR: Success rate calculation works
        with patch(
            "core.message_analytics.get_recent_messages",
            return_value=mock_messages_mixed_status,
        ):
            result = analytics.get_delivery_success_rate("test_user", days=30)

        assert "error" not in result, "Should not have error with valid data"
        assert "success_rate" in result, "Should have success_rate"
        assert "status_breakdown" in result, "Should have status_breakdown"
        assert "total_messages" in result, "Should have total_messages"

        # [OK] VERIFY REAL BEHAVIOR: Success rate is calculated correctly
        assert 0 <= result["success_rate"] <= 100, "Success rate should be percentage"
        assert result["total_messages"] == 25, "Should have correct total"
        assert "sent" in result["status_breakdown"], "Should track sent status"

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.critical
    def test_delivery_success_rate_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test delivery success rate with no message data."""
        # [OK] VERIFY REAL BEHAVIOR: No data returns error
        with patch("core.message_analytics.get_recent_messages", return_value=[]):
            result = analytics.get_delivery_success_rate("test_user", days=30)

        assert "error" in result, "Should return error when no data available"
        assert "period_days" in result, "Should have period_days"


@pytest.mark.behavior
class TestMessageAnalyticsSummaryBehavior:
    """Test message summary functionality with real behavior verification."""

    @pytest.fixture
    def analytics(self):
        """Create MessageAnalytics instance for testing."""
        return MessageAnalytics()

    @pytest.fixture
    def mock_messages(self):
        """Create mock sent message data."""
        base_date = datetime.now() - timedelta(days=30)
        messages = []

        for i in range(20):
            date = base_date + timedelta(days=i)
            messages.append(
                {
                    "message_id": f"msg-{i}",
                    "message": f"Test message {i}",
                    "category": "motivational" if i % 2 == 0 else "health",
                    "timestamp": format_timestamp(date, TIMESTAMP_FULL),
                    "delivery_status": "sent",
                    "time_period": "morning",
                }
            )

        return messages

    @pytest.mark.analytics
    @pytest.mark.messages
    @pytest.mark.regression
    def test_message_summary_real_behavior(self, analytics, mock_messages):
        """REAL BEHAVIOR TEST: Test comprehensive message summary."""
        # [OK] VERIFY REAL BEHAVIOR: Summary combines frequency and delivery data
        with patch(
            "core.message_analytics.get_recent_messages", return_value=mock_messages
        ):
            result = analytics.get_message_summary("test_user", days=30)

        assert "error" not in result, "Should not have error with valid data"
        assert "total_messages" in result, "Should have total_messages"
        assert "average_per_day" in result, "Should have average_per_day"
        assert "delivery_success_rate" in result, "Should have delivery_success_rate"
        assert "category_counts" in result, "Should have category_counts"

        # [OK] VERIFY REAL BEHAVIOR: Summary values are reasonable
        assert result["total_messages"] == 20, "Should have correct total"
        assert result["average_per_day"] > 0, "Average should be positive"
        assert (
            0 <= result["delivery_success_rate"] <= 100
        ), "Success rate should be percentage"
