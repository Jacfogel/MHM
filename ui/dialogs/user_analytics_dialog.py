"""
User Analytics Dialog

Provides comprehensive analytics visualization for user check-in data,
including wellness scores, mood trends, habit analysis, and sleep patterns.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QComboBox,
    QTabWidget,
    QWidget,
    QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush
from ui.generated.user_analytics_dialog_pyqt import Ui_Dialog_user_analytics

# Import core functionality
from core.checkin_analytics import CheckinAnalytics
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

setup_logging()
logger = get_component_logger("ui")


class UserAnalyticsDialog(QDialog):
    """Dialog for displaying comprehensive user analytics."""

    # ERROR_HANDLING_EXCLUDE: Dialog constructor - simple UI setup, no error-prone operations
    def __init__(self, parent=None, user_id=None):
        """Initialize the user analytics dialog."""
        super().__init__(parent)
        self.user_id = user_id
        self.analytics = CheckinAnalytics()
        self.current_days = 30  # Default to 30 days
        self.available_data_types = {}

        # Setup UI
        self.ui = Ui_Dialog_user_analytics()
        self.ui.setupUi(self)

        # Setup functionality
        self.setup_connections()
        self.setup_initial_state()

        # Load analytics data
        self.load_analytics_data()

    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        self.ui.pushButton_refresh.clicked.connect(self.refresh_analytics)
        self.ui.pushButton_close.clicked.connect(self.accept)
        self.ui.comboBox_time_period.currentIndexChanged.connect(
            self.on_time_period_changed
        )

    @handle_errors("setting up initial state")
    def setup_initial_state(self):
        """Setup initial dialog state."""
        # Set window title with user info
        if self.user_id:
            user_data = get_user_data(self.user_id, "account")
            username = user_data.get("account", {}).get(
                "internal_username", self.user_id
            )
            self.setWindowTitle(f"User Analytics - {username}")

        # Set default time period to 30 days
        self.ui.comboBox_time_period.setCurrentIndex(2)  # 30 days

        # Initialize empty state
        self.show_loading_state()

    @handle_errors("loading analytics data")
    def load_analytics_data(self):
        """Load and display analytics data."""
        if not self.user_id:
            self.show_error_state("No user selected")
            return

        try:
            # Get time period
            time_periods = [7, 14, 30, 60, 90]
            self.current_days = time_periods[
                self.ui.comboBox_time_period.currentIndex()
            ]

            # First detect what data is available
            self.detect_available_data_types()

            # Load overview data (always)
            self.load_overview_data()

            # Load data for visible tabs only
            if self.available_data_types.get("mood", False):
                self.load_mood_data()

            if self.available_data_types.get("habits", False):
                self.load_habits_data()

            if self.available_data_types.get("sleep", False):
                self.load_sleep_data()

            if self.available_data_types.get("quantitative", False):
                self.load_quantitative_data()

        except Exception as e:
            logger.error(f"Error loading analytics data for user {self.user_id}: {e}")
            self.show_error_state(f"Error loading analytics: {str(e)}")

    @handle_errors("detecting available data types")
    def detect_available_data_types(self):
        """Detect what types of data are available and configure tab visibility."""
        try:
            # Get available data types from analytics backend
            data_types_result = self.analytics.get_available_data_types(
                self.user_id, self.current_days
            )

            if "error" in data_types_result:
                logger.warning(
                    f"Could not detect data types: {data_types_result['error']}"
                )
                self.available_data_types = {
                    "mood": True,  # Default to showing mood tab
                    "energy": False,
                    "sleep": False,
                    "habits": False,
                    "quantitative": False,
                }
            else:
                self.available_data_types = data_types_result.get("data_types", {})

            # Configure tab visibility based on available data
            self.configure_tab_visibility()

        except Exception as e:
            logger.error(f"Error detecting data types: {e}")
            # Default to showing all tabs if detection fails
            self.available_data_types = {
                "mood": True,
                "energy": True,
                "sleep": True,
                "habits": True,
                "quantitative": True,
            }
            self.configure_tab_visibility()

    @handle_errors("configuring tab visibility")
    def configure_tab_visibility(self):
        """Configure which tabs are visible based on available data."""
        try:
            # Get tab widget
            tab_widget = self.ui.tabWidget_analytics

            # Configure each tab based on available data
            tab_configs = [
                ("Overview", True),  # Always show overview
                ("Mood Trends", self.available_data_types.get("mood", False)),
                ("Habits", self.available_data_types.get("habits", False)),
                ("Sleep", self.available_data_types.get("sleep", False)),
                (
                    "Quantitative Data",
                    self.available_data_types.get("quantitative", False),
                ),
            ]

            # Hide tabs that don't have data
            for i, (tab_name, should_show) in enumerate(tab_configs):
                if i < tab_widget.count():
                    if should_show:
                        tab_widget.setTabVisible(i, True)
                    else:
                        tab_widget.setTabVisible(i, False)
                        logger.debug(f"Hiding tab '{tab_name}' - no data available")

            # If no specific data tabs are available, show a message in overview
            if not any(self.available_data_types.values()):
                logger.warning(
                    "No specific data types available - showing overview only"
                )

        except Exception as e:
            logger.error(f"Error configuring tab visibility: {e}")

    @handle_errors("loading overview data")
    def load_overview_data(self):
        """Load and display overview analytics."""
        try:
            # Get wellness score
            wellness_data = self.analytics.get_wellness_score(
                self.user_id, self.current_days
            )

            if "error" in wellness_data:
                error_msg = wellness_data.get("error", "Unknown error")
                total_checkins = wellness_data.get("total_checkins", 0)
                data_completeness = wellness_data.get("data_completeness", 0.0)

                self.ui.label_wellness_score.setText(
                    "Wellness Score: No data available"
                )
                self.ui.label_wellness_score.setStyleSheet(
                    "color: gray; font-weight: bold;"
                )

                summary_text = f"""Wellness Analysis (Last {self.current_days} days):
                
⚠️ {error_msg}
• Total check-ins: {total_checkins}
• Data completeness: {data_completeness:.1f}%
• Analysis period: {self.current_days} days

To see wellness insights, please complete more check-ins."""

                self.ui.textEdit_summary.setPlainText(summary_text)
                self.ui.textEdit_recommendations.setPlainText(
                    "Complete more check-ins to see wellness insights."
                )
                return

            # Display wellness score with color coding
            score = wellness_data.get("score", 0)
            level = wellness_data.get("level", "Unknown")

            # Color code the wellness score
            if score >= 80:
                color = "green"
            elif score >= 60:
                color = "orange"
            else:
                color = "red"

            self.ui.label_wellness_score.setText(
                f"Wellness Score: {score}/100 ({level})"
            )
            self.ui.label_wellness_score.setStyleSheet(
                f"color: {color}; font-weight: bold;"
            )

            # Display summary with actual data from backend
            # The backend doesn't provide total_checkins and data_completeness in the response
            # We need to calculate these from the actual data using calendar days
            from core.response_tracking import get_checkins_by_days

            actual_checkins = get_checkins_by_days(self.user_id, self.current_days)
            total_checkins = len(actual_checkins)
            data_completeness = (
                (total_checkins / self.current_days) * 100
                if self.current_days > 0
                else 0
            )

            summary_text = f"""Wellness Analysis (Last {self.current_days} days):
            
Overall Score: {score}/100
Level: {level}

Key Metrics:
• Total check-ins: {total_checkins}
• Data completeness: {data_completeness:.1f}%
• Analysis period: {self.current_days} days"""

            self.ui.textEdit_summary.setPlainText(summary_text)

            # Display recommendations
            recommendations = wellness_data.get("recommendations", [])
            if recommendations:
                rec_text = "• " + "\n• ".join(recommendations)
            else:
                rec_text = "No specific recommendations at this time."

            self.ui.textEdit_recommendations.setPlainText(rec_text)

        except Exception as e:
            # In test mode, these are expected errors when mocks are used, so use DEBUG
            import os

            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"Error loading overview data: {e} (expected in tests with mocks)"
                )
            else:
                logger.error(f"Error loading overview data: {e}")
            self.ui.textEdit_summary.setPlainText(
                f"Error loading overview data: {str(e)}"
            )

    @handle_errors("loading mood data")
    def load_mood_data(self):
        """Load and display mood analytics."""
        try:
            mood_data = self.analytics.get_mood_trends(self.user_id, self.current_days)

            if "error" in mood_data:
                self.ui.textEdit_mood_data.setPlainText(
                    "No mood data available for analysis."
                )
                return

            # Format mood data
            avg_mood = mood_data.get("average_mood", 0)
            trend = mood_data.get("trend", "stable")
            mood_changes = mood_data.get("mood_changes", 0)

            mood_text = f"""Mood Analysis (Last {self.current_days} days):

Average Mood: {avg_mood:.1f}/5
Trend: {trend.title()}
Mood Changes: {mood_changes}

Recent Mood Data:"""

            # Add recent mood entries with trend visualization
            recent_data = mood_data.get("recent_data", [])
            if recent_data:
                # Create a simple trend visualization
                mood_values = [
                    entry.get("mood", 0)
                    for entry in recent_data
                    if isinstance(entry.get("mood"), (int, float))
                ]
                if mood_values:
                    avg_mood = sum(mood_values) / len(mood_values)
                    trend_indicator = (
                        "📈"
                        if len(mood_values) > 1 and mood_values[-1] > mood_values[0]
                        else (
                            "📉"
                            if len(mood_values) > 1 and mood_values[-1] < mood_values[0]
                            else "➡️"
                        )
                    )
                    mood_text += f"\n\n📊 Trend Visualization: {trend_indicator}"
                    mood_text += f"\n📈 Average Mood: {avg_mood:.1f}/5"

                    # Show mood distribution
                    high_moods = sum(1 for m in mood_values if m >= 4)
                    low_moods = sum(1 for m in mood_values if m <= 2)
                    mood_text += f"\n🎯 High Mood Days: {high_moods}"
                    mood_text += f"\n😔 Low Mood Days: {low_moods}"

            for entry in recent_data[:10]:  # Show last 10 entries
                date = entry.get("date", "Unknown")
                mood = entry.get("mood", "N/A")
                # Add emoji based on mood level
                mood_emoji = "😊" if mood >= 4 else "😐" if mood >= 3 else "😔"
                mood_text += f"\n• {date}: {mood_emoji} {mood}/5"

            self.ui.textEdit_mood_data.setPlainText(mood_text)

        except Exception as e:
            # In test mode, these are expected errors when mocks are used, so use DEBUG
            import os

            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"Error loading mood data: {e} (expected in tests with mocks)"
                )
            else:
                logger.error(f"Error loading mood data: {e}")
            self.ui.textEdit_mood_data.setPlainText(
                f"Error loading mood data: {str(e)}"
            )

    @handle_errors("loading habits data")
    def load_habits_data(self):
        """Load and display habit analytics."""
        try:
            habit_data = self.analytics.get_habit_analysis(
                self.user_id, self.current_days
            )

            if "error" in habit_data:
                self.ui.textEdit_habits_data.setPlainText(
                    "No habit data available for analysis."
                )
                return

            # Format habit data with validation
            completion_rate = habit_data.get("overall_completion", 0)
            habits_dict = habit_data.get("habits", {})
            total_habits = len(habits_dict)

            # Calculate total completed habits across all habits
            completed_habits = sum(
                stats.get("completed_days", 0) for stats in habits_dict.values()
            )

            # Fix inconsistency: if total habits is 0, completion rate should be 0 or N/A
            if total_habits == 0:
                completion_rate = 0
                habits_text = f"""Habit Analysis (Last {self.current_days} days):

⚠️ No Habits Configured
Overall Completion Rate: N/A
Total Habits: {total_habits}
Completed Habits: {completed_habits}

To track habits, please configure them in your check-in settings."""
            else:
                habits_text = f"""Habit Analysis (Last {self.current_days} days):

Overall Completion Rate: {completion_rate:.1f}%
Total Habits: {total_habits}
Completed Habits: {completed_habits}

Habit Breakdown:"""

            # Add individual habit statistics
            for habit_key, stats in habits_dict.items():
                name = stats.get("name", habit_key)
                completion = stats.get("completion_rate", 0)
                total_days = stats.get("total_days", 0)
                completed_days = stats.get("completed_days", 0)
                status = stats.get("status", "Unknown")

                # Add emoji indicator based on completion rate
                if completion >= 80:
                    indicator = "🟢"
                elif completion >= 60:
                    indicator = "🟡"
                else:
                    indicator = "🔴"

                habits_text += f"\n{indicator} {name}: {completion:.1f}% ({completed_days}/{total_days} days) - {status}"

            self.ui.textEdit_habits_data.setPlainText(habits_text)

        except Exception as e:
            # In test mode, these are expected errors when mocks are used, so use DEBUG
            import os

            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"Error loading habits data: {e} (expected in tests with mocks)"
                )
            else:
                logger.error(f"Error loading habits data: {e}")
            self.ui.textEdit_habits_data.setPlainText(
                f"Error loading habits data: {str(e)}"
            )

    @handle_errors("loading sleep data")
    def load_sleep_data(self):
        """Load and display sleep analytics."""
        try:
            sleep_data = self.analytics.get_sleep_analysis(
                self.user_id, self.current_days
            )

            if "error" in sleep_data:
                self.ui.textEdit_sleep_data.setPlainText(
                    "No sleep data available for analysis."
                )
                return

            # Format sleep data
            avg_hours = sleep_data.get("average_hours", 0)
            avg_quality = sleep_data.get("average_quality", 0)
            good_sleep_days = sleep_data.get("good_sleep_days", 0)
            poor_sleep_days = sleep_data.get("poor_sleep_days", 0)
            consistency = sleep_data.get("sleep_consistency", 0)

            # Add sleep quality indicators with None handling
            if avg_hours is not None:
                hours_indicator = (
                    "🟢" if avg_hours >= 7 else "🟡" if avg_hours >= 6 else "🔴"
                )
            else:
                hours_indicator = "❓"  # No data available

            if avg_quality is not None:
                quality_indicator = (
                    "🟢" if avg_quality >= 4 else "🟡" if avg_quality >= 3 else "🔴"
                )
            else:
                quality_indicator = "❓"  # No data available

            if consistency is not None:
                consistency_indicator = (
                    "🟢" if consistency >= 80 else "🟡" if consistency >= 60 else "🔴"
                )
            else:
                consistency_indicator = "❓"  # No data available

            # Format display values
            hours_display = (
                f"{avg_hours:.1f} hours" if avg_hours is not None else "No data"
            )
            quality_display = (
                f"{avg_quality:.1f}/5" if avg_quality is not None else "No data"
            )
            consistency_display = (
                f"{consistency:.1f}%" if consistency is not None else "No data"
            )

            sleep_text = f"""Sleep Analysis (Last {self.current_days} days):

{hours_indicator} Average Hours: {hours_display}
{quality_indicator} Average Quality: {quality_display}
🟢 Good Sleep Days: {good_sleep_days}
🔴 Poor Sleep Days: {poor_sleep_days}
{consistency_indicator} Sleep Consistency: {consistency_display}

Recommendations:"""

            # Add sleep recommendations
            recommendations = sleep_data.get("recommendations", [])
            if recommendations:
                for rec in recommendations:
                    sleep_text += f"\n• {rec}"
            else:
                sleep_text += "\n• No specific sleep recommendations"

            self.ui.textEdit_sleep_data.setPlainText(sleep_text)

        except Exception as e:
            # In test mode, these are expected errors when mocks are used, so use DEBUG
            import os

            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"Error loading sleep data: {e} (expected in tests with mocks)"
                )
            else:
                logger.error(f"Error loading sleep data: {e}")
            self.ui.textEdit_sleep_data.setPlainText(
                f"Error loading sleep data: {str(e)}"
            )

    @handle_errors("loading quantitative data")
    def load_quantitative_data(self):
        """Load and display quantitative analytics."""
        try:
            # Get quantitative summaries (let the backend auto-detect available fields)
            summaries = self.analytics.get_quantitative_summaries(
                self.user_id, self.current_days
            )

            if "error" in summaries:
                self.ui.textEdit_quantitative_data.setPlainText(
                    "No quantitative data available for analysis."
                )
                return

            # Format quantitative data
            quant_text = f"""Quantitative Summaries (Last {self.current_days} days):

Field-by-Field Analysis:"""

            for field, stats in summaries.items():
                avg = stats.get("average", 0)
                min_val = stats.get("min", 0)
                max_val = stats.get("max", 0)
                count = stats.get("count", 0)

                quant_text += f"\n• {field.title()}:"
                quant_text += f"\n  - Average: {avg:.2f}"
                quant_text += f"\n  - Range: {min_val} - {max_val}"
                quant_text += f"\n  - Data points: {int(count)}"
                quant_text += "\n"

            self.ui.textEdit_quantitative_data.setPlainText(quant_text)

        except Exception as e:
            # In test mode, these are expected errors when mocks are used, so use DEBUG
            import os

            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"Error loading quantitative data: {e} (expected in tests with mocks)"
                )
            else:
                logger.error(f"Error loading quantitative data: {e}")
            self.ui.textEdit_quantitative_data.setPlainText(
                f"Error loading quantitative data: {str(e)}"
            )

    @handle_errors("refreshing analytics")
    def refresh_analytics(self):
        """Refresh all analytics data."""
        logger.info(f"Refreshing analytics for user {self.user_id}")
        self.load_analytics_data()

    @handle_errors("handling time period change")
    def on_time_period_changed(self, index):
        """Handle time period selection change."""
        time_periods = [7, 14, 30, 60, 90]
        if 0 <= index < len(time_periods):
            self.current_days = time_periods[index]
            logger.info(f"Changed time period to {self.current_days} days")
            self.load_analytics_data()

    @handle_errors("showing loading state")
    def show_loading_state(self):
        """Show loading state while data is being processed."""
        self.ui.label_wellness_score.setText("Wellness Score: Loading...")
        self.ui.textEdit_summary.setPlainText("Loading analytics data...")
        self.ui.textEdit_mood_data.setPlainText("Loading mood data...")
        self.ui.textEdit_habits_data.setPlainText("Loading habits data...")
        self.ui.textEdit_sleep_data.setPlainText("Loading sleep data...")
        self.ui.textEdit_quantitative_data.setPlainText("Loading quantitative data...")
        self.ui.textEdit_recommendations.setPlainText("Loading recommendations...")

    @handle_errors("showing error state")
    def show_error_state(self, error_message):
        """Show error state with message."""
        self.ui.label_wellness_score.setText("Wellness Score: Error")
        self.ui.textEdit_summary.setPlainText(f"Error: {error_message}")
        self.ui.textEdit_mood_data.setPlainText("Error loading data")
        self.ui.textEdit_habits_data.setPlainText("Error loading data")
        self.ui.textEdit_sleep_data.setPlainText("Error loading data")
        self.ui.textEdit_quantitative_data.setPlainText("Error loading data")
        self.ui.textEdit_recommendations.setPlainText("Error loading data")


@handle_errors("opening user analytics dialog", default_return=None)
def open_user_analytics_dialog(parent, user_id):
    """Open the user analytics dialog."""
    dialog = UserAnalyticsDialog(parent, user_id)
    return dialog.exec()
