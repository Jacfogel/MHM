# tag_widget.py - Flexible tag widget for both management and selection

import sys
import os

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QWidget, QListWidgetItem, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from ui.generated.tag_widget_pyqt import Ui_Widget_tag
from tasks.task_management import add_user_task_tag, remove_user_task_tag
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

setup_logging()
logger = get_component_logger('ui')
widget_logger = logger

class TagWidget(QWidget):
    """Flexible tag widget that can work in management or selection mode."""
    
    tags_changed = Signal()  # Signal emitted when tags are modified
    
    @handle_errors("initializing tag widget")
    def __init__(self, parent=None, user_id=None, mode="management", selected_tags=None, title="Task Tags"):
        """Initialize the tag widget.
        
        Args:
            parent: Parent widget
            user_id: User ID for loading/saving tags
            mode: "management" for full CRUD operations, "selection" for checkbox selection
            selected_tags: List of currently selected tags (for selection mode)
            title: Title for the group box
        """
        super().__init__(parent)
        self.user_id = user_id
        self.mode = mode
        self.selected_tags = selected_tags or []
        self.title = title
        self.available_tags = []
        self.deleted_tags = []  # For undo functionality during account creation
        
        self.ui = Ui_Widget_tag()
        self.ui.setupUi(self)
        
        self.setup_ui()
        self.setup_connections()
        self.load_tags()
    
    @handle_errors("setting up UI")
    def setup_ui(self):
        """Setup the UI components based on mode."""
        # Set the group box title
        self.ui.groupBox_tags.setTitle(self.title)
        
        # Configure list widget based on mode
        if self.mode == "selection":
            # Selection mode: use checkboxes, single selection
            self.ui.listWidget_tags.setSelectionMode(self.ui.listWidget_tags.SelectionMode.SingleSelection)
        else:
            # Management mode: use single selection for edit/delete
            self.ui.listWidget_tags.setSelectionMode(self.ui.listWidget_tags.SelectionMode.SingleSelection)
        
        # Show/hide buttons based on mode
        if self.mode == "selection":
            # In selection mode, hide edit/delete buttons
            self.ui.pushButton_edit_tag.setVisible(False)
            self.ui.pushButton_delete_tag.setVisible(False)
    
    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        # Connect tag management buttons
        self.ui.pushButton_add_tag.clicked.connect(self.add_tag)
        self.ui.lineEdit_new_tag.returnPressed.connect(self.add_tag)
        
        if self.mode == "management":
            # Management mode connections
            self.ui.pushButton_edit_tag.clicked.connect(self.edit_tag)
            self.ui.pushButton_delete_tag.clicked.connect(self.delete_tag)
            self.ui.pushButton_undo_delete.clicked.connect(self.undo_last_tag_delete)
            self.ui.listWidget_tags.itemSelectionChanged.connect(self.update_button_states)
        else:
            # Selection mode connections
            self.ui.listWidget_tags.itemChanged.connect(self.on_tag_selection_changed)
    
    @handle_errors("loading tags")
    def load_tags(self):
        """Load the user's tags."""
        if not self.user_id:
            return
            
        try:
            prefs_result = get_user_data(self.user_id, 'preferences')
            preferences_data = prefs_result.get('preferences', {}) if prefs_result else {}
            task_settings = preferences_data.get('task_settings', {})
            self.available_tags = task_settings.get('tags', [])
            self.refresh_tag_list()
            if self.mode == "management":
                self.update_button_states()
        except Exception as e:
            logger.error(f"Error loading tags for user {self.user_id}: {e}")

    @handle_errors("refreshing tag list")
    def refresh_tag_list(self):
        """Refresh the tag list display."""
        self.ui.listWidget_tags.clear()
        
        for tag in self.available_tags:
            item = QListWidgetItem(tag)
            
            if self.mode == "selection":
                # Selection mode: add checkboxes
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                if tag in self.selected_tags:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
            else:
                # Management mode: no checkboxes
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            
            self.ui.listWidget_tags.addItem(item)

    @handle_errors("updating button states")
    def update_button_states(self):
        """Update button enabled states based on selection (management mode only)."""
        if self.mode != "management":
            return
            
        has_selection = len(self.ui.listWidget_tags.selectedItems()) > 0
        self.ui.pushButton_edit_tag.setEnabled(has_selection)
        self.ui.pushButton_delete_tag.setEnabled(has_selection)
        
        # Enable undo button only if there are deleted tags to restore (during account creation)
        has_deleted_tags = not self.user_id and len(self.deleted_tags) > 0
        self.ui.pushButton_undo_delete.setEnabled(has_deleted_tags)

    @handle_errors("handling tag selection change")
    def on_tag_selection_changed(self, item):
        """Handle when a tag checkbox is changed (selection mode only)."""
        if self.mode != "selection":
            return
            
        tag = item.text()
        if item.checkState() == Qt.CheckState.Checked:
            if tag not in self.selected_tags:
                self.selected_tags.append(tag)
        else:
            if tag in self.selected_tags:
                self.selected_tags.remove(tag)
        self.tags_changed.emit()

    @handle_errors("adding tag")
    def add_tag(self):
        """Add a new tag."""
        tag_text = self.ui.lineEdit_new_tag.text().strip()
        if not tag_text:
            QMessageBox.warning(self, "Validation Error", "Please enter a tag name.")
            return
        
        if tag_text in self.available_tags:
            QMessageBox.warning(self, "Duplicate Tag", f"Tag '{tag_text}' already exists.")
            return
        
        try:
            # Handle case where user_id is None (during account creation)
            if not self.user_id:
                # During account creation, just add to local list
                self.available_tags.append(tag_text)
                self.refresh_tag_list()
                self.ui.lineEdit_new_tag.clear()
                
                # In selection mode, automatically select newly added tag
                if self.mode == "selection" and tag_text not in self.selected_tags:
                    self.selected_tags.append(tag_text)
                
                self.tags_changed.emit()
                logger.info(f"Added tag '{tag_text}' to local list (account creation mode)")
            else:
                # Normal mode - save to database
                if add_user_task_tag(self.user_id, tag_text):
                    self.available_tags.append(tag_text)
                    self.refresh_tag_list()
                    self.ui.lineEdit_new_tag.clear()
                    
                    # In selection mode, automatically select newly added tag
                    if self.mode == "selection" and tag_text not in self.selected_tags:
                        self.selected_tags.append(tag_text)
                    
                    self.tags_changed.emit()
                    logger.info(f"Added tag '{tag_text}' for user {self.user_id}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to add tag '{tag_text}'.")
        except Exception as e:
            logger.error(f"Error adding tag '{tag_text}' for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add tag: {e}")

    @handle_errors("editing tag")
    def edit_tag(self):
        """Edit the selected tag (management mode only)."""
        if self.mode != "management":
            return
            
        selected_items = self.ui.listWidget_tags.selectedItems()
        if not selected_items:
            return
        
        old_tag = selected_items[0].text()
        
        new_tag, ok = QInputDialog.getText(self, "Edit Tag", 
                                         f"Enter new name for tag '{old_tag}':",
                                         text=old_tag)
        
        if not ok or not new_tag.strip():
            return
        
        new_tag = new_tag.strip()
        if new_tag == old_tag:
            return
        
        if new_tag in self.available_tags:
            QMessageBox.warning(self, "Duplicate Tag", f"Tag '{new_tag}' already exists.")
            return
        
        try:
            # Handle case where user_id is None (during account creation)
            if not self.user_id:
                # During account creation, just update local list
                index = self.available_tags.index(old_tag)
                self.available_tags[index] = new_tag
                self.refresh_tag_list()
                self.tags_changed.emit()
                logger.info(f"Edited tag '{old_tag}' to '{new_tag}' in local list (account creation mode)")
            else:
                # Normal mode - save to database
                if remove_user_task_tag(self.user_id, old_tag) and add_user_task_tag(self.user_id, new_tag):
                    # Update local list
                    index = self.available_tags.index(old_tag)
                    self.available_tags[index] = new_tag
                    self.refresh_tag_list()
                    self.tags_changed.emit()
                    logger.info(f"Edited tag '{old_tag}' to '{new_tag}' for user {self.user_id}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to edit tag '{old_tag}'.")
        except Exception as e:
            logger.error(f"Error editing tag '{old_tag}' to '{new_tag}' for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit tag: {e}")

    @handle_errors("deleting tag")
    def delete_tag(self):
        """Delete the selected tag (management mode only)."""
        if self.mode != "management":
            return
            
        selected_items = self.ui.listWidget_tags.selectedItems()
        if not selected_items:
            return
        
        tag_to_delete = selected_items[0].text()
        
        # Confirm deletion
        if not self.user_id:
            # During account creation - no tasks exist yet
            reply = QMessageBox.question(self, "Confirm Deletion", 
                                       f"Are you sure you want to delete the tag '{tag_to_delete}'?\n\n"
                                       "This tag will be removed from your account settings.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            # Normal mode - tasks might exist
            reply = QMessageBox.question(self, "Confirm Deletion", 
                                       f"Are you sure you want to delete the tag '{tag_to_delete}'?\n\n"
                                       "This will remove the tag from all tasks that use it.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Handle case where user_id is None (during account creation)
            if not self.user_id:
                # During account creation, just remove from local list
                self.available_tags.remove(tag_to_delete)
                # Store for undo functionality
                self.deleted_tags.append(tag_to_delete)
                self.refresh_tag_list()
                self.update_button_states()
                self.tags_changed.emit()
                logger.info(f"Deleted tag '{tag_to_delete}' from local list (account creation mode)")
            else:
                # Normal mode - save to database
                if remove_user_task_tag(self.user_id, tag_to_delete):
                    self.available_tags.remove(tag_to_delete)
                    self.refresh_tag_list()
                    self.update_button_states()
                    self.tags_changed.emit()
                    logger.info(f"Deleted tag '{tag_to_delete}' for user {self.user_id}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete tag '{tag_to_delete}'.")
        except Exception as e:
            logger.error(f"Error deleting tag '{tag_to_delete}' for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete tag: {e}")

    @handle_errors("getting available tags")
    def get_available_tags(self):
        """Get the current list of available tags."""
        return self.available_tags.copy()
    
    @handle_errors("getting selected tags")
    def get_selected_tags(self):
        """Get the currently selected tags (selection mode only)."""
        if self.mode == "selection":
            return self.selected_tags.copy()
        return []
    
    @handle_errors("setting selected tags")
    def set_selected_tags(self, tags):
        """Set the selected tags (selection mode only)."""
        if self.mode == "selection":
            self.selected_tags = tags.copy()
            self.refresh_tag_list()
    
    @handle_errors("refreshing tags")
    def refresh_tags(self):
        """Refresh the tags in the tag widget."""
        self.load_tags()
    
    @handle_errors("undoing last tag delete")
    def undo_last_tag_delete(self):
        """Undo the last tag deletion (account creation mode only)."""
        if not self.user_id and self.deleted_tags:
            # During account creation, restore the last deleted tag
            tag_to_restore = self.deleted_tags.pop()
            if tag_to_restore not in self.available_tags:
                self.available_tags.append(tag_to_restore)
                self.refresh_tag_list()
                self.tags_changed.emit()
                logger.info(f"Restored tag '{tag_to_restore}' (account creation mode)")
                return True
        return False 