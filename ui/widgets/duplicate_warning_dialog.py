"""
Duplicate warning dialog for appending data with duplicate timestamps.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config


class DuplicateWarningDialog(QDialog):
    """Dialog to warn user about duplicate timestamps when appending data."""

    def __init__(self, metadata: dict, parent=None):
        """
        Initialize the duplicate warning dialog.

        Args:
            metadata: Dictionary containing:
                - duplicate_count: Number of duplicate timestamps
                - existing_date_range: (min, max) datetime tuple
                - new_date_range: (min, max) datetime tuple
            parent: Parent widget
        """
        super().__init__(parent)
        self.metadata = metadata
        self.setWindowTitle(f"{config.APP_NAME} - Duplicate Timestamps Detected")
        self.setModal(True)
        self.setMinimumWidth(550)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Warning icon and title
        title_layout = QHBoxLayout()

        # Warning symbol
        warning_label = QLabel("\u26A0")  # Warning triangle symbol
        warning_font = QFont()
        warning_font.setPointSize(24)
        warning_label.setFont(warning_font)
        warning_label.setStyleSheet("color: #FF9800;")
        title_layout.addWidget(warning_label)

        # Title text
        title = QLabel("Duplicate Timestamps Detected")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #D0D0D0;")
        layout.addWidget(separator)

        # Main message
        duplicate_count = self.metadata.get('duplicate_count', 0)
        message = QLabel(
            f"The data you are trying to append contains <b>{duplicate_count}</b> "
            f"timestamp(s) that already exist in your current dataset."
        )
        message.setStyleSheet("color: #2C2C2C; font-size: 11pt;")
        message.setWordWrap(True)
        layout.addWidget(message)

        layout.addSpacing(10)

        # Date range information
        existing_min, existing_max = self.metadata.get('existing_date_range', (None, None))
        new_min, new_max = self.metadata.get('new_date_range', (None, None))

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border: 1px solid #D0D0D0;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)

        # Existing data range
        if existing_min and existing_max:
            existing_label = QLabel("<b>Existing data range:</b>")
            existing_label.setStyleSheet("color: #1f77b4; font-size: 10pt;")
            info_layout.addWidget(existing_label)

            existing_range = QLabel(
                f"{existing_min.strftime('%Y-%m-%d %H:%M:%S')} to "
                f"{existing_max.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            existing_range.setStyleSheet("color: #2C2C2C; margin-left: 20px; font-size: 10pt;")
            info_layout.addWidget(existing_range)

        # New data range
        if new_min and new_max:
            new_label = QLabel("<b>New data range:</b>")
            new_label.setStyleSheet("color: #1f77b4; font-size: 10pt;")
            info_layout.addWidget(new_label)

            new_range = QLabel(
                f"{new_min.strftime('%Y-%m-%d %H:%M:%S')} to "
                f"{new_max.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            new_range.setStyleSheet("color: #2C2C2C; margin-left: 20px; font-size: 10pt;")
            info_layout.addWidget(new_range)

        layout.addWidget(info_frame)

        layout.addSpacing(10)

        # Behavior explanation
        behavior_label = QLabel(
            "<b>What will happen if you proceed:</b><br>"
            "• Duplicate timestamps will be replaced with new data values<br>"
            "• All other data points will be preserved<br>"
            "• Data will be sorted chronologically"
        )
        behavior_label.setStyleSheet("color: #555555; font-size: 10pt; padding: 10px;")
        behavior_label.setWordWrap(True)
        layout.addWidget(behavior_label)

        layout.addSpacing(10)

        # Question
        question_label = QLabel("Do you want to proceed with appending this data?")
        question_font = QFont()
        question_font.setPointSize(11)
        question_font.setBold(True)
        question_label.setFont(question_font)
        question_label.setStyleSheet("color: #2C2C2C;")
        layout.addWidget(question_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        button_layout.addSpacing(10)

        # Proceed button
        proceed_button = QPushButton("Proceed")
        proceed_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        proceed_button.clicked.connect(self.accept)
        button_layout.addWidget(proceed_button)

        layout.addLayout(button_layout)

        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        self.setLayout(layout)
