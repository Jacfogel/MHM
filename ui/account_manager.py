# account_manager.py - User account content and settings management

import tkinter as tk
from tkinter import messagebox, Toplevel, Button, Entry, Checkbutton, IntVar, Frame, font, ttk
import uuid

import core.utils
from core.logger import get_logger
from user.user_context import UserContext

logger = get_logger(__name__)

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
        view_messages_window.title(f"Edit Messages for {core.utils.title_case(category)}")
        view_messages_window.category = category
        setattr(parent, window_attr_name, view_messages_window)
    else:
        for widget in view_messages_window.winfo_children():
            widget.destroy()

    load_and_display_messages(view_messages_window, category)

def setup_view_edit_schedule_window(parent, category, scheduler_manager):
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
        view_schedule_window.title(f"Edit Schedule for {core.utils.title_case(category)}")
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

def add_message_dialog(parent, category):
    """Opens a dialog to add a message to the specified category."""
    user_id = UserContext().get_user_id()
    try:
        data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{category}/{user_id}'))
        if data is None:
            raise ValueError("Failed to load message data.")
    except Exception as e:
        logger.error(f"Error loading message data for category {category}: {e}", exc_info=True)
        messagebox.showerror("Error", "Failed to load message data. Please check the data source.")
        return

    try:
        dialog = MessageDialog(parent, category, data=data)
        dialog.grab_set()
        dialog.geometry("304x521+100+100")
        dialog.mainloop()
    except Exception as e:
        logger.error(f"Error opening message dialog for category {category}: {e}", exc_info=True)
        messagebox.showerror("Error", "Failed to open the message dialog. Please try again.")

def save_geometry_and_close(window, parent, window_attr_name):
    """Save the window's geometry and then close it."""
    geometry = window.geometry()
    setattr(parent, f"{window_attr_name}_window_geometry", geometry)
    logger.debug(f"Saving geometry for {window_attr_name}: {geometry}")
    window.destroy()

def refresh_window(window, setup_func, parent, category, scheduler_manager):
    """Refreshes the given window by re-running the setup function."""
    setup_func(parent, category, scheduler_manager)

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
        
        try:
            self.data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{category}/{user_id}'))
            if not self.data:
                self.data = {"messages": []}
        except Exception as e:
            logger.error(f"Error loading data for MessageDialog: {e}", exc_info=True)
            messagebox.showerror("Error", "Failed to load message data.")
            self.destroy()
            return

        self.days_vars = {day: IntVar(value=day in self.message_data.get('days', [])) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
        self.time_periods = core.utils.get_schedule_time_periods(user_id, self.category)
        self.time_period_vars = {period: IntVar(value=period in self.message_data.get('time_periods', [])) for period in self.time_periods}
        self.select_all_font = font.Font(weight="normal")
        self.select_all_color = "#555555"
       
        self.build_ui()  
        
    def build_ui(self):
        """Build the UI for the message dialog."""
        tk.Label(self, text="Message:").pack()
        self.message_entry = Entry(self, width=50)
        self.message_entry.insert(0, self.message_data.get('message', ''))
        self.message_entry.pack(pady=5)

        self.build_day_checkboxes()
        self.build_time_period_checkboxes()

        save_button = Button(self, text="Save Message", command=self.save_message)
        save_button.pack(pady=10)

        self.message_entry.bind("<Return>", lambda event: self.save_message())
        
    def build_day_checkboxes(self):
        """Build checkboxes for selecting days."""
        tk.Label(self, text="Select days:").pack()
        self.all_days_var = IntVar(value=all(var.get() for var in self.days_vars.values()))
        self.all_days_label = Checkbutton(self, text="Select All Days", variable=self.all_days_var, command=self.toggle_all_days, font=self.select_all_font, fg=self.select_all_color)
        self.all_days_label.pack(anchor='w')        
        for day, var in self.days_vars.items():
            Checkbutton(self, text=day, variable=var).pack(anchor='w')

    def build_time_period_checkboxes(self):
        """Build checkboxes for selecting time periods."""
        tk.Label(self, text="Select time periods:").pack()
        self.all_periods_var = IntVar(value=all(var.get() for var in self.time_period_vars.values()))
        self.all_periods_label = Checkbutton(self, text="Select All Periods", variable=self.all_periods_var, command=self.toggle_all_periods, font=self.select_all_font, fg=self.select_all_color)
        self.all_periods_label.pack(anchor='w')        
        for period, var in self.time_period_vars.items():
            frame = Frame(self)
            frame.pack(fill='x', expand=True)
            Checkbutton(frame, text=f"{core.utils.title_case(period)} ({self.time_periods[period]['start']} - {self.time_periods[period]['end']})", variable=var).pack(side='left')
            
    def toggle_all_days(self):
        """Toggle the selection of all days."""
        is_selected = self.all_days_var.get()
        for var in self.days_vars.values():
            var.set(is_selected)

    def toggle_all_periods(self):
        """Toggle the selection of all periods."""
        is_selected = self.all_periods_var.get()
        for var in self.time_period_vars.values():
            var.set(is_selected)
            
    def save_message(self):
        """Saves the message to the JSON file."""
        selected_days = [day for day, var in self.days_vars.items() if var.get() == 1]
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

        user_id = UserContext().get_user_id()
        if not user_id:
            logger.error("save_message called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            if self.index is not None:
                # Editing existing message
                self.data['messages'][self.index] = message_data
                core.utils.edit_message(user_id, self.category, self.index, message_data)
                target_index = self.index
                logger.debug(f"Edited message at index {self.index} for category {self.category}")
            else:
                # Adding new message
                core.utils.add_message(user_id, self.category, message_data)
                # Don't manually update self.data here - let the refresh handle it
                # Get the new target index by reloading the data
                updated_data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{self.category}/{user_id}'))
                target_index = len(updated_data.get('messages', [])) - 1 if updated_data else 0
                logger.debug(f"Added new message for category {self.category}, target index: {target_index}")

        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save message: {e}")
            return

        messagebox.showinfo("Message Saved", "Your message has been saved successfully.")
        self.refresh_open_treeviews(self.category, target_index)
        self.destroy()
        
    def refresh_open_treeviews(self, category, target_index=None):
        """Refresh all open treeviews showing messages for the given category."""
        user_id = UserContext().get_user_id()
        if not user_id:
            logger.error("refresh_open_treeviews called with None user_id")
            return
        
        logger.debug(f"Refreshing treeviews for category {category}, target_index: {target_index}")
        
        # Check if the parent window itself has a tree and category (direct case)
        if hasattr(self.parent, 'category') and self.parent.category == category:
            if hasattr(self.parent, 'tree') and self.parent.tree is not None:
                try:
                    if self.parent.tree.winfo_exists():
                        logger.debug(f"Found direct parent treeview for category {category}")
                        self._refresh_single_treeview(self.parent, category, user_id, target_index)
                except tk.TclError:
                    logger.debug("Parent tree widget no longer exists")
        
        # Also check children of the parent (for cases where dialog is opened from a different parent)
        for window in self.parent.winfo_children():
            if isinstance(window, tk.Toplevel) and hasattr(window, 'category') and window.category == category:
                if hasattr(window, 'tree') and window.tree is not None:
                    try:
                        if window.tree.winfo_exists():
                            logger.debug(f"Found child treeview for category {category}")
                            self._refresh_single_treeview(window, category, user_id, target_index)
                    except tk.TclError:
                        logger.debug("Child tree widget no longer exists")
        
        # Finally, check if the parent's parent has any relevant windows (for nested cases)
        if hasattr(self.parent, 'master') and self.parent.master:
            for window in self.parent.master.winfo_children():
                if isinstance(window, tk.Toplevel) and hasattr(window, 'category') and window.category == category:
                    if hasattr(window, 'tree') and window.tree is not None:
                        try:
                            if window.tree.winfo_exists():
                                logger.debug(f"Found master's child treeview for category {category}")
                                self._refresh_single_treeview(window, category, user_id, target_index)
                        except tk.TclError:
                            logger.debug("Master's child tree widget no longer exists")
    
    def _refresh_single_treeview(self, window, category, user_id, target_index):
        """Helper method to refresh a single treeview window."""
        try:
            # Clear existing items
            for item in window.tree.get_children():
                window.tree.delete(item)
            
            # Reload data from file to ensure we have the latest version
            data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{category}/{user_id}'))
            if data is not None:
                messages = data.get('messages', [])
                window.messages = messages  # Update the messages list
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                periods = list(core.utils.get_schedule_time_periods(user_id, category).keys())
                
                for i, msg in enumerate(messages):
                    values = [msg.get('message', 'N/A'), msg['message_id']]
                    for day in days:
                        values.append('✔' if day in msg.get('days', []) else '')
                    for period in periods:
                        values.append('✔' if period in msg.get('time_periods', []) else '')
                    item = window.tree.insert("", tk.END, values=values)
                    
                    # Highlight and scroll to the target message if specified
                    if target_index is not None and i == target_index:
                        window.tree.selection_set(item)
                        window.tree.see(item)
                        
                logger.debug(f"Successfully refreshed treeview for category {category} with {len(messages)} messages")
            else:
                logger.warning(f"No data found for category {category}")
        except Exception as e:
            logger.error(f"Error refreshing treeview: {e}", exc_info=True)

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
        data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{category}/{user_id}'))
        messages = data.get('messages', []) if data else []
    except Exception as e:
        logger.error(f"Error loading messages for category {category}: {e}", exc_info=True)
        messagebox.showerror("Error", "Failed to load messages. Please try again.")
        return

    # Initialize the deleted message stack for this category if it doesn't exist
    if category not in deleted_message_stacks:
        deleted_message_stacks[category] = []

    # Create the Treeview widget with additional columns for days and periods
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    periods = list(core.utils.get_schedule_time_periods(user_id, category).keys())
    columns = ["message", "message_id"] + days + periods
    tree = ttk.Treeview(view_messages_window, columns=columns, show="headings")
    tree.pack(fill="both", expand=True, padx=20, pady=20)

    # Define the column headings
    tree.heading("message", text="Message", command=lambda: sort_treeview_column(tree, "message", category))
    tree.heading("message_id", text="message_id", command=lambda: sort_treeview_column(tree, "message_id", category))
    for day in days:
        tree.heading(day, text=day, command=lambda c=day: sort_treeview_column(tree, c, category))
    for period in periods:
        tree.heading(period, text=core.utils.title_case(period), command=lambda c=period: sort_treeview_column(tree, c, category))

    # Define the column widths
    tree.column("message", width=300)
    tree.column("message_id", width=0, stretch=False)
    for day in days:
        tree.column(day, width=50)
    for period in periods:
        tree.column(period, width=50)

    # Set the tree and messages as attributes of the window for refreshing later
    view_messages_window.tree = tree
    view_messages_window.messages = messages
    
    # Populate the Treeview with messages from the specified category
    for msg in messages:
        values = [msg.get('message', 'N/A'), msg['message_id']]
        for day in days:
            values.append('✔' if day in msg.get('days', []) else '')
        for period in periods:
            values.append('✔' if period in msg.get('time_periods', []) else '')
        tree.insert("", tk.END, values=values)

    def delete_message():
        """Deletes the selected message from the Treeview and updates the data file."""
        user_id = UserContext().get_user_id()  # Get the user ID
        if not user_id:
            logger.error("delete_message called with None user_id")
            messagebox.showerror("Error", "User ID is not set. Please ensure you are logged in.")
            return

        try:
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a message to delete.")
                return

            message_id = tree.item(selected_item)["values"][1]
            if message_id:
                # Reload data from file to ensure we have the most current version (in case message was recently edited)
                current_data = core.utils.load_json_data(core.utils.determine_file_path('messages', f'{category}/{user_id}'))
                if current_data and current_data.get('messages'):
                    # Find the current version of the message from the file
                    current_message_data = next((msg for msg in current_data['messages'] if msg['message_id'] == message_id), None)
                    if current_message_data:
                        # Store the current (possibly edited) version for undo
                        deleted_message_stacks[category].append(current_message_data.copy())
                        
                        # Remove from local messages list
                        local_message_data = next((msg for msg in messages if msg['message_id'] == message_id), None)
                        if local_message_data:
                            messages.remove(local_message_data)
                        
                        # Delete from file
                        core.utils.delete_message(user_id, category, message_id)
                        tree.delete(selected_item)
                        update_undo_delete_message_button_state()
                        messagebox.showinfo("Success", "Message deleted successfully.")
                    else:
                        messagebox.showerror("Error", "Message not found in current data.")
                else:
                    messagebox.showerror("Error", "Could not load current message data.")
            else:
                messagebox.showerror("Error", "Invalid message ID.")
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to delete message: {e}")

    def edit_message():
        """Edits the selected message in the Treeview and updates the data file."""
        user_id = UserContext().get_user_id()  # Get the user ID
        if not user_id:
            logger.error("edit_message called with None user_id")
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
                core.utils.add_message(user_id, category, message_data)

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

    edit_button = Button(left_button_frame, text="Edit Message", command=edit_message)
    edit_button.pack(side="left", padx=5)

    # Right side buttons
    right_button_frame = Frame(button_frame)
    right_button_frame.pack(side="right", padx=5)

    delete_button = Button(right_button_frame, text="Delete Message", command=delete_message)
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

        if col in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] + list(core.utils.get_schedule_time_periods(user_id, category).keys()):
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
        schedule_data = core.utils.get_schedule_time_periods(user_id, category)
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
        """Deletes a schedule period and updates the data file."""
        if period in schedule_data:
            # First, update the active status explicitly before deletion
            period_data = schedule_data[period]
            period_data['active'] = entries[period]['active_var'].get() == 1  # Update the internal status

            if len(schedule_data) <= 1:
                messagebox.showerror("Error", "You must have at least one schedule period.")
                return

            try:
                # Store the deleted period and its full data, including the active status
                deleted_period_info = {'period': period, 'data': period_data}
                if category not in deleted_period_stacks:
                    deleted_period_stacks[category] = []
                deleted_period_stacks[category].append(deleted_period_info)

                core.utils.delete_schedule_period(category, period, scheduler_manager)
                logger.debug(f"Current undo stack for {category}: {deleted_period_stacks[category]}")

                refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
                update_undo_delete_period_button_state()  # Ensure the button state is updated after deletion
            except Exception as e:
                logger.error(f"Error deleting schedule period: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to delete schedule period: {e}")

    def update_period_active_status(period, var, category):
        """Updates the active status of a schedule period."""
        user_id = UserContext().get_user_id()
        is_active = var.get() == 1

        try:
            # Update the status in the schedule_data directly
            if period in schedule_data:
                schedule_data[period]['active'] = is_active

            core.utils.set_schedule_period_active(user_id, category, period, is_active)
            logger.info(f"Period '{period}' in category '{category}' set to {'active' if is_active else 'inactive'}.")

            # Call rescheduling if the period is set to active (only if scheduler is available)
            if is_active and scheduler_manager:
                scheduler_manager.reset_and_reschedule_daily_messages(category)
            elif is_active and not scheduler_manager:
                logger.info(f"Period '{period}' activated, but no scheduler manager available (UI-only mode)")
        except Exception as e:
            logger.error(f"Error updating period active status for '{period}': {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to update period status: {e}")

    def undo_last_period_deletion(view_schedule_window, parent, category, scheduler_manager):
        """Restores the most recently deleted period."""
        if category in deleted_period_stacks and deleted_period_stacks[category]:
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

                # Load user data to ensure the period is restored in the correct state
                user_info = core.utils.load_user_info_data(user_id) or {}
                schedules = user_info.setdefault('schedules', {})
                category_schedules = schedules.setdefault(category, {})

                # Restore the period with its original data, including active status
                category_schedules[period] = times  # Use the data from the stack

                core.utils.save_user_info_data(user_info, user_id)
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

            except Exception as e:
                logger.error(f"Error undoing schedule period deletion: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to undo delete: {e}")

    def update_undo_delete_period_button_state():
        """Update the state of the undo delete button for periods."""
        if category in deleted_period_stacks and deleted_period_stacks[category]:
            parent.undo_button['state'] = 'normal'
        else:
            parent.undo_button['state'] = 'disabled'

    def validate_and_save_period(category, name, start, end, schedule_data, scheduler_manager, refresh=True):
        """Validates and saves a schedule period."""
        try:
            if name in schedule_data:
                core.utils.edit_schedule_period(category, name, start, end, scheduler_manager)
            else:
                core.utils.add_schedule_period(category, name, start, end, scheduler_manager)
        except core.utils.InvalidTimeFormatError:
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

        tk.Label(frame, text=f"{core.utils.title_case(period)} Start:").pack(side='left')
        start_entry = Entry(frame, width=10)
        start_entry.insert(0, times['start'])
        start_entry.pack(side='left', padx=5)

        tk.Label(frame, text="End:").pack(side='left')
        end_entry = Entry(frame, width=10)
        end_entry.insert(0, times['end'])
        end_entry.pack(side='left', padx=5)

        # Add a Checkbutton to toggle the active status of the period
        active_var = IntVar(value=1 if times.get('active', True) else 0)
        active_checkbutton = Checkbutton(frame, text="Active", variable=active_var, command=lambda p=period, v=active_var, c=category: update_period_active_status(p, v, c))
        active_checkbutton.pack(side='left', padx=5)

        delete_button = Button(frame, text="Delete", command=lambda p=period: delete_period(p))
        delete_button.pack(side='right')

        entries[period] = {'start': start_entry, 'end': end_entry, 'active_var': active_var}
        original_times[period] = {'start': times['start'], 'end': times['end']}

    def add_edit_period():
        """Add a new schedule period or update an existing one."""
        new_period_frame = Frame(view_schedule_window)
        new_period_frame.pack(fill='x', padx=10, pady=5)

        # Period Name
        period_name_frame = Frame(new_period_frame)
        period_name_frame.pack(fill='x', padx=5, pady=2)
        tk.Label(period_name_frame, text="Period Name:").pack(anchor='w')
        new_period_name = Entry(period_name_frame, width=20)
        new_period_name.pack(anchor='w', padx=5)

        # Start and End Time
        time_frame = Frame(new_period_frame)
        time_frame.pack(fill='x', padx=5, pady=2)

        tk.Label(time_frame, text="Start Time:").grid(row=0, column=0, sticky='w', padx=5)
        tk.Label(time_frame, text="End Time:").grid(row=0, column=1, sticky='w', padx=5)

        new_start_entry = Entry(time_frame, width=10)
        new_start_entry.grid(row=1, column=0, padx=5)

        new_end_entry = Entry(time_frame, width=10)
        new_end_entry.grid(row=1, column=1, padx=5)

        def confirm():
            """Confirm the addition or editing of a period."""
            name = new_period_name.get().lower()
            start = new_start_entry.get()
            end = new_end_entry.get()

            # Check if the period name already exists in the schedule
            if name in schedule_data:
                response = messagebox.askyesno("Name Exists", f"A period named '{name}' already exists. Would you like to edit it?")
                if response:
                    if validate_and_save_period(category, name, start, end, schedule_data, scheduler_manager):
                        messagebox.showinfo("Updated", "Period updated successfully.")
                        new_period_frame.destroy()
                else:
                    messagebox.showinfo("Change Name", "Please change the name of the period.")
            else:
                # Proceed to validate and save the new period
                if validate_and_save_period(category, name, start, end, schedule_data, scheduler_manager):
                    messagebox.showinfo("Added", "New period added successfully.")
                    new_period_frame.destroy()

        confirm_button = Button(new_period_frame, text="Confirm", command=confirm)
        confirm_button.pack(pady=10)

        # Bind Enter key to confirm
        new_period_name.bind("<Return>", lambda event: confirm())
        new_start_entry.bind("<Return>", lambda event: confirm())
        new_end_entry.bind("<Return>", lambda event: confirm())

    def save_schedule():
        """Save changes to the schedule based on user inputs using the validate_and_save_period function."""
        updated = False  # To track if any periods were updated
        for period, entry_controls in entries.items():
            # Retrieve the start and end times from the entry controls
            start_time_str = entry_controls['start'].get()
            end_time_str = entry_controls['end'].get()

            # Check if the current period data has changed from the original
            if start_time_str != original_times[period]['start'] or end_time_str != original_times[period]['end']:
                # Use the validate_and_save_period function to process each changed period
                if validate_and_save_period(category, period, start_time_str, end_time_str, schedule_data, scheduler_manager, refresh=False):
                    updated = True  # Mark as updated if any period was successfully processed

        if updated:
            messagebox.showinfo("Schedule Saved", "The schedule has been updated successfully.")
            refresh_window(view_schedule_window, setup_view_edit_schedule_window, parent, category, scheduler_manager)
        else:
            messagebox.showinfo("No Changes", "No changes were made to the schedule.")

    # Buttons for adding new periods and saving changes
    add_button = Button(view_schedule_window, text="Add New Period", command=add_edit_period)
    add_button.pack(pady=10)

    save_button = Button(view_schedule_window, text="Save Schedule", command=save_schedule)
    save_button.pack(pady=10)

# Communication channel and category management functions
def setup_communication_settings_window(parent, user_id):
    """Opens a window to manage user's communication settings."""
    logger.info(f"Opening communication settings for user {user_id}")
    
    settings_window = Toplevel(parent)
    settings_window.title(f"Communication Settings - {user_id}")
    settings_window.geometry("450x500")
    
    try:
        user_info = core.utils.get_user_info(user_id)
        current_service = user_info.get('preferences', {}).get('messaging_service', 'email')
        
        # Get existing contact info
        current_email = user_info.get('email', '')
        current_phone = user_info.get('phone', '')
        current_discord_id = user_info.get('preferences', {}).get('discord_user_id', '')
        
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
                user_info['preferences']['messaging_service'] = new_service
                user_info['email'] = new_email
                user_info['phone'] = new_phone
                user_info['preferences']['discord_user_id'] = new_discord_id
                
                core.utils.save_user_info_data(user_info, user_id)
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
        user_info = core.utils.get_user_info(user_id)
        current_categories = user_info.get('preferences', {}).get('categories', [])
        available_categories = core.utils.get_message_categories()
        
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
            checkbox = tk.Checkbutton(category_frame, text=core.utils.title_case(category), variable=var, font=("Arial", 10))
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
                if 'preferences' not in user_info:
                    user_info['preferences'] = {}
                user_info['preferences']['categories'] = selected_categories
                
                # Save changes
                core.utils.save_user_info_data(user_info, user_id)
                
                # Create message files for new categories
                for category in added_categories:
                    core.utils.create_user_message_file(user_id, category)
                
                # Show what changed
                change_summary = []
                if added_categories:
                    change_summary.append(f"Added: {', '.join(core.utils.title_case(cat) for cat in sorted(added_categories))}")
                if removed_categories:
                    change_summary.append(f"Removed: {', '.join(core.utils.title_case(cat) for cat in sorted(removed_categories))}")
                
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

def setup_checkin_management_window(parent, user_id):
    """Opens a window to manage user's check-in preferences."""
    logger.info(f"Opening check-in management for user {user_id}")
    
    checkin_window = Toplevel(parent)
    checkin_window.title(f"Check-in Settings - {user_id}")
    checkin_window.geometry("650x650")
    
    try:
        user_info = core.utils.get_user_info(user_id)
        current_checkin_prefs = user_info.get('preferences', {}).get('checkins', {})
        
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
                
                # Update user preferences
                if 'preferences' not in user_info:
                    user_info['preferences'] = {}
                user_info['preferences']['checkins'] = new_checkin_prefs
                
                # Save changes
                core.utils.save_user_info_data(user_info, user_id)
                
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