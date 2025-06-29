from bot.channel_factory import ChannelFactory
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
# from bot.telegram_bot import TelegramBot  # Deactivated
from bot.email_bot import EmailBot
from bot.discord_bot import DiscordBot

@handle_errors("registering all channels")
def register_all_channels():
    """Register all available communication channels"""
    # ChannelFactory.register_channel('telegram', TelegramBot)  # Deactivated
    ChannelFactory.register_channel('email', EmailBot)
    ChannelFactory.register_channel('discord', DiscordBot)
    print("Communication channels registered successfully (Telegram deactivated)") 