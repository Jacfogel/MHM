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
        # Note: \{.*\{.*\}.*\} is NOT an issue for command mode - nested JSON is valid
        # Only flag this for non-command responses
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
        
        # Check for suspicious patterns (skip nested JSON warning for command mode - it's valid)
        if test_type != "command":
            suspicious = cls._check_suspicious_patterns(response)
            if suspicious:
                warnings.extend(suspicious)
        
        # NEW: Check for truncation issues
        truncation_issues = cls._check_truncation(response, prompt)
        if truncation_issues:
            issues.extend(truncation_issues)
        
        # NEW: Check for inappropriate assumptions (check-ins, tasks when none exist)
        assumption_issues = cls._check_inappropriate_assumptions(response, prompt, test_type)
        if assumption_issues:
            issues.extend(assumption_issues)
        
        # NEW: Check for past dates in task creation
        if test_type == "command" or "task" in prompt.lower():
            date_issues = cls._check_past_dates(response)
            if date_issues:
                issues.extend(date_issues)
        
        # NEW: Check for response appropriateness (length, off-topic)
        appropriateness_issues = cls._check_response_appropriateness(response, prompt, test_type)
        if appropriateness_issues:
            issues.extend(appropriateness_issues)
        
        # NEW: Check for missing context handling quality
        if "context" in test_type.lower() or "missing" in prompt.lower():
            context_quality_issues = cls._check_missing_context_handling(response, prompt)
            if context_quality_issues:
                issues.extend(context_quality_issues)
        
        # NEW: Check for role reversal (AI responding as if user is the AI)
        role_issues = cls._check_role_reversal(response, prompt)
        if role_issues:
            issues.extend(role_issues)
        
        # Check for username prefixes in responses (skip - names are fine in any response)
        # The AI can use user names conversationally, so we don't flag this
        # We only flag if it's clearly a test artifact (like "User1:" prefix), which is handled by meta-text patterns
        
        # Determine status
        if issues:
            # If there are critical issues (meta-text, code fragments, prompt-response mismatches), mark as FAIL
            critical_issues = [i for i in issues if any(critical in i.lower() for critical in 
                                                       ["meta-text", "code fragment", "truncated", "past date", "inappropriate assumption",
                                                        "should acknowledge", "should provide", "should answer", "should describe",
                                                        "should not assume", "should ask for information"])]
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
    def _check_truncation(cls, response: str, prompt: str) -> List[str]:
        """Check if response appears to be unexpectedly truncated"""
        issues = []
        
        # Check if response ends mid-sentence (likely truncated)
        if response and len(response) > 50:  # Only check longer responses
            response_clean = response.strip()
            # Check for incomplete sentences (ends without punctuation and not ending with ellipsis)
            if not response_clean.endswith(('.', '!', '?', '…', '...')) and not response_clean.endswith(('...', '…')):
                # Check if it ends mid-word or mid-sentence
                last_char = response_clean[-1]
                # Be less aggressive - only flag if it clearly ends mid-sentence
                if last_char.isalnum() or last_char in [',', ';', ':', '-']:
                    # Check if response length suggests truncation (common truncation points: 200, 300 chars)
                    # Only flag if it ends at exactly these common truncation points
                    truncation_points = [200, 300]
                    if len(response) in truncation_points:
                        issues.append(f"Response appears truncated: ends mid-sentence at {len(response)} chars (common truncation point)")
                    # Also check if ends mid-word (more obvious truncation)
                    elif last_char.isalnum() and len(response) > 150:
                        # Check if it ends mid-word by looking at last few chars
                        last_word = response_clean.split()[-1] if response_clean.split() else ""
                        # If last word is suspiciously short or cut off, might be truncated
                        if len(last_word) < 3 and len(response) > 180:
                            issues.append("Response appears truncated: ends mid-word without proper punctuation")
        
        return issues
    
    @classmethod
    def _check_inappropriate_assumptions(cls, response: str, prompt: str, test_type: str) -> List[str]:
        """Check if response makes inappropriate assumptions about check-ins, tasks, etc."""
        issues = []
        
        # Check for assumptions about daily tasks in check-in data (unclear reference)
        if "daily task" in response.lower() and "check-in" in response.lower():
            issues.append("Response makes unclear reference to 'daily task in check-in data' - this is ambiguous")
        
        # Check for assumptions about check-ins when user is new or context is missing
        if test_type == "contextual" and any(word in prompt.lower() for word in ["how am i", "how are you", "hello"]):
            # For new users or simple prompts, shouldn't assume specific check-in completion
            if any(phrase in response.lower() for phrase in [
                "haven't completed", "check-in", "daily task", "goals yet"
            ]):
                # This might be OK if context exists, but flag for review
                pass  # Will be caught by context quality checks
        
        return issues
    
    @classmethod
    def _check_past_dates(cls, response: str) -> List[str]:
        """Check for past dates in task creation responses"""
        issues = []
        
        # Check for dates in the past (2020-2024 especially old)
        import re
        from datetime import datetime
        
        # Match dates in various formats
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
        ]
        
        current_year = datetime.now().year
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, response)
            for match in matches:
                try:
                    if pattern.startswith(r'(\d{4})'):
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                    else:
                        year = int(match.group(3))
                        month = int(match.group(1))
                        day = int(match.group(2))
                    
                    # Check if date is more than 1 year in the past
                    if year < current_year - 1:
                        issues.append(f"Response contains past date: {match.group(0)} (year {year} is more than 1 year in the past)")
                    elif year == current_year - 1:
                        # Check if date is definitely in the past (more than 30 days ago)
                        try:
                            date_obj = datetime(year, month, day)
                            days_ago = (datetime.now() - date_obj).days
                            if days_ago > 30:
                                issues.append(f"Response contains past date: {match.group(0)} ({days_ago} days ago)")
                        except ValueError:
                            pass
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    @classmethod
    def _check_response_appropriateness(cls, response: str, prompt: str, test_type: str) -> List[str]:
        """Check if response is appropriate in length and topic - also validates prompt-response matching"""
        issues = []
        
        # Check for responses that are too long and go off-topic
        if len(response) > 250:  # Longer responses might be going off-topic
            # Check if prompt is simple but response is long
            if len(prompt) < 50 and len(response) > 300:
                issues.append(f"Response may be too long for simple prompt ({len(response)} chars for {len(prompt)} char prompt)")
        
        # Check if capabilities question gets answered correctly
        if "capabilities" in prompt.lower() or "what can you" in prompt.lower():
            # Should mention actual capabilities like listening, CRUD operations, support, etc.
            capability_keywords = ["listening", "support", "help", "task", "message", "check-in", "schedule", "remind"]
            has_capabilities = any(keyword in response.lower() for keyword in capability_keywords)
            if not has_capabilities and len(response) > 100:
                issues.append("Response about capabilities doesn't mention specific capabilities (tasks, messages, check-ins, etc.)")
        
        # Check prompt-response matching
        
        # "How are you doing today?" / "How are you?" - should get greeting/wellness response
        if re.search(r'\bhow are you (doing|feeling)?( today)?\??', prompt.lower()):
            # Response should acknowledge the question, not just redirect
            greeting_indicators = ["good", "well", "great", "fine", "doing", "feeling", "thanks", "thank", "here"]
            has_greeting_response = any(indicator in response.lower() for indicator in greeting_indicators)
            # Should not just ask what's on their mind or redirect
            redirect_indicators = ["what's on your mind", "what's on your", "how can i help", "tell me more", "what's up"]
            redirects = any(indicator in response.lower() for indicator in redirect_indicators)
            if redirects and not has_greeting_response:
                issues.append("Response to 'How are you?' should acknowledge the greeting, not just redirect or ask questions")
        
        # "Tell me something helpful" - should provide helpful information, not ask questions
        if "tell me something helpful" in prompt.lower() or "something helpful" in prompt.lower():
            # Response should provide information, not just ask questions
            question_count = response.count('?')
            # If more questions than statements, likely not providing helpful info
            if question_count > 1:
                issues.append("Response to 'Tell me something helpful' should provide helpful information, not ask questions")
        
        # "How are you feeling?" - should answer how AI is feeling, not redirect
        if re.search(r'\bhow are you feeling\??', prompt.lower()) and "with special characters" not in prompt.lower():
            # Response should answer the question about AI's state
            feeling_indicators = ["feeling", "doing well", "doing great", "good", "well", "great"]
            has_feeling_response = any(indicator in response.lower() for indicator in feeling_indicators)
            # Should not redirect to "How can I help"
            if "how can i help" in response.lower() and not has_feeling_response:
                issues.append("Response to 'How are you feeling?' should answer the question, not redirect to 'How can I help'")
        
        # "Tell me about yourself" - should describe AI, not ask for user info
        if "tell me about yourself" in prompt.lower():
            # Should describe AI capabilities/personality
            self_descriptors = ["i'm", "i am", "my", "assistant", "capabilities", "personality", "purpose", "here to"]
            has_self_description = any(desc in response.lower() for desc in self_descriptors)
            # Should not ask for user info (name, etc.)
            if "what's your name" in response.lower() or "your name" in response.lower():
                issues.append("Response to 'Tell me about yourself' should describe the AI, not ask for user information (role reversal)")
        
        # "Hello" / simple greeting - should not assume negative mental state
        if prompt.lower().strip() in ["hello", "hi", "hey"]:
            # Should not assume user is overwhelmed/anxious from simple greeting
            negative_assumptions = ["overwhelmed", "anxious", "stressed", "struggling", "difficult", "hard time"]
            assumes_negative = any(word in response.lower() for word in negative_assumptions)
            if assumes_negative:
                issues.append("Response to simple greeting should not assume user is overwhelmed/anxious without context")
        
        # "How am I doing?" / questions about user - should not use vague references when no context
        if re.search(r'\bhow am i (doing|feeling)?\??', prompt.lower()):
            # Check for vague references like "that", "it" with no previous context
            vague_refs = ["about that", "about it", "feeling about it", "feeling about that"]
            has_vague_refs = any(ref in response.lower() for ref in vague_refs)
            # Should ask for information explicitly
            explicit_requests = ["tell me", "share", "let me know", "can you tell me"]
            has_explicit = any(req in response.lower() for req in explicit_requests)
            if has_vague_refs and not has_explicit:
                issues.append("Response to 'How am I doing?' should ask for information explicitly, not use vague references like 'that' or 'it'")
        
        return issues
    
    @classmethod
    def _check_missing_context_handling(cls, response: str, prompt: str) -> List[str]:
        """Check quality of responses when context is missing"""
        issues = []
        
        # For missing context scenarios, response should be supportive and ask for information
        supportive_phrases = ["tell me", "let's figure", "together", "can you share", "how about"]
        has_supportive = any(phrase in response.lower() for phrase in supportive_phrases)
        
        # Generic/unhelpful responses when context is missing
        generic_responses = [
            "i'm here if you want to talk",
            "how are you feeling today",
        ]
        
        # Check for vague references when context is missing
        vague_refs = ["about that", "about it", "feeling about it", "feeling about that"]
        has_vague_refs = any(ref in response.lower() for ref in vague_refs)
        
        if not has_supportive:
            # Check if response is too generic
            is_too_generic = any(gr in response.lower() for gr in generic_responses)
            if is_too_generic and len(response) < 100:
                issues.append("Response to missing context should be more supportive and ask for information, not just generic 'how are you feeling'")
        
        # Vague references are problematic when context is missing
        if has_vague_refs and not has_supportive:
            issues.append("Response uses vague references ('that', 'it') when context is missing - should ask for information explicitly")
        
        return issues
    
    @classmethod
    def _check_role_reversal(cls, response: str, prompt: str) -> List[str]:
        """Check if AI responded as though the user was the AI (role reversal)"""
        issues = []
        
        # Patterns that indicate role reversal - AI describing the user as an AI
        role_reversal_patterns = [
            r'\byou are an? ai\b',
            r'\byou\'re an? ai\b',
            r'\byou are a supportive\b',
            r'\byour purpose is to\b',
            r'\byou can communicate\b',
            r'\byou\'re an ai assistant\b',
        ]
        
        # Especially problematic if prompt asks about "your" capabilities or "yourself"
        if any(word in prompt.lower() for word in ["your capabilities", "tell me about yourself", "what are you", "who are you"]):
            for pattern in role_reversal_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    issues.append("Role reversal detected: Response treats the user as the AI assistant instead of responding as the AI")
                    break  # Only report once
        
        # "Tell me about yourself" - should describe AI, not ask for user name/info
        if "tell me about yourself" in prompt.lower():
            if "what's your name" in response.lower() or ("your name" in response.lower() and "?" in response):
                issues.append("Role reversal detected: User asked AI to tell about itself, but AI asks for user's name instead")
        
        return issues
    
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

