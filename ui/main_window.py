"""
Main window for the DCS Data Viewer application.
"""

from PyQt6.QtWidgets import QMainWindow, QSplitter, QStatusBar, QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon
import pyqtgraph as pg

from ui.widgets.control_panel import ControlPanel
from ui.widgets.placeholder_widget import PlaceholderWidget
from ui.widgets.data_quality_dialog import DataQualityDialog
from ui.widgets.duplicate_warning_dialog import DuplicateWarningDialog
from data.data_manager import DataManager
from data.data_validator import DataValidator
from plotting.plot_manager import PlotManager
from utils.helpers import (
    open_excel_file_dialog, save_session_file_dialog,
    open_session_file_dialog, save_png_file_dialog,
    show_error_message, validate_row_numbers, show_blank_column_warning, show_info_message
)
from utils.data_cleaner import DataCleaner
import config
import os
import sys


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    Args:
        relative_path: Path relative to the project root

    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running as script - use normal path (go up from ui/ to project root)
        base_path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.plot_manager = None
        self.control_panel = None
        self.main_plot_widget = None  # Store reference to main plot widget
        self.additional_plots = []  # Store additional stacked plot widgets
        self.main_layout = None  # Store main vertical layout
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 800)

        # Set window icon if available
        icon_path = get_resource_path(os.path.join('assets', 'app_icon.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Create main central widget with vertical layout
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(0)  # No spacing between plots
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # No margins

        # Create horizontal splitter for control panel and plot area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create control panel (left side)
        self.control_panel = ControlPanel()
        self.control_panel.load_new_data_clicked.connect(self._on_load_new_data)
        self.control_panel.save_session_clicked.connect(self._on_save_session)
        self.control_panel.load_session_clicked.connect(self._on_load_session)
        self.control_panel.append_data_clicked.connect(self._on_append_data)
        self.control_panel.export_plot_clicked.connect(self._on_export_plot)
        self.control_panel.export_data_clicked.connect(self._on_export_data)
        self.control_panel.check_data_quality_clicked.connect(self._on_check_data_quality)
        self.control_panel.customize_chart_clicked.connect(self._on_customize_chart)
        self.control_panel.tag_check_changed.connect(self._on_tag_check_changed)
        self.control_panel.axis_change_requested.connect(self._on_axis_change_requested)
        splitter.addWidget(self.control_panel)

        # Create main plot widget (right side) with white background
        self.main_plot_widget = pg.PlotWidget(background=config.PLOT_BACKGROUND_COLOR)

        # Create the placeholder and the stacked widget
        self.placeholder = PlaceholderWidget()
        self.plot_stack = QStackedWidget()
        self.plot_stack.addWidget(self.placeholder)  # Index 0
        self.plot_stack.addWidget(self.main_plot_widget)  # Index 1

        # Set the initial view to the placeholder
        self.plot_stack.setCurrentIndex(0)

        splitter.addWidget(self.plot_stack)

        # Set splitter sizes (30% control panel, 70% plot)
        splitter.setSizes([300, 700])

        # Add splitter to main layout
        self.main_layout.addWidget(splitter)

        # Create PlotManager with main plot widget
        self.plot_manager = PlotManager(self.main_plot_widget, self.data_manager)

        # Connect signal for creating additional stacked plots (DISABLED - stacked plots not implemented)
        # self.plot_manager.new_plot_requested.connect(self._create_new_plot_widget)

        # Connect signal for max axes reached notification
        self.plot_manager.max_axes_reached.connect(self._on_max_axes_reached)

        # Connect Y-axis lock signal from control panel to plot manager
        self.control_panel.y_axis_lock_changed.connect(self.plot_manager.set_y_axis_lock)

        # Connect plot visibility signals
        self.plot_manager.first_plot_added.connect(self.show_plot_widget)
        self.plot_manager.all_plots_removed.connect(self.show_placeholder_widget)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _on_load_new_data(self):
        """Handle Load New Data button click."""
        # Check if data already exists - if so, ask user to confirm reset
        if self.data_manager.has_data():
            reply = QMessageBox.question(
                self,
                "Reset Session?",
                "This will clear the current session and all plotted data.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            # Reset the session
            self.data_manager.reset_session()
            self.plot_manager.reset()
            self.control_panel.reset_ui()
            self.status_bar.showMessage("Session reset. Ready to load new data.")

            # Parameters are re-enabled by reset_ui()
            # Return early - let user modify Excel parameters and click Load again
            return

        # Get file path from dialog
        filepath = open_excel_file_dialog(self)
        if not filepath:
            return

        # Get row numbers
        tag_row, description_row, units_row, data_start_row = self.control_panel.get_row_numbers()

        # Validate row numbers
        is_valid, error_msg = validate_row_numbers(tag_row, description_row, units_row, data_start_row)
        if not is_valid:
            show_error_message(self, "Invalid Row Numbers", error_msg)
            return

        # Detect blank columns
        self.status_bar.showMessage("Checking for blank columns...")
        success, message, blank_count = self.data_manager.detect_blank_columns(filepath, tag_row)
        if not success:
            show_error_message(self, "Error Detecting Columns", message)
            self.status_bar.showMessage("Failed to detect columns")
            return

        # If blank columns found, ask user to proceed
        if blank_count > 0:
            if not show_blank_column_warning(self, blank_count):
                self.status_bar.showMessage("Load cancelled by user")
                return

        # Run automatic quick validation
        self.status_bar.showMessage("Validating data quality...")
        validator = DataValidator(filepath, tag_row, description_row, units_row, data_start_row)
        report = validator.run_quick_validation()

        if report.has_issues():
            # Show validation results and let user decide
            action = self._show_validation_dialog(report, filepath, tag_row, description_row, units_row, data_start_row)

            if action == DataQualityDialog.ACTION_CANCEL:
                self.status_bar.showMessage("Load cancelled by user")
                return
            elif action == DataQualityDialog.ACTION_CLEAN:
                # User chose to export cleaned file
                # The dialog handler already exported the cleaned file
                self.status_bar.showMessage("Please load the cleaned file when ready")
                return
            # If ACTION_CONTINUE, proceed with loading

        # Load data
        self.status_bar.showMessage("Loading data...")
        success, message, df = self.data_manager.load_excel(
            filepath, tag_row, description_row, units_row, data_start_row, blank_count
        )

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
            self._update_tag_list()
            self.control_panel.enable_data_operations(True)
            # Auto-collapse and disable Excel File Parameters after load
            self.control_panel.collapse_params()
            self.control_panel.set_params_enabled(False)
        else:
            show_error_message(self, "Error Loading Data", message)
            self.status_bar.showMessage("Failed to load data")

    def _on_save_session(self):
        """Handle Save Session button click."""
        # Get file path from dialog
        filepath = save_session_file_dialog(self)
        if not filepath:
            return

        # Ensure .h5 extension
        if not filepath.endswith('.h5'):
            filepath += '.h5'

        # Save session
        self.status_bar.showMessage("Saving session...")
        success, message = self.data_manager.save_session(filepath)

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
        else:
            show_error_message(self, "Error Saving Session", message)
            self.status_bar.showMessage("Failed to save session")

    def _on_load_session(self):
        """Handle Load Session button click."""
        # Get file path from dialog
        filepath = open_session_file_dialog(self)
        if not filepath:
            return

        # Load session
        self.status_bar.showMessage("Loading session...")
        success, message, df = self.data_manager.load_session(filepath)

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
            self._update_tag_list()
            self.control_panel.enable_data_operations(True)
            # Auto-collapse and disable Excel File Parameters after loading session
            self.control_panel.collapse_params()
            self.control_panel.set_params_enabled(False)
        else:
            show_error_message(self, "Error Loading Session", message)
            self.status_bar.showMessage("Failed to load session")

    def _on_append_data(self):
        """Handle Append Data button click."""
        # Get file path from dialog
        filepath = open_excel_file_dialog(self)
        if not filepath:
            return

        # Get row numbers
        tag_row, description_row, units_row, data_start_row = self.control_panel.get_row_numbers()

        # Validate row numbers
        is_valid, error_msg = validate_row_numbers(tag_row, description_row, units_row, data_start_row)
        if not is_valid:
            show_error_message(self, "Invalid Row Numbers", error_msg)
            return

        # Detect blank columns
        self.status_bar.showMessage("Checking for blank columns...")
        success, message, blank_count = self.data_manager.detect_blank_columns(filepath, tag_row)
        if not success:
            show_error_message(self, "Error Detecting Columns", message)
            self.status_bar.showMessage("Failed to detect columns")
            return

        # If blank columns found, ask user to proceed
        if blank_count > 0:
            if not show_blank_column_warning(self, blank_count):
                self.status_bar.showMessage("Append cancelled by user")
                return

        # Run automatic quick validation
        self.status_bar.showMessage("Validating data quality...")
        validator = DataValidator(filepath, tag_row, description_row, units_row, data_start_row)
        report = validator.run_quick_validation()

        if report.has_issues():
            # Show validation results and let user decide
            action = self._show_validation_dialog(report, filepath, tag_row, description_row, units_row, data_start_row)

            if action == DataQualityDialog.ACTION_CANCEL:
                self.status_bar.showMessage("Append cancelled by user")
                return
            elif action == DataQualityDialog.ACTION_CLEAN:
                # User chose to export cleaned file
                self.status_bar.showMessage("Please append the cleaned file when ready")
                return
            # If ACTION_CONTINUE, proceed with appending

        # Append data
        self.status_bar.showMessage("Appending data...")
        success, message, df = self.data_manager.append_data(
            filepath, tag_row, description_row, units_row, data_start_row, blank_count
        )

        # Check if duplicates were detected
        if not success and message == "DUPLICATES_DETECTED":
            # Show duplicate warning dialog
            dialog = DuplicateWarningDialog(df, self)  # df contains metadata in this case
            result = dialog.exec()

            if result == 1:  # QDialog.Accepted (from accept() in dialog)
                # User confirmed - proceed with append
                self.status_bar.showMessage("Appending data (confirmed)...")
                success, message, df = self.data_manager.append_data_confirmed(
                    filepath, tag_row, description_row, units_row, data_start_row, blank_count
                )

                if success:
                    self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
                    self._update_tag_list()
                    # Refresh any currently plotted tags
                    self._refresh_plots()
                else:
                    show_error_message(self, "Error Appending Data", message)
                    self.status_bar.showMessage("Failed to append data")
            else:
                # User cancelled
                self.status_bar.showMessage("Append cancelled by user")
        elif success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
            self._update_tag_list()
            # Refresh any currently plotted tags
            self._refresh_plots()
        else:
            show_error_message(self, "Error Appending Data", message)
            self.status_bar.showMessage("Failed to append data")

    def _on_export_plot(self):
        """Handle Export Plot as PNG button click."""
        # Get file path from dialog
        filepath = save_png_file_dialog(self)
        if not filepath:
            return

        # Ensure .png extension
        if not filepath.lower().endswith('.png'):
            filepath += '.png'

        # Export plot
        self.status_bar.showMessage("Exporting plot...")
        success, message = self.plot_manager.export_to_png(filepath)

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
        else:
            show_error_message(self, "Error Exporting Plot", message)
            self.status_bar.showMessage("Failed to export plot")

    def _on_customize_chart(self):
        """Handle Customize Chart button click."""
        from ui.widgets.customize_chart_dialog import CustomizeChartDialog

        # Get current customizations from plot manager
        current_title, current_left, current_right = self.plot_manager.get_chart_customizations()

        # Check if right axis exists
        has_right_axis = self.plot_manager.has_right_axis()

        # Show customization dialog
        dialog = CustomizeChartDialog(
            self,
            current_title=current_title,
            current_left_label=current_left,
            current_right_label=current_right,
            has_right_axis=has_right_axis
        )

        if dialog.exec() == CustomizeChartDialog.DialogCode.Accepted:
            # Apply customizations
            title, left_label, right_label = dialog.get_customizations()
            self.plot_manager.set_chart_customizations(title, left_label, right_label)
            self.status_bar.showMessage("Chart customizations applied", config.STATUS_MESSAGE_TIMEOUT)

    def _on_export_data(self):
        """Handle Export Data to Excel button click."""
        from ui.widgets.export_dialog import ExportDialog
        from utils.helpers import save_excel_file_dialog
        from data.export_manager import export_to_excel

        # Check if any tags are plotted
        plotted_tags = self.plot_manager.get_plotted_tags()
        if not plotted_tags:
            show_error_message(self, "No Data to Export",
                              "No tags are currently plotted. Please plot tags before exporting.")
            return

        # Get visible time range
        start_time, end_time = self.plot_manager.get_visible_time_range()

        # Show export dialog
        dialog = ExportDialog(self, plotted_tags, start_time, end_time)
        if dialog.exec() != ExportDialog.DialogCode.Accepted:
            return

        settings = dialog.get_export_settings()

        # Get file path
        filepath = save_excel_file_dialog(self)
        if not filepath:
            return
        if not filepath.lower().endswith('.xlsx'):
            filepath += '.xlsx'

        # Get data
        if settings['time_range'] == 'visible':
            df = self.data_manager.get_data_for_tags_in_range(
                plotted_tags, start_time, end_time
            )
        else:
            df = self.data_manager.get_full_data_for_tags(plotted_tags)

        if df is None or df.empty:
            show_error_message(self, "Export Error", "No data available for export.")
            return

        # Get tag info
        tag_info = {
            'units': {tag: self.data_manager.units.get(tag, '') for tag in plotted_tags}
        }

        # Export (pass aggregation params)
        self.status_bar.showMessage("Exporting to Excel...")
        success, message = export_to_excel(
            df,
            filepath,
            tag_info,
            interval=settings.get('interval'),
            stats=settings.get('stats')
        )

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
        else:
            show_error_message(self, "Export Error", message)
            self.status_bar.showMessage("Export failed")

    def _on_tag_check_changed(self, tag_name: str, is_checked: bool):
        """
        Handle tag checkbox state change.

        Args:
            tag_name: Name of the tag
            is_checked: Whether the tag is now checked
        """
        if is_checked:
            # Add plot for this tag
            timestamps, values = self.data_manager.get_data_for_tag(tag_name)
            if timestamps is not None and values is not None:
                success = self.plot_manager.add_plot(tag_name, timestamps, values)
                if success:
                    # Update the axis display in the UI
                    axis = self.plot_manager.get_tag_axis(tag_name)
                    if axis:
                        self.control_panel.update_tag_axis_display(tag_name, axis)
                    self.status_bar.showMessage(f"Plotted {tag_name}", config.STATUS_MESSAGE_TIMEOUT)
                else:
                    self.status_bar.showMessage(f"Failed to plot {tag_name}")
        else:
            # Remove plot for this tag
            success = self.plot_manager.remove_plot(tag_name)
            if success:
                self.status_bar.showMessage(f"Removed {tag_name}", config.STATUS_MESSAGE_TIMEOUT)

    def _on_axis_change_requested(self, tag_name: str, target_axis: str):
        """
        Handle axis change request from UI.

        Args:
            tag_name: Name of the tag
            target_axis: Target axis ('left' or 'right')
        """
        success = self.plot_manager.move_plot_to_axis(tag_name, target_axis)
        if success:
            # Update the axis display in the UI
            self.control_panel.update_tag_axis_display(tag_name, target_axis)
            axis_name = "primary" if target_axis == "left" else "secondary"
            self.status_bar.showMessage(f"Moved {tag_name} to {axis_name} axis", config.STATUS_MESSAGE_TIMEOUT)
        else:
            self.status_bar.showMessage(f"Failed to move {tag_name} to {target_axis} axis")

    def _on_max_axes_reached(self, tag_name: str):
        """
        Handle max axes reached notification from PlotManager.

        Shows a user-friendly message explaining the 2-axis limitation
        and suggesting solutions.

        Args:
            tag_name: Name of the tag that couldn't be added
        """
        # Uncheck the tag in the UI since it couldn't be plotted
        self.control_panel.tag_list_widget.set_tag_checked(tag_name, False)

        # Show informative message dialog
        QMessageBox.warning(
            self,
            "Maximum Axes Reached",
            f"Cannot plot '{tag_name}' - this tag requires a third independent scale.\n\n"
            f"Currently, only 2 different scales are supported (Primary and Secondary axes).\n\n"
            f"To plot this tag, you can:\n"
            f"  • Uncheck other tags with different scales\n"
            f"  • Right-click a plotted tag and use 'Move to Left/Right Axis' to reassign axes\n\n"
            f"Note: Multiple Y-axis support (3+ scales) is planned for a future release."
        )

        self.status_bar.showMessage(
            f"Cannot add '{tag_name}' - maximum of 2 scales supported",
            config.STATUS_MESSAGE_TIMEOUT
        )

    def _update_tag_list(self):
        """Update the tag list with available tags from data manager."""
        tags = self.data_manager.get_tag_list()
        # Store currently checked tags before repopulating
        checked_tags = self.control_panel.get_checked_tags()

        # Get descriptions for all tags
        descriptions = {tag: self.data_manager.get_description_for_tag(tag) for tag in tags}

        # Populate tags with descriptions
        self.control_panel.populate_tags(tags, descriptions)

        # Re-check tags that existed before
        self.control_panel.set_checked_tags(checked_tags)

        # Clear all plots when new data is loaded
        self.plot_manager.clear_all_plots()

        # Show or hide the Tags/Description toggle based on whether descriptions are available
        has_descriptions = bool(self.data_manager.descriptions)
        self.control_panel.set_toggle_visible(has_descriptions)

    def _refresh_plots(self):
        """Efficiently refresh plotted data instead of recreating."""
        checked_tags = self.control_panel.get_checked_tags()
        for tag_name in checked_tags:
            timestamps, values = self.data_manager.get_data_for_tag(tag_name)
            if timestamps is not None and values is not None:
                self.plot_manager.update_plot_data(tag_name, timestamps, values)
        self.status_bar.showMessage("Plots refreshed with appended data.", config.STATUS_MESSAGE_TIMEOUT)

    @pyqtSlot(str)
    def _create_new_plot_widget(self, tag_name: str):
        """
        Create a new stacked plot widget and link its X-axis to the main plot.

        Args:
            tag_name: Name of the tag that triggered the new plot request
        """
        # Create new plot widget with same background color
        new_plot_widget = pg.PlotWidget(background=config.PLOT_BACKGROUND_COLOR)
        new_plot_widget.setMaximumHeight(250)  # Fixed height for stacked plots

        # Add to the main layout (below existing plots)
        self.main_layout.addWidget(new_plot_widget)

        # Link X-axis to main plot for synchronized pan/zoom
        new_plot_widget.setXLink(self.main_plot_widget)

        # Store reference
        self.additional_plots.append(new_plot_widget)

        # Get the PlotItem and pass it back to PlotManager
        new_plot_item = new_plot_widget.getPlotItem()
        self.plot_manager.add_new_plot_item(tag_name, new_plot_item)

        # Re-trigger the plot addition now that the widget is ready
        timestamps, values = self.data_manager.get_data_for_tag(tag_name)
        if timestamps is not None:
            self.plot_manager.add_plot(tag_name, timestamps, values)

        self.status_bar.showMessage(f"Created new stacked plot for {tag_name}", config.STATUS_MESSAGE_TIMEOUT)

    def _show_validation_dialog(self, report, filepath, tag_row, description_row, units_row, data_start_row):
        """
        Show validation dialog and handle user action.

        Args:
            report: ValidationReport with issues found
            filepath: Path to the Excel file
            tag_row: Tag row number
            description_row: Description row number (can be None)
            units_row: Units row number (can be None)
            data_start_row: Data start row number

        Returns:
            User action: ACTION_CONTINUE, ACTION_CLEAN, or ACTION_CANCEL
        """
        filename = os.path.basename(filepath)
        dialog = DataQualityDialog(report, filename, self)
        dialog.exec()

        action = dialog.get_user_action()

        # If user chose to clean, export cleaned file
        if action == DataQualityDialog.ACTION_CLEAN:
            self.status_bar.showMessage("Cleaning data...")
            cleaner = DataCleaner(filepath, tag_row, description_row, units_row, data_start_row)
            success, message, output_path = cleaner.clean_and_export()

            if success:
                show_info_message(self, "Data Cleaned", f"{message}\n\nYou can now load the cleaned file.")
                self.status_bar.showMessage("Data cleaned successfully", config.STATUS_MESSAGE_TIMEOUT)
            else:
                show_error_message(self, "Error Cleaning Data", message)
                self.status_bar.showMessage("Failed to clean data")

        return action

    def _on_check_data_quality(self):
        """Handle manual Check Data Quality button click."""
        # Get file path from dialog
        filepath = open_excel_file_dialog(self)
        if not filepath:
            return

        # Get row numbers from control panel
        tag_row, description_row, units_row, data_start_row = self.control_panel.get_row_numbers()

        # Validate row numbers
        is_valid, error_msg = validate_row_numbers(tag_row, description_row, units_row, data_start_row)
        if not is_valid:
            show_error_message(self, "Invalid Row Numbers", error_msg)
            return

        # Run full validation
        self.status_bar.showMessage("Running comprehensive data quality check...")
        validator = DataValidator(filepath, tag_row, description_row, units_row, data_start_row)
        report = validator.run_full_validation()

        # Always show the dialog, even if no issues found
        if not report.has_issues():
            # Add a success message to the report
            report.add_issue("INFO", "Validation", "No data quality issues detected! File looks good.")

        # Show validation results
        self._show_validation_dialog(report, filepath, tag_row, description_row, units_row, data_start_row)

        self.status_bar.showMessage("Data quality check complete", config.STATUS_MESSAGE_TIMEOUT)

    @pyqtSlot()
    def show_plot_widget(self):
        """Switches the view to show the plot widget."""
        self.plot_stack.setCurrentIndex(1)

    @pyqtSlot()
    def show_placeholder_widget(self):
        """Switches the view to show the placeholder message."""
        self.plot_stack.setCurrentIndex(0)

    def closeEvent(self, event):
        """
        Handle window close event.
        If data is loaded, ask user if they want to save the session before exiting.

        Args:
            event: QCloseEvent
        """
        # Check if there's data loaded
        if self.data_manager.has_data():
            # Create message box with custom buttons
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Save Session Before Exit?")
            msg_box.setText("You have data loaded. Would you like to save your session before exiting?")
            msg_box.setIcon(QMessageBox.Icon.Question)

            # Add custom buttons
            save_button = msg_box.addButton("Save && Exit", QMessageBox.ButtonRole.AcceptRole)
            exit_button = msg_box.addButton("Exit Without Saving", QMessageBox.ButtonRole.DestructiveRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

            # Show dialog and get result
            msg_box.exec()
            clicked_button = msg_box.clickedButton()

            if clicked_button == save_button:
                # Save session before exiting
                filepath = save_session_file_dialog(self)
                if filepath:
                    # Ensure .h5 extension
                    if not filepath.endswith('.h5'):
                        filepath += '.h5'

                    # Save session
                    success, message = self.data_manager.save_session(filepath)
                    if success:
                        event.accept()  # Close the window
                    else:
                        # Show error and don't close
                        show_error_message(self, "Error Saving Session", message)
                        event.ignore()
                else:
                    # User cancelled the save dialog, don't close
                    event.ignore()

            elif clicked_button == exit_button:
                # Exit without saving
                event.accept()

            else:  # cancel_button or closed dialog
                # Cancel close operation
                event.ignore()
        else:
            # No data loaded, just close
            event.accept()
