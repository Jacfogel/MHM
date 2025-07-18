# account_manager.py - User account content and settings management

import tkinter as tk
from tkinter import messagebox, Toplevel, Button, Entry, Checkbutton, IntVar, Frame, font, ttk, Label
import uuid
from datetime import datetime
import re
from tkcalendar import DateEntry, Calendar
import json
import os
from tkinter import simpledialog

from core.file_operations import load_json_data, save_json_data, determine_file_path, get_user_file_path, get_user_data_dir
from core.user_management import update_user_preferences, get_user_data
from core.file_operations import create_user_files
from core.message_management import edit_message, add_message, delete_message, get_message_categories, update_message
from core.schedule_management import (
    get_schedule_time_periods, delete_schedule_period, set_schedule_period_active,
    edit_schedule_period, add_schedule_period, clear_schedule_periods_cache,
    get_schedule_days, set_schedule_days, set_schedule_periods, validate_and_format_time
)
from core.validation import title_case
from core.service_utilities import InvalidTimeFormatError
from core.logger import get_logger
from user.user_context import UserContext
from core.checkin_analytics import checkin_analytics
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
from tasks.task_management import (
    load_active_tasks, save_active_tasks, load_completed_tasks, save_completed_tasks,
    create_task, update_task, complete_task, delete_task, get_task_by_id,
    get_tasks_due_soon, get_user_task_stats
)

logger = get_logger(__name__)

def time_to_minutes(t):
    """Convert a time string 'HH:MM' to minutes since midnight."""
    if not isinstance(t, str):
        return 0
    match = re.match(r"(\d{1,2}):(\d{2})", t)
    if not match:
        return 0
    h, m = map(int, match.groups())
    return h * 60 + m

@handle_errors("setting up view edit messages window")
def setup_view_edit_messages_window(parent, category):
    """Opens a window for viewing and editing messages in a given category."""
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("setup_view_edit_messages_window called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return None
    
    window_attr_name = f"_{category}_edit_messages_window"
    view_messages_window = getattr(parent, window_attr_name, None)
    if view_messages_window is None or not view_messages_window.winfo_exists():
        view_messages_window = Toplevel(parent)
        view_messages_window.title(f"Edit Messages for {title_case(category)}")
        view_messages_window.category = category
        setattr(parent, window_attr_name, view_messages_window)
        
        # Set a better default size for the messages window
        default_geometry = "800x600"
        
        # Apply saved geometry if it exists, otherwise use default
        if hasattr(parent, f"{window_attr_name}_window_geometry"):
            geometry = getattr(parent, f"{window_attr_name}_window_geometry")
            logger.debug(f"Applying saved geometry: {geometry}")
            view_messages_window.geometry(geometry)
        else:
            view_messages_window.geometry(default_geometry)
            
        # Set minimum size to prevent content from being cut off
        view_messages_window.minsize(600, 400)
        
        # Define what happens when the window is closed using the custom function
        view_messages_window.protocol("WM_DELETE_WINDOW", lambda: save_geometry_and_close(view_messages_window, parent, window_attr_name))
    else:
        for widget in view_messages_window.winfo_children():
            widget.destroy()

    load_and_display_messages(view_messages_window, category)

@handle_errors("setting up view edit schedule window")
def setup_view_edit_schedule_window(parent, category, scheduler_manager=None):
    """Opens a window to view and edit the schedule for a given category."""
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("setup_view_edit_schedule_window called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return None
    
    window_attr_name = f"_{category}_edit_schedule_window"
    view_schedule_window = getattr(parent, window_attr_name, None)
    if view_schedule_window is None or not view_schedule_window.winfo_exists():
        view_schedule_window = Toplevel(parent)
        view_schedule_window.title(f"Edit Schedule for {title_case(category)}")
        view_schedule_window.category = category
        setattr(parent, window_attr_name, view_schedule_window)
        
        # --- Dynamic window sizing for schedule ---
        user_periods = get_schedule_time_periods(user_id, category)
        n_periods = len(user_periods)
        base_height = 180
        row_height = 38
        win_height = min(max(base_height + n_periods * row_height, 320), 700)
        win_width = 500
        view_schedule_window.geometry(f"{win_width}x{win_height}")
        view_schedule_window.minsize(400, 250)
        
        # Set minimum size to prevent content from being cut off
        #view_schedule_window.minsize(500, 400)
    
        # Define what happens when the window is closed using the custom function
        view_schedule_window.protocol("WM_DELETE_WINDOW", lambda: save_geometry_and_close(view_schedule_window, parent, window_attr_name))
    else:
        for widget in view_schedule_window.winfo_children():
            widget.destroy()

    load_and_display_schedule(view_schedule_window, parent, category, scheduler_manager)

@handle_errors("adding message dialog")
def add_message_dialog(parent, category):
    """Opens a dialog to add a message to the specified category."""
    user_id = UserContext().get_user_id()
    # Use new user-specific message file structure
    user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
    file_path = os.path.join(user_messages_dir, f"{category}.json")
    data = load_json_data(file_path)
    if data is None:
        raise ValueError("Failed to load message data.")

    dialog = MessageDialog(parent, category, data=data)
    dialog.grab_set()
    dialog.geometry("304x521+100+100")
    dialog.mainloop()

@handle_errors("saving geometry and closing window")
def save_geometry_and_close(window, parent, window_attr_name):
    """Save the window's geometry and then close it."""
    geometry = window.geometry()
    setattr(parent, f"{window_attr_name}_window_geometry", geometry)
    logger.debug(f"Saving geometry for {window_attr_name}: {geometry}")
    window.destroy()

@handle_errors("refreshing window")
def refresh_window(window, setup_func, parent, category, scheduler_manager):
    """Refreshes the given window by clearing and rebuilding the content."""
    # Clear all existing widgets in the window
    for widget in window.winfo_children():
        widget.destroy()
    
    # Rebuild the window content by calling the display function directly
    if setup_func == setup_view_edit_schedule_window:
        load_and_display_schedule(window, parent, category, scheduler_manager)
    elif setup_func == setup_view_edit_messages_window:
        load_and_display_messages(window, category)
    else:
        # Fallback to the original method
        setup_func(parent, category, scheduler_manager)
        
    logger.debug(f"Successfully refreshed window for category {category}")

# Initialize stacks for storing deleted items
deleted_message_stacks = {}
deleted_period_stacks = {}

class MessageDialog(tk.Toplevel):
    def __init__(self, parent, category, index=None, message_data=None, tree=None, data=None):
        super().__init__(parent)
        self.category = category
        self.parent = parent
        self.index = index
        self.message_data = message_data or {'message_id': str(uuid.uuid4()), 'days': [], 'time_periods': []}
        self.tree = tree

        user_id = UserContext().get_user_id()
        if not user_id:
            logger.error("MessageDialog.__init__ called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            self.destroy()
            return
        
        # Use new user-specific message file structure
        user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
        file_path = os.path.join(user_messages_dir, f"{category}.json")
        self.data = load_json_data(file_path)
        if not self.data:
            self.data = {"messages": []}

        try:
            # Use new user-specific message file structure
            user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
            file_path = os.path.join(user_messages_dir, f"{category}.json")
            self.data = load_json_data(file_path)
            if not self.data:
                self.data = {"messages": []}
        except Exception as e:
            logger.error(f"Error loading data for MessageDialog: {e}", exc_info=True)
            messagebox.showerror("Error", "Failed to load message data.")
            self.destroy()
            return

        # Days order (Sunday first)
        self.days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        # Prefill days: True if in message_data['days'] or if 'ALL' in message_data['days']
        self.days_vars = {day: IntVar(value=(('ALL' in self.message_data.get('days', [])) or (day in self.message_data.get('days', [])))) for day in self.days_order}
        user_time_periods = get_schedule_time_periods(user_id, self.category)
        # Sort periods by true chronological order (minutes since midnight)
        self.ordered_time_periods = sorted(
            [p for p in user_time_periods if p != 'ALL'],
            key=lambda p: time_to_minutes(user_time_periods[p]['start'])
        )
        self.time_periods = user_time_periods
        # Prefill time periods: True if in message_data['time_periods'] or if 'ALL' in message_data['time_periods']
        self.time_period_vars = {period: IntVar(value=(('ALL' in self.message_data.get('time_periods', [])) or (period in self.message_data.get('time_periods', [])))) for period in self.ordered_time_periods}
        self.select_all_font = font.Font(weight="bold", size=10)
        self.select_all_color = "black"

        # --- Dynamic window sizing ---
        base_height = 220
        row_height = 32
        n_rows = len(self.days_order) + len(self.ordered_time_periods) + 8  # 8 for labels/buttons/extra
        win_height = min(max(base_height + n_rows * row_height, 420), 900)
        # Width: base or based on longest period label
        base_width = 350
        max_period_label = max([len(f"{title_case(p)} ({self.time_periods[p]['start']} - {self.time_periods[p]['end']})") for p in self.ordered_time_periods], default=0)
        win_width = max(base_width, 250 + max_period_label * 7)
        self.geometry(f"{win_width}x{win_height}")
        self.minsize(350, 420)
        self.maxsize(700, 1000)

        # Add vertical scrollbar if content is tall
        if win_height >= 700:
            canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
            frame = tk.Frame(canvas, background="#f0f0f0")
            vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.create_window((0, 0), window=frame, anchor="nw")
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            frame.bind("<Configure>", on_frame_configure)
            self.content_frame = frame
        else:
            self.content_frame = self

        self.build_ui()

    def build_ui(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        tk.Label(self.content_frame, text="Message:").pack(anchor='w')
        self.message_entry = tk.Entry(self.content_frame, width=40)
        self.message_entry.pack(fill='x', padx=5, pady=2)
        self.message_entry.insert(0, self.message_data.get('message', ''))

        # --- Days section (Sunday first) ---
        days_frame = tk.LabelFrame(self.content_frame, text="Days:", font=("Arial", 10, "bold"))
        days_frame.pack(fill='x', padx=5, pady=(8, 0))
        
        # Check if all days are selected (either 'ALL' is present or all individual days are selected)
        all_days_selected = ('ALL' in self.message_data.get('days', [])) or all(day in self.message_data.get('days', []) for day in self.days_order)
        self.all_days_var = IntVar(value=all_days_selected)
        
        self.all_days_label = Checkbutton(days_frame, text="Select All", variable=self.all_days_var, command=self.handle_all_days_toggle, font=self.select_all_font, fg=self.select_all_color, activeforeground=self.select_all_color, selectcolor="white")
        self.all_days_label.pack(anchor='w')
        self.day_checkboxes = {}
        day_font = font.Font(size=10)
        for day in self.days_order:
            var = self.days_vars[day]
            cb = Checkbutton(days_frame, text=day, variable=var, font=day_font, fg="black", activeforeground="black", selectcolor="white", command=self.check_days_all_selected)
            cb.pack(anchor='w')
            self.day_checkboxes[day] = cb
        
        # Apply the correct state based on whether all days are selected
        if all_days_selected:
            self.handle_all_days_toggle()

        # --- Time periods section (chronological order) ---
        periods_frame = tk.LabelFrame(self.content_frame, text="Time Periods:", font=("Arial", 10, "bold"))
        periods_frame.pack(fill='x', padx=5, pady=(8, 0))
        
        # Check if all time periods are selected (either 'ALL' is present or all individual periods are selected)
        all_periods_selected = ('ALL' in self.message_data.get('time_periods', [])) or all(period in self.message_data.get('time_periods', []) for period in self.ordered_time_periods)
        self.all_periods_var = IntVar(value=all_periods_selected)
        
        self.all_periods_label = Checkbutton(periods_frame, text="Select All", variable=self.all_periods_var, command=self.handle_all_periods_toggle, font=self.select_all_font, fg=self.select_all_color, activeforeground=self.select_all_color, selectcolor="white")
        self.all_periods_label.pack(anchor='w')
        self.period_checkboxes = {}
        period_font = font.Font(size=10)
        for period in self.ordered_time_periods:
            var = self.time_period_vars[period]
            checkbox = Checkbutton(periods_frame, text=f"{title_case(period)} ({self.time_periods[period]['start']} - {self.time_periods[period]['end']})", variable=var, font=period_font, fg="black", activeforeground="black", selectcolor="white", command=self.check_periods_all_selected)
            checkbox.pack(anchor='w')
            self.period_checkboxes[period] = checkbox
        
        # Apply the correct state based on whether all periods are selected
        if all_periods_selected:
            self.handle_all_periods_toggle()

        tk.Button(self.content_frame, text="Save Message", command=self.save_message).pack(pady=8)

    @handle_errors("saving message")
    def save_message(self):
        """Saves the message to the JSON file."""
        # Days - check if all individual days are selected and convert to ALL
        individual_selected_days = [day for day, var in self.days_vars.items() if var.get() == 1]
        if len(individual_selected_days) == len(self.days_order):
            # All individual days are selected, use ALL
            selected_days = ['ALL']
        elif self.all_days_var.get() == 1:
            selected_days = ['ALL']
        else:
            selected_days = individual_selected_days
            
        # Periods - check if all individual periods are selected and convert to ALL
        individual_selected_periods = [period for period, var in self.time_period_vars.items() if var.get() == 1]
        if len(individual_selected_periods) == len(self.ordered_time_periods):
            # All individual periods are selected, use ALL
            selected_periods = ['ALL']
        elif self.all_periods_var.get() == 1:
            selected_periods = ['ALL']
        else:
            selected_periods = individual_selected_periods

        if not selected_days or not selected_periods:
            messagebox.showerror("Validation Error", "Please select at least one day and one time period.")
            return

        message_data = {
            "message_id": self.message_data.get("message_id", str(uuid.uuid4())),
            "message": self.message_entry.get(),
            "days": selected_days,
            "time_periods": selected_periods
        }

        if self.index is not None and self.tree is not None:
            # Editing existing message
            self.data['messages'][self.index] = message_data
        else:
            # Adding new message
            self.data['messages'].append(message_data)

        save_json_data(self.data, determine_file_path('messages', f'{self.category}/{UserContext().get_user_id()}'))
        if self.tree:
            self.tree.event_generate('<<DataUpdated>>')
            # Refresh the treeview after saving
            self.tree.update_idletasks()
        self.destroy()
        
    def handle_all_days_toggle(self):
        all_selected = self.all_days_var.get() == 1
        for day, cb in self.day_checkboxes.items():
            if all_selected:
                self.days_vars[day].set(1)
            else:
                self.days_vars[day].set(0)

    def handle_all_periods_toggle(self):
        all_selected = self.all_periods_var.get() == 1
        for period, cb in self.period_checkboxes.items():
            if all_selected:
                self.time_period_vars[period].set(1)
            else:
                self.time_period_vars[period].set(0)

    def check_days_all_selected(self):
        """Check if all individual days are selected and update the Select All checkbox accordingly"""
        individual_selected_count = sum(1 for var in self.days_vars.values() if var.get() == 1)
        if individual_selected_count == len(self.days_order):
            # All individual days are selected, check the Select All box
            self.all_days_var.set(1)
        elif individual_selected_count == 0:
            # No individual days are selected, uncheck the Select All box
            self.all_days_var.set(0)
        else:
            # Some but not all days are selected, uncheck the Select All box
            self.all_days_var.set(0)

    def check_periods_all_selected(self):
        """Check if all individual periods are selected and update the Select All checkbox accordingly"""
        individual_selected_count = sum(1 for var in self.time_period_vars.values() if var.get() == 1)
        if individual_selected_count == len(self.ordered_time_periods):
            # All individual periods are selected, check the Select All box
            self.all_periods_var.set(1)
        elif individual_selected_count == 0:
            # No individual periods are selected, uncheck the Select All box
            self.all_periods_var.set(0)
        else:
            # Some but not all periods are selected, uncheck the Select All box
            self.all_periods_var.set(0)

def load_and_display_messages(view_messages_window, category):
    """
    Loads and displays messages in the specified window for a given category, allowing for message editing.
    """
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("load_and_display_messages called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return

    try:
        # Use new user-specific message file structure
        user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
        file_path = os.path.join(user_messages_dir, f"{category}.json")
        data = load_json_data(file_path)
        messages = data.get('messages', []) if data else []
    except Exception as e:
        logger.error(f"Error loading messages for category {category}: {e}", exc_info=True)
        messagebox.showerror("Error", "Failed to load messages. Please try again.")
        return

    # Initialize the deleted message stack for this category if it doesn't exist
    if category not in deleted_message_stacks:
        deleted_message_stacks[category] = []

    # Get periods in chronological order (excluding ALL), then add ALL at the end if present
    periods_dict = get_schedule_time_periods(user_id, category)
    regular_periods = [p for p in periods_dict if p != 'ALL']
    # Sort periods by true chronological order (minutes since midnight)
    periods = sorted(regular_periods, key=lambda p: time_to_minutes(periods_dict[p]['start']))

    # Days order
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Columns: Message, message_id (hidden), All Days, days, All Times, periods
    columns = ['Message', 'message_id', 'All Days'] + days + ['All Times'] + periods
    # --- Scrollbars ---
    tree_frame = Frame(view_messages_window)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
    v_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
    h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended",
                       yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    v_scroll.config(command=tree.yview)
    h_scroll.config(command=tree.xview)
    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True, side="left")

    # --- Dynamic window width ---
    col_widths = [300 if col == 'Message' else 90 if col in ['All Days', 'All Times'] else 60 for col in columns]
    total_width = sum(col_widths) + 80  # Add some padding
    min_width = 800
    win_width = max(total_width, min_width)
    win_height = 600
    view_messages_window.geometry(f"{win_width}x{win_height}")

    # Define the column headings and widths
    for col in columns:
        if col == 'Message':
            tree.heading(col, text=col, anchor='w', command=lambda c=col: sort_treeview_column(tree, c, category))
            tree.column(col, width=300, anchor='w')
        elif col == 'message_id':
            tree.heading(col, text=col)
            tree.column(col, width=0, stretch=False)
        elif col == 'All Days':
            tree.heading(col, text='ALL DAYS', anchor='center', command=lambda c=col: sort_treeview_column(tree, c, category))
            tree.column(col, width=90, anchor='center')
        elif col == 'All Times':
            tree.heading(col, text='ALL TIMES', anchor='center', command=lambda c=col: sort_treeview_column(tree, c, category))
            tree.column(col, width=90, anchor='center')
        elif col in days:
            tree.heading(col, text=col, anchor='center', command=lambda c=col: sort_treeview_column(tree, c, category))
            tree.column(col, width=60, anchor='center')
        else:
            tree.heading(col, text=title_case(col), anchor='center', command=lambda c=col: sort_treeview_column(tree, c, category))
            tree.column(col, width=60, anchor='center')

    # Set the tree and messages as attributes of the window for refreshing later
    view_messages_window.tree = tree
    view_messages_window.messages = messages

    def on_treeview_click(event):
        """Handle clicks on the treeview to toggle checkmarks, but allow normal selection everywhere."""
        region = tree.identify("region", event.x, event.y)
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if region == "cell" and item and column:
            col_idx = int(column[1:]) - 1
            col_name = columns[col_idx]
            if col_name in days or col_name in periods or col_name in ['All Days', 'All Times']:
                toggle_checkmark(item, col_name, col_idx)
                return "break"  # Prevent selection from being overridden
        # Otherwise, allow normal selection

    def toggle_checkmark(item, col_name, col_idx):
        """Toggle the checkmark for a specific cell, fixing ALL DAYS/ALL TIMES logic."""
        user_id = UserContext().get_user_id()
        if not user_id:
            return
        try:
            values = tree.item(item)["values"]
            message_id = values[1]
            message_data = next((msg for msg in messages if msg['message_id'] == message_id), None)
            if not message_data:
                return
            changed = False
            if col_name == 'All Days':
                current_days = message_data.get('days', [])
                if 'ALL' in current_days:
                    current_days.remove('ALL')
                else:
                    current_days = ['ALL']
                message_data['days'] = current_days
                changed = True
            elif col_name in days:
                current_days = message_data.get('days', [])
                if 'ALL' in current_days:
                    # Replace 'ALL' with all days except the one being unchecked
                    current_days = [d for d in days if d != col_name]
                elif col_name in current_days:
                    # Uncheck: just remove this day (leave others)
                    current_days.remove(col_name)
                else:
                    # Check: add this day
                    current_days.append(col_name)
                # If all days are checked, switch to ALL
                if len(current_days) == len(days):
                    current_days = ['ALL']
                message_data['days'] = current_days
                changed = True
            elif col_name == 'All Times':
                current_periods = message_data.get('time_periods', [])
                if 'ALL' in current_periods:
                    current_periods.remove('ALL')
                else:
                    current_periods = ['ALL']
                message_data['time_periods'] = current_periods
                changed = True
            elif col_name in periods:
                current_periods = message_data.get('time_periods', [])
                if 'ALL' in current_periods:
                    # Replace 'ALL' with all periods except the one being unchecked
                    current_periods = [p for p in periods if p != col_name]
                elif col_name in current_periods:
                    current_periods.remove(col_name)
                else:
                    current_periods.append(col_name)
                # If all periods are checked, switch to ALL
                if len(current_periods) == len(periods):
                    current_periods = ['ALL']
                message_data['time_periods'] = current_periods
                changed = True
            if changed:
                update_message(user_id, category, message_id, message_data)
                # Instead of full refresh, just update the row to preserve order/selection
                update_treeview_row(item, message_data)
        except Exception as e:
            logger.error(f"Error toggling checkmark: {e}", exc_info=True)

    def update_treeview_row(item, message_data):
        # Rebuild the row values for this message
        row = []
        row.append(message_data.get('message', 'N/A'))
        row.append(message_data['message_id'])
        all_days = 'ALL' in message_data.get('days', [])
        row.append(checkmark(big=True) if all_days else '')
        for day in days:
            if all_days or day in message_data.get('days', []):
                row.append(checkmark())
            else:
                row.append('')
        all_times = 'ALL' in message_data.get('time_periods', [])
        row.append(checkmark(big=True) if all_times else '')
        for period in periods:
            if all_times or period in message_data.get('time_periods', []):
                row.append(checkmark())
            else:
                row.append('')
        tree.item(item, values=row)

    tree.bind("<Button-1>", on_treeview_click)

    # Helper for checkmark (✅ for All Days/Times columns, ✔ for others)
    def checkmark(big=False):
        return '✅' if big else '✔'

    # Populate the Treeview with messages from the specified category
    for msg in messages:
        row = []
        row.append(msg.get('message', 'N/A'))  # Message
        row.append(msg['message_id'])           # message_id (hidden)
        # All Days
        all_days = 'ALL' in msg.get('days', [])
        row.append(checkmark(big=True) if all_days else '')
        # Days
        for day in days:
            if all_days or day in msg.get('days', []):
                row.append(checkmark())
            else:
                row.append('')
        # All Times
        all_times = 'ALL' in msg.get('time_periods', [])
        row.append(checkmark(big=True) if all_times else '')
        # Periods
        for period in periods:
            if all_times or period in msg.get('time_periods', []):
                row.append(checkmark())
            else:
                row.append('')
        tree.insert("", tk.END, values=row)

    # Restore column sorting for all columns
    def treeview_sort_column(tv, col, category, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        # For checkmark columns, sort by presence of checkmark
        if col in ['All Days', 'All Times'] + days + periods:
            l.sort(key=lambda t: t[0] == '', reverse=reverse)
        elif col == 'Message':
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)  # Case-insensitive sort
        else:
            l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, category, not reverse))

    # Set up sorting for all columns
    for col in columns:
        if col != 'message_id':
            tree.heading(col, command=lambda c=col: treeview_sort_column(tree, c, category, False))

    def delete_message_local():
        """Deletes the selected message(s) from the Treeview and data file."""
        user_id = UserContext().get_user_id()
        if not user_id:
            logger.error("delete_message_local called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showerror("Error", "Please select at least one message to delete.")
                return

            # Confirm deletion
            if len(selected_items) == 1:
                confirm_message = "Are you sure you want to delete this message?"
            else:
                confirm_message = f"Are you sure you want to delete {len(selected_items)} messages?"
            
            if not messagebox.askyesno("Confirm Deletion", confirm_message):
                return

            deleted_count = 0
            for selected_item in selected_items:
                message_id = tree.item(selected_item)["values"][1]
                if message_id:
                    current_message_data = next((msg for msg in messages if msg['message_id'] == message_id), None)
                    if current_message_data:
                        # Store the current (possibly edited) version for undo
                        deleted_message_stacks[category].append(current_message_data.copy())
                        
                        # Remove from local messages list
                        local_message_data = next((msg for msg in messages if msg['message_id'] == message_id), None)
                        if local_message_data:
                            messages.remove(local_message_data)
                        
                        # Delete from file
                        delete_message(user_id, category, message_id)
                        deleted_count += 1
                    else:
                        logger.warning(f"Message not found in current data for ID: {message_id}")
                else:
                    logger.warning("Invalid message ID found in selection")

            # Refresh the treeview to reflect all changes
            refresh_treeview()
            update_undo_delete_message_button_state()
            
            if deleted_count == 1:
                messagebox.showinfo("Success", "Message deleted successfully.")
            else:
                messagebox.showinfo("Success", f"{deleted_count} messages deleted successfully.")
                
        except Exception as e:
            logger.error(f"Error deleting message(s): {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to delete message(s): {e}")

    def edit_message_local():
        """Edits the selected message in the Treeview and updates the data file."""
        user_id = UserContext().get_user_id()  # Get the user ID
        if not user_id:
            logger.error("edit_message_local called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showerror("Error", "Please select a message to edit.")
                return

            # If multiple items are selected, use the first one
            if len(selected_items) > 1:
                messagebox.showinfo("Multiple Selection", "Multiple messages selected. Only the first message will be edited.")

            selected_item = selected_items[0]
            message_id = tree.item(selected_item)["values"][1]
            message_data = next((msg for msg in messages if msg['message_id'] == message_id), None)
            if not message_data:
                messagebox.showerror("Error", "Message not found.")
                return

            dialog = MessageDialog(view_messages_window, category, index=messages.index(message_data), message_data=message_data, tree=tree, data=data)
            dialog.grab_set()
            dialog.geometry("304x521+100+100")
            dialog.mainloop()
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to edit message: {e}")

    def undo_message_deletion():
        """Restores the most recently deleted message."""
        if category in deleted_message_stacks and deleted_message_stacks[category]:
            user_id = UserContext().get_user_id()
            if not user_id:
                logger.error("undo_message_deletion called with None user_id")
                messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
                return

            try:
                # Restore the most recently deleted message from the stack
                message_data = deleted_message_stacks[category].pop()

                # Use the updated add_message function with the index and category
                add_message(user_id, category, message_data)

                # Update the local messages list
                messages.append(message_data)
                refresh_treeview()

                update_undo_delete_message_button_state()
            except Exception as e:
                logger.error(f"Error undoing message deletion: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to undo delete: {e}")

    def refresh_treeview():
        """Refresh the Treeview with the current messages list."""
        for item in tree.get_children():
            tree.delete(item)
        for msg in messages:
            row = []
            row.append(msg.get('message', 'N/A'))  # Message
            row.append(msg['message_id'])           # message_id (hidden)
            # All Days
            all_days = 'ALL' in msg.get('days', [])
            row.append(checkmark(big=True) if all_days else '')
            # Days
            for day in days:
                if all_days or day in msg.get('days', []):
                    row.append(checkmark())
                else:
                    row.append('')
            # All Times
            all_times = 'ALL' in msg.get('time_periods', [])
            row.append(checkmark(big=True) if all_times else '')
            # Periods
            for period in periods:
                if all_times or period in msg.get('time_periods', []):
                    row.append(checkmark())
                else:
                    row.append('')
            tree.insert("", tk.END, values=row)

    def update_undo_delete_message_button_state():
        """Update the state of the undo delete button."""
        if category in deleted_message_stacks and deleted_message_stacks[category]:
            undo_delete_message_button['state'] = 'normal'
        else:
            undo_delete_message_button['state'] = 'disabled'

    # Add buttons for message management
    button_frame = Frame(view_messages_window)
    button_frame.pack(fill="x", pady=10)

    # Left side buttons
    left_button_frame = Frame(button_frame)
    left_button_frame.pack(side="left", padx=5)

    add_button = Button(left_button_frame, text="Add Message", command=lambda: add_message_dialog(view_messages_window, category))
    add_button.pack(side="left", padx=5)

    edit_button = Button(left_button_frame, text="Edit Message", command=edit_message_local)
    edit_button.pack(side="left", padx=5)

    def select_all_messages():
        """Select all messages in the treeview."""
        for item in tree.get_children():
            tree.selection_add(item)
    
    def clear_selection():
        """Clear all selections in the treeview."""
        tree.selection_remove(tree.selection())
    
    select_all_button = Button(left_button_frame, text="Select All", command=select_all_messages)
    select_all_button.pack(side="left", padx=5)
    
    clear_selection_button = Button(left_button_frame, text="Clear Selection", command=clear_selection)
    clear_selection_button.pack(side="left", padx=5)
    
    refresh_button = Button(left_button_frame, text="Refresh", command=refresh_treeview)
    refresh_button.pack(side="left", padx=5)

    # Status bar
    status_frame = Frame(view_messages_window)
    status_frame.pack(fill="x", side="bottom", padx=10, pady=5)
    
    def update_status_bar():
        """Update the status bar with current selection and total counts."""
        total_items = len(tree.get_children())
        selected_items = len(tree.selection())
        if selected_items == 0:
            status_text = f"Total messages: {total_items}"
        elif selected_items == 1:
            status_text = f"1 of {total_items} messages selected"
        else:
            status_text = f"{selected_items} of {total_items} messages selected"
        status_label.config(text=status_text)
    
    status_label = Label(status_frame, text="", anchor="w")
    status_label.pack(side="left")
    
    # Update status when selection changes
    def on_selection_change(event):
        """
        Handle selection change events in the treeview.
        
        Args:
            event: Selection change event
        """
        # Update status bar and button states when selection changes
        update_status_bar()
        update_undo_delete_message_button_state()
    
    tree.bind("<<TreeviewSelect>>", on_selection_change)
    
    # Initial status update
    update_status_bar()

    # Right side buttons
    right_button_frame = Frame(button_frame)
    right_button_frame.pack(side="right", padx=5)

    delete_button = Button(right_button_frame, text="Delete Selected", command=delete_message_local)
    delete_button.pack(side="left", padx=5)

    undo_delete_message_button = Button(right_button_frame, text="Undo Last Delete", command=undo_message_deletion)
    undo_delete_message_button.pack(side="left", padx=5)

    # Set the state of the undo button based on the undo stack's state
    update_undo_delete_message_button_state()

# Global variables to track the current sort column and direction
current_sort_col = None
current_sort_reverse = False

def sort_treeview_column(tree, col, category, reverse=None):
    """
    Sorts the treeview column when a column heading is clicked.
    """
    global current_sort_col, current_sort_reverse
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("sort_treeview_column called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return

    try:
        # Determine if the column being sorted is different from the current sort column
        if col != current_sort_col:
            reverse = False  # Reset to ascending order for new column
        else:
            reverse = not current_sort_reverse if reverse is None else reverse

        if col in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] + list(get_schedule_time_periods(user_id, category).keys()):
            # Special handling for columns that have checkmarks
            data = [(tree.set(child, col) == '✔', child) for child in tree.get_children('')]
            data.sort(key=lambda x: (not x[0], x[0]), reverse=reverse)  # True as greater than False
        else:
            data = [(tree.set(child, col).lower(), child) for child in tree.get_children('')]
            data.sort(reverse=reverse)

        for index, (val, child) in enumerate(data):
            tree.move(child, '', index)

        # Update column heading command to sort in the opposite direction next time
        tree.heading(col, command=lambda: sort_treeview_column(tree, col, category))

        # Update the current sort column and direction
        current_sort_col = col
        current_sort_reverse = reverse

        logger.debug(f"Sorted column '{col}' in {'descending' if reverse else 'ascending'} order.")
    except Exception as e:
        logger.error(f"Error sorting column '{col}': {e}", exc_info=True)
        messagebox.showerror("Error", f"Failed to sort column: {e}")

def load_and_display_schedule(view_schedule_window, parent, category, scheduler_manager):
    """
    Loads schedule data and displays it in the specified window.
    This function is responsible for both fetching the data from a backend source and updating the UI components in the window.
    """
    global deleted_period_stacks

    user_id = UserContext().get_user_id()  # Ensure we are using user_id
    if not user_id:
        logger.error("load_and_display_schedule called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return

    try:
        schedule_data = get_schedule_time_periods(user_id, category)
        entries = {}
        original_times = {}
    except Exception as e:
        logger.error(f"Error loading schedule data for category {category}: {e}", exc_info=True)
        messagebox.showerror("Error", "Failed to load schedule data. Please try again.")
        return

    # Set the state of the undo button based on the undo stack's state
    undo_delete_period_button_state = 'normal' if category in deleted_period_stacks and deleted_period_stacks[category] else 'disabled'
    parent.undo_button = Button(view_schedule_window, text="Undo Last Delete", state=undo_delete_period_button_state, command=lambda: undo_last_period_deletion(view_schedule_window, parent, category, scheduler_manager))
    parent.undo_button.pack(pady=5)

    def delete_period(period):
        if period == 'ALL':
            return  # Do nothing for ALL
        user_id = UserContext().get_user_id()
        current_schedule_data = get_schedule_time_periods(user_id, category)
        if period in current_schedule_data:
            period_data = current_schedule_data[period]
            if period in entries:
                period_data['active'] = entries[period]['active_var'].get() == 1
            if len(current_schedule_data) <= 1:
                messagebox.showerror("Error", "You must have at least one schedule period.")
                return
            try:
                deleted_period_info = {'period': period, 'data': period_data}
                if category not in deleted_period_stacks:
                    deleted_period_stacks[category] = []
                deleted_period_stacks[category].append(deleted_period_info)
                delete_schedule_period(category, period, scheduler_manager)
                logger.debug(f"Current undo stack for {category}: {deleted_period_stacks[category]}")
                refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
                update_undo_delete_period_button_state()
            except Exception as e:
                logger.error(f"Error deleting schedule period: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to delete schedule period: {e}")
        else:
            logger.error(f"Period '{period}' not found in category '{category}' for user {user_id}.")
            messagebox.showerror("Error", f"Period '{period}' not found. The schedule may have been modified.")

    def update_period_active_status(period, var, category):
        if period == 'ALL':
            return  # Do nothing for ALL
        user_id = UserContext().get_user_id()
        is_active = var.get() == 1
        try:
            current_schedule_data = get_schedule_time_periods(user_id, category)
            if period not in current_schedule_data:
                logger.error(f"Period '{period}' not found in category '{category}' for user {user_id}.")
                messagebox.showerror("Error", f"Period '{period}' not found. The schedule may have been modified.")
                return
            set_schedule_period_active(user_id, category, period, is_active)
            logger.info(f"Period '{period}' in category '{category}' set to {'active' if is_active else 'inactive'}.")
            if is_active and scheduler_manager:
                scheduler_manager.reset_and_reschedule_daily_messages(category)
            elif is_active and not scheduler_manager:
                logger.info(f"Period '{period}' activated, but no scheduler manager available (UI-only mode)")
        except Exception as e:
            logger.error(f"Error updating period active status for '{period}': {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to update period status: {e}")

    def validate_and_save_period(category, name, start, end, scheduler_manager, refresh=True):
        if name == 'ALL':
            return False  # Do nothing for ALL
        user_id = UserContext().get_user_id()
        try:
            current_schedule_data = get_schedule_time_periods(user_id, category)
            if name in current_schedule_data:
                edit_schedule_period(category, name, start, end, scheduler_manager)
            else:
                add_schedule_period(category, name, start, end, scheduler_manager)
        except InvalidTimeFormatError:
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM format (e.g., 09:00).")
            return False
        except Exception as e:
            logger.error(f"Error saving schedule period '{name}' in category '{category}': {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save schedule period: {e}")
            return False
        if refresh:
            refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
        return True

    # Displaying existing schedule periods
    if not schedule_data:
        logger.error(f"No schedule times data available for {category}.")
        messagebox.showerror("Error", f"No schedule times data available for {category}.")
        return

    for period, times in schedule_data.items():
        frame = Frame(view_schedule_window)
        frame.pack(fill='x', padx=10, pady=5)
        tk.Label(frame, text=f"{title_case(period)} Start:").pack(side='left')
        start_entry = Entry(frame, width=10)
        start_entry.insert(0, times['start'])
        start_entry.pack(side='left', padx=5)
        tk.Label(frame, text="End:").pack(side='left')
        end_entry = Entry(frame, width=10)
        end_entry.insert(0, times['end'])
        end_entry.pack(side='left', padx=5)
        active_var = IntVar(value=1 if times.get('active', True) else 0)
        active_checkbutton = Checkbutton(frame, text="Active", variable=active_var, command=lambda p=period, v=active_var, c=category: update_period_active_status(p, v, c))
        active_checkbutton.pack(side='left', padx=5)
        delete_button = Button(frame, text="Delete", command=lambda p=period: delete_period(p))
        delete_button.pack(side='right')
        # Special handling for ALL period
        if period == 'ALL':
            start_entry.config(state='disabled')
            end_entry.config(state='disabled')
            active_var.set(1)
            active_checkbutton.config(state='disabled')
            delete_button.config(state='disabled')
        entries[period] = {'start': start_entry, 'end': end_entry, 'active_var': active_var}
        original_times[period] = {'start': times['start'], 'end': times['end']}

    def add_edit_period():
        new_period_frame = Frame(view_schedule_window)
        new_period_frame.pack(fill='x', padx=10, pady=5)
        period_name_frame = Frame(new_period_frame)
        period_name_frame.pack(fill='x', padx=5, pady=2)
        tk.Label(period_name_frame, text="Period Name:").pack(anchor='w')
        new_period_name = Entry(period_name_frame, width=20)
        new_period_name.pack(anchor='w', padx=5)
        time_frame = Frame(new_period_frame)
        time_frame.pack(fill='x', padx=5, pady=2)
        tk.Label(time_frame, text="Start Time:").grid(row=0, column=0, sticky='w', padx=5)
        tk.Label(time_frame, text="End Time:").grid(row=0, column=1, sticky='w', padx=5)
        new_start_entry = Entry(time_frame, width=10)
        new_start_entry.grid(row=1, column=0, padx=5)
        new_end_entry = Entry(time_frame, width=10)
        new_end_entry.grid(row=1, column=1, padx=5)
        def confirm():
            name = new_period_name.get().lower()
            start = new_start_entry.get()
            end = new_end_entry.get()
            user_id = UserContext().get_user_id()
            current_schedule_data = get_schedule_time_periods(user_id, category)
            if name in current_schedule_data:
                response = messagebox.askyesno("Name Exists", f"A period named '{name}' already exists. Would you like to edit it?")
                if response:
                    if validate_and_save_period(category, name, start, end, scheduler_manager):
                        messagebox.showinfo("Updated", "Period updated successfully.")
                        new_period_frame.destroy()
                else:
                    messagebox.showinfo("Change Name", "Please change the name of the period.")
            else:
                if validate_and_save_period(category, name, start, end, scheduler_manager):
                    messagebox.showinfo("Added", "New period added successfully.")
                    new_period_frame.destroy()
        confirm_button = Button(new_period_frame, text="Confirm", command=confirm)
        confirm_button.pack(pady=10)
        new_period_name.bind("<Return>", lambda event: confirm())
        new_start_entry.bind("<Return>", lambda event: confirm())
        new_end_entry.bind("<Return>", lambda event: confirm())

    def save_schedule():
        updated = False
        for period, entry_controls in entries.items():
            if period == 'ALL':
                continue  # Do not allow editing ALL
            start_time_str = entry_controls['start'].get()
            end_time_str = entry_controls['end'].get()
            if start_time_str != original_times[period]['start'] or end_time_str != original_times[period]['end']:
                if validate_and_save_period(category, period, start_time_str, end_time_str, scheduler_manager, refresh=False):
                    updated = True
        if updated:
            messagebox.showinfo("Schedule Saved", "The schedule has been updated successfully.")
            refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
        else:
            messagebox.showinfo("No Changes", "No changes were made to the schedule.")

    add_button = Button(view_schedule_window, text="Add New Period", command=add_edit_period)
    add_button.pack(pady=10)
    save_button = Button(view_schedule_window, text="Save Schedule", command=save_schedule)
    save_button.pack(pady=10)

    def undo_last_period_deletion(view_schedule_window, parent, category, scheduler_manager):
        """Restores the most recently deleted period, skipping 'ALL' if present."""
        while category in deleted_period_stacks and deleted_period_stacks[category]:
            user_id = UserContext().get_user_id()
            if not user_id:
                logger.error("undo_last_period_deletion called with None user_id")
                messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
                return
            try:
                # Restore the most recently deleted period from the stack
                last_deleted_period_info = deleted_period_stacks[category].pop()
                period = last_deleted_period_info['period']
                times = last_deleted_period_info['data']
                if period == 'ALL':
                    # Skip restoring ALL, try next
                    continue
                # Load user data to ensure the period is restored in the correct state
                from core.user_management import get_user_data, update_user_account, update_user_preferences, update_user_context
                from core.schedule_management import set_schedule_periods
                
                # Get current user data
                user_data_result = get_user_data(user_id, 'account')
                user_account = user_data_result.get('account') or {}
                prefs_result = get_user_data(user_id, 'preferences')
                user_preferences = prefs_result.get('preferences') or {}
                context_result = get_user_data(user_id, 'context')
                user_context = context_result.get('context') or {}
                
                # Update schedules in preferences
                if 'schedules' not in user_preferences:
                    user_preferences['schedules'] = {}
                if category not in user_preferences['schedules']:
                    user_preferences['schedules'][category] = {}
                
                # Restore the period with its original data, including active status
                user_preferences['schedules'][category][period] = times
                
                # Save updated preferences
                update_user_preferences(user_id, user_preferences)
                # Clear the cache for this user/category
                clear_schedule_periods_cache(user_id, category)
                logger.info(f"Restored schedule period for user {user_id}, category {category}, period {period} with data: {times}")
                # Refresh the schedule window to reflect the restored period
                refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
                # Reschedule if the restored period is active (only if scheduler is available)
                if times.get('active', False) and scheduler_manager:
                    scheduler_manager.reset_and_reschedule_daily_messages(category)
                elif times.get('active', False) and not scheduler_manager:
                    logger.info(f"Period '{period}' restored as active, but no scheduler manager available (UI-only mode)")
                # Update the undo button state
                update_undo_delete_period_button_state()
                break  # Only restore one period per undo
            except Exception as e:
                logger.error(f"Error undoing schedule period deletion: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to undo delete: {e}")
                break

    def update_undo_delete_period_button_state():
        """Update the state of the undo delete button for periods."""
        if category in deleted_period_stacks and deleted_period_stacks[category]:
            parent.undo_button['state'] = 'normal'
        else:
            parent.undo_button['state'] = 'disabled'

# Communication channel and category management functions
def setup_communication_settings_window(parent, user_id):
    """Opens a window to manage user's communication settings."""
    logger.info(f"Opening communication settings for user {user_id}")
    
    settings_window = Toplevel(parent)
    settings_window.title(f"Communication Settings - {user_id}")
    settings_window.geometry("450x300")
    
    try:
        # Load preferences and profile separately for accuracy using new functions
        from core.user_management import get_user_data, update_user_account, update_user_preferences, update_user_context
        
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account') or {}
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences') or {}
        context_result = get_user_data(user_id, 'context')
        user_context = context_result.get('context') or {}
        
        # Ensure preferences structure exists
        if not user_preferences:
            user_preferences = {}
        
        preferences = user_preferences
        profile = user_account
        current_service = preferences.get('channel', {}).get('type', 'email')
        current_email = profile.get('email', '')
        current_phone = profile.get('phone', '')
        current_discord_id = profile.get('discord_user_id', '')
        
        tk.Label(settings_window, text="Communication Channel Settings", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Current service display
        tk.Label(settings_window, text=f"Current service: {current_service.title()}", font=("Arial", 12), fg="blue").pack(pady=5)
        
        # Combined Contact Information & Service Selection Section
        combined_frame = tk.LabelFrame(settings_window, text="Contact Information & Communication Service", font=("Arial", 10, "bold"))
        combined_frame.pack(fill="x", padx=20, pady=10)
        
        service_var = tk.StringVar(value=current_service)
        
        # Email
        email_frame = tk.Frame(combined_frame)
        email_frame.pack(fill="x", pady=5, padx=10)
        email_radio = tk.Radiobutton(email_frame, text="Email:", variable=service_var, value="email", width=10, anchor='w')
        email_radio.pack(side="left")
        email_var = tk.StringVar(value=current_email)
        email_entry = tk.Entry(email_frame, textvariable=email_var, width=25)
        email_entry.pack(side="left", padx=(5, 10))
        email_status = tk.Label(email_frame, text="✓ Configured" if current_email else "✗ Not configured", 
                               fg="green" if current_email else "red", font=("Arial", 8))
        email_status.pack(side="left")
        
        # Telegram/Phone
        telegram_frame = tk.Frame(combined_frame)
        telegram_frame.pack(fill="x", pady=5, padx=10)
        telegram_radio = tk.Radiobutton(telegram_frame, text="Telegram:", variable=service_var, value="telegram", width=10, anchor='w')
        telegram_radio.pack(side="left")
        phone_var = tk.StringVar(value=current_phone)
        phone_entry = tk.Entry(telegram_frame, textvariable=phone_var, width=25)
        phone_entry.pack(side="left", padx=(5, 10))
        telegram_status = tk.Label(telegram_frame, text="✓ Configured" if current_phone else "✗ Not configured", 
                                  fg="green" if current_phone else "red", font=("Arial", 8))
        telegram_status.pack(side="left")
        
        # Discord
        discord_frame = tk.Frame(combined_frame)
        discord_frame.pack(fill="x", pady=5, padx=10)
        discord_radio = tk.Radiobutton(discord_frame, text="Discord:", variable=service_var, value="discord", width=10, anchor='w')
        discord_radio.pack(side="left")
        discord_var = tk.StringVar(value=current_discord_id)
        discord_entry = tk.Entry(discord_frame, textvariable=discord_var, width=25)
        discord_entry.pack(side="left", padx=(5, 10))
        discord_status = tk.Label(discord_frame, text="✓ Configured" if current_discord_id else "✗ Not configured", 
                                 fg="green" if current_discord_id else "red", font=("Arial", 8))
        discord_status.pack(side="left")
        
        def update_status_labels():
            """Update status labels based on current field values"""
            email_status.config(text="✓ Configured" if email_var.get().strip() else "✗ Not configured",
                               fg="green" if email_var.get().strip() else "red")
            telegram_status.config(text="✓ Configured" if phone_var.get().strip() else "✗ Not configured",
                                  fg="green" if phone_var.get().strip() else "red")
            discord_status.config(text="✓ Configured" if discord_var.get().strip() else "✗ Not configured",
                                 fg="green" if discord_var.get().strip() else "red")
        
        # Bind entry fields to update status labels
        email_var.trace('w', lambda *args: update_status_labels())
        phone_var.trace('w', lambda *args: update_status_labels())
        discord_var.trace('w', lambda *args: update_status_labels())
        
        def save_communication_settings():
            new_service = service_var.get()
            new_email = email_var.get().strip()
            new_phone = phone_var.get().strip()
            new_discord_id = discord_var.get().strip()
            
            # Validate that required field is filled for selected service
            if new_service == "email" and not new_email:
                messagebox.showerror("Validation Error", "Email address is required for email service.")
                return
            elif new_service == "telegram" and not new_phone:
                messagebox.showerror("Validation Error", "Phone number is required for Telegram service.")
                return
            elif new_service == "discord" and not new_discord_id:
                messagebox.showerror("Validation Error", "Discord ID is required for Discord service.")
                return
            
            # Track what changes were made
            changes = []
            
            # Check service change
            if new_service != current_service:
                changes.append(f"Primary communication channel set to {new_service.title()}")
            
            # Check email change
            if new_email != current_email:
                if current_email and new_email:
                    changes.append("Email address updated")
                elif new_email:
                    changes.append("Email address added")
                elif current_email:
                    changes.append("Email address removed")
            
            # Check phone change
            if new_phone != current_phone:
                if current_phone and new_phone:
                    changes.append("Phone number updated")
                elif new_phone:
                    changes.append("Phone number added")
                elif current_phone:
                    changes.append("Phone number removed")
            
            # Check Discord ID change
            if new_discord_id != current_discord_id:
                if current_discord_id and new_discord_id:
                    changes.append("Discord ID updated")
                elif new_discord_id:
                    changes.append("Discord ID added")
                elif current_discord_id:
                    changes.append("Discord ID removed")
            
            # If no changes, show appropriate message
            if not changes:
                messagebox.showinfo("No Changes", "No changes were made to communication settings.")
                return
            
            try:
                # Update user preferences and contact info
                preferences['discord_user_id'] = new_discord_id
                profile['email'] = new_email
                profile['phone'] = new_phone
                # Save both preferences and profile using new functions
                update_user_preferences(user_id, preferences)
                update_user_account(user_id, profile)
                logger.info(f"Updated communication settings for user {user_id}: service={new_service}, email={bool(new_email)}, phone={bool(new_phone)}, discord={bool(new_discord_id)}")
                
                # Show detailed feedback about what changed
                changes_text = "\n• " + "\n• ".join(changes)
                messagebox.showinfo("Settings Updated", f"Successfully updated:\n{changes_text}")
                settings_window.destroy()
            except Exception as e:
                logger.error(f"Error updating communication settings: {e}")
                messagebox.showerror("Error", f"Failed to update settings: {e}")
        
        # Save and Cancel buttons
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        
        Button(button_frame, text="Save Changes", command=save_communication_settings).pack(side="left", padx=5)
        Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side="left", padx=5)
        
    except Exception as e:
        logger.error(f"Error loading communication settings: {e}")
        messagebox.showerror("Error", f"Failed to load communication settings: {e}")
        settings_window.destroy()

def setup_category_management_window(parent, user_id):
    """Opens a window to manage user's message categories."""
    logger.info(f"Opening category management for user {user_id}")
    
    category_window = Toplevel(parent)
    category_window.title(f"Category Management - {user_id}")
    category_window.geometry("500x400")
    
    try:
        # Use new user management functions
        from core.user_management import update_user_preferences
        
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences') or {}
        preferences = user_preferences
        current_categories = preferences.get('categories', [])
        available_categories = get_message_categories()
        
        tk.Label(category_window, text="Manage Categories", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Categories frame
        categories_frame = tk.LabelFrame(category_window, text="Available Categories", font=("Arial", 10, "bold"))
        categories_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Combined toggle button (like checkin settings)
        control_frame = tk.Frame(categories_frame)
        control_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        category_vars = {}
        
        def toggle_all():
            """Smart toggle: select all if not all selected, deselect all if all selected"""
            # Check if all are currently selected
            all_selected = all(var.get() == 1 for var in category_vars.values())
            
            if all_selected:
                # Deselect all
                for var in category_vars.values():
                    var.set(0)
                toggle_button.config(text="Select All")
            else:
                # Select all
                for var in category_vars.values():
                    var.set(1)
                toggle_button.config(text="Deselect All")
        
        def update_toggle_button_text():
            """Update the toggle button text based on current selection state"""
            if not category_vars:  # If category_vars is empty, can't check
                return
            all_selected = all(var.get() == 1 for var in category_vars.values())
            toggle_button.config(text="Deselect All" if all_selected else "Select All")
        
        toggle_button = tk.Button(control_frame, text="Select All", command=toggle_all, width=12)
        toggle_button.pack(side="left", padx=5)
        
        # Sort categories for consistent display
        sorted_categories = sorted(available_categories)
        
        for category in sorted_categories:
            var = tk.IntVar(value=1 if category in current_categories else 0)
            category_vars[category] = var
            
            category_frame = tk.Frame(categories_frame)
            category_frame.pack(fill="x", pady=2, padx=10)
            
            # Checkbox for the category
            checkbox = tk.Checkbutton(category_frame, text=title_case(category), variable=var, font=("Arial", 10))
            checkbox.pack(side="left")
            
            # Status indicator
            if category in current_categories:
                status_label = tk.Label(category_frame, text="✓ Currently Active", fg="green", font=("Arial", 8))
            else:
                status_label = tk.Label(category_frame, text="○ Currently Inactive", fg="gray", font=("Arial", 8))
            status_label.pack(side="left", padx=(20, 0))
            
            def make_update_status(status_label=status_label, var=var):
                def update_status(*args):
                    if var.get():
                        status_label.config(text="✓ Will be Active", fg="blue")
                    else:
                        status_label.config(text="○ Will be Inactive", fg="orange")
                    # Update toggle button text when any checkbox changes
                    update_toggle_button_text()
                return update_status
            
            var.trace('w', make_update_status())
        
        # Set initial toggle button text
        update_toggle_button_text()
        
        # Instructions
        instructions_frame = tk.Frame(category_window)
        instructions_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(instructions_frame, text="Note: Enabling a category will create default schedules and message files.", 
                font=("Arial", 8, "italic"), fg="gray").pack()
        tk.Label(instructions_frame, text="Disabling a category will keep existing data but hide it from the user.", 
                font=("Arial", 8, "italic"), fg="gray").pack()
        
        def save_category_changes():
            try:
                selected_categories = [category for category, var in category_vars.items() if var.get() == 1]
                
                # Check for changes
                original_set = set(current_categories)
                new_set = set(selected_categories)
                
                if original_set == new_set:
                    # No changes made
                    messagebox.showinfo("No Changes", "No changes were made to category settings.")
                    logger.info(f"No changes made to categories for user {user_id}")
                    category_window.destroy()
                    return
                
                if not selected_categories:
                    messagebox.showerror("Error", "At least one category must be selected.")
                    return
                
                # Determine what changed
                added_categories = new_set - original_set
                removed_categories = original_set - new_set
                
                # Update categories in preferences using new functions
                prefs_result = get_user_data(user_id, 'preferences')
                user_preferences = prefs_result.get('preferences') or {}
                user_preferences['categories'] = selected_categories
                
                # Save changes
                update_user_preferences(user_id, user_preferences)
                
                # Create message files for new categories
                for category in added_categories:
                    # Message files are now created automatically by ensure_user_message_files()
                    # when categories are added via update_user_preferences()
                    pass
                
                # Show what changed
                change_summary = []
                if added_categories:
                    change_summary.append(f"Added: {', '.join(title_case(cat) for cat in sorted(added_categories))}")
                if removed_categories:
                    change_summary.append(f"Removed: {', '.join(title_case(cat) for cat in sorted(removed_categories))}")
                
                message = "Categories updated successfully!\n\n" + "\n".join(change_summary)
                
                logger.info(f"Updated categories for user {user_id}: {selected_categories}")
                messagebox.showinfo("Categories Updated", message)
                
                category_window.destroy()
                
            except Exception as e:
                logger.error(f"Error updating categories: {e}")
                messagebox.showerror("Error", f"Failed to update categories: {e}")
        
        # Buttons frame
        button_frame = tk.Frame(category_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Save Changes", command=save_category_changes).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=category_window.destroy).pack(side="left", padx=5)
        
    except Exception as e:
        logger.error(f"Error loading category management: {e}")
        messagebox.showerror("Error", f"Failed to load category management: {e}")
        category_window.destroy()

def setup_checkin_management_window(root, user_id):
    """Set up the check-in management window for a specific user"""
    # Removed duplicate logging - ui_app.py already logs this action
    
    # Create a new window
    checkin_window = tk.Toplevel(root)
    checkin_window.title(f"Check-in Settings - {user_id}")
    # Dynamic: base + 30 per question, clamp 500-900
    n_questions = 14  # If you add more, update this
    base_height = 260
    row_height = 32
    win_height = min(max(base_height + n_questions * row_height, 600), 900)
    checkin_window.geometry(f"600x{win_height}")
    checkin_window.minsize(500, 600)
    checkin_window.resizable(True, True)

    try:
        # Use new user management functions
        from core.user_management import update_user_preferences
        
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences') or {}
        preferences = user_preferences
        current_checkin_prefs = preferences.get('checkins', {})
        
        # Load schedule data from schedules.json to get time and days
        from core.file_operations import get_user_file_path, load_json_data
        schedules_file = get_user_file_path(user_id, 'schedules')
        schedules_data = load_json_data(schedules_file) or {}
        checkin_schedule = schedules_data.get('checkin', {}).get('checkin_time', {})
        
        # Merge preferences with schedule data
        current_checkin_prefs = {
            "enabled": current_checkin_prefs.get("enabled", False),
            "start_time": checkin_schedule.get("start", "09:00"),
            "end_time": checkin_schedule.get("end", "10:00"),
            "days": checkin_schedule.get("days", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
            "questions": current_checkin_prefs.get("questions", {})
        }
        
        tk.Label(checkin_window, text="Check-in Settings", font=("Arial", 14, "bold")).pack(pady=10)

        # Enable/disable check-ins (within the Check-in Settings section)
        enabled_frame = tk.Frame(checkin_window)
        enabled_frame.pack(fill="x", padx=20, pady=(0, 10))
        checkin_enabled_var = tk.IntVar(value=1 if current_checkin_prefs.get("enabled", False) else 0)
        checkin_checkbox = tk.Checkbutton(enabled_frame, text="Enable check-ins", variable=checkin_enabled_var, font=("Arial", 12, "bold"))
        checkin_checkbox.pack(side="left")
        if current_checkin_prefs.get("enabled", False):
            status_label = tk.Label(enabled_frame, text="✓ Currently Active", fg="green", font=("Arial", 10))
        else:
            status_label = tk.Label(enabled_frame, text="○ Currently Inactive", fg="gray", font=("Arial", 10))
        status_label.pack(side="left", padx=(20, 0))

        # Main content frame for two-column layout
        content_frame = tk.Frame(checkin_window)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left column (Time Range + Days)
        left_col = tk.Frame(content_frame)
        left_col.pack(side="left", fill="y", padx=(0, 10), pady=0, anchor="n")

        # Right column (Questions)
        right_col = tk.Frame(content_frame)
        right_col.pack(side="left", fill="both", expand=True, pady=0, anchor="n")

        # --- Time Range Section ---
        current_start = current_checkin_prefs.get("start_time", "09:00")
        current_end = current_checkin_prefs.get("end_time", "10:00")
        time_frame = tk.LabelFrame(left_col, text="Time Range", font=("Arial", 10, "bold"))
        time_frame.pack(fill="x", padx=5, pady=(0, 10))
        time_selection_frame = tk.Frame(time_frame)
        time_selection_frame.pack(fill="x", padx=5, pady=3)
        tk.Label(time_selection_frame, text="Start:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        checkin_start_var = tk.StringVar(value=current_start)
        start_entry = tk.Entry(time_selection_frame, textvariable=checkin_start_var, width=6, font=("Arial", 10))
        start_entry.pack(side="left", padx=2)
        tk.Label(time_selection_frame, text="End:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
        checkin_end_var = tk.StringVar(value=current_end)
        end_entry = tk.Entry(time_selection_frame, textvariable=checkin_end_var, width=6, font=("Arial", 10))
        end_entry.pack(side="left", padx=2)
        # --- End Time Range Section ---

        # --- Days of the Week Section ---
        current_days = current_checkin_prefs.get("days", [
            "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
        ])
        days_frame = tk.LabelFrame(left_col, text="Days of the Week", font=("Arial", 10, "bold"))
        days_frame.pack(fill="x", padx=5, pady=(0, 10))
        days_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_vars = {day: tk.IntVar(value=1 if day in current_days else 0) for day in days_order}
        # Select All checkbox
        def all_days_selected():
            """
            Check if all days of the week are selected for check-in preferences.
            
            Returns:
                bool: True if all days are selected, False otherwise
            """
            return all(day_vars[day].get() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
        def handle_all_days_toggle():
            new_val = all_days_var.get()
            for var in day_vars.values():
                var.set(new_val)
        all_days_var = tk.IntVar(value=1 if all_days_selected() else 0)
        all_days_cb = tk.Checkbutton(days_frame, text="Select All", variable=all_days_var, font=("Arial", 10, "bold"), command=handle_all_days_toggle)
        all_days_cb.pack(anchor="w", padx=2, pady=(2, 0))
        # Update Select All if any day is toggled
        def update_all_days_cb(*_):
            all_selected = all_days_selected()
            if all_selected != bool(all_days_var.get()):
                all_days_var.set(1 if all_selected else 0)
        for day in days_order:
            day_vars[day].trace_add('write', update_all_days_cb)
        day_font = font.Font(size=10)
        for day in days_order:
            cb = tk.Checkbutton(days_frame, text=day, variable=day_vars[day], font=day_font, fg="black", activeforeground="black", selectcolor="white")
            cb.pack(anchor="w", padx=12)
        # --- End Days of the Week Section ---

        # --- Questions section (right column) ---
        questions_frame = tk.LabelFrame(right_col, text="Questions to Include", font=("Arial", 10, "bold"))
        questions_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        control_frame = tk.Frame(questions_frame)
        control_frame.pack(fill="x", padx=10, pady=(5, 10))
        default_questions = {
            'mood': {'label': 'Mood (1-5 scale) (recommended)', 'default': True},
            'energy': {'label': 'Energy level (1-5 scale) (recommended)', 'default': True},
            'ate_breakfast': {'label': 'Had breakfast (yes/no) (recommended)', 'default': True},
            'brushed_teeth': {'label': 'Brushed teeth (yes/no) (recommended)', 'default': True},
            'sleep_quality': {'label': 'Sleep quality (1-5 scale)', 'default': False},
            'sleep_hours': {'label': 'Hours of sleep (number)', 'default': False},
            'anxiety_level': {'label': 'Anxiety level (1-5 scale)', 'default': False},
            'focus_level': {'label': 'Focus/attention (1-5 scale)', 'default': False},
            'medication_taken': {'label': 'Took medication (yes/no)', 'default': False},
            'exercise': {'label': 'Did exercise (yes/no)', 'default': False},
            'hydration': {'label': 'Staying hydrated (yes/no)', 'default': False},
            'social_interaction': {'label': 'Had social interaction (yes/no)', 'default': False},
            'stress_level': {'label': 'Stress level (1-5 scale)', 'default': False},
            'daily_reflection': {'label': 'Brief reflection/notes (text)', 'default': False}
        }
        question_vars = {}
        current_questions = current_checkin_prefs.get("questions", {})
        def select_default():
            """
            Select default check-in preferences for the user.
            
            Sets up common default values for check-in frequency and questions.
            """
            # Set default values
            frequency_var.set("daily")
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                day_vars[day].set(True)
            for day in ['saturday', 'sunday']:
                day_vars[day].set(False)
        def toggle_all():
            all_selected = all(var.get() == 1 for var in question_vars.values())
            if all_selected:
                for var in question_vars.values():
                    var.set(0)
                toggle_button.config(text="Select All")
            else:
                for var in question_vars.values():
                    var.set(1)
                toggle_button.config(text="Deselect All")
        def update_toggle_button_text():
            if not question_vars:
                return
            all_selected = all(var.get() == 1 for var in question_vars.values())
            toggle_button.config(text="Deselect All" if all_selected else "Select All")
        Button(control_frame, text="Select Default", command=select_default, width=12, font=day_font).pack(side="left", padx=(0, 5))
        toggle_button = Button(control_frame, text="Select All", command=toggle_all, width=12, font=day_font)
        toggle_button.pack(side="left")
        
        # Create scrollable frame for questions
        canvas = tk.Canvas(questions_frame)
        scrollbar = tk.Scrollbar(questions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse scroll wheel support
        def on_mouse_wheel(event):
            """
            Handle mouse wheel scrolling for the check-in management window.
            
            Args:
                event: Mouse wheel event containing delta information
            """
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def bind_mouse_wheel(widget):
            """Recursively bind mouse wheel to widget and all its children"""
            widget.bind("<MouseWheel>", on_mouse_wheel)
            for child in widget.winfo_children():
                bind_mouse_wheel(child)
        
        # Bind mouse wheel to canvas and all children
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        scrollable_frame.bind("<MouseWheel>", on_mouse_wheel)
        
        # Add questions to scrollable frame
        row = 0
        for question_key, question_info in default_questions.items():
            # Check if question is currently enabled
            current_enabled = current_questions.get(question_key, {}).get("enabled", question_info['default'])
            
            var = tk.IntVar(value=1 if current_enabled else 0)
            question_vars[question_key] = var
            
            question_frame = tk.Frame(scrollable_frame)
            question_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
            scrollable_frame.grid_columnconfigure(0, weight=1)
            
            checkbox = tk.Checkbutton(question_frame, text=question_info['label'], 
                                    variable=var, font=("Arial", 10))
            checkbox.pack(side="left")
            
            # Bind mouse wheel to checkbox
            checkbox.bind("<MouseWheel>", on_mouse_wheel)
            
            # Status indicator
            if current_enabled:
                status = tk.Label(question_frame, text="✓ Active", fg="green", font=("Arial", 8))
            else:
                status = tk.Label(question_frame, text="○ Inactive", fg="gray", font=("Arial", 8))
            status.pack(side="left", padx=(20, 0))
            
            # Bind mouse wheel to status label and question frame
            status.bind("<MouseWheel>", on_mouse_wheel)
            question_frame.bind("<MouseWheel>", on_mouse_wheel)
            
            # Update status when checkbox changes
            def make_update_status(status_label=status, var=var):
                def update_status(*args):
                    if var.get():
                        status_label.config(text="✓ Will be Active", fg="blue")
                    else:
                        status_label.config(text="○ Will be Inactive", fg="orange")
                    # Note: Category management doesn't need toggle button text updates
                return update_status
            
            var.trace('w', make_update_status())
            
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Set initial toggle button text
        update_toggle_button_text()
        
        # Instructions
        instructions_frame = tk.Frame(checkin_window)
        instructions_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(instructions_frame, 
                text="Note: Check-ins help track patterns and provide personalized AI responses.\n"
                     "More questions provide richer data but take longer to complete.", 
                font=("Arial", 8, "italic"), fg="gray", justify=tk.LEFT).pack()
        
        def save_checkin_changes():
            try:
                from core.schedule_management import validate_and_format_time
                # Validate time fields
                try:
                    formatted_start = validate_and_format_time(checkin_start_var.get())
                    formatted_end = validate_and_format_time(checkin_end_var.get())
                except Exception as e:
                    messagebox.showerror("Invalid Time Format", f"Start and End times must be in HH:MM (24h) or H[H]:MM AM/PM format.\nError: {e}")
                    return
                # Build new check-in preferences
                selected_days = [day for day, var in day_vars.items() if var.get() == 1]
                new_checkin_prefs = {
                    "enabled": checkin_enabled_var.get() == 1,
                    "start_time": formatted_start,
                    "end_time": formatted_end,
                    "days": selected_days,
                    "questions": {}
                }
                for question_key, var in question_vars.items():
                    new_checkin_prefs["questions"][question_key] = {
                        "enabled": var.get() == 1,
                        "label": default_questions[question_key]['label']
                    }
                # Check for changes by comparing with current settings
                current_enabled = current_checkin_prefs.get("enabled", False)
                current_start = current_checkin_prefs.get("start_time", "09:00")
                current_end = current_checkin_prefs.get("end_time", "10:00")
                current_days = current_checkin_prefs.get("days", [
                    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
                ])
                current_questions_dict = current_checkin_prefs.get("questions", {})
                enabled_changed = new_checkin_prefs["enabled"] != current_enabled
                start_changed = new_checkin_prefs["start_time"] != current_start
                end_changed = new_checkin_prefs["end_time"] != current_end
                days_changed = set(new_checkin_prefs["days"]) != set(current_days)
                questions_changed = False
                for question_key, new_data in new_checkin_prefs["questions"].items():
                    current_data = current_questions_dict.get(question_key, {})
                    current_question_enabled = current_data.get("enabled", default_questions[question_key]['default'])
                    if new_data["enabled"] != current_question_enabled:
                        questions_changed = True
                        break
                if not (enabled_changed or start_changed or end_changed or days_changed or questions_changed):
                    messagebox.showinfo("No Changes", "No changes were made to check-in settings.")
                    logger.info(f"No changes made to check-in settings for user {user_id}")
                    checkin_window.destroy()
                    return
                # Load user data using new structure
                from core.user_management import get_user_data, update_user_account, update_user_preferences, update_user_context
                
                user_data_result = get_user_data(user_id, 'account')
                user_account = user_data_result.get('account') or {}
                prefs_result = get_user_data(user_id, 'preferences')
                user_preferences = prefs_result.get('preferences') or {}
                context_result = get_user_data(user_id, 'context')
                user_context = context_result.get('context') or {}
                
                # Ensure preferences structure exists
                if not user_preferences:
                    user_preferences = {}
                
                # Save check-in preferences (enabled status and questions) to preferences
                checkin_preferences = {
                    "enabled": new_checkin_prefs["enabled"],
                    "questions": new_checkin_prefs["questions"]
                }
                user_preferences['checkins'] = checkin_preferences
                
                # Load current schedules to preserve existing category schedules
                from core.file_operations import get_user_file_path, load_json_data
                schedules_file = get_user_file_path(user_id, 'schedules')
                current_schedules = load_json_data(schedules_file) or {}
                
                # Update schedules with new check-in settings
                if 'schedules' not in current_schedules:
                    current_schedules['schedules'] = {}
                
                # Preserve existing category schedules
                for category, schedule_info in current_schedules.items():
                    if category != 'checkin':  # Don't overwrite check-in, we'll set that below
                        current_schedules[category] = schedule_info
                
                # Always preserve check-in schedule data, regardless of enabled status
                current_schedules["checkin"] = {
                    "checkin_time": {
                        "start": new_checkin_prefs["start_time"],
                        "end": new_checkin_prefs["end_time"],
                        "active": True,
                        "days": selected_days,
                        "description": f"Check-in scheduled between {new_checkin_prefs['start_time']} and {new_checkin_prefs['end_time']} on {', '.join(selected_days)}"
                    }
                }
                
                # Save check-in preferences using new structure
                user_preferences['checkins'] = checkin_preferences
                update_user_preferences(user_id, user_preferences)
                
                # Reschedule check-ins if enabled status changed or schedule changed
                if enabled_changed or start_changed or end_changed or days_changed:
                    try:
                        # Create reschedule request for service to pick up
                        from core.service_utilities import create_reschedule_request
                        create_reschedule_request(user_id, "checkin")
                        logger.info(f"Created reschedule request for check-ins for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Could not create reschedule request for check-ins: {e}")
                
                enabled_count = sum(1 for var in question_vars.values() if var.get() == 1)
                status = "enabled" if new_checkin_prefs["enabled"] else "disabled"
                change_details = []
                if enabled_changed:
                    change_details.append(f"Check-ins {status}")
                if start_changed or end_changed:
                    change_details.append(f"Time Range: {new_checkin_prefs['start_time']} - {new_checkin_prefs['end_time']}")
                if days_changed:
                    change_details.append(f"Days: {', '.join(new_checkin_prefs['days'])}")
                if questions_changed:
                    change_details.append(f"Questions: {enabled_count} selected")
                message = "Check-in settings updated successfully!\n\n" + "\n".join(change_details)
                logger.info(f"Updated check-in settings for user {user_id}: enabled={new_checkin_prefs['enabled']}, questions={enabled_count}, time={new_checkin_prefs['start_time']}-{new_checkin_prefs['end_time']}, days={new_checkin_prefs['days']}")
                messagebox.showinfo("Check-in Settings Updated", message)
                checkin_window.destroy()
            except Exception as e:
                logger.error(f"Error updating check-in settings: {e}")
                messagebox.showerror("Error", f"Failed to update check-in settings: {e}")
        
        # Buttons frame
        button_frame = tk.Frame(checkin_window)
        button_frame.pack(pady=10)
        
        Button(button_frame, text="Save Changes", command=save_checkin_changes).pack(side="left", padx=5)
        Button(button_frame, text="Cancel", command=checkin_window.destroy).pack(side="left", padx=5)
        
        # Update status when main checkbox changes
        def update_main_status(*args):
            if checkin_enabled_var.get():
                status_label.config(text="✓ Will be Active", fg="blue")
            else:
                status_label.config(text="○ Will be Inactive", fg="orange")
        
        checkin_enabled_var.trace('w', update_main_status)
        
        # Add extra padding below buttons if present
        for child in checkin_window.winfo_children():
            if isinstance(child, tk.Frame):
                child.pack_configure(pady=(0, 10))
        
    except Exception as e:
        logger.error(f"Error loading check-in management: {e}")
        messagebox.showerror("Error", f"Failed to load check-in management: {e}")
        checkin_window.destroy()

def setup_checkin_analytics_window(root, user_id):
    """Set up the check-in analytics window for a specific user"""
    # Create a new window
    analytics_window = tk.Toplevel(root)
    analytics_window.title(f"Check-in Analytics - {user_id}")
    analytics_window.geometry("800x600")
    analytics_window.resizable(True, True)

    try:
        # Create main frame with scrollbar
        main_frame = tk.Frame(analytics_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = tk.Label(scrollable_frame, text="Check-in Analytics & Insights", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Period selection
        period_frame = tk.LabelFrame(scrollable_frame, text="Analysis Period", font=("Arial", 10, "bold"))
        period_frame.pack(fill="x", pady=(0, 20))
        
        period_var = tk.StringVar(value="30")
        tk.Label(period_frame, text="Days to analyze:").pack(side="left", padx=10, pady=5)
        for days in ["7", "14", "30", "60"]:
            tk.Radiobutton(period_frame, text=f"{days} days", variable=period_var, 
                          value=days).pack(side="left", padx=10, pady=5)
        
        # Results area
        results_frame = tk.LabelFrame(scrollable_frame, text="Analytics Results", font=("Arial", 10, "bold"))
        results_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create text widget for results
        results_text = tk.Text(results_frame, wrap="word", height=20, font=("Consolas", 9))
        results_scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        results_scrollbar.pack(side="right", fill="y")
        
        def run_analytics():
            """Run analytics and display results"""
            try:
                days = int(period_var.get())
                results_text.delete(1.0, tk.END)
                results_text.insert(tk.END, f"Running analytics for {days} days...\n\n")
                analytics_window.update()
                
                # Run all analytics
                analyses = {}
                
                # Mood trends
                results_text.insert(tk.END, "📊 Analyzing mood trends...\n")
                mood_analysis = checkin_analytics.get_mood_trends(user_id, days)
                analyses['mood'] = mood_analysis
                
                # Habit analysis
                results_text.insert(tk.END, "📈 Analyzing habits...\n")
                habit_analysis = checkin_analytics.get_habit_analysis(user_id, days)
                analyses['habits'] = habit_analysis
                
                # Sleep analysis
                results_text.insert(tk.END, "😴 Analyzing sleep patterns...\n")
                sleep_analysis = checkin_analytics.get_sleep_analysis(user_id, days)
                analyses['sleep'] = sleep_analysis
                
                # Wellness score
                results_text.insert(tk.END, "🌟 Calculating wellness score...\n")
                wellness_score = checkin_analytics.get_wellness_score(user_id, min(days, 7))
                analyses['wellness'] = wellness_score
                
                # Clear and display results
                results_text.delete(1.0, tk.END)
                display_analytics_results(results_text, analyses, days)
                
            except Exception as e:
                logger.error(f"Error running analytics for user {user_id}: {e}")
                results_text.delete(1.0, tk.END)
                results_text.insert(tk.END, f"Error running analytics: {e}")
        
        def display_analytics_results(text_widget, analyses, days):
            """Display formatted analytics results"""
            text_widget.insert(tk.END, f"📊 CHECK-IN ANALYTICS REPORT\n")
            text_widget.insert(tk.END, f"Period: Last {days} days\n")
            text_widget.insert(tk.END, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            text_widget.insert(tk.END, "=" * 60 + "\n\n")
            
            # Wellness Score (most important)
            wellness = analyses.get('wellness', {})
            if 'error' not in wellness:
                text_widget.insert(tk.END, "🌟 WELLNESS SCORE\n")
                text_widget.insert(tk.END, f"Overall Score: {wellness.get('overall_score', 'N/A')}/100 ({wellness.get('score_level', 'N/A')})\n")
                text_widget.insert(tk.END, f"Mood Score: {wellness.get('mood_score', 'N/A')}/100\n")
                text_widget.insert(tk.END, f"Habit Score: {wellness.get('habit_score', 'N/A')}/100\n")
                text_widget.insert(tk.END, f"Sleep Score: {wellness.get('sleep_score', 'N/A')}/100\n")
                
                recommendations = wellness.get('recommendations', [])
                if recommendations:
                    text_widget.insert(tk.END, "\n💡 Recommendations:\n")
                    for rec in recommendations:
                        text_widget.insert(tk.END, f"• {rec}\n")
                text_widget.insert(tk.END, "\n")
            
            # Mood Trends
            mood = analyses.get('mood', {})
            if 'error' not in mood:
                text_widget.insert(tk.END, "😊 MOOD TRENDS\n")
                text_widget.insert(tk.END, f"Average Mood: {mood.get('average_mood', 'N/A')}/5\n")
                text_widget.insert(tk.END, f"Mood Trend: {mood.get('trend', 'N/A').title()}\n")
                text_widget.insert(tk.END, f"Best Day: {mood.get('best_day', {}).get('date', 'N/A')} (Mood: {mood.get('best_day', {}).get('mood', 'N/A')})\n")
                text_widget.insert(tk.END, f"Worst Day: {mood.get('worst_day', {}).get('date', 'N/A')} (Mood: {mood.get('worst_day', {}).get('mood', 'N/A')})\n")
                text_widget.insert(tk.END, "\n")
            
            # Habit Analysis
            habits = analyses.get('habits', {})
            if 'error' not in habits:
                text_widget.insert(tk.END, "📈 HABIT ANALYSIS\n")
                text_widget.insert(tk.END, f"Overall Completion: {habits.get('overall_completion', 'N/A')}%\n\n")
                
                habit_stats = habits.get('habits', {})
                for habit_key, habit_data in habit_stats.items():
                    text_widget.insert(tk.END, f"{habit_data['name']}:\n")
                    text_widget.insert(tk.END, f"  Completion: {habit_data['completion_rate']}% ({habit_data['status']})\n")
                    text_widget.insert(tk.END, f"  Current Streak: {habit_data['current_streak']} days\n")
                    text_widget.insert(tk.END, f"  Best Streak: {habit_data['best_streak']} days\n")
                text_widget.insert(tk.END, "\n")
            
            # Sleep Analysis
            sleep = analyses.get('sleep', {})
            if 'error' not in sleep:
                text_widget.insert(tk.END, "😴 SLEEP ANALYSIS\n")
                text_widget.insert(tk.END, f"Average Hours: {sleep.get('average_hours', 'N/A')}\n")
                text_widget.insert(tk.END, f"Average Quality: {sleep.get('average_quality', 'N/A')}/5\n")
                text_widget.insert(tk.END, f"Good Sleep Days: {sleep.get('good_sleep_days', 'N/A')}\n")
                text_widget.insert(tk.END, f"Poor Sleep Days: {sleep.get('poor_sleep_days', 'N/A')}\n")
                text_widget.insert(tk.END, f"Sleep Consistency: {sleep.get('sleep_consistency', 'N/A')}%\n")
                
                recommendations = sleep.get('recommendations', [])
                if recommendations:
                    text_widget.insert(tk.END, "\n💡 Sleep Recommendations:\n")
                    for rec in recommendations:
                        text_widget.insert(tk.END, f"• {rec}\n")
                text_widget.insert(tk.END, "\n")
            
            # Error handling
            for analysis_name, analysis_data in analyses.items():
                if 'error' in analysis_data:
                    text_widget.insert(tk.END, f"❌ {analysis_name.upper()} ANALYSIS ERROR\n")
                    text_widget.insert(tk.END, f"{analysis_data['error']}\n\n")
        
        # Buttons
        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Run Analytics", command=run_analytics, 
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(button_frame, text="Close", command=analytics_window.destroy).pack(side="left", padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Run initial analytics
        run_analytics()
        
    except Exception as e:
        logger.error(f"Error setting up analytics window for user {user_id}: {e}")
        messagebox.showerror("Error", f"Failed to load analytics: {e}")
        analytics_window.destroy() 

def setup_task_management_window(parent, user_id):
    """Opens a window to manage user's task settings."""
    logger.info(f"Opening task management for user {user_id}")

    task_window = Toplevel(parent)
    task_window.title(f"Task Management - {user_id}")
    task_window.geometry("700x600")

    try:
        # Load user data using new structure
        from core.user_management import get_user_data, update_user_preferences
        
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences') or {}
        if 'tasks' not in user_preferences:
            user_preferences['tasks'] = {}
        task_preferences = user_preferences.get('tasks', {})
        tasks_enabled = task_preferences.get('enabled', False)
        
        # Load reminder periods and days from schedules.json using the same system as check-ins
        from core.schedule_management import get_reminder_periods_and_days
        reminder_periods, reminder_days = get_reminder_periods_and_days(user_id, 'tasks')
        
        # Backward compatibility: migrate old single time if present in preferences
        if not reminder_periods and 'default_reminder_time' in task_preferences:
            reminder_periods = [{
                'start': task_preferences['default_reminder_time'],
                'end': task_preferences['default_reminder_time'],
                'active': True
            }]

        # Title label at the top
        tk.Label(task_window, text="Task Management Settings", font=("Arial", 16, "bold")).pack(pady=(15, 5))

        # Enable/disable tasks (moved above settings)
        enable_frame = tk.Frame(task_window)
        enable_frame.pack(fill="x", padx=20, pady=(0, 0))
        tasks_enabled_var = tk.IntVar(value=1 if tasks_enabled else 0)
        enable_checkbox = tk.Checkbutton(enable_frame, text="Enable Task Management", variable=tasks_enabled_var, font=("Arial", 10))
        enable_checkbox.pack(anchor="w")

        # Main settings frame
        settings_frame = tk.LabelFrame(task_window, text="Task Settings", font=("Arial", 10, "bold"))
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Two-column layout for periods and days as side-by-side boxes
        columns_frame = tk.Frame(settings_frame)
        columns_frame.pack(fill="x", padx=10, pady=10)

        # Left: Reminder Time Periods box (narrower)
        periods_box = tk.LabelFrame(columns_frame, text="Reminder Time Periods", font=("Arial", 10, "bold"))
        periods_box.pack(side="left", fill="both", expand=False, padx=(0, 15), pady=0, anchor="n", ipadx=10, ipady=5)
        periods_box.config(width=280)
        period_widgets = []
        def render_periods():
            for w in period_widgets:
                w.destroy()
            period_widgets.clear()
            for idx, period in enumerate(reminder_periods):
                row = tk.Frame(periods_box)
                row.pack(fill="x", pady=3, anchor="w")
                start_var = tk.StringVar(value=period.get('start', '09:00'))
                tk.Label(row, text="Start:").pack(side="left")
                start_entry = tk.Entry(row, textvariable=start_var, width=6)
                start_entry.pack(side="left", padx=(0, 5))
                end_var = tk.StringVar(value=period.get('end', '10:00'))
                tk.Label(row, text="End:").pack(side="left")
                end_entry = tk.Entry(row, textvariable=end_var, width=6)
                end_entry.pack(side="left", padx=(0, 5))
                active_var = tk.IntVar(value=1 if period.get('active', True) else 0)
                active_cb = tk.Checkbutton(row, text="Active", variable=active_var)
                active_cb.pack(side="left", padx=(5, 5))
                def make_delete(idx):
                    return lambda: (reminder_periods.pop(idx), render_periods())
                del_btn = tk.Button(row, text="Delete", command=make_delete(idx))
                del_btn.pack(side="left", padx=(5, 0))
                period_widgets.append(row)
                period['__vars'] = {
                    'start_time': start_var, 'end_time': end_var, 'active': active_var
                }
        render_periods()
        tk.Button(periods_box, text="Add New Period", command=lambda: (reminder_periods.append({'start_time': '09:00', 'end_time': '10:00', 'active': True}), render_periods())).pack(anchor="w", pady=5)

        # Right: Reminder Days box (wider)
        days_box = tk.LabelFrame(columns_frame, text="Reminder Days", font=("Arial", 10, "bold"))
        days_box.pack(side="left", fill="y", expand=True, padx=(0,0), pady=0, anchor="n", ipadx=30, ipady=5)
        days_box.config(width=200)
        days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_vars = []
        
        # Create day variables first
        for i, day in enumerate(days_of_week):
            var = tk.IntVar(value=1 if day in reminder_days else 0)
            day_vars.append(var)
        
        # Select All checkbox - initialize based on actual selected days
        all_days_selected = all(var.get() for var in day_vars)
        select_all_var = tk.IntVar(value=1 if all_days_selected else 0)
        
        def on_select_all():
            """
            Handle select all functionality for task management.
            
            Selects all available tasks in the current view.
            """
            for item in task_tree.selection():
                task_tree.selection_remove(item)
            for item in task_tree.get_children():
                task_tree.selection_add(item)
        
        select_all_cb = tk.Checkbutton(days_box, text="Select All", variable=select_all_var, command=on_select_all)
        select_all_cb.pack(anchor="w", pady=(2, 2))
        
        def update_select_all(*_):
            if all(v.get() for v in day_vars):
                select_all_var.set(1)
            elif all(not v.get() for v in day_vars):
                select_all_var.set(0)
            else:
                select_all_var.set(0)
        
        # Create checkboxes and bind update function
        for i, day in enumerate(days_of_week):
            cb = tk.Checkbutton(days_box, text=day, variable=day_vars[i], command=update_select_all)
            cb.pack(anchor="w")

        # When enabling task management for the first time, add a default period if none exist
        def on_enable_toggle(*_):
            """
            Handle enable/disable toggle for task management.
            
            Toggles the enabled state of task management features.
            """
            enabled = enable_var.get()
            if enabled:
                # Enable task management features
                task_tree.config(state='normal')
                add_button.config(state='normal')
                edit_button.config(state='normal')
                complete_button.config(state='normal')
                delete_button.config(state='normal')
            else:
                # Disable task management features
                task_tree.config(state='disabled')
                add_button.config(state='disabled')
                edit_button.config(state='disabled')
                complete_button.config(state='disabled')
                delete_button.config(state='disabled')
        tasks_enabled_var.trace_add('write', on_enable_toggle)

        # Task statistics frame (unchanged)
        stats_frame = tk.LabelFrame(task_window, text="Task Statistics", font=("Arial", 10, "bold"))
        stats_frame.pack(fill="x", padx=20, pady=10)
        try:
            from tasks.task_management import get_user_task_stats
            stats = get_user_task_stats(user_id)
            stats_text = f"Active Tasks: {stats.get('active_count', 0)}\n"
            stats_text += f"Completed Tasks: {stats.get('completed_count', 0)}\n"
            stats_text += f"Total Tasks: {stats.get('total_count', 0)}"
            stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 10), justify=tk.LEFT)
            stats_label.pack(padx=10, pady=10)
        except Exception as e:
            logger.warning(f"Could not load task statistics: {e}")
            stats_label = tk.Label(stats_frame, text="Task statistics unavailable", font=("Arial", 10, "italic"), fg="gray")
            stats_label.pack(padx=10, pady=10)

        # Instructions (unchanged)
        instructions_frame = tk.Frame(task_window)
        instructions_frame.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(instructions_frame, text="Task management allows users to create and track tasks with reminders.", font=("Arial", 8, "italic"), fg="gray").pack()
        tk.Label(instructions_frame, text="Tasks can be managed through the AI chatbot interface.", font=("Arial", 8, "italic"), fg="gray").pack()

        def save_task_changes():
            try:
                from core.file_operations import get_user_file_path, load_json_data, save_json_data
                from core.schedule_management import validate_and_format_time
                schedules_file = get_user_file_path(user_id, 'schedules')
                # Gather periods from UI
                new_periods = []
                for period in reminder_periods:
                    vars = period.get('__vars', {})
                    start = vars['start_time'].get().strip()
                    end = vars['end_time'].get().strip()
                    try:
                        formatted_start = validate_and_format_time(start)
                        formatted_end = validate_and_format_time(end)
                    except Exception as e:
                        messagebox.showerror("Error", f"Invalid time format: {e}")
                        return
                    active = vars['active'].get() == 1
                    new_periods.append({'start_time': formatted_start, 'end_time': formatted_end, 'active': active})
                # Gather days from UI (as names)
                days = [day for day, v in zip(days_of_week, day_vars) if v.get() == 1]
                if not days:
                    messagebox.showerror("Error", "Please select at least one day for reminders.")
                    return
                new_enabled = tasks_enabled_var.get() == 1
                # Update task preferences using new structure
                user_preferences['tasks']['enabled'] = new_enabled
                update_user_preferences(user_id, user_preferences)
                # Always preserve task reminder schedule data, regardless of enabled status
                from core.schedule_management import set_reminder_periods_and_days
                set_reminder_periods_and_days(user_id, 'tasks', new_periods, days)
                
                # Reschedule task reminders if enabled status changed or schedule changed
                if new_enabled != tasks_enabled:
                    try:
                        # Create reschedule request for service to pick up
                        from core.service_utilities import create_reschedule_request
                        create_reschedule_request(user_id, "tasks")
                        logger.info(f"Created reschedule request for task reminders for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Could not create reschedule request for task reminders: {e}")
                
                message = "Task settings updated successfully!"
                logger.info(f"Updated task settings for user {user_id}: enabled={new_enabled}, periods={new_periods}, days={days}")
                messagebox.showinfo("Task Settings Updated", message)
                task_window.destroy()
            except Exception as e:
                logger.error(f"Error updating task settings: {e}")
                messagebox.showerror("Error", f"Failed to update task settings: {e}")

        button_frame = tk.Frame(task_window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save Changes", command=save_task_changes).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=task_window.destroy).pack(side="left", padx=5)

    except Exception as e:
        logger.error(f"Error loading task management: {e}")
        messagebox.showerror("Error", f"Failed to load task management: {e}")
        task_window.destroy()

@handle_errors("setting up task CRUD window")
def setup_task_crud_window(parent, user_id):
    """Opens a window for full CRUD operations on tasks."""
    logger.info(f"Opening task CRUD window for user {user_id}")

    task_crud_window = Toplevel(parent)
    task_crud_window.title(f"Task Management - {user_id}")
    task_crud_window.geometry("1000x700")
    task_crud_window.minsize(800, 600)

    # Main container
    main_frame = tk.Frame(task_crud_window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Title
    title_label = tk.Label(main_frame, text="Task Management", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 10))

    # Create notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True)

    # Active Tasks Tab
    active_frame = tk.Frame(notebook)
    notebook.add(active_frame, text="Active Tasks")

    # Completed Tasks Tab
    completed_frame = tk.Frame(notebook)
    notebook.add(completed_frame, text="Completed Tasks")

    # Task Statistics Tab
    stats_frame = tk.Frame(notebook)
    notebook.add(stats_frame, text="Statistics")

    # Active Tasks Tab Content
    def setup_active_tasks_tab():
        # Toolbar
        toolbar = tk.Frame(active_frame)
        toolbar.pack(fill="x", padx=5, pady=5)

        tk.Button(toolbar, text="Add New Task", command=lambda: add_task_dialog(active_frame, user_id, refresh_active_tasks)).pack(side="left", padx=5)
        tk.Button(toolbar, text="Edit Selected", command=lambda: edit_selected_task(active_frame, user_id, refresh_active_tasks)).pack(side="left", padx=5)
        tk.Button(toolbar, text="Complete Selected", command=lambda: complete_selected_task(active_frame, user_id, refresh_active_tasks)).pack(side="left", padx=5)
        tk.Button(toolbar, text="Delete Selected", command=lambda: delete_selected_task(active_frame, user_id, refresh_active_tasks)).pack(side="left", padx=5)
        tk.Button(toolbar, text="Refresh", command=lambda: refresh_active_tasks()).pack(side="left", padx=5)

        # Treeview for active tasks
        columns = ("Title", "Description", "Due Date", "Due Time", "Priority", "Category", "Created")
        active_tree = ttk.Treeview(active_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        active_tree.heading("Title", text="Title")
        active_tree.heading("Description", text="Description")
        active_tree.heading("Due Date", text="Due Date")
        active_tree.heading("Due Time", text="Due Time")
        active_tree.heading("Priority", text="Priority")
        active_tree.heading("Category", text="Category")
        active_tree.heading("Created", text="Created")

        active_tree.column("Title", width=150)
        active_tree.column("Description", width=200)
        active_tree.column("Due Date", width=100)
        active_tree.column("Due Time", width=80)
        active_tree.column("Priority", width=80)
        active_tree.column("Category", width=100)
        active_tree.column("Created", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(active_frame, orient="vertical", command=active_tree.yview)
        active_tree.configure(yscrollcommand=scrollbar.set)

        active_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Status bar
        status_bar = tk.Label(active_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        def refresh_active_tasks():
            """Refresh the active tasks treeview."""
            try:
                # Clear existing items
                for item in active_tree.get_children():
                    active_tree.delete(item)

                # Load and display active tasks
                tasks = load_active_tasks(user_id)
                for task in tasks:
                    values = (
                        task.get('title', ''),
                        task.get('description', ''),
                        task.get('due_date', ''),
                        task.get('due_time', ''),
                        task.get('priority', 'medium'),
                        task.get('category', ''),
                        task.get('created_at', '')
                    )
                    active_tree.insert('', 'end', values=values, tags=(task.get('task_id', ''),))

                status_bar.config(text=f"Loaded {len(tasks)} active tasks")
                
            except Exception as e:
                logger.error(f"Error refreshing active tasks: {e}")
                status_bar.config(text=f"Error loading tasks: {e}")

        # Store the tree and refresh function for external access
        active_frame.active_tree = active_tree
        active_frame.refresh_active_tasks = refresh_active_tasks
        active_frame.status_bar = status_bar

        # Initial load
        refresh_active_tasks()

    # Completed Tasks Tab Content
    def setup_completed_tasks_tab():
        # Toolbar
        toolbar = tk.Frame(completed_frame)
        toolbar.pack(fill="x", padx=5, pady=5)

        tk.Button(toolbar, text="Refresh", command=lambda: refresh_completed_tasks()).pack(side="left", padx=5)

        # Treeview for completed tasks
        columns = ("Title", "Description", "Due Date", "Priority", "Category", "Completed")
        completed_tree = ttk.Treeview(completed_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        completed_tree.heading("Title", text="Title")
        completed_tree.heading("Description", text="Description")
        completed_tree.heading("Due Date", text="Due Date")
        completed_tree.heading("Priority", text="Priority")
        completed_tree.heading("Category", text="Category")
        completed_tree.heading("Completed", text="Completed")

        completed_tree.column("Title", width=150)
        completed_tree.column("Description", width=200)
        completed_tree.column("Due Date", width=100)
        completed_tree.column("Priority", width=80)
        completed_tree.column("Category", width=100)
        completed_tree.column("Completed", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(completed_frame, orient="vertical", command=completed_tree.yview)
        completed_tree.configure(yscrollcommand=scrollbar.set)

        completed_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Status bar
        status_bar = tk.Label(completed_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        def refresh_completed_tasks():
            """Refresh the completed tasks treeview."""
            try:
                # Clear existing items
                for item in completed_tree.get_children():
                    completed_tree.delete(item)

                # Load and display completed tasks
                tasks = load_completed_tasks(user_id)
                for task in tasks:
                    values = (
                        task.get('title', ''),
                        task.get('description', ''),
                        task.get('due_date', ''),
                        task.get('priority', 'medium'),
                        task.get('category', ''),
                        task.get('completed_at', '')
                    )
                    completed_tree.insert('', 'end', values=values, tags=(task.get('task_id', ''),))

                status_bar.config(text=f"Loaded {len(tasks)} completed tasks")
                
            except Exception as e:
                logger.error(f"Error refreshing completed tasks: {e}")
                status_bar.config(text=f"Error loading tasks: {e}")

        # Store the tree and refresh function for external access
        completed_frame.completed_tree = completed_tree
        completed_frame.refresh_completed_tasks = refresh_completed_tasks
        completed_frame.status_bar = status_bar

        # Initial load
        refresh_completed_tasks()

    # Statistics Tab Content
    def setup_statistics_tab():
        stats_content = tk.Frame(stats_frame)
        stats_content.pack(fill="both", expand=True, padx=20, pady=20)

        def refresh_statistics():
            """Refresh the statistics display."""
            try:
                # Clear existing content
                for widget in stats_content.winfo_children():
                    widget.destroy()

                # Get statistics
                stats = get_user_task_stats(user_id)
                active_tasks = load_active_tasks(user_id)
                completed_tasks = load_completed_tasks(user_id)
                due_soon = get_tasks_due_soon(user_id, 7)

                # Create statistics display
                tk.Label(stats_content, text="Task Statistics", font=("Arial", 14, "bold")).pack(pady=(0, 20))

                # Basic stats
                basic_frame = tk.LabelFrame(stats_content, text="Overview", font=("Arial", 10, "bold"))
                basic_frame.pack(fill="x", pady=10)

                tk.Label(basic_frame, text=f"Active Tasks: {stats.get('active_count', 0)}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)
                tk.Label(basic_frame, text=f"Completed Tasks: {stats.get('completed_count', 0)}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)
                tk.Label(basic_frame, text=f"Total Tasks: {stats.get('total_count', 0)}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)

                # Due soon tasks
                due_frame = tk.LabelFrame(stats_content, text=f"Due Within 7 Days ({len(due_soon)} tasks)", font=("Arial", 10, "bold"))
                due_frame.pack(fill="both", expand=True, pady=10)

                if due_soon:
                    # Create treeview for due soon tasks
                    columns = ("Title", "Due Date", "Priority", "Category")
                    due_tree = ttk.Treeview(due_frame, columns=columns, show="headings", height=8)
                    
                    due_tree.heading("Title", text="Title")
                    due_tree.heading("Due Date", text="Due Date")
                    due_tree.heading("Priority", text="Priority")
                    due_tree.heading("Category", text="Category")

                    due_tree.column("Title", width=200)
                    due_tree.column("Due Date", width=100)
                    due_tree.column("Priority", width=80)
                    due_tree.column("Category", width=100)

                    scrollbar = ttk.Scrollbar(due_frame, orient="vertical", command=due_tree.yview)
                    due_tree.configure(yscrollcommand=scrollbar.set)

                    due_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                    scrollbar.pack(side="right", fill="y", pady=5)

                    for task in due_soon:
                        values = (
                            task.get('title', ''),
                            task.get('due_date', ''),
                            task.get('priority', 'medium'),
                            task.get('category', '')
                        )
                        due_tree.insert('', 'end', values=values)
                else:
                    tk.Label(due_frame, text="No tasks due within 7 days", font=("Arial", 10, "italic"), fg="gray").pack(pady=20)

                # Refresh button
                tk.Button(stats_content, text="Refresh Statistics", command=refresh_statistics).pack(pady=10)

            except Exception as e:
                logger.error(f"Error refreshing statistics: {e}")
                tk.Label(stats_content, text=f"Error loading statistics: {e}", fg="red").pack(pady=20)

        # Initial load
        refresh_statistics()

    # Setup all tabs
    setup_active_tasks_tab()
    setup_completed_tasks_tab()
    setup_statistics_tab()

    # Store references for external access
    task_crud_window.active_frame = active_frame
    task_crud_window.completed_frame = completed_frame
    task_crud_window.stats_frame = stats_frame

    return task_crud_window

class TaskDialog(tk.Toplevel):
    """Dialog for adding or editing tasks."""
    
    def __init__(self, parent, user_id, task_data=None, on_save=None):
        super().__init__(parent)
        self.user_id = user_id
        self.task_data = task_data or {}
        self.on_save = on_save
        self.is_edit = bool(task_data)
        self.tags = self.load_tags()
        self.selected_tags = set(self.task_data.get('categories', [])) if 'categories' in self.task_data else set([self.task_data.get('category', '')] if self.task_data.get('category', '') else [])
        self.reminder_periods = self.task_data.get('reminder_periods', []) or []
        self.title("Edit Task" if self.is_edit else "Add New Task")
        self.geometry("850x900")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.setup_ui()
        self.bind('<Return>', lambda e: self.save_task())
        self.bind('<Escape>', lambda e: self.destroy())

    def load_tags(self):
        tags_file = os.path.join('data', 'users', self.user_id, 'tags.json')
        if os.path.exists(tags_file):
            try:
                with open(tags_file, 'r', encoding='utf-8') as f:
                    tags = json.load(f)
                if isinstance(tags, list):
                    return tags
            except Exception:
                pass
        return []

    def save_tags(self):
        tags_file = os.path.join('data', 'users', self.user_id, 'tags.json')
        try:
            with open(tags_file, 'w', encoding='utf-8') as f:
                json.dump(self.tags, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tags: {e}")

    def setup_ui(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        title_text = "Edit Task" if self.is_edit else "Add New Task"
        tk.Label(main_frame, text=title_text, font=("Arial", 14, "bold")).pack(pady=(0, 20))
        form_frame = tk.Frame(main_frame)
        form_frame.pack(fill="both", expand=True)
        # Title
        tk.Label(form_frame, text="Title *:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.title_var = tk.StringVar(value=self.task_data.get('title', ''))
        title_entry = tk.Entry(form_frame, textvariable=self.title_var, width=50)
        title_entry.pack(fill="x", pady=(0, 15))
        title_entry.focus_set()
        # Description
        tk.Label(form_frame, text="Description:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.description_text = tk.Text(form_frame, height=4, width=50)
        self.description_text.insert("1.0", self.task_data.get('description', ''))
        self.description_text.pack(fill="x", pady=(0, 15))
        # Due Date (always-visible Calendar)
        tk.Label(form_frame, text="Due Date:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        cal_frame = tk.Frame(form_frame)
        cal_frame.pack(anchor="w", pady=(0, 10))
        self.due_date_var = tk.StringVar(value=self.task_data.get('due_date', ''))
        self.due_calendar = Calendar(cal_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.due_calendar.pack()
        if self.due_date_var.get():
            try:
                self.due_calendar.selection_set(self.due_date_var.get())
            except Exception:
                pass
        # Due Time (ComboBoxes + AM/PM)
        tk.Label(form_frame, text="Due Time:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        due_time_frame = tk.Frame(form_frame)
        due_time_frame.pack(anchor="w", pady=(0, 15))
        hour_options = [''] + [f"{h:02d}" for h in range(1, 13)]
        minute_options = [''] + [f"{m:02d}" for m in range(0, 60, 5)]
        ampm_options = ['', 'AM', 'PM']
        due_time = self.task_data.get('due_time', '')
        due_hour, due_minute, due_ampm = '', '00', 'AM'
        if due_time:
            try:
                h, m = map(int, due_time.split(':'))
                due_ampm = 'AM' if h < 12 or h == 24 else 'PM'
                h12 = h % 12
                if h12 == 0: h12 = 12
                due_hour = f"{h12:02d}"
                due_minute = f"{m:02d}"
            except Exception:
                pass
        self.due_hour_var = tk.StringVar(value=due_hour)
        self.due_minute_var = tk.StringVar(value=due_minute)
        self.due_ampm_var = tk.StringVar(value=due_ampm)
        ttk.Combobox(due_time_frame, textvariable=self.due_hour_var, values=hour_options, width=3, state="readonly").pack(side=tk.LEFT)
        tk.Label(due_time_frame, text=":").pack(side=tk.LEFT)
        ttk.Combobox(due_time_frame, textvariable=self.due_minute_var, values=minute_options, width=3, state="readonly").pack(side=tk.LEFT)
        ttk.Combobox(due_time_frame, textvariable=self.due_ampm_var, values=ampm_options, width=3, state="readonly").pack(side=tk.LEFT)
        for val in ("AM", "PM"):
            tk.Radiobutton(due_time_frame, text=val, variable=self.due_ampm_var, value=val).pack(side=tk.LEFT)
        # Priority (Titlecase)
        tk.Label(form_frame, text="Priority:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        priority_val = self.task_data.get('priority')
        if priority_val and priority_val.lower() in ['low', 'medium', 'high']:
            priority_val = priority_val.capitalize()
        else:
            priority_val = ''  # Allow blank/none
        self.priority_var = tk.StringVar(value=priority_val)
        priority_combo = ttk.Combobox(form_frame, textvariable=self.priority_var, 
                                    values=['', 'Low', 'Medium', 'High'], state="readonly", width=15)
        priority_combo.pack(anchor="w", pady=(0, 15))
        # Multi-Tag UI
        tk.Label(form_frame, text="Tags:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.tag_bubble_frame = tk.Frame(form_frame)
        self.tag_bubble_frame.pack(fill="x", pady=(0, 5))
        self.render_tag_bubbles()
        tag_list_frame = tk.Frame(form_frame)
        tag_list_frame.pack(fill="x", pady=(0, 10))
        tag_listbox_frame = tk.Frame(tag_list_frame)
        tag_listbox_frame.pack(side=tk.LEFT, fill="y")
        tag_scrollbar = tk.Scrollbar(tag_listbox_frame, orient="vertical")
        self.tag_listbox = tk.Listbox(tag_listbox_frame, selectmode=tk.SINGLE, yscrollcommand=tag_scrollbar.set, height=5)
        tag_scrollbar.config(command=self.tag_listbox.yview)
        tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.refresh_tag_listbox()
        tag_btn_frame = tk.Frame(tag_list_frame)
        tag_btn_frame.pack(side=tk.LEFT, padx=5)
        tk.Button(tag_btn_frame, text="Add Tag", command=self.add_selected_tag).pack(fill="x")
        tk.Button(tag_btn_frame, text="New Tag", command=self.create_new_tag).pack(fill="x", pady=(5,0))
        # Reminder Periods Section (unchanged except for tag storage)
        tk.Label(form_frame, text="Reminder Time Periods:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.reminder_periods_frame = tk.Frame(form_frame)
        self.reminder_periods_frame.pack(fill="x", pady=(0, 10))
        self.render_reminder_periods()
        tk.Button(form_frame, text="Add New Reminder Period", command=self.add_reminder_period).pack(anchor="w", pady=(0, 10))
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        tk.Button(button_frame, text="Save", command=self.save_task).pack(side="right", padx=(5, 0))
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right")

    def render_tag_bubbles(self):
        for widget in self.tag_bubble_frame.winfo_children():
            widget.destroy()
        for tag in sorted(self.selected_tags):
            bubble = tk.Frame(self.tag_bubble_frame, bd=1, relief=tk.SOLID, bg="#e0e0e0", padx=6, pady=2)
            tk.Label(bubble, text=tag, bg="#e0e0e0").pack(side=tk.LEFT)
            tk.Button(bubble, text="×", command=lambda t=tag: self.remove_tag_bubble(t), bd=0, bg="#e0e0e0", fg="red", padx=2).pack(side=tk.LEFT)
            bubble.pack(side=tk.LEFT, padx=3, pady=2)

    def refresh_tag_listbox(self):
        self.tag_listbox.delete(0, tk.END)
        for tag in sorted([t for t in self.tags if t not in self.selected_tags]):
            self.tag_listbox.insert(tk.END, tag)

    def add_selected_tag(self):
        selection = self.tag_listbox.curselection()
        if selection:
            tag = self.tag_listbox.get(selection[0])
            self.selected_tags.add(tag)
            self.render_tag_bubbles()
            self.refresh_tag_listbox()

    def remove_tag_bubble(self, tag):
        """
        Remove a tag bubble from the task.
        
        Args:
            tag: Tag to remove from the task
        """
        if tag in self.task_data.get('tags', []):
            self.task_data['tags'].remove(tag)
            self.render_tag_bubbles()

    def create_new_tag(self):
        new_tag = simpledialog.askstring("Create New Tag", "Enter new tag name:")
        if new_tag and new_tag not in self.tags:
            self.tags.append(new_tag)
            self.save_tags()
            self.refresh_tag_listbox()

    def render_reminder_periods(self):
        """
        Render the reminder periods section of the task dialog.
        """
        # Clear existing reminder periods
        for widget in self.reminder_periods_frame.winfo_children():
            widget.destroy()

        # Render each reminder period
        for idx, period in enumerate(self.task_data.get('reminder_periods', [])):
            self.render_reminder_period_row(idx, period)

    def render_reminder_period_row(self, idx, period):
        row = tk.Frame(self.reminder_periods_frame)
        row.pack(fill="x", pady=2, expand=True)
        # Date
        tk.Label(row, text="Date:").pack(side=tk.LEFT)
        date_var = tk.StringVar(value=period.get('date', ''))
        date_entry = DateEntry(row, textvariable=date_var, width=10, date_pattern='yyyy-mm-dd')
        date_entry.pack(side=tk.LEFT, padx=(2, 5))
        # Start Time
        tk.Label(row, text="Start Time:").pack(side=tk.LEFT)
        start_hour_var = tk.StringVar(value='')
        start_minute_var = tk.StringVar(value='00')
        start_ampm_var = tk.StringVar(value='AM')
        if 'start_time' in period and period['start_time']:
            try:
                h, m = map(int, period['start_time'].split(':'))
                start_ampm_var.set('AM' if h < 12 or h == 24 else 'PM')
                h12 = h % 12
                if h12 == 0: h12 = 12
                start_hour_var.set(f"{h12:02d}")
                start_minute_var.set(f"{m:02d}")
            except Exception:
                pass
        hour_options = [''] + [f"{h:02d}" for h in range(1, 13)]
        minute_options = [''] + [f"{m:02d}" for m in range(0, 60, 5)]
        ampm_options = ['', 'AM', 'PM']
        ttk.Combobox(row, textvariable=start_hour_var, values=hour_options, width=3, state="readonly").pack(side=tk.LEFT)
        tk.Label(row, text=":").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=start_minute_var, values=minute_options, width=3, state="readonly").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=start_ampm_var, values=ampm_options, width=3, state="readonly").pack(side=tk.LEFT)
        for val in ("AM", "PM"):
            tk.Radiobutton(row, text=val, variable=start_ampm_var, value=val).pack(side=tk.LEFT)
        # End Time
        tk.Label(row, text="End Time:").pack(side=tk.LEFT, padx=(10, 0))
        end_hour_var = tk.StringVar(value='')
        end_minute_var = tk.StringVar(value='00')
        end_ampm_var = tk.StringVar(value='AM')
        if 'end_time' in period and period['end_time']:
            try:
                h, m = map(int, period['end_time'].split(':'))
                end_ampm_var.set('AM' if h < 12 or h == 24 else 'PM')
                h12 = h % 12
                if h12 == 0: h12 = 12
                end_hour_var.set(f"{h12:02d}")
                end_minute_var.set(f"{m:02d}")
            except Exception:
                pass
        ttk.Combobox(row, textvariable=end_hour_var, values=hour_options, width=3, state="readonly").pack(side=tk.LEFT)
        tk.Label(row, text=":").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=end_minute_var, values=minute_options, width=3, state="readonly").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=end_ampm_var, values=ampm_options, width=3, state="readonly").pack(side=tk.LEFT)
        for val in ("AM", "PM"):
            tk.Radiobutton(row, text=val, variable=end_ampm_var, value=val).pack(side=tk.LEFT)
        # No Active checkbox (just add/delete)
        # Delete button
        tk.Button(row, text="Delete", command=lambda idx=idx: self.delete_reminder_period(idx)).pack(side=tk.LEFT, padx=(10, 0))
        # Store variables for later retrieval
        period['__vars'] = {
            'date': date_var,
            'start_hour': start_hour_var,
            'start_minute': start_minute_var,
            'start_ampm': start_ampm_var,
            'end_hour': end_hour_var,
            'end_minute': end_minute_var,
            'end_ampm': end_ampm_var
        }

    def add_reminder_period(self):
        """
        Add a new reminder period to the task.
        """
        new_period = {
            'start_time': '09:00',
            'end_time': '17:00',
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        }
        self.task_data.setdefault('reminder_periods', []).append(new_period)
        self.render_reminder_periods()

    def delete_reminder_period(self, idx):
        """
        Delete a reminder period from the task.
        
        Args:
            idx: Index of the reminder period to delete
        """
        if 'reminder_periods' in self.task_data and idx < len(self.task_data['reminder_periods']):
            del self.task_data['reminder_periods'][idx]
            self.render_reminder_periods()

    def validate_dates(self, due_date, reminder_periods):
        """Validate dates and show confirmation dialogs if needed."""
        from datetime import datetime, date
        
        today = date.today()
        due_date_obj = None
        
        # Check if due date is in the past
        try:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            if due_date_obj < today:
                result = messagebox.askyesno(
                    "Past Due Date", 
                    f"The due date ({due_date}) is in the past.\n\nDo you want to continue anyway?"
                )
                if not result:
                    return False
        except Exception:
            pass  # Invalid date format, let it pass
        
        # Check reminder periods
        for i, period in enumerate(reminder_periods):
            try:
                reminder_date = datetime.strptime(period['date'], '%Y-%m-%d').date()
                
                # Check if reminder date is in the past
                if reminder_date < today:
                    result = messagebox.askyesno(
                        "Past Reminder Date", 
                        f"Reminder period {i+1} date ({period['date']}) is in the past.\n\nDo you want to continue anyway?"
                    )
                    if not result:
                        return False
                
                # Check if reminder date is after due date (only if due date is valid)
                if due_date_obj and reminder_date > due_date_obj:
                    result = messagebox.askyesno(
                        "Reminder After Due Date", 
                        f"Reminder period {i+1} date ({period['date']}) is after the due date ({due_date}).\n\nDo you want to continue anyway?"
                    )
                    if not result:
                        return False
                        
            except Exception:
                pass  # Invalid date format, let it pass
        
        return True

    def save_task(self, *_):
        try:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Title is required.")
                return
            due_date_val = self.due_calendar.get_date()
            if hasattr(due_date_val, 'strftime'):
                due_date = due_date_val.strftime('%Y-%m-%d')
            else:
                due_date = str(due_date_val)
            # Only save due_time if both hour and minute are set and not blank
            due_time = None
            hour = self.due_hour_var.get().strip()
            minute = self.due_minute_var.get().strip()
            if hour:
                try:
                    h = int(hour)
                    m = int(minute)
                    if self.due_ampm_var.get() == 'PM' and h != 12:
                        h += 12
                    if self.due_ampm_var.get() == 'AM' and h == 12:
                        h = 0
                    due_time = f"{h:02d}:{m:02d}"
                except Exception:
                    due_time = None
            priority = self.priority_var.get().lower() if self.priority_var.get() else None
            tags = sorted(self.selected_tags)
            # Only save reminder_periods if at least one is present
            reminder_periods = []
            for period in self.reminder_periods:
                vars = period.get('__vars', {})
                date = vars['date'].get().strip()
                sh = vars['start_hour'].get().strip()
                sm = vars['start_minute'].get().strip()
                eh = vars['end_hour'].get().strip()
                em = vars['end_minute'].get().strip()
                # Only save if both start and end hour are set (minute/ampm can default)
                if date and sh and eh:
                    try:
                        sh24 = int(sh)
                        sm = int(sm) if sm else 0
                        eh24 = int(eh)
                        em = int(em) if em else 0
                        if vars['start_ampm'].get() == 'PM' and sh24 != 12:
                            sh24 += 12
                        if vars['start_ampm'].get() == 'AM' and sh24 == 12:
                            sh24 = 0
                        if vars['end_ampm'].get() == 'PM' and eh24 != 12:
                            eh24 += 12
                        if vars['end_ampm'].get() == 'AM' and eh24 == 12:
                            eh24 = 0
                        reminder_periods.append({
                            'date': date,
                            'start_time': f"{sh24:02d}:{sm:02d}",
                            'end_time': f"{eh24:02d}:{em:02d}"
                        })
                    except Exception:
                        continue
            task_data = {
                'title': title,
                'description': self.description_text.get("1.0", tk.END).strip(),
                'due_date': due_date,
                'priority': priority,
                'categories': tags
            }
            if due_time:
                task_data['due_time'] = due_time
            if reminder_periods:
                task_data['reminder_periods'] = reminder_periods
            
            # Validate dates and get user confirmation if needed
            if not self.validate_dates(due_date, reminder_periods):
                return  # User cancelled
                
            if self.is_edit:
                task_id = self.task_data.get('task_id')
                if update_task(self.user_id, task_id, task_data):
                    messagebox.showinfo("Success", "Task updated successfully!")
                    if self.on_save:
                        self.on_save()
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update task.")
            else:
                task_id = create_task(
                    self.user_id,
                    task_data['title'],
                    task_data['description'],
                    task_data['due_date'],
                    task_data.get('due_time'),
                    task_data['priority'],
                    ','.join(task_data['categories']),
                    reminder_periods if reminder_periods else None
                )
                if task_id:
                    messagebox.showinfo("Success", "Task created successfully!")
                    if self.on_save:
                        self.on_save()
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to create task.")
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            messagebox.showerror("Error", f"Failed to save task: {e}")

def add_task_dialog(parent, user_id, on_save=None):
    """Open dialog to add a new task."""
    dialog = TaskDialog(parent, user_id, on_save=on_save)
    dialog.wait_window()

def edit_selected_task(parent, user_id, on_save=None):
    """Edit the selected task in the active tasks treeview."""
    try:
        active_tree = parent.active_tree
        selection = active_tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return
        
        # Get the selected item
        item = selection[0]
        task_id = active_tree.item(item, "tags")[0]
        
        # Get task data
        task_data = get_task_by_id(user_id, task_id)
        if not task_data:
            messagebox.showerror("Error", "Task not found.")
            return
        
        # Open edit dialog
        dialog = TaskDialog(parent, user_id, task_data, on_save=on_save)
        dialog.wait_window()
        
    except Exception as e:
        logger.error(f"Error editing task: {e}")
        messagebox.showerror("Error", f"Failed to edit task: {e}")

def complete_selected_task(parent, user_id, on_save=None):
    """Complete the selected task in the active tasks treeview."""
    try:
        active_tree = parent.active_tree
        selection = active_tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to complete.")
            return
        
        # Get the selected item
        item = selection[0]
        task_id = active_tree.item(item, "tags")[0]
        
        # Confirm completion
        task_data = get_task_by_id(user_id, task_id)
        if not task_data:
            messagebox.showerror("Error", "Task not found.")
            return
        
        result = messagebox.askyesno("Complete Task", 
                                   f"Are you sure you want to mark '{task_data.get('title', '')}' as completed?")
        if result:
            if complete_task(user_id, task_id):
                messagebox.showinfo("Success", "Task marked as completed!")
                if on_save:
                    on_save()
            else:
                messagebox.showerror("Error", "Failed to complete task.")
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        messagebox.showerror("Error", f"Failed to complete task: {e}")

def delete_selected_task(parent, user_id, on_save=None):
    """Delete the selected task in the active tasks treeview."""
    try:
        active_tree = parent.active_tree
        selection = active_tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return
        
        # Get the selected item
        item = selection[0]
        task_id = active_tree.item(item, "tags")[0]
        
        # Confirm deletion
        task_data = get_task_by_id(user_id, task_id)
        if not task_data:
            messagebox.showerror("Error", "Task not found.")
            return
        
        result = messagebox.askyesno("Delete Task", 
                                   f"Are you sure you want to delete '{task_data.get('title', '')}'?\n\nThis action cannot be undone.")
        if result:
            if delete_task(user_id, task_id):
                messagebox.showinfo("Success", "Task deleted successfully!")
                if on_save:
                    on_save()
            else:
                messagebox.showerror("Error", "Failed to delete task.")
        
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        messagebox.showerror("Error", f"Failed to delete task: {e}")

@handle_errors("setting up personalization management window")
def setup_personalization_management_window(parent, user_id):
    """Opens a window for managing user personalization settings."""
    if not user_id:
        logger.error("setup_personalization_management_window called with None user_id")
        messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
        return None
    
    window_attr_name = "_personalization_management_window"
    personalization_window = getattr(parent, window_attr_name, None)
    if personalization_window is None or not personalization_window.winfo_exists():
        personalization_window = Toplevel(parent)
        personalization_window.title("Personalization Management")
        setattr(parent, window_attr_name, personalization_window)
        
        # Set window size
        personalization_window.geometry("850x750")
        personalization_window.minsize(700, 600)
        
        # Define what happens when the window is closed
        personalization_window.protocol("WM_DELETE_WINDOW", lambda: save_geometry_and_close(personalization_window, parent, window_attr_name))
    else:
        for widget in personalization_window.winfo_children():
            widget.destroy()

    # Create main frame
    main_frame = ttk.Frame(personalization_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Title
    title_label = ttk.Label(main_frame, text="Personalization Management", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Description
    description_label = ttk.Label(main_frame, 
                                 text="Manage user personalization settings including pronouns, health information, interests, and more.",
                                 font=("Arial", 10), wraplength=600)
    description_label.pack(pady=(0, 20))
    
    # Button to open personalization dialog
    def open_personalization_dialog():
        try:
            from ui.dialogs.user_profile_dialog import open_personalization_dialog
            from core.user_management import get_user_data, update_user_context
            
            def on_personalization_save(data):
                """Callback when personalization data is saved."""
                try:
                    # Update the context data with personalization fields
                    update_user_context(user_id, data)
                    messagebox.showinfo("Success", "Personalization data updated successfully!")
                    logger.info(f"Personalization data updated for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to save personalization data: {e}")
                    messagebox.showerror("Error", f"Failed to save personalization data: {str(e)}")
            
            # Load existing data to pass to dialog
            context_result = get_user_data(user_id, 'context')
            existing_data = context_result.get('context', {})
            open_personalization_dialog(personalization_window, user_id, on_personalization_save, existing_data)
            
        except Exception as e:
            logger.error(f"Error opening personalization dialog: {e}")
            messagebox.showerror("Error", f"Failed to open personalization dialog: {str(e)}")
    
    # Create button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    ttk.Button(button_frame, text="Edit Personalization Settings", 
              command=open_personalization_dialog,
              style="Accent.TButton").pack(pady=10)
    
    # Add some spacing
    ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=20)
    
    # Show current personalization summary
    try:
        from core.user_management import get_user_data
        
        context_result = get_user_data(user_id, 'context')
        personalization_data = context_result.get('context', {})
        if personalization_data:
            summary_frame = ttk.LabelFrame(main_frame, text="Current Personalization Summary")
            summary_frame.pack(fill=tk.X, pady=10)
            
            summary_text = tk.Text(summary_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
            summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create summary content
            summary_content = []
            
            # Basic info
            if personalization_data.get("pronouns"):
                summary_content.append(f"Pronouns: {', '.join(personalization_data['pronouns'])}")
            
            if personalization_data.get("date_of_birth"):
                summary_content.append(f"Date of Birth: {personalization_data['date_of_birth']}")
            
            if personalization_data.get("timezone"):
                summary_content.append(f"Timezone: {personalization_data['timezone']}")
            
            # Health info
            if personalization_data.get("health_conditions"):
                summary_content.append(f"\nHealth Conditions: {', '.join(personalization_data['health_conditions'])}")
            
            if personalization_data.get("medications_treatments"):
                summary_content.append(f"Medications/Treatments: {', '.join(personalization_data['medications_treatments'])}")
            
            if personalization_data.get("reminders_needed"):
                summary_content.append(f"Reminders Needed: {', '.join(personalization_data['reminders_needed'])}")
            
            # Loved ones
            if personalization_data.get("loved_ones"):
                summary_content.append(f"\nLoved Ones:")
                for loved_one in personalization_data["loved_ones"]:
                    name = loved_one.get("name", "Unknown")
                    type_val = loved_one.get("type", "Unknown")
                    relationships = loved_one.get("relationships", [])
                    rel_text = f" ({', '.join(relationships)})" if relationships else ""
                    summary_content.append(f"  • {name} ({type_val}){rel_text}")
            
            # Interests
            if personalization_data.get("interests"):
                summary_content.append(f"\nInterests: {', '.join(personalization_data['interests'])}")
            
            if personalization_data.get("activities_for_encouragement"):
                summary_content.append(f"Activities for Encouragement: {', '.join(personalization_data['activities_for_encouragement'])}")
            
            # Notes
            if personalization_data.get("notes_for_ai"):
                summary_content.append(f"\nNotes for AI: {', '.join(personalization_data['notes_for_ai'])}")
            
            # Goals
            if personalization_data.get("goals"):
                summary_content.append(f"\nGoals: {', '.join(personalization_data['goals'])}")
            
            # Update text widget
            summary_text.config(state=tk.NORMAL)
            summary_text.delete(1.0, tk.END)
            if summary_content:
                summary_text.insert(1.0, '\n'.join(summary_content))
            else:
                summary_text.insert(1.0, "No personalization data has been set yet.\n\nClick 'Edit Personalization Settings' to get started.")
            summary_text.config(state=tk.DISABLED)
            
        else:
            # No personalization data
            no_data_label = ttk.Label(main_frame, 
                                     text="No personalization data has been set yet.\n\nClick 'Edit Personalization Settings' to get started.",
                                     font=("Arial", 10), justify=tk.CENTER)
            no_data_label.pack(pady=20)
            
    except Exception as e:
        logger.error(f"Error loading personalization summary: {e}")
        error_label = ttk.Label(main_frame, 
                               text=f"Error loading personalization data: {str(e)}",
                               font=("Arial", 10), foreground="red")
        error_label.pack(pady=20)