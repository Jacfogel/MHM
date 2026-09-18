"""Allowlisted self-service settings backed by MHM's existing profile documents."""

import copy
import hashlib
import json
import re
from datetime import date

import pytz

from core.error_handling import ValidationError, handle_errors
from core.profile_v2_io import schedule_categories
from core.schedule_period_normalize import create_default_schedule_periods
from core.time_utilities import now_timestamp_full
from storage.user_data_validation import validate_schedule_periods

PROFILE_LISTS = (
    "pronouns",
    "gender_identity",
    "interests",
    "goals",
    "activities_for_encouragement",
    "notes_for_ai",
)

PROFILE_CUSTOM_LISTS = (
    "health_conditions",
    "medications_treatments",
    "reminders_needed",
    "allergies_sensitivities",
)

PERSONALIZED_CATEGORIES = {
    "personalized_checkin": "checkins",
    "personalized_google_health": "google_health",
    "personalized_profile": None,
}
CUSTOM_QUESTION_TYPES = frozenset(
    {"optional_text", "yes_no", "scale_1_5", "number", "time_pair"}
)
DEFAULT_QUESTION_CATEGORIES = frozenset(
    {"mood", "energy", "health", "activities", "general"}
)


@handle_errors("filtering available website message categories", default_return=[])
def _available_message_categories(options, features):
    """Return categories supported by the user's currently enabled data sources."""
    categories = options.get("categories") or []
    return [
        category
        for category in categories
        if category not in PERSONALIZED_CATEGORIES
        or PERSONALIZED_CATEGORIES[category] is None
        or features.get(PERSONALIZED_CATEGORIES[category]) == "enabled"
    ]


@handle_errors(
    "reading editable custom check-in questions",
    user_friendly=False,
    re_raise=True,
)
def _editable_custom_questions(checkin_settings):
    """Return browser-editable custom question definitions from saved preferences."""
    if not isinstance(checkin_settings, dict):
        raise ValidationError("Saved check-in settings must use the current format.")
    saved_questions = checkin_settings.get("custom_questions", {})
    if not isinstance(saved_questions, dict):
        raise ValidationError("Saved custom questions must use the current format.")
    result = {}
    expected_fields = {
        "type",
        "question_text",
        "ui_display_name",
        "category",
        "validation",
        "enabled",
        "always_include",
        "sometimes_include",
    }
    for key, definition in saved_questions.items():
        if (
            not isinstance(key, str)
            or not re.fullmatch(r"custom_[a-z0-9_]{1,100}", key)
            or not isinstance(definition, dict)
            or set(definition) != expected_fields
            or definition["type"] not in CUSTOM_QUESTION_TYPES
            or not isinstance(definition["question_text"], str)
            or not definition["question_text"].strip()
            or len(definition["question_text"].strip()) > 300
            or not isinstance(definition["ui_display_name"], str)
            or not definition["ui_display_name"].strip()
            or len(definition["ui_display_name"].strip()) > 150
            or not isinstance(definition["category"], str)
            or definition["category"] not in DEFAULT_QUESTION_CATEGORIES
            or not isinstance(definition["validation"], dict)
            or set(definition["validation"])
            - {"min", "max", "error_message"}
            or type(definition["enabled"]) is not bool
            or type(definition["always_include"]) is not bool
            or type(definition["sometimes_include"]) is not bool
            or definition["always_include"]
            and definition["sometimes_include"]
            or definition["enabled"]
            != (
                definition["always_include"]
                or definition["sometimes_include"]
            )
        ):
            raise ValidationError("Saved custom questions must use the current format.")
        validation = definition["validation"]
        if any(
            not isinstance(validation[field], (int, float))
            or isinstance(validation[field], bool)
            for field in ("min", "max")
            if field in validation
        ) or (
            "error_message" in validation
            and not isinstance(validation["error_message"], str)
        ):
            raise ValidationError("Saved custom questions must use the current format.")
        result[key] = {
            "question_text": definition["question_text"].strip(),
            "ui_display_name": definition["ui_display_name"].strip(),
            "type": definition["type"],
            "category": definition["category"].strip(),
            "validation": copy.deepcopy(definition["validation"]),
        }
    return result


@handle_errors("loading website settings options", user_friendly=False, re_raise=True)
def settings_options(user_id):
    """Return the time zones, message categories, and check-in choices for a user."""
    from messages.message_data_manager import get_message_categories
    from checkins.checkin_dynamic_manager import dynamic_checkin_manager

    questions = dynamic_checkin_manager.get_enabled_questions_for_ui(user_id)
    categories = dynamic_checkin_manager.get_categories()
    templates = dynamic_checkin_manager.get_question_templates()
    return {
        "timezones": pytz.all_timezones,
        "categories": get_message_categories(),
        "questions": {
            key: value["ui_display_name"] for key, value in questions.items()
        },
        "question_defaults": {
            key: "sometimes" if value["enabled"] else "off"
            for key, value in questions.items()
        },
        "question_category_map": {
            key: str(value.get("category") or "general")
            for key, value in questions.items()
        },
        "question_categories": categories,
        "question_templates": templates,
    }


@handle_errors("building website settings snapshot", user_friendly=False, re_raise=True)
def settings_snapshot(documents, options):
    """Build browser-safe settings sections and optimistic-lock revisions."""
    account = documents.get("account") or {}
    prefs = documents.get("preferences") or {}
    context = documents.get("context") or {}
    schedules = schedule_categories(copy.deepcopy(documents.get("schedules") or {}))
    features = account.get("features") or {}
    effective_options = copy.deepcopy(options)
    effective_options["categories"] = _available_message_categories(
        options, features
    )
    task = prefs.get("task_settings") or {}
    checkin = prefs.get("checkin_settings") or {}
    custom_questions = _editable_custom_questions(checkin)
    effective_options.setdefault("questions", {})
    effective_options.setdefault("question_defaults", {})
    for key, definition in custom_questions.items():
        effective_options["questions"].setdefault(key, definition["question_text"])
        effective_options["question_defaults"].setdefault(key, "sometimes")
    custom_fields = context.get("custom_fields") or {}

    from core.natural_language_defaults import (
        NaturalLanguageDefaults,
        natural_language_defaults_to_preferences_dict,
    )

    phrase_defaults = natural_language_defaults_to_preferences_dict(
        NaturalLanguageDefaults.from_preferences(
            prefs.get("natural_language_defaults")
        )
    )
    from tasks.task_time_parsing import parse_time_string

    for key in ("tonight_start_time", "after_work_school_time"):
        phrase_defaults[key] = parse_time_string(phrase_defaults[key]) or phrase_defaults[key]
    phrase_defaults["time_of_day_defaults"] = {
        key: parse_time_string(value) or value
        for key, value in phrase_defaults["time_of_day_defaults"].items()
    }

    # ERROR_HANDLING_EXCLUDE: Pure helper protected by settings_snapshot's boundary.
    def periods(category):
        """Return editable named periods for one schedule category."""
        current = schedules.get(category, {}).get("periods")
        return {
            name: value
            for name, value in (
                current or create_default_schedule_periods(category)
            ).items()
            if name != "ALL"
        }

    selected_raw = prefs.get("categories") or []
    selected = [
        category
        for category in selected_raw
        if category in effective_options["categories"]
    ]
    question_states = {}
    for key in effective_options["questions"]:
        question = (checkin.get("questions") or {}).get(key)
        if not question:
            custom = (checkin.get("custom_questions") or {}).get(key)
            if isinstance(custom, dict):
                question = {
                    "always_include": custom.get("enabled", True)
                    and custom.get("always_include", True),
                    "sometimes_include": custom.get("sometimes_include", False),
                }
            else:
                question_states[key] = effective_options.get("question_defaults", {}).get(
                    key, "off"
                )
                continue
        question_states[key] = (
            "always"
            if question.get("always_include")
            else "sometimes" if question.get("sometimes_include") else "off"
        )
    sections = {
        "profile": {
            "preferred_name": context.get("preferred_name", ""),
            "date_of_birth": context.get("date_of_birth", ""),
            **{key: context.get(key) or [] for key in PROFILE_LISTS},
            **{key: custom_fields.get(key) or [] for key in PROFILE_CUSTOM_LISTS},
            "loved_ones": context.get("loved_ones") or [],
        },
        "delivery": {
            "timezone": account.get("timezone", ""),
            "channel": (prefs.get("channel") or {}).get("type", "email"),
        },
        "messages": {
            "enabled": features.get("automated_messages") == "enabled",
            "categories": selected,
            "periods": {category: periods(category) for category in selected},
        },
        "tasks": {
            "enabled": features.get("task_management") == "enabled",
            "periods": periods("tasks"),
            "recurring": {
                "default_recurrence_pattern": (
                    task.get("recurring_settings") or {}
                ).get("default_recurrence_pattern"),
                "default_recurrence_interval": (
                    task.get("recurring_settings") or {}
                ).get("default_recurrence_interval", 1),
                "default_repeat_after_completion": (
                    task.get("recurring_settings") or {}
                ).get("default_repeat_after_completion", True),
            },
        },
        "checkins": {
            "enabled": features.get("checkins") == "enabled",
            "periods": periods("checkin"),
            "questions": question_states,
            "custom_questions": custom_questions,
            "min_questions": checkin.get("min_questions", 1),
            "max_questions": checkin.get("max_questions", 1),
        },
        "phrases": phrase_defaults,
    }
    revisions = {
        key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        for key, value in sections.items()
    }
    available_message_periods = {
        category: periods(category) for category in effective_options["categories"]
    }
    revisions["messages"] = hashlib.sha256(
        json.dumps(
            {
                "section": sections["messages"],
                "available_periods": available_message_periods,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return {
        "sections": sections,
        "revisions": revisions,
        "options": effective_options,
        "available_message_periods": available_message_periods,
        "discord_linked": bool(account.get("discord_user_id")),
    }


@handle_errors("validating website settings updates", user_friendly=False, re_raise=True)
def build_settings_updates(documents, options, section, values):
    """Validate all input before producing updates; preserve unrelated saved fields."""
    snapshot = settings_snapshot(documents, options)
    current = snapshot["sections"]
    if (
        not isinstance(section, str)
        or section not in current
        or not isinstance(values, dict)
        or set(values) != set(current[section])
    ):
        raise ValidationError("Please submit only the fields in this settings section.")
    account = copy.deepcopy(documents.get("account") or {})
    prefs = copy.deepcopy(documents.get("preferences") or {})
    context = copy.deepcopy(documents.get("context") or {})
    schedules = schedule_categories(copy.deepcopy(documents.get("schedules") or {}))

    # ERROR_HANDLING_EXCLUDE: Validation helper protected by the decorated caller.
    def flag(key):
        """Apply a validated website feature flag to the account document."""
        if type(values["enabled"]) is not bool:
            raise ValidationError("Choose whether this feature is enabled.")
        account.setdefault("features", {})[key] = (
            "enabled" if values["enabled"] else "disabled"
        )

    # ERROR_HANDLING_EXCLUDE: Validation helper protected by the decorated caller.
    def save_periods(category, periods):
        """Validate and stage named reminder windows for one category."""
        if not isinstance(periods, dict) or len(periods) > 20:
            raise ValidationError("Use at most 20 reminder windows per category.")
        for name, period in periods.items():
            if (
                not isinstance(name, str)
                or not name.strip()
                or len(name) > 80
                or name.upper() == "ALL"
            ):
                raise ValidationError(
                    "Give each reminder window a unique name other than ALL."
                )
            if not isinstance(period, dict) or set(period) != {
                "active",
                "days",
                "start_time",
                "end_time",
            }:
                raise ValidationError(
                    "Each reminder window needs a start time, end time, days, and enabled state."
                )
            if type(period["active"]) is not bool or not isinstance(
                period["days"], list
            ):
                raise ValidationError(
                    "Check the days and enabled state for each reminder window."
                )
            if any(
                not isinstance(period[key], str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", period[key])
                for key in ("start_time", "end_time")
            ):
                raise ValidationError(
                    "Use valid start and end times for each reminder window."
                )
            if period["start_time"] >= period["end_time"]:
                raise ValidationError("Each reminder window must start before it ends.")
            days = period["days"]
            if (
                any(
                    not isinstance(day, str)
                    or day
                    not in (
                        "ALL",
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    )
                    for day in days
                )
                or len(set(days)) != len(days)
                or ("ALL" in days and len(days) != 1)
                or (period["active"] and not days)
            ):
                raise ValidationError("Choose valid days for each enabled reminder window.")
        if periods:
            valid, errors = validate_schedule_periods(periods, category)
            # The admin console permits all windows to be disabled when a feature is off.
            if not valid and (
                values["enabled"]
                or errors
                != [f"At least one time period must be enabled for {category}."]
            ):
                raise ValidationError(errors[0])
        elif values["enabled"]:
            raise ValidationError(
                "Add at least one enabled reminder window before enabling this feature."
            )
        old_all = schedules.get(category, {}).get("periods", {}).get("ALL")
        schedules[category] = {
            **schedules.get(category, {}),
            "periods": {
                "ALL": old_all or create_default_schedule_periods(category)["ALL"],
                **periods,
            },
        }

    if section == "profile":
        name = values["preferred_name"]
        if not isinstance(name, str) or len(name) > 100:
            raise ValidationError("Use a preferred name of at most 100 characters.")
        date_of_birth = values["date_of_birth"]
        if not isinstance(date_of_birth, str):
            raise ValidationError("Use a valid date of birth.")
        if date_of_birth:
            try:
                parsed_birth_date = date.fromisoformat(date_of_birth)
            except ValueError:
                raise ValidationError("Use a valid date of birth.") from None
            if parsed_birth_date > date.today():
                raise ValidationError("Date of birth cannot be in the future.")
        for key in (*PROFILE_LISTS, *PROFILE_CUSTOM_LISTS):
            items = values[key]
            limit = 1000 if key == "notes_for_ai" else 200
            if (
                not isinstance(items, list)
                or len(items) > 30
                or any(not isinstance(item, str) or len(item) > limit for item in items)
            ):
                raise ValidationError(
                    "Use at most 30 entries in each profile list and keep entries brief."
                )
        loved_ones = values["loved_ones"]
        if not isinstance(loved_ones, list) or len(loved_ones) > 30:
            raise ValidationError("Add at most 30 people to your support network.")
        for person in loved_ones:
            if (
                not isinstance(person, dict)
                or set(person) != {"name", "type", "relationships"}
                or not isinstance(person["name"], str)
                or not person["name"].strip()
                or len(person["name"].strip()) > 100
                or not isinstance(person["type"], str)
                or len(person["type"].strip()) > 100
                or not isinstance(person["relationships"], list)
                or len(person["relationships"]) > 20
                or any(
                    not isinstance(relationship, str)
                    or not relationship.strip()
                    or len(relationship.strip()) > 100
                    for relationship in person["relationships"]
                )
            ):
                raise ValidationError(
                    "Each support person needs a name and valid relationship details."
                )
        context.update({key: values[key] for key in PROFILE_LISTS})
        context["preferred_name"] = name.strip()
        context["date_of_birth"] = date_of_birth
        context["loved_ones"] = [
            {
                "name": person["name"].strip(),
                "type": person["type"].strip(),
                "relationships": [
                    relationship.strip() for relationship in person["relationships"]
                ],
            }
            for person in loved_ones
        ]
        custom_fields = copy.deepcopy(context.get("custom_fields") or {})
        for key in PROFILE_CUSTOM_LISTS:
            if values[key] or key in custom_fields:
                custom_fields[key] = values[key]
        context["custom_fields"] = custom_fields
        context["last_updated"] = now_timestamp_full()
        return {"context": context}
    if section == "delivery":
        if (
            not isinstance(values["timezone"], str)
            or values["timezone"] not in options["timezones"]
        ):
            raise ValidationError("Choose a valid time zone.")
        channel = values["channel"]
        if (
            not isinstance(channel, str)
            or channel not in {"email", "discord"}
            or (channel == "discord" and not account.get("discord_user_id"))
        ):
            raise ValidationError(
                "Link your Discord account before selecting Discord delivery."
            )
        account["timezone"] = values["timezone"]
        account["chat_id"] = (
            account.get("discord_user_id")
            if channel == "discord"
            else account.get("email")
        )
        prefs["channel"] = {"type": channel}
        return {"account": account, "preferences": prefs}
    if section == "messages":
        categories = values["categories"]
        available_categories = snapshot["options"]["categories"]
        if (
            not isinstance(categories, list)
            or any(
                not isinstance(c, str) or c not in available_categories
                for c in categories
            )
            or len(set(categories)) != len(categories)
        ):
            raise ValidationError("Choose from the available message categories.")
        if values["enabled"] and not categories:
            raise ValidationError(
                "Choose at least one message category before enabling messages."
            )
        if not isinstance(values["periods"], dict) or set(values["periods"]) != set(
            categories
        ):
            raise ValidationError("Provide reminder windows for each selected category.")
        flag("automated_messages")
        for category in categories:
            save_periods(category, values["periods"][category])
        prefs["categories"] = categories
    elif section == "tasks":
        recurring = values["recurring"]
        if not isinstance(recurring, dict) or set(recurring) != set(
            current["tasks"]["recurring"]
        ):
            raise ValidationError("Check your recurring task defaults.")
        if (
            recurring["default_recurrence_pattern"]
            not in (None, "daily", "weekly", "monthly", "yearly")
            or type(recurring["default_recurrence_interval"]) is not int
            or not 1 <= recurring["default_recurrence_interval"] <= 365
            or type(recurring["default_repeat_after_completion"]) is not bool
        ):
            raise ValidationError(
                "Choose a recurrence pattern and an interval between 1 and 365."
            )
        flag("task_management")
        save_periods("tasks", values["periods"])
        task = prefs.get("task_settings") or {}
        task["recurring_settings"] = {
            **(task.get("recurring_settings") or {}),
            **recurring,
        }
        prefs["task_settings"] = task
    elif section == "checkins":
        checkin = prefs.get("checkin_settings") or {}
        custom_questions = values["custom_questions"]
        if not isinstance(custom_questions, dict) or len(custom_questions) > 20:
            raise ValidationError("Add at most 20 custom check-in questions.")
        for key, definition in custom_questions.items():
            allowed_categories = set(
                snapshot["options"].get("question_categories") or {}
            ) | {"general"}
            if not allowed_categories:
                allowed_categories = set(DEFAULT_QUESTION_CATEGORIES)
            if (
                not isinstance(key, str)
                or not re.fullmatch(r"custom_[a-z0-9_]{1,100}", key)
                or not isinstance(definition, dict)
                or set(definition)
                != {
                    "question_text",
                    "ui_display_name",
                    "type",
                    "category",
                    "validation",
                }
                or not isinstance(definition["question_text"], str)
                or not definition["question_text"].strip()
                or len(definition["question_text"].strip()) > 300
                or not isinstance(definition["ui_display_name"], str)
                or not definition["ui_display_name"].strip()
                or len(definition["ui_display_name"].strip()) > 150
                or definition["type"] not in CUSTOM_QUESTION_TYPES
                or definition["category"] not in allowed_categories
                or not isinstance(definition["validation"], dict)
                or set(definition["validation"])
                - {"min", "max", "error_message"}
            ):
                raise ValidationError("Check each custom question and answer type.")
            validation = definition["validation"]
            for bound in ("min", "max"):
                if bound in validation and (
                    not isinstance(validation[bound], (int, float))
                    or isinstance(validation[bound], bool)
                    or not -1000000 <= validation[bound] <= 1000000
                ):
                    raise ValidationError("Use valid numeric question limits.")
            if (
                "min" in validation
                and "max" in validation
                and validation["min"] >= validation["max"]
            ):
                raise ValidationError(
                    "A numeric question's minimum must be below its maximum."
                )
            error_message = validation.get("error_message", "")
            if not isinstance(error_message, str) or len(error_message) > 300:
                raise ValidationError("Keep question validation messages brief.")
        states = values["questions"]
        existing_custom = _editable_custom_questions(checkin)
        predefined_questions = set(snapshot["options"]["questions"]) - set(
            existing_custom
        )
        expected_questions = predefined_questions | set(custom_questions)
        if (
            not isinstance(states, dict)
            or set(states) != expected_questions
            or any(
                not isinstance(state, str)
                or state not in {"off", "always", "sometimes"}
                for state in states.values()
            )
        ):
            raise ValidationError(
                "Choose how often to include each available check-in question."
            )
        minimum, maximum = values["min_questions"], values["max_questions"]
        if (
            type(minimum) is not int
            or type(maximum) is not int
            or not 1 <= minimum <= maximum <= 100
        ):
            raise ValidationError(
                "Question counts must be between 1 and 100, with minimum no greater than maximum."
            )
        always = list(states.values()).count("always")
        sometimes = list(states.values()).count("sometimes")
        if values["enabled"] and (
            minimum < max(always, 1)
            or maximum < max(always + bool(sometimes), 1)
            or maximum > always + sometimes - bool(sometimes)
        ):
            raise ValidationError(
                "Question counts must include all Always questions and leave room to vary Sometimes questions."
            )
        flag("checkins")
        save_periods("checkin", values["periods"])
        questions = copy.deepcopy(checkin.get("questions") or {})
        for removed_key in set(existing_custom) - set(custom_questions):
            questions.pop(removed_key, None)
        checkin["custom_questions"] = {
            key: {
                "question_text": definition["question_text"].strip(),
                "ui_display_name": definition["ui_display_name"].strip(),
                "type": definition["type"],
                "category": definition["category"],
                "enabled": states[key] != "off",
                "always_include": states[key] == "always",
                "sometimes_include": states[key] == "sometimes",
                "validation": copy.deepcopy(definition["validation"]),
            }
            for key, definition in custom_questions.items()
        }
        for key, state in states.items():
            label = snapshot["options"]["questions"].get(key)
            if not label:
                label = custom_questions[key]["question_text"]
            questions[key] = {
                **questions.get(key, {}),
                "label": label,
                "enabled": state != "off",
                "always_include": state == "always",
                "sometimes_include": state == "sometimes",
            }
        checkin.update(
            {"questions": questions, "min_questions": minimum, "max_questions": maximum}
        )
        prefs["checkin_settings"] = checkin
    elif section == "phrases":
        time_fields = (
            "tonight_start_time",
            "after_work_school_time",
        )
        time_of_day = values["time_of_day_defaults"]
        if not isinstance(time_of_day, dict) or set(time_of_day) != {
            "morning",
            "afternoon",
            "evening",
            "night",
        }:
            raise ValidationError("Check the morning, afternoon, evening, and night times.")
        all_times = [values[key] for key in time_fields] + list(time_of_day.values())
        if any(
            not isinstance(value, str)
            or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value)
            for value in all_times
        ):
            raise ValidationError("Use valid times for each phrase setting.")
        weekend = values["weekend_this_week_means_coming_week"]
        if type(weekend) is not bool:
            raise ValidationError("Choose how MHM should interpret ‘this week’ on weekends.")
        prefs["natural_language_defaults"] = copy.deepcopy(values)
        return {"preferences": prefs}
    return {"account": account, "preferences": prefs, "schedules": schedules}


@handle_errors("saving website settings", user_friendly=False, default_return=False)
def save_settings(user_id, updates):
    """Persist validated settings and refresh dependent caches and defaults."""
    from core import save_user_data_transaction
    from core.schedule_runtime import clear_schedule_periods_cache
    from messages.message_data_manager import ensure_user_message_files

    if not save_user_data_transaction(user_id, updates, auto_create=False):
        return False
    clear_schedule_periods_cache(user_id)
    if (
        updates.get("account", {}).get("features", {}).get("task_management")
        == "enabled"
    ):
        from tasks import setup_default_task_tags

        if not setup_default_task_tags(user_id):
            return False
    if "categories" in updates.get("preferences", {}):
        categories = updates["preferences"]["categories"]
        if categories and not ensure_user_message_files(user_id, categories).get(
            "success"
        ):
            return False
    return True
