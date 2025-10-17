"""
Placeholder widget displayed when no data is plotted.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt


class PlaceholderWidget(QWidget):
    """
    A simple widget to display a placeholder message when no data is plotted.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message_label = QLabel(
            "Please load data and select tags to begin."
        )
        font = self.message_label.font()
        font.setPointSize(16)
        self.message_label.setFont(font)
        self.message_label.setStyleSheet("color: #888;")  # Light gray text
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.message_label)
        self.setLayout(layout)
