# command_registry.py

from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route command registry logs to communication component
registry_logger = get_component_logger("command_registry")
logger = registry_logger


@dataclass
class CommandDefinition:
    """Definition of a command that can be registered"""

    name: str
    description: str
    handler: Callable
    aliases: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    cooldown: float = 0.0
    enabled: bool = True

    @handle_errors("post-initializing command definition")
    def __post_init__(self):
        """Post-initialization setup"""
        if self.aliases is None:
            self.aliases = []
        if self.permissions is None:
            self.permissions = []


class CommandRegistry(ABC):
    """Abstract base class for command registration utilities"""

    @handle_errors("initializing command registry", default_return=None)
    def __init__(self):
        """Initialize the command registry"""
        self._commands: Dict[str, CommandDefinition] = {}
        self._aliases: Dict[str, str] = {}

    @handle_errors("registering command", default_return=False)
    def register_command(self, command_def: CommandDefinition) -> bool:
        """Register a command definition"""
        try:
            # Register main command
            self._commands[command_def.name] = command_def

            # Register aliases
            if command_def.aliases:
                for alias in command_def.aliases:
                    if alias in self._aliases:
                        logger.warning(
                            f"Alias '{alias}' already registered for '{self._aliases[alias]}', overwriting with '{command_def.name}'"
                        )
                    self._aliases[alias] = command_def.name

            logger.debug(
                f"Registered command '{command_def.name}' with {len(command_def.aliases or [])} aliases"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register command '{command_def.name}': {e}")
            return False

    @handle_errors("unregistering command")
    def unregister_command(self, command_name: str) -> bool:
        """Unregister a command"""
        try:
            if command_name not in self._commands:
                return False

            command_def = self._commands[command_name]

            # Remove aliases
            aliases_to_remove = [
                alias for alias, cmd in self._aliases.items() if cmd == command_name
            ]
            for alias in aliases_to_remove:
                del self._aliases[alias]

            # Remove main command
            del self._commands[command_name]

            logger.debug(f"Unregistered command '{command_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister command '{command_name}': {e}")
            return False

    @handle_errors("getting command")
    def get_command(self, command_name: str) -> Optional[CommandDefinition]:
        """Get a command by name or alias"""
        # Check main commands first
        if command_name in self._commands:
            return self._commands[command_name]

        # Check aliases
        if command_name in self._aliases:
            return self._commands[self._aliases[command_name]]

        return None

    @handle_errors("getting all commands")
    def get_all_commands(self) -> List[CommandDefinition]:
        """Get all registered commands"""
        return list(self._commands.values())

    @handle_errors("getting enabled commands")
    def get_enabled_commands(self) -> List[CommandDefinition]:
        """Get all enabled commands"""
        return [cmd for cmd in self._commands.values() if cmd.enabled]

    @handle_errors("checking if command is registered")
    def is_command_registered(self, command_name: str) -> bool:
        """Check if a command is registered"""
        return command_name in self._commands or command_name in self._aliases

    @abstractmethod
    @handle_errors("registering with platform", default_return=False)
    def register_with_platform(self, command_def: CommandDefinition) -> bool:
        """Register command with the specific platform (Discord, etc.)"""
        pass

    @abstractmethod
    @handle_errors("unregistering from platform", default_return=False)
    def unregister_from_platform(self, command_name: str) -> bool:
        """Unregister command from the specific platform"""
        pass


class DiscordCommandRegistry(CommandRegistry):
    """Discord-specific command registry"""

    @handle_errors("initializing Discord command registry")
    def __init__(self, bot=None):
        """Initialize Discord command registry"""
        super().__init__()
        self.bot = bot

    @handle_errors("registering with Discord platform", default_return=False)
    def register_with_platform(self, command_def: CommandDefinition) -> bool:
        """Register command with Discord"""
        if not self.bot:
            logger.warning("Discord bot not available for command registration")
            return False

        # Create Discord command callback
        @handle_errors(
            "handling Discord command",
            context={"command": command_def.name},
            default_return=None,
        )
        async def discord_command_callback(interaction, *args, **kwargs):
            # Call the original handler
            result = await command_def.handler(interaction, *args, **kwargs)
            return result

        # Register as Discord slash command
        from discord import app_commands

        app_cmd = app_commands.Command(
            name=command_def.name,
            description=command_def.description,
            callback=discord_command_callback,
        )
        self.bot.tree.add_command(app_cmd)

        logger.debug(f"Registered Discord command '{command_def.name}'")
        return True

    @handle_errors("unregistering from Discord platform", default_return=False)
    def unregister_from_platform(self, command_name: str) -> bool:
        """Unregister command from Discord"""
        if not self.bot:
            return False

        # Remove from Discord command tree
        command = self.bot.tree.get_command(command_name)
        if command:
            self.bot.tree.remove_command(command_name)
            logger.debug(f"Unregistered Discord command '{command_name}'")
            return True

        return False


class EmailCommandRegistry(CommandRegistry):
    """Email-specific command registry"""

    @handle_errors("registering with email platform")
    def register_with_platform(self, command_def: CommandDefinition) -> bool:
        """Register command with email system"""
        # Email commands are typically handled through message parsing
        # rather than explicit registration, so this is mostly a placeholder
        logger.debug(f"Email command '{command_def.name}' available for parsing")
        return True

    @handle_errors("unregistering from email platform")
    def unregister_from_platform(self, command_name: str) -> bool:
        """Unregister command from email system"""
        # Email commands are handled through parsing, so unregistration
        # just removes from the registry
        logger.debug(f"Email command '{command_name}' removed from registry")
        return True


# Factory function to get appropriate command registry
@handle_errors("getting command registry")
def get_command_registry(channel_type: str, platform_instance=None) -> CommandRegistry:
    """Get the appropriate command registry for a channel type"""
    if channel_type == "discord":
        return DiscordCommandRegistry(platform_instance)
    elif channel_type == "email":
        return EmailCommandRegistry()
    else:
        # Return email registry as fallback for unknown channels
        # (EmailCommandRegistry is concrete, CommandRegistry is abstract)
        return EmailCommandRegistry()
