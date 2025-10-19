"""
Export dialog for Excel data export.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QLabel, QPushButton, QListWidget,
                             QComboBox, QCheckBox, QWidget, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt
from datetime import datetime
import config


class ExportDialog(QDialog):
    """Dialog for configuring Excel export options."""

    def __init__(self, parent, plotted_tags: list, start_time: datetime, end_time: datetime):
        super().__init__(parent)
        self.plotted_tags = plotted_tags
        self.start_time = start_time
        self.end_time = end_time

        self.setWindowTitle("Export Data to Excel")
        self.setModal(True)
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Tags to export (read-only list)
        tags_group = QGroupBox("Tags to Export (Currently Plotted)")
        tags_layout = QVBoxLayout()
        self.tags_list = QListWidget()
        self.tags_list.addItems(self.plotted_tags)
        self.tags_list.setEnabled(False)  # Read-only
        tags_layout.addWidget(self.tags_list)
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        # Time range selection
        time_group = QGroupBox("Time Range")
        time_layout = QVBoxLayout()

        self.visible_range_radio = QRadioButton("Visible Range")
        self.full_range_radio = QRadioButton("Full Dataset")
        self.visible_range_radio.setChecked(True)

        # Show range info
        visible_info = QLabel(f"{self.start_time:%Y-%m-%d %H:%M:%S} to {self.end_time:%Y-%m-%d %H:%M:%S}")
        visible_info.setStyleSheet("color: gray; font-size: 10px;")

        time_layout.addWidget(self.visible_range_radio)
        time_layout.addWidget(visible_info)
        time_layout.addWidget(self.full_range_radio)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Data Options (Aggregation)
        agg_group = QGroupBox("Data Options")
        agg_layout = QVBoxLayout()

        self.raw_data_radio = QRadioButton("Raw Data (No Aggregation)")
        self.aggregate_radio = QRadioButton("Aggregate Data")
        self.raw_data_radio.setChecked(True)

        agg_layout.addWidget(self.raw_data_radio)
        agg_layout.addWidget(self.aggregate_radio)

        # Aggregation controls (initially disabled)
        self.agg_controls_widget = QWidget()
        agg_controls_layout = QVBoxLayout()

        # Interval selection
        interval_label = QLabel("Aggregation Interval:")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(list(config.AGGREGATION_PRESETS.keys()))
        agg_controls_layout.addWidget(interval_label)
        agg_controls_layout.addWidget(self.interval_combo)

        # Custom interval input (QSpinBox + QComboBox for better UX)
        self.custom_interval_widget = QWidget()
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra padding

        custom_layout.addWidget(QLabel("Custom Interval:"))
        self.custom_interval_value = QSpinBox()
        self.custom_interval_value.setRange(1, 999)  # Reasonable range
        self.custom_interval_value.setValue(5)

        self.custom_interval_unit = QComboBox()
        self.custom_interval_unit.addItems(["Seconds", "Minutes", "Hours"])

        custom_layout.addWidget(self.custom_interval_value)
        custom_layout.addWidget(self.custom_interval_unit)
        self.custom_interval_widget.setLayout(custom_layout)
        self.custom_interval_widget.setVisible(False)  # Initially hidden
        agg_controls_layout.addWidget(self.custom_interval_widget)

        # Statistics checkboxes
        stats_label = QLabel("Statistics to Include:")
        self.mean_checkbox = QCheckBox("Mean (Average)")
        self.min_checkbox = QCheckBox("Min")
        self.max_checkbox = QCheckBox("Max")
        self.mean_checkbox.setChecked(True)
        self.min_checkbox.setChecked(True)
        self.max_checkbox.setChecked(True)

        agg_controls_layout.addWidget(stats_label)
        agg_controls_layout.addWidget(self.mean_checkbox)
        agg_controls_layout.addWidget(self.min_checkbox)
        agg_controls_layout.addWidget(self.max_checkbox)

        self.agg_controls_widget.setLayout(agg_controls_layout)
        self.agg_controls_widget.setEnabled(False)
        agg_layout.addWidget(self.agg_controls_widget)

        agg_group.setLayout(agg_layout)
        layout.addWidget(agg_group)

        # Connect signals
        self.aggregate_radio.toggled.connect(self._on_aggregate_toggled)
        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        self.mean_checkbox.toggled.connect(self._on_stat_toggled)
        self.min_checkbox.toggled.connect(self._on_stat_toggled)
        self.max_checkbox.toggled.connect(self._on_stat_toggled)

        # Buttons
        button_layout = QHBoxLayout()
        self.export_button = QPushButton("Export")
        self.cancel_button = QPushButton("Cancel")

        self.export_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _on_aggregate_toggled(self, checked: bool):
        """Enable/disable aggregation controls."""
        self.agg_controls_widget.setEnabled(checked)

    def _on_interval_changed(self, interval_name: str):
        """Show custom input if 'Custom...' selected."""
        self.custom_interval_widget.setVisible(interval_name == "Custom...")

    def _on_stat_toggled(self):
        """Ensure at least one checkbox remains checked."""
        checked_stats = []
        if self.mean_checkbox.isChecked():
            checked_stats.append(self.mean_checkbox)
        if self.min_checkbox.isChecked():
            checked_stats.append(self.min_checkbox)
        if self.max_checkbox.isChecked():
            checked_stats.append(self.max_checkbox)

        if len(checked_stats) == 1:
            # Disable the last checked box to prevent unchecking
            checked_stats[0].setEnabled(False)
        else:
            # Re-enable all boxes if more than one is checked
            self.mean_checkbox.setEnabled(True)
            self.min_checkbox.setEnabled(True)
            self.max_checkbox.setEnabled(True)

    def accept(self):
        """Override to validate settings before closing."""
        settings = self.get_export_settings()

        if settings['aggregate']:
            if not settings['stats']:
                QMessageBox.warning(self, "Invalid Settings",
                                  "Please select at least one statistic (Mean, Min, or Max).")
                return  # Stop the accept process

            if not settings['interval']:
                QMessageBox.warning(self, "Invalid Settings",
                                  "The custom aggregation interval cannot be empty.")
                return  # Stop the accept process

        # If all checks pass, call the parent's accept() method to close the dialog
        super().accept()

    def get_export_settings(self) -> dict:
        """Return user's export settings."""
        if self.aggregate_radio.isChecked():
            # Get interval
            interval_name = self.interval_combo.currentText()
            if interval_name == "Custom...":
                value = self.custom_interval_value.value()
                unit_map = {"Seconds": "s", "Minutes": "min", "Hours": "h"}
                unit = unit_map[self.custom_interval_unit.currentText()]
                interval = f"{value}{unit}"
            else:
                interval = config.AGGREGATION_PRESETS[interval_name]

            # Get stats
            stats = []
            if self.mean_checkbox.isChecked():
                stats.append('mean')
            if self.min_checkbox.isChecked():
                stats.append('min')
            if self.max_checkbox.isChecked():
                stats.append('max')

            return {
                'time_range': 'visible' if self.visible_range_radio.isChecked() else 'full',
                'aggregate': True,
                'interval': interval,
                'stats': stats
            }
        else:
            return {
                'time_range': 'visible' if self.visible_range_radio.isChecked() else 'full',
                'aggregate': False,
                'interval': None,
                'stats': None
            }
