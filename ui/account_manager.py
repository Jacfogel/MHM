# account_manager.py - User account content and settings management

import tkinter as tk
from tkinter import messagebox, Toplevel, Button, Entry, Checkbutton, IntVar, Frame, font, ttk
import uuid
from datetime import datetime
import re

from core.file_operations import load_json_data, save_json_data, determine_file_path, get_user_file_path
from core.user_management import load_user_info_data, save_user_info_data
from core.message_management import edit_message, add_message, delete_message, get_message_categories
from core.schedule_management import (
    get_schedule_time_periods, delete_schedule_period, set_schedule_period_active,
    edit_schedule_period, add_schedule_period, clear_schedule_periods_cache
)
from core.validation import title_case
from core.service_utilities import InvalidTimeFormatError
from core.logger import get_logger
from user.user_context import UserContext
from core.checkin_analytics import checkin_analytics
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
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
        
        # Set a better default size for the schedule window
        default_geometry = "600x500"
        
        # Apply saved geometry if it exists, otherwise use default
        if hasattr(parent, f"{window_attr_name}_window_geometry"):
            geometry = getattr(parent, f"{window_attr_name}_window_geometry")
            logger.debug(f"Applying saved geometry: {geometry}")
            view_schedule_window.geometry(geometry)
        else:
            view_schedule_window.geometry(default_geometry)
            
        # Set minimum size to prevent content from being cut off
        view_schedule_window.minsize(500, 400)
    
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
    data = load_json_data(determine_file_path('messages', f'{category}/{user_id}'))
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
        
        self.data = load_json_data(determine_file_path('messages', f'{category}/{user_id}'))
        if not self.data:
            self.data = {"messages": []}

        try:
            self.data = load_json_data(determine_file_path('messages', f'{category}/{user_id}'))
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

        self.build_ui()

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        tk.Label(self, text="Message:").pack(anchor='w')
        self.message_entry = tk.Entry(self, width=40)
        self.message_entry.pack(fill='x', padx=5, pady=2)
        self.message_entry.insert(0, self.message_data.get('message', ''))

        # --- Days section (Sunday first) ---
        days_frame = tk.LabelFrame(self, text="Days:", font=("Arial", 10, "bold"))
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
            cb = Checkbutton(days_frame, text=day, variable=var, font=day_font, fg="black", activeforeground="black", selectcolor="white")
            cb.pack(anchor='w')
            self.day_checkboxes[day] = cb
        
        # Apply the correct state based on whether all days are selected
        if all_days_selected:
            self.handle_all_days_toggle()

        # --- Time periods section (chronological order) ---
        periods_frame = tk.LabelFrame(self, text="Time Periods:", font=("Arial", 10, "bold"))
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
            checkbox = Checkbutton(periods_frame, text=f"{title_case(period)} ({self.time_periods[period]['start']} - {self.time_periods[period]['end']})", variable=var, font=period_font, fg="black", activeforeground="black", selectcolor="white")
            checkbox.pack(anchor='w')
            self.period_checkboxes[period] = checkbox
        
        # Apply the correct state based on whether all periods are selected
        if all_periods_selected:
            self.handle_all_periods_toggle()

        tk.Button(self, text="Save Message", command=self.save_message).pack(pady=8)

    @handle_errors("saving message")
    def save_message(self):
        """Saves the message to the JSON file."""
        # Days
        if self.all_days_var.get() == 1:
            selected_days = ['ALL']
        else:
            selected_days = [day for day, var in self.days_vars.items() if var.get() == 1]
        # Periods
        if self.all_periods_var.get() == 1:
            selected_periods = ['ALL']
        else:
            selected_periods = [period for period, var in self.time_period_vars.items() if var.get() == 1]

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
                cb.config(state='disabled')
            else:
                self.days_vars[day].set(0)
                cb.config(state='normal')

    def handle_all_periods_toggle(self):
        all_selected = self.all_periods_var.get() == 1
        for period, cb in self.period_checkboxes.items():
            if all_selected:
                self.time_period_vars[period].set(1)
                cb.config(state='disabled')
            else:
                self.time_period_vars[period].set(0)
                cb.config(state='normal')

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
        data = load_json_data(determine_file_path('messages', f'{category}/{user_id}'))
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
    tree = ttk.Treeview(view_messages_window, columns=columns, show="headings")
    tree.pack(fill="both", expand=True, padx=20, pady=20)

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
        """Deletes the selected message from the Treeview and data file."""
        user_id = UserContext().get_user_id()
        if not user_id:
            logger.error("delete_message_local called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a message to delete.")
                return

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
                    tree.delete(selected_item)
                    update_undo_delete_message_button_state()
                    messagebox.showinfo("Success", "Message deleted successfully.")
                else:
                    messagebox.showerror("Error", "Message not found in current data.")
            else:
                messagebox.showerror("Error", "Invalid message ID.")
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to delete message: {e}")

    def edit_message_local():
        """Edits the selected message in the Treeview and updates the data file."""
        user_id = UserContext().get_user_id()  # Get the user ID
        if not user_id:
            logger.error("edit_message_local called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a message to edit.")
                return

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
            values = [msg.get('message', 'N/A'), msg['message_id']]
            for day in days:
                values.append('✔' if day in msg.get('days', []) else '')
            for period in periods:
                values.append('✔' if period in msg.get('time_periods', []) else '')
            tree.insert("", tk.END, values=values)

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

    # Right side buttons
    right_button_frame = Frame(button_frame)
    right_button_frame.pack(side="right", padx=5)

    delete_button = Button(right_button_frame, text="Delete Message", command=delete_message_local)
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
                user_info = load_user_info_data(user_id) or {}
                schedules = user_info.setdefault('schedules', {})
                category_schedules = schedules.setdefault(category, {})
                # Restore the period with its original data, including active status
                category_schedules[period] = times  # Use the data from the stack
                save_user_info_data(user_info, user_id)
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
    settings_window.geometry("450x500")
    
    try:
        # Load preferences and profile separately for accuracy
        user_data = load_user_info_data(user_id)
        if not user_data:
            user_data = {}
        
        # Ensure preferences structure exists
        if 'preferences' not in user_data:
            user_data['preferences'] = {}
        
        preferences = user_data.get('preferences', {})
        profile = load_user_info_data(user_id)
        current_service = preferences.get('messaging_service', 'email')
        current_email = profile.get('email', '')
        current_phone = profile.get('phone', '')
        current_discord_id = preferences.get('discord_user_id', '')
        
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
                preferences['messaging_service'] = new_service
                preferences['discord_user_id'] = new_discord_id
                profile['email'] = new_email
                profile['phone'] = new_phone
                # Save both preferences and profile
                save_json_data(preferences, get_user_file_path(user_id, 'preferences'))
                save_json_data(profile, get_user_file_path(user_id, 'profile'))
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
        user_data = load_user_info_data(user_id)
        if not user_data:
            user_data = {}
        
        # Ensure preferences structure exists
        if 'preferences' not in user_data:
            user_data['preferences'] = {}
        
        preferences = user_data.get('preferences', {})
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
                
                # Update user preferences
                if 'preferences' not in preferences:
                    preferences['preferences'] = {}
                preferences['preferences']['categories'] = selected_categories
                
                # Save changes
                save_user_info_data(preferences, user_id)
                
                # Create message files for new categories
                for category in added_categories:
                    # TODO: Investigate and fix create_user_message_file function
                    # create_user_message_file(user_id, category)
                    logger.warning(f"create_user_message_file not implemented - skipping creation for category {category}")
                
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
    checkin_window.geometry("500x400")
    checkin_window.resizable(True, True)

    try:
        user_data = load_user_info_data(user_id)
        if not user_data:
            user_data = {}
        
        # Ensure preferences structure exists
        if 'preferences' not in user_data:
            user_data['preferences'] = {}
        
        preferences = user_data.get('preferences', {})
        current_checkin_prefs = preferences.get('checkins', {})
        # Default check-in preferences if none exist
        if not current_checkin_prefs:
            current_checkin_prefs = {
                "enabled": False,
                "frequency": "daily",
                "questions": {}
            }
        
        tk.Label(checkin_window, text="Check-in Settings", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Enable/disable check-ins
        enabled_frame = tk.Frame(checkin_window)
        enabled_frame.pack(fill="x", padx=20, pady=10)
        
        checkin_enabled_var = tk.IntVar(value=1 if current_checkin_prefs.get("enabled", False) else 0)
        checkin_checkbox = tk.Checkbutton(enabled_frame, text="Enable check-ins", 
                                        variable=checkin_enabled_var, 
                                        font=("Arial", 12, "bold"))
        checkin_checkbox.pack(side="left")
        
        if current_checkin_prefs.get("enabled", False):
            status_label = tk.Label(enabled_frame, text="✓ Currently Active", fg="green", font=("Arial", 10))
        else:
            status_label = tk.Label(enabled_frame, text="○ Currently Inactive", fg="gray", font=("Arial", 10))
        status_label.pack(side="left", padx=(20, 0))
        
        # Frequency selection
        frequency_frame = tk.LabelFrame(checkin_window, text="Frequency", font=("Arial", 10, "bold"))
        frequency_frame.pack(fill="x", padx=20, pady=10)
        
        frequency_var = tk.StringVar(value=current_checkin_prefs.get("frequency", "daily"))
        
        for freq in ["daily", "weekly", "none", "custom"]:
            rb = tk.Radiobutton(frequency_frame, text=freq.title(), variable=frequency_var, value=freq)
            rb.pack(side="left", padx=10, pady=5)
        
        # Add explanatory text for frequency options
        freq_help_frame = tk.Frame(frequency_frame)
        freq_help_frame.pack(fill="x", pady=(5, 0))
        
        # Break the text into multiple lines for better readability
        help_text = (
            "Daily: Prompted once per day\n"
            "Weekly: Prompted once per week\n" 
            "None: Manual only (/checkin command)\n"
            "Custom: Set your own schedule"
        )
        tk.Label(freq_help_frame, 
                text=help_text, 
                font=("Arial", 8, "italic"), fg="gray", justify=tk.LEFT).pack(anchor="w")
        
        # Questions section
        questions_frame = tk.LabelFrame(checkin_window, text="Questions to Include", font=("Arial", 10, "bold"))
        questions_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        
        # Select All / Deselect All buttons (above questions)
        control_frame = tk.Frame(questions_frame)
        control_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Default question definitions with recommended defaults marked
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
        
        # Define select functions and smart toggle button
        def select_default():
            """Select only the recommended default questions"""
            for question_key, var in question_vars.items():
                var.set(1 if default_questions[question_key]['default'] else 0)
        
        def toggle_all():
            """Smart toggle: select all if not all selected, deselect all if all selected"""
            # Check if all are currently selected
            all_selected = all(var.get() == 1 for var in question_vars.values())
            
            if all_selected:
                # Deselect all
                for var in question_vars.values():
                    var.set(0)
                toggle_button.config(text="Select All")
            else:
                # Select all
                for var in question_vars.values():
                    var.set(1)
                toggle_button.config(text="Deselect All")
        
        def update_toggle_button_text():
            """Update the toggle button text based on current selection state"""
            if not question_vars:  # If question_vars is empty, can't check
                return
            all_selected = all(var.get() == 1 for var in question_vars.values())
            toggle_button.config(text="Deselect All" if all_selected else "Select All")
        
        # Add the buttons
        Button(control_frame, text="Select Default", command=select_default, width=12).pack(side="left", padx=(0, 5))
        toggle_button = Button(control_frame, text="Select All", command=toggle_all, width=12)
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
                # Build new check-in preferences
                new_checkin_prefs = {
                    "enabled": checkin_enabled_var.get() == 1,
                    "frequency": frequency_var.get(),
                    "questions": {}
                }
                
                # Collect question preferences
                for question_key, var in question_vars.items():
                    new_checkin_prefs["questions"][question_key] = {
                        "enabled": var.get() == 1,
                        "label": default_questions[question_key]['label']
                    }
                
                # Check for changes by comparing with current settings
                current_enabled = current_checkin_prefs.get("enabled", False)
                current_frequency = current_checkin_prefs.get("frequency", "daily")
                current_questions_dict = current_checkin_prefs.get("questions", {})
                
                # Compare enabled status
                enabled_changed = new_checkin_prefs["enabled"] != current_enabled
                
                # Compare frequency 
                frequency_changed = new_checkin_prefs["frequency"] != current_frequency
                
                # Compare questions
                questions_changed = False
                for question_key, new_data in new_checkin_prefs["questions"].items():
                    current_data = current_questions_dict.get(question_key, {})
                    current_question_enabled = current_data.get("enabled", default_questions[question_key]['default'])
                    if new_data["enabled"] != current_question_enabled:
                        questions_changed = True
                        break
                
                # If no changes, show appropriate message
                if not (enabled_changed or frequency_changed or questions_changed):
                    messagebox.showinfo("No Changes", "No changes were made to check-in settings.")
                    logger.info(f"No changes made to check-in settings for user {user_id}")
                    checkin_window.destroy()
                    return
                
                # Load full user data to preserve categories and schedules
                user_data = load_user_info_data(user_id)
                if not user_data:
                    user_data = {}
                
                # Ensure preferences structure exists
                if 'preferences' not in user_data:
                    user_data['preferences'] = {}
                
                # Update only the check-in preferences
                user_data['preferences']['checkins'] = new_checkin_prefs
                
                # Save changes
                save_user_info_data(user_data, user_id)
                
                # Show confirmation with details of what changed
                enabled_count = sum(1 for var in question_vars.values() if var.get() == 1)
                status = "enabled" if new_checkin_prefs["enabled"] else "disabled"
                frequency = new_checkin_prefs["frequency"]
                
                change_details = []
                if enabled_changed:
                    change_details.append(f"Check-ins {status}")
                if frequency_changed:
                    change_details.append(f"Frequency: {frequency.title()}")
                if questions_changed:
                    change_details.append(f"Questions: {enabled_count} selected")
                
                message = "Check-in settings updated successfully!\n\n" + "\n".join(change_details)
                
                logger.info(f"Updated check-in settings for user {user_id}: enabled={new_checkin_prefs['enabled']}, frequency={frequency}, questions={enabled_count}")
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