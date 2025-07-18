# ui_app.py - MHM Management UI (Standalone)

import tkinter as tk
from tkinter import messagebox
import subprocess
import psutil
import os
import sys
import time
import logging

# Add parent directory to path so we can import from core
import sys
import os

from user import user_context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import configuration validation
from core.config import validate_all_configuration, ConfigValidationError

# Import comprehensive error handling
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

from ui.account_manager import setup_view_edit_messages_window, setup_view_edit_schedule_window, add_message_dialog, setup_task_management_window
from user.user_context import UserContext
from core.user_management import get_all_user_ids, get_user_data
from core.validation import title_case
from tkinter import ttk
from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH

class ServiceManager:
    """Manages the MHM backend service process"""
    
    def __init__(self):
        self.service_process = None
        
    @handle_errors("validating configuration before start", default_return=False)
    def validate_configuration_before_start(self):
        """Validate configuration before attempting to start the service."""
        result = validate_all_configuration()
        
        if not result['valid']:
            error_message = "Configuration validation failed:\n\n"
            for error in result['errors']:
                error_message += f"• {error}\n"
            
            if result['warnings']:
                error_message += "\nWarnings:\n"
                for warning in result['warnings']:
                    error_message += f"• {warning}\n"
            
            messagebox.showerror("Configuration Error", error_message)
            return False
        
        # Filter out non-critical warnings that don't need popup
        critical_warnings = []
        for warning in result['warnings']:
            # Skip warnings about default values and auto-creation settings
            if any(skip_phrase in warning.lower() for skip_phrase in [
                'using default',
                'auto_create_user_dirs is enabled',
                'not set (using default)'
            ]):
                # Log these warnings but don't show popup
                logger.info(f"Configuration note: {warning}")
                continue
            critical_warnings.append(warning)
        
        # Only show popup for critical warnings
        if critical_warnings:
            warning_message = "Configuration warnings:\n\n"
            for warning in critical_warnings:
                warning_message += f"• {warning}\n"
            warning_message += "\nThe service will start, but you may want to address these warnings."
            messagebox.showwarning("Configuration Warnings", warning_message)
        
        if not result['available_channels']:
            messagebox.showwarning("No Communication Channels", 
                                 "No communication channels are configured. The service will start but won't be able to send messages.")
        
        return True
        
    @handle_errors("checking service status", default_return=(False, None))
    def is_service_running(self):
        """Check if the MHM service is running"""
        # Look for python processes running service.py
        service_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Skip if process info is not accessible (already terminated)
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('service.py' in arg for arg in cmdline):
                # Double-check process is still running
                if proc.is_running():
                    service_pids.append(proc.info['pid'])
        
        if service_pids:
            if len(service_pids) > 1:
                logger.debug(f"Status check: Found {len(service_pids)} service processes: {service_pids}")
            # Only log single process on DEBUG level if needed for troubleshooting
            return True, service_pids[0]  # Return first PID
        return False, None
    
    @handle_errors("starting service", default_return=False)
    def start_service(self):
        """Start the MHM backend service"""
        # Validate configuration before starting
        if not self.validate_configuration_before_start():
            return False
        
        is_running, pid = self.is_service_running()
        if is_running:
            logger.debug(f"Service already running with PID {pid}")
            messagebox.showinfo("Service Status", f"MHM Service is already running (PID: {pid})")
            return True
        
        # Start the service - updated path
        service_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'service.py')
        
        logger.debug(f"Service path: {service_path}")
        
        # Ensure we use the venv Python explicitly
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_python = os.path.join(script_dir, '.venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            python_executable = venv_python
        else:
            python_executable = sys.executable
        
        logger.debug(f"Using Python: {python_executable}")
        
        # Set up environment to ensure venv is used
        env = os.environ.copy()
        venv_scripts_dir = os.path.join(script_dir, '.venv', 'Scripts')
        if os.path.exists(venv_scripts_dir):
            # Add venv Scripts directory to PATH to ensure it's found first
            env['PATH'] = venv_scripts_dir + os.pathsep + env.get('PATH', '')
        
        # Run the service in the background without showing a console window
        if os.name == 'nt':  # Windows
            # Run without showing console window
            self.service_process = subprocess.Popen([
                python_executable, service_path
            ], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # Unix/Linux/Mac
            # Run in background
            self.service_process = subprocess.Popen([
                python_executable, service_path
            ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        logger.debug("Service process started, waiting for initialization...")
        # Give it a moment to start
        time.sleep(2)
        
        is_running, pid = self.is_service_running()
        if is_running:
            logger.info(f"Service started with PID {pid}")
            messagebox.showinfo("Service Status", f"MHM Service started successfully (PID: {pid})")
            return True
        else:
            logger.error("Failed to start service")
            messagebox.showerror("Service Error", "Failed to start MHM Service")
            return False
    
    @handle_errors("stopping service", default_return=False)
    def stop_service(self):
        """Stop the MHM backend service"""
        is_running, pid = self.is_service_running()
        if not is_running:
            logger.info("Stop service requested but service is not running")
            messagebox.showinfo("Service Status", "MHM Service is not running")
            return True
        
        logger.info(f"Stop service requested for PID: {pid}")
        
        # Create shutdown request file
        shutdown_file = os.path.join(os.path.dirname(__file__), '..', 'shutdown_request.flag')
        try:
            with open(shutdown_file, 'w') as f:
                f.write(f"SHUTDOWN_REQUESTED_BY_UI_{time.time()}")
            logger.info(f"Created shutdown request file: {shutdown_file}")
        except Exception as e:
            logger.warning(f"Could not create shutdown file: {e}")
        
        # Try to terminate ALL service processes
        found_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                    continue
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('service.py' in arg for arg in cmdline):
                    if proc.is_running():
                        found_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not found_processes:
            # Wait-and-retry loop to confirm service is stopped
            max_retries = 6  # 3 seconds total
            for _ in range(max_retries):
                is_running, current_pid = self.is_service_running()
                if not is_running:
                    break
                time.sleep(0.5)
            is_running, current_pid = self.is_service_running()
            if not is_running:
                logger.info("Service is not running - stop operation successful")
                messagebox.showinfo("Service Status", "Service is already stopped")
                return True
            else:
                logger.info(f"Service still detected with different PID {current_pid} - considering stop successful")
                messagebox.showinfo("Service Status", "Service processes cleaned up successfully")
                return True
        else:
            if len(found_processes) > 1:
                logger.info(f"Found {len(found_processes)} service processes, cleaning up all instances")
            else:
                logger.info(f"Found {len(found_processes)} service process, terminating")
            all_terminated = True
            
            for proc in found_processes:
                proc_pid = proc.info['pid']
                logger.info(f"Terminating service process (PID: {proc_pid})")
                try:
                    if not proc.is_running():
                        logger.debug(f"Process {proc_pid} already terminated, skipping")
                        continue
                    proc.terminate()
                    logger.info(f"Termination signal sent to PID {proc_pid}, waiting for graceful shutdown...")
                    try:
                        proc.wait(timeout=8)
                        logger.info(f"Service stopped gracefully (PID: {proc_pid})")
                    except psutil.TimeoutExpired:
                        logger.warning(f"Process {proc_pid} didn't stop gracefully within 8 seconds, using Windows taskkill")
                        if os.name == 'nt':
                            try:
                                result = subprocess.run(['taskkill', '/PID', str(proc_pid), '/F'], 
                                                      capture_output=True, text=True, timeout=10)
                                logger.info(f"Taskkill result for PID {proc_pid}: {result.returncode}, output: {result.stdout}, error: {result.stderr}")
                                time.sleep(2)
                                if not proc.is_running():
                                    logger.info(f"Service forcefully terminated via taskkill (PID: {proc_pid})")
                                else:
                                    logger.error(f"Failed to kill process {proc_pid} even with taskkill")
                                    all_terminated = False
                            except Exception as e:
                                logger.error(f"Taskkill failed for PID {proc_pid}: {e}")
                                all_terminated = False
                        if proc.is_running():
                            try:
                                proc.kill()
                                proc.wait(timeout=5)
                                logger.info(f"Service forcefully terminated via proc.kill() (PID: {proc_pid})")
                            except Exception as e:
                                logger.error(f"Failed to kill process {proc_pid}: {e}")
                                all_terminated = False
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    logger.info(f"Process {proc_pid} already terminated or inaccessible: {e}")
                except Exception as e:
                    logger.error(f"Error terminating process {proc_pid}: {e}")
                    all_terminated = False
            # Clean up shutdown file
            try:
                if os.path.exists(shutdown_file):
                    os.remove(shutdown_file)
                    logger.info("Cleanup: Removed shutdown request file")
            except Exception as e:
                logger.warning(f"Could not remove shutdown file: {e}")
            # Wait-and-retry loop to confirm service is stopped
            max_retries = 6  # 3 seconds total
            for _ in range(max_retries):
                is_running, current_pid = self.is_service_running()
                if not is_running:
                    break
                time.sleep(0.5)
            is_running, current_pid = self.is_service_running()
            if all_terminated:
                if len(found_processes) > 1:
                    messagebox.showinfo("Service Status", f"All {len(found_processes)} MHM Service processes stopped successfully")
                else:
                    messagebox.showinfo("Service Status", "MHM Service stopped successfully")
                return True
            else:
                messagebox.showwarning("Service Status", "Some MHM Service processes may still be running")
                return False
        
    @handle_errors("restarting service", default_return=False)
    def restart_service(self):
        """Restart the MHM backend service"""
        logger.info("Restart service requested")
        
        # Stop the service
        if not self.stop_service():
            logger.error("Failed to stop service during restart")
            messagebox.showerror("Service Error", "Failed to stop service during restart")
            return False
        
        # Wait a moment for cleanup
        time.sleep(2)
        
        # Start the service
        if not self.start_service():
            logger.error("Failed to start service during restart")
            messagebox.showerror("Service Error", "Failed to start service during restart")
            return False
        
        logger.info("Service restart completed successfully")
        messagebox.showinfo("Service Status", "MHM Service restarted successfully")
        return True

class MHMManagerUI:
    """
    Main UI application for managing MHM system.
    
    Provides a graphical interface for managing users, messages, schedules,
    and system configuration.
    """
    
    def __init__(self, root):
        """
        Initialize the MHM Manager UI.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("MHM Manager")
        self.root.geometry("800x600")
        
        # Initialize service manager
        self.service_manager = ServiceManager()
        
        # Initialize user context
        self.user_context = UserContext()
        
        # UI state
        self.current_user = None
        self.user_listbox = None
        self.status_label = None
        self.content_management_enabled = False
        
        # Set up the UI
        self.setup_ui()
        self.setup_menu_bar()
        
        # Initial status update
        self.update_service_status()
    
    def setup_menu_bar(self):
        """Set up the menu bar with debug and admin options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Debug menu (from main_ui.py functionality)
        debug_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Debug", menu=debug_menu)
        
        # Add logging toggle
        from core.logger import get_verbose_mode
        verbose_status = "ON" if get_verbose_mode() else "OFF"
        debug_menu.add_command(
            label=f"Toggle Verbose Logging (Currently: {verbose_status})", 
            command=self.toggle_logging_verbosity
        )
        debug_menu.add_separator()
        debug_menu.add_command(label="View Log File", command=self.view_log_file)
        
        # Cache cleanup submenu
        debug_menu.add_separator()
        cache_submenu = tk.Menu(debug_menu, tearoff=0)
        debug_menu.add_cascade(label="Cache Management", menu=cache_submenu)
        cache_submenu.add_command(label="View Cache Status", command=self.view_cache_status)
        cache_submenu.add_command(label="Force Clean Cache", command=self.force_clean_cache)
        
        # Admin menu
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=admin_menu)
        admin_menu.add_command(label="Validate Configuration", command=self.validate_configuration)
        admin_menu.add_separator()
        admin_menu.add_command(label="View All Users", command=self.view_all_users_summary)
        admin_menu.add_command(label="System Health Check", command=self.system_health_check)
    
    def toggle_logging_verbosity(self):
        """
        Toggle between verbose and quiet logging modes.
        
        Changes the console logging level while keeping file logging at DEBUG.
        """
        from core.logger import toggle_verbose_logging, get_verbose_mode
        
        is_verbose = toggle_verbose_logging()
        mode = "Verbose" if is_verbose else "Quiet"
        messagebox.showinfo("Logging Mode", f"Logging mode changed to: {mode}")

    @handle_errors("viewing log file")
    def view_log_file(self):
        """Open the log file in the default text editor."""
        import webbrowser
        from core.config import LOG_FILE_PATH
        webbrowser.open(LOG_FILE_PATH)

    @handle_errors("viewing cache status")
    def view_cache_status(self):
        """Show cache cleanup status and information."""
        from core.auto_cleanup import get_cleanup_status, find_pycache_dirs, find_pyc_files, calculate_cache_size
        import os
        
        # Get cleanup status
        status = get_cleanup_status()
        
        # Get current cache size
        pycache_dirs = find_pycache_dirs('.')
        pyc_files = find_pyc_files('.')
        current_size = calculate_cache_size(pycache_dirs, pyc_files)
        
        # Create status window
        status_window = tk.Toplevel(self.root)
        status_window.title("Cache Cleanup Status")
        status_window.geometry("450x350")
        status_window.resizable(False, False)
        
        # Status information
        tk.Label(status_window, text="Cache Cleanup Status", font=('Arial', 14, 'bold')).pack(pady=10)
        
        status_frame = tk.Frame(status_window)
        status_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(status_frame, text=f"Last cleanup: {status['last_cleanup']}", anchor='w').pack(fill='x', pady=2)
        tk.Label(status_frame, text=f"Days since cleanup: {status['days_since']}", anchor='w').pack(fill='x', pady=2)
        tk.Label(status_frame, text=f"Next cleanup: {status['next_cleanup']}", anchor='w').pack(fill='x', pady=2)
        
        tk.Label(status_frame, text="", anchor='w').pack(fill='x', pady=5)  # Spacer
        
        tk.Label(status_frame, text=f"Current cache files found:", anchor='w', font=('Arial', 10, 'bold')).pack(fill='x', pady=2)
        tk.Label(status_frame, text=f"• {len(pycache_dirs)} __pycache__ directories", anchor='w').pack(fill='x', pady=1)
        tk.Label(status_frame, text=f"• {len(pyc_files)} standalone .pyc files", anchor='w').pack(fill='x', pady=1)
        tk.Label(status_frame, text=f"• Total size: {current_size / 1024:.1f} KB ({current_size / (1024*1024):.2f} MB)", anchor='w').pack(fill='x', pady=1)
        
        # Buttons
        button_frame = tk.Frame(status_window)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(button_frame, text="Force Clean", command=lambda: [self.force_clean_cache(), status_window.destroy()]).pack(side='left', padx=5)
        tk.Button(button_frame, text="Close", command=status_window.destroy).pack(side='right', padx=5)

    @handle_errors("forcing cache cleanup")
    def force_clean_cache(self):
        """Force cache cleanup regardless of schedule."""
        from core.auto_cleanup import perform_cleanup, update_cleanup_timestamp
        
        # Ask for confirmation
        if not messagebox.askyesno("Force Cache Cleanup", 
                                 "This will force cleanup of all Python cache files regardless of when they were last cleaned.\n\nAre you sure you want to continue?"):
            return
        
        success = perform_cleanup()
        if success:
            update_cleanup_timestamp()
            messagebox.showinfo("Cache Cleanup", "Force cache cleanup completed successfully!")
            logger.info("Force cache cleanup completed successfully")
        else:
            messagebox.showerror("Error", "Cache cleanup failed")

    @handle_errors("validating configuration")
    def validate_configuration(self):
        """Show detailed configuration validation report."""
        from core.config import validate_all_configuration
        
        result = validate_all_configuration()
        
        # Create validation report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Configuration Validation Report")
        report_window.geometry("700x600")
        
        # Main frame
        main_frame = tk.Frame(report_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Configuration Validation Report", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Summary
        summary_frame = tk.Frame(main_frame)
        summary_frame.pack(fill='x', pady=(0, 20))
        
        summary_text = result['summary']
        if result['valid']:
            summary_color = 'green'
            summary_icon = "✓"
        else:
            summary_color = 'red'
            summary_icon = "✗"
        
        tk.Label(summary_frame, text=f"{summary_icon} {summary_text}", 
                font=('Arial', 12, 'bold'), fg=summary_color).pack()
        
        # Available channels
        if result['available_channels']:
            tk.Label(summary_frame, text=f"Available Channels: {', '.join(result['available_channels'])}", 
                    font=('Arial', 10), fg='blue').pack(pady=(5, 0))
        else:
            tk.Label(summary_frame, text="No communication channels available", 
                    font=('Arial', 10), fg='orange').pack(pady=(5, 0))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Errors tab
        if result['errors']:
            errors_frame = tk.Frame(notebook)
            notebook.add(errors_frame, text=f"Errors ({len(result['errors'])})")
            
            errors_text = tk.Text(errors_frame, wrap='word', height=10)
            errors_scrollbar = tk.Scrollbar(errors_frame, orient='vertical', command=errors_text.yview)
            errors_text.configure(yscrollcommand=errors_scrollbar.set)
            
            errors_text.pack(side='left', fill='both', expand=True)
            errors_scrollbar.pack(side='right', fill='y')
            
            for i, error in enumerate(result['errors'], 1):
                errors_text.insert('end', f"{i}. {error}\n\n")
            errors_text.config(state='disabled')
        
        # Warnings tab
        if result['warnings']:
            warnings_frame = tk.Frame(notebook)
            notebook.add(warnings_frame, text=f"Warnings ({len(result['warnings'])})")
            
            warnings_text = tk.Text(warnings_frame, wrap='word', height=10)
            warnings_scrollbar = tk.Scrollbar(warnings_frame, orient='vertical', command=warnings_text.yview)
            warnings_text.configure(yscrollcommand=warnings_scrollbar.set)
            
            warnings_text.pack(side='left', fill='both', expand=True)
            warnings_scrollbar.pack(side='right', fill='y')
            
            for i, warning in enumerate(result['warnings'], 1):
                warnings_text.insert('end', f"{i}. {warning}\n\n")
            warnings_text.config(state='disabled')
        
        # Current Configuration tab
        config_frame = tk.Frame(notebook)
        notebook.add(config_frame, text="Current Configuration")
        
        config_text = tk.Text(config_frame, wrap='word', height=10)
        config_scrollbar = tk.Scrollbar(config_frame, orient='vertical', command=config_text.yview)
        config_text.configure(yscrollcommand=config_scrollbar.set)
        
        config_text.pack(side='left', fill='both', expand=True)
        config_scrollbar.pack(side='right', fill='y')
        
        # Add current configuration values
        from core.config import (
            BASE_DATA_DIR, LOG_FILE_PATH, LOG_LEVEL, LM_STUDIO_BASE_URL, 
            AI_TIMEOUT_SECONDS, SCHEDULER_INTERVAL, EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, 
            EMAIL_SMTP_USERNAME, DISCORD_BOT_TOKEN
        )
        
        config_values = [
            ("Base Data Directory", BASE_DATA_DIR),
            ("Log File", LOG_FILE_PATH),
            ("Log Level", LOG_LEVEL),
            ("LM Studio URL", LM_STUDIO_BASE_URL),
            ("AI Timeout", f"{AI_TIMEOUT_SECONDS}s"),
            ("Scheduler Interval", f"{SCHEDULER_INTERVAL}s"),
            ("Email SMTP Server", EMAIL_SMTP_SERVER or "Not configured"),
            ("Email IMAP Server", EMAIL_IMAP_SERVER or "Not configured"),
            ("Email Username", EMAIL_SMTP_USERNAME or "Not configured"),
            ("Discord Bot Token", "Configured" if DISCORD_BOT_TOKEN else "Not configured"),
        ]
        
        for name, value in config_values:
            config_text.insert('end', f"{name}: {value}\n")
        
        config_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        if not result['valid']:
            tk.Button(button_frame, text="Fix Configuration", 
                     command=lambda: self.show_configuration_help(report_window)).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Close", 
                 command=report_window.destroy).pack(side='right', padx=5)

    def show_configuration_help(self, parent_window):
        """Show help for fixing configuration issues."""
        help_window = tk.Toplevel(parent_window)
        help_window.title("Configuration Help")
        help_window.geometry("600x500")
        
        help_text = tk.Text(help_window, wrap='word', padx=20, pady=20)
        help_scrollbar = tk.Scrollbar(help_window, orient='vertical', command=help_text.yview)
        help_text.configure(yscrollcommand=help_scrollbar.set)
        
        help_text.pack(side='left', fill='both', expand=True)
        help_scrollbar.pack(side='right', fill='y')
        
        help_content = """
CONFIGURATION HELP

To fix configuration issues, you need to set up environment variables. Create a .env file in the MHM root directory with the following variables:

REQUIRED SETTINGS:
=================

1. COMMUNICATION CHANNELS (at least one required):
   - For Email: EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
   - For Discord: DISCORD_BOT_TOKEN

2. AI CONFIGURATION:
   - LM_STUDIO_BASE_URL (default: http://localhost:1234/v1)
   - LM_STUDIO_API_KEY (default: lm-studio)
   - LM_STUDIO_MODEL (default: deepseek-llm-7b-chat)

OPTIONAL SETTINGS:
=================

- BASE_DATA_DIR (default: data)
- LOG_FILE_PATH (default: app.log)
- LOG_LEVEL (default: WARNING)
- AI_TIMEOUT_SECONDS (default: 15)
- SCHEDULER_INTERVAL (default: 60)
- AUTO_CREATE_USER_DIRS (default: true)

EXAMPLE .env FILE:
=================

EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# OR for Discord:
DISCORD_BOT_TOKEN=your-discord-bot-token

# AI Configuration:
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=deepseek-llm-7b-chat

# Optional settings:
LOG_LEVEL=INFO
AI_TIMEOUT_SECONDS=30
SCHEDULER_INTERVAL=60

SETUP INSTRUCTIONS:
==================

1. Create a .env file in the MHM root directory
2. Add the required environment variables
3. Restart the MHM application
4. Run "Validate Configuration" again to check

For detailed setup instructions, see the README.md file.
"""
        
        help_text.insert('1.0', help_content)
        help_text.config(state='disabled')
        
        tk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)

    def view_all_users_summary(self):
        """Show a summary of all users in the system."""
        try:
            user_ids = get_all_user_ids()
            
            # Create summary window
            summary_window = tk.Toplevel(self.root)
            summary_window.title("All Users Summary")
            summary_window.geometry("600x400")
            
            tk.Label(summary_window, text="All Users Summary", font=('Arial', 14, 'bold')).pack(pady=10)
            
            # Create scrollable text area
            text_frame = tk.Frame(summary_window)
            text_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap='word')
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=text_widget.yview)
            
            if not user_ids:
                text_widget.insert('end', "No users found in the system.\n")
            else:
                text_widget.insert('end', f"Total users: {len(user_ids)}\n\n")
                
                for user_id in user_ids:
                    # Get user account data
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account')
                    if not user_account:
                        logger.error(f"User account not found for {user_id}")
                        continue
                    username = user_account.get('internal_username', 'Unknown')
                    preferred_name = user_account.get('preferred_name', '')
                    prefs_result = get_user_data(user_id, 'preferences')
                    categories = prefs_result.get('preferences', {}).get('categories', [])
                    prefs = prefs_result.get('preferences', {})
                    messaging_service = prefs.get('channel', {}).get('type', 'Unknown')
                    
                    text_widget.insert('end', f"User: {username}")
                    if preferred_name:
                        text_widget.insert('end', f" ({preferred_name})")
                    text_widget.insert('end', f"\n")
                    text_widget.insert('end', f"  ID: {user_id}\n")
                    text_widget.insert('end', f"  Service: {messaging_service}\n")
                    text_widget.insert('end', f"  Categories: {', '.join(categories) if categories else 'None'}\n")
                    text_widget.insert('end', "\n")
            
            text_widget.config(state='disabled')  # Make read-only
            
            tk.Button(summary_window, text="Close", command=summary_window.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Failed to show users summary: {e}")
            messagebox.showerror("Error", f"Failed to load users summary: {e}")

    def system_health_check(self):
        """Perform a basic system health check."""
        try:
            # Create health check window
            health_window = tk.Toplevel(self.root)
            health_window.title("System Health Check")
            health_window.geometry("500x400")
            
            tk.Label(health_window, text="System Health Check", font=('Arial', 14, 'bold')).pack(pady=10)
            
            # Create scrollable text area
            text_frame = tk.Frame(health_window)
            text_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap='word')
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Perform checks
            text_widget.insert('end', "Running system health checks...\n\n")
            
            # Check service status
            is_running, pid = self.service_manager.is_service_running()
            text_widget.insert('end', f"✓ Service Status: {'Running' if is_running else 'Stopped'}")
            if is_running:
                text_widget.insert('end', f" (PID: {pid})")
            text_widget.insert('end', "\n")
            
            # Check user count
            user_ids = get_all_user_ids()
            text_widget.insert('end', f"✓ Total Users: {len(user_ids)}\n")
            
            # Check data directories
            required_dirs = [BASE_DATA_DIR, USER_INFO_DIR_PATH]
            for dir_path in required_dirs:
                exists = os.path.exists(dir_path)
                status = "✓" if exists else "✗"
                text_widget.insert('end', f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}\n")
            
            # Check for common issues
            text_widget.insert('end', "\nChecking for common issues...\n")
            
            # Check for orphaned message files
            if os.path.exists(USER_INFO_DIR_PATH):
                orphaned_files = 0
                for root, dirs, files in os.walk(USER_INFO_DIR_PATH):
                    for file in files:
                        if file.endswith('.json'):
                            # Extract user_id from filename
                            user_id = file.replace('.json', '')
                            if user_id not in user_ids:
                                orphaned_files += 1
                
                if orphaned_files == 0:
                    text_widget.insert('end', "✓ No orphaned message files found\n")
                else:
                    text_widget.insert('end', f"⚠ Found {orphaned_files} orphaned message files\n")
            
            text_widget.insert('end', "\nHealth check complete.\n")
            text_widget.config(state='disabled')  # Make read-only
            
            tk.Button(health_window, text="Close", command=health_window.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            messagebox.showerror("Error", f"Failed to perform health check: {e}")
        
    def setup_ui(self):
        """Set up the comprehensive admin panel UI"""
        # Title
        title_label = tk.Label(self.root, text="MHM Admin Panel", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Service Management Section
        service_frame = ttk.LabelFrame(self.root, text="Service Management", padding=(10, 10))
        service_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Service status
        status_frame = tk.Frame(service_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(status_frame, text="Service Status:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.status_label = tk.Label(status_frame, text="Checking...", fg="orange")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Service control buttons
        button_frame = tk.Frame(service_frame)
        button_frame.pack(pady=10)
        
        self.start_button = tk.Button(button_frame, text="Start Service", command=self.start_service, width=10)
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = tk.Button(button_frame, text="Stop Service", command=self.stop_service, width=10)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        self.restart_button = tk.Button(button_frame, text="Restart", command=self.restart_service, width=10)
        self.restart_button.pack(side=tk.LEFT, padx=2)
        
        self.refresh_button = tk.Button(button_frame, text="Refresh", command=self.update_service_status, width=10)
        self.refresh_button.pack(side=tk.LEFT, padx=2)
        
        # User Management Section
        user_frame = ttk.LabelFrame(self.root, text="User Management", padding=(10, 10))
        user_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create New User (separate row)
        create_user_frame = tk.Frame(user_frame)
        create_user_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(create_user_frame, text="Create New User", command=self.create_new_user, width=15).pack(side=tk.LEFT)
        
        # User selection (separate row)
        user_select_frame = tk.Frame(user_frame)
        user_select_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(user_select_frame, text="Select User:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.user_listbox = tk.Listbox(user_select_frame, width=35)
        self.user_listbox.pack(side=tk.LEFT, padx=(10, 0))
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_selected)
        
        # User info display (connected to dropdown)
        self.user_info_frame = tk.Frame(user_frame)
        self.user_info_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.user_info_label = tk.Label(self.user_info_frame, text="Select a user to manage content", 
                                       fg="gray", font=("Arial", 9, "italic"))
        self.user_info_label.pack(side=tk.LEFT)
        
        # Content Management Section (part of user management)
        content_frame = tk.Frame(user_frame)
        content_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Content management buttons
        self.content_button_frame = tk.Frame(content_frame)
        self.content_button_frame.pack(pady=10)
        
        self.edit_messages_button = tk.Button(self.content_button_frame, text="Edit Messages", 
                                            command=self.edit_user_messages, width=12, state=tk.DISABLED)
        self.edit_messages_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_schedules_button = tk.Button(self.content_button_frame, text="Edit Schedules", 
                                             command=self.edit_user_schedules, width=12, state=tk.DISABLED)
        self.edit_schedules_button.pack(side=tk.LEFT, padx=5)
        
        self.send_test_button = tk.Button(self.content_button_frame, text="Send Test Message", 
                                        command=self.send_test_message, width=15, state=tk.DISABLED)
        self.send_test_button.pack(side=tk.LEFT, padx=5)
        
        self.comm_settings_button = tk.Button(self.content_button_frame, text="Communication Settings", 
                                            command=self.manage_communication_settings, width=18, state=tk.DISABLED)
        self.comm_settings_button.pack(side=tk.LEFT, padx=5)
        
        # User settings management buttons
        self.settings_button_frame = tk.Frame(content_frame)
        self.settings_button_frame.pack(pady=10)
        
        self.category_settings_button = tk.Button(self.settings_button_frame, text="Manage Categories", 
                                                command=self.manage_categories, width=15, state=tk.DISABLED)
        self.category_settings_button.pack(side=tk.LEFT, padx=5)
        
        self.checkin_settings_button = tk.Button(self.settings_button_frame, text="Check-in Settings", 
                                               command=self.manage_checkins, width=14, state=tk.DISABLED)
        self.checkin_settings_button.pack(side=tk.LEFT, padx=5)
        
        self.task_settings_button = tk.Button(self.settings_button_frame, text="Task Management", 
                                            command=self.manage_tasks, width=15, state=tk.DISABLED)
        self.task_settings_button.pack(side=tk.LEFT, padx=5)
        
        self.task_crud_button = tk.Button(self.settings_button_frame, text="Task CRUD", 
                                        command=self.manage_task_crud, width=12, state=tk.DISABLED)
        self.task_crud_button.pack(side=tk.LEFT, padx=5)
        
        self.personalization_button = tk.Button(self.settings_button_frame, text="Personalization", 
                                              command=self.manage_personalization, width=15, state=tk.DISABLED)
        self.personalization_button.pack(side=tk.LEFT, padx=5)
        
        # Info label about test messages
        info_label = tk.Label(content_frame, text="Note: Test messages require the MHM service to be running", 
                             fg="gray", font=("Arial", 8, "italic"))
        info_label.pack(pady=(5, 0))
        
    def update_service_status(self):
        """
        Update the service status display in the UI.
        
        Checks if the service is running and updates the status label accordingly.
        """
        is_running, pid = self.service_manager.is_service_running()
        status_text = f"Service: {'Running' if is_running else 'Stopped'}"
        if is_running and pid:
            status_text += f" (PID: {pid})"
        self.status_label.config(text=status_text)

    def start_service(self):
        """
        Start the MHM backend service.
        
        Attempts to start the service and updates the UI status.
        """
        logger.info("Admin Panel: Starting service...")
        if self.service_manager.start_service():
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service start failed")
    
    def stop_service(self):
        """
        Stop the MHM backend service.
        
        Attempts to stop the service and updates the UI status.
        """
        logger.info("Admin Panel: Stop service requested")
        if self.service_manager.stop_service():
            logger.info("Admin Panel: Service stopped successfully")
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service stop failed")
    
    def restart_service(self):
        """
        Restart the MHM backend service.
        
        Stops the service if running, then starts it again.
        """
        logger.info("Admin Panel: Restart service requested")
        if self.service_manager.restart_service():
            logger.info("Admin Panel: Service restarted successfully")
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service restart failed")
    
    @handle_errors("refreshing user list", default_return=None)
    def refresh_user_list(self):
        """Refresh the user list in the combo box"""
        try:
            user_ids = get_all_user_ids()
            self.user_listbox.delete(0, tk.END)
            self.user_listbox.insert(tk.END, "Select a user...")
            
            for user_id in user_ids:
                # Get user account data
                user_data_result = get_user_data(user_id, 'account')
                user_account = user_data_result.get('account')
                internal_username = user_account.get('internal_username', 'Unknown') if user_account else 'Unknown'
                # Get user context
                context_result = get_user_data(user_id, 'context')
                user_context = context_result.get('context')
                preferred_name = user_context.get('preferred_name', '') if user_context else ''
                if preferred_name:
                    display_name = f"{preferred_name} ({internal_username}) - {user_id}"
                else:
                    display_name = f"{internal_username} - {user_id}"
                self.user_listbox.insert(tk.END, display_name)
                
        except Exception as e:
            logger.error(f"Error refreshing user list: {e}")
            messagebox.showerror("Error", f"Failed to refresh user list: {e}")

    @handle_errors("handling user selection", default_return=None)
    def on_user_selected(self, event=None):
        """Handle user selection from listbox"""
        selection = self.user_listbox.curselection()
        if not selection or selection[0] == 0:  # "Select a user..." is selected
            self.current_user_id = None
            self.disable_content_management()
            return
        
        try:
            # Extract user_id from display name (format: "Name - user_id")
            display_name = self.user_listbox.get(selection[0])
            if " - " in display_name:
                user_id = display_name.split(" - ")[-1]
            else:
                logger.warning(f"Could not parse user_id from selected_display: '{display_name}'")
                self.disable_content_management()
                return
                
            self.current_user_id = user_id
            # Get user account data
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account')
            if user_account:
                # Load user categories
                self.load_user_categories(user_id)
                self.enable_content_management()
                logger.info(f"Admin Panel: User selected for management: {user_id} ({user_account.get('internal_username', 'Unknown')})")
            else:
                messagebox.showerror("User Error", f"Could not load user account for {user_id}")
                self.disable_content_management()
                return
                
        except Exception as e:
            logger.error(f"Error handling user selection: {e}")
            messagebox.showerror("Error", f"Failed to load user: {e}")
            self.disable_content_management()

    @handle_errors("enabling content management")
    def enable_content_management(self):
        """Enable content management buttons"""
        self.edit_messages_button.config(state=tk.NORMAL)
        self.edit_schedules_button.config(state=tk.NORMAL)
        self.send_test_button.config(state=tk.NORMAL)
        self.comm_settings_button.config(state=tk.NORMAL)
        self.category_settings_button.config(state=tk.NORMAL)
        self.checkin_settings_button.config(state=tk.NORMAL)
        self.task_settings_button.config(state=tk.NORMAL)
        self.task_crud_button.config(state=tk.NORMAL)
        self.personalization_button.config(state=tk.NORMAL)
        logger.debug("Admin Panel: Content management buttons enabled successfully")

    def disable_content_management(self):
        """Disable content management buttons"""
        self.edit_messages_button.config(state=tk.DISABLED)
        self.edit_schedules_button.config(state=tk.DISABLED)
        self.send_test_button.config(state=tk.DISABLED)
        self.comm_settings_button.config(state=tk.DISABLED)
        self.category_settings_button.config(state=tk.DISABLED)
        self.checkin_settings_button.config(state=tk.DISABLED)
        self.task_settings_button.config(state=tk.DISABLED)
        self.task_crud_button.config(state=tk.DISABLED)
        self.personalization_button.config(state=tk.DISABLED)
        self.user_info_label.config(text="Select a user to manage content", 
                                   fg="gray", font=("Arial", 9, "italic"))
        self.current_user_id = None

    @handle_errors("creating new user")
    def create_new_user(self):
        """Open dialog to create a new user"""
        logger.info("Admin Panel: Opening create new user dialog")
        from ui.account_creator import CreateAccountScreen
        from bot.communication_manager import CommunicationManager
        from bot.channel_registry import register_all_channels
        
        # Create a temporary communication manager for the create account screen
        register_all_channels()
        temp_comm_manager = CommunicationManager()
        
        # Open create account dialog
        create_window = tk.Toplevel(self.root)
        create_window.title("Create New User")
        create_account_app = CreateAccountScreen(create_window, temp_comm_manager)
        
        # Wait for create window to close, then refresh user list
        self.root.wait_window(create_window)
        self.refresh_user_list()
        logger.info("Admin Panel: Create user dialog closed, user list refreshed")
        
        # Clean up temporary communication manager
        try:
            temp_comm_manager.stop_all()
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up temporary communication manager: {cleanup_error}")

    @handle_errors("editing user messages")
    def edit_user_messages(self):
        """Open message editing interface for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user_id}")
        # Temporarily set the user context for editing
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user_id)
        
        # Load the user's full data to get internal_username and other details
        # Get user account data
        user_data_result = get_user_data(self.current_user_id, 'account')
        user_account = user_data_result.get('account')
        if user_account:
            UserContext().set_internal_username(user_account.get('internal_username', ''))
            if user_context:
                UserContext().set_preferred_name(user_context.get('preferred_name', ''))
            # Load the full user data into UserContext
            UserContext().load_user_data(self.current_user_id)
        
        # Get user categories
        prefs_result = get_user_data(self.current_user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        prefs = prefs_result.get('preferences', {})
        
        if not categories:
            logger.info(f"Admin Panel: User {self.current_user_id} has no message categories configured")
            messagebox.showinfo("No Categories", "This user has no message categories configured.")
            return
        
        # Open category selection dialog
        category_dialog = tk.Toplevel(self.root)
        category_dialog.title(f"Select Category - {self.current_user_id}")
        category_dialog.geometry("300x200")
        category_dialog.transient(self.root)
        category_dialog.grab_set()
        
        title_label = tk.Label(category_dialog, text="Select message category to edit:", font=("Arial", 12))
        title_label.pack(pady=10)
        
        for category in categories:
            button = tk.Button(category_dialog, text=title_case(category), 
                             command=lambda c=category: self.open_message_editor(category_dialog, c))
            button.pack(pady=2)

    @handle_errors("opening message editor")
    def open_message_editor(self, parent_window, category):
        """Open the message editing window for a specific category"""
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user_id}, category {category}")
        parent_window.destroy()
        setup_view_edit_messages_window(self.root, category)

    @handle_errors("editing user schedules")
    def edit_user_schedules(self):
        """Open schedule editing interface for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
        
        # Check if a category is selected
        selected_category = self.category_combo.get()
        if not selected_category or selected_category == "Select a category...":
            messagebox.showerror("No Category Selected", "Please select a category from the dropdown first.")
            return
            
        logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user_id}, category {selected_category}")
        
        # Temporarily set the user context for editing
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user_id)
        
        # Load the user's full data to get internal_username and other details
        # Get user account data
        user_data_result = get_user_data(self.current_user_id, 'account')
        user_account = user_data_result.get('account')
        if user_account:
            UserContext().set_internal_username(user_account.get('internal_username', ''))
            if user_context:
                UserContext().set_preferred_name(user_context.get('preferred_name', ''))
            # Load the full user data into UserContext
            UserContext().load_user_data(self.current_user_id)
        
        # Open the schedule editor directly with the selected category
        self.open_schedule_editor(None, selected_category)

    @handle_errors("sending test message")
    def send_test_message(self):
        """Send a test message to the selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
        
        logger.info(f"Admin Panel: Preparing test message for user {self.current_user_id}")
        # Get user categories
        prefs_result = get_user_data(self.current_user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        
        if not categories:
            logger.info(f"Admin Panel: User {self.current_user_id} has no message categories for test")
            messagebox.showinfo("No Categories", "This user has no message categories configured.")
            return
        
        # Open category selection dialog for test message
        category_dialog = tk.Toplevel(self.root)
        category_dialog.title(f"Send Test Message - {self.current_user_id}")
        category_dialog.geometry("300x200")
        category_dialog.transient(self.root)
        category_dialog.grab_set()
        
        title_label = tk.Label(category_dialog, text="Select category for test message:", font=("Arial", 12))
        title_label.pack(pady=10)
        
        for category in categories:
            button = tk.Button(category_dialog, text=title_case(category), 
                             command=lambda c=category: self.confirm_test_message(category_dialog, c))
            button.pack(pady=2)

    @handle_errors("confirming test message")
    def confirm_test_message(self, parent_window, category):
        """Confirm and send test message"""
        parent_window.destroy()
        
        result = messagebox.askyesno("Confirm Test Message", 
                                   f"Send a test {category} message to {self.current_user_id}?\n\n"
                                   f"This will send a random message from their {category} collection.")
        
        if result:
            logger.info(f"Admin Panel: Test message confirmed for user {self.current_user_id}, category {category}")
            # Actually send the test message using communication manager
            self.send_actual_test_message(category)
        else:
            logger.info(f"Admin Panel: Test message cancelled for user {self.current_user_id}, category {category}")

    @handle_errors("sending actual test message")
    def send_actual_test_message(self, category):
        """Send a test message via the running service"""
        # Since service is running, we'll create a minimal communication to the service
        # For now, we'll use a simple approach: create a test message file that the service can pick up
        # This is safer than trying to inject into the running service's communication channels
        
        # Store original user context and set to selected user
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user_id)
        
        logger.info(f"Admin Panel: Creating test message request for user {self.current_user_id}, category {category}")
        
        # Create a test message request using the same pattern as shutdown requests
        from datetime import datetime
        import json
        
        # Use the same directory structure as the shutdown flag
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to MHM root
        request_file = os.path.join(base_dir, f'test_message_request_{self.current_user_id}_{category}.flag')
        
        test_request = {
            "user_id": self.current_user_id,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "source": "admin_panel"
        }
        
        with open(request_file, 'w') as f:
            json.dump(test_request, f, indent=2)
        
        messagebox.showinfo("Test Message Requested", 
                          f"Test {category} message request created for {self.current_user_id}.\n\n"
                          f"The running service will check for this request and send the message.\n\n"
                          f"Note: Current implementation creates a request file.\n"
                          f"Future versions will have direct service communication.\n\n"
                          f"Request file: {os.path.basename(request_file)}")
        
        logger.info(f"Admin Panel: Test message request file created: {request_file}")
        
        # Optional: Clean up old request files after a short delay
        import threading
        def cleanup_old_requests():
            import time
            time.sleep(300)  # Wait 5 minutes
            try:
                if os.path.exists(request_file):
                    os.remove(request_file)
                    logger.debug(f"Cleaned up old request file: {request_file}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up request file: {cleanup_error}")
        
        cleanup_thread = threading.Thread(target=cleanup_old_requests, daemon=True)
        cleanup_thread.start()
        
        # Restore original user context
        if original_user:
            UserContext().set_user_id(original_user)
        else:
            UserContext().set_user_id(None)

    @handle_errors("managing communication settings")
    def manage_communication_settings(self):
        """Open communication settings management for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening communication settings for user {self.current_user_id}")
        from ui.account_manager import setup_communication_settings_window
        setup_communication_settings_window(self.root, self.current_user_id)

    @handle_errors("managing categories")
    def manage_categories(self):
        """Open category management for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening category management for user {self.current_user_id}")
        from ui.account_manager import setup_category_management_window
        setup_category_management_window(self.root, self.current_user_id)

    @handle_errors("managing checkins")
    def manage_checkins(self):
        """Open check-in settings management for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening check-in management for user {self.current_user_id}")
        from ui.account_manager import setup_checkin_management_window
        setup_checkin_management_window(self.root, self.current_user_id)

    @handle_errors("managing tasks")
    def manage_tasks(self):
        """Open task management for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening task management for user {self.current_user_id}")
        from ui.account_manager import setup_task_management_window
        setup_task_management_window(self.root, self.current_user_id)

    @handle_errors("managing task CRUD operations")
    def manage_task_crud(self):
        """Open comprehensive task CRUD operations for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening task CRUD operations for user {self.current_user_id}")
        from ui.account_manager import setup_task_crud_window
        setup_task_crud_window(self.root, self.current_user_id)

    @handle_errors("managing personalization")
    def manage_personalization(self):
        """Open personalization management interface for selected user"""
        if not self.current_user_id:
            messagebox.showerror("No User Selected", "Please select a user first.")
            return
        
        logger.info(f"Admin Panel: Opening personalization management for user {self.current_user_id}")
        from ui.account_manager import setup_personalization_management_window
        setup_personalization_management_window(self.root, self.current_user_id)

    @handle_errors("shutting down UI components")
    def shutdown_ui_components(self, communication_manager=None):
        """Shutdown any UI-created components gracefully"""
        logger.info("Shutting down admin panel.")
        if communication_manager:
            logger.debug("Stopping communication manager (legacy UI instance).")
            communication_manager.stop_all()
        # Admin panel no longer creates its own communication manager
        logger.debug("Admin panel cleanup complete - no communication channels to stop.")
        logger.info("Admin panel shutdown complete.")
    
    def on_closing(self):
        """Handle window close event"""
        self.shutdown_ui_components()
        self.root.destroy()

    def load_user_categories(self, user_id):
        """Load categories for the selected user"""
        try:
            # Get user preferences to find categories
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            prefs = prefs_result.get('preferences', {})
            
            # Handle both list and dictionary formats
            if isinstance(categories, dict):
                self.current_user_categories = list(categories.keys())
            elif isinstance(categories, list):
                self.current_user_categories = categories
            else:
                self.current_user_categories = []
            
            # Update category combo box
            self.category_combo['values'] = ["Select a category..."] + self.current_user_categories
            self.category_combo.set("Select a category...")
                
        except Exception as e:
            logger.error(f"Error loading user categories: {e}")
            self.current_user_categories = []

@handle_errors("starting UI application")
def main():
    """Main entry point for the UI application"""
    root = tk.Tk()
    app = MHMManagerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 