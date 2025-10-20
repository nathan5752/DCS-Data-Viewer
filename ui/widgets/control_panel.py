"""
Control panel widget containing all UI controls for data loading and tag selection.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox,
    QPushButton, QLabel, QGroupBox, QLineEdit, QCheckBox, QRadioButton, QButtonGroup, QHBoxLayout, QGridLayout, QToolButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QSize
from PyQt6.QtGui import QIcon
from ui.widgets.tag_list import TagList
from ui.widgets.help_dialog import HelpDialog
import config


class ControlPanel(QWidget):
    """Control panel with buttons and tag selection list."""

    # Signals for button clicks
    load_new_data_clicked = pyqtSignal()
    save_session_clicked = pyqtSignal()
    load_session_clicked = pyqtSignal()
    append_data_clicked = pyqtSignal()
    export_plot_clicked = pyqtSignal()
    export_data_clicked = pyqtSignal()
    check_data_quality_clicked = pyqtSignal()
    customize_chart_clicked = pyqtSignal()

    # Signal for tag selection changes
    tag_check_changed = pyqtSignal(str, bool)  # (tag_name, is_checked)

    # Signal for axis change requests
    axis_change_requested = pyqtSignal(str, str)  # (tag_name, target_axis)

    # Signal for Y-axis lock state
    y_axis_lock_changed = pyqtSignal(bool)  # (is_locked)

    # Signal for display mode changes
    display_mode_changed = pyqtSignal(str)  # ("tag" or "description")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tag_list = None
        self.params_widget = None  # Store reference for collapsible section
        self.params_visible = True  # Track collapse state
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        # Apply light theme to control panel
        # Only set background, let child widgets define their own colors
        self.setStyleSheet(f"""
            ControlPanel {{
                background-color: {config.CONTROL_PANEL_BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {config.CONTROL_PANEL_TEXT_COLOR};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(config.CONTROL_PANEL_SPACING)

        # Help button at the top
        help_button = QPushButton(" Quick Start Guide")
        style = self.style()
        help_button.setIcon(style.standardIcon(style.StandardPixmap.SP_MessageBoxQuestion))
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #1f77b4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1565a0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        help_button.setMinimumHeight(36)
        help_button.clicked.connect(self._show_help_dialog)
        layout.addWidget(help_button)

        # Excel parsing parameters group with collapse button
        params_group = QGroupBox()
        params_group.setStyleSheet(config.CONTROL_PANEL_GROUPBOX_STYLE)
        params_group_layout = QVBoxLayout()

        # Title bar with collapse button
        title_layout = QHBoxLayout()
        title_label = QLabel("Excel File Parameters")
        title_label.setStyleSheet("font-weight: bold; color: #2C2C2C;")

        self.collapse_button = QToolButton()
        self.collapse_button.setText("▼")
        self.collapse_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                font-size: 10px;
                color: #666666;
            }
            QToolButton:hover {
                color: #1f77b4;
            }
        """)
        self.collapse_button.setFixedSize(20, 20)
        self.collapse_button.clicked.connect(self._toggle_params_visibility)

        title_layout.addWidget(self.collapse_button)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        params_group_layout.addLayout(title_layout)

        # Collapsible parameters widget
        self.params_widget = QWidget()
        params_layout = QFormLayout()
        params_layout.setSpacing(8)

        # Row number inputs with styling
        self.tag_row_spin = QSpinBox()
        self.tag_row_spin.setMinimum(1)
        self.tag_row_spin.setMaximum(1000)
        self.tag_row_spin.setValue(config.DEFAULT_TAG_ROW)
        self.tag_row_spin.setStyleSheet(config.CONTROL_PANEL_SPINBOX_STYLE)
        params_layout.addRow("Tag Row:", self.tag_row_spin)

        # Description row with toggle button (optional)
        description_row_layout = QHBoxLayout()
        description_row_layout.setSpacing(8)
        self.description_row_button = QPushButton("Enabled")
        self.description_row_button.setToolTip("Click to enable/disable description row")
        self.description_row_button.setStyleSheet(config.TOGGLE_BUTTON_ENABLED_STYLE)
        self.description_row_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.description_row_button.setFixedWidth(70)
        self.description_row_enabled = True  # Track state
        self.description_row_spin = QSpinBox()
        self.description_row_spin.setMinimum(1)
        self.description_row_spin.setMaximum(1000)
        self.description_row_spin.setValue(config.DEFAULT_DESCRIPTION_ROW)
        self.description_row_spin.setStyleSheet(config.CONTROL_PANEL_SPINBOX_STYLE)
        self.description_row_button.clicked.connect(self._toggle_description_row)
        description_row_layout.addWidget(self.description_row_button)
        description_row_layout.addWidget(self.description_row_spin)
        params_layout.addRow("Description Row:", description_row_layout)

        # Units row with toggle button (optional)
        units_row_layout = QHBoxLayout()
        units_row_layout.setSpacing(8)
        self.units_row_button = QPushButton("Enabled")
        self.units_row_button.setToolTip("Click to enable/disable units row")
        self.units_row_button.setStyleSheet(config.TOGGLE_BUTTON_ENABLED_STYLE)
        self.units_row_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.units_row_button.setFixedWidth(70)
        self.units_row_enabled = True  # Track state
        self.units_row_spin = QSpinBox()
        self.units_row_spin.setMinimum(1)
        self.units_row_spin.setMaximum(1000)
        self.units_row_spin.setValue(config.DEFAULT_UNITS_ROW)
        self.units_row_spin.setStyleSheet(config.CONTROL_PANEL_SPINBOX_STYLE)
        self.units_row_button.clicked.connect(self._toggle_units_row)
        units_row_layout.addWidget(self.units_row_button)
        units_row_layout.addWidget(self.units_row_spin)
        params_layout.addRow("Units Row:", units_row_layout)

        self.data_start_row_spin = QSpinBox()
        self.data_start_row_spin.setMinimum(1)
        self.data_start_row_spin.setMaximum(1000)
        self.data_start_row_spin.setValue(config.DEFAULT_DATA_START_ROW)
        self.data_start_row_spin.setStyleSheet(config.CONTROL_PANEL_SPINBOX_STYLE)
        params_layout.addRow("Data Start Row:", self.data_start_row_spin)

        self.params_widget.setLayout(params_layout)
        params_group_layout.addWidget(self.params_widget)
        params_group.setLayout(params_group_layout)
        layout.addWidget(params_group)

        # Data loading buttons group with grid layout
        buttons_group = QGroupBox("Data Operations")
        buttons_group.setStyleSheet(config.CONTROL_PANEL_GROUPBOX_STYLE)
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(8)

        # Get Qt standard icons
        style = self.style()

        # Row 0: Load New Data | Save Session
        self.load_new_button = QPushButton(" Load New Data")
        self.load_new_button.setIcon(style.standardIcon(style.StandardPixmap.SP_DirOpenIcon))
        self.load_new_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.load_new_button.setMinimumHeight(32)
        self.load_new_button.clicked.connect(self.load_new_data_clicked.emit)
        buttons_layout.addWidget(self.load_new_button, 0, 0)

        self.save_session_button = QPushButton(" Save Session")
        self.save_session_button.setIcon(style.standardIcon(style.StandardPixmap.SP_DialogSaveButton))
        self.save_session_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.save_session_button.setMinimumHeight(32)
        self.save_session_button.clicked.connect(self.save_session_clicked.emit)
        self.save_session_button.setEnabled(False)  # Disabled until data is loaded
        buttons_layout.addWidget(self.save_session_button, 0, 1)

        # Row 1: Load Session | Append Data
        self.load_session_button = QPushButton(" Load Session")
        self.load_session_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileIcon))
        self.load_session_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.load_session_button.setMinimumHeight(32)
        self.load_session_button.clicked.connect(self.load_session_clicked.emit)
        buttons_layout.addWidget(self.load_session_button, 1, 0)

        self.append_data_button = QPushButton(" Append Data")
        self.append_data_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileDialogDetailedView))
        self.append_data_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.append_data_button.setMinimumHeight(32)
        self.append_data_button.clicked.connect(self.append_data_clicked.emit)
        self.append_data_button.setEnabled(False)  # Disabled until data is loaded
        buttons_layout.addWidget(self.append_data_button, 1, 1)

        # Row 2: Check Data Quality | Customize Chart
        self.check_quality_button = QPushButton(" Check Data Quality")
        self.check_quality_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileDialogInfoView))
        self.check_quality_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.check_quality_button.setMinimumHeight(32)
        self.check_quality_button.setToolTip("Validate Excel file structure and data quality")
        self.check_quality_button.clicked.connect(self.check_data_quality_clicked.emit)
        buttons_layout.addWidget(self.check_quality_button, 2, 0)

        self.customize_chart_button = QPushButton(" Customize Chart")
        self.customize_chart_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileDialogDetailedView))
        self.customize_chart_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.customize_chart_button.setMinimumHeight(32)
        self.customize_chart_button.setToolTip("Customize chart title and axis labels")
        self.customize_chart_button.clicked.connect(self.customize_chart_clicked.emit)
        self.customize_chart_button.setEnabled(False)  # Disabled until data is plotted
        buttons_layout.addWidget(self.customize_chart_button, 2, 1)

        # Row 3: Export Plot as PNG | Export Data to Excel
        self.export_plot_button = QPushButton(" Export Plot as PNG")
        self.export_plot_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileDialogContentsView))
        self.export_plot_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.export_plot_button.setMinimumHeight(32)
        self.export_plot_button.clicked.connect(self.export_plot_clicked.emit)
        self.export_plot_button.setEnabled(False)  # Disabled until data is plotted
        buttons_layout.addWidget(self.export_plot_button, 3, 0)

        self.export_data_button = QPushButton(" Export Data to Excel")
        self.export_data_button.setIcon(style.standardIcon(style.StandardPixmap.SP_FileIcon))
        self.export_data_button.setStyleSheet(config.CONTROL_PANEL_BUTTON_STYLE)
        self.export_data_button.setMinimumHeight(32)
        self.export_data_button.setToolTip("Export plotted tags to Excel with optional aggregation")
        self.export_data_button.clicked.connect(self.export_data_clicked.emit)
        self.export_data_button.setEnabled(False)  # Disabled until data is plotted
        buttons_layout.addWidget(self.export_data_button, 3, 1)

        # Row 4: Y-axis lock checkbox (spans both columns)
        self.lock_y_axis_checkbox = QCheckBox("Lock Y-Axis (Prevent Zoom)")
        self.lock_y_axis_checkbox.setChecked(False)
        self.lock_y_axis_checkbox.setToolTip("Prevent accidental Y-axis zooming while inspecting data")
        self.lock_y_axis_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2C2C2C;
                padding: 4px;
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
            }
        """)
        self.lock_y_axis_checkbox.stateChanged.connect(
            lambda state: self.y_axis_lock_changed.emit(state == Qt.CheckState.Checked.value)
        )
        buttons_layout.addWidget(self.lock_y_axis_checkbox, 4, 0, 1, 2)  # Span 2 columns

        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)

        # Tag selection group
        tags_group = QGroupBox("Select Tags to Plot")
        tags_group.setStyleSheet(config.CONTROL_PANEL_GROUPBOX_STYLE)
        tags_layout = QVBoxLayout()
        tags_layout.setSpacing(8)

        # Add display mode radio buttons
        display_mode_layout = QHBoxLayout()
        self.display_by_tag_radio = QRadioButton("By Tag Name")
        self.display_by_description_radio = QRadioButton("By Description")
        self.display_by_tag_radio.setChecked(True)  # Default to tag name display

        # Style radio buttons
        radio_style = """
            QRadioButton {
                color: #2C2C2C;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #CCCCCC;
                border-radius: 7px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #1f77b4;
                border-color: #1f77b4;
            }
        """
        self.display_by_tag_radio.setStyleSheet(radio_style)
        self.display_by_description_radio.setStyleSheet(radio_style)

        # Group the radio buttons
        self.display_mode_button_group = QButtonGroup()
        self.display_mode_button_group.addButton(self.display_by_tag_radio)
        self.display_mode_button_group.addButton(self.display_by_description_radio)

        display_mode_layout.addWidget(self.display_by_tag_radio)
        display_mode_layout.addWidget(self.display_by_description_radio)
        tags_layout.addLayout(display_mode_layout)

        # Connect radio button signals
        self.display_by_tag_radio.toggled.connect(self._on_display_mode_changed)

        # Add search/filter box
        self.tag_filter_input = QLineEdit()
        self.tag_filter_input.setPlaceholderText("Filter tags...")
        self.tag_filter_input.setClearButtonEnabled(True)
        self.tag_filter_input.setStyleSheet(config.CONTROL_PANEL_LINEEDIT_STYLE)
        tags_layout.addWidget(self.tag_filter_input)

        self.tag_list = TagList()
        self.tag_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                color: #2C2C2C;
            }
            QListWidget::item {
                color: #2C2C2C;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #E8F4F8;
                color: #2C2C2C;
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;
            }
        """)
        self.tag_list.tag_check_changed.connect(self.tag_check_changed.emit)
        self.tag_list.axis_change_requested.connect(self.axis_change_requested.emit)
        tags_layout.addWidget(self.tag_list)

        # Connect filter input to tag list
        self.tag_filter_input.textChanged.connect(self.tag_list.filter_tags)

        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group, stretch=1)  # Give this section more space

        self.setLayout(layout)
        self.setMinimumWidth(config.CONTROL_PANEL_MIN_WIDTH)

    def get_row_numbers(self) -> tuple:
        """
        Get the current row number settings.
        Returns None for optional parameters (description/units) if disabled.

        Returns:
            Tuple of (tag_row, description_row, units_row, data_start_row)
            where description_row and units_row may be None if disabled
        """
        description_row = self.description_row_spin.value() if self.description_row_enabled else None
        units_row = self.units_row_spin.value() if self.units_row_enabled else None

        return (
            self.tag_row_spin.value(),
            description_row,
            units_row,
            self.data_start_row_spin.value()
        )

    def populate_tags(self, tag_names: list, descriptions: dict = None):
        """
        Populate the tag list with available tags and descriptions.

        Args:
            tag_names: List of tag names
            descriptions: Dictionary mapping tag names to descriptions
        """
        self.tag_list.populate_tags(tag_names, descriptions)

    def enable_data_operations(self, enabled: bool):
        """
        Enable or disable data operation buttons.

        Args:
            enabled: True to enable, False to disable
        """
        self.save_session_button.setEnabled(enabled)
        self.append_data_button.setEnabled(enabled)
        self.export_plot_button.setEnabled(enabled)
        self.export_data_button.setEnabled(enabled)
        self.customize_chart_button.setEnabled(enabled)

    def get_checked_tags(self) -> list:
        """
        Get list of currently checked tags.

        Returns:
            List of checked tag names
        """
        return self.tag_list.get_checked_tags()

    def set_checked_tags(self, tag_names: list):
        """
        Set multiple tags as checked.

        Args:
            tag_names: List of tag names to check
        """
        self.tag_list.set_checked_tags(tag_names)

    def update_tag_axis_display(self, tag_name: str, axis: str):
        """
        Update the axis display for a specific tag.

        Args:
            tag_name: Name of the tag
            axis: The axis ('left' or 'right')
        """
        self.tag_list.update_tag_axis_display(tag_name, axis)

    def _on_display_mode_changed(self, checked: bool):
        """
        Handle display mode radio button toggle.

        Args:
            checked: Whether the tag radio button is checked
        """
        if checked:
            # Tag name radio button was selected
            mode = "tag"
        else:
            # Description radio button was selected
            mode = "description"

        # Update the tag list display mode
        self.tag_list.set_display_mode(mode)

        # Emit signal for other components
        self.display_mode_changed.emit(mode)

    def _toggle_params_visibility(self):
        """Toggle the visibility of the Excel parameters section."""
        self.params_visible = not self.params_visible

        if self.params_visible:
            self.params_widget.show()
            self.collapse_button.setText("▼")
        else:
            self.params_widget.hide()
            self.collapse_button.setText("▶")

    def collapse_params(self):
        """
        Programmatically collapse the Excel File Parameters section with animation.
        Only collapses if currently visible.
        """
        if self.params_visible:
            # Create smooth collapse animation
            self.params_visible = False
            self.collapse_button.setText("▶")

            # Animate the collapse
            animation = QPropertyAnimation(self.params_widget, b"maximumHeight")
            animation.setDuration(300)  # 300ms animation
            animation.setStartValue(self.params_widget.height())
            animation.setEndValue(0)
            animation.finished.connect(self.params_widget.hide)
            animation.start()

            # Store animation to prevent garbage collection
            self._collapse_animation = animation

    def expand_params(self):
        """
        Programmatically expand the Excel File Parameters section.
        Only expands if currently collapsed.
        """
        if not self.params_visible:
            self.params_visible = True
            self.collapse_button.setText("▼")
            self.params_widget.setMaximumHeight(16777215)  # Reset to default max height
            self.params_widget.show()

    def set_params_enabled(self, enabled: bool):
        """
        Enable or disable the Excel File Parameters section.
        When disabled, all controls are grayed out and non-interactive.

        Args:
            enabled: True to enable, False to disable
        """
        # Enable/disable all spinboxes
        self.tag_row_spin.setEnabled(enabled)
        self.description_row_spin.setEnabled(enabled and self.description_row_enabled)
        self.units_row_spin.setEnabled(enabled and self.units_row_enabled)
        self.data_start_row_spin.setEnabled(enabled)

        # Enable/disable toggle buttons
        self.description_row_button.setEnabled(enabled)
        self.units_row_button.setEnabled(enabled)

        # Keep collapse button enabled so users can expand/collapse to view parameters
        # (they just can't edit them when disabled)

        # Update tooltip to explain why it's disabled
        if not enabled:
            self.params_widget.setToolTip(
                "Excel parameters are locked after loading data.\n"
                "Click 'Load New Data' and confirm reset to change parameters."
            )
        else:
            self.params_widget.setToolTip("")

    def reset_ui(self):
        """
        Reset the UI to its initial state.
        Clears tag list and disables data operation buttons.
        """
        # Clear tag list
        self.tag_list.clear()

        # Disable data operation buttons
        self.enable_data_operations(False)

        # Expand and re-enable Excel File Parameters section
        self.expand_params()
        self.set_params_enabled(True)

    def set_toggle_visible(self, visible: bool):
        """
        Set the visibility of the Tags/Description toggle radio buttons.

        Args:
            visible: True to show the toggle, False to hide it
        """
        self.display_by_tag_radio.setVisible(visible)
        self.display_by_description_radio.setVisible(visible)

        # If hiding and currently in description mode, switch to tag mode
        if not visible and self.display_by_description_radio.isChecked():
            self.display_by_tag_radio.setChecked(True)

    def _show_help_dialog(self):
        """Show the help dialog with quick start guide."""
        dialog = HelpDialog(self)
        dialog.exec()

    def _toggle_description_row(self):
        """Toggle the description row enabled/disabled state."""
        self.description_row_enabled = not self.description_row_enabled

        if self.description_row_enabled:
            self.description_row_button.setText("Enabled")
            self.description_row_button.setStyleSheet(config.TOGGLE_BUTTON_ENABLED_STYLE)
            self.description_row_spin.setEnabled(True)
        else:
            self.description_row_button.setText("Disabled")
            self.description_row_button.setStyleSheet(config.TOGGLE_BUTTON_DISABLED_STYLE)
            self.description_row_spin.setEnabled(False)

    def _toggle_units_row(self):
        """Toggle the units row enabled/disabled state."""
        self.units_row_enabled = not self.units_row_enabled

        if self.units_row_enabled:
            self.units_row_button.setText("Enabled")
            self.units_row_button.setStyleSheet(config.TOGGLE_BUTTON_ENABLED_STYLE)
            self.units_row_spin.setEnabled(True)
        else:
            self.units_row_button.setText("Disabled")
            self.units_row_button.setStyleSheet(config.TOGGLE_BUTTON_DISABLED_STYLE)
            self.units_row_spin.setEnabled(False)
