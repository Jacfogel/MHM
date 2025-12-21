# process_watcher_dialog.py - Process Watcher Dialog

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from core.logger import get_component_logger
from core.error_handling import handle_errors
import psutil
from datetime import datetime

# Route process watcher logs to UI component
process_logger = get_component_logger('process_watcher')
logger = process_logger

class ProcessWatcherDialog(QDialog):
    """Dialog for monitoring Python processes and their associations."""
    
    # ERROR_HANDLING_EXCLUDE: Dialog constructor - errors should propagate so caller knows initialization failed
    def __init__(self, parent=None):
        """
        Initialize the ProcessWatcherDialog.
        
        Args:
            parent: Parent widget for the dialog
        """
        super().__init__(parent)
        self.setWindowTitle("Process Watcher - Python Processes")
        self.setModal(False)  # Allow multiple instances
        self.resize(1000, 700)
        self.setup_ui()
        self.setup_timer()
        # Initial refresh to populate the tables
        self.refresh_processes()
        logger.debug("Process watcher dialog initialized successfully")
    
    @handle_errors("setting up process watcher UI")
    def setup_ui(self):
        """Setup the UI components."""
        try:
            layout = QVBoxLayout(self)
            
            # Title and refresh button
            header_layout = QHBoxLayout()
            title_label = QLabel("Python Process Monitor")
            title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header_layout.addWidget(title_label)
            
            header_layout.addStretch()
            
            self.refresh_button = QPushButton("Refresh")
            self.refresh_button.clicked.connect(self.refresh_processes)
            header_layout.addWidget(self.refresh_button)
            
            self.auto_refresh_checkbox = QPushButton("Auto Refresh: OFF")
            self.auto_refresh_checkbox.setCheckable(True)
            self.auto_refresh_checkbox.clicked.connect(self.toggle_auto_refresh)
            header_layout.addWidget(self.auto_refresh_checkbox)
            
            layout.addLayout(header_layout)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # All Python Processes Tab
            self.setup_all_processes_tab()
            
            # MHM Service Processes Tab
            self.setup_mhm_processes_tab()
            
            # Process Details Tab
            self.setup_process_details_tab()
            
            logger.debug("Process watcher UI setup completed")
        except Exception as e:
            logger.error(f"Error setting up process watcher UI: {e}")
            raise
    
    @handle_errors("setting up all processes tab")
    def setup_all_processes_tab(self):
        """Setup the tab showing all Python processes."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # All Python processes table
            self.all_processes_table = QTableWidget()
            self.all_processes_table.setColumnCount(6)
            self.all_processes_table.setHorizontalHeaderLabels([
                "PID", "Name", "Command Line", "CPU %", "Memory %", "Start Time"
            ])
            
            # Set column widths
            header = self.all_processes_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # PID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Name
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Command Line
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # CPU %
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Memory %
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Start Time
            
            self.all_processes_table.setColumnWidth(0, 80)   # PID
            self.all_processes_table.setColumnWidth(1, 120)   # Name
            self.all_processes_table.setColumnWidth(3, 80)    # CPU %
            self.all_processes_table.setColumnWidth(4, 80)    # Memory %
            self.all_processes_table.setColumnWidth(5, 150)   # Start Time
            
            # Connect selection change
            self.all_processes_table.itemSelectionChanged.connect(self.on_process_selected)
            
            layout.addWidget(self.all_processes_table)
            self.tab_widget.addTab(tab, "All Python Processes")
            
        except Exception as e:
            logger.error(f"Error setting up all processes tab: {e}")
            raise
    
    @handle_errors("setting up MHM processes tab")
    def setup_mhm_processes_tab(self):
        """Setup the tab showing MHM-specific processes."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # MHM processes table
            self.mhm_processes_table = QTableWidget()
            self.mhm_processes_table.setColumnCount(7)
            self.mhm_processes_table.setHorizontalHeaderLabels([
                "PID", "Type", "Command Line", "CPU %", "Memory %", "Start Time", "Status"
            ])
            
            # Set column widths
            header = self.mhm_processes_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # PID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Type
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Command Line
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # CPU %
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Memory %
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Start Time
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Status
            
            self.mhm_processes_table.setColumnWidth(0, 80)   # PID
            self.mhm_processes_table.setColumnWidth(1, 100)   # Type
            self.mhm_processes_table.setColumnWidth(3, 80)    # CPU %
            self.mhm_processes_table.setColumnWidth(4, 80)    # Memory %
            self.mhm_processes_table.setColumnWidth(5, 150)   # Start Time
            self.mhm_processes_table.setColumnWidth(6, 100)   # Status
            
            layout.addWidget(self.mhm_processes_table)
            self.tab_widget.addTab(tab, "MHM Services")
            
        except Exception as e:
            logger.error(f"Error setting up MHM processes tab: {e}")
            raise
    
    @handle_errors("setting up process details tab")
    def setup_process_details_tab(self):
        """Setup the tab showing detailed process information."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # Process details text area
            self.process_details_text = QTextEdit()
            self.process_details_text.setReadOnly(True)
            self.process_details_text.setFont(QFont("Consolas", 9))
            
            layout.addWidget(self.process_details_text)
            self.tab_widget.addTab(tab, "Process Details")
            
        except Exception as e:
            logger.error(f"Error setting up process details tab: {e}")
            raise
    
    @handle_errors("setting up timer")
    def setup_timer(self):
        """Setup the auto-refresh timer."""
        try:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_processes)
            self.auto_refresh_enabled = False
        except Exception as e:
            logger.error(f"Error setting up timer: {e}")
            raise
    
    @handle_errors("toggling auto refresh")
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        try:
            self.auto_refresh_enabled = not self.auto_refresh_enabled
            
            if self.auto_refresh_enabled:
                self.auto_refresh_checkbox.setText("Auto Refresh: ON")
                self.auto_refresh_checkbox.setStyleSheet("background-color: lightgreen;")
                self.refresh_timer.start(5000)  # Refresh every 5 seconds
                logger.debug("Auto-refresh enabled")
            else:
                self.auto_refresh_checkbox.setText("Auto Refresh: OFF")
                self.auto_refresh_checkbox.setStyleSheet("")
                self.refresh_timer.stop()
                logger.debug("Auto-refresh disabled")
        except Exception as e:
            logger.error(f"Error toggling auto refresh: {e}")
    
    @handle_errors("refreshing processes")
    def refresh_processes(self):
        """Refresh the process information."""
        try:
            logger.debug("Refreshing process information")
            self.update_all_processes()
            self.update_mhm_processes()
        except Exception as e:
            logger.error(f"Error refreshing processes: {e}")
    
    @handle_errors("updating all processes")
    def update_all_processes(self):
        """Update the all processes table."""
        try:
            # Get all Python processes
            python_processes = []
            logger.debug("Scanning for Python processes...")
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                        logger.debug(f"Found Python process: PID {proc.info['pid']}, Name: {proc.info['name']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            logger.debug(f"Found {len(python_processes)} Python processes")
            
            # Update table
            self.all_processes_table.setRowCount(len(python_processes))
            logger.debug(f"Setting table row count to {len(python_processes)}")
            
            for row, proc_info in enumerate(python_processes):
                logger.debug(f"Adding row {row}: PID {proc_info['pid']}")
                
                # PID
                self.all_processes_table.setItem(row, 0, QTableWidgetItem(str(proc_info['pid'])))
                
                # Name
                self.all_processes_table.setItem(row, 1, QTableWidgetItem(proc_info['name'] or 'Unknown'))
                
                # Command Line
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'N/A'
                self.all_processes_table.setItem(row, 2, QTableWidgetItem(cmdline))
                
                # CPU %
                self.all_processes_table.setItem(row, 3, QTableWidgetItem(f"{proc_info['cpu_percent']:.1f}%"))
                
                # Memory %
                self.all_processes_table.setItem(row, 4, QTableWidgetItem(f"{proc_info['memory_percent']:.1f}%"))
                
                # Start Time
                start_time = datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                self.all_processes_table.setItem(row, 5, QTableWidgetItem(start_time))
            
            logger.debug(f"Updated all processes table with {len(python_processes)} processes")
        except Exception as e:
            logger.error(f"Error updating all processes: {e}")
    
    @handle_errors("updating MHM processes")
    def update_mhm_processes(self):
        """Update the MHM processes table."""
        try:
            # Import here to avoid circular imports
            from core.service_utilities import get_service_processes
            
            # Get MHM service processes
            logger.debug("Getting MHM service processes...")
            service_processes = get_service_processes()
            logger.debug(f"Found {len(service_processes)} MHM service processes")
            
            # Update table
            self.mhm_processes_table.setRowCount(len(service_processes))
            
            for row, proc_info in enumerate(service_processes):
                # PID
                self.mhm_processes_table.setItem(row, 0, QTableWidgetItem(str(proc_info['pid'])))
                
                # Type
                process_type = proc_info.get('process_type', 'unknown')
                type_item = QTableWidgetItem(process_type)
                
                # Color code by type
                if process_type == 'headless':
                    type_item.setBackground(Qt.GlobalColor.blue)
                elif process_type == 'ui_managed':
                    type_item.setBackground(Qt.GlobalColor.green)
                else:
                    type_item.setBackground(Qt.GlobalColor.gray)
                
                self.mhm_processes_table.setItem(row, 1, type_item)
                
                # Command Line
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'N/A'
                self.mhm_processes_table.setItem(row, 2, QTableWidgetItem(cmdline))
                
                # Get additional process info
                try:
                    proc = psutil.Process(proc_info['pid'])
                    cpu_percent = proc.cpu_percent()
                    memory_percent = proc.memory_percent()
                    status = proc.status()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu_percent = 0.0
                    memory_percent = 0.0
                    status = 'Unknown'
                
                # CPU %
                self.mhm_processes_table.setItem(row, 3, QTableWidgetItem(f"{cpu_percent:.1f}%"))
                
                # Memory %
                self.mhm_processes_table.setItem(row, 4, QTableWidgetItem(f"{memory_percent:.1f}%"))
                
                # Start Time
                start_time = datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                self.mhm_processes_table.setItem(row, 5, QTableWidgetItem(start_time))
                
                # Status
                self.mhm_processes_table.setItem(row, 6, QTableWidgetItem(status))
            
            logger.debug(f"Updated MHM processes table with {len(service_processes)} processes")
        except Exception as e:
            logger.error(f"Error updating MHM processes: {e}")
    
    @handle_errors("handling process selection")
    def on_process_selected(self):
        """Handle process selection change."""
        try:
            current_tab = self.tab_widget.currentIndex()
            
            if current_tab == 0:  # All processes tab
                self.update_process_details_from_all()
            elif current_tab == 1:  # MHM processes tab
                self.update_process_details_from_mhm()
        except Exception as e:
            logger.error(f"Error handling process selection: {e}")
    
    @handle_errors("updating process details from all processes")
    def update_process_details_from_all(self):
        """Update process details from all processes table."""
        try:
            current_row = self.all_processes_table.currentRow()
            if current_row < 0:
                return
            
            pid_item = self.all_processes_table.item(current_row, 0)
            if not pid_item:
                return
            
            pid = int(pid_item.text())
            self.show_process_details(pid)
        except Exception as e:
            logger.error(f"Error updating process details from all processes: {e}")
    
    @handle_errors("updating process details from MHM processes")
    def update_process_details_from_mhm(self):
        """Update process details from MHM processes table."""
        try:
            current_row = self.mhm_processes_table.currentRow()
            if current_row < 0:
                return
            
            pid_item = self.mhm_processes_table.item(current_row, 0)
            if not pid_item:
                return
            
            pid = int(pid_item.text())
            self.show_process_details(pid)
        except Exception as e:
            logger.error(f"Error updating process details from MHM processes: {e}")
    
    @handle_errors("showing process details")
    def show_process_details(self, pid):
        """Show detailed information about a process."""
        try:
            try:
                proc = psutil.Process(pid)
                
                details = f"Process Details for PID {pid}\n"
                details += "=" * 50 + "\n\n"
                
                # Basic info
                details += f"Name: {proc.name()}\n"
                details += f"Status: {proc.status()}\n"
                details += f"Create Time: {datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')}\n"
                details += f"CPU Percent: {proc.cpu_percent():.1f}%\n"
                details += f"Memory Percent: {proc.memory_percent():.1f}%\n"
                details += f"Memory Info: {proc.memory_info()}\n\n"
                
                # Command line
                details += "Command Line:\n"
                details += "-" * 20 + "\n"
                cmdline = proc.cmdline()
                for i, arg in enumerate(cmdline):
                    details += f"{i:2d}: {arg}\n"
                details += "\n"
                
                # Environment (first 10 variables)
                details += "Environment Variables (first 10):\n"
                details += "-" * 35 + "\n"
                try:
                    env = proc.environ()
                    for i, (key, value) in enumerate(list(env.items())[:10]):
                        details += f"{key} = {value}\n"
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    details += "Access denied\n"
                details += "\n"
                
                # Connections
                details += "Network Connections:\n"
                details += "-" * 20 + "\n"
                try:
                    connections = proc.connections()
                    if connections:
                        for conn in connections[:5]:  # First 5 connections
                            details += f"  {conn}\n"
                    else:
                        details += "  No connections\n"
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    details += "  Access denied\n"
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                details = f"Error accessing process {pid}: {e}\n"
                details += "Process may have terminated or access is denied."
            
            self.process_details_text.setPlainText(details)
            
        except Exception as e:
            logger.error(f"Error showing process details: {e}")
            self.process_details_text.setPlainText(f"Error: {e}")
    
    @handle_errors("closing process watcher dialog", user_friendly=False, default_return=None)
    def closeEvent(self, event):
        """Handle dialog close event."""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        logger.debug("Process watcher dialog closed")
        event.accept()
