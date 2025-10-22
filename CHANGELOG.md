# Changelog

All notable changes to DCS Data Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-10-22

### Added
- **Compare Mode** feature for normalizing all visible tags to 0-100% scale, enabling easy comparison of relative trends between signals with very different units or magnitudes
- Two normalization methods: **Robust Min-Max (p5-p95)** (reduces outlier impact) and **Min-Max** (classic normalization)
- Two scope options: **Entire series** (stable normalization using full dataset) and **Visible window** (dynamic normalization based on current zoom level)
- Tooltip display modes: **Compact** (default, clean display) and **Detailed** (shows normalization reference ranges)
- Keyboard shortcuts: **Ctrl+Shift+C** to toggle Compare Mode, **T** to toggle tooltip mode
- **Alt key override** for temporarily viewing detailed tooltip mode
- Automatic axis button management: buttons disabled in Compare Mode to prevent multi-axis conflicts
- Automatic right axis hiding when entering Compare Mode, with restoration on exit
- Compare Mode status label showing current method and scope settings
- Throttled recalculation (150ms) for smooth performance with visible window scope
- Flat series detection: series with span < 1e-10 render at 50% with "(flat)" indicator
- Y-proximity sorting in tooltips: series nearest to cursor appear first
- Tooltip line limiting: max 6 lines with "+N more" overflow indicator
- HTML-escaped tag names in tooltips for safety

### Changed
- Enhanced tooltips with normalized percentage display in Compare Mode (e.g., "Tag: 42.1 A • 78%")
- Detailed tooltip mode shows normalization reference ranges (e.g., "series robust p5–p95: 10.2–63.7 A")
- Y-axis lock checkbox automatically disabled and locked to 0-100% range when Compare Mode is active
- Export Plot tooltip clarified: "Exports normalized view if Compare Mode is active"
- Export Data tooltip clarified: "Export plotted tags to Excel with optional aggregation (Exports original values - Compare Mode does not affect data)"
- Help guide expanded with Section 7: Compare Mode documentation covering methods, scopes, usage, and important notes
- Tooltip formatting improved: 3 significant figures, no trailing zeros, clean number display

### Fixed
- Compare Mode automatically exits when loading new data to prevent state confusion
- Normalization statistics recalculate when appending data with 'entire series' scope
- Axis assignment locked at logic layer: `move_plot_to_axis()` returns False immediately if Compare Mode enabled
- Multi-axis creation prevented: `_should_create_right_axis()` returns False in Compare Mode
- Right axis properly hidden/shown when entering/exiting Compare Mode
- Viewbox mappings correctly stored and restored when switching between modes
- Index alignment uses original X array in Compare Mode to avoid downsampling mismatches
- No-data guard prevents enabling Compare Mode when no data is loaded

## [1.3.0] - 2025-10-20

### Fixed
- Excel parameter spinbox buttons that were only partially functional
- Excel parameters can no longer be modified after data is loaded, preventing user confusion
- Parameters are automatically disabled (grayed out) and collapsed after loading data or sessions

### Changed
- Removed up/down arrow buttons from all spinbox inputs for cleaner UX
- Users now type row numbers directly instead of using increment/decrement buttons
- Excel parameters section can still be expanded/collapsed when disabled to view current settings
- Added helpful tooltip explaining that parameters are locked after loading and how to re-enable them
- Parameters automatically re-enable when user clicks "Load New Data" and confirms session reset

## [1.2.0] - 2025-10-19

### Added
- Global exception handler that catches uncaught exceptions and logs to `~/.dcs_data_viewer/logs/error.log`
- User-friendly error dialogs with detailed error information and log file location
- Comprehensive help guide with 6 sections (Getting Started, Working with Data, Interacting with Plots, Saving & Loading, Data Quality & Export, Troubleshooting)
- Scrollable help dialog (650x500px) with HTML formatting
- CSV to Excel converter script (`scripts/csv_to_excel.py`) with argparse CLI
- Sample CSV data generator (`scripts/generate_sample_csv.py`) for testing
- Error log directory at `~/.dcs_data_viewer/logs/` for troubleshooting

### Fixed
- Reset session flow now properly resets viewbox to default zoom/pan state
- Axis labels reset to defaults ("Value (Primary)", "Time") after session reset
- Reset session no longer immediately opens file dialog (allows parameter adjustment)
- Excel parameters now consistently auto-collapse after data load
- RuntimeError in tag_list.py clear() method that occurred after reset
- Black background in help dialog - now uses explicit white background styling

### Changed
- Enhanced error messages for FileNotFoundError with troubleshooting steps (check path, permissions, file location)
- Enhanced error messages for PermissionError with actionable solutions (close Excel, check read-only, admin rights)
- Improved error messages for generic errors with diagnostic information
- CSV converter includes overwrite protection with user confirmation prompt
- CSV converter supports --force flag to bypass confirmation
- CSV converter supports --help and --version flags

## [1.1.0] - 2025-10-19

### Added
- Data quality checks with duplicate timestamp detection during data appending
- User warnings for overlapping time ranges when appending data
- Excel export feature for plotted tags with time range selection (visible range or full dataset)
- Data aggregation with configurable time intervals (5s, 10s, 30s, 1min, 5min, 15min, 1hr, custom)
- Multiple aggregation statistics per interval (mean, min, max) with selectable combinations
- Proper Excel export formatting (bold headers, frozen panes, auto-width columns, units row)
- Timezone-aware exports that match plot display times (UTC/local conversion)
- Export dialog with intuitive controls for all export options
- Performance optimization: Large datasets (100K+ rows) export in 2-10 seconds

### Fixed
- Timezone conversion issues in Excel exports (local time now matches plot display)
- Excel file structure formatting (tag names, units, and data rows properly aligned)
- Timestamp loading constraint that prevented certain Excel date formats from loading

### Changed
- Export operations use pandas resample for efficient time-series aggregation
- Aggregated column naming follows pattern: TagName_statistic (e.g., Tag1_mean, Tag1_min, Tag1_max)
- Units row in exported Excel files properly duplicates units for each aggregated statistic

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
