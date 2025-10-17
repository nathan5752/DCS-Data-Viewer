"""
Main window for the DCS Data Viewer application.
"""

from PyQt6.QtWidgets import QMainWindow, QSplitter, QStatusBar, QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSlot
import pyqtgraph as pg

from ui.widgets.control_panel import ControlPanel
from ui.widgets.placeholder_widget import PlaceholderWidget
from data.data_manager import DataManager
from plotting.plot_manager import PlotManager
from utils.helpers import (
    open_excel_file_dialog, save_session_file_dialog,
    open_session_file_dialog, save_png_file_dialog,
    show_error_message, validate_row_numbers, show_blank_column_warning
)
import config


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

        # Connect signal for creating additional stacked plots
        self.plot_manager.new_plot_requested.connect(self._create_new_plot_widget)

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

        # Load data
        self.status_bar.showMessage("Loading data...")
        success, message, df = self.data_manager.load_excel(
            filepath, tag_row, description_row, units_row, data_start_row, blank_count
        )

        if success:
            self.status_bar.showMessage(message, config.STATUS_MESSAGE_TIMEOUT)
            self._update_tag_list()
            self.control_panel.enable_data_operations(True)
            # Auto-collapse Excel File Parameters after first load
            self.control_panel.collapse_params()
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
            # Auto-collapse Excel File Parameters after loading session
            self.control_panel.collapse_params()
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

        # Append data
        self.status_bar.showMessage("Appending data...")
        success, message, df = self.data_manager.append_data(
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

    @pyqtSlot()
    def show_plot_widget(self):
        """Switches the view to show the plot widget."""
        self.plot_stack.setCurrentIndex(1)

    @pyqtSlot()
    def show_placeholder_widget(self):
        """Switches the view to show the placeholder message."""
        self.plot_stack.setCurrentIndex(0)
