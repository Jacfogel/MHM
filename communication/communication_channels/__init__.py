"""Communication channels package.

Contains concrete channel implementations (Discord, Email) and base
channel infrastructure for the communication subsystem.
"""

# Main public API - package-level exports for easier refactoring
# Note: BaseChannel classes are exported from parent communication package
# Discord and Email bots may have circular dependencies, so they're lazy imports

# Discord channel - lazy import to avoid circular dependencies
# Use: from communication.communication_channels import DiscordBot (imported on-demand)
# Note: DiscordBot has circular dependencies, so it's imported lazily

# Email channel - lazy import to avoid circular dependencies
# Use: from communication.communication_channels import EmailBot (imported on-demand)
# Note: EmailBot has circular dependencies, so it's imported lazily

__all__ = [
    # BaseChannel, ChannelStatus, ChannelType, ChannelConfig are exported from parent
]
