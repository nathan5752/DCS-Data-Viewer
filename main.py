"""
DCS Data Viewer - Main application entry point.

A desktop application for visualizing time-series data from industrial systems.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create the application
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
