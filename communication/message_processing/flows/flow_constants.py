# communication/message_processing/flows/flow_constants.py

"""Flow and check-in state constants for conversation flows."""

# We'll define 'flow' constants
FLOW_NONE = 0
FLOW_CHECKIN = 1
FLOW_TASK_REMINDER = 2
FLOW_NOTE_BODY = 3
FLOW_LIST_ITEMS = 4
FLOW_TASK_DUE_DATE = 5
FLOW_TASK_PRIORITY = 6
FLOW_JOURNAL_BODY = 7


# We'll define states for check-in - now dynamic based on user preferences
CHECKIN_START = 100
CHECKIN_MOOD = 101
CHECKIN_BREAKFAST = 102
CHECKIN_ENERGY = 103
CHECKIN_TEETH = 104
CHECKIN_SLEEP_QUALITY = 105
CHECKIN_SLEEP_SCHEDULE = 106
CHECKIN_ANXIETY = 107
CHECKIN_FOCUS = 108
CHECKIN_MEDICATION = 109
CHECKIN_EXERCISE = 110
CHECKIN_HYDRATION = 111
CHECKIN_SOCIAL = 112
CHECKIN_STRESS = 113
CHECKIN_REFLECTION = 114
CHECKIN_HOPELESSNESS = 115
CHECKIN_IRRITABILITY = 116
CHECKIN_MOTIVATION = 117
CHECKIN_TREATMENT = 118
CHECKIN_COMPLETE = 200

# Idle expiry threshold for check-in flows (2 hours)
CHECKIN_INACTIVITY_MINUTES = 120
# Post-flow cooldown to delay scheduled automations after flow completion
POST_FLOW_COOLDOWN_MINUTES = 10
# Idle expiry for multi-step create flows (tasks, notes, lists, future events)
CONVERSATION_FLOW_TIMEOUT_MINUTES = 10

# Discord/channel suggestion buttons for task creation follow-ups
FLOW_CONTROL_SKIP_LABELS = frozenset(
    {"Skip", "Skip Question", "Skip All", "End List"}
)
FLOW_UNDO_BUTTON_PREFIX = "Undo "

# Default daytime window for day-based task reminders (date-only due dates)
TASK_REMINDER_DAY_WINDOW_START_HOUR = 9
TASK_REMINDER_DAY_WINDOW_END_HOUR = 17

TASK_DUE_DATE_SUGGESTIONS = ["Skip Question", "Skip All", "Undo Task Creation"]
TASK_PRIORITY_SUGGESTIONS = [
    "Low",
    "Medium",
    "High",
    "Critical",
    "Skip Question",
    "Skip All",
    "Undo Task Creation",
]
NOTEBOOK_BODY_SUGGESTIONS = ["Skip Question", "Undo Note Creation"]
JOURNAL_BODY_SUGGESTIONS = ["Skip Question", "Undo Entry Creation"]
LIST_ITEMS_SUGGESTIONS = ["End List", "Undo List Creation"]

# Question mapping for dynamic flow
QUESTION_STATES = {
    "mood": CHECKIN_MOOD,
    "ate_breakfast": CHECKIN_BREAKFAST,
    "energy": CHECKIN_ENERGY,
    "brushed_teeth": CHECKIN_TEETH,
    "sleep_quality": CHECKIN_SLEEP_QUALITY,
    "sleep_schedule": CHECKIN_SLEEP_SCHEDULE,
    "anxiety_level": CHECKIN_ANXIETY,
    "focus_level": CHECKIN_FOCUS,
    "medication_taken": CHECKIN_MEDICATION,
    "exercise": CHECKIN_EXERCISE,
    "hydration": CHECKIN_HYDRATION,
    "social_interaction": CHECKIN_SOCIAL,
    "stress_level": CHECKIN_STRESS,
    "daily_reflection": CHECKIN_REFLECTION,
    "hopelessness_level": CHECKIN_HOPELESSNESS,
    "irritability_level": CHECKIN_IRRITABILITY,
    "motivation_level": CHECKIN_MOTIVATION,
    "treatment_adherence": CHECKIN_TREATMENT,
}
