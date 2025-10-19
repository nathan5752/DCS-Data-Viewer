"""
Utility functions for the DCS Data Viewer application.
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from typing import Optional
import config


def open_excel_file_dialog(parent=None) -> Optional[str]:
    """
    Opens a file dialog to select an Excel file.

    Args:
        parent: Parent widget for the dialog

    Returns:
        Selected file path or None if cancelled
    """
    filepath, _ = QFileDialog.getOpenFileName(
        parent,
        "Open Excel File",
        "",
        config.EXCEL_FILE_FILTER
    )
    return filepath if filepath else None


def save_session_file_dialog(parent=None) -> Optional[str]:
    """
    Opens a file dialog to save a session file.

    Args:
        parent: Parent widget for the dialog

    Returns:
        Selected file path or None if cancelled
    """
    filepath, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Session File",
        "",
        config.SESSION_FILE_FILTER
    )
    return filepath if filepath else None


def open_session_file_dialog(parent=None) -> Optional[str]:
    """
    Opens a file dialog to load a session file.

    Args:
        parent: Parent widget for the dialog

    Returns:
        Selected file path or None if cancelled
    """
    filepath, _ = QFileDialog.getOpenFileName(
        parent,
        "Open Session File",
        "",
        config.SESSION_FILE_FILTER
    )
    return filepath if filepath else None


def save_png_file_dialog(parent=None) -> Optional[str]:
    """
    Opens a file dialog to save a PNG image file.

    Args:
        parent: Parent widget for the dialog

    Returns:
        Selected file path or None if cancelled
    """
    filepath, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Plot as PNG",
        "plot_export.png",
        config.EXPORT_FILE_FILTER
    )
    return filepath if filepath else None


def save_excel_file_dialog(parent=None) -> Optional[str]:
    """
    Opens a file dialog to save an Excel file.

    Args:
        parent: Parent widget for the dialog

    Returns:
        Selected file path or None if cancelled
    """
    filepath, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Data to Excel",
        "",
        config.EXPORT_EXCEL_FILTER
    )
    return filepath if filepath else None


def show_error_message(parent, title: str, message: str):
    """
    Displays an error message dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Error message to display
    """
    QMessageBox.critical(parent, title, message)


def show_info_message(parent, title: str, message: str):
    """
    Displays an information message dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Information message to display
    """
    QMessageBox.information(parent, title, message)


def show_blank_column_warning(parent, blank_count: int) -> bool:
    """
    Shows a warning dialog about blank columns detected in Excel file.

    Args:
        parent: Parent widget for the dialog
        blank_count: Number of blank columns detected

    Returns:
        True if user chooses to proceed, False if cancelled
    """
    message = (
        f"Detected {blank_count} blank column(s) at the left of the Excel file.\n\n"
        "These columns will be ignored during import.\n\n"
        "Do you want to proceed?"
    )

    reply = QMessageBox.question(
        parent,
        "Blank Columns Detected",
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Yes
    )

    return reply == QMessageBox.StandardButton.Yes


def validate_row_numbers(
    tag_row: int,
    description_row: Optional[int],
    units_row: Optional[int],
    data_start_row: int
) -> tuple[bool, str]:
    """
    Validates that row numbers are positive and in correct order.
    Description and units rows are optional and can be None.

    Args:
        tag_row: Row number for tag names (required)
        description_row: Row number for descriptions (optional, can be None)
        units_row: Row number for units (optional, can be None)
        data_start_row: Row number where data starts (required)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate required parameters
    if tag_row < 1:
        return False, "Tag row number must be positive (1 or greater)."

    if data_start_row < 1:
        return False, "Data start row number must be positive (1 or greater)."

    if data_start_row <= tag_row:
        return False, "Data start row must be after tag row."

    # Validate optional parameters if provided
    if description_row is not None:
        if description_row < 1:
            return False, "Description row number must be positive (1 or greater)."
        if description_row <= tag_row:
            return False, "Description row must be after tag row."
        if description_row >= data_start_row:
            return False, "Description row must be before data start row."

    if units_row is not None:
        if units_row < 1:
            return False, "Units row number must be positive (1 or greater)."
        if units_row <= tag_row:
            return False, "Units row must be after tag row."
        if units_row >= data_start_row:
            return False, "Units row must be before data start row."

    # Check for duplicate row numbers among provided rows
    header_rows = [tag_row]
    if description_row is not None:
        header_rows.append(description_row)
    if units_row is not None:
        header_rows.append(units_row)

    if len(header_rows) != len(set(header_rows)):
        return False, "Tag row, description row, and units row must all be different."

    return True, ""
