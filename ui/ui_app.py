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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

from ui.account_manager import setup_view_edit_messages_window, setup_view_edit_schedule_window, add_message_dialog
from user.user_context import UserContext
import core.utils
from tkinter import ttk
from core.config import BASE_DATA_DIR, MESSAGES_BY_CATEGORY_DIR_PATH, USER_INFO_DIR_PATH

class ServiceManager:
    """Manages the MHM backend service process"""
    
    def __init__(self):
        self.service_process = None
        
    def is_service_running(self):
        """Check if the MHM service is running"""
        try:
            # Look for python processes running service.py
            service_pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Skip if process info is not accessible (already terminated)
                    if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                        continue
                    
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('service.py' in arg for arg in cmdline):
                        # Double-check process is still running
                        if proc.is_running():
                            service_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process terminated while we were checking it - skip it
                    continue
            
            if service_pids:
                if len(service_pids) > 1:
                    logger.debug(f"Found {len(service_pids)} service processes: {service_pids} (will clean up extras)")
                else:
                    logger.debug(f"Service process found: {service_pids[0]}")
                return True, service_pids[0]  # Return first PID
            return False, None
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False, None
    
    def start_service(self):
        """Start the MHM backend service"""
        try:
            is_running, pid = self.is_service_running()
            if is_running:
                logger.debug(f"Service already running with PID {pid}")
                messagebox.showinfo("Service Status", f"MHM Service is already running (PID: {pid})")
                return True
            
            # Start the service - updated path
            service_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'service.py')
            
            logger.debug(f"Service path: {service_path}")
            
            # Run the service in the background without showing a console window
            if os.name == 'nt':  # Windows
                # Run without showing console window
                self.service_process = subprocess.Popen([
                    sys.executable, service_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
            else:  # Unix/Linux/Mac
                # Run in background
                self.service_process = subprocess.Popen([
                    sys.executable, service_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
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
                
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            messagebox.showerror("Service Error", f"Error starting service: {str(e)}")
            return False
    
    def stop_service(self):
        """Stop the MHM backend service"""
        try:
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
                        # Only add if process is still running
                        if proc.is_running():
                            found_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process terminated while we were checking it - skip it
                    continue
            
            if not found_processes:
                logger.info(f"No service processes found (reported PID {pid} may have already terminated)")
                # Double-check if any service is actually running
                is_running, current_pid = self.is_service_running()
                if not is_running:
                    logger.info("Service is not running - stop operation successful")
                    messagebox.showinfo("Service Status", "Service is already stopped")
                    return True
                else:
                    logger.info(f"Service still detected with different PID {current_pid} - considering stop successful")
                    messagebox.showinfo("Service Status", "Service processes cleaned up successfully")
                    return True
            
            logger.info(f"Found {len(found_processes)} service process(es), terminating all")
            all_terminated = True
            
            for proc in found_processes:
                proc_pid = proc.info['pid']
                logger.info(f"Terminating service process (PID: {proc_pid})")
                
                try:
                    # Check if process still exists before trying to terminate
                    if not proc.is_running():
                        logger.info(f"Process {proc_pid} already terminated, skipping")
                        continue
                        
                    # First try SIGTERM (graceful)
                    proc.terminate()
                    logger.info(f"Termination signal sent to PID {proc_pid}, waiting for graceful shutdown...")
                    
                    try:
                        proc.wait(timeout=8)  # Wait up to 8 seconds for graceful shutdown
                        logger.info(f"Service stopped gracefully (PID: {proc_pid})")
                    except psutil.TimeoutExpired:
                        logger.warning(f"Process {proc_pid} didn't stop gracefully within 8 seconds, using Windows taskkill")
                        
                        # On Windows, use taskkill for more reliable termination
                        if os.name == 'nt':
                            try:
                                result = subprocess.run(['taskkill', '/PID', str(proc_pid), '/F'], 
                                                      capture_output=True, text=True, timeout=10)
                                logger.info(f"Taskkill result for PID {proc_pid}: {result.returncode}, output: {result.stdout}, error: {result.stderr}")
                                
                                # Wait a moment and check if process is gone
                                time.sleep(2)
                                if not proc.is_running():
                                    logger.info(f"Service forcefully terminated via taskkill (PID: {proc_pid})")
                                else:
                                    logger.error(f"Failed to kill process {proc_pid} even with taskkill")
                                    all_terminated = False
                            except Exception as e:
                                logger.error(f"Taskkill failed for PID {proc_pid}: {e}")
                                all_terminated = False
                        
                        # Fallback to psutil kill
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
                    # This is fine - process is gone
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
            
            if all_terminated:
                messagebox.showinfo("Service Status", "All MHM Service processes stopped successfully")
                return True
            else:
                messagebox.showwarning("Service Status", "Some MHM Service processes may still be running")
                return False
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            messagebox.showerror("Service Error", f"Error stopping service: {str(e)}")
            return False

    def restart_service(self):
        """Restart the MHM backend service"""
        try:
            logger.info("Restarting MHM service...")
            if self.stop_service():
                time.sleep(3)  # Give it time to fully stop
                if self.start_service():
                    return True
            return False
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            messagebox.showerror("Service Error", f"Error restarting service: {str(e)}")
            return False

class MHMManagerUI:
    """Main management UI for MHM - Comprehensive Admin Panel"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MHM Admin Panel")
        self.root.geometry("600x500")
        
        self.service_manager = ServiceManager()
        self.selected_user_id = tk.StringVar()
        
        # Set up close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add menu bar with debug functionality
        self.setup_menu_bar()
        
        self.setup_ui()
        self.update_service_status()
        self.refresh_user_list()
    
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
        admin_menu.add_command(label="View All Users", command=self.view_all_users_summary)
        admin_menu.add_command(label="System Health Check", command=self.system_health_check)
    
    def toggle_logging_verbosity(self):
        """Toggle logging verbosity and update menu."""
        from core.logger import toggle_verbose_logging, get_verbose_mode
        is_verbose = toggle_verbose_logging()
        
        # Update the menu text
        menubar = self.root.nametowidget(self.root['menu'])
        debug_menu = menubar.nametowidget(menubar.entryconfig(1)['menu'][4])
        verbose_status = "ON" if is_verbose else "OFF"
        debug_menu.entryconfig(0, label=f"Toggle Verbose Logging (Currently: {verbose_status})")
        
        # Show status message
        status = "enabled" if is_verbose else "disabled"
        messagebox.showinfo("Logging", f"Verbose logging has been {status}")

    def view_log_file(self):
        """Open the log file in the default text editor."""
        try:
            import webbrowser
            from core.config import LOG_FILE_PATH
            webbrowser.open(LOG_FILE_PATH)
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
            messagebox.showerror("Error", f"Failed to open log file: {e}")

    def view_cache_status(self):
        """Show cache cleanup status and information."""
        try:
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
            
        except Exception as e:
            logger.error(f"Failed to show cache status: {e}")
            messagebox.showerror("Error", f"Failed to retrieve cache status: {e}")

    def force_clean_cache(self):
        """Force cache cleanup regardless of schedule."""
        try:
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
                
        except Exception as e:
            logger.error(f"Failed to force clean cache: {e}")
            messagebox.showerror("Error", f"Failed to clean cache: {e}")

    def view_all_users_summary(self):
        """Show a summary of all users in the system."""
        try:
            user_ids = core.utils.get_all_user_ids()
            
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
                    user_info = core.utils.get_user_info(user_id)
                    if user_info:
                        username = user_info.get('internal_username', 'Unknown')
                        preferred_name = user_info.get('preferred_name', '')
                        categories = user_info.get('preferences', {}).get('categories', [])
                        messaging_service = user_info.get('preferences', {}).get('messaging_service', 'Unknown')
                        
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
            user_ids = core.utils.get_all_user_ids()
            text_widget.insert('end', f"✓ Total Users: {len(user_ids)}\n")
            
            # Check data directories
            required_dirs = [BASE_DATA_DIR, MESSAGES_BY_CATEGORY_DIR_PATH, USER_INFO_DIR_PATH]
            for dir_path in required_dirs:
                exists = os.path.exists(dir_path)
                status = "✓" if exists else "✗"
                text_widget.insert('end', f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}\n")
            
            # Check for common issues
            text_widget.insert('end', "\nChecking for common issues...\n")
            
            # Check for orphaned message files
            if os.path.exists(MESSAGES_BY_CATEGORY_DIR_PATH):
                orphaned_files = 0
                for root, dirs, files in os.walk(MESSAGES_BY_CATEGORY_DIR_PATH):
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
        self.user_dropdown = ttk.Combobox(user_select_frame, textvariable=self.selected_user_id, 
                                         state="readonly", width=35)
        self.user_dropdown.pack(side=tk.LEFT, padx=(10, 0))
        self.user_dropdown.bind('<<ComboboxSelected>>', self.on_user_selected)
        
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
        
        # User settings management buttons
        self.settings_button_frame = tk.Frame(content_frame)
        self.settings_button_frame.pack(pady=10)
        
        self.comm_settings_button = tk.Button(self.settings_button_frame, text="Communication Settings", 
                                            command=self.manage_communication_settings, width=18, state=tk.DISABLED)
        self.comm_settings_button.pack(side=tk.LEFT, padx=5)
        
        self.category_settings_button = tk.Button(self.settings_button_frame, text="Manage Categories", 
                                                command=self.manage_categories, width=15, state=tk.DISABLED)
        self.category_settings_button.pack(side=tk.LEFT, padx=5)
        
        self.checkin_settings_button = tk.Button(self.settings_button_frame, text="Check-in Settings", 
                                               command=self.manage_checkins, width=14, state=tk.DISABLED)
        self.checkin_settings_button.pack(side=tk.LEFT, padx=5)
        
        # Info label about test messages
        info_label = tk.Label(content_frame, text="Note: Test messages require the MHM service to be running", 
                             fg="gray", font=("Arial", 8, "italic"))
        info_label.pack(pady=(5, 0))
        
    def update_service_status(self):
        """Update the service status display"""
        is_running, pid = self.service_manager.is_service_running()
        if is_running:
            self.status_label.config(text=f"Running (PID: {pid})", fg="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Stopped", fg="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
    
    def start_service(self):
        """Start the service"""
        logger.info("Admin Panel: Starting service...")
        if self.service_manager.start_service():
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service start failed")
    
    def stop_service(self):
        """Stop the service"""
        logger.info("Admin Panel: Stop service requested")
        if self.service_manager.stop_service():
            logger.info("Admin Panel: Service stopped successfully")
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service stop failed")
    
    def restart_service(self):
        """Restart the service"""
        logger.info("Admin Panel: Restart service requested")
        if self.service_manager.restart_service():
            logger.info("Admin Panel: Service restarted successfully")
            self.update_service_status()
        else:
            logger.warning("Admin Panel: Service restart failed")
    
    def refresh_user_list(self):
        """Refresh the user dropdown list"""
        try:
            user_ids = core.utils.get_all_user_ids()
            user_display_names = []
            
            for user_id in user_ids:
                user_info = core.utils.get_user_info(user_id)
                internal_username = user_info.get('internal_username', 'Unknown')
                preferred_name = user_info.get('preferred_name', '')
                
                if preferred_name:
                    display_name = f"{preferred_name} ({internal_username}) - {user_id}"
                else:
                    display_name = f"{internal_username} - {user_id}"
                user_display_names.append(display_name)
            
            # Add blank option at the beginning
            dropdown_values = [""] + user_display_names
            self.user_dropdown['values'] = dropdown_values
            
            # Set to blank by default
            self.selected_user_id.set("")
            
            if user_display_names:
                logger.info(f"Found {len(user_display_names)} users")
            else:
                logger.info("No users found")
                
        except Exception as e:
            logger.error(f"Error refreshing user list: {e}")
            self.user_dropdown['values'] = []
    
    def on_user_selected(self, event=None):
        """Handle user selection from dropdown"""
        try:
            selected_display = self.selected_user_id.get()
            
            if not selected_display or selected_display == "":
                self.disable_content_management()
                return
                
            # Extract user_id from display name (format: "Name - user_id")
            if " - " in selected_display:
                user_id = selected_display.split(" - ")[-1]
                self.current_user_id = user_id
                
                # Update user info display
                user_info = core.utils.get_user_info(user_id)
                if not user_info:
                    logger.error(f"Admin Panel: Could not load user info for user_id: {user_id}")
                    self.disable_content_management()
                    return
                
                internal_username = user_info.get('internal_username', 'Unknown')
                info_text = f"Managing: {internal_username} ({user_id})"
                self.user_info_label.config(text=info_text, fg="black", font=("Arial", 9, "normal"))
                
                # Enable content management buttons
                self.enable_content_management()
                
                logger.info(f"Admin Panel: User selected for management: {user_id} ({internal_username})")
            else:
                logger.warning(f"Admin Panel: Could not parse user_id from selected_display: '{selected_display}'")
                self.disable_content_management()
                
        except Exception as e:
            logger.error(f"Admin Panel: Error handling user selection: {e}", exc_info=True)
            self.disable_content_management()
    
    def enable_content_management(self):
        """Enable content management buttons"""
        try:
            self.edit_messages_button.config(state=tk.NORMAL)
            self.edit_schedules_button.config(state=tk.NORMAL)
            self.send_test_button.config(state=tk.NORMAL)
            self.comm_settings_button.config(state=tk.NORMAL)
            self.category_settings_button.config(state=tk.NORMAL)
            self.checkin_settings_button.config(state=tk.NORMAL)
            logger.debug("Admin Panel: Content management buttons enabled successfully")
        except Exception as e:
            logger.error(f"Admin Panel: Error enabling content management buttons: {e}", exc_info=True)
    
    def disable_content_management(self):
        """Disable content management buttons"""
        self.edit_messages_button.config(state=tk.DISABLED)
        self.edit_schedules_button.config(state=tk.DISABLED)
        self.send_test_button.config(state=tk.DISABLED)
        self.comm_settings_button.config(state=tk.DISABLED)
        self.category_settings_button.config(state=tk.DISABLED)
        self.checkin_settings_button.config(state=tk.DISABLED)
        self.user_info_label.config(text="Select a user to manage content", 
                                   fg="gray", font=("Arial", 9, "italic"))
        self.current_user_id = None
    
    def create_new_user(self):
        """Open dialog to create a new user"""
        try:
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
            
        except Exception as e:
            logger.error(f"Admin Panel: Error creating new user: {e}")
            messagebox.showerror("Error", f"Failed to open create user dialog: {str(e)}")
    
    def edit_user_messages(self):
        """Open message editing interface for selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        try:
            logger.info(f"Admin Panel: Opening message editor for user {self.current_user_id}")
            # Temporarily set the user context for editing
            original_user = UserContext().get_user_id()
            UserContext().set_user_id(self.current_user_id)
            
            # Get user categories
            categories = core.utils.get_user_preferences(self.current_user_id).get('categories', [])
            
            if not categories:
                logger.info(f"Admin Panel: User {self.current_user_id} has no message categories configured")
                messagebox.showinfo("No Categories", "This user has no message categories configured.")
                return
            
            # Open category selection dialog
            category_window = tk.Toplevel(self.root)
            category_window.title(f"Select Category - {self.current_user_id}")
            category_window.geometry("300x200")
            
            tk.Label(category_window, text="Select message category to edit:", font=("Arial", 12)).pack(pady=10)
            
            for category in categories:
                tk.Button(category_window, text=core.utils.title_case(category), 
                         command=lambda c=category: self.open_message_editor(category_window, c),
                         width=20).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error opening message editor for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to open message editor: {str(e)}")
            # Restore original user context
            if 'original_user' in locals() and original_user:
                UserContext().set_user_id(original_user)
    
    def open_message_editor(self, parent_window, category):
        """Open the message editing window for a specific category"""
        try:
            logger.info(f"Admin Panel: Opening message editor for user {self.current_user_id}, category {category}")
            parent_window.destroy()
            setup_view_edit_messages_window(self.root, category)
        except Exception as e:
            logger.error(f"Admin Panel: Error opening message editor for user {self.current_user_id}, category {category}: {e}")
            messagebox.showerror("Error", f"Failed to open message editor: {str(e)}")
    
    def edit_user_schedules(self):
        """Open schedule editing interface for selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        try:
            logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user_id}")
            # Temporarily set the user context for editing
            original_user = UserContext().get_user_id()
            UserContext().set_user_id(self.current_user_id)
            
            # Get user categories
            categories = core.utils.get_user_preferences(self.current_user_id).get('categories', [])
            
            if not categories:
                logger.info(f"Admin Panel: User {self.current_user_id} has no schedule categories configured")
                messagebox.showinfo("No Categories", "This user has no message categories configured.")
                return
            
            # Open category selection dialog
            category_window = tk.Toplevel(self.root)
            category_window.title(f"Select Category - {self.current_user_id}")
            category_window.geometry("300x200")
            
            tk.Label(category_window, text="Select category to edit schedule:", font=("Arial", 12)).pack(pady=10)
            
            for category in categories:
                tk.Button(category_window, text=core.utils.title_case(category), 
                         command=lambda c=category: self.open_schedule_editor(category_window, c),
                         width=20).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error opening schedule editor for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to open schedule editor: {str(e)}")
            # Restore original user context
            if 'original_user' in locals() and original_user:
                UserContext().set_user_id(original_user)
    
    def open_schedule_editor(self, parent_window, category):
        """Open the schedule editing window for a specific category"""
        try:
            logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user_id}, category {category}")
            parent_window.destroy()
            setup_view_edit_schedule_window(self.root, category, None)  # None = no scheduler manager (UI-only mode)
        except Exception as e:
            logger.error(f"Admin Panel: Error opening schedule editor for user {self.current_user_id}, category {category}: {e}")
            messagebox.showerror("Error", f"Failed to open schedule editor: {str(e)}")
    
    def send_test_message(self):
        """Send a test message for the selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        # Check if service is running - required for test messages
        is_running, pid = self.service_manager.is_service_running()
        if not is_running:
            logger.warning(f"Admin Panel: Test message request failed - service not running for user {self.current_user_id}")
            messagebox.showerror("Service Required", 
                               "The MHM service must be running to send test messages.\n\n"
                               "The service manages all communication channels. Please:\n"
                               "1. Click 'Start Service' above\n"
                               "2. Wait for service to initialize\n"
                               "3. Try sending the test message again\n\n"
                               "The admin panel does not create its own communication channels.")
            return
        
        try:
            logger.info(f"Admin Panel: Preparing test message for user {self.current_user_id}")
            # Get user categories
            categories = core.utils.get_user_preferences(self.current_user_id).get('categories', [])
            
            if not categories:
                logger.info(f"Admin Panel: User {self.current_user_id} has no message categories for test")
                messagebox.showinfo("No Categories", "This user has no message categories configured.")
                return
            
            # Open category selection dialog for test message
            category_window = tk.Toplevel(self.root)
            category_window.title(f"Send Test Message - {self.current_user_id}")
            category_window.geometry("300x200")
            
            tk.Label(category_window, text="Select category for test message:", font=("Arial", 12)).pack(pady=10)
            
            for category in categories:
                tk.Button(category_window, text=core.utils.title_case(category), 
                         command=lambda c=category: self.confirm_test_message(category_window, c),
                         width=20).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error preparing test message for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to prepare test message: {str(e)}")
    
    def confirm_test_message(self, parent_window, category):
        """Confirm and send test message"""
        try:
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
            
        except Exception as e:
            logger.error(f"Admin Panel: Error sending test message for user {self.current_user_id}, category {category}: {e}")
            messagebox.showerror("Error", f"Failed to send test message: {str(e)}")
    
    def send_actual_test_message(self, category):
        """Send a test message via the running service"""
        try:
            # Since service is running, we'll create a minimal communication to the service
            # For now, we'll use a simple approach: create a test message file that the service can pick up
            # This is safer than trying to inject into the running service's communication channels
            
            # Store original user context and set to selected user
            original_user = UserContext().get_user_id()
            UserContext().set_user_id(self.current_user_id)
            
            try:
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
                
            finally:
                # Restore original user context
                if original_user:
                    UserContext().set_user_id(original_user)
                else:
                    UserContext().set_user_id(None)
            
        except Exception as e:
            logger.error(f"Error creating test message request: {e}")
            messagebox.showerror("Test Message Request Failed", 
                f"Failed to create test message request: {str(e)}\n\n"
                f"Make sure the user has:\n"
                f"• A configured messaging service\n"
                f"• Valid recipient information\n"
                f"• Messages in the {category} category")
    
    def manage_communication_settings(self):
        """Open communication settings management for selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        try:
            logger.info(f"Admin Panel: Opening communication settings for user {self.current_user_id}")
            from ui.account_manager import setup_communication_settings_window
            setup_communication_settings_window(self.root, self.current_user_id)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error opening communication settings for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to open communication settings: {str(e)}")
    
    def manage_categories(self):
        """Open category management for selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        try:
            logger.info(f"Admin Panel: Opening category management for user {self.current_user_id}")
            from ui.account_manager import setup_category_management_window
            setup_category_management_window(self.root, self.current_user_id)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error opening category management for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to open category management: {str(e)}")

    def manage_checkins(self):
        """Open check-in settings management for selected user"""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showwarning("No User Selected", "Please select a user first.")
            return
            
        try:
            logger.info(f"Admin Panel: Opening check-in management for user {self.current_user_id}")
            from ui.account_manager import setup_checkin_management_window
            setup_checkin_management_window(self.root, self.current_user_id)
            
        except Exception as e:
            logger.error(f"Admin Panel: Error opening check-in management for user {self.current_user_id}: {e}")
            messagebox.showerror("Error", f"Failed to open check-in management: {str(e)}")
    
    def shutdown_ui_components(self, communication_manager=None):
        """Shutdown any UI-created components gracefully"""
        logger.info("Shutting down admin panel.")
        try:
            if communication_manager:
                logger.debug("Stopping communication manager (legacy UI instance).")
                communication_manager.stop_all()
            # Admin panel no longer creates its own communication manager
            logger.debug("Admin panel cleanup complete - no communication channels to stop.")
        except Exception as e:
            logger.error(f"Error during admin panel shutdown: {e}", exc_info=True)
        finally:
            logger.info("Admin panel shutdown complete.")
    
    def on_closing(self):
        """Handle window close event"""
        self.shutdown_ui_components()
        self.root.destroy()

def main():
    """Main entry point for the UI application"""
    try:
        root = tk.Tk()
        app = MHMManagerUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error starting UI application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main() 