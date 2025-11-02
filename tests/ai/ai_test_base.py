"""
Base class for AI functionality tests

Provides shared utilities for all AI test modules.
"""

import os
from datetime import datetime
from unittest.mock import patch

from ai.chatbot import AIChatBotSingleton
from tests.test_utilities import TestUserFactory
from core.user_management import get_user_id_by_identifier
from tests.ai.ai_response_validator import AIResponseValidator


class AITestBase:
    """Base class for AI functionality tests with shared utilities"""
    
    def __init__(self, test_data_dir, results_collector):
        """
        Initialize test base
        
        Args:
            test_data_dir: Directory for test data
            results_collector: Object that collects test results (must have results list)
        """
        self.test_data_dir = test_data_dir
        self.results_collector = results_collector
        self.chatbot = AIChatBotSingleton()
        self._test_users = {}  # Cache created test users
    
    def log_test(self, test_id, test_name, status, notes="", issues="", prompt="", response="", response_time=None, metrics=None, test_type="", context_info=None):
        """
        Log test result with optional performance metrics and automatic response review.
        
        Args:
            test_id: Test identifier (e.g., "T-1.1")
            test_name: Human-readable test name
            status: Initial status ("PASS", "PARTIAL", "FAIL")
            notes: Optional notes
            issues: Optional issues string
            prompt: Original prompt (for validation)
            response: AI response (for validation)
            response_time: Optional response time in seconds
            metrics: Optional metrics dict
            test_type: Type of test (e.g., "command", "chat", "contextual") - used for validation
            context_info: Optional dict with context information (check-ins, tasks, etc.) available to AI
        """
        # Automatically review response if provided
        reviewed_status = status
        review_issues = []
        review_warnings = []
        
        if response and isinstance(response, str) and test_type != "mode_detection":
            # Skip validation for mode detection tests (they return "Mode: X" which is expected)
            reviewed_status, review_issues, review_warnings = AIResponseValidator.review_response(
                response, prompt, test_name, test_type
            )
            
            # Combine existing issues with review issues
            all_issues = []
            if issues:
                all_issues.append(issues)
            if review_issues:
                all_issues.extend(review_issues)
            
            # Combine issues into a single string for display
            if all_issues:
                issues = " | ".join(all_issues)
            
            # Update status based on review (review can only make status worse, not better)
            if reviewed_status == "FAIL" and status in ["PASS", "PARTIAL"]:
                status = "FAIL"
            elif reviewed_status == "PARTIAL" and status == "PASS":
                status = "PARTIAL"
            
            # Add warnings to notes if any
            if review_warnings:
                if notes:
                    notes += " | "
                notes += "Warnings: " + " | ".join(review_warnings)
        
        result = {
            "test_id": test_id,
            "test_name": test_name,
            "status": status,
            "notes": notes,
            "issues": issues,
            "prompt": prompt,
            "response": response,
            "response_time": response_time,
            "metrics": metrics or {},
            "context_info": context_info or {},  # Include context information
            "manual_review_notes": "",  # Will be populated during AI review
            "timestamp": datetime.now().isoformat()
        }
        self.results_collector.results.append(result)
        
        if response_time is not None:
            self.results_collector.performance_metrics.append({
                "test_id": test_id,
                "response_time": response_time
            })
        
        # Print result (using text symbols to avoid Windows Unicode issues)
        status_symbol = {"PASS": "[PASS]", "FAIL": "[FAIL]", "PARTIAL": "[PARTIAL]"}.get(status, "[?]")
        print(f"{status_symbol} {test_id}: {test_name}")
        if prompt:
            # Safely encode prompt for Windows console (replace unicode that can't be encoded)
            try:
                # Use ASCII encoding with replacement for console output to avoid Windows encoding errors
                safe_prompt = prompt.encode('ascii', errors='replace').decode('ascii')
            except:
                # Fallback: truncate and show only safe characters
                safe_prompt = str(prompt)[:50] + "..." if len(str(prompt)) > 50 else str(prompt)
                try:
                    safe_prompt = safe_prompt.encode('ascii', errors='replace').decode('ascii')
                except:
                    safe_prompt = "[Prompt contains non-displayable characters]"
            print(f"   Prompt: {safe_prompt}")
        if issues:
            # Safely encode issues for Windows console
            try:
                safe_issues = issues.encode('ascii', errors='replace').decode('ascii')
            except:
                safe_issues = "[Issues contain non-displayable characters]"
            print(f"   Issues: {safe_issues}")
        if notes:
            # Safely encode notes for Windows console
            try:
                safe_notes = notes.encode('ascii', errors='replace').decode('ascii')
            except:
                safe_notes = "[Notes contain non-displayable characters]"
            print(f"   Notes: {safe_notes}")
    
    def _get_or_create_test_user(self, identifier):
        """Get or create a minimal test user, returning UUID"""
        if identifier in self._test_users:
            return self._test_users[identifier]
        
        # Create minimal test user (fastest option with minimal data)
        success = TestUserFactory.create_minimal_user(
            identifier,
            test_data_dir=self.test_data_dir
        )
        if success:
            # Patch config to use test data directory when looking up user
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                user_uuid = get_user_id_by_identifier(identifier)
                if user_uuid:
                    self._test_users[identifier] = user_uuid
                    return user_uuid
        
        # If user creation fails, return None (will test without user context)
        return None
    
    def _get_basic_test_user(self, identifier):
        """Get or create a basic test user with check-ins and tasks"""
        if identifier in self._test_users:
            return self._test_users[identifier]
        
        success = TestUserFactory.create_basic_user(
            identifier,
            enable_checkins=True,
            enable_tasks=True,
            test_data_dir=self.test_data_dir
        )
        
        if success:
            import core.config
            with patch.object(core.config, "BASE_DATA_DIR", self.test_data_dir), \
                 patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(self.test_data_dir, 'users')):
                user_uuid = get_user_id_by_identifier(identifier)
                if user_uuid:
                    self._test_users[identifier] = user_uuid
                    return user_uuid
        
        return None
    
    def _build_context_info(self, user_id: str = None, include_history: bool = False) -> dict:
        """
        Build comprehensive context information for test reporting.
        
        Args:
            user_id: User ID (if None, returns minimal context info)
            include_history: Whether to include conversation history in context check
            
        Returns:
            dict: Context information including feature enablement, data counts, etc.
        """
        context_info = {
            "context_provided": user_id is not None,
            "checkins_enabled": False,
            "tasks_enabled": False,
            "recent_checkins_count": 0,
            "checkins_today": 0,
            "conversation_history_count": 0,
            "active_tasks_count": 0,
            "context_keys": []
        }
        
        if not user_id:
            return context_info
        
        try:
            from user.context_manager import user_context_manager
            from core.response_tracking import get_recent_checkins, is_user_checkins_enabled
            from core.user_data_handlers import get_user_data
            from datetime import datetime
            
            # Check feature enablement
            account_result = get_user_data(user_id, 'account')
            account = account_result.get('account', {}) if account_result else {}
            features = account.get('features', {})
            
            context_info["checkins_enabled"] = features.get('checkins') == 'enabled' or is_user_checkins_enabled(user_id)
            context_info["tasks_enabled"] = features.get('task_management') == 'enabled'
            
            # Get check-in data counts
            if context_info["checkins_enabled"]:
                recent_checkins = get_recent_checkins(user_id, limit=10) if user_id else []
                context_info["recent_checkins_count"] = len(recent_checkins)
                checkins_today = [c for c in recent_checkins if c.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
                context_info["checkins_today"] = len(checkins_today)
            
            # Get task counts
            if context_info["tasks_enabled"]:
                try:
                    from tasks.task_management import load_active_tasks
                    tasks_data = load_active_tasks(user_id) if user_id else []
                    context_info["active_tasks_count"] = len(tasks_data) if isinstance(tasks_data, list) else 0
                except:
                    pass
            
            # Get context structure and extract relevant details
            try:
                context = user_context_manager.get_ai_context(user_id, include_conversation_history=include_history)
                if context and isinstance(context, dict):
                    context_info["context_keys"] = list(context.keys())
                    conversation_history = context.get('conversation_history', [])
                    context_info["conversation_history_count"] = len(conversation_history) if isinstance(conversation_history, list) else 0
                    
                    # Extract actual context details for reporting
                    user_profile = context.get('user_profile', {})
                    if user_profile:
                        if user_profile.get('preferred_name'):
                            context_info["user_name"] = user_profile.get('preferred_name')
                        if user_profile.get('active_categories'):
                            context_info["active_categories"] = user_profile.get('active_categories')
                        if user_profile.get('messaging_service'):
                            context_info["messaging_service"] = user_profile.get('messaging_service')
                        if user_profile.get('active_schedules'):
                            context_info["active_schedules_count"] = len(user_profile.get('active_schedules', []))
                    
                    recent_activity = context.get('recent_activity', {})
                    if recent_activity:
                        if recent_activity.get('recent_responses_count', 0) > 0:
                            context_info["recent_responses_count"] = recent_activity.get('recent_responses_count')
                        if recent_activity.get('last_response_date'):
                            context_info["last_response_date"] = recent_activity.get('last_response_date')
                        if recent_activity.get('recent_messages_count', 0) > 0:
                            context_info["recent_messages_count"] = recent_activity.get('recent_messages_count')
                    
                    mood_trends = context.get('mood_trends', {})
                    if mood_trends:
                        if mood_trends.get('trend') and mood_trends.get('trend') != 'no_data':
                            context_info["mood_trend"] = mood_trends.get('trend')
                        if mood_trends.get('average_mood') is not None:
                            context_info["average_mood"] = round(mood_trends.get('average_mood'), 2)
                        if mood_trends.get('average_energy') is not None:
                            context_info["average_energy"] = round(mood_trends.get('average_energy'), 2)
                    
                    conversation_insights = context.get('conversation_insights', {})
                    if conversation_insights:
                        if conversation_insights.get('recent_topics'):
                            context_info["recent_topics"] = conversation_insights.get('recent_topics')
                        if conversation_insights.get('engagement_level'):
                            context_info["engagement_level"] = conversation_insights.get('engagement_level')
                    
                    preferences = context.get('preferences', {})
                    if preferences:
                        # Only include relevant preference details (not empty)
                        if preferences.get('categories'):
                            context_info["preference_categories"] = preferences.get('categories')
            except:
                pass
                
        except Exception as e:
            # If any errors occur, just return what we have
            context_info["error"] = f"Error building context info: {str(e)[:50]}"
        
        return context_info
