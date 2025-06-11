from bot.channel_factory import ChannelFactory
# from bot.telegram_bot import TelegramBot  # Deactivated
from bot.email_bot import EmailBot
from bot.discord_bot import DiscordBot

def register_all_channels():
    """Register all available communication channels"""
    # ChannelFactory.register_channel('telegram', TelegramBot)  # Deactivated
    ChannelFactory.register_channel('email', EmailBot)
    ChannelFactory.register_channel('discord', DiscordBot)
    print("Communication channels registered successfully (Telegram deactivated)") 