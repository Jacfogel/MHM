﻿# telegram_bot.py

import threading
import time
import requests
import telegram
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, filters
import os
import json
import core.scheduler
from core.logger import get_logger
from core.config import TELEGRAM_BOT_TOKEN
from user.user_context import UserContext
import uuid
from threading import Lock
from typing import List, Dict, Any
import warnings
from telegram.warnings import PTBUserWarning
from core.service_utilities import wait_for_network, title_case
from core.user_management import get_user_id_by_chat_id
from core.schedule_management import get_schedule_time_periods, add_schedule_period
from core.message_management import add_message
from core.validation import InvalidTimeFormatError
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

# Import the new base classes
from bot.base_channel import BaseChannel, ChannelType, ChannelStatus, ChannelConfig

logger = get_logger(__name__)

# NEW: Additional states for daily check-in
CHECKIN_MOOD, CHECKIN_BREAKFAST, CHECKIN_ENERGY, CHECKIN_TEETH = range(100, 104)  # Using large distinct enum

# Define conversation states for adding messages and editing schedules
CATEGORY, MESSAGE, DAYS, TIME_PERIODS, VIEW_EDIT_SCHEDULE, EDIT_PERIOD = range(6)

# Keep original exception classes for backward compatibility
class TelegramBotError(Exception):
    """Custom exception for Telegram bot-related errors."""
    pass

class TelegramBot(BaseChannel):  # Now extends BaseChannel
    def __init__(self, config: ChannelConfig = None):
        # Suppress PTB warnings about ConversationHandler settings
        warnings.filterwarnings("ignore", category=PTBUserWarning)
        
        # Initialize BaseChannel
        if config is None:
            config = ChannelConfig(
                name='telegram',
                max_retries=5,
                retry_delay=2.0,
                backoff_multiplier=2.0
            )
        super().__init__(config)
        
        # Keep existing attributes
        self.application = None
        self.selected_days = {}
        self.selected_time_periods = {}
        self.screaming = False
        self.telegram_thread = None
        self._lock = Lock()

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.ASYNC

    @handle_errors("running Telegram polling")
    def run_polling(self):
        """Run Telegram polling safely in a separate thread with an event loop."""
        logger.info("Starting Telegram polling in a background thread...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.application.run_polling())

    @handle_errors("initializing Telegram bot", default_return=False)
    async def initialize(self) -> bool:
        """Initialize the Telegram bot - replaces the old start() method"""
        self._set_status(ChannelStatus.INITIALIZING)
        
        if not wait_for_network():
            error_msg = "Network not available after wake-up. Please check your connection."
            self._set_status(ChannelStatus.ERROR, error_msg)
            return False

        backoff_time = self.config.retry_delay
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug("Initializing Telegram Application")
                self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

                logger.debug("Registering command handlers")
                await self._register_handlers()

                # Test the connection
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                await bot.get_me()

                with self._lock:
                    self._set_status(ChannelStatus.READY)
                
                # Start polling in background thread - FIXED: Ensure run_polling exists
                if hasattr(self, 'run_polling'):
                    self.telegram_thread = threading.Thread(target=self.run_polling, daemon=True)
                    self.telegram_thread.start()
                else:
                    logger.error("run_polling method not found!")
                    return False
                
                logger.info("Telegram bot initialized successfully.")
                return True
                
            except telegram.error.NetworkError as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(backoff_time)
                    backoff_time *= self.config.backoff_multiplier
                    
            except telegram.error.InvalidToken as e:
                error_msg = f"Invalid Telegram bot token: {e}"
                self._set_status(ChannelStatus.ERROR, error_msg)
                return False
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(backoff_time)
                    backoff_time *= self.config.backoff_multiplier

        error_msg = f"Failed to initialize after {self.config.max_retries} attempts"
        self._set_status(ChannelStatus.ERROR, error_msg)
        return False

    @handle_errors("registering handlers")
    async def _register_handlers(self):
        """Register all command and conversation handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("scream", self.scream_command))
        self.application.add_handler(CommandHandler("whisper", self.whisper_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("send", self.send_command))

        self.application.add_handler(self.add_message_conv_handler())
        self.application.add_handler(self.schedule_conv_handler())
        self.application.add_handler(self.daily_checkin_conv_handler())

    @handle_errors("shutting down Telegram bot", default_return=False)
    async def shutdown(self) -> bool:
        """Shutdown the Telegram bot"""
        if self.application:
            # Stop the application first, then shutdown
            if self.application.running:
                await self.application.stop()
            await self.application.shutdown()
        self._set_status(ChannelStatus.STOPPED)
        logger.info("Telegram bot shutdown successfully")
        return True

    @handle_errors("sending Telegram message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send a message via Telegram - conforms to BaseChannel interface"""
        if not self.is_ready():
            logger.error("Telegram bot is not ready to send messages")
            return False

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        parse_mode = kwargs.get('parse_mode', ParseMode.MARKDOWN)
        
        await bot.send_message(
            chat_id=recipient, 
            text=message, 
            parse_mode=parse_mode
        )
        
        logger.info(f"Message sent to chat_id: {recipient}")
        return True

    @handle_errors("receiving Telegram messages", default_return=[])
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from Telegram"""
        # For Telegram, this is handled via webhooks/polling in the background
        # Return empty list as messages are processed via handlers
        return []

    @handle_errors("performing Telegram health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform health check on Telegram bot"""
        if not self.application:
            return False
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.get_me()
        return True

    # Legacy method for backward compatibility
    @handle_errors("starting Telegram bot")
    def start(self):
        """Legacy start method - calls the new async initialize"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.initialize())
        if not success:
            raise TelegramBotError("Failed to initialize Telegram bot")
        return success

    # Legacy method for backward compatibility  
    @handle_errors("stopping Telegram bot")
    def stop(self):
        """Legacy stop method - calls the new async shutdown"""
        if asyncio.get_event_loop().is_running():
            # If we're in an async context, schedule the shutdown
            asyncio.create_task(self.shutdown())
        else:
            # If not in async context, run it
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.shutdown())

    def is_initialized(self):
        """Legacy method for backward compatibility"""
        return self.is_ready()

    @handle_errors("handling start command")
    async def start_command(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        logger.info(f"Received /start command from chat ID: {chat_id}")
        await update.message.reply_text('Hello! I am your personal assistant bot.')

    @handle_errors("handling help command")
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        logger.info("Received /help command")
        if not self.ensure_user_exists(update):
            return
        
        user_context = UserContext()
        preferred_name = user_context.get_preferred_name()

        help_text = (
            f"Hello {preferred_name},\n"
            "Here are the available commands:\n"
            "/help - Show this help message\n"
            "/scream - Make the bot scream\n"
            "/whisper - Make the bot whisper\n"
            "/menu - Show the menu\n"
            "/send - Send a message from the specified category\n"
        )
        await update.message.reply_text(help_text)

    @handle_errors("handling scream command")
    def scream_command(self, update: Update, context: CallbackContext) -> None:
        self.screaming = True
        logger.info("Received /scream command")
        self.ensure_user_exists(update)

    @handle_errors("handling whisper command")
    def whisper_command(self, update: Update, context: CallbackContext) -> None:
        self.screaming = False
        logger.info("Received /whisper command")
        self.ensure_user_exists(update)

    @handle_errors("handling menu command")
    async def menu_command(self, update: Update, context: CallbackContext) -> None:
        logger.info("Received /menu command")
        self.ensure_user_exists(update)

        buttons = [
            [InlineKeyboardButton("✉️ View Recent Messages by Category", callback_data="view_recent_message_categories")],
            [InlineKeyboardButton("➕ Add Message", callback_data='add_message')],
            [InlineKeyboardButton("📤 Send Message", callback_data='send')],
            [InlineKeyboardButton("🗓️ View/Edit Schedule", callback_data='view_edit_schedule')],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await update.message.reply_text("Please choose an option:", reply_markup=reply_markup)

    @handle_errors("handling send command")
    async def send_command(self, update: Update, context: CallbackContext) -> None:
        if not self.ensure_user_exists(update):
            return

        user_id = UserContext().get_user_id()
        category = context.user_data.get('category', 'default')
        message_data = "This is a test message."
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

        success = await self.send_message(str(chat_id), message_data)
        if success:
            await update.message.reply_text("Message sent successfully.")
        else:
            await update.message.reply_text("Failed to send message.")

    @handle_errors("canceling operation")
    def cancel(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Operation canceled.')
        return ConversationHandler.END

    @handle_errors("adding message command")
    def add_message_command(self, update: Update, context: CallbackContext) -> int:
        self.ensure_user_exists(update)
        return self.prompt_category_selection(update, context, 'add_message')

    @handle_errors("prompting category selection")
    def prompt_category_selection(self, update: Update, context: CallbackContext, action: str, prompt_message: str = "Please choose a category:", is_message: bool = False) -> int:
        """Prompt user to select a category"""
        self.ensure_user_exists(update)
        context.user_data['action'] = action
        context.user_data['category_prompt'] = True

        user_id = UserContext().get_user_id()
        # Get user categories
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', []) or []

        buttons = [[InlineKeyboardButton(title_case(category), callback_data=f'category_{category}')] for category in categories]
        reply_markup = InlineKeyboardMarkup(buttons)

        if is_message:
            update.message.reply_text(prompt_message, reply_markup=reply_markup)
        else:
            update.callback_query.message.reply_text(prompt_message, reply_markup=reply_markup)
        return CATEGORY

    @handle_errors("handling category selection")
    def handle_category_selection(self, update: Update, context: CallbackContext) -> int:
        """Handle category selection"""
        self.ensure_user_exists(update)
        query = update.callback_query
        category = query.data.split('_')[1].strip().lower()
        context.user_data['category'] = category
        return self.prompt_for_message(update, context, category)

    @handle_errors("prompting for message")
    def prompt_for_message(self, update: Update, context: CallbackContext, category: str) -> int:
        """Prompt user to enter a message"""
        self.ensure_user_exists(update)
        update.callback_query.message.reply_text("Please enter the message you want to add:")
        return MESSAGE

    @handle_errors("handling message received")
    def message_received(self, update: Update, context: CallbackContext) -> int:
        """Handle received message text"""
        self.ensure_user_exists(update)
        message = update.message.text.strip()
        context.user_data['new_message'] = message
        # Continue with days selection...
        update.message.reply_text("Message received. (Days selection not implemented yet)")
        return ConversationHandler.END

    @handle_errors("getting base days keyboard")
    def get_base_days_keyboard(self) -> InlineKeyboardMarkup:
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        buttons = [[InlineKeyboardButton(day, callback_data=day)] for day in days_of_week]
        buttons.append([InlineKeyboardButton('Submit', callback_data='submit_days')])
        return InlineKeyboardMarkup(buttons)

    @handle_errors("prompting for days")
    def prompt_for_days(self, update: Update, context: CallbackContext) -> int:
        reply_markup = self.get_base_days_keyboard()
        update.message.reply_text("Please select the days for the message:", reply_markup=reply_markup)
        return DAYS

    @handle_errors("handling days selection")
    def days_selected(self, update: Update, context: CallbackContext) -> int:
        """Handle days selection"""
        # Implementation needed
        update.callback_query.message.reply_text("Days selection not implemented yet")
        return ConversationHandler.END

    @handle_errors("prompting for time periods")
    def prompt_for_time_periods(self, update: Update, context: CallbackContext) -> int:
        user_id = UserContext().get_user_id()
        selected_periods = self.selected_time_periods.get(user_id, [])
        category = context.user_data.get('category')
        available_periods = get_schedule_time_periods(user_id, category)

        period_buttons = [
            [InlineKeyboardButton(f"{'✔️ ' if period in selected_periods else ''}{title_case(period)}", callback_data=period)]
            for period in available_periods.keys()
        ]
        period_buttons.append([InlineKeyboardButton('Submit', callback_data='submit_time_periods')])

        reply_markup = InlineKeyboardMarkup(period_buttons)
        update.callback_query.message.reply_text("Please select the time periods for the message:", reply_markup=reply_markup)
        return TIME_PERIODS

    @handle_errors("handling time periods selection")
    def time_periods_selected(self, update: Update, context: CallbackContext) -> int:
        """Handle time periods selection"""
        # Implementation needed
        update.callback_query.message.reply_text("Time periods selection not implemented yet")
        return ConversationHandler.END

    @handle_errors("updating time periods keyboard")
    def update_time_periods_keyboard(self, update: Update, context: CallbackContext, selected: list) -> None:
        user_id = UserContext().get_user_id()  
        category = context.user_data.get('category')
        available_periods = get_schedule_time_periods(user_id, category)

        period_buttons = [
            [InlineKeyboardButton(f"{'✔️ ' if period in selected else ''}{title_case(period)}", callback_data=period)]
            for period in available_periods.keys()
        ]
        period_buttons.append([InlineKeyboardButton('Submit', callback_data='submit_time_periods')])

        reply_markup = InlineKeyboardMarkup(period_buttons)
        update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    @handle_errors("saving new message")
    def save_new_message(self, update: Update, context: CallbackContext) -> None:
        self.ensure_user_exists(update)
        user_id = UserContext().get_user_id()
        category = context.user_data['category']
        new_message = context.user_data['new_message']
        selected_days_list = self.selected_days.get(user_id, [])
        selected_time_periods_list = self.selected_time_periods.get(user_id, [])

        if not selected_days_list or not selected_time_periods_list:
            update.message.reply_text("No days or time periods selected. Please select at least one day and one time period.")
            return

        message_data = {
            "message_id": str(uuid.uuid4()),
            "message": new_message,
            "days": selected_days_list,
            "time_periods": selected_time_periods_list
        }

        add_message(user_id, category, message_data)
        update.message.reply_text("Message added successfully.")
        self.selected_days[user_id] = []
        self.selected_time_periods[user_id] = []

    @handle_errors("viewing/editing schedule command")
    def view_edit_schedule_command(self, update: Update, context: CallbackContext) -> int:
        """View/edit schedule command"""
        # Implementation needed
        update.callback_query.message.reply_text("Schedule editing not implemented yet")
        return ConversationHandler.END

    @handle_errors("handling schedule category selection")
    def handle_schedule_category_selection(self, update: Update, context: CallbackContext) -> int:
        """Handle schedule category selection"""
        # Implementation needed
        return ConversationHandler.END

    @handle_errors("showing schedule")
    def show_schedule(self, update: Update, context: CallbackContext, category: str) -> int:
        user_id = UserContext().get_user_id()
        schedule_data = get_schedule_time_periods(user_id, category)
        
        if not schedule_data:
            update.callback_query.message.reply_text(f"No schedule times data available for {title_case(category)}.")
            return ConversationHandler.END

        buttons = [
            [InlineKeyboardButton(f"{title_case(period)}: {times['start_time']} - {times['end_time']}", callback_data=f"edit_period_{period}")]
            for period, times in schedule_data.items()
        ]
        buttons.append([InlineKeyboardButton("➕ Add New Period", callback_data="add_period")])
        buttons.append([InlineKeyboardButton("🔙 Return to Menu", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        update.callback_query.message.reply_text("Please choose a time period to edit or add a new one:", reply_markup=reply_markup)
        
        return VIEW_EDIT_SCHEDULE

    @handle_errors("handling period selection")
    def handle_period_selection(self, update: Update, context: CallbackContext) -> int:
        """Handle period selection"""
        # Implementation needed
        return ConversationHandler.END

    @handle_errors("editing schedule period")
    def edit_schedule_period(self, update: Update, context: CallbackContext) -> int:
        """Edit schedule period"""
        # Implementation needed
        update.message.reply_text("Schedule period editing not implemented yet")
        return ConversationHandler.END

    @handle_errors("adding new period")
    def add_new_period(self, update: Update, context: CallbackContext) -> int:
        category = context.user_data['category']
        period_name = context.user_data['new_period_name']
        start_time = context.user_data['new_period_start_time']
        end_time = update.message.text.strip()

        try:
            add_schedule_period(category, period_name, start_time, end_time)
            update.message.reply_text(f"New period '{period_name}' added successfully.")
            return self.show_schedule(update, context, category)
        except InvalidTimeFormatError:
            update.message.reply_text("Invalid time format. Please use HH:MM format (e.g., 09:00).")
            return EDIT_PERIOD
        except Exception as e:
            update.message.reply_text(f"Error adding new period for category {title_case(category)}. Please try again.")
            return VIEW_EDIT_SCHEDULE

    @handle_errors("creating add message conversation handler")
    def add_message_conv_handler(self):
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_message_command, pattern='^add_message$')],
            states={
                CATEGORY: [CallbackQueryHandler(self.handle_category_selection, pattern='^category_')],
                MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_received)],
                DAYS: [CallbackQueryHandler(self.days_selected, pattern='^.*$')],
                TIME_PERIODS: [CallbackQueryHandler(self.time_periods_selected, pattern='^.*$')]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False,  # Set to False because we have mixed handler types
            per_chat=True,
            per_user=False,
            allow_reentry=True
        )
        return conv_handler

    @handle_errors("creating schedule conversation handler")
    def schedule_conv_handler(self):
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.view_edit_schedule_command, pattern='^view_edit_schedule$')],
            states={
                CATEGORY: [CallbackQueryHandler(self.handle_schedule_category_selection, pattern='^category_')],
                VIEW_EDIT_SCHEDULE: [CallbackQueryHandler(self.handle_period_selection, pattern='^.*$')],
                EDIT_PERIOD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.edit_schedule_period),
                    CallbackQueryHandler(self.handle_period_selection, pattern='^.*$')
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False,  # Set to False because we have mixed handler types
            per_chat=True,
            per_user=False,
            allow_reentry=True
        )
        return conv_handler

    # -------------------------------------------------------------------------------------------
    # NEW: Daily Check-In Flow
    @handle_errors("creating daily checkin conversation handler")
    def daily_checkin_conv_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler("dailycheckin", self.start_daily_checkin),
                          CallbackQueryHandler(self.start_daily_checkin, pattern='^daily_checkin$')],
            states={
                CHECKIN_MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.capture_mood)],
                CHECKIN_BREAKFAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.capture_breakfast)],
                CHECKIN_ENERGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.capture_energy)],
                CHECKIN_TEETH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.capture_teeth)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_checkin)],
            per_user=True,
            per_chat=False,  # Use per_user instead of per_chat for user-specific flows
            per_message=False,
            allow_reentry=False
        )

    @handle_errors("starting daily checkin")
    async def start_daily_checkin(self, update: Update, context: CallbackContext):
        """Start daily check-in"""
        if not self.ensure_user_exists(update):
            return ConversationHandler.END

        await update.message.reply_text(
            "How are you feeling today on a scale of 1 to 5? (1 = terrible, 5 = wonderful)\n"
            "Type /cancel at any time to quit."
        )
        return CHECKIN_MOOD

    @handle_errors("capturing mood")
    async def capture_mood(self, update: Update, context: CallbackContext):
        """Capture mood"""
        # Implementation needed
        await update.message.reply_text("Mood captured (not fully implemented)")
        return ConversationHandler.END

    @handle_errors("capturing breakfast")
    async def capture_breakfast(self, update: Update, context: CallbackContext):
        """Capture breakfast"""
        # Implementation needed
        return ConversationHandler.END

    @handle_errors("capturing energy")
    async def capture_energy(self, update: Update, context: CallbackContext):
        """Capture energy"""
        # Implementation needed
        return ConversationHandler.END

    @handle_errors("capturing teeth")
    async def capture_teeth(self, update: Update, context: CallbackContext):
        """Capture teeth"""
        # Implementation needed
        return ConversationHandler.END

    @handle_errors("canceling checkin")
    async def cancel_checkin(self, update: Update, context: CallbackContext):
        """Cancel check-in"""
        await update.message.reply_text("Daily check-in canceled.")
        return ConversationHandler.END

    @handle_errors("ensuring user exists", default_return=False)
    def ensure_user_exists(self, update: Update) -> bool:
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        telegram_username = update.message.from_user.username if update.message else update.callback_query.from_user.username
        user_context = UserContext()

        user_id = get_user_id_by_chat_id(chat_id)
        if user_id:
            # Get user context
            context_result = get_user_data(user_id, 'context')
            user_context_data = context_result.get('context')
            user_context.set_user_id(user_id)
            user_context.set_internal_username(user_context_data.get('internal_username') if user_context_data else '')
            user_context.set_preferred_name(user_context_data.get('preferred_name') if user_context_data else '')
            return True

        new_user_id = str(uuid.uuid4())
        # Create new user using the new structure
        from core.user_management import create_new_user
        user_data = {
            "user_id": new_user_id,
            "internal_username": telegram_username,
            "preferred_name": telegram_username,
            "chat_id": chat_id
        }
        create_new_user(user_data)
        user_context.set_user_id(new_user_id)
        user_context.set_internal_username(telegram_username)
        user_context.set_preferred_name(telegram_username)
        return True

    def get_user_categories(self, user_id: str) -> List[str]:
        """Get user's message categories."""
        try:
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            if categories is None:
                return []
            elif isinstance(categories, list):
                return categories
            elif isinstance(categories, dict):
                return list(categories.keys())
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {e}")
            return []

    def handle_user_command(self, update, context):
        """Handle /user command to show user information."""
        try:
            user_id = UserContext().get_user_id()
            if not user_id:
                update.message.reply_text("No user context found.")
                return
            
            # Get user data using new functions
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account')
            prefs_result = get_user_data(user_id, 'preferences')
            user_preferences = prefs_result.get('preferences')
            # Get user context
            context_result = get_user_data(user_id, 'context')
            user_context_data = context_result.get('context')
            
            if not user_account:
                update.message.reply_text("User account not found.")
                return
            
            # Build user info message
            username = user_account.get('internal_username', 'Unknown')
            preferred_name = user_context_data.get('preferred_name', '') if user_context_data else ''
            categories = prefs_result.get('preferences', {}).get('categories', []) or []
            messaging_service = user_preferences.get('channel', {}).get('type', 'Unknown') if user_preferences else 'Unknown'
            
            message = f"User: {username}"
            if preferred_name:
                message += f" ({preferred_name})"
            message += f"\nService: {messaging_service}"
            message += f"\nCategories: {', '.join(categories) if categories else 'None'}"
            
            update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error handling /user command: {e}")
            update.message.reply_text("Error retrieving user information.")

    def get_user_categories_for_telegram(self, user_id: str) -> List[str]:
        """Get user's message categories for Telegram bot."""
        try:
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            if categories is None:
                return []
            elif isinstance(categories, list):
                return categories
            elif isinstance(categories, dict):
                return list(categories.keys())
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {e}")
            return []

# Initialize the bot instance
telegram_bot = TelegramBot()

# Running the bot

@handle_errors("running Telegram bot in background")
def run_telegram_bot_in_background():
    telegram_bot.start()
