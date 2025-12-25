"""
Command Registry Tests

Tests for communication/communication_channels/base/command_registry.py:
- CommandDefinition dataclass
- CommandRegistry abstract base class
- DiscordCommandRegistry
- EmailCommandRegistry
- Factory function
"""

import pytest
from unittest.mock import patch, MagicMock

from communication.communication_channels.base.command_registry import (
    CommandDefinition,
    CommandRegistry,
    DiscordCommandRegistry,
    EmailCommandRegistry,
    get_command_registry
)
import discord


class TestCommandDefinition:
    """Test CommandDefinition dataclass"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_definition_initialization(self):
        """Test: CommandDefinition initializes correctly"""
        # Arrange
        def handler():
            pass
        
        # Act
        cmd_def = CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler
        )
        
        # Assert
        assert cmd_def.name == "test_command", "Should set name"
        assert cmd_def.description == "Test command", "Should set description"
        assert cmd_def.handler == handler, "Should set handler"
        assert cmd_def.aliases == [], "Should default aliases to empty list"
        assert cmd_def.permissions == [], "Should default permissions to empty list"
        assert cmd_def.cooldown == 0.0, "Should default cooldown to 0.0"
        assert cmd_def.enabled is True, "Should default enabled to True"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_definition_with_all_fields(self):
        """Test: CommandDefinition initializes with all fields"""
        # Arrange
        def handler():
            pass
        
        # Act
        cmd_def = CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler,
            aliases=["test", "t"],
            permissions=["admin"],
            cooldown=5.0,
            enabled=False
        )
        
        # Assert
        assert cmd_def.aliases == ["test", "t"], "Should set aliases"
        assert cmd_def.permissions == ["admin"], "Should set permissions"
        assert cmd_def.cooldown == 5.0, "Should set cooldown"
        assert cmd_def.enabled is False, "Should set enabled"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_definition_post_init_with_none_aliases(self):
        """Test: CommandDefinition __post_init__ handles None aliases"""
        # Arrange
        def handler():
            pass
        
        # Act
        cmd_def = CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler,
            aliases=None
        )
        
        # Assert
        assert cmd_def.aliases == [], "Should convert None aliases to empty list"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_definition_post_init_with_none_permissions(self):
        """Test: CommandDefinition __post_init__ handles None permissions"""
        # Arrange
        def handler():
            pass
        
        # Act
        cmd_def = CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler,
            permissions=None
        )
        
        # Assert
        assert cmd_def.permissions == [], "Should convert None permissions to empty list"


class TestCommandRegistry:
    """Test CommandRegistry abstract base class"""
    
    @pytest.fixture
    def concrete_registry(self):
        """Create a concrete implementation of CommandRegistry for testing"""
        class TestCommandRegistry(CommandRegistry):
            def register_with_platform(self, command_def: CommandDefinition) -> bool:
                return True
            
            def unregister_from_platform(self, command_name: str) -> bool:
                return True
        
        return TestCommandRegistry()
    
    @pytest.fixture
    def command_def(self):
        """Create a test command definition"""
        def handler():
            pass
        
        return CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler,
            aliases=["test", "t"]
        )
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization(self, concrete_registry):
        """Test: CommandRegistry initializes correctly"""
        # Assert
        assert concrete_registry._commands == {}, "Should initialize commands dict"
        assert concrete_registry._aliases == {}, "Should initialize aliases dict"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_command_success(self, concrete_registry, command_def):
        """Test: register_command registers command successfully"""
        # Act
        result = concrete_registry.register_command(command_def)
        
        # Assert
        assert result is True, "Should return True on success"
        assert "test_command" in concrete_registry._commands, "Should register main command"
        assert concrete_registry._commands["test_command"] == command_def, "Should store command definition"
        assert "test" in concrete_registry._aliases, "Should register alias"
        assert concrete_registry._aliases["test"] == "test_command", "Should map alias to command"
        assert "t" in concrete_registry._aliases, "Should register second alias"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_command_without_aliases(self, concrete_registry):
        """Test: register_command works without aliases"""
        # Arrange
        def handler():
            pass
        command_def = CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler
        )
        
        # Act
        result = concrete_registry.register_command(command_def)
        
        # Assert
        assert result is True, "Should return True on success"
        assert "test_command" in concrete_registry._commands, "Should register command"
        assert len(concrete_registry._aliases) == 0, "Should not register aliases"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_command_overwrites_alias(self, concrete_registry):
        """Test: register_command overwrites existing alias"""
        # Arrange
        def handler1():
            pass
        def handler2():
            pass
        
        cmd1 = CommandDefinition(
            name="command1",
            description="First command",
            handler=handler1,
            aliases=["alias"]
        )
        cmd2 = CommandDefinition(
            name="command2",
            description="Second command",
            handler=handler2,
            aliases=["alias"]
        )
        
        # Act
        concrete_registry.register_command(cmd1)
        result = concrete_registry.register_command(cmd2)
        
        # Assert
        assert result is True, "Should return True on success"
        assert concrete_registry._aliases["alias"] == "command2", "Should overwrite alias"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_command_success(self, concrete_registry, command_def):
        """Test: unregister_command removes command successfully"""
        # Arrange
        concrete_registry.register_command(command_def)
        
        # Act
        result = concrete_registry.unregister_command("test_command")
        
        # Assert
        assert result is True, "Should return True on success"
        assert "test_command" not in concrete_registry._commands, "Should remove command"
        assert "test" not in concrete_registry._aliases, "Should remove aliases"
        assert "t" not in concrete_registry._aliases, "Should remove second alias"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_command_not_found(self, concrete_registry):
        """Test: unregister_command returns False when command not found"""
        # Act
        result = concrete_registry.unregister_command("nonexistent")
        
        # Assert
        assert result is False, "Should return False when command not found"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_by_name(self, concrete_registry, command_def):
        """Test: get_command returns command by name"""
        # Arrange
        concrete_registry.register_command(command_def)
        
        # Act
        result = concrete_registry.get_command("test_command")
        
        # Assert
        assert result == command_def, "Should return command definition"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_by_alias(self, concrete_registry, command_def):
        """Test: get_command returns command by alias"""
        # Arrange
        concrete_registry.register_command(command_def)
        
        # Act
        result = concrete_registry.get_command("test")
        
        # Assert
        assert result == command_def, "Should return command definition via alias"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_not_found(self, concrete_registry):
        """Test: get_command returns None when command not found"""
        # Act
        result = concrete_registry.get_command("nonexistent")
        
        # Assert
        assert result is None, "Should return None when command not found"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_all_commands(self, concrete_registry):
        """Test: get_all_commands returns all registered commands"""
        # Arrange
        def handler1():
            pass
        def handler2():
            pass
        
        cmd1 = CommandDefinition("cmd1", "First", handler1)
        cmd2 = CommandDefinition("cmd2", "Second", handler2)
        concrete_registry.register_command(cmd1)
        concrete_registry.register_command(cmd2)
        
        # Act
        result = concrete_registry.get_all_commands()
        
        # Assert
        assert len(result) == 2, "Should return all commands"
        assert cmd1 in result, "Should include first command"
        assert cmd2 in result, "Should include second command"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_enabled_commands(self, concrete_registry):
        """Test: get_enabled_commands returns only enabled commands"""
        # Arrange
        def handler1():
            pass
        def handler2():
            pass
        
        cmd1 = CommandDefinition("cmd1", "First", handler1, enabled=True)
        cmd2 = CommandDefinition("cmd2", "Second", handler2, enabled=False)
        concrete_registry.register_command(cmd1)
        concrete_registry.register_command(cmd2)
        
        # Act
        result = concrete_registry.get_enabled_commands()
        
        # Assert
        assert len(result) == 1, "Should return only enabled commands"
        assert cmd1 in result, "Should include enabled command"
        assert cmd2 not in result, "Should exclude disabled command"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_is_command_registered_by_name(self, concrete_registry, command_def):
        """Test: is_command_registered returns True for registered command"""
        # Arrange
        concrete_registry.register_command(command_def)
        
        # Act
        result = concrete_registry.is_command_registered("test_command")
        
        # Assert
        assert result is True, "Should return True for registered command"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_is_command_registered_by_alias(self, concrete_registry, command_def):
        """Test: is_command_registered returns True for registered alias"""
        # Arrange
        concrete_registry.register_command(command_def)
        
        # Act
        result = concrete_registry.is_command_registered("test")
        
        # Assert
        assert result is True, "Should return True for registered alias"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_is_command_registered_not_found(self, concrete_registry):
        """Test: is_command_registered returns False for unregistered command"""
        # Act
        result = concrete_registry.is_command_registered("nonexistent")
        
        # Assert
        assert result is False, "Should return False for unregistered command"


class TestDiscordCommandRegistry:
    """Test DiscordCommandRegistry"""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot"""
        mock_bot = MagicMock()
        mock_bot.tree = MagicMock()
        return mock_bot
    
    @pytest.fixture
    def discord_registry(self, mock_bot):
        """Create a DiscordCommandRegistry instance"""
        return DiscordCommandRegistry(mock_bot)
    
    @pytest.fixture
    def command_def(self):
        """Create a test command definition"""
        async def handler(interaction):
            pass
        
        return CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler
        )
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_with_bot(self, mock_bot):
        """Test: DiscordCommandRegistry initializes with bot"""
        # Act
        registry = DiscordCommandRegistry(mock_bot)
        
        # Assert
        assert registry.bot == mock_bot, "Should set bot"
        assert registry._commands == {}, "Should initialize commands dict"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_without_bot(self):
        """Test: DiscordCommandRegistry initializes without bot"""
        # Act
        registry = DiscordCommandRegistry(None)
        
        # Assert
        assert registry.bot is None, "Should handle None bot"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_with_platform_without_bot(self, command_def):
        """Test: register_with_platform returns False when bot not available"""
        # Arrange
        registry = DiscordCommandRegistry(None)
        
        # Act
        result = registry.register_with_platform(command_def)
        
        # Assert
        assert result is False, "Should return False when bot not available"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_with_platform_success(self, discord_registry, mock_bot, command_def):
        """Test: register_with_platform registers command with Discord"""
        # Arrange
        mock_bot.tree.add_command = MagicMock()
        
        # Mock discord.app_commands.Command to avoid import issues
        with patch('discord.app_commands.Command') as mock_command_class:
            mock_command = MagicMock()
            mock_command_class.return_value = mock_command
            
            # Act
            result = discord_registry.register_with_platform(command_def)
            
            # Assert
            assert result is True, "Should return True on success"
            mock_bot.tree.add_command.assert_called_once()
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_from_platform_without_bot(self, command_def):
        """Test: unregister_from_platform returns False when bot not available"""
        # Arrange
        registry = DiscordCommandRegistry(None)
        
        # Act
        result = registry.unregister_from_platform("test_command")
        
        # Assert
        assert result is False, "Should return False when bot not available"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_from_platform_success(self, discord_registry, mock_bot):
        """Test: unregister_from_platform removes command from Discord"""
        # Arrange
        mock_command = MagicMock()
        mock_bot.tree.get_command.return_value = mock_command
        mock_bot.tree.remove_command = MagicMock()
        
        # Act
        result = discord_registry.unregister_from_platform("test_command")
        
        # Assert
        assert result is True, "Should return True on success"
        mock_bot.tree.remove_command.assert_called_once_with("test_command")
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_from_platform_command_not_found(self, discord_registry, mock_bot):
        """Test: unregister_from_platform returns False when command not found"""
        # Arrange
        mock_bot.tree.get_command.return_value = None
        
        # Act
        result = discord_registry.unregister_from_platform("nonexistent")
        
        # Assert
        assert result is False, "Should return False when command not found"


class TestEmailCommandRegistry:
    """Test EmailCommandRegistry"""
    
    @pytest.fixture
    def email_registry(self):
        """Create an EmailCommandRegistry instance"""
        return EmailCommandRegistry()
    
    @pytest.fixture
    def command_def(self):
        """Create a test command definition"""
        def handler():
            pass
        
        return CommandDefinition(
            name="test_command",
            description="Test command",
            handler=handler
        )
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_with_platform(self, email_registry, command_def):
        """Test: register_with_platform always returns True for email"""
        # Act
        result = email_registry.register_with_platform(command_def)
        
        # Assert
        assert result is True, "Should return True for email commands"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_unregister_from_platform(self, email_registry):
        """Test: unregister_from_platform always returns True for email"""
        # Act
        result = email_registry.unregister_from_platform("test_command")
        
        # Assert
        assert result is True, "Should return True for email commands"


class TestGetCommandRegistry:
    """Test get_command_registry factory function"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_registry_discord(self):
        """Test: get_command_registry returns DiscordCommandRegistry for discord"""
        # Arrange
        mock_bot = MagicMock()
        
        # Act
        result = get_command_registry("discord", mock_bot)
        
        # Assert
        assert isinstance(result, DiscordCommandRegistry), "Should return DiscordCommandRegistry"
        assert result.bot == mock_bot, "Should set bot on registry"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_registry_email(self):
        """Test: get_command_registry returns EmailCommandRegistry for email"""
        # Act
        result = get_command_registry("email")
        
        # Assert
        assert isinstance(result, EmailCommandRegistry), "Should return EmailCommandRegistry"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_command_registry_unknown_fallback(self):
        """Test: get_command_registry returns EmailCommandRegistry for unknown channel"""
        # Act
        result = get_command_registry("unknown")
        
        # Assert
        assert isinstance(result, EmailCommandRegistry), "Should return EmailCommandRegistry as fallback"

