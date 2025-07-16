# account_creator.py - Account creation functionality

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from core.logger import get_logger
from user.user_context import UserContext
from core.message_management import get_message_categories
from core.validation import title_case
from core.user_management import get_user_id_by_internal_username, create_new_user
from core.file_operations import create_user_files
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
import uuid
from core.schedule_management import validate_and_format_time, set_schedule_periods, set_schedule_days, clear_schedule_periods_cache

logger = get_logger(__name__)

class CreateAccountScreen:
    def __init__(self, master, communication_manager):
        """
        Initializes the account creation screen.
        """
        self.master = master
        self.communication_manager = communication_manager
        self.master.title("Create Account")

        # Set up the close protocol
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Compact window size with scrollable content
        initial_width = 580  # Reduced further for compactness
        initial_height = 650
        self.master.geometry(f"{initial_width}x{initial_height}")
        self.master.minsize(550, 500)

        # Create main scrollable frame for entire window content
        self.main_canvas = tk.Canvas(self.master)
        self.main_scrollbar = tk.Scrollbar(self.master, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_main_frame = tk.Frame(self.main_canvas)

        # Configure scrollable main frame
        self.scrollable_main_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.main_canvas.create_window((0, 0), window=self.scrollable_main_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        # Mouse wheel support for main canvas
        def on_main_mouse_wheel(event):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.main_canvas.bind("<MouseWheel>", on_main_mouse_wheel)
        self.scrollable_main_frame.bind("<MouseWheel>", on_main_mouse_wheel)

        # Pack main canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        # Use the scrollable frame as the master for all content
        master = self.scrollable_main_frame

        # Fixed grid layout to prevent jumping when content changes
        master.grid_columnconfigure(0, weight=0, minsize=110)  # Labels
        master.grid_columnconfigure(1, weight=0, minsize=180)  # Main content
        master.grid_columnconfigure(2, weight=0, minsize=130)  # Status/extras
        master.grid_columnconfigure(3, weight=1, minsize=50)   # Buffer

        current_row = 0

        # Title
        tk.Label(master, text="Create a New Account", font=("Arial", 16, "bold")).grid(
            row=current_row, column=0, columnspan=4, pady=10)
        current_row += 1

        # Basic Information Section
        tk.Label(master, text="Basic Information", font=("Arial", 12, "bold")).grid(
            row=current_row, column=0, columnspan=4, pady=(10, 5), sticky=tk.W, padx=15)
        current_row += 1

        tk.Label(master, text="*Username:").grid(row=current_row, column=0, sticky=tk.W, padx=15, pady=3)
        self.internal_username_entry = tk.Entry(master, width=20)
        self.internal_username_entry.grid(row=current_row, column=1, padx=10, pady=3, sticky=tk.W)
        self.internal_username_entry.bind("<MouseWheel>", on_main_mouse_wheel)
        current_row += 1

        tk.Label(master, text="Preferred Name:").grid(row=current_row, column=0, sticky=tk.W, padx=15, pady=3)
        self.preferred_name_entry = tk.Entry(master, width=20)
        self.preferred_name_entry.grid(row=current_row, column=1, padx=10, pady=3, sticky=tk.W)
        self.preferred_name_entry.bind("<MouseWheel>", on_main_mouse_wheel)
        current_row += 1

        # Primary Message Service Section  
        tk.Label(master, text="*Primary Message Service", font=("Arial", 12, "bold")).grid(
            row=current_row, column=0, columnspan=4, pady=(15, 8), sticky=tk.W, padx=15)
        current_row += 1

        # Service selection with stable layout
        service_container = tk.Frame(master)
        service_container.grid(row=current_row, column=0, columnspan=4, padx=15, pady=8, sticky=tk.W+tk.E)
        service_container.grid_columnconfigure(0, weight=0, minsize=140)  # Service selection
        service_container.grid_columnconfigure(1, weight=1, minsize=300)  # Contact info
        service_container.bind("<MouseWheel>", on_main_mouse_wheel)
        
        # Initialize service variable
        self.service_var = tk.StringVar()
        self.service_var.set("NONE_SELECTED")
        
        # Left side - Service selection
        service_selection_frame = tk.Frame(service_container)
        service_selection_frame.grid(row=0, column=0, sticky=tk.N+tk.W, padx=(0, 10))
        service_selection_frame.bind("<MouseWheel>", on_main_mouse_wheel)
        
        tk.Label(service_selection_frame, text="Select Service:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        self.discord_radio = tk.Radiobutton(service_selection_frame, text="Discord", 
                                          variable=self.service_var, value="discord", 
                                          command=self.update_service_selection)
        self.discord_radio.pack(anchor='w', pady=1)
        self.discord_radio.bind("<MouseWheel>", on_main_mouse_wheel)
        
        self.email_radio = tk.Radiobutton(service_selection_frame, text="Email", 
                                        variable=self.service_var, value="email", 
                                        command=self.update_service_selection)
        self.email_radio.pack(anchor='w', pady=1)
        self.email_radio.bind("<MouseWheel>", on_main_mouse_wheel)
        
        self.telegram_radio = tk.Radiobutton(service_selection_frame, text="Telegram", 
                                           variable=self.service_var, value="telegram", 
                                           command=self.update_service_selection)
        self.telegram_radio.pack(anchor='w', pady=1)
        self.telegram_radio.bind("<MouseWheel>", on_main_mouse_wheel)
        
        # Right side - Contact Information
        contact_frame = tk.Frame(service_container)
        contact_frame.grid(row=0, column=1, sticky=tk.N+tk.W, padx=(10, 0))
        contact_frame.grid_columnconfigure(0, weight=0, minsize=70)   # Labels
        contact_frame.grid_columnconfigure(1, weight=0, minsize=120) # Entries
        contact_frame.grid_columnconfigure(2, weight=0, minsize=110) # Status
        contact_frame.bind("<MouseWheel>", on_main_mouse_wheel)
        
        tk.Label(contact_frame, text="Contact Information:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Discord ID
        tk.Label(contact_frame, text="Discord ID:").grid(row=1, column=0, sticky=tk.W, pady=1)
        self.discord_id_entry = tk.Entry(contact_frame, width=16)
        self.discord_id_entry.grid(row=1, column=1, padx=(5, 5), pady=1, sticky=tk.W)
        self.discord_id_entry.bind("<MouseWheel>", on_main_mouse_wheel)
        self.discord_status = tk.Label(contact_frame, text="✗ Not configured", fg="red", font=("Arial", 8))
        self.discord_status.grid(row=1, column=2, sticky=tk.W, pady=1)
        
        # Email
        tk.Label(contact_frame, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=1)
        self.email_entry = tk.Entry(contact_frame, width=16)
        self.email_entry.grid(row=2, column=1, padx=(5, 5), pady=1, sticky=tk.W)
        self.email_entry.bind("<MouseWheel>", on_main_mouse_wheel)
        self.email_status = tk.Label(contact_frame, text="✗ Not configured", fg="red", font=("Arial", 8))
        self.email_status.grid(row=2, column=2, sticky=tk.W, pady=1)
        
        # Telegram/Phone
        phone_frame = tk.Frame(contact_frame)
        phone_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=1)
        phone_frame.bind("<MouseWheel>", on_main_mouse_wheel)
        
        tk.Label(phone_frame, text="Phone:").grid(row=0, column=0, sticky=tk.W)
        self.country_code = ttk.Combobox(phone_frame, width=4, values=["+1", "+44", "+91", "+86"])
        self.country_code.set("+1")
        self.country_code.grid(row=0, column=1, padx=(5, 2))
        self.phone_entry = tk.Entry(phone_frame, width=10)
        self.phone_entry.grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.phone_entry.bind("<MouseWheel>", on_main_mouse_wheel)
        self.telegram_status = tk.Label(phone_frame, text="✗ Not configured", fg="red", font=("Arial", 8))
        self.telegram_status.grid(row=0, column=3, sticky=tk.W)
        
        current_row += 1

        # Categories Section
        tk.Label(master, text="*Select Categories (at least one required)", font=("Arial", 12, "bold")).grid(
            row=current_row, column=0, columnspan=4, pady=(15, 8), sticky=tk.W, padx=15)
        current_row += 1

        # Categories checkboxes
        categories_frame = tk.Frame(master)
        categories_frame.grid(row=current_row, column=0, columnspan=4, padx=15, pady=5, sticky=tk.W)
        categories_frame.bind("<MouseWheel>", on_main_mouse_wheel)
        
        self.categories = get_message_categories()
        self.category_vars = {category: tk.IntVar() for category in self.categories}

        # Arrange categories in columns
        col = 0
        row_in_frame = 0
        max_cols = 2
        
        for category, var in self.category_vars.items():
            checkbox = tk.Checkbutton(categories_frame, text=title_case(category), variable=var)
            checkbox.grid(row=row_in_frame, column=col, sticky=tk.W, padx=(0, 20), pady=1)
            checkbox.bind("<MouseWheel>", on_main_mouse_wheel)
            col += 1
            if col >= max_cols:
                col = 0
                row_in_frame += 1
        
        current_row += 1

        # Task Management Section
        tk.Label(master, text="Task Management", font=("Arial", 12, "bold")).grid(
            row=current_row, column=0, columnspan=4, pady=(15, 8), sticky=tk.W, padx=15)
        current_row += 1

        # Task management options
        self.task_section_box = tk.LabelFrame(master, text="Task Management (Optional)", font=("Arial", 10, "bold"))
        self.task_section_box.grid(row=current_row, column=0, columnspan=4, padx=15, pady=(10, 0), sticky=tk.W+tk.E)
        self.tasks_enabled_var = tk.IntVar()
        self.task_enable_checkbox = tk.Checkbutton(self.task_section_box, text="Enable Task Management", variable=self.tasks_enabled_var, command=self.update_task_options)
        self.task_enable_checkbox.pack(anchor="w", padx=10, pady=(5, 2))
        self.task_content_frame = tk.Frame(self.task_section_box)
        self.task_content_frame.pack(fill="x", pady=(5, 0))
        self.task_content_frame.pack_forget()
        # Task periods and days UI (like admin)
        self.task_reminder_periods = []  # List of dicts with start, end, active, and UI vars
        self.task_period_widgets = []
        self.task_days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.task_day_vars = []
        self.task_select_all_var = tk.IntVar(value=1)
        def render_task_periods():
            for w in self.task_period_widgets:
                w.destroy()
            self.task_period_widgets.clear()
            for idx, period in enumerate(self.task_reminder_periods):
                row = tk.Frame(self.task_periods_box)
                row.pack(fill="x", pady=3, anchor="w")
                start_var = period['start_var']
                end_var = period['end_var']
                active_var = period['active_var']
                tk.Label(row, text="Start:").pack(side="left")
                tk.Entry(row, textvariable=start_var, width=6).pack(side="left", padx=(0, 5))
                tk.Label(row, text="End:").pack(side="left")
                tk.Entry(row, textvariable=end_var, width=6).pack(side="left", padx=(0, 5))
                tk.Checkbutton(row, text="Active", variable=active_var).pack(side="left", padx=(5, 5))
                def make_delete(idx):
                    return lambda: (self.task_reminder_periods.pop(idx), render_task_periods())
                tk.Button(row, text="Delete", command=make_delete(idx)).pack(side="left", padx=(5, 0))
                self.task_period_widgets.append(row)
        def add_task_period():
            self.task_reminder_periods.append({
                'start_var': tk.StringVar(value="12:00"),
                'end_var': tk.StringVar(value="12:00"),
                'active_var': tk.IntVar(value=1)
            })
            render_task_periods()
        # Periods and days boxes side by side
        self.task_columns_frame = tk.Frame(self.task_content_frame)
        self.task_columns_frame.pack(fill="x", pady=5)
        self.task_periods_box = tk.LabelFrame(self.task_columns_frame, text="Reminder Time Periods", font=("Arial", 10, "bold"))
        self.task_periods_box.pack(side="left", fill="both", expand=False, padx=(0, 15), ipadx=10, ipady=5)
        tk.Button(self.task_periods_box, text="Add New Period", command=add_task_period).pack(anchor="w", pady=5)
        self.task_days_box = tk.LabelFrame(self.task_columns_frame, text="Reminder Days", font=("Arial", 10, "bold"))
        self.task_days_box.pack(side="left", fill="y", expand=True, ipadx=30, ipady=5)
        def on_task_select_all():
            val = self.task_select_all_var.get()
            for v in self.task_day_vars:
                v.set(val)
        tk.Checkbutton(self.task_days_box, text="Select All", variable=self.task_select_all_var, command=on_task_select_all).pack(anchor="w", pady=(2, 2))
        self.task_day_vars.clear()
        for day in self.task_days_of_week:
            var = tk.IntVar(value=1)
            tk.Checkbutton(self.task_days_box, text=day, variable=var).pack(anchor="w")
            self.task_day_vars.append(var)
        def update_task_select_all(*_):
            if all(v.get() for v in self.task_day_vars):
                self.task_select_all_var.set(1)
            elif all(not v.get() for v in self.task_day_vars):
                self.task_select_all_var.set(0)
            else:
                self.task_select_all_var.set(0)
        for v in self.task_day_vars:
            v.trace_add('write', update_task_select_all)
        # Initial state: no periods until enabled
        def update_task_options():
            enabled = self.tasks_enabled_var.get() == 1
            if enabled:
                self.task_content_frame.pack(fill="x", pady=(5, 0))
                if not self.task_reminder_periods:
                    add_task_period()
            else:
                self.task_content_frame.pack_forget()
        self.update_task_options = update_task_options
        self.tasks_enabled_var.trace_add('write', lambda *_: self.update_task_options())

        current_row += 1

        # Check-in Settings Section with collapsible layout
        checkin_outer_frame = tk.LabelFrame(master, text="Check-in Settings (Optional)", font=("Arial", 10, "bold"))
        checkin_outer_frame.grid(row=current_row, column=0, columnspan=4, padx=15, pady=12, sticky=tk.W+tk.E)
        checkin_outer_frame.bind("<MouseWheel>", on_main_mouse_wheel)
        
        self.checkin_enabled_var = tk.IntVar(value=0)
        checkin_checkbox = tk.Checkbutton(checkin_outer_frame, text="Enable check-ins", 
                                        variable=self.checkin_enabled_var, command=self.update_checkin_options)
        checkin_checkbox.pack(anchor="w", padx=10, pady=5)
        checkin_checkbox.bind("<MouseWheel>", on_main_mouse_wheel)
        
        # Container for dynamic content - will be created/destroyed to allow proper collapsing
        self.checkin_outer_frame = checkin_outer_frame  # Store reference for update_checkin_options
        
        # Initialize checkin components (will be created/destroyed dynamically)
        self.checkin_frequency_var = tk.StringVar(value="daily")
        self.checkin_questions = {
            'mood': {'var': tk.IntVar(value=1), 'label': 'Mood (1-5 scale) (recommended)'},
            'energy': {'var': tk.IntVar(value=1), 'label': 'Energy level (1-5 scale) (recommended)'},
            'ate_breakfast': {'var': tk.IntVar(value=1), 'label': 'Had breakfast (yes/no) (recommended)'},
            'brushed_teeth': {'var': tk.IntVar(value=1), 'label': 'Brushed teeth (yes/no) (recommended)'},
            'sleep_quality': {'var': tk.IntVar(value=0), 'label': 'Sleep quality (1-5 scale)'},
            'anxiety_level': {'var': tk.IntVar(value=0), 'label': 'Anxiety level (1-5 scale)'},
            'focus_level': {'var': tk.IntVar(value=0), 'label': 'Focus/attention (1-5 scale)'},
            'medication_taken': {'var': tk.IntVar(value=0), 'label': 'Took medication (yes/no)'},
            'exercise': {'var': tk.IntVar(value=0), 'label': 'Did exercise (yes/no)'},
            'hydration': {'var': tk.IntVar(value=0), 'label': 'Staying hydrated (yes/no)'}
        }
        
        # Store main mouse wheel handler for dynamic creation
        self.on_main_mouse_wheel = on_main_mouse_wheel
        
        current_row += 1

        # Personalization Button
        self.personalization_button = tk.Button(master, text="Personalization Settings", 
                                              command=self.open_personalization_dialog,
                                              font=("Arial", 10), bg="#2196F3", fg="white", pady=6)
        self.personalization_button.grid(row=current_row, column=0, columnspan=4, pady=(10, 5))
        self.personalization_button.bind("<MouseWheel>", on_main_mouse_wheel)
        current_row += 1

        # Create Account Button
        self.create_button = tk.Button(master, text="Create Account", command=self.create_account, 
                                     font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", pady=8)
        self.create_button.grid(row=current_row, column=0, columnspan=4, pady=15)
        self.create_button.bind("<MouseWheel>", on_main_mouse_wheel)
        current_row += 1

        # Bind entry fields to update status labels
        self.email_entry.bind('<KeyRelease>', self.update_status_labels)
        self.phone_entry.bind('<KeyRelease>', self.update_status_labels)
        self.discord_id_entry.bind('<KeyRelease>', self.update_status_labels)
        
        # Initial status update and layout
        self.update_status_labels()
        self.update_checkin_options()  # Set initial state

        # Bind main mouse wheel to all relevant widgets except questions area
        self._bind_main_mouse_wheel_recursive(master, on_main_mouse_wheel)

    def _bind_main_mouse_wheel_recursive(self, widget, callback):
        """Recursively bind mouse wheel to widget and children, except questions area"""
        try:
            # Skip questions-related widgets to avoid conflicts
            if (hasattr(self, 'questions_canvas') and 
                (widget == self.questions_canvas or 
                 widget == self.questions_scrollable_frame or
                 str(widget).startswith(str(self.questions_scrollable_frame)))):
                return
                
            widget.bind("<MouseWheel>", callback)
            for child in widget.winfo_children():
                self._bind_main_mouse_wheel_recursive(child, callback)
        except:
            pass

    def update_status_labels(self, event=None):
        """Update status labels based on current field values"""
        email_text = self.email_entry.get().strip()
        phone_text = self.phone_entry.get().strip()
        discord_text = self.discord_id_entry.get().strip()
        
        # Update email status
        if email_text:
            self.email_status.config(text="✓ Configured", fg="green")
        else:
            self.email_status.config(text="✗ Not configured", fg="red")
            
        # Update phone status
        if phone_text:
            self.telegram_status.config(text="✓ Configured", fg="green")
        else:
            self.telegram_status.config(text="✗ Not configured", fg="red")
            
        # Update discord status
        if discord_text:
            self.discord_status.config(text="✓ Configured", fg="green")
        else:
            self.discord_status.config(text="✗ Not configured", fg="red")
    
    def update_service_selection(self):
        """Called when service selection changes"""
        self.update_status_labels()

    def update_checkin_options(self):
        """Show/hide check-in options based on main checkbox - create/destroy content for proper collapsing"""
        enabled = self.checkin_enabled_var.get() == 1
        
        # First, destroy any existing content
        if hasattr(self, 'checkin_content_frame'):
            self.checkin_content_frame.destroy()
        
        if enabled:
            # Create the content frame dynamically
            self.checkin_content_frame = tk.Frame(self.checkin_outer_frame)
            self.checkin_content_frame.pack(fill="x", padx=8, pady=5)
            self.checkin_content_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Create frequency selection frame
            self.frequency_frame = tk.LabelFrame(self.checkin_content_frame, text="Frequency", font=("Arial", 9, "bold"))
            self.frequency_frame.pack(fill="x", pady=5)
            self.frequency_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Radio buttons for frequency
            freq_radios_frame = tk.Frame(self.frequency_frame)
            freq_radios_frame.pack(fill="x", padx=5, pady=3)
            freq_radios_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            self.frequency_radios = []
            for freq in ["daily", "weekly", "none", "custom"]:
                rb = tk.Radiobutton(freq_radios_frame, text=freq.title(), 
                                  variable=self.checkin_frequency_var, value=freq)
                rb.pack(side="left", padx=8, pady=2)
                rb.bind("<MouseWheel>", self.on_main_mouse_wheel)
                self.frequency_radios.append(rb)
            
            # Explanatory text for frequency options (4 lines)
            freq_help_frame = tk.Frame(self.frequency_frame)
            freq_help_frame.pack(fill="x", padx=5, pady=(0, 3))
            freq_help_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            help_text = (
                "Daily: Prompted once per day\n"
                "Weekly: Prompted once per week\n" 
                "None: Manual only (/checkin command)\n"
                "Custom: Set your own schedule"
            )
            help_label = tk.Label(freq_help_frame, text=help_text, 
                                 font=("Arial", 8, "italic"), fg="gray", justify=tk.LEFT)
            help_label.pack(anchor="w")
            help_label.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Add check-in time scheduling
            time_frame = tk.LabelFrame(self.checkin_content_frame, text="Check-in Time", font=("Arial", 9, "bold"))
            time_frame.pack(fill="x", pady=5)
            time_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Time selection
            time_selection_frame = tk.Frame(time_frame)
            time_selection_frame.pack(fill="x", padx=5, pady=3)
            time_selection_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            tk.Label(time_selection_frame, text="Preferred time:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
            
            # Time dropdown (hour)
            self.checkin_hour_var = tk.StringVar(value="09")
            hour_dropdown = tk.OptionMenu(time_selection_frame, self.checkin_hour_var, 
                                        *[f"{i:02d}" for i in range(24)])
            hour_dropdown.config(width=3, font=("Arial", 9))
            hour_dropdown.pack(side="left", padx=2)
            
            tk.Label(time_selection_frame, text=":", font=("Arial", 9)).pack(side="left", padx=2)
            
            # Time dropdown (minute)
            self.checkin_minute_var = tk.StringVar(value="00")
            minute_dropdown = tk.OptionMenu(time_selection_frame, self.checkin_minute_var, 
                                          *[f"{i:02d}" for i in range(0, 60, 15)])  # 15-minute intervals
            minute_dropdown.config(width=3, font=("Arial", 9))
            minute_dropdown.pack(side="left", padx=2)
            
            # Time help text
            time_help_frame = tk.Frame(time_frame)
            time_help_frame.pack(fill="x", padx=5, pady=(0, 3))
            time_help_frame.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            time_help_text = "Check-ins will be scheduled at this time. You can adjust this later in settings."
            time_help_label = tk.Label(time_help_frame, text=time_help_text, 
                                      font=("Arial", 8, "italic"), fg="gray", justify=tk.LEFT)
            time_help_label.pack(anchor="w")
            time_help_label.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Create questions section - use a simple Frame instead of LabelFrame to avoid border issues
            questions_container = tk.Frame(self.checkin_content_frame)
            questions_container.pack(fill="x", pady=(3, 5))
            questions_container.bind("<MouseWheel>", self.on_main_mouse_wheel)
            
            # Title label instead of LabelFrame to avoid scrolling border issues
            tk.Label(questions_container, text="Questions to Include", 
                    font=("Arial", 9, "bold")).pack(anchor="w", padx=5)
            
            # Create scrollable area for questions without LabelFrame border
            questions_scroll_frame = tk.Frame(questions_container, relief="ridge", bd=1)
            questions_scroll_frame.pack(fill="x", padx=5, pady=2)
            
            # Create scrollable canvas for questions
            self.questions_canvas = tk.Canvas(questions_scroll_frame, height=90, highlightthickness=0)
            self.questions_scrollbar = tk.Scrollbar(questions_scroll_frame, orient="vertical", command=self.questions_canvas.yview)
            self.questions_scrollable_frame = tk.Frame(self.questions_canvas)
            
            self.questions_scrollable_frame.bind(
                "<Configure>",
                lambda e: self.questions_canvas.configure(scrollregion=self.questions_canvas.bbox("all"))
            )
            
            self.questions_canvas.create_window((0, 0), window=self.questions_scrollable_frame, anchor="nw")
            self.questions_canvas.configure(yscrollcommand=self.questions_scrollbar.set)
            
            # Mouse wheel handler for questions area
            def on_questions_mouse_wheel(event):
                self.questions_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            
            # Bind mouse wheel events
            self.questions_canvas.bind("<MouseWheel>", on_questions_mouse_wheel)
            self.questions_scrollable_frame.bind("<MouseWheel>", on_questions_mouse_wheel)
            
            # Create question checkboxes
            question_row = 0
            for question_key, question_data in self.checkin_questions.items():
                checkbox = tk.Checkbutton(self.questions_scrollable_frame, text=question_data['label'], 
                                        variable=question_data['var'], font=("Arial", 9))
                checkbox.grid(row=question_row, column=0, sticky=tk.W, padx=8, pady=1)
                checkbox.bind("<MouseWheel>", on_questions_mouse_wheel)
                question_data['checkbox'] = checkbox
                question_row += 1
            
            # Pack questions canvas and scrollbar
            self.questions_canvas.pack(side="left", fill="both", expand=True)
            self.questions_scrollbar.pack(side="right", fill="y")
            
            # Explanatory text
            self.explanation = tk.Label(self.checkin_content_frame, 
                                 text="Note: Check-ins help track patterns and provide personalized AI responses. You can modify these settings later.", 
                                 font=("Arial", 7, "italic"), fg="gray", justify=tk.LEFT, wraplength=400)
            self.explanation.pack(anchor="w", pady=3)
            self.explanation.bind("<MouseWheel>", self.on_main_mouse_wheel)
        # If disabled, content frame is destroyed and not recreated, allowing proper collapsing

    def update_task_options(self):
        """Show/hide task options based on main checkbox"""
        # For now, just enable/disable the reminder time entry
        enabled = self.tasks_enabled_var.get() == 1
        # The reminder time entry is always visible but can be disabled if needed
        # This method can be expanded later for more complex task UI

    def open_personalization_dialog(self):
        """Open the personalization dialog for the user."""
        try:
            from ui.dialogs.user_profile_dialog import open_personalization_dialog
            
            # Create a temporary user ID for the dialog
            temp_user_id = str(uuid.uuid4())
            
            def on_personalization_save(data):
                """Callback when personalization data is saved."""
                # Store the personalization data temporarily
                self.temp_personalization_data = data
                logger.info("Personalization data saved for account creation")
            
            # Pass existing data if available (for editing)
            existing_data = getattr(self, 'temp_personalization_data', None)
            open_personalization_dialog(self.master, temp_user_id, on_personalization_save, existing_data)
            
        except Exception as e:
            logger.error(f"Error opening personalization dialog: {e}")
            messagebox.showerror("Error", f"Failed to open personalization dialog: {str(e)}")

    @handle_errors("creating account")
    def create_account(self):
        """Create the user account."""
        try:
            # Create user data in the new format
            user_data = {
                'internal_username': self.internal_username_entry.get().strip().lower(),
                'preferred_name': self.preferred_name_entry.get().strip(),
                'chat_id': self.discord_id_entry.get().strip() if self.service_var.get() == "discord" else "",
                'phone': f"{self.country_code.get().strip()} {self.phone_entry.get().strip()}" if self.service_var.get() == "telegram" else "",
                'email': self.email_entry.get().strip() if self.service_var.get() == "email" else "",
                'discord_user_id': self.discord_id_entry.get().strip() if self.service_var.get() == "discord" else "",
                'categories': [category for category, var in self.category_vars.items() if var.get() == 1],
                'checkin_settings': {
                    "enabled": self.checkin_enabled_var.get() == 1,
                    "questions": {question_key: {"enabled": question_data['var'].get() == 1, "label": question_data['label']} for question_key, question_data in self.checkin_questions.items()},
                    "frequency": self.checkin_frequency_var.get(),
                    "hour": self.checkin_hour_var.get(),
                    "minute": self.checkin_minute_var.get()
                },
                'task_settings': {
                    "enabled": self.tasks_enabled_var.get() == 1
                },
                'personalization_data': getattr(self, 'temp_personalization_data', None)
            }

            # Create the user using the new function
            user_id = create_new_user(user_data)
            
            # Create user files
            create_user_files(user_id, user_data['categories'], user_data)
            
            logger.info(f"Created new user account: {self.internal_username_entry.get().strip().lower()} (ID: {user_id})")
            messagebox.showinfo("Account Created", f"Account created for {self.internal_username_entry.get().strip().lower()}.\n\nYou can now manage this user through the admin panel.")
            self.master.destroy()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            messagebox.showerror("Account Creation Failed", f"Failed to create account: {str(e)}")
            return False

    @handle_errors("closing account creator")
    def on_closing(self):
        """Handles the window close event for the account creation screen."""
        logger.info("CreateAccountScreen is closing.")
        self.master.destroy() 