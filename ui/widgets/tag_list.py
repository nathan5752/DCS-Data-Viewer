"""
Tag list widget with checkboxes for selecting tags to plot.
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from ui.widgets.tag_list_item import TagListItemWidget


class TagList(QListWidget):
    """List widget for displaying and selecting tags with checkboxes and axis controls."""

    # Signal emitted when a tag's check state changes
    # Emits: (tag_name, is_checked)
    tag_check_changed = pyqtSignal(str, bool)

    # Signal emitted when user requests to change a tag's axis
    # Emits: (tag_name, target_axis)
    axis_change_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.display_mode = "tag"  # "tag" or "description"
        self.tag_descriptions = {}  # Store {tag_name: description}
        self.tag_widgets = {}  # Store {tag_name: TagListItemWidget}

    def clear(self):
        """
        Override clear to also clean up tag_widgets and tag_descriptions dictionaries.
        This prevents RuntimeError when trying to access deleted widgets after reset.
        """
        super().clear()  # Clear the QListWidget items
        self.tag_widgets.clear()  # Clear the widget references
        self.tag_descriptions.clear()  # Clear descriptions too

    def populate_tags(self, tag_names: list, descriptions: dict = None):
        """
        Populate the list with tag names and descriptions.

        Args:
            tag_names: List of tag names
            descriptions: Dictionary mapping tag names to descriptions {tag_name: description}
        """
        # Block signals while populating to avoid triggering check changed events
        self.blockSignals(True)
        self.clear()
        self.tag_widgets.clear()

        # Store descriptions for later use
        self.tag_descriptions = descriptions if descriptions else {}

        for tag_name in tag_names:
            # Determine display text based on current display mode
            if self.display_mode == "description" and tag_name in self.tag_descriptions:
                display_text = self.tag_descriptions[tag_name]
            else:
                display_text = tag_name

            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, tag_name)
            self.addItem(item)

            # Create custom widget for this item
            widget = TagListItemWidget(tag_name, display_text)
            widget.check_state_changed.connect(self._on_item_check_changed)
            widget.axis_change_requested.connect(self._on_axis_change_requested)

            # Set the custom widget for this item
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

            # Store reference
            self.tag_widgets[tag_name] = widget

        self.blockSignals(False)

    def _on_item_check_changed(self, tag_name: str, is_checked: bool):
        """
        Handle item check state changes from custom widgets.

        Args:
            tag_name: The tag name
            is_checked: Whether it's now checked
        """
        self.tag_check_changed.emit(tag_name, is_checked)

    def _on_axis_change_requested(self, tag_name: str, target_axis: str):
        """
        Handle axis change requests from custom widgets.

        Args:
            tag_name: The tag name
            target_axis: The target axis ('left' or 'right')
        """
        self.axis_change_requested.emit(tag_name, target_axis)

    def get_checked_tags(self) -> list:
        """
        Get list of currently checked tag names.

        Returns:
            List of checked tag names
        """
        checked_tags = []
        for tag_name, widget in self.tag_widgets.items():
            if widget.is_checked():
                checked_tags.append(tag_name)
        return checked_tags

    def set_tag_checked(self, tag_name: str, checked: bool):
        """
        Set the check state of a specific tag.

        Args:
            tag_name: Name of the tag
            checked: Whether to check or uncheck
        """
        if tag_name in self.tag_widgets:
            self.tag_widgets[tag_name].set_checked(checked)

    def set_checked_tags(self, tag_names: list):
        """
        Set multiple tags as checked.

        Args:
            tag_names: List of tag names to check
        """
        self.blockSignals(True)
        for tag_name in tag_names:
            self.set_tag_checked(tag_name, True)
        self.blockSignals(False)

    def update_tag_axis_display(self, tag_name: str, axis: str):
        """
        Update the axis display for a specific tag.

        Args:
            tag_name: Name of the tag
            axis: The axis ('left' or 'right')
        """
        if tag_name in self.tag_widgets:
            self.tag_widgets[tag_name].update_axis_display(axis)

    def filter_tags(self, text: str):
        """
        Filter the tag list based on search text.

        Args:
            text: Search text to filter by (case-insensitive)
        """
        search_text = text.lower()
        for i in range(self.count()):
            item = self.item(i)
            tag_name = item.data(Qt.ItemDataRole.UserRole)

            # Get both tag name and description for matching
            tag_name_lower = tag_name.lower() if tag_name else ""
            description = self.tag_descriptions.get(tag_name, "").lower()

            # Show item if search text is empty or found in either tag name or description
            if search_text:
                is_match = search_text in tag_name_lower or search_text in description
            else:
                is_match = True
            item.setHidden(not is_match)

    def set_display_mode(self, mode: str):
        """
        Set the display mode to show either tag names or descriptions.

        Args:
            mode: "tag" to display tag names, "description" to display descriptions
        """
        if mode not in ["tag", "description"]:
            return

        # Update display mode
        self.display_mode = mode

        # Update display text for all custom widgets
        for tag_name, widget in self.tag_widgets.items():
            # Determine new display text based on mode
            if mode == "description" and tag_name in self.tag_descriptions:
                display_text = self.tag_descriptions[tag_name]
            else:
                display_text = tag_name

            widget.update_display_text(display_text)

    def set_axis_buttons_enabled(self, enabled: bool):
        """
        Enable or disable all axis buttons.
        Used to disable axis changing when in compare mode.

        Args:
            enabled: True to enable all buttons, False to disable
        """
        for tag_name, widget in self.tag_widgets.items():
            widget.set_axis_button_enabled(enabled)
