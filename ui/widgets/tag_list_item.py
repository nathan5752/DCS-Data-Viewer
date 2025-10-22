"""
Custom widget for tag list items with axis override controls.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
import config


class TagListItemWidget(QWidget):
    """Custom widget for a single tag list item with checkbox and axis toggle."""

    # Signals
    check_state_changed = pyqtSignal(str, bool)  # (tag_name, is_checked)
    axis_change_requested = pyqtSignal(str, str)  # (tag_name, target_axis)

    def __init__(self, tag_name: str, display_text: str, parent=None):
        super().__init__(parent)
        self.tag_name = tag_name
        self.display_text = display_text
        self.current_axis = None  # Will be set when tag is plotted

        self._init_ui()

    def _init_ui(self):
        """Initialize the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Checkbox for tag selection
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1f77b4;
                border-color: #1f77b4;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #1f77b4;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        # Label showing tag name or description
        self.label = QLabel(self.display_text)
        self.label.setStyleSheet("QLabel { color: #2C2C2C; }")
        layout.addWidget(self.label, stretch=1)

        # Axis toggle button (hidden by default, shown when checked)
        self.axis_button = QPushButton("Primary")
        self.axis_button.setFixedSize(config.AXIS_BUTTON_WIDTH, config.AXIS_BUTTON_HEIGHT)
        self.axis_button.setStyleSheet(config.AXIS_BUTTON_PRIMARY_STYLE)
        self.axis_button.clicked.connect(self._on_axis_button_clicked)
        self.axis_button.setVisible(False)
        layout.addWidget(self.axis_button)

    def _on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        is_checked = (state == Qt.CheckState.Checked.value)

        # Show/hide axis button based on check state
        if is_checked:
            # Button will be shown after plot is added and axis is determined
            pass
        else:
            self.axis_button.setVisible(False)
            self.current_axis = None

        self.check_state_changed.emit(self.tag_name, is_checked)

    def _on_axis_button_clicked(self):
        """Handle axis button click - toggle between primary and secondary."""
        if self.current_axis == 'left':
            target_axis = 'right'
        elif self.current_axis == 'right':
            target_axis = 'left'
        else:
            # Default to switching to right if axis is unknown
            target_axis = 'right'

        self.axis_change_requested.emit(self.tag_name, target_axis)

    def set_checked(self, checked: bool):
        """Set the checkbox state programmatically."""
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

    def is_checked(self) -> bool:
        """Get the current checkbox state."""
        return self.checkbox.isChecked()

    def update_axis_display(self, axis: str):
        """
        Update the axis button to reflect the current axis.

        Args:
            axis: 'left' for primary axis, 'right' for secondary axis
        """
        self.current_axis = axis

        if axis == 'left':
            self.axis_button.setText("Primary")
            self.axis_button.setStyleSheet(config.AXIS_BUTTON_PRIMARY_STYLE)
        elif axis == 'right':
            self.axis_button.setText("Secondary")
            self.axis_button.setStyleSheet(config.AXIS_BUTTON_SECONDARY_STYLE)

        # Show the button when axis is set (tag is plotted)
        if self.checkbox.isChecked():
            self.axis_button.setVisible(True)

    def update_display_text(self, display_text: str):
        """Update the display text (for toggling between tag name and description)."""
        self.display_text = display_text
        self.label.setText(display_text)

    def set_axis_button_enabled(self, enabled: bool):
        """
        Enable or disable the axis button.
        Used to disable axis changing when in compare mode.

        Args:
            enabled: True to enable button, False to disable
        """
        self.axis_button.setEnabled(enabled)
        if not enabled:
            self.axis_button.setToolTip("Axis assignment locked in Compare Mode")
        else:
            self.axis_button.setToolTip("")
