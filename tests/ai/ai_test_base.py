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
    
    def log_test(self, test_id, test_name, status, notes="", issues="", prompt="", response="", response_time=None, metrics=None, test_type=""):
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
        if response_time is not None:
            print(f"   Response Time: {response_time:.2f}s")
        if notes:
            print(f"   Notes: {notes}")
        if issues:
            print(f"   Issues: {issues}")
        print()
    
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

