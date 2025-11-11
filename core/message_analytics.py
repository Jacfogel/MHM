# core/message_analytics.py

"""
Message Analytics Module

Provides insights and analysis from sent message data to help users
understand message frequency, patterns, and delivery effectiveness.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from core.logger import get_component_logger
from core.message_management import get_recent_messages
from core.error_handling import handle_errors

logger = get_component_logger('user_activity')
analytics_logger = get_component_logger('user_activity')


class MessageAnalytics:
    @handle_errors("initializing message analytics", default_return=None)
    def __init__(self):
        """
        Initialize the MessageAnalytics instance.
        
        This class provides analytics and insights from sent message data.
        """
        pass
    
    @handle_errors("analyzing message frequency", default_return={"error": "Analysis failed"})
    def get_message_frequency(self, user_id: str, days: int = 30, category: Optional[str] = None) -> Dict:
        """
        Analyze message send frequency by category and time period.
        
        Args:
            user_id: The user ID to analyze
            days: Number of days to analyze (default: 30)
            category: Optional category filter (None = all categories)
            
        Returns:
            Dict containing frequency statistics
        """
        # Get all sent messages for the period
        messages = get_recent_messages(user_id, category=category, limit=1000, days_back=days)
        
        if not messages:
            return {
                "error": f"No message data available for the last {days} days",
                "period_days": days,
                "total_messages": 0
            }
        
        # Count messages by category
        category_counts = defaultdict(int)
        time_period_counts = defaultdict(int)
        category_time_period_counts = defaultdict(lambda: defaultdict(int))
        
        # Track daily frequency
        daily_counts = defaultdict(int)
        
        for msg in messages:
            msg_category = msg.get('category', 'unknown')
            time_period = msg.get('time_period', 'unknown')
            timestamp = msg.get('timestamp', '')
            
            category_counts[msg_category] += 1
            time_period_counts[time_period] += 1
            category_time_period_counts[msg_category][time_period] += 1
            
            # Extract date from timestamp for daily tracking
            try:
                if timestamp:
                    # Handle both formats: 'YYYY-MM-DD HH:MM:SS' and ISO format
                    if 'T' in timestamp:
                        date_str = timestamp.split('T')[0]
                    else:
                        date_str = timestamp.split(' ')[0]
                    daily_counts[date_str] += 1
            except Exception:
                pass
        
        # Calculate averages
        total_messages = len(messages)
        avg_per_day = total_messages / days if days > 0 else 0
        avg_per_category = {cat: count / days for cat, count in category_counts.items()} if days > 0 else {}
        
        # Find most active day
        most_active_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        
        return {
            "period_days": days,
            "total_messages": total_messages,
            "average_per_day": round(avg_per_day, 2),
            "category_counts": dict(category_counts),
            "category_averages": {cat: round(avg, 2) for cat, avg in avg_per_category.items()},
            "time_period_counts": dict(time_period_counts),
            "category_time_period_breakdown": {
                cat: dict(periods) for cat, periods in category_time_period_counts.items()
            },
            "most_active_day": {
                "date": most_active_day[0],
                "count": most_active_day[1]
            } if most_active_day else None,
            "daily_distribution": dict(daily_counts)
        }
    
    @handle_errors("analyzing message delivery success", default_return={"error": "Analysis failed"})
    def get_delivery_success_rate(self, user_id: str, days: int = 30) -> Dict:
        """
        Analyze message delivery success rates.
        
        Args:
            user_id: The user ID to analyze
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dict containing delivery statistics
        """
        messages = get_recent_messages(user_id, limit=1000, days_back=days)
        
        if not messages:
            return {
                "error": f"No message data available for the last {days} days",
                "period_days": days
            }
        
        # Count by delivery status
        status_counts = defaultdict(int)
        category_status_counts = defaultdict(lambda: defaultdict(int))
        
        for msg in messages:
            status = msg.get('delivery_status', 'unknown')
            category = msg.get('category', 'unknown')
            
            status_counts[status] += 1
            category_status_counts[category][status] += 1
        
        total = len(messages)
        sent_count = status_counts.get('sent', 0)
        success_rate = (sent_count / total * 100) if total > 0 else 0
        
        return {
            "period_days": days,
            "total_messages": total,
            "success_rate": round(success_rate, 2),
            "status_breakdown": dict(status_counts),
            "category_status_breakdown": {
                cat: dict(statuses) for cat, statuses in category_status_counts.items()
            }
        }
    
    @handle_errors("getting message summary", default_return={"error": "Summary failed"})
    def get_message_summary(self, user_id: str, days: int = 30) -> Dict:
        """
        Get a comprehensive summary of message activity.
        
        Args:
            user_id: The user ID to analyze
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dict containing summary statistics
        """
        frequency_data = self.get_message_frequency(user_id, days)
        delivery_data = self.get_delivery_success_rate(user_id, days)
        
        if "error" in frequency_data:
            return frequency_data
        
        if "error" in delivery_data:
            return delivery_data
        
        return {
            "period_days": days,
            "total_messages": frequency_data.get("total_messages", 0),
            "average_per_day": frequency_data.get("average_per_day", 0),
            "delivery_success_rate": delivery_data.get("success_rate", 0),
            "top_category": max(
                frequency_data.get("category_counts", {}).items(),
                key=lambda x: x[1]
            )[0] if frequency_data.get("category_counts") else None,
            "category_counts": frequency_data.get("category_counts", {}),
            "time_period_distribution": frequency_data.get("time_period_counts", {})
        }

