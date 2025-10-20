"""
Customize Chart dialog for setting chart title and axis labels.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFrame, QHBoxLayout, QFormLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config


class CustomizeChartDialog(QDialog):
    """Dialog for customizing chart title and axis labels."""

    def __init__(self, parent=None, current_title="", current_left_label="", current_right_label="", has_right_axis=False):
        """
        Initialize the customize chart dialog.

        Args:
            parent: Parent widget
            current_title: Current chart title
            current_left_label: Current left Y-axis label
            current_right_label: Current right Y-axis label
            has_right_axis: Whether the right axis currently exists
        """
        super().__init__(parent)
        self.has_right_axis = has_right_axis
        self.setWindowTitle(f"{config.APP_NAME} - Customize Chart")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._init_ui(current_title, current_left_label, current_right_label)

    def _init_ui(self, current_title, current_left_label, current_right_label):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Title
        title = QLabel("Customize Chart Appearance")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #D0D0D0;")
        main_layout.addWidget(separator)

        # Description
        description = QLabel(
            "Customize the chart title and axis labels. Leave fields blank to use default values."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666666; font-size: 10pt;")
        main_layout.addWidget(description)

        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Chart Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter chart title (optional)")
        self.title_input.setText(current_title)
        self.title_input.setStyleSheet(config.CONTROL_PANEL_LINEEDIT_STYLE)
        form_layout.addRow("<b>Chart Title:</b>", self.title_input)

        # Y1 Axis Label input
        self.y1_input = QLineEdit()
        self.y1_input.setPlaceholderText(f"Default: {config.DEFAULT_LEFT_AXIS_LABEL}")
        self.y1_input.setText(current_left_label if current_left_label != config.DEFAULT_LEFT_AXIS_LABEL else "")
        self.y1_input.setStyleSheet(config.CONTROL_PANEL_LINEEDIT_STYLE)
        form_layout.addRow("<b>Y1 Axis Label:</b>", self.y1_input)

        # Y2 Axis Label input (only if right axis exists)
        self.y2_input = QLineEdit()
        self.y2_input.setPlaceholderText(f"Default: {config.DEFAULT_RIGHT_AXIS_LABEL}")
        self.y2_input.setText(current_right_label if current_right_label != config.DEFAULT_RIGHT_AXIS_LABEL else "")
        self.y2_input.setStyleSheet(config.CONTROL_PANEL_LINEEDIT_STYLE)
        self.y2_input.setEnabled(self.has_right_axis)

        y2_label = QLabel("<b>Y2 Axis Label:</b>")
        if not self.has_right_axis:
            y2_label.setStyleSheet("color: #A0A0A0;")
            self.y2_input.setToolTip("Y2 axis is not currently active")

        form_layout.addRow(y2_label, self.y2_input)

        main_layout.addLayout(form_layout)

        # Add note about right axis
        if not self.has_right_axis:
            note = QLabel("Note: Y2 axis will appear when plotting tags with different scales.")
            note.setStyleSheet("color: #666666; font-size: 9pt; font-style: italic;")
            note.setWordWrap(True)
            main_layout.addWidget(note)

        main_layout.addStretch()

        # Separator before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("background-color: #D0D0D0;")
        main_layout.addWidget(separator2)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #2C2C2C;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
        """)
        reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #2C2C2C;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #1f77b4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565a0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        apply_button.clicked.connect(self.accept)
        apply_button.setDefault(True)
        button_layout.addWidget(apply_button)

        main_layout.addLayout(button_layout)

        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        self.setLayout(main_layout)

    def _reset_to_defaults(self):
        """Reset all fields to defaults."""
        self.title_input.clear()
        self.y1_input.clear()
        self.y2_input.clear()

    def get_customizations(self):
        """
        Get the customization values from the dialog.

        Returns:
            Tuple of (title, y1_label, y2_label) where empty strings mean use default
        """
        return (
            self.title_input.text().strip(),
            self.y1_input.text().strip(),
            self.y2_input.text().strip() if self.has_right_axis else ""
        )
