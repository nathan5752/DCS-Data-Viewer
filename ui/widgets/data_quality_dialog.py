"""
Dialog for displaying data quality validation results.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from data.data_validator import ValidationReport
import config


class DataQualityDialog(QDialog):
    """Dialog for displaying data quality validation results."""

    # Return values for user choice
    ACTION_CONTINUE = 1
    ACTION_CLEAN = 2
    ACTION_CANCEL = 0

    def __init__(self, report: ValidationReport, filename: str, parent=None):
        """
        Initialize the data quality dialog.

        Args:
            report: ValidationReport containing issues found
            filename: Name of the file being validated
            parent: Parent widget
        """
        super().__init__(parent)
        self.report = report
        self.filename = filename
        self.user_action = self.ACTION_CANCEL  # Default to cancel
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Data Quality Check Results")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        # Set light background for entire dialog to avoid dark borders
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Title section
        title_label = QLabel(f"Data Quality Check: {self.filename}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                padding: 12px;
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        layout.addWidget(title_label)

        # Summary section
        summary_widget = self._create_summary_section()
        layout.addWidget(summary_widget)

        # Issues section (scrollable)
        issues_widget = self._create_issues_section()
        layout.addWidget(issues_widget, stretch=1)

        # Action buttons
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_summary_section(self) -> QWidget:
        """Create the summary section showing issue counts."""
        summary_group = QGroupBox("Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #424242;
            }
        """)

        layout = QHBoxLayout()
        layout.setSpacing(20)

        counts = self.report.get_issue_count()
        total = counts['errors'] + counts['warnings'] + counts['infos']

        # Total issues
        total_label = QLabel(f"<b>Total Issues:</b> {total}")
        total_label.setStyleSheet("color: #424242; padding: 5px; font-size: 11px;")
        layout.addWidget(total_label)

        layout.addStretch()

        # Errors
        if counts['errors'] > 0:
            error_label = QLabel(f"<b>Errors:</b> {counts['errors']}")
            error_label.setStyleSheet(f"""
                color: {config.SEVERITY_ERROR_COLOR};
                padding: 6px 12px;
                background-color: #ffebee;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.addWidget(error_label)

        # Warnings
        if counts['warnings'] > 0:
            warning_label = QLabel(f"<b>Warnings:</b> {counts['warnings']}")
            warning_label.setStyleSheet(f"""
                color: {config.SEVERITY_WARNING_COLOR};
                padding: 6px 12px;
                background-color: #fff3e0;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.addWidget(warning_label)

        # Infos
        if counts['infos'] > 0:
            info_label = QLabel(f"<b>Info:</b> {counts['infos']}")
            info_label.setStyleSheet(f"""
                color: {config.SEVERITY_INFO_COLOR};
                padding: 6px 12px;
                background-color: #e3f2fd;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.addWidget(info_label)

        summary_group.setLayout(layout)
        return summary_group

    def _create_issues_section(self) -> QScrollArea:
        """Create the scrollable issues section."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)

        # Display errors first
        if self.report.has_errors():
            errors_group = self._create_issue_group(
                "Errors",
                self.report.get_errors(),
                config.SEVERITY_ERROR_COLOR
            )
            content_layout.addWidget(errors_group)

        # Then warnings
        if self.report.has_warnings():
            warnings_group = self._create_issue_group(
                "Warnings",
                self.report.get_warnings(),
                config.SEVERITY_WARNING_COLOR
            )
            content_layout.addWidget(warnings_group)

        # Then info
        infos = self.report.get_infos()
        if infos:
            infos_group = self._create_issue_group(
                "Information",
                infos,
                config.SEVERITY_INFO_COLOR
            )
            content_layout.addWidget(infos_group)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)

        return scroll

    def _create_issue_group(self, title: str, issues: list, color: str) -> QGroupBox:
        """
        Create a group box for a specific severity level.

        Args:
            title: Group title
            issues: List of ValidationIssue objects
            color: Color for the title and markers

        Returns:
            QGroupBox containing the issues
        """
        group = QGroupBox(f"{title} ({len(issues)})")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11px;
                color: {color};
                border: 2px solid {color};
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(6)

        for issue in issues:
            issue_widget = self._create_issue_item(issue, color)
            layout.addWidget(issue_widget)

        group.setLayout(layout)
        return group

    def _create_issue_item(self, issue, color: str) -> QWidget:
        """
        Create a widget for a single issue.

        Args:
            issue: ValidationIssue object
            color: Color for highlighting

        Returns:
            QWidget containing the issue details
        """
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: #fafafa;
                border-left: 4px solid {color};
                border-radius: 3px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)

        # Category and message
        message_html = f"<b>[{issue.category}]</b> {issue.message}"
        if issue.location:
            message_html += f" <span style='color: #757575;'>({issue.location})</span>"

        message_label = QLabel(message_html)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #212121; background-color: transparent; border: none; font-size: 10px;")
        layout.addWidget(message_label)

        # Suggestion (if available)
        if issue.suggestion:
            suggestion_label = QLabel(f"<i>💡 {issue.suggestion}</i>")
            suggestion_label.setWordWrap(True)
            suggestion_label.setStyleSheet("color: #616161; background-color: transparent; border: none; font-size: 9px;")
            layout.addWidget(suggestion_label)

        widget.setLayout(layout)
        return widget

    def _create_button_section(self) -> QHBoxLayout:
        """Create the button section with action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Style for buttons
        button_style = """
            QPushButton {
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
        """

        # Export Cleaned File button (primary action if errors exist)
        self.clean_button = QPushButton("Export Cleaned File")
        self.clean_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #1f77b4;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565a0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.clean_button.clicked.connect(self._on_clean_clicked)
        button_layout.addWidget(self.clean_button)

        button_layout.addStretch()

        # Continue Anyway button (show even with errors, but warn user)
        self.continue_button = QPushButton("Continue Anyway")
        if self.report.has_errors():
            self.continue_button.setStyleSheet(button_style + """
                QPushButton {
                    background-color: #f57c00;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #e65100;
                }
            """)
            self.continue_button.setToolTip("Load data despite errors (may cause issues)")
        else:
            self.continue_button.setStyleSheet(button_style + """
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
            """)
        self.continue_button.clicked.connect(self._on_continue_clicked)
        button_layout.addWidget(self.continue_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        return button_layout

    def _on_clean_clicked(self):
        """Handle Export Cleaned File button click."""
        self.user_action = self.ACTION_CLEAN
        self.accept()

    def _on_continue_clicked(self):
        """Handle Continue Anyway button click."""
        self.user_action = self.ACTION_CONTINUE
        self.accept()

    def _on_cancel_clicked(self):
        """Handle Cancel button click."""
        self.user_action = self.ACTION_CANCEL
        self.reject()

    def get_user_action(self) -> int:
        """
        Get the user's chosen action.

        Returns:
            ACTION_CONTINUE, ACTION_CLEAN, or ACTION_CANCEL
        """
        return self.user_action
