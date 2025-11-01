"""
AI Response Validator

Validates AI responses for quality issues like meta-text, code fragments, and other problems.
Used in manual AI functionality tests to automatically flag issues.
"""

import re
from typing import List, Dict, Tuple, Optional


class AIResponseValidator:
    """Validates AI responses for quality issues"""
    
    # Patterns that indicate meta-text or debugging information
    META_TEXT_PATTERNS = [
        r'\(50 words\)',
        r'\(.*words?\)',
        r'\(.*chars?\)',
        r'\(.*characters?\)',
        r'Response \d+:',
        r'Exchange \d+:',
        r'Mode:',
        r'User\d+\s*[,:]',  # Username prefix pattern (e.g., "User1, " or "User1:")
    ]
    
    # Patterns that indicate code fragments (Python/JSON)
    CODE_FRAGMENT_PATTERNS = [
        r'^import\s+\w+',
        r'^from\s+\w+\s+import',
        r'^def\s+\w+\s*\(',
        r'^class\s+\w+',
        r'"""',
        r'from typing import',
        r'from nltk\.',
        r'json\.(load|dump)',
        r'List\[',
        r'Dict\[',
        r'Optional\[',
    ]
    
    # Patterns that might indicate issues
    SUSPICIOUS_PATTERNS = [
        r'\{.*\{.*\}.*\}',  # Nested JSON/structures that might be code
        r'Response \d+',
        r'User\d+\s+R\d+',
        r'Command:',
        r'Chat:',
    ]
    
    @classmethod
    def validate_response(cls, response: str, prompt: str = "", test_type: str = "") -> Dict[str, any]:
        """
        Validate an AI response for quality issues.
        
        Args:
            response: The AI response to validate
            prompt: The original prompt (optional, for context)
            test_type: Type of test (e.g., "command", "chat", "contextual") (optional)
        
        Returns:
            Dict with:
                - valid: bool - Whether response passes basic validation
                - issues: List[str] - List of found issues
                - warnings: List[str] - List of warnings
                - status: str - "PASS", "PARTIAL", or "FAIL"
        """
        if not response or not isinstance(response, str):
            return {
                "valid": False,
                "issues": ["Response is empty or not a string"],
                "warnings": [],
                "status": "FAIL"
            }
        
        issues = []
        warnings = []
        
        # Check for meta-text
        meta_issues = cls._check_meta_text(response)
        if meta_issues:
            issues.extend(meta_issues)
        
        # Check for code fragments (depending on test type)
        if test_type != "command":  # Command mode might legitimately return JSON
            code_issues = cls._check_code_fragments(response)
            if code_issues:
                issues.extend(code_issues)
        else:
            # For command mode, check if it's clean JSON or if it has code fragments
            code_issues = cls._check_code_fragments_in_command(response)
            if code_issues:
                issues.extend(code_issues)
        
        # Check for suspicious patterns
        suspicious = cls._check_suspicious_patterns(response)
        if suspicious:
            warnings.extend(suspicious)
        
        # Check for username prefixes in responses (skip - names are fine in any response)
        # The AI can use user names conversationally, so we don't flag this
        # We only flag if it's clearly a test artifact (like "User1:" prefix), which is handled by meta-text patterns
        
        # Determine status
        if issues:
            # If there are critical issues (meta-text or code fragments), mark as FAIL
            critical_issues = [i for i in issues if "meta-text" in i.lower() or "code fragment" in i.lower()]
            if critical_issues:
                status = "FAIL"
            else:
                status = "PARTIAL"
        else:
            status = "PASS"
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "status": status
        }
    
    @classmethod
    def _check_meta_text(cls, response: str) -> List[str]:
        """Check for meta-text patterns in response"""
        issues = []
        
        for pattern in cls.META_TEXT_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(f"Meta-text detected: Response contains debugging/meta information (pattern: {pattern})")
        
        return issues
    
    @classmethod
    def _check_code_fragments(cls, response: str) -> List[str]:
        """Check for code fragments in response (for chat/contextual modes)"""
        issues = []
        
        for pattern in cls.CODE_FRAGMENT_PATTERNS:
            if re.search(pattern, response, re.MULTILINE):
                issues.append(f"Code fragment detected: Response contains code-like content (pattern: {pattern})")
        
        return issues
    
    @classmethod
    def _check_code_fragments_in_command(cls, response: str) -> List[str]:
        """Check for code fragments in command mode responses (should be clean JSON)"""
        issues = []
        
        # Command mode should return JSON, not Python code
        python_patterns = [
            r'^import\s+',
            r'^from\s+\w+\s+import',
            r'^def\s+',
            r'^class\s+',
            r'"""',
            r'from typing',
            r'from nltk',
        ]
        
        for pattern in python_patterns:
            if re.search(pattern, response, re.MULTILINE):
                issues.append(f"Code fragment in command response: Response contains Python code instead of clean JSON (pattern: {pattern})")
        
        return issues
    
    @classmethod
    def _check_suspicious_patterns(cls, response: str) -> List[str]:
        """Check for suspicious patterns that might indicate issues"""
        warnings = []
        
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append(f"Suspicious pattern detected: {pattern}")
        
        return warnings
    
    @classmethod
    def _has_username_prefix(cls, response: str) -> bool:
        """Check if response starts with a username/test identifier"""
        # Check if response starts with common test username patterns
        if re.match(r'^(TestUser|testuser|User\d+)\s*[,:]', response, re.IGNORECASE):
            return True
        return False
    
    @classmethod
    def review_response(cls, response: str, prompt: str, test_name: str, test_type: str = "") -> Tuple[str, List[str], List[str]]:
        """
        Review a response and return status, issues, and warnings.
        
        Args:
            response: The AI response
            prompt: The original prompt
            test_name: Name of the test
            test_type: Type of test (optional)
        
        Returns:
            Tuple of (status, issues_list, warnings_list)
        """
        validation = cls.validate_response(response, prompt, test_type)
        
        # Format issues and warnings for reporting
        issues_text = validation["issues"]
        warnings_text = validation["warnings"]
        
        return validation["status"], issues_text, warnings_text

