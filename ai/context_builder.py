# context_builder.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.response_tracking import get_recent_responses
from core.user_data_handlers import get_user_data
from user.context_manager import user_context_manager

# Route context builder logs to AI component
context_logger = get_component_logger('ai_context')
logger = context_logger

@dataclass
class ContextData:
    """Structured context data for AI interactions"""
    user_profile: Dict[str, Any] = None
    user_context: Dict[str, Any] = None
    recent_checkins: List[Dict[str, Any]] = None
    conversation_history: List[Dict[str, Any]] = None
    current_time: datetime = None
    
    def __post_init__(self):
        """Post-initialization setup"""
        if self.user_profile is None:
            self.user_profile = {}
        if self.user_context is None:
            self.user_context = {}
        if self.recent_checkins is None:
            self.recent_checkins = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.current_time is None:
            self.current_time = datetime.now()

@dataclass
class ContextAnalysis:
    """Analysis results from context data"""
    breakfast_rate: float = 0.0
    avg_mood: Optional[float] = None
    avg_energy: Optional[float] = None
    teeth_brushing_rate: float = 0.0
    mood_trend: str = "stable"
    energy_trend: str = "stable"
    overall_wellness_score: float = 0.0
    insights: List[str] = None
    
    def __post_init__(self):
        """Post-initialization setup"""
        if self.insights is None:
            self.insights = []

class ContextBuilder:
    """Builds comprehensive context for AI interactions"""
    
    def __init__(self):
        """Initialize the context builder"""
        pass
    
    @handle_errors("building user context", default_return=ContextData())
    def build_user_context(self, user_id: str, include_conversation_history: bool = True) -> ContextData:
        """
        Build comprehensive context for a user
        
        Args:
            user_id: User ID to build context for
            include_conversation_history: Whether to include conversation history
            
        Returns:
            ContextData object with all available context
        """
        try:
            logger.debug(f"Building context for user {user_id}, include_conversation_history={include_conversation_history}")
            
            # Get comprehensive user context from context manager
            context = user_context_manager.get_ai_context(
                user_id, 
                include_conversation_history=include_conversation_history
            )
            
            # Get recent check-ins
            recent_checkins = get_recent_responses(user_id, limit=10)
            logger.debug(f"Retrieved {len(recent_checkins)} recent check-ins for user {user_id}")
            
            # Get user profile and context data
            profile_result = get_user_data(user_id, 'profile')
            context_result = get_user_data(user_id, 'context')
            
            user_profile = profile_result.get('profile', {}) if profile_result else {}
            user_context = context_result.get('context', {}) if context_result else {}
            
            conversation_history = context.get('conversation_history', []) if context else []
            
            logger.debug(f"Context built successfully for user {user_id}: profile_fields={len(user_profile)}, context_fields={len(user_context)}, conversation_entries={len(conversation_history)}")
            
            return ContextData(
                user_profile=user_profile,
                user_context=user_context,
                recent_checkins=recent_checkins,
                conversation_history=conversation_history,
                current_time=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error building context for user {user_id}: {e}")
            return ContextData()
    
    @handle_errors("analyzing context data", default_return=ContextAnalysis())
    def analyze_context(self, context_data: ContextData) -> ContextAnalysis:
        """
        Analyze context data to extract insights
        
        Args:
            context_data: Context data to analyze
            
        Returns:
            ContextAnalysis with insights and trends
        """
        try:
            recent_checkins = context_data.recent_checkins
            if not recent_checkins:
                logger.debug("No recent check-ins available for analysis")
                return ContextAnalysis()
            
            total_entries = len(recent_checkins)
            logger.debug(f"Analyzing {total_entries} recent check-ins")
            
            # Analyze breakfast patterns
            breakfast_count = sum(1 for entry in recent_checkins if entry.get('ate_breakfast') is True)
            breakfast_rate = (breakfast_count / total_entries) * 100 if total_entries > 0 else 0
            
            # Analyze mood trends
            moods = [entry.get('mood') for entry in recent_checkins if entry.get('mood') is not None]
            avg_mood = sum(moods) / len(moods) if moods else None
            
            # Analyze energy trends
            energies = [entry.get('energy') for entry in recent_checkins if entry.get('energy') is not None]
            avg_energy = sum(energies) / len(energies) if energies else None
            
            # Analyze teeth brushing
            teeth_brushed_count = sum(1 for entry in recent_checkins if entry.get('brushed_teeth') is True)
            teeth_brushing_rate = (teeth_brushed_count / total_entries) * 100 if total_entries > 0 else 0
            
            # Determine trends
            mood_trend = self._determine_trend(moods)
            energy_trend = self._determine_trend(energies)
            
            # Calculate overall wellness score
            wellness_score = self._calculate_wellness_score(
                breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate
            )
            
            # Generate insights
            insights = self._generate_insights(
                breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate,
                mood_trend, energy_trend
            )
            
            logger.debug(f"Context analysis completed: wellness_score={wellness_score:.1f}, mood_trend={mood_trend}, energy_trend={energy_trend}, insights_count={len(insights)}")
            
            return ContextAnalysis(
                breakfast_rate=breakfast_rate,
                avg_mood=avg_mood,
                avg_energy=avg_energy,
                teeth_brushing_rate=teeth_brushing_rate,
                mood_trend=mood_trend,
                energy_trend=energy_trend,
                overall_wellness_score=wellness_score,
                insights=insights
            )
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return ContextAnalysis()
    
    def _determine_trend(self, values: List[float]) -> str:
        """Determine trend from a list of values"""
        if len(values) < 3:
            return "stable"
        
        # Simple trend analysis - compare first half to second half
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 0.5:
            return "improving"
        elif second_avg < first_avg - 0.5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_wellness_score(self, breakfast_rate: float, avg_mood: Optional[float], 
                                 avg_energy: Optional[float], teeth_brushing_rate: float) -> float:
        """Calculate overall wellness score (0-100)"""
        score = 0.0
        factors = 0
        
        # Breakfast factor (25% weight)
        if breakfast_rate > 0:
            score += (breakfast_rate / 100) * 25
            factors += 1
        
        # Mood factor (30% weight)
        if avg_mood is not None:
            score += (avg_mood / 5) * 30
            factors += 1
        
        # Energy factor (30% weight)
        if avg_energy is not None:
            score += (avg_energy / 5) * 30
            factors += 1
        
        # Teeth brushing factor (15% weight)
        if teeth_brushing_rate > 0:
            score += (teeth_brushing_rate / 100) * 15
            factors += 1
        
        return score if factors > 0 else 0.0
    
    def _generate_insights(self, breakfast_rate: float, avg_mood: Optional[float], 
                          avg_energy: Optional[float], teeth_brushing_rate: float,
                          mood_trend: str, energy_trend: str) -> List[str]:
        """Generate insights from analyzed data"""
        insights = []
        
        # Breakfast insights
        if breakfast_rate >= 80:
            insights.append("excellent breakfast habits")
        elif breakfast_rate >= 60:
            insights.append("good breakfast consistency")
        elif breakfast_rate <= 30:
            insights.append("room for improvement in breakfast habits")
        
        # Mood insights
        if avg_mood is not None:
            if avg_mood >= 4:
                insights.append("generally positive mood")
            elif avg_mood <= 2:
                insights.append("challenging mood patterns")
            
            if mood_trend == "improving":
                insights.append("mood is trending upward")
            elif mood_trend == "declining":
                insights.append("mood is trending downward")
        
        # Energy insights
        if avg_energy is not None:
            if avg_energy >= 4:
                insights.append("good energy levels")
            elif avg_energy <= 2:
                insights.append("low energy patterns")
            
            if energy_trend == "improving":
                insights.append("energy is trending upward")
            elif energy_trend == "declining":
                insights.append("energy is trending downward")
        
        # Teeth brushing insights
        if teeth_brushing_rate >= 90:
            insights.append("excellent dental hygiene")
        elif teeth_brushing_rate <= 50:
            insights.append("room for improvement in dental hygiene")
        
        return insights
    
    @handle_errors("creating context prompt", default_return="")
    def create_context_prompt(self, context_data: ContextData, analysis: ContextAnalysis = None) -> str:
        """
        Create a context prompt string for AI interactions
        
        Args:
            context_data: User context data
            analysis: Optional pre-computed analysis
            
        Returns:
            Formatted context prompt string
        """
        try:
            logger.debug("Creating context prompt for AI interaction")
            
            if analysis is None:
                analysis = self.analyze_context(context_data)
            
            context_parts = []
            
            # User profile information
            profile = context_data.user_profile
            if profile.get('preferred_name'):
                context_parts.append(f"User's name: {profile['preferred_name']}")
                logger.debug(f"Added user name to context: {profile['preferred_name']}")
            if profile.get('active_categories'):
                context_parts.append(f"Interests: {', '.join(profile['active_categories'])}")
                logger.debug(f"Added user interests to context: {profile['active_categories']}")
            
            # Neurodivergent-specific context
            user_context = context_data.user_context
            if user_context:
                # Health conditions
                health_conditions = user_context.get('custom_fields', {}).get('health_conditions', [])
                if health_conditions:
                    context_parts.append(f"Health conditions: {', '.join(health_conditions)}")
                    logger.debug(f"Added health conditions to context: {health_conditions}")
                
                # User's notes for AI
                notes_for_ai = user_context.get('notes_for_ai', [])
                if notes_for_ai:
                    context_parts.append(f"User notes for AI: {'; '.join(notes_for_ai)}")
                    logger.debug(f"Added user notes to context: {len(notes_for_ai)} notes")
                
                # Encouraging activities
                encouraging_activities = user_context.get('activities_for_encouragement', [])
                if encouraging_activities:
                    context_parts.append(f"Encouraging activities: {', '.join(encouraging_activities)}")
                    logger.debug(f"Added encouraging activities to context: {encouraging_activities}")
                
                # Goals
                goals = user_context.get('goals', [])
                if goals:
                    context_parts.append(f"User goals: {', '.join(goals)}")
                    logger.debug(f"Added user goals to context: {goals}")
            
            # Recent check-in analysis
            if context_data.recent_checkins:
                total_entries = len(context_data.recent_checkins)
                context_parts.append(f"Recent check-in data (last {total_entries} entries):")
                context_parts.append(f"- Breakfast eaten: {analysis.breakfast_rate:.0f}% of the time")
                if analysis.avg_mood:
                    context_parts.append(f"- Average mood: {analysis.avg_mood:.1f}/5 ({analysis.mood_trend})")
                if analysis.avg_energy:
                    context_parts.append(f"- Average energy: {analysis.avg_energy:.1f}/5 ({analysis.energy_trend})")
                context_parts.append(f"- Teeth brushed: {analysis.teeth_brushing_rate:.0f}% of the time")
                context_parts.append(f"- Overall wellness score: {analysis.overall_wellness_score:.1f}/100")
                
                # Add insights
                if analysis.insights:
                    context_parts.append(f"Key insights: {', '.join(analysis.insights)}")
                
                logger.debug(f"Added check-in analysis to context: {total_entries} entries, wellness_score={analysis.overall_wellness_score:.1f}")
            
            context_prompt = "\n".join(context_parts)
            logger.debug(f"Context prompt created successfully: {len(context_prompt)} characters, {len(context_parts)} sections")
            
            return context_prompt
            
        except Exception as e:
            logger.error(f"Error creating context prompt: {e}")
            return ""
    
    @handle_errors("creating task-specific context", default_return="")
    def create_task_context(self, user_id: str, task_description: str) -> str:
        """
        Create context specifically for task-related interactions
        
        Args:
            user_id: User ID
            task_description: Description of the task
            
        Returns:
            Task-specific context string
        """
        try:
            context_data = self.build_user_context(user_id, include_conversation_history=False)
            analysis = self.analyze_context(context_data)
            
            # Get user's task-related preferences
            user_context = context_data.user_context
            task_preferences = []
            
            if user_context:
                # Preferred task times
                preferred_times = user_context.get('preferred_task_times', [])
                if preferred_times:
                    task_preferences.append(f"prefers tasks at: {', '.join(preferred_times)}")
                
                # Task completion patterns
                task_patterns = user_context.get('task_completion_patterns', [])
                if task_patterns:
                    task_preferences.append(f"task patterns: {', '.join(task_patterns)}")
            
            # Build task-specific context
            context_parts = [
                f"Task: {task_description}",
                self.create_context_prompt(context_data, analysis)
            ]
            
            if task_preferences:
                context_parts.append(f"Task preferences: {'; '.join(task_preferences)}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error creating task context: {e}")
            return f"Task: {task_description}"
    
    @handle_errors("creating checkin context", default_return="")
    def create_checkin_context(self, user_id: str, checkin_type: str = "daily") -> str:
        """
        Create context specifically for check-in interactions
        
        Args:
            user_id: User ID
            checkin_type: Type of check-in (daily, weekly, etc.)
            
        Returns:
            Check-in specific context string
        """
        try:
            context_data = self.build_user_context(user_id, include_conversation_history=False)
            analysis = self.analyze_context(context_data)
            
            # Build check-in specific context
            context_parts = [
                f"Check-in Type: {checkin_type}",
                self.create_context_prompt(context_data, analysis)
            ]
            
            # Add check-in specific insights
            if analysis.insights:
                context_parts.append(f"Areas to focus on: {', '.join(analysis.insights)}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error creating checkin context: {e}")
            return f"Check-in Type: {checkin_type}"

# Global context builder instance
_context_builder = None

def get_context_builder() -> ContextBuilder:
    """Get the global context builder instance"""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
