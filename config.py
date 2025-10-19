"""
Configuration and constants for the DCS Data Viewer application.
"""

# Application metadata
APP_NAME = "DCS Data Viewer"
APP_VERSION = "1.1.0"

# Default row numbers for Excel parsing
DEFAULT_TAG_ROW = 1
DEFAULT_DESCRIPTION_ROW = 2
DEFAULT_UNITS_ROW = 3
DEFAULT_DATA_START_ROW = 4

# File filters for dialogs
EXCEL_FILE_FILTER = "Excel Files (*.xlsx *.xls)"
SESSION_FILE_FILTER = "Session Files (*.h5)"

# HDF5 storage key
HDF5_KEY = 'data'

# Plot colors (cycle through these for different tags)
PLOT_COLORS = [
    (31, 119, 180),   # Blue
    (255, 127, 14),   # Orange
    (44, 160, 44),    # Green
    (214, 39, 40),    # Red
    (148, 103, 189),  # Purple
    (140, 86, 75),    # Brown
    (227, 119, 194),  # Pink
    (127, 127, 127),  # Gray
    (188, 189, 34),   # Yellow-green
    (23, 190, 207),   # Cyan
]

# Multi-axis detection threshold
# If the order of magnitude difference between datasets exceeds this, create new axis
AXIS_MAGNITUDE_THRESHOLD = 1.5

# Plot settings
PLOT_LINE_WIDTH = 2
DOWNSAMPLE_MODE = 'peak'  # Keep peaks visible when downsampling
PLOT_BACKGROUND_COLOR = 'w'  # White background for better contrast

# UI Layout
CONTROL_PANEL_MIN_WIDTH = 250
SPLITTER_SIZES = [30, 70]  # 30% control panel, 70% plot area (in percentages)

# Status bar message timeout (milliseconds)
STATUS_MESSAGE_TIMEOUT = 3000  # 3 seconds

# PNG Export settings (for publication-quality output)
EXPORT_WIDTH_PIXELS = 2400  # ~8 inches at 300 DPI for technical reports
EXPORT_BACKGROUND_COLOR = 'w'  # White background for technical documentation
EXPORT_FOREGROUND_COLOR = 'k'  # Black text/axes for print clarity
EXPORT_FILE_FILTER = "PNG Images (*.png)"

# Excel Export settings
EXPORT_EXCEL_FILTER = "Excel Files (*.xlsx)"

# Aggregation presets (for Phase 2)
AGGREGATION_PRESETS = {
    '5 seconds': '5s',
    '10 seconds': '10s',
    '30 seconds': '30s',
    '1 minute': '1min',
    '5 minutes': '5min',
    '15 minutes': '15min',
    '1 hour': '1h',
    'Custom...': 'custom'
}

DEFAULT_AGGREGATION_STATS = ['mean', 'min', 'max']

# Axis toggle button settings
AXIS_BUTTON_WIDTH = 70
AXIS_BUTTON_HEIGHT = 20
AXIS_BUTTON_PRIMARY_STYLE = """
    QPushButton {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 3px;
        font-size: 9px;
        font-weight: bold;
        padding: 2px;
    }
    QPushButton:hover {
        background-color: #1565a0;
    }
"""
AXIS_BUTTON_SECONDARY_STYLE = """
    QPushButton {
        background-color: #ff7f0e;
        color: white;
        border: none;
        border-radius: 3px;
        font-size: 9px;
        font-weight: bold;
        padding: 2px;
    }
    QPushButton:hover {
        background-color: #e67000;
    }
"""

# Control Panel Theme - Light Mode
CONTROL_PANEL_BACKGROUND_COLOR = "#F5F5F5"
CONTROL_PANEL_TEXT_COLOR = "#2C2C2C"
CONTROL_PANEL_GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 1px solid #D0D0D0;
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 10px;
        background-color: white;
        color: #2C2C2C;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        top: 0px;
        padding: 0 5px 0 5px;
        color: #2C2C2C;
        background-color: white;
    }
"""
CONTROL_PANEL_BUTTON_STYLE = """
    QPushButton {
        background-color: #FFFFFF;
        color: #2C2C2C;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 11px;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #E8F4F8;
        border-color: #1f77b4;
    }
    QPushButton:pressed {
        background-color: #D0E8F0;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        color: #A0A0A0;
        border-color: #E0E0E0;
    }
"""
CONTROL_PANEL_SPINBOX_STYLE = """
    QSpinBox {
        background-color: white;
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 3px;
        color: #2C2C2C;
    }
    QSpinBox:focus {
        border-color: #1f77b4;
    }
"""
CONTROL_PANEL_LINEEDIT_STYLE = """
    QLineEdit {
        background-color: white;
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 4px;
        color: #2C2C2C;
    }
    QLineEdit:focus {
        border-color: #1f77b4;
    }
"""

# Toggle button styles for enabled/disabled states
TOGGLE_BUTTON_ENABLED_STYLE = """
    QPushButton {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 10px;
        font-weight: bold;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: #1565a0;
    }
    QPushButton:pressed {
        background-color: #0d47a1;
    }
"""

TOGGLE_BUTTON_DISABLED_STYLE = """
    QPushButton {
        background-color: #E0E0E0;
        color: #666666;
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 10px;
        font-weight: bold;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: #D0D0D0;
        border-color: #AAAAAA;
    }
    QPushButton:pressed {
        background-color: #C0C0C0;
    }
"""

CONTROL_PANEL_SPACING = 15  # Increased spacing between sections

# Data Validation Settings
VALIDATION_MAX_MISSING_PERCENT = 90  # Warn if column has >90% missing values
VALIDATION_SAMPLE_ROWS = 1000  # Number of rows to sample for quick validation
CLEANED_FILE_SUFFIX = "_cleaned"  # Suffix for cleaned Excel files

# Validation severity colors for UI
SEVERITY_ERROR_COLOR = "#d32f2f"    # Red for errors
SEVERITY_WARNING_COLOR = "#f57c00"  # Orange for warnings
SEVERITY_INFO_COLOR = "#1976d2"     # Blue for information
