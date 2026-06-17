# communication/message_processing/command_registry.py

"""Canonical slash/bang command definitions for channel-agnostic routing."""

from dataclasses import dataclass

from core.error_handling import handle_errors


@dataclass
class CommandDefinition:
    """
    Canonical command definition.

    - name: The slash/bang command name without prefix (e.g. "tasks")
    - mapped_message: The internal message text to feed the parser/handlers (e.g. "show my tasks")
        - Use None for "discoverability-only" commands (no mapping/translation)
    - description: Human-facing help text
    - is_flow: Whether this command should invoke a flow starter directly
    """

    name: str
    description: str
    mapped_message: str | None = None
    is_flow: bool = False

    @handle_errors("getting mapped message", default_return="!unknown")
    def get_mapped_message(self) -> str:
        """Get the mapped message, defaulting to !{name} if not specified."""
        if self.mapped_message is not None:
            return self.mapped_message
        return f"!{self.name}"


@handle_errors("building command definitions", default_return=[])
def build_command_definitions() -> list[CommandDefinition]:
    """Build complete command definitions with base commands and analytics aliases."""
    command_definitions = build_base_command_definitions()
    command_definitions.extend(build_analytics_alias_commands())
    return command_definitions


@handle_errors("building base command definitions", default_return=[])
def build_base_command_definitions() -> list[CommandDefinition]:
    """Return channel-agnostic base commands."""
    return [
        CommandDefinition("start", "Get started with MHM", mapped_message="start"),
        CommandDefinition("help", "Show help and examples", mapped_message="help"),
        CommandDefinition("status", "Show system/user status", mapped_message="status"),
        CommandDefinition("tasks", "Show your tasks", mapped_message="show my tasks"),
        CommandDefinition("profile", "Show your profile", mapped_message="show profile"),
        CommandDefinition("schedule", "Show your schedules", mapped_message="show schedule"),
        CommandDefinition("messages", "Show your messages", mapped_message="show messages"),
        CommandDefinition(
            "analytics", "Show wellness analytics", mapped_message="show analytics"
        ),
        CommandDefinition(
            "checkin",
            "Start a check-in",
            mapped_message="start checkin",
            is_flow=True,
        ),
        CommandDefinition(
            "restart",
            "Restart check-in",
            mapped_message="restart checkin",
            is_flow=True,
        ),
        CommandDefinition(
            "clear",
            "Clear stuck conversation flows",
            mapped_message="clear flows",
            is_flow=True,
        ),
        CommandDefinition("cancel", "Cancel current flow", mapped_message="cancel"),
        CommandDefinition("n", "Create a note", mapped_message=None),
        CommandDefinition("note", "Create a note", mapped_message=None),
        CommandDefinition("task", "Create a task", mapped_message=None),
        CommandDefinition("l", "Create or manage a list", mapped_message=None),
        CommandDefinition("list", "Create a list", mapped_message=None),
        CommandDefinition("show", "Show an entry by ID or title", mapped_message=None),
        CommandDefinition("recent", "Show recent entries", mapped_message=None),
        CommandDefinition("r", "Show recent entries", mapped_message=None),
        CommandDefinition("pinned", "Show pinned entries", mapped_message=None),
        CommandDefinition("inbox", "Show inbox entries", mapped_message=None),
        CommandDefinition("recentn", "Show recent notes", mapped_message=None),
        CommandDefinition("rnote", "Show recent notes", mapped_message=None),
        CommandDefinition("append", "Append text to an entry", mapped_message=None),
        CommandDefinition("add", "Add text to an entry", mapped_message=None),
        CommandDefinition("addto", "Add text to an entry", mapped_message=None),
        CommandDefinition("tag", "Add tags or view entries by tag", mapped_message=None),
        CommandDefinition("untag", "Remove tags from an entry", mapped_message=None),
        CommandDefinition("t", "Show entries by tag", mapped_message=None),
        CommandDefinition("group", "Set or view entries by group", mapped_message=None),
        CommandDefinition("search", "Search entries", mapped_message=None),
        CommandDefinition("s", "Search entries", mapped_message=None),
        CommandDefinition("pin", "Pin an entry", mapped_message=None),
        CommandDefinition("unpin", "Unpin an entry", mapped_message=None),
        CommandDefinition("archive", "Archive an entry", mapped_message=None),
        CommandDefinition("unarchive", "Unarchive an entry", mapped_message=None),
        CommandDefinition("complete", "Complete a task", mapped_message=None),
        CommandDefinition("uncomplete", "Uncomplete a task", mapped_message=None),
    ]


# devtools: ignore[facade-shims]: analytics aliases are intentional command vocabulary
@handle_errors("building analytics alias command definitions", default_return=[])
def build_analytics_alias_commands() -> list[CommandDefinition]:
    """Return analytics command aliases mapped to canonical prompts."""
    analytics_aliases = [
        ("show-analytics", "Show check-in analytics", "show analytics"),
        ("showanalytics", "Show check-in analytics", "show analytics"),
        ("show-trends", "Show check-in analytics", "show analytics"),
        ("showtrends", "Show check-in analytics", "show analytics"),
        ("checkin-trends", "Show check-in trends", "checkin trends"),
        ("checkintrends", "Show check-in trends", "checkin trends"),
        ("checkin-analysis", "Show check-in analysis", "checkin analysis"),
        ("checkinanalysis", "Show check-in analysis", "checkin analysis"),
        ("checkin-history", "Show check-in history", "checkin history"),
        ("checkinhistory", "Show check-in history", "checkin history"),
        ("show-checkin-trends", "Show check-in trends", "checkin trends"),
        ("showcheckintrends", "Show check-in trends", "checkin trends"),
        ("show-checkin-analysis", "Show check-in analysis", "checkin analysis"),
        ("showcheckinanalysis", "Show check-in analysis", "checkin analysis"),
        ("show-checkin-history", "Show check-in history", "checkin history"),
        ("showcheckinhistory", "Show check-in history", "checkin history"),
        ("habit-analysis", "Show habit analysis", "habit analysis"),
        ("habitanalysis", "Show habit analysis", "habit analysis"),
        ("habit-trends", "Show habit trends", "habit trends"),
        ("habittrends", "Show habit trends", "habit trends"),
        ("habit-history", "Show habit history", "habit history"),
        ("habithistory", "Show habit history", "habit history"),
        ("show-habit-analysis", "Show habit analysis", "habit analysis"),
        ("showhabitanalysis", "Show habit analysis", "habit analysis"),
        ("show-habit-trends", "Show habit trends", "habit trends"),
        ("showhabittrends", "Show habit trends", "habit trends"),
        ("show-habit-history", "Show habit history", "habit history"),
        ("showhabithistory", "Show habit history", "habit history"),
        ("sleep-analysis", "Show sleep analysis", "sleep analysis"),
        ("sleepanalysis", "Show sleep analysis", "sleep analysis"),
        ("sleep-trends", "Show sleep trends", "sleep trends"),
        ("sleeptrends", "Show sleep trends", "sleep trends"),
        ("sleep-history", "Show sleep history", "sleep history"),
        ("sleephistory", "Show sleep history", "sleep history"),
        ("show-sleep-analysis", "Show sleep analysis", "sleep analysis"),
        ("showsleepanalysis", "Show sleep analysis", "sleep analysis"),
        ("show-sleep-trends", "Show sleep trends", "sleep trends"),
        ("showsleeptrends", "Show sleep trends", "sleep trends"),
        ("show-sleep-history", "Show sleep history", "sleep history"),
        ("showsleephistory", "Show sleep history", "sleep history"),
        ("energy-trends", "Show energy trends", "energy trends"),
        ("energytrends", "Show energy trends", "energy trends"),
        ("energy-analysis", "Show energy analysis", "energy analysis"),
        ("energyanalysis", "Show energy analysis", "energy analysis"),
        ("energy-history", "Show energy history", "energy history"),
        ("energyhistory", "Show energy history", "energy history"),
        ("energy-graphs", "Show energy graphs", "energy graphs"),
        ("energygraphs", "Show energy graphs", "energy graphs"),
        ("show-energy-trends", "Show energy trends", "energy trends"),
        ("showenergytrends", "Show energy trends", "energy trends"),
        ("show-energy-analysis", "Show energy analysis", "energy analysis"),
        ("showenergyanalysis", "Show energy analysis", "energy analysis"),
        ("show-energy-history", "Show energy history", "energy history"),
        ("showenergyhistory", "Show energy history", "energy history"),
        ("show-energy-graphs", "Show energy graphs", "energy graphs"),
        ("showenergygraphs", "Show energy graphs", "energy graphs"),
        ("mood-trends", "Show mood trends", "mood trends"),
        ("moodtrends", "Show mood trends", "mood trends"),
        ("mood-analysis", "Show mood analysis", "mood analysis"),
        ("moodanalysis", "Show mood analysis", "mood analysis"),
        ("mood-history", "Show mood history", "mood history"),
        ("moodhistory", "Show mood history", "mood history"),
        ("mood-graphs", "Show mood graphs", "mood graphs"),
        ("moodgraphs", "Show mood graphs", "mood graphs"),
        ("show-mood-trends", "Show mood trends", "mood trends"),
        ("showmoodtrends", "Show mood trends", "mood trends"),
        ("show-mood-analysis", "Show mood analysis", "mood analysis"),
        ("showmoodanalysis", "Show mood analysis", "mood analysis"),
        ("show-mood-history", "Show mood history", "mood history"),
        ("showmoodhistory", "Show mood history", "mood history"),
        ("show-mood-graphs", "Show mood graphs", "mood graphs"),
        ("showmoodgraphs", "Show mood graphs", "mood graphs"),
    ]
    return [
        CommandDefinition(name, description, mapped_message=mapped_message)
        for name, description, mapped_message in analytics_aliases
    ]


@handle_errors("looking up command definition", default_return=None)
def lookup_command_definition(
    command_definitions: list[CommandDefinition], cmd_name: str
) -> CommandDefinition | None:
    """Find a command definition by name."""
    return next((c for c in command_definitions if c.name == cmd_name), None)


@handle_errors("building slash command map", default_return={})
def build_slash_command_map(command_definitions: list[CommandDefinition]) -> dict[str, str]:
    """Return dict like {'tasks': 'show my tasks', ...} for Discord registration."""
    return {c.name: c.get_mapped_message() for c in command_definitions}


@handle_errors("building command definition dicts", default_return=[])
def command_definitions_as_dicts(
    command_definitions: list[CommandDefinition],
) -> list[dict[str, str]]:
    """Return canonical command definitions as dicts for channel registration."""
    return [
        {
            "name": c.name,
            "mapped_message": c.get_mapped_message(),
            "description": c.description,
        }
        for c in command_definitions
    ]
