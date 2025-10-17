# Changelog

All notable changes to DCS Data Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-17

### Added
- Y-axis lock checkbox to prevent accidental zooming while inspecting data
- Debug flag (DEBUG) in plot_manager.py for optional verbose logging
- Guard clause in update_views() closure to prevent AttributeError

### Fixed
- AttributeError crash in update_views() closure when right_viewbox is None
- Multi-axis logic: groups now use first tag as stable reference mean (not running average)
- Prevents drift in group magnitude calculations

### Changed
- Group mean calculation now uses first tag as permanent reference
- Improved stability of multi-axis assignment algorithm

## [2.0.0] - 2025-01-XX

### Added
- Interactive crosshair system synchronized across all plots
- Interactive tooltip showing timestamp and all tag values at cursor
- Line highlighting (nearest line to cursor highlights with 2x width)
- 60Hz rate limiting for smooth performance during mouse movement
- Multi-axis plotting with intelligent scale detection
- Right axis support for secondary Y-axis
- Stacked plots that dynamically create additional plot panels
- X-axis synchronization across all plots (pan/zoom linked)
- Plot legend with automatic tag names and color coding
- Dynamic axis labels showing units for each Y-axis
- Tag search/filter functionality with real-time filtering
- Units storage and display extracted from Excel files

### Changed
- Refactored plot management to use group-based scale assignment
- Improved magnitude comparison algorithm (threshold: 1.5)
- Enhanced plot organization for better handling of multiple scale ranges

## [1.0.0] - Initial Release

### Added
- Excel data loading with configurable row numbers (tag_row, units_row, data_start_row)
- HDF5 session management for fast save/load operations
- Data appending with automatic duplicate removal based on timestamps
- PyQtGraph plotting with automatic downsampling for performance
- Basic multi-axis support (left and right Y-axes)
- Tag selection with checkbox-based interface
- Pan and zoom capabilities
- Color cycling for multiple plot lines
- Clean modular architecture (data/plotting/ui/utils layers)
- Error handling for all file operations
- QSplitter layout (30% control panel, 70% plot area)
- Status bar for user feedback
- Test data generators (quick and large dataset options)
- PyInstaller configuration for building standalone executable
- Comprehensive documentation (README, CLAUDE.md)
