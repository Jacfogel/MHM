# ai/chatbot.py

"""
ai/chatbot.py

A separate module to handle AI chatbot logic for any platform
(Discord, Email, etc.). This keeps AI-specific code in one place,
so we can phase in or out different messaging services without duplicating logic.
"""

import os
import asyncio
import threading
import requests
import collections
from typing import Optional
from core.logger import get_component_logger
from core.config import (
    LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL, 
    AI_TIMEOUT_SECONDS, AI_CACHE_RESPONSES,
    AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT,
    AI_CONNECTION_TEST_TIMEOUT, AI_API_CALL_TIMEOUT, AI_PERSONALIZED_MESSAGE_TIMEOUT,
    AI_CONTEXTUAL_RESPONSE_TIMEOUT, AI_QUICK_RESPONSE_TIMEOUT,
    AI_MAX_RESPONSE_LENGTH, AI_MAX_RESPONSE_WORDS, AI_MAX_RESPONSE_TOKENS, AI_MIN_RESPONSE_LENGTH,
    AI_CHAT_TEMPERATURE, AI_COMMAND_TEMPERATURE, AI_CLARIFICATION_TEMPERATURE,
)
# Legacy import removed - using get_user_data() instead
from core.response_tracking import get_recent_responses, store_chat_interaction
from core.user_data_handlers import get_user_data
from user.context_manager import user_context_manager
from ai.prompt_manager import get_prompt_manager
from ai.cache_manager import get_response_cache
from datetime import datetime
from core.error_handling import handle_errors



ai_logger = get_component_logger('ai')
logger = ai_logger

# Global prompt manager instance
prompt_manager = get_prompt_manager()

class AIChatBotSingleton:
    """
    A Singleton container for LM Studio API client.
    """
    _instance = None

    @handle_errors("creating AI chatbot instance", default_return=None)
    def __new__(cls):
        """Create a new instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @handle_errors("initializing AI chatbot", default_return=None)
    def __init__(self):
        """Initialize the object."""
        if self._initialized:
            return
        logger.info("Initializing shared AIChatBot with LM Studio API (singleton).")
        self.lm_studio_available = False
        self.response_cache = get_response_cache()
        self._generation_lock = threading.Lock()  # Prevent concurrent generations
        self._locks_by_user = collections.defaultdict(threading.Lock)  # Per-user locks for better concurrency
        
        # Test LM Studio connection
        self._test_lm_studio_connection()
        
        # If connection failed, check LM Studio status
        if not self.lm_studio_available:
            try:
                from ai.lm_studio_manager import is_lm_studio_ready
                if is_lm_studio_ready():
                    logger.info("LM Studio is now ready - retrying connection")
                    # Retry the connection test
                    self._test_lm_studio_connection()
                else:
                    logger.warning("LM Studio not ready - AI features will be limited")
            except Exception as e:
                logger.warning(f"LM Studio status check error: {e}")
        
        self._initialized = True

    @handle_errors("making cache key inputs", default_return=("", "", ""))
    def _make_cache_key_inputs(self, mode: str, user_prompt: str, user_id: Optional[str]):
        """
        Create consistent cache key inputs with validation.
        
        Returns:
            tuple: (user_prompt, user_id, mode)
        """
        # Validate mode
        if not mode or not isinstance(mode, str):
            logger.error(f"Invalid mode: {mode}")
            return "", "", ""
            
        if not mode.strip():
            logger.error("Empty mode provided")
            return "", "", ""
            
        # Validate user_prompt
        if not user_prompt or not isinstance(user_prompt, str):
            logger.error(f"Invalid user_prompt: {user_prompt}")
            return "", "", ""
            
        if not user_prompt.strip():
            logger.error("Empty user_prompt provided")
            return "", "", ""
            
        # Validate user_id if provided
        if user_id is not None and not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return "", "", ""
        """Create consistent cache key inputs using prompt_type parameter."""
        # Always use the raw prompt; pass mode as prompt_type into the cache
        return user_prompt, user_id, mode

    @handle_errors("testing LM Studio connection", default_return=None)
    def _test_lm_studio_connection(self):
        """
        Test connection to LM Studio server with validation.
        
        Returns:
            None: Always returns None
        """
        """Test connection to LM Studio server."""
        # In testing environments, skip real HTTP calls and assume LM Studio is available
        if os.getenv("MHM_TESTING") == "1":
            self.lm_studio_available = True
            logger.info("Skipping LM Studio connection test in testing mode")
            ai_logger.info("LM Studio connection assumed available for tests")
            return

        # Test with a simple request to models endpoint
        response = requests.get(
            f"{LM_STUDIO_BASE_URL}/models",
            headers={"Authorization": f"Bearer {LM_STUDIO_API_KEY}"},
            timeout=AI_CONNECTION_TEST_TIMEOUT
        )

        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            model_count = len(models)
            
            # Single consolidated log message
            logger.info(f"LM Studio connection successful. Available models: {model_count}")
            self.lm_studio_available = True

            # Log the first few models for debugging (only if there are models)
            if models:
                model_names = [model.get('id', 'unknown') for model in models[:3]]
                logger.debug(f"Available models (first 3): {model_names}")
            else:
                logger.warning("LM Studio is running but no models are loaded")
                ai_logger.warning("LM Studio running but no models loaded")

        else:
            logger.warning(f"LM Studio connection test failed: HTTP {response.status_code}")
            ai_logger.warning("LM Studio connection test failed",
                             status_code=response.status_code)
            self.lm_studio_available = False

    @handle_errors("calling LM Studio API", default_return=None)
    def _call_lm_studio_api(self, messages: list, max_tokens: int = 100, temperature: float = 0.2, timeout: int = None) -> Optional[str]:
        """Make an API call to LM Studio using OpenAI-compatible format."""
        if timeout is None:
            timeout = AI_API_CALL_TIMEOUT
            
        payload = {
            "model": LM_STUDIO_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.7,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LM_STUDIO_API_KEY}"
        }
        
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                return content.strip()
            else:
                logger.warning("LM Studio API returned empty choices")
                return None
        else:
            logger.warning(f"LM Studio API error: HTTP {response.status_code} - {response.text}")
            return None

    @handle_errors("getting contextual fallback", default_return="I'd like to help with that! How can I assist you today?")
    def _get_contextual_fallback(self, user_prompt: str, user_id: Optional[str] = None) -> str:
        """
        Provide contextually aware fallback responses based on user data and prompt analysis.
        Now actually analyzes user's check-in data for meaningful responses.
        """
        prompt_lower = user_prompt.lower()
        
        # Get user context
        context_result = get_user_data(user_id, 'context')
        user_context = context_result.get('context') if context_result else {}
        
        user_name = ""
        if user_id and user_context:
            user_name = user_context.get('preferred_name', '').strip()
        
        name_prefix = f"{user_name}, " if user_name else ""
        
        # Analyze user's actual check-in data for meaningful responses
        if user_id:
            recent_data = get_recent_responses(user_id, limit=10)  # Get more data for analysis
            
            if recent_data:
                # Analyze breakfast patterns
                breakfast_count = sum(1 for entry in recent_data if entry.get('ate_breakfast') is True)
                total_entries = len(recent_data)
                breakfast_rate = (breakfast_count / total_entries) * 100 if total_entries > 0 else 0
                
                # Analyze mood trends
                moods = [entry.get('mood') for entry in recent_data if entry.get('mood') is not None]
                avg_mood = sum(moods) / len(moods) if moods else None
                
                # Analyze energy trends
                energies = [entry.get('energy') for entry in recent_data if entry.get('energy') is not None]
                avg_energy = sum(energies) / len(energies) if energies else None
                
                # Check for specific questions about data
                if any(word in prompt_lower for word in ['breakfast', 'eat', 'ate']):
                    if breakfast_rate >= 80:
                        return (f"{name_prefix}Great news! You've been eating breakfast {breakfast_rate:.0f}% of the time in your recent check-ins. "
                               f"That's a really healthy habit to maintain!")
                    elif breakfast_rate >= 50:
                        return (f"{name_prefix}You've been eating breakfast {breakfast_rate:.0f}% of the time recently. "
                               f"Breakfast can really help with energy and focus throughout the day!")
                    else:
                        return (f"{name_prefix}I notice you've been eating breakfast {breakfast_rate:.0f}% of the time in your recent check-ins. "
                               f"Starting the day with a good breakfast can help with energy and mood!")
                
                # Check for questions about mood/energy
                if any(word in prompt_lower for word in ['mood', 'feeling', 'how have i been', 'lately']):
                    if avg_mood and avg_energy:
                        if avg_mood >= 4 and avg_energy >= 4:
                            return (f"{name_prefix}Looking at your recent check-ins, you've been doing really well! "
                                   f"Your average mood has been {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                                   f"Keep up those positive patterns!")
                        elif avg_mood <= 2 or avg_energy <= 2:
                            return (f"{name_prefix}I've noticed from your recent check-ins that things might be challenging lately. "
                                   f"Your average mood is {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                                   f"Remember that tough periods are temporary, and it's okay to take things one step at a time.")
                        else:
                            return (f"{name_prefix}Based on your recent check-ins, you're doing okay! "
                                   f"Your average mood is {avg_mood:.1f}/5 and energy {avg_energy:.1f}/5. "
                                   f"Small improvements each day add up to big changes over time.")
                
                # Check for general "how am I doing" questions
                if any(word in prompt_lower for word in ['how am i', 'how have i been', 'doing lately', 'progress']):
                    insights = []
                    if breakfast_rate >= 70:
                        insights.append("great breakfast habits")
                    if avg_mood and avg_mood >= 3.5:
                        insights.append("generally positive mood")
                    if avg_energy and avg_energy >= 3:
                        insights.append("decent energy levels")
                    
                    if insights:
                        return (f"{name_prefix}You're doing well in several areas: {', '.join(insights)}. Keep up the good work!")
                    else:
                        return (f"{name_prefix}There's room for improvement, but that's normal! Every small step counts.")
                
                # Check for specific data requests
                if any(word in prompt_lower for word in ['how many', 'times', 'count', 'frequency']):
                    if 'breakfast' in prompt_lower:
                        return (f"{name_prefix}You ate breakfast {breakfast_count}/{total_entries} times ({breakfast_rate:.0f}%).")
                    elif 'mood' in prompt_lower:
                        return (f"{name_prefix}Your average mood was {avg_mood:.1f}/5 - {'positive' if avg_mood >= 4 else 'neutral' if avg_mood >= 3 else 'challenging'}.")
                    elif 'energy' in prompt_lower:
                        return (f"{name_prefix}Your average energy was {avg_energy:.1f}/5 - {'high' if avg_energy >= 4 else 'moderate' if avg_energy >= 3 else 'low'}.")
        
        # Fall back to keyword-based responses if no data analysis possible
        
        # Handle work-related fatigue and lack of motivation
        work_fatigue_keywords = ['off work', 'don\'t feel like', 'tired', 'exhausted', 'no energy', 'can\'t motivate', 'don\'t want to']
        if any(keyword in prompt_lower for keyword in work_fatigue_keywords):
            return (f"{name_prefix}I understand you're feeling unmotivated. "
                   f"That's a common experience, especially after work. "
                   f"What small thing might help you feel a bit better?")
        
        # Mood and mental health inquiries
        mood_keywords = ['depressed', 'anxious', 'sad', 'worried', 'stressed', 'overwhelmed', 'down', 'hopeless']
        if any(keyword in prompt_lower for keyword in mood_keywords):
            return (f"{name_prefix}It sounds like you're going through a difficult time. "
                   f"Remember that your feelings are valid, and it's okay to not be okay. "
                   f"What small thing could help you feel a bit better right now? "
                   f"Sometimes just taking one tiny step is enough.")
        
        # Health and wellness topics
        health_keywords = ['sleep', 'exercise', 'diet', 'energy', 'tired', 'nutrition']
        if any(keyword in prompt_lower for keyword in health_keywords):
            return (f"{name_prefix}Taking care of your physical health is so important for overall wellbeing. "
                   f"Small, consistent changes often make the biggest difference. What aspect of your health "
                   f"would you like to focus on improving?")
        
        # Executive function and focus support
        focus_keywords = ['focus', 'concentrate', 'distracted', 'procrastinate', 'forget', 'remember', 'task', 'overwhelm']
        if any(keyword in prompt_lower for keyword in focus_keywords):
            return (f"{name_prefix}Tasks can feel overwhelming when focus is challenging. "
                   f"Try breaking things into tiny steps - even 5 minutes of progress counts. "
                   f"What's one small thing you could do right now?")
        
        # Motivational and goal-related
        goal_keywords = ['motivation', 'goal', 'habit', 'change', 'improve', 'better', 'start', 'begin']
        if any(keyword in prompt_lower for keyword in goal_keywords):
            return (f"{name_prefix}It's wonderful that you're thinking about positive changes! "
                   f"Big goals can feel overwhelming. Try starting with something tiny - "
                   f"even 2 minutes of progress is real progress. What's one small step you could take today?")
        
        # Relationship and social topics
        social_keywords = ['lonely', 'friends', 'family', 'relationship', 'social', 'isolated']
        if any(keyword in prompt_lower for keyword in social_keywords):
            return (f"{name_prefix}Connections with others are such an important part of wellbeing. "
                   f"Even small social interactions can make a meaningful difference. "
                   f"Is there someone you could reach out to today?")
        
        # Basic greetings and check-ins
        greeting_keywords = ['hello', 'hi', 'hey', 'how are you', 'good morning', 'good evening']
        if any(keyword in prompt_lower for keyword in greeting_keywords):
            return (f"Hello{', ' + user_name if user_name else ''}! I'm here to offer support and encouragement. "
                   f"How are you doing today? What's on your mind?")
        
        # Gratitude and positive interactions
        thanks_keywords = ['thank', 'appreciate', 'grateful', 'helpful']
        if any(keyword in prompt_lower for keyword in thanks_keywords):
            return (f"{name_prefix}You're very welcome! I'm glad I could help. "
                   f"Remember that seeking support and taking care of yourself shows real strength. "
                   f"Keep up the great work!")
        
        # Default contextual response - more empathetic fallback
        # Check for distress keywords
        distress_keywords = ['breakdown', 'overwhelmed', 'struggling', 'difficult', 'hard', 'tough', 'stress', 'anxiety', 'depression', 'sad', 'upset', 'worried', 'scared', 'frustrated', 'angry']
        if any(keyword in prompt_lower for keyword in distress_keywords):
            return (f"{name_prefix}I can hear that you're going through a really tough time right now. "
                   f"I'm here with you, and it's okay to feel overwhelmed. "
                   f"Would you like to talk about what's happening, or would it help to focus on just getting through the next few minutes?")
        
        # Check for general emotional support needs
        support_keywords = ['help', 'support', 'listen', 'talk', 'feel', 'emotion', 'mood', 'crisis']
        if any(keyword in prompt_lower for keyword in support_keywords):
            return (f"{name_prefix}I'm here to listen and support you through whatever you're experiencing. "
                   f"You don't have to face this alone. What would be most helpful right now?")
        
        # Default empathetic response
        return (f"{name_prefix}I'm here to listen and support you. "
               f"How are you feeling right now? What's on your mind?")

    @handle_errors("getting fallback response", default_return="I'd like to help with that! While my AI capabilities may be limited, I can offer encouragement and general wellness tips.")
    def _get_fallback_response(self, user_prompt: str) -> str:
        """Legacy fallback method for backwards compatibility."""
        return self._get_contextual_fallback(user_prompt)

    @handle_errors("getting fallback personalized message", default_return="Wishing you a wonderful day! Remember that every small step toward your wellbeing matters.")
    def _get_fallback_personalized_message(self, user_id: str) -> str:
        """
        Provide fallback personalized messages when AI model is not available.
        """
        # Try to get recent user data for basic personalization
        recent_data = get_recent_responses(user_id, limit=5)
        # Get user context
        context_result = get_user_data(user_id, 'context')
        user_context = context_result.get('context')
        user_name = user_context.get('preferred_name', '') if user_context else ''
        name_prefix = f"{user_name}, " if user_name else ""
        
        if recent_data:
            # Simple analysis of recent data
            latest_entry = recent_data[0]
            mood = latest_entry.get('mood', None)
            energy = latest_entry.get('energy', None)
            
            if mood and energy:
                if mood >= 4 and energy >= 4:
                    return (f"{name_prefix}You're doing great! Your recent check-ins show positive energy and mood. "
                           f"Keep up those healthy habits and celebrate your progress!")
                elif mood <= 2 or energy <= 2:
                    return (f"{name_prefix}I noticed things might be challenging for you lately. "
                           f"Remember that tough days are temporary, and it's okay to take things one step at a time. "
                           f"Consider reaching out for support if you need it.")
                else:
                    return (f"{name_prefix}You're making steady progress! Focus on the small things that "
                           f"make you feel good and energized. Every positive step counts.")
            
        return (f"{name_prefix}Hope you're having a good day! Remember to take care of yourself "
               f"and celebrate the small wins along the way.")

    @handle_errors("optimizing prompt", default_return=[{"role": "system", "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational."}, {"role": "user", "content": "Hello"}])
    def _optimize_prompt(self, user_prompt: str, context: Optional[str] = None) -> list:
        """Create optimized messages array for LM Studio API."""
        # Create system message using the centralized prompt loader
        system_message = {
            "role": "system",
            "content": prompt_manager.get_prompt('wellness')
        }
        
        # Create user message with optional context
        if context and len(context) < 200:  # Only include context if it's reasonable size
            user_content = f"Context: {context}\n\nQuestion: {user_prompt}"
        else:
            user_content = user_prompt
            
        user_message = {
            "role": "user", 
            "content": user_content
        }
        
        return [system_message, user_message]

    @handle_errors("creating comprehensive context prompt", default_return=[{"role": "system", "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational."}, {"role": "user", "content": "Hello"}])
    def _create_comprehensive_context_prompt(self, user_id: str, user_prompt: str) -> list:
        """Create a comprehensive context prompt with all user data for LM Studio."""
        # Get comprehensive user context
        context = user_context_manager.get_ai_context(user_id, include_conversation_history=True)
        
        # Build detailed context string with all available data
        context_parts = []
        
        # User profile information
        profile = context.get('user_profile', {})
        if profile.get('preferred_name'):
            context_parts.append(f"User's name: {profile['preferred_name']}")
        if profile.get('active_categories'):
            context_parts.append(f"Interests: {', '.join(profile['active_categories'])}")
        
        # Neurodivergent-specific context from user data
        user_context_data = context.get('user_context', {})
        if user_context_data:
            # Health conditions (ADHD, depression, etc.)
            health_conditions = user_context_data.get('custom_fields', {}).get('health_conditions', [])
            if health_conditions:
                context_parts.append(f"Health conditions: {', '.join(health_conditions)}")
            
            # User's notes for AI (specific needs, preferences)
            notes_for_ai = user_context_data.get('notes_for_ai', [])
            if notes_for_ai:
                context_parts.append(f"User notes for AI: {'; '.join(notes_for_ai)}")
            
            # Activities that encourage the user
            encouraging_activities = user_context_data.get('activities_for_encouragement', [])
            if encouraging_activities:
                context_parts.append(f"Encouraging activities: {', '.join(encouraging_activities)}")
            
            # Goals and interests
            goals = user_context_data.get('goals', [])
            if goals:
                context_parts.append(f"User goals: {', '.join(goals)}")
        
        # Recent check-in data analysis
        recent_checkins = get_recent_responses(user_id, limit=10)
        if recent_checkins:
            # Analyze breakfast patterns
            breakfast_count = sum(1 for entry in recent_checkins if entry.get('ate_breakfast') is True)
            total_entries = len(recent_checkins)
            breakfast_rate = (breakfast_count / total_entries) * 100 if total_entries > 0 else 0
            
            # Analyze mood and energy trends
            moods = [entry.get('mood') for entry in recent_checkins if entry.get('mood') is not None]
            energies = [entry.get('energy') for entry in recent_checkins if entry.get('energy') is not None]
            avg_mood = sum(moods) / len(moods) if moods else None
            avg_energy = sum(energies) / len(energies) if energies else None
            
            # Analyze other habits
            teeth_brushed_count = sum(1 for entry in recent_checkins if entry.get('brushed_teeth') is True)
            teeth_rate = (teeth_brushed_count / total_entries) * 100 if total_entries > 0 else 0
            
            context_parts.append(f"Recent check-in data (last {total_entries} entries):")
            context_parts.append(f"- Breakfast eaten: {breakfast_count}/{total_entries} times ({breakfast_rate:.0f}%)")
            if avg_mood:
                context_parts.append(f"- Average mood: {avg_mood:.1f}/5")
            if avg_energy:
                context_parts.append(f"- Average energy: {avg_energy:.1f}/5")
            context_parts.append(f"- Teeth brushed: {teeth_brushed_count}/{total_entries} times ({teeth_rate:.0f}%)")
            
            # Add specific recent entries for context
            recent_summary = []
            for i, entry in enumerate(recent_checkins[:3]):  # Last 3 entries
                entry_parts = []
                if entry.get('mood'):
                    entry_parts.append(f"mood={entry['mood']}")
                if entry.get('energy'):
                    entry_parts.append(f"energy={entry['energy']}")
                if entry.get('ate_breakfast') is not None:
                    entry_parts.append(f"breakfast={'yes' if entry['ate_breakfast'] else 'no'}")
                if entry.get('brushed_teeth') is not None:
                    entry_parts.append(f"teeth={'yes' if entry['brushed_teeth'] else 'no'}")
                if entry_parts:
                    recent_summary.append(f"Entry {i+1}: {', '.join(entry_parts)}")
            
            if recent_summary:
                context_parts.append(f"Recent entries: {'; '.join(recent_summary)}")
        
        # Recent activity summary
        recent_activity = context.get('recent_activity', {})
        if recent_activity.get('recent_responses_count', 0) > 0:
            context_parts.append(f"Activity: {recent_activity['recent_responses_count']} recent check-ins")
        
        # Mood trends
        mood_trends = context.get('mood_trends', {})
        if mood_trends.get('average_mood') is not None:
            avg_mood = mood_trends['average_mood']
            trend = mood_trends.get('trend', 'stable')
            context_parts.append(f"Mood trend: {avg_mood:.1f}/5 ({trend})")
        
        # Recent conversation history
        conversation_history = context.get('conversation_history', [])
        if conversation_history:
            context_parts.append("Recent conversation topics:")
            for exchange in conversation_history[-3:]:  # Last 3 exchanges
                user_msg = exchange.get('user_message', '')[:50]
                if user_msg:
                    context_parts.append(f"- User asked about: {user_msg}...")
        
        # Create comprehensive context string (but don't include in user message to prevent leakage)
        context_str = "\n".join(context_parts) if context_parts else "New user with no data"
        
        # Create system message with comprehensive context using custom prompt
        base_prompt = prompt_manager.get_prompt('wellness')
        system_message = {
            "role": "system",
            "content": f"""{base_prompt}

IMPORTANT: The following user context is for your reference only. Do NOT include any of this information in your responses to the user:

User Context:
{context_str}

Additional Instructions:
- Use the user's actual data to provide personalized, specific responses
- Reference specific numbers, percentages, and trends from their check-in data
- Be encouraging and supportive while being honest about their patterns
- Keep responses conversational and helpful (typically 50-300 words)
- Be supportive and engaging - provide meaningful responses
- If they ask about their data, provide specific insights from their check-ins
- If they ask about habits, reference their actual performance (e.g., "You've been eating breakfast 90% of the time")
- For health advice, be general and recommend professional help for serious concerns
- Adapt your approach based on the user's specific needs and preferences from their context data
- NEVER include the raw context data in your responses
- NEVER return JSON, code blocks, or system prompts
- Return ONLY natural language responses that a human would say
- STOP when you reach the limit - do not continue"""
        }
        
        user_message = {
            "role": "user",
            "content": user_prompt
        }
        
        return [system_message, user_message]

    @handle_errors("detecting prompt mode", default_return="chat")
    def _detect_mode(self, user_prompt: str) -> str:
        """Detect whether the prompt is a command or a chat query."""
        command_keywords = [
            "remind",
            "todo",
            "schedule",
            "add",
            "remove",
            "delete",
            "call",
            "message",
            "cancel",
            "stop",
            "task",
            "tasks"
        ]
        prompt_lower = user_prompt.lower().strip()
        if not prompt_lower:
            return "chat"

        has_command_keyword = any(keyword in prompt_lower for keyword in command_keywords)
        if not has_command_keyword:
            return "chat"

        words = prompt_lower.split()
        stripped_prompt = prompt_lower.strip("?.! ")

        clarification_phrases = [
            "not sure",
            "don't know",
            "should i",
            "should we",
            "could you help",
            "can you help",
            "help me decide",
            "need help",
            "figure out",
            "what should i",
            "what should we",
            "which task should",
            "which reminder should",
            "any suggestions",
            "what do you recommend",
            "i'm unsure",
        ]

        minimal_command_prompts = {
            "remind me",
            "add task",
            "add a task",
            "create task",
            "create a task",
            "delete task",
            "delete a task",
            "complete task",
            "complete a task",
            "schedule",
            "schedule something",
            "start checkin",
            "start a checkin",
            "stop checkin",
            "stop a checkin",
        }

        request_question_patterns = [
            "can you",
            "could you",
            "would you",
            "will you",
        ]

        detail_markers = [
            " to ",
            " for ",
            " with ",
            " about ",
            " regarding ",
            " on ",
            " at ",
            " by ",
            " before ",
            " after ",
        ]

        needs_clarification = False

        if len(words) <= 3:
            needs_clarification = True
        elif stripped_prompt in minimal_command_prompts:
            needs_clarification = True
        elif any(phrase in prompt_lower for phrase in clarification_phrases):
            needs_clarification = True
        else:
            has_question_request = '?' in prompt_lower and any(
                pattern in prompt_lower for pattern in request_question_patterns
            )
            if has_question_request and not any(marker in prompt_lower for marker in detail_markers):
                needs_clarification = True

        if needs_clarification:
            return "command_with_clarification"
        return "command"

    @handle_errors(
        "creating command parsing prompt",
        default_return=[
            {"role": "system", "content": "You are a command parser."},
            {"role": "user", "content": ""},
        ],
    )
    def _create_command_parsing_prompt(self, user_prompt: str) -> list:
        """Create a prompt instructing the model to return strict JSON."""
        system_message = {
            "role": "system",
            "content": prompt_manager.get_prompt('command'),
        }

        user_message = {"role": "user", "content": user_prompt}
        return [system_message, user_message]

    @handle_errors(
        "creating command parsing with clarification prompt",
        default_return=[
            {"role": "system", "content": "You are a command parser. Your job is to extract the user's intent and return it as JSON. If the user's request is ambiguous or incomplete, you should ask for clarification. Available actions: create_task, list_tasks, complete_task, delete_task, update_task, task_stats, start_checkin, checkin_status, show_profile, update_profile, profile_stats, show_schedule, schedule_status, add_schedule_period, show_analytics, mood_trends, habit_analysis, sleep_analysis, wellness_score, help, commands, examples, status, messages."},
            {"role": "user", "content": "Hello"},
        ],
    )
    def _create_command_parsing_with_clarification_prompt(self, user_prompt: str) -> list:
        """Create a prompt instructing the model to return strict JSON and ask for clarification if ambiguous."""
        system_message = {
            "role": "system",
            "content": prompt_manager.get_prompt('command'),
        }

        user_message = {"role": "user", "content": user_prompt}
        return [system_message, user_message]

    @handle_errors("generating AI response", default_return="I'm having trouble generating a response right now. Please try again in a moment.")
    def generate_response(
        self,
        user_prompt: str,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> str:
        """
        Generate a basic AI response from user_prompt, using LM Studio API.
        Uses adaptive timeout to prevent blocking for too long with improved performance optimizations.
        """
        # Validate timeout parameter
        if timeout is not None and not isinstance(timeout, int):
            logger.error(f"Invalid timeout parameter: {timeout} (expected int)")
            return "I'm having trouble generating a response. Please check your input and try again."
            
        if timeout is None:
            timeout = self._get_adaptive_timeout(AI_TIMEOUT_SECONDS)

        if mode is None:
            mode = self._detect_mode(user_prompt)
        mode = mode.lower()
        if mode != "chat" and not mode.startswith("command"):
            mode = "chat"

        prompt_for_key, uid_for_key, ptype = self._make_cache_key_inputs(mode, user_prompt, user_id)
        
        # Check if inputs are valid - if cache key inputs are empty, inputs were invalid
        if not prompt_for_key or not prompt_for_key.strip():
            logger.error(f"Invalid inputs provided to generate_response: mode={mode}, user_prompt={user_prompt}, user_id={user_id}")
            return "I'm having trouble generating a response. Please check your input and try again."

        # Check cache first, but skip cache for chat mode and fallback responses to allow variation
        if mode != "chat":
            cached_response = self.response_cache.get(prompt_for_key, uid_for_key, prompt_type=ptype)
            if cached_response and not cached_response.startswith("I'm here to listen and support you"):
                ai_logger.debug("AI response served from cache", 
                               user_id=user_id, 
                               mode=mode, 
                               prompt_length=len(user_prompt))
                return cached_response
        
        # Test connection if not available
        if not self.lm_studio_available:
            self._test_lm_studio_connection()
        
        # Use fallback if LM Studio is not available
        if not self.lm_studio_available:
            response = self._get_contextual_fallback(user_prompt, user_id)
            # Don't cache fallback responses to allow variation
            ai_logger.warning("AI response using fallback - LM Studio unavailable", 
                             user_id=user_id, 
                             mode=mode, 
                             prompt_length=len(user_prompt))
            return response

        # Use per-user locks for better concurrency
        lock = self._locks_by_user[user_id or "__anon__"]
        lock_acquired = lock.acquire(blocking=True, timeout=3)
        if not lock_acquired:
            logger.warning("API is busy, using enhanced contextual fallback")
            ai_logger.warning("AI response using fallback - API busy", 
                             user_id=user_id, 
                             mode=mode, 
                             prompt_length=len(user_prompt))
            response = self._get_contextual_fallback(user_prompt, user_id)
            # Don't cache fallback responses to allow variation
            return response

        logger.debug(
            f"AIChatBot generating response via LM Studio for prompt: {user_prompt[:60]} in mode {mode}..."
        )

        if mode == "command":
            messages = self._create_command_parsing_prompt(user_prompt)
            max_tokens = 60
            temperature = AI_COMMAND_TEMPERATURE
        elif mode == "command_with_clarification":
            messages = self._create_command_parsing_with_clarification_prompt(user_prompt)
            max_tokens = 120
            temperature = AI_CLARIFICATION_TEMPERATURE
        else:
            messages = self._create_comprehensive_context_prompt(user_id, user_prompt)
            # Use centralized token limit from config
            max_tokens = AI_MAX_RESPONSE_TOKENS
            temperature = AI_CHAT_TEMPERATURE
        
        try:
            # Call LM Studio API with adaptive timeout
            result = self._call_lm_studio_api(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
            )
            
            if result:
                response = result.strip()
                
                # Enforce response length limit with smart truncation using centralized config
                response = self._smart_truncate_response(response, AI_MAX_RESPONSE_LENGTH, AI_MAX_RESPONSE_WORDS)
                
                # Enhance response for better conversational engagement
                response = self._enhance_conversational_engagement(response)
                
                # Cache successful responses (skip cache for chat mode to allow variation)
                if mode != "chat":
                    self.response_cache.set(prompt_for_key, response, uid_for_key, prompt_type=ptype)
                
                # Store chat interaction for context and reference
                if mode == "chat" and user_id:
                    from core.response_tracking import store_chat_interaction
                    store_chat_interaction(user_id, user_prompt, response, context_used=True)
                
                ai_logger.info("AI response generated successfully", 
                              user_id=user_id, 
                              mode=mode, 
                              prompt_length=len(user_prompt),
                              response_length=len(response),
                              max_tokens=max_tokens,
                              temperature=temperature)
                return response
            else:
                # API failed, use contextual fallback
                response = self._get_contextual_fallback(user_prompt, user_id)
                # Don't cache fallback responses to allow variation
                
                # Store fallback chat interaction for context and reference
                if mode == "chat" and user_id:
                    from core.response_tracking import store_chat_interaction
                    store_chat_interaction(user_id, user_prompt, response, context_used=False)
                
                ai_logger.error("AI response generation failed - using fallback", 
                               user_id=user_id, 
                               mode=mode, 
                               prompt_length=len(user_prompt))
                return response
        finally:
            # Always release the lock
            if lock_acquired:
                lock.release()

    @handle_errors("generating async AI response")
    async def async_generate_response(self, user_prompt: str, user_id: Optional[str] = None) -> str:
        """
        Async variant if you need to integrate with an async context.
        """
        # Use get_running_loop() first, fallback to get_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_response, user_prompt, AI_TIMEOUT_SECONDS, user_id)

    @handle_errors("checking AI availability", default_return=False)
    def is_ai_available(self) -> bool:
        """
        Check if the AI model is available and functional.
        """
        return self.lm_studio_available
    
    @handle_errors("reloading system prompt", default_return=None)
    def reload_system_prompt(self):
        """
        Reload the system prompt from file (useful for development and testing).
        """
        prompt_manager.reload_custom_prompt()
        logger.info("System prompt reloaded via AI chatbot")
    
    def test_system_prompt_integration(self) -> dict:
        """
        Test the system prompt integration and return status information.
        """
        test_results = {
            'custom_prompt_enabled': AI_USE_CUSTOM_PROMPT,
            'prompt_file_exists': os.path.exists(AI_SYSTEM_PROMPT_PATH),
            'custom_prompt_loaded': prompt_manager.has_custom_prompt(),
            'prompt_length': prompt_manager.custom_prompt_length(),
            'fallback_prompts_available': len(prompt_manager.fallback_prompt_keys()) > 0,
        }
        
        # Test each prompt type
        for prompt_type in ['wellness', 'command', 'neurodivergent_support']:
            try:
                prompt = prompt_manager.get_prompt(prompt_type)
                test_results[f'{prompt_type}_prompt_works'] = True
                test_results[f'{prompt_type}_prompt_length'] = len(prompt)
            except Exception as e:
                test_results[f'{prompt_type}_prompt_works'] = False
                test_results[f'{prompt_type}_prompt_error'] = str(e)
        
        return test_results

    @handle_errors("getting AI status", default_return={})
    def get_ai_status(self) -> dict:
        """
        Get detailed status information about the AI system.
        """
        return {
            'lm_studio_available': self.lm_studio_available,
            'lm_studio_base_url': LM_STUDIO_BASE_URL,
            'lm_studio_model': LM_STUDIO_MODEL,
            'ai_functional': self.lm_studio_available,
            'fallback_mode': not self.lm_studio_available,
            'cache_enabled': AI_CACHE_RESPONSES,
            'cache_size': len(self.response_cache.cache),
            'timeout_seconds': AI_TIMEOUT_SECONDS,
            # System prompt information
            'custom_prompt_enabled': AI_USE_CUSTOM_PROMPT,
            'custom_prompt_path': AI_SYSTEM_PROMPT_PATH,
            'custom_prompt_loaded': prompt_manager.has_custom_prompt(),
            'prompt_length': prompt_manager.custom_prompt_length(),
            'prompt_file_exists': os.path.exists(AI_SYSTEM_PROMPT_PATH),
        }

    @handle_errors("generating personalized message", default_return="Wishing you a wonderful day! Remember that every small step toward your wellbeing matters.")
    def generate_personalized_message(self, user_id: str, timeout: Optional[int] = None) -> str:
        """
        Generate a personalized message by examining the user's recent responses
        (check-in data). Uses longer timeout since this is not real-time.
        """
        if timeout is None:
            timeout = AI_PERSONALIZED_MESSAGE_TIMEOUT
            
        if not self.lm_studio_available:
            return self._get_fallback_personalized_message(user_id)

        recent_data = get_recent_responses(user_id, limit=3)  # Reduced for performance
        summary_lines = []
        for entry in recent_data:
            line_parts = []
            for k, v in entry.items():
                if k == "timestamp":
                    continue
                line_parts.append(f"{k}={v}")
            summary_lines.append(", ".join(line_parts))

        user_summary = "\n".join(summary_lines) if summary_lines else "No recent data available."
        
        # Create a more concise prompt for better performance
        prompt = (
            f"Create a brief, encouraging message for a user based on their recent wellness data. "
            f"Data: {user_summary[:200]}. "  # Limit context size
            f"Keep it supportive, personal, and under 100 words."
        )
        
        # Check cache for personalized messages too
        cached_response = self.response_cache.get(prompt, user_id, prompt_type="personalized")
        if cached_response:
            return cached_response
            
        response = self.generate_response(prompt, timeout=timeout, user_id=user_id)
        
        # Cache the final response for personalized messages
        self.response_cache.set(
            prompt, response, user_id, prompt_type="personalized",
            metadata={"mode": "personalized"}
        )
        
        return response

    @handle_errors("generating quick response", default_return="I'm having trouble responding right now. Please try again in a moment.")
    def generate_quick_response(self, user_prompt: str, user_id: Optional[str] = None) -> str:
        """
        Generate a quick response for real-time chat (Discord, etc.).
        Uses shorter timeout optimized for responsiveness.
        """
        # Use shorter timeout for real-time interactions
        return self.generate_response(user_prompt, timeout=AI_QUICK_RESPONSE_TIMEOUT, user_id=user_id)

    @handle_errors("generating contextual response", default_return="I'm having trouble generating a contextual response right now. Please try again in a moment.")
    def generate_contextual_response(self, user_id: str, user_prompt: str, timeout: Optional[int] = None) -> str:
        """
        Generate a context-aware response using comprehensive user data.
        Integrates with existing UserContext and UserPreferences systems.
        """
        if timeout is None:
            timeout = AI_CONTEXTUAL_RESPONSE_TIMEOUT
            
        # Get comprehensive context 
        context = user_context_manager.get_ai_context(user_id, include_conversation_history=True)
        
        # Create a meaningful but concise context summary for better AI performance
        context_summary = []
        
        # User profile information
        profile = context.get('user_profile', {})
        if profile.get('preferred_name'):
            context_summary.append(f"User's name is {profile['preferred_name']}")
        if profile.get('active_categories'):
            # Limit to top 2 categories for brevity
            categories = profile['active_categories'][:2]
            context_summary.append(f"Interested in: {', '.join(categories)}")
        
        # Recent activity (only if significant)
        recent_activity = context.get('recent_activity', {})
        if recent_activity.get('recent_responses_count', 0) > 2:
            context_summary.append(f"Active user with {recent_activity['recent_responses_count']} recent check-ins")
        
        # Mood trends (only if data available)
        mood_trends = context.get('mood_trends', {})
        if mood_trends.get('average_mood') is not None:
            avg_mood = mood_trends['average_mood']
            context_summary.append(f"Recent mood: {avg_mood:.1f}/5")
        
        # Create context string (keep it concise for performance)
        context_str = ". ".join(context_summary) if context_summary else "New user"
        
        if not self.lm_studio_available:
            # Use enhanced contextual fallback with user information and data analysis
            fallback_response = self._get_contextual_fallback(user_prompt, user_id)
            
            # Enhance fallback with context if available
            if context_summary:
                user_name = profile.get('preferred_name', '')
                if user_name and not user_name in fallback_response:
                    fallback_response = fallback_response.replace("Hello!", f"Hello {user_name}!")
                    fallback_response = fallback_response.replace("Hi!", f"Hi {user_name}!")
            
            # Store the chat interaction
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            store_chat_interaction(user_id, user_prompt, fallback_response, context_used=True)
            user_context_manager.add_conversation_exchange(user_id, user_prompt, fallback_response)
            return fallback_response
        
        # Create comprehensive context-aware messages for LM Studio with all user data
        messages = self._create_comprehensive_context_prompt(user_id, user_prompt)
        
        # For data analysis questions, skip cache to ensure fresh responses
        data_analysis_keywords = ['how often', 'how many', 'check', 'frequency', 'times', 'average', 'lately', 'recent']
        is_data_question = any(keyword in user_prompt.lower() for keyword in data_analysis_keywords)
        
        if not is_data_question:
            # Check cache using the cache's own key generation method
            cached_response = self.response_cache.get(user_prompt, user_id, prompt_type="contextual")
            if cached_response:
                # Still store and add to conversation for tracking
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                store_chat_interaction(user_id, user_prompt, cached_response, context_used=True)
                user_context_manager.add_conversation_exchange(user_id, user_prompt, cached_response)
                return cached_response

        # Generate AI response with context
        # Use per-user locks for better concurrency
        lock = self._locks_by_user[user_id or "__anon__"]
        lock_acquired = lock.acquire(blocking=True, timeout=5)
        if not lock_acquired:
            logger.warning("API is busy, using enhanced contextual fallback")
            fallback_response = self._get_contextual_fallback(user_prompt, user_id)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            store_chat_interaction(user_id, user_prompt, fallback_response, context_used=False)
            user_context_manager.add_conversation_exchange(user_id, user_prompt, fallback_response)
            return fallback_response

        logger.debug(f"Generating contextual response for user {user_id} with context: {context_str[:60]}...")
        
        try:
            # Call LM Studio API with context
            result = self._call_lm_studio_api(
                messages=messages,
                max_tokens=80,  # Shorter responses for faster generation
                temperature=0.2,  # Lower temperature for focused responses
                timeout=timeout
            )
            
            if result:
                response = result.strip()
                # Ensure response acknowledges the user by name if available
                user_name = profile.get('preferred_name', '')
                if user_name and user_name.lower() not in response.lower():
                    # Prepend name if not already included
                    response = f"{user_name}, {response}"
            else:
                response = self._get_contextual_fallback(user_prompt, user_id)
                logger.info("Using contextual fallback response")
            
            # Cache the final response for contextual prompts
            self.response_cache.set(
                user_prompt, response, user_id, prompt_type="contextual",
                metadata={"mode": "contextual"}
            )
            
            # Single call to record the interaction
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            store_chat_interaction(user_id, user_prompt, response, context_used=True)
            user_context_manager.add_conversation_exchange(user_id, user_prompt, response)
            
            return response
        finally:
            # Always release the lock
            if lock_acquired:
                lock.release()

    @handle_errors("detecting resource constraints", default_return=False)
    def _detect_resource_constraints(self) -> bool:
        """Detect if system is resource-constrained."""
        import psutil
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Consider system constrained if:
        # - Memory usage > 90%
        # - Available memory < 2 GB
        # - CPU usage > 80%
        is_constrained = (
            memory.percent > 90 or 
            memory.available < (2 * 1024**3) or  # 2 GB
            cpu_percent > 80
        )
        
        if is_constrained:
            logger.warning(f"System resource constraints detected: Memory {memory.percent}%, CPU {cpu_percent}%, Available RAM {memory.available / (1024**3):.1f}GB")
        
        return is_constrained

    @handle_errors("smart truncating response", default_return="...")
    def _smart_truncate_response(self, text: str, max_chars: int, max_words: int = None) -> str:
        """
        Smartly truncate response to avoid mid-sentence cuts.
        Supports both character and word limits.
        """
        if max_words:
            words = text.split()
            if len(words) > max_words:
                return " ".join(words[:max_words]).rstrip(" ,.;:!?") + "…"
        
        if len(text) <= max_chars:
            return text
        
        # Try to cut at a sentence boundary within max_chars
        cut = text[:max_chars]
        for mark in (". ", "! ", "? "):
            idx = cut.rfind(mark)
            if idx >= 0 and idx > max_chars * 0.6:
                return cut[:idx+1]
        
        return cut.rstrip() + "…"

    @handle_errors("enhancing conversational engagement", default_return="")
    def _enhance_conversational_engagement(self, response: str) -> str:
        """
        Enhance response to ensure good conversational engagement.
        Adds engagement prompts if the response doesn't already have them.
        """
        if not response or len(response.strip()) < AI_MIN_RESPONSE_LENGTH:
            return response
        
        # Check if response already ends with engagement indicators
        response_lower = response.lower().strip()
        engagement_indicators = [
            "?", "how are you", "what do you think", "would you like", 
            "tell me more", "i'm here", "feel free", "let me know",
            "what's on your mind", "how can i help", "anything else"
        ]
        
        # If response already has engagement, return as-is
        for indicator in engagement_indicators:
            if response_lower.endswith(indicator) or indicator in response_lower[-50:]:
                return response
        
        # Add gentle engagement prompt if response seems complete but lacks engagement
        if response.endswith(('.', '!', '...')):
            engagement_options = [
                " How are you feeling about that?",
                " I'm here if you want to talk more about this.",
                " What would help you feel better right now?",
                " Would you like to tell me more about what's on your mind?",
                " How can I support you with this?",
                " What else is on your mind today?"
            ]
            
            # Choose engagement based on response content
            if any(word in response_lower for word in ['difficult', 'hard', 'struggle', 'tough', 'challenge']):
                return response + engagement_options[0]  # "How are you feeling about that?"
            elif any(word in response_lower for word in ['good', 'great', 'better', 'improve', 'progress']):
                return response + engagement_options[3]  # "Would you like to tell me more..."
            elif any(word in response_lower for word in ['help', 'support', 'need', 'want']):
                return response + engagement_options[4]  # "How can I support you..."
            else:
                return response + engagement_options[5]  # "What else is on your mind..."
        
        return response

    @handle_errors("getting adaptive timeout", default_return=15)
    def _get_adaptive_timeout(self, base_timeout: int) -> int:
        """Get adaptive timeout based on system resources."""
        if self._detect_resource_constraints():
            # Increase timeout for resource-constrained systems
            return min(base_timeout * 2, 60)  # Cap at 60 seconds
        return base_timeout

@handle_errors("getting AI chatbot instance")
def get_ai_chatbot():
    """
    Return the shared AIChatBot instance.
    """
    return AIChatBotSingleton()
