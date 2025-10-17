"""
Help dialog with quick start guide for first-time users.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config


class HelpDialog(QDialog):
    """Simple help dialog with quick start instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{config.APP_NAME} - Quick Start Guide")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("Quick Start Guide")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #D0D0D0;")
        layout.addWidget(separator)

        # Instructions
        instructions = [
            ("1. Excel File Parameters", "These tell the app which rows contain tags, descriptions, units, and data in your Excel file"),
            ("2. Load Data", "Click 'Load New Data' and select your Excel file"),
            ("3. Check Tags", "Select tags from the list to plot them on the graph"),
            ("4. Interact", "Left-click to pan, scroll wheel to zoom"),
            ("5. Save Session", "Save to .h5 format for instant loading later"),
            ("6. Export", "Export your plots as PNG images for reports")
        ]

        for step, description in instructions:
            step_label = QLabel(f"<b>{step}</b>")
            step_label.setStyleSheet("color: #1f77b4; font-size: 11pt;")
            layout.addWidget(step_label)

            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #2C2C2C; margin-left: 20px; font-size: 10pt;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        layout.addSpacing(10)

        # Excel format note
        note_label = QLabel("<b>Excel Format:</b> First column must be timestamps, "
                           "followed by tag columns. Default rows: Tag=1, Description=2, Units=3, Data Start=4")
        note_label.setStyleSheet("color: #666666; font-size: 9pt; padding: 10px; "
                                "background-color: #F5F5F5; border: 1px solid #D0D0D0; border-radius: 3px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        layout.addStretch()

        # Close button
        close_button = QPushButton("Got It!")
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        self.setLayout(layout)
