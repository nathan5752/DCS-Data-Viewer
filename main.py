"""
DCS Data Viewer - Main application entry point.

A desktop application for visualizing time-series data from industrial systems.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow


def exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for uncaught exceptions.
    Shows user-friendly dialog and logs to file.
    """
    # Format the exception
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write to log file
    log_dir = Path.home() / ".dcs_data_viewer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "error.log"

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"{'='*80}\n")
        f.write(error_msg)

    # Show user-friendly dialog
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Unexpected Error")
    msg.setText("An unexpected error occurred. The application may need to restart.")
    msg.setInformativeText(f"Error: {exc_value}\n\nError log saved to:\n{log_file}")
    msg.setDetailedText(error_msg)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


def main():
    """Main application entry point."""
    # Install global exception handler
    sys.excepthook = exception_handler

    # Create the application
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
