"""
Help dialog with quick start guide for first-time users.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config


class HelpDialog(QDialog):
    """Comprehensive help dialog with quick start instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{config.APP_NAME} - Quick Start Guide")
        self.setModal(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        # Main layout for dialog
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Title
        title = QLabel("Quick Start Guide")
        title_font = QFont()
        title_font.setPointSize(14)
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

        # Create scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)

        # Add all sections to content
        self._add_section_1(content_layout)
        self._add_section_2(content_layout)
        self._add_section_3(content_layout)
        self._add_section_4(content_layout)
        self._add_section_5(content_layout)
        self._add_section_6(content_layout)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        main_layout.addWidget(scroll_area)

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
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QScrollArea {
                background-color: white;
                border: none;
            }
        """)

        self.setLayout(main_layout)

    def _create_section_header(self, text):
        """Create a styled section header label."""
        label = QLabel(f"<b>{text}</b>")
        label.setStyleSheet("color: #1f77b4; font-size: 12pt; margin-top: 5px;")
        return label

    def _create_content_label(self, html_text):
        """Create a styled content label with HTML support."""
        label = QLabel(html_text)
        label.setStyleSheet("color: #2C2C2C; margin-left: 20px; font-size: 10pt;")
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        return label

    def _add_section_1(self, layout):
        """Section 1: Getting Started (First Load)"""
        layout.addWidget(self._create_section_header("1. Getting Started (First Load)"))

        content = """
        <p><b>Excel File Parameters</b> tell the app which rows contain your data structure:</p>
        <p style="margin-left: 15px;">
        • <b>Tag Row:</b> Row number containing tag names (default: 1)<br>
        • <b>Description Row:</b> Row with tag descriptions (default: 2, toggle off if not in your file)<br>
        • <b>Units Row:</b> Row with measurement units (default: 3, toggle off if not in your file)<br>
        • <b>Data Start Row:</b> First row of actual timestamp/value data (default: 4)
        </p>

        <p><b>Excel Format Requirements:</b></p>
        <p style="margin-left: 15px;">
        • First column MUST be timestamps (datetime format)<br>
        • Subsequent columns contain tag values<br>
        • Blank columns are automatically detected and skipped
        </p>

        <p>Click <b>Load New Data</b> to select your Excel file and start plotting.</p>
        """
        layout.addWidget(self._create_content_label(content))

    def _add_section_2(self, layout):
        """Section 2: Working with Data"""
        layout.addWidget(self._create_section_header("2. Working with Data"))

        content = """
        <p><b>Plotting Tags:</b></p>
        <p style="margin-left: 15px;">
        • Check any tag in the list to plot it on the graph<br>
        • Uncheck to remove it from the plot<br>
        • Each tag gets a unique color automatically
        </p>

        <p><b>Filter Tags:</b> Use the search box to quickly find tags by name or description.</p>

        <p><b>Display Mode Toggle:</b> Switch between "By Tag Name" and "By Description" views using the radio buttons.</p>

        <p><b>Multi-Axis Support:</b> When tags have different scales (e.g., temperature vs. pressure),
        the app automatically creates a <b>secondary Y-axis</b> on the right side. This prevents small-scale
        values from being lost when plotted with large-scale values.</p>

        <p><b>Y-Axis Lock:</b> Check this box to prevent accidental zooming on the Y-axis while inspecting data.
        You can still zoom on the time (X) axis.</p>
        """
        layout.addWidget(self._create_content_label(content))

    def _add_section_3(self, layout):
        """Section 3: Interacting with Plots"""
        layout.addWidget(self._create_section_header("3. Interacting with Plots"))

        content = """
        <p><b>Pan:</b> Left-click and drag to move around the plot.</p>

        <p><b>Zoom:</b> Use mouse wheel to zoom in/out. Right-click menu offers "View All" to reset zoom.</p>

        <p><b>Crosshair:</b> Move your mouse over the plot to see a crosshair that helps you read exact values.</p>

        <p><b>Tooltip:</b> When you hover over data points, a tooltip displays all tag values at that timestamp.</p>
        """
        layout.addWidget(self._create_content_label(content))

    def _add_section_4(self, layout):
        """Section 4: Saving & Loading"""
        layout.addWidget(self._create_section_header("4. Saving & Loading"))

        content = """
        <p><b>Save Session:</b> Export your current data to <b>.h5 format</b> (HDF5). This is 10-100x faster
        than loading Excel files and preserves all your data perfectly. Ideal for large datasets!</p>

        <p><b>Load Session:</b> Instantly reload a previously saved .h5 session file. No need to wait for
        Excel parsing or specify row parameters again.</p>

        <p><b>Append Data:</b> Add more data to your current session.</p>
        <p style="margin-left: 15px;">
        • Load additional Excel files to extend your time series<br>
        • <b>Duplicate timestamps</b> are automatically detected<br>
        • You'll be prompted to choose: keep original, keep new, or cancel<br>
        • Overlapping data is seamlessly merged
        </p>
        """
        layout.addWidget(self._create_content_label(content))

    def _add_section_5(self, layout):
        """Section 5: Data Quality & Export"""
        layout.addWidget(self._create_section_header("5. Data Quality & Export"))

        content = """
        <p><b>Check Data Quality:</b> Validate your Excel files before loading. This tool:</p>
        <p style="margin-left: 15px;">
        • Detects blank columns and invalid timestamps<br>
        • Reports data quality issues with details<br>
        • Offers to create a <b>cleaned version</b> of your file<br>
        • Helps troubleshoot loading problems
        </p>

        <p><b>Export Plot as PNG:</b> Save publication-quality images of your current plot view.</p>

        <p><b>Export Data to Excel:</b> Export your plotted tags back to Excel with powerful options:</p>
        <p style="margin-left: 15px;">
        • <b>Time Range:</b> Choose "Visible range" (current zoom) or "All data"<br>
        • <b>Aggregation:</b> Downsample data to 5s, 10s, 30s, 1min, 5min, 15min, 30min, or 1hr intervals<br>
        • <b>Statistics:</b> For each interval, get mean, min, and max values<br>
        • Perfect for creating summary reports!
        </p>
        """
        layout.addWidget(self._create_content_label(content))

    def _add_section_6(self, layout):
        """Section 6: Troubleshooting"""
        layout.addWidget(self._create_section_header("6. Troubleshooting"))

        content = """
        <p><b>Blank Columns:</b> Automatically detected and skipped during loading. You'll see a warning
        but data will still load correctly.</p>

        <p><b>Invalid Timestamps:</b> Rows with unparseable dates are removed. Check the status bar for
        how many rows were affected.</p>

        <p><b>File Format Issues:</b> Use <b>Check Data Quality</b> first if you encounter loading problems.
        It will help identify and fix issues.</p>

        <p><b>Working with CSV Files?</b> Use the <b>scripts/csv_to_excel.py</b> converter to prepare your data:</p>
        <p style="margin-left: 15px; font-family: monospace; background-color: #F5F5F5; padding: 5px; border-radius: 3px;">
        python scripts/csv_to_excel.py input.csv output.xlsx
        </p>
        <p style="margin-left: 15px;">
        This converts CSV files into the Excel format required by DCS Data Viewer.
        </p>
        """
        layout.addWidget(self._create_content_label(content))
