"""
Plot management module for handling PyQtGraph plotting with multi-axis support.
"""

import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
import html
from typing import Optional, Dict, Tuple
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt6.QtWidgets import QGraphicsItem, QApplication
import config

# Debug flag - set to True to see detailed group assignment logging
DEBUG = False


class DateAxis(pg.AxisItem):
    """A custom axis item that displays timestamps as dates."""

    def tickStrings(self, values, scale, spacing):
        """Convert timestamp values to readable date-time strings."""
        strings = []
        for value in values:
            try:
                # Convert to datetime and format
                dt_str = datetime.fromtimestamp(value).strftime("%Y-%m-%d\n%H:%M:%S")
                strings.append(dt_str)
            except (ValueError, OSError, OverflowError) as e:
                # Fallback: show the numeric value if conversion fails
                # This helps debug timestamp issues
                strings.append(f"{value:.0f}")
        return strings


class PlotManager(QObject):
    """Manages plotting operations with automatic multi-axis support."""

    # Signal for requesting new stacked plot widgets (Phase 3) - DISABLED FOR NOW
    # new_plot_requested = pyqtSignal(str)  # Emits tag_name (commented out - stacked plots disabled)

    # Signal for max axes reached (2-axis limitation)
    max_axes_reached = pyqtSignal(str)  # Emits tag_name when unable to add due to axis limit

    # Signals for plot visibility (empty plot handling)
    first_plot_added = pyqtSignal()
    all_plots_removed = pyqtSignal()

    # Signal for Compare Mode UI synchronization
    compare_mode_ui_update_requested = pyqtSignal(bool)  # Emits True when entering, False when exiting

    def __init__(self, plot_widget: pg.PlotWidget, data_manager=None):
        super().__init__()  # Initialize QObject
        self.plot_widget = plot_widget
        self.plot_item = self.plot_widget.getPlotItem()  # Get the central PlotItem
        self.managed_plot_items = [self.plot_item]  # List of PlotItems for multi-plot crosshair
        self.plot_items: Dict[str, Dict] = {}  # {tag_name: {'plot_item': ..., 'axis': ..., 'viewbox': ...}}
        self.color_index = 0
        self.active_plot_count = 0  # Track number of active plots for visibility control
        self.left_axis_data_mean: Optional[float] = None  # Store mean instead of full array
        self.right_viewbox: Optional[pg.ViewBox] = None
        self.right_axis: Optional[pg.AxisItem] = None
        self.data_manager = data_manager  # Reference to DataManager for unit lookups

        # Chart customizations
        self.custom_title: Optional[str] = None
        self.custom_left_label: Optional[str] = None
        self.custom_right_label: Optional[str] = None

        # Plot group management (Phase 3)
        self.plot_groups: Dict = {}  # {group_id: {'plot_item': PlotItem, 'tags': [], 'mean': float}}
        self.tag_to_group: Dict = {}  # {tag_name: group_id}
        self.next_group_id = 0
        self.pending_tags: Dict = {}  # Store tag data while waiting for new plot widget

        # Crosshair and tooltip structures (Phase 2)
        self.crosshair_lines: Dict = {}  # {plot_item: {'v': v_line, 'h': h_line}}
        self.tooltip: Optional[pg.TextItem] = None
        self.mouse_proxy = None
        self.last_highlighted = None

        # Configure the plot widget
        self._configure_plot()

        # Initialize crosshair for main plot
        self._init_crosshair_for_plot(self.plot_item)

        # Initialize first group with main plot (left axis)
        self.plot_groups[0] = {'plot_item': self.plot_item, 'tags': [], 'mean': None}

        # Compare Mode state variables
        self.compare_mode_enabled = config.COMPARE_MODE_DEFAULT_ENABLED
        self.compare_method = config.COMPARE_MODE_DEFAULT_METHOD
        self.compare_scope = config.COMPARE_MODE_DEFAULT_SCOPE

        # Normalization cache: {tag_name: {'min', 'max', 'p5', 'p95', 'mean', 'std', 'computed_for', 'x_window'}}
        self._norm_stats = {}

        # Original data storage for restoration when exiting compare mode
        self._original_data = {}  # {tag_name: {'x': array, 'y': array}}

        # Store state before entering compare mode for restoration
        self._pre_compare_state = {
            'axis_assignments': {},  # {tag_name: 'left'|'right'}
            'right_axis_existed': False,
            'left_label': None,
            'tag_viewbox': {}  # {tag_name: ViewBox}
        }

        # Tooltip settings
        self.tooltip_mode = config.TOOLTIP_MODE_DEFAULT
        self.tooltip_max_lines = config.TOOLTIP_MAX_LINES

        # Throttled timer for visible-window recomputation (150ms)
        self._compare_recalc_timer = QTimer()
        self._compare_recalc_timer.setSingleShot(True)
        self._compare_recalc_timer.setInterval(150)
        self._compare_recalc_timer.timeout.connect(self._recompute_visible_window_norm)

    def _configure_plot(self):
        """Configure plot widget with proper settings."""
        # Set custom DateAxis for the bottom axis
        self.plot_item.setAxisItems({'bottom': DateAxis(orientation='bottom')})

        # Set axis labels
        self.plot_item.setLabel('bottom', 'Time')
        self.plot_item.setLabel('left', 'Value (Primary)')

        # Disable SI prefix on bottom axis to prevent "(1e09)" suffix
        bottom_axis = self.plot_item.getAxis('bottom')
        bottom_axis.enableAutoSIPrefix(False)

        self.plot_item.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=True, y=True)

        # Add legend to the plot and store reference
        self.legend = self.plot_item.addLegend()

        # Enable auto-range
        self.plot_item.enableAutoRange()

    def _get_next_color(self) -> tuple:
        """Get the next color from the color palette."""
        color = config.PLOT_COLORS[self.color_index % len(config.PLOT_COLORS)]
        self.color_index += 1
        return color

    def _update_axis_labels(self):
        """Update axis labels with units from plotted tags."""
        if not self.data_manager:
            return  # Can't update labels without data_manager

        # Collect units for left axis tags
        left_units = set()
        right_units = set()

        for tag_name, plot_info in self.plot_items.items():
            unit = self.data_manager.get_unit_for_tag(tag_name)
            if plot_info['axis'] == 'left':
                left_units.add(unit)
            elif plot_info['axis'] == 'right':
                right_units.add(unit)

        # Update left axis label (only if not custom)
        if not self.custom_left_label:
            if left_units:
                left_label = f"Value ({', '.join(sorted(left_units))})"
            else:
                left_label = "Value (Primary)"
            self.plot_item.setLabel('left', left_label)

        # Update right axis label if it exists (only if not custom)
        if self.right_axis and not self.custom_right_label:
            if right_units:
                right_label = f"Value ({', '.join(sorted(right_units))})"
            else:
                right_label = "Value (Secondary)"
            self.right_axis.setLabel(right_label)

    # =========================================================================
    # Compare Mode - Normalization Helper Methods
    # =========================================================================

    def _compute_stats_entire_series(self, tag_name: str, y_arr: np.ndarray):
        """
        Compute statistics for entire series and store in normalization cache.

        Args:
            tag_name: Name of the tag
            y_arr: Array of Y values
        """
        # Ensure float64 for precision
        y_arr = np.asarray(y_arr, dtype=np.float64)

        # Calculate percentiles and basic stats
        p5 = float(np.nanpercentile(y_arr, config.COMPARE_ROBUST_LO))
        p95 = float(np.nanpercentile(y_arr, config.COMPARE_ROBUST_HI))
        ymin = float(np.nanmin(y_arr))
        ymax = float(np.nanmax(y_arr))
        mean = float(np.nanmean(y_arr))
        std = float(np.nanstd(y_arr))

        self._norm_stats[tag_name] = {
            'min': ymin,
            'max': ymax,
            'p5': p5,
            'p95': p95,
            'mean': mean,
            'std': std,
            'computed_for': 'entire_series',
            'x_window': None
        }

    def _compute_stats_visible_window(self, tag_name: str, x_arr: np.ndarray, y_arr: np.ndarray, x_lo: float, x_hi: float):
        """
        Compute statistics for visible window only.

        Args:
            tag_name: Name of the tag
            x_arr: Array of X values (timestamps)
            y_arr: Array of Y values
            x_lo: Lower X bound of visible window
            x_hi: Upper X bound of visible window
        """
        # Find indices within the visible window
        i0 = int(np.searchsorted(x_arr, x_lo, side='left'))
        i1 = int(np.searchsorted(x_arr, x_hi, side='right'))

        if i1 <= i0:
            # Empty window, keep previous stats if any
            return

        # Get data slice for visible window
        ys = y_arr[i0:i1]

        # Ensure float64
        ys = np.asarray(ys, dtype=np.float64)

        # Calculate percentiles and stats
        p5 = float(np.nanpercentile(ys, config.COMPARE_ROBUST_LO))
        p95 = float(np.nanpercentile(ys, config.COMPARE_ROBUST_HI))
        ymin = float(np.nanmin(ys))
        ymax = float(np.nanmax(ys))
        mean = float(np.nanmean(ys))
        std = float(np.nanstd(ys))

        self._norm_stats[tag_name] = {
            'min': ymin,
            'max': ymax,
            'p5': p5,
            'p95': p95,
            'mean': mean,
            'std': std,
            'computed_for': 'visible_window',
            'x_window': (x_lo, x_hi)
        }

    def _is_flat_series(self, stats: dict) -> bool:
        """
        Check if a series is effectively flat (constant value).

        Args:
            stats: Statistics dictionary for a tag

        Returns:
            True if series is flat, False otherwise
        """
        if not stats:
            return False

        # Check if range is effectively zero
        span = stats['max'] - stats['min']
        robust_span = stats['p95'] - stats['p5']

        return (not np.isfinite(span) or
                span < config.COMPARE_FLAT_THRESHOLD or
                robust_span < config.COMPARE_FLAT_THRESHOLD)

    def _normalize(self, tag_name: str, y_arr: np.ndarray) -> Optional[np.ndarray]:
        """
        Normalize an array to 0-100% based on cached statistics.

        Args:
            tag_name: Name of the tag
            y_arr: Array of Y values to normalize

        Returns:
            Normalized array [0, 100] or None if stats not available
        """
        stats = self._norm_stats.get(tag_name)
        if not stats:
            return None

        # Ensure float64
        y_arr = np.asarray(y_arr, dtype=np.float64)

        # Check for flat series - return 50% line
        if self._is_flat_series(stats):
            return np.full_like(y_arr, 50.0, dtype=np.float64)

        # Select normalization range based on method
        if self.compare_method == 'robust_minmax':
            lo, hi = stats['p5'], stats['p95']
        else:  # 'minmax'
            lo, hi = stats['min'], stats['max']

        # Calculate span
        span = hi - lo

        # Safety check for flat series (shouldn't happen due to earlier check)
        if not np.isfinite(span) or span < config.COMPARE_FLAT_THRESHOLD:
            return np.full_like(y_arr, 50.0, dtype=np.float64)

        # Normalize to 0-100
        yn = (y_arr - lo) * 100.0 / span

        # Clip to [0, 100] to handle outliers
        yn = np.clip(yn, 0.0, 100.0)

        return yn

    def _normalize_point(self, tag_name: str, y_val: float) -> Optional[float]:
        """
        Normalize a single point to 0-100% based on cached statistics.

        Args:
            tag_name: Name of the tag
            y_val: Single Y value to normalize

        Returns:
            Normalized value [0, 100] or None if stats not available
        """
        stats = self._norm_stats.get(tag_name)
        if not stats:
            return None

        # Check for flat series
        if self._is_flat_series(stats):
            return 50.0

        # Select normalization range based on method
        if self.compare_method == 'robust_minmax':
            lo, hi = stats['p5'], stats['p95']
        else:  # 'minmax'
            lo, hi = stats['min'], stats['max']

        # Calculate span
        span = hi - lo

        # Safety check
        if not np.isfinite(span) or span < config.COMPARE_FLAT_THRESHOLD:
            return 50.0

        # Normalize to 0-100
        yn = (y_val - lo) * 100.0 / span

        # Clip to [0, 100]
        yn = np.clip(yn, 0.0, 100.0)

        return yn

    # =========================================================================
    # Compare Mode - Enter/Exit and State Management
    # =========================================================================

    def _enter_compare_mode(self):
        """Enter compare mode: store state, normalize all plots, lock Y-axis."""
        # 1. Store current state for restoration
        self._pre_compare_state['axis_assignments'] = {}
        for tag, info in self.plot_items.items():
            self._pre_compare_state['axis_assignments'][tag] = info['axis']

        self._pre_compare_state['right_axis_existed'] = self.right_viewbox is not None
        self._pre_compare_state['left_label'] = self.custom_left_label or self._get_current_left_label()

        # 2. Store original data for ALL plotted tags
        for tag, info in self.plot_items.items():
            x_data, y_data = info['plot_item'].getData()
            if x_data is not None and y_data is not None:
                self._original_data[tag] = {
                    'x': np.copy(x_data),
                    'y': np.copy(y_data)
                }

        # 3. Hide right axis and unify all plots on left axis
        if self.right_viewbox is not None:
            # Store which viewbox each tag was on before compare mode
            self._pre_compare_state['tag_viewbox'] = {}
            left_vb = self.plot_item.getViewBox()

            # Find all tags plotted on right viewbox and move them to left
            for tag, info in self.plot_items.items():
                current_vb = info.get('viewbox')
                self._pre_compare_state['tag_viewbox'][tag] = current_vb

                if current_vb is self.right_viewbox:
                    plot_data_item = info['plot_item']
                    # Remove from right viewbox
                    try:
                        self.right_viewbox.removeItem(plot_data_item)
                    except Exception:
                        pass  # Already removed or not present
                    # Add to left viewbox
                    left_vb.addItem(plot_data_item)
                    # Update internal tracking
                    info['viewbox'] = left_vb

            # Hide the right axis widget
            if self.right_axis:
                self.right_axis.hide()

        # 4. Compute stats and normalize all visible tags
        for tag, info in self.plot_items.items():
            if tag in self._original_data:
                y_data = self._original_data[tag]['y']
                x_data = self._original_data[tag]['x']

                # Compute stats based on scope
                if self.compare_scope == 'entire_series':
                    self._compute_stats_entire_series(tag, y_data)
                else:  # visible_window
                    vb = self.plot_item.getViewBox()
                    x_range = vb.viewRange()[0]
                    self._compute_stats_visible_window(tag, x_data, y_data, x_range[0], x_range[1])

                # Normalize and update plot
                yn = self._normalize(tag, y_data)
                if yn is not None:
                    info['plot_item'].setData(x_data, yn)

        # 5. Lock Y-axis to [0, 100]
        vb = self.plot_item.getViewBox()
        vb.enableAutoRange(axis=vb.YAxis, enable=False)
        vb.setYRange(config.COMPARE_Y_MIN, config.COMPARE_Y_MAX, padding=0.0)
        vb.setMouseEnabled(x=True, y=False)  # Block Y-axis zoom/pan

        # Also lock right viewbox if it exists
        if self.right_viewbox:
            self.right_viewbox.enableAutoRange(axis=self.right_viewbox.YAxis, enable=False)
            self.right_viewbox.setYRange(config.COMPARE_Y_MIN, config.COMPARE_Y_MAX, padding=0.0)
            self.right_viewbox.setMouseEnabled(x=True, y=False)

        # 6. Update left axis label to "Normalized (%)"
        self.plot_item.setLabel('left', 'Normalized (%)')

        # 7. Wire X-range signal if scope is visible_window
        if self.compare_scope == 'visible_window':
            try:
                self.plot_item.getViewBox().sigXRangeChanged.connect(self._on_x_range_changed)
            except:
                pass  # Already connected

        # 8. Emit signal for UI to update (disable axis buttons, etc.)
        self.compare_mode_ui_update_requested.emit(True)

    def _exit_compare_mode(self):
        """Exit compare mode: restore original data, axes, and interactivity."""
        # 1. Unwire X-range signal
        try:
            self.plot_item.getViewBox().sigXRangeChanged.disconnect(self._on_x_range_changed)
        except:
            pass  # Not connected or already disconnected

        # 2. Restore original data for all plotted tags
        for tag, info in self.plot_items.items():
            if tag in self._original_data:
                x_data = self._original_data[tag]['x']
                y_data = self._original_data[tag]['y']
                info['plot_item'].setData(x_data, y_data)

        # 3. Restore Y-axis interactivity
        vb = self.plot_item.getViewBox()
        vb.setMouseEnabled(x=True, y=True)  # Restore Y-axis zoom/pan
        vb.enableAutoRange(axis=vb.YAxis, enable=True)

        if self.right_viewbox:
            self.right_viewbox.setMouseEnabled(x=True, y=True)
            self.right_viewbox.enableAutoRange(axis=self.right_viewbox.YAxis, enable=True)

        # 4. Auto-range to fit data
        vb.autoRange()

        # 5. Restore left axis label
        if self._pre_compare_state['left_label'] and self._pre_compare_state['left_label'] != 'Value (Primary)':
            # Had a custom label, restore it
            self.plot_item.setLabel('left', self._pre_compare_state['left_label'])
        else:
            # Restore auto-generated label based on units
            self._update_axis_labels()

        # 5a. Restore right axis visibility and move plots back to original viewboxes
        if self._pre_compare_state.get('right_axis_existed') and self.right_axis:
            # Show the right axis
            self.right_axis.show()

            # Move plots back to their original viewboxes
            tag_viewbox_map = self._pre_compare_state.get('tag_viewbox', {})
            left_vb = self.plot_item.getViewBox()

            for tag, target_vb in tag_viewbox_map.items():
                if tag in self.plot_items and target_vb is not None:
                    info = self.plot_items[tag]
                    current_vb = info.get('viewbox')
                    plot_data_item = info['plot_item']

                    # If tag should be on right viewbox but is currently on left, move it back
                    if target_vb is self.right_viewbox and current_vb is not self.right_viewbox:
                        # Remove from left
                        try:
                            left_vb.removeItem(plot_data_item)
                        except Exception:
                            pass
                        # Add to right
                        self.right_viewbox.addItem(plot_data_item)
                        # Update tracking
                        info['viewbox'] = self.right_viewbox

        # 6. Restore right axis if it existed before and plots need it
        # (The right axis state is preserved by the existing multi-axis logic)

        # 7. Clear caches
        self._norm_stats.clear()
        self._original_data.clear()
        self._pre_compare_state = {
            'axis_assignments': {},
            'right_axis_existed': False,
            'left_label': None,
            'tag_viewbox': {}
        }

        # 8. Emit signal for UI to update (re-enable axis buttons, etc.)
        self.compare_mode_ui_update_requested.emit(False)

    def _on_x_range_changed(self, viewbox, x_range):
        """
        Handle X-range changes for visible window normalization.
        Throttled to avoid excessive recomputation.

        Args:
            viewbox: The ViewBox that changed
            x_range: The new X range (not used, we query it when timer fires)
        """
        if not self.compare_mode_enabled or self.compare_scope != 'visible_window':
            return

        # Trigger throttled recompute (restarts timer if already running)
        self._compare_recalc_timer.start()

    def _recompute_visible_window_norm(self):
        """
        Recompute normalization for all visible tags based on current X-range.
        Called by throttled timer after pan/zoom settles.
        """
        if not self.compare_mode_enabled or self.compare_scope != 'visible_window':
            return

        # Get current visible X range
        vb = self.plot_item.getViewBox()
        x_lo, x_hi = vb.viewRange()[0]

        # Recompute stats and normalize for each plotted tag
        for tag, info in self.plot_items.items():
            if tag in self._original_data:
                x_data = self._original_data[tag]['x']
                y_data = self._original_data[tag]['y']

                # Compute stats for visible window
                self._compute_stats_visible_window(tag, x_data, y_data, x_lo, x_hi)

                # Normalize and update plot
                yn = self._normalize(tag, y_data)
                if yn is not None:
                    info['plot_item'].setData(x_data, yn)

    def _recalculate_all_stats_and_redraw(self):
        """
        Recalculate normalization stats for all plotted tags and redraw.
        Used after data append in entire_series scope.
        """
        if not self.compare_mode_enabled:
            return

        for tag, info in self.plot_items.items():
            if tag in self._original_data:
                x_data = self._original_data[tag]['x']
                y_data = self._original_data[tag]['y']

                # Recompute stats based on current scope
                if self.compare_scope == 'entire_series':
                    self._compute_stats_entire_series(tag, y_data)
                else:  # visible_window
                    vb = self.plot_item.getViewBox()
                    x_range = vb.viewRange()[0]
                    self._compute_stats_visible_window(tag, x_data, y_data, x_range[0], x_range[1])

                # Normalize and update plot
                yn = self._normalize(tag, y_data)
                if yn is not None:
                    info['plot_item'].setData(x_data, yn)

    # =========================================================================
    # Compare Mode - Public API
    # =========================================================================

    def set_compare_mode(self, enabled: bool):
        """
        Enable or disable compare mode.

        Args:
            enabled: True to enable compare mode, False to disable
        """
        if self.compare_mode_enabled == enabled:
            return  # No change

        self.compare_mode_enabled = enabled

        if enabled:
            self._enter_compare_mode()
        else:
            self._exit_compare_mode()

    def set_compare_method(self, method: str):
        """
        Set the normalization method.

        Args:
            method: 'robust_minmax' or 'minmax'
        """
        if method not in ['robust_minmax', 'minmax']:
            print(f"Warning: Invalid compare method '{method}', ignoring")
            return

        self.compare_method = method

        # If currently in compare mode, recalculate and redraw
        if self.compare_mode_enabled:
            self._recalculate_all_stats_and_redraw()

    def set_compare_scope(self, scope: str):
        """
        Set the normalization scope.

        Args:
            scope: 'entire_series' or 'visible_window'
        """
        if scope not in ['entire_series', 'visible_window']:
            print(f"Warning: Invalid compare scope '{scope}', ignoring")
            return

        old_scope = self.compare_scope
        self.compare_scope = scope

        # If currently in compare mode, handle scope change
        if self.compare_mode_enabled:
            # Disconnect old signal if switching from visible_window
            if old_scope == 'visible_window':
                try:
                    self.plot_item.getViewBox().sigXRangeChanged.disconnect(self._on_x_range_changed)
                except:
                    pass

            # Recalculate with new scope
            self._recalculate_all_stats_and_redraw()

            # Connect new signal if switching to visible_window
            if scope == 'visible_window':
                try:
                    self.plot_item.getViewBox().sigXRangeChanged.connect(self._on_x_range_changed)
                except:
                    pass  # Already connected

    def get_compare_mode_status(self) -> str:
        """
        Get a status string describing the current compare mode settings.

        Returns:
            Status string for display in UI
        """
        if not self.compare_mode_enabled:
            return "Compare Mode: OFF"

        method_str = "Robust (p5-p95)" if self.compare_method == 'robust_minmax' else "Min-Max"
        scope_str = "Entire series" if self.compare_scope == 'entire_series' else "Visible window"

        return f"Compare Mode: {method_str}, {scope_str}"

    def set_tooltip_mode(self, mode: str):
        """
        Set tooltip detail level ('compact' or 'detailed').

        Args:
            mode: Tooltip mode - 'compact' or 'detailed'
        """
        if mode in ['compact', 'detailed']:
            self.tooltip_mode = mode

    def _init_crosshair_for_plot(self, plot_item: pg.PlotItem):
        """
        Initialize crosshair lines for a plot item.

        Args:
            plot_item: The PlotItem to add crosshairs to
        """
        # Create vertical and horizontal infinite lines
        v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', style=Qt.PenStyle.DashLine))
        h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('k', style=Qt.PenStyle.DashLine))

        # Add lines to the plot item
        plot_item.addItem(v_line, ignoreBounds=True)
        plot_item.addItem(h_line, ignoreBounds=True)

        # Store references
        self.crosshair_lines[plot_item] = {'v': v_line, 'h': h_line}

        # Create tooltip if this is the first plot (only need one tooltip)
        if self.tooltip is None:
            self.tooltip = pg.TextItem(anchor=(0, 1), color=(200, 200, 200), fill=(0, 0, 0, 150))
            plot_item.addItem(self.tooltip)

        # Connect mouse move signal (only once for the main plot's scene)
        if self.mouse_proxy is None:
            self.mouse_proxy = pg.SignalProxy(
                plot_item.scene().sigMouseMoved,
                rateLimit=60,
                slot=self._mouse_moved
            )

    def _mouse_moved(self, event):
        """
        Handle mouse movement for crosshair and tooltip updates.

        Args:
            event: Mouse move event from SignalProxy
        """
        pos = event[0]

        # Find which plot item contains the mouse
        source_item = None
        for item in self.managed_plot_items:
            if item.sceneBoundingRect().contains(pos):
                source_item = item
                break

        if not source_item:
            return

        # Convert scene position to view coordinates
        mouse_point = source_item.vb.mapSceneToView(pos)
        x_pos = mouse_point.x()
        y_pos = mouse_point.y()

        # Update vertical line on ALL managed plots (synced X-axis)
        for item in self.managed_plot_items:
            if item in self.crosshair_lines:
                self.crosshair_lines[item]['v'].setPos(x_pos)

        # Update horizontal line only on source plot
        if source_item in self.crosshair_lines:
            self.crosshair_lines[source_item]['h'].setPos(y_pos)

        # Update tooltip with timestamp and values
        # Check if Alt is held for temporary detailed mode
        alt_held = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier)
        self._update_tooltip(x_pos, y_pos, source_item, alt_override=alt_held)

        # Highlight nearest plot line
        self._highlight_nearest_line(x_pos, source_item)

    # =========================================================================
    # Tooltip Formatting Helpers
    # =========================================================================

    def _format_value(self, x: float) -> str:
        """
        Format value with 3 significant figures, strip trailing zeros.

        Args:
            x: Value to format

        Returns:
            Formatted string
        """
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "—"
        ax = abs(x)
        # Use 3 sig figs; avoid noisy scientific notation for mid-range
        if ax == 0:
            return "0"
        if (ax != 0 and ax < 0.01) or ax >= 1000:
            return f"{x:.3g}"
        s = f"{x:.3f}"
        return s.rstrip('0').rstrip('.')

    def _format_percent(self, p: float) -> str:
        """
        Format percentage as integer with % symbol.

        Args:
            p: Percentage value (0-100)

        Returns:
            Formatted string
        """
        if p is None or (isinstance(p, float) and np.isnan(p)):
            return "—"
        return f"{p:.0f}%"

    def _get_series_color_hex(self, tag_name: str) -> str:
        """
        Get hex color for a tag from its plot item's pen.

        Args:
            tag_name: Name of the tag

        Returns:
            Hex color string (e.g., "#1f77b4")
        """
        if tag_name in self.plot_items:
            plot_item = self.plot_items[tag_name]['plot_item']
            pen = plot_item.opts.get('pen')
            if pen:
                try:
                    qcolor = pen.color()
                    return qcolor.name()
                except:
                    pass
            # Fallback to internal color dict
            color = self.plot_items[tag_name]['color']
            return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        return "#FFFFFF"

    def _update_tooltip(self, x_pos: float, y_pos: float, source_item: pg.PlotItem, alt_override: bool = False):
        """
        Update tooltip content with timestamp and tag values.

        Args:
            x_pos: X position (timestamp)
            y_pos: Y position
            source_item: The PlotItem where mouse is located
            alt_override: If True, temporarily show detailed mode regardless of tooltip_mode
        """
        if not self.tooltip:
            return

        # Determine effective tooltip mode
        effective_mode = "detailed" if alt_override else self.tooltip_mode

        # Format timestamp
        try:
            timestamp_str = datetime.fromtimestamp(x_pos).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, OSError):
            timestamp_str = "Invalid time"

        # Build tooltip lines with (line_html, y_distance) for sorting
        tooltip_lines = []

        for tag_name, plot_info in self.plot_items.items():
            plot_data_item = plot_info['plot_item']
            data = plot_data_item.getData()

            if data[0] is None or len(data[0]) == 0:
                continue

            x_data, y_data = data

            # Get unit
            unit = self.data_manager.get_unit_for_tag(tag_name) if self.data_manager else ''

            # Get color from pen
            color_hex = self._get_series_color_hex(tag_name)
            chip = f'<span style="color:{color_hex};">■</span> '

            # HTML-escape tag name
            safe_tag_name = html.escape(tag_name)

            # Build line based on mode
            if self.compare_mode_enabled and tag_name in self._original_data:
                # Compare mode: use original X array for index alignment
                original_x = self._original_data[tag_name]['x']
                original_y = self._original_data[tag_name]['y']

                # Find nearest point in ORIGINAL data
                idx = np.abs(original_x - x_pos).argmin()

                if idx < len(original_y):
                    original_value = original_y[idx]

                    # Get displayed (normalized) value
                    idx_displayed = np.abs(x_data - x_pos).argmin()
                    displayed_value = y_data[idx_displayed]

                    # Get stats
                    stats = self._norm_stats.get(tag_name)

                    # Compact: Tag • value unit • percent
                    line = f"{chip}{safe_tag_name}: {self._format_value(original_value)} {unit} • {self._format_percent(displayed_value)}"

                    # Detailed: add normalization range
                    if effective_mode == "detailed" and stats:
                        if self._is_flat_series(stats):
                            line += " (flat)"
                        else:
                            scope = "series" if self.compare_scope == "entire_series" else "window"
                            if self.compare_method == "robust_minmax":
                                lo, hi = stats['p5'], stats['p95']
                                line += f" ({scope} robust p5\u2013p95: {self._format_value(lo)}\u2013{self._format_value(hi)} {unit})"
                            else:
                                lo, hi = stats['min'], stats['max']
                                line += f" ({scope} min\u2013max: {self._format_value(lo)}\u2013{self._format_value(hi)} {unit})"

                    # Calculate Y distance for sorting
                    y_distance = abs(original_value - y_pos)
                    tooltip_lines.append((line, y_distance))
            else:
                # Normal mode: simple value
                idx = np.abs(x_data - x_pos).argmin()
                displayed_value = y_data[idx]

                line = f"{chip}{safe_tag_name}: {self._format_value(displayed_value)} {unit}"

                # Calculate Y distance for sorting
                y_distance = abs(displayed_value - y_pos)
                tooltip_lines.append((line, y_distance))

        # Sort by Y proximity
        tooltip_lines.sort(key=lambda x: x[1])

        # Apply line limit
        lines_html = [line for line, _ in tooltip_lines]
        if len(lines_html) > self.tooltip_max_lines:
            extra = len(lines_html) - self.tooltip_max_lines
            lines_html = lines_html[:self.tooltip_max_lines]
            lines_html.append(f"<i>… +{extra} more</i>")

        # Build final HTML with improved styling
        tooltip_html = "<div style='background-color: rgba(0,0,0,0.75); color: #eee; padding: 6px 8px; border-radius: 6px; font-size: 11px; line-height: 1.3;'>"
        tooltip_html += f"<b>{timestamp_str}</b><br>"
        tooltip_html += "<br>".join(lines_html)
        tooltip_html += "</div>"

        # Position and update tooltip
        self.tooltip.setHtml(tooltip_html)
        self.tooltip.setPos(x_pos, y_pos)

    def _highlight_nearest_line(self, x_pos: float, source_item: pg.PlotItem):
        """
        Highlight the plot line nearest to the cursor.

        Args:
            x_pos: X position (timestamp)
            source_item: The PlotItem where mouse is located
        """
        if not self.plot_items:
            return

        # Find closest plot to cursor
        closest_plot = None
        min_distance = float('inf')

        for tag_name, plot_info in self.plot_items.items():
            plot_data_item = plot_info['plot_item']
            data = plot_data_item.getData()

            if data[0] is not None and len(data[0]) > 0:
                x_data, y_data = data
                # Find nearest X point
                idx = np.abs(x_data - x_pos).argmin()

                # Calculate distance from cursor Y to this plot's Y at this X
                # We need to map to scene coordinates for fair comparison
                try:
                    y_val = y_data[idx]
                    # Simple distance in data coordinates
                    distance = abs(idx)  # Use index as proxy for now

                    if distance < min_distance:
                        min_distance = distance
                        closest_plot = plot_data_item
                except (IndexError, TypeError):
                    continue

        # Restore previous highlighted plot
        if self.last_highlighted and self.last_highlighted is not closest_plot:
            if hasattr(self.last_highlighted, 'opts') and 'originalPen' in self.last_highlighted.opts:
                self.last_highlighted.setPen(self.last_highlighted.opts['originalPen'])

        # Highlight the closest plot
        if closest_plot:
            if 'originalPen' not in closest_plot.opts:
                closest_plot.opts['originalPen'] = closest_plot.opts['pen']

            original_pen = closest_plot.opts['originalPen']
            highlight_pen = pg.mkPen(original_pen.color(), width=original_pen.width() * 2)
            closest_plot.setPen(highlight_pen)
            self.last_highlighted = closest_plot

    def add_new_plot_item(self, tag_name: str, plot_item: pg.PlotItem):
        """
        Add a new plot item (from a new stacked plot widget) to the manager.

        Args:
            tag_name: Name of the tag that triggered this new plot
            plot_item: The PlotItem from the new plot widget
        """
        # Create a new group for this plot item
        group_id = self.next_group_id
        self.next_group_id += 1

        self.plot_groups[group_id] = {
            'plot_item': plot_item,
            'tags': [],
            'mean': None
        }

        # Add to managed plots for crosshair
        self.managed_plot_items.append(plot_item)

        # Initialize crosshair for this plot
        self._init_crosshair_for_plot(plot_item)

        # Configure the new plot item
        plot_item.setAxisItems({'bottom': DateAxis(orientation='bottom')})
        plot_item.setLabel('bottom', 'Time')

        # Disable SI prefix on bottom axis to prevent "(1e09)" suffix
        bottom_axis = plot_item.getAxis('bottom')
        bottom_axis.enableAutoSIPrefix(False)

        plot_item.showGrid(x=True, y=True, alpha=0.3)
        plot_item.addLegend()

    def _find_suitable_group(self, new_mean: float) -> Optional[int]:
        """
        Find a suitable group for a tag based on its data mean.

        Args:
            new_mean: Mean of the tag's data

        Returns:
            Group ID if found, None if no suitable group exists
        """
        if DEBUG:
            print(f"[FIND_GROUP] Searching for group for mean: {new_mean:.4f}")

        if new_mean == 0:
            if DEBUG:
                print(f"[FIND_GROUP] Zero mean detected, using Group 0")
            return 0 if 0 in self.plot_groups else None

        for group_id, group_info in self.plot_groups.items():
            if DEBUG:
                print(f"[FIND_GROUP] Checking Group {group_id}...")

            if group_info['mean'] is None:
                if DEBUG:
                    print(f"[FIND_GROUP]   Group {group_id} is EMPTY -> SELECTED")
                return group_id

            group_mean = group_info['mean']
            if DEBUG:
                print(f"[FIND_GROUP]   Group {group_id} mean: {group_mean:.4f}")

            if group_mean == 0:
                if DEBUG:
                    print(f"[FIND_GROUP]   Group {group_id} has zero mean -> SKIP")
                continue

            # Check magnitude difference
            try:
                magnitude_diff = abs(np.log10(new_mean) - np.log10(group_mean))
                if DEBUG:
                    print(f"[FIND_GROUP]   Magnitude diff: {magnitude_diff:.4f} (threshold: {config.AXIS_MAGNITUDE_THRESHOLD})")

                if magnitude_diff <= config.AXIS_MAGNITUDE_THRESHOLD:
                    if DEBUG:
                        print(f"[FIND_GROUP]   Group {group_id} is COMPATIBLE -> SELECTED")
                    return group_id
                else:
                    if DEBUG:
                        print(f"[FIND_GROUP]   Group {group_id} is INCOMPATIBLE -> SKIP")
            except (ValueError, TypeError) as e:
                if DEBUG:
                    print(f"[FIND_GROUP]   Group {group_id} caused error: {e} -> SKIP")
                continue

        if DEBUG:
            print(f"[FIND_GROUP] NO suitable group found -> will create new axis/plot")
        return None  # No suitable group found

    def _should_create_right_axis(self, new_values: np.ndarray) -> bool:
        """
        Determine if a new right axis should be created based on order of magnitude difference.

        Args:
            new_values: Array of values for the new plot

        Returns:
            True if a new axis should be created
        """
        # GUARD: Never create right axis in compare mode
        if self.compare_mode_enabled:
            return False

        # If no data on left axis yet, use left axis
        if self.left_axis_data_mean is None:
            return False

        # If right axis already exists, use it
        if self.right_viewbox is not None:
            return True

        # Calculate mean values (excluding NaN)
        left_mean = self.left_axis_data_mean
        new_mean = np.nanmean(np.abs(new_values))

        # Avoid log of zero
        if left_mean == 0 or new_mean == 0:
            return abs(left_mean - new_mean) > 100  # Heuristic for non-log scale

        # Check order of magnitude difference
        try:
            magnitude_diff = abs(np.log10(new_mean) - np.log10(left_mean))
            return magnitude_diff > config.AXIS_MAGNITUDE_THRESHOLD
        except (ValueError, TypeError):
            return False

    def _create_right_axis(self):
        """Create a right Y-axis for plots with different scales."""
        if self.right_viewbox is not None:
            return  # Already created

        # Create a new ViewBox for the right axis
        self.right_viewbox = pg.ViewBox()
        self.right_axis = pg.AxisItem('right')
        self.right_axis.setLabel('Value (Secondary)')

        # Add the new axis to the layout
        self.plot_item.layout.addItem(self.right_axis, 2, 3)

        # Add the new viewbox to the scene
        self.plot_item.scene().addItem(self.right_viewbox)

        # Link the axis to the viewbox
        self.right_axis.linkToView(self.right_viewbox)

        # Link the new viewbox's X-axis to the main viewbox
        self.right_viewbox.setXLink(self.plot_item.getViewBox())

        # Update views when the plot resizes
        def update_views():
            if self.right_viewbox:  # Guard against None
                self.right_viewbox.setGeometry(self.plot_item.getViewBox().sceneBoundingRect())
                self.right_viewbox.linkedViewChanged(self.plot_item.getViewBox(), self.right_viewbox.XAxis)

        update_views()
        self.plot_item.getViewBox().sigResized.connect(update_views)

    def add_plot(self, tag_name: str, timestamps, values) -> bool:
        """
        Add a new plot line for a tag with group-based scale management.

        Args:
            tag_name: Name of the tag
            timestamps: Pandas Series or array of timestamps
            values: Pandas Series or array of values

        Returns:
            True if successful
        """
        try:
            if timestamps.empty or values.empty:
                print(f"Warning: Empty data for tag {tag_name}")
                return False

            # Convert timestamps to numerical format (seconds since epoch)
            x_data = timestamps.values.astype(np.int64) // 10**9
            y_data = values.to_numpy(dtype=float)

            # ===== COMPARE MODE: Simplified single-axis plotting =====
            if self.compare_mode_enabled:
                # Store original data
                self._original_data[tag_name] = {
                    'x': np.copy(x_data),
                    'y': np.copy(y_data)
                }

                # Compute stats based on scope
                if self.compare_scope == 'entire_series':
                    self._compute_stats_entire_series(tag_name, y_data)
                else:  # visible_window
                    vb = self.plot_item.getViewBox()
                    x_range = vb.viewRange()[0]
                    self._compute_stats_visible_window(tag_name, x_data, y_data, x_range[0], x_range[1])

                # Normalize data
                yn = self._normalize(tag_name, y_data)
                if yn is None:
                    yn = y_data  # Fallback if normalization fails

                # Get color and create plot
                color = self._get_next_color()
                pen = pg.mkPen(color=color, width=config.PLOT_LINE_WIDTH)

                plot_data_item = pg.PlotDataItem(
                    x=x_data,
                    y=yn,  # Use normalized data
                    pen=pen,
                    name=tag_name
                )
                plot_data_item.setDownsampling(auto=True, method=config.DOWNSAMPLE_MODE)

                # Add to left axis only
                self.plot_item.addItem(plot_data_item)

                # Store plot information
                self.plot_items[tag_name] = {
                    'plot_item': plot_data_item,
                    'axis': 'left',  # All plots on left axis in compare mode
                    'viewbox': self.plot_item.getViewBox(),
                    'color': color,
                    'group_id': 0
                }

                # Add to group 0
                if tag_name not in self.plot_groups[0]['tags']:
                    self.plot_groups[0]['tags'].append(tag_name)
                    self.tag_to_group[tag_name] = 0

                # Increment active plot count and emit signal if it's the first one
                self.active_plot_count += 1
                if self.active_plot_count == 1:
                    self.first_plot_added.emit()

                return True  # Success

            # ===== NORMAL MODE: Multi-axis group-based plotting =====
            # Calculate mean for group assignment
            new_mean = np.nanmean(np.abs(y_data))

            # DEBUG: Log tag addition details
            if DEBUG:
                print(f"\n{'='*60}")
                print(f"[ADD_PLOT] Tag: {tag_name}")
                print(f"[ADD_PLOT] Data range: [{y_data.min():.2f}, {y_data.max():.2f}]")
                print(f"[ADD_PLOT] Calculated mean: {new_mean:.4f}")
                print(f"[ADD_PLOT] Current groups: {list(self.plot_groups.keys())}")
                for gid, ginfo in self.plot_groups.items():
                    print(f"[ADD_PLOT]   Group {gid}: mean={ginfo['mean']}, tags={ginfo['tags']}")

            # Find suitable group
            target_group_id = self._find_suitable_group(new_mean)

            # If no suitable group exists, we need either a right axis or a new stacked plot
            if target_group_id is None:
                # Check if we can use right axis on the main plot
                if self.right_viewbox is None:
                    # Create right axis for group 1
                    self._create_right_axis()
                    group_id = 1
                    if group_id not in self.plot_groups:
                        self.plot_groups[group_id] = {'plot_item': self.plot_item, 'tags': [], 'mean': new_mean}
                    target_group_id = group_id
                    if DEBUG:
                        print(f"[ADD_PLOT] Created Group 1 (right axis) with mean={new_mean:.4f}")
                else:
                    # Both axes on main plot are used, cannot add more plots
                    # Emit signal to notify UI that max axes limit has been reached
                    if DEBUG:
                        print(f"[ADD_PLOT] Max axes reached, cannot add {tag_name}")
                    self.max_axes_reached.emit(tag_name)
                    print(f"Warning: Cannot add '{tag_name}' - maximum of 2 different scales supported.")
                    return False  # Failed to add plot due to axis limit

            # Get target group
            group_info = self.plot_groups[target_group_id]
            target_plot_item = group_info['plot_item']

            # Update group mean (only set once - use first tag as reference)
            if group_info['mean'] is None:
                group_info['mean'] = new_mean
                if DEBUG:
                    print(f"[ADD_PLOT] Set Group {target_group_id} reference mean to {new_mean:.4f}")
            else:
                # Keep the original mean as the reference for this group
                if DEBUG:
                    print(f"[ADD_PLOT] Group {target_group_id} keeping reference mean {group_info['mean']:.4f}")

            # Determine which axis/viewbox to use
            if target_group_id == 0:
                # Main plot, left axis
                viewbox = self.plot_item.getViewBox()
                axis = 'left'
                target_item_to_add = self.plot_item
            elif target_group_id == 1 and target_plot_item == self.plot_item:
                # Main plot, right axis
                # Recreate right axis if it was removed
                if self.right_viewbox is None:
                    self._create_right_axis()
                viewbox = self.right_viewbox
                axis = 'right'
                target_item_to_add = self.right_viewbox
            else:
                # Stacked plot
                viewbox = target_plot_item.getViewBox()
                axis = f'group_{target_group_id}'
                target_item_to_add = target_plot_item

            if DEBUG:
                print(f"[ADD_PLOT] Assigned to axis: {axis}")
                print(f"{'='*60}\n")

            # Get color for this plot
            color = self._get_next_color()
            pen = pg.mkPen(color=color, width=config.PLOT_LINE_WIDTH)

            # Create the plot item
            plot_data_item = pg.PlotDataItem(
                x=x_data,
                y=y_data,
                pen=pen,
                name=tag_name
            )

            # Enable downsampling for performance
            plot_data_item.setDownsampling(auto=True, method=config.DOWNSAMPLE_MODE)

            # Add to appropriate viewbox
            target_item_to_add.addItem(plot_data_item)

            # Manually add right-axis items to legend
            # (left-axis items are added automatically, but right-axis items need manual addition)
            if axis == 'right':
                self.legend.addItem(plot_data_item, tag_name)

            # Store plot information
            self.plot_items[tag_name] = {
                'plot_item': plot_data_item,
                'axis': axis,
                'viewbox': viewbox,
                'color': color,
                'group_id': target_group_id
            }

            # Add to group's tag list
            group_info['tags'].append(tag_name)
            self.tag_to_group[tag_name] = target_group_id

            # Update left axis mean (for legacy compatibility)
            if axis == 'left':
                if self.left_axis_data_mean is None:
                    self.left_axis_data_mean = new_mean
                else:
                    self.left_axis_data_mean = (self.left_axis_data_mean + new_mean) / 2

            # Update axis labels with units
            self._update_axis_labels()

            # Increment active plot count and emit signal if it's the first one
            self.active_plot_count += 1
            if self.active_plot_count == 1:
                self.first_plot_added.emit()

            return True

        except Exception as e:
            print(f"Error adding plot for {tag_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def remove_plot(self, tag_name: str) -> bool:
        """
        Remove a plot line for a tag.

        Args:
            tag_name: Name of the tag to remove

        Returns:
            True if successful
        """
        if tag_name not in self.plot_items:
            return False

        try:
            plot_info = self.plot_items[tag_name]
            plot_item = plot_info['plot_item']
            viewbox = plot_info['viewbox']

            # Remove from legend first
            try:
                if self.legend is not None:
                    self.legend.removeItem(plot_item)
            except Exception as legend_err:
                # Legend removal can fail, but don't let it block plot removal
                print(f"Warning: Could not remove legend entry for {tag_name}: {legend_err}")

            # Remove the plot item from its viewbox
            viewbox.removeItem(plot_item)

            # Remove from dictionary
            del self.plot_items[tag_name]

            # Clean up group bookkeeping
            group_id = plot_info.get('group_id')
            if group_id is not None:
                # Remove from group's tag list
                if group_id in self.plot_groups:
                    if tag_name in self.plot_groups[group_id]['tags']:
                        self.plot_groups[group_id]['tags'].remove(tag_name)

                    # If group becomes empty, reset its mean
                    if len(self.plot_groups[group_id]['tags']) == 0:
                        self.plot_groups[group_id]['mean'] = None

                # Remove from tag-to-group mapping
                if tag_name in self.tag_to_group:
                    del self.tag_to_group[tag_name]

            # Decrement active plot count and emit signal if it's the last one
            self.active_plot_count -= 1
            if self.active_plot_count == 0:
                self.all_plots_removed.emit()

            # If no more plots on right axis, remove it
            if self.right_viewbox is not None:
                right_plots = [p for p in self.plot_items.values() if p['axis'] == 'right']
                if len(right_plots) == 0:
                    self._remove_right_axis()

            # Reset left axis mean if no left plots remain
            if not any(p['axis'] == 'left' for p in self.plot_items.values()):
                self.left_axis_data_mean = None

            # Update axis labels after removal
            self._update_axis_labels()

            return True

        except Exception as e:
            print(f"Error removing plot for {tag_name}: {e}")
            return False

    def _remove_right_axis(self):
        """Remove the right axis if it exists and is no longer needed."""
        if self.right_viewbox is None:
            return

        try:
            # FIX: Use plot_item consistently and check if viewbox is in scene
            if self.right_viewbox.scene() is not None:
                self.plot_item.scene().removeItem(self.right_viewbox)
            self.plot_item.layout.removeItem(self.right_axis)
            self.right_viewbox = None
            self.right_axis = None
        except Exception as e:
            print(f"Error removing right axis: {e}")

    def clear_all_plots(self):
        """Remove all plot lines."""
        for tag_name in list(self.plot_items.keys()):
            self.remove_plot(tag_name)

        self.left_axis_data_mean = None
        self.color_index = 0

    def update_plot_data(self, tag_name: str, timestamps, values):
        """Efficiently update data of an existing plot."""
        if tag_name not in self.plot_items:
            return

        try:
            # Use .values to get NumPy array and avoid index-based KeyError issues
            x_data = timestamps.values.astype(np.int64) // 10**9
            y_data = values.to_numpy(dtype=float)
            self.plot_items[tag_name]['plot_item'].setData(x=x_data, y=y_data)
        except Exception as e:
            print(f"Error updating plot data for {tag_name}: {e}")

    def get_plotted_tags(self) -> list:
        """Get list of currently plotted tags."""
        return list(self.plot_items.keys())

    def get_tag_axis(self, tag_name: str) -> Optional[str]:
        """
        Get the current axis for a plotted tag.

        Args:
            tag_name: Name of the tag

        Returns:
            'left', 'right', or axis string for stacked plots, None if not plotted
        """
        if tag_name not in self.plot_items:
            return None
        return self.plot_items[tag_name]['axis']

    def get_visible_time_range(self) -> Tuple[datetime, datetime]:
        """
        Get the currently visible time range from the plot.

        Returns:
            (start_datetime, end_datetime) tuple
        """
        viewbox = self.plot_item.getViewBox()
        x_range = viewbox.viewRange()[0]  # Returns [x_min, x_max]

        # x_range is in Unix timestamp (seconds since epoch)
        start_time = datetime.fromtimestamp(x_range[0])
        end_time = datetime.fromtimestamp(x_range[1])

        return start_time, end_time

    def move_plot_to_axis(self, tag_name: str, target_axis: str) -> bool:
        """
        Move a plot from its current axis to a different axis.

        Args:
            tag_name: Name of the tag to move
            target_axis: Target axis ('left' or 'right')

        Returns:
            True if successful, False otherwise
        """
        # GUARD: No axis changes allowed in compare mode
        if self.compare_mode_enabled:
            return False

        # Validate inputs
        if tag_name not in self.plot_items:
            print(f"Error: Tag {tag_name} is not currently plotted")
            return False

        if target_axis not in ['left', 'right']:
            print(f"Error: Invalid target axis {target_axis}. Must be 'left' or 'right'")
            return False

        # Get current plot info
        plot_info = self.plot_items[tag_name]
        current_axis = plot_info['axis']
        plot_data_item = plot_info['plot_item']
        current_viewbox = plot_info['viewbox']
        current_group_id = plot_info['group_id']

        # Check if already on target axis
        if current_axis == target_axis:
            if DEBUG:
                print(f"[MOVE_PLOT] Tag {tag_name} is already on {target_axis} axis")
            return True

        # Only support moving between Groups 0 (left) and 1 (right) for now
        if current_group_id not in [0, 1]:
            print(f"Warning: Moving plots from stacked plots (Group {current_group_id}) not supported yet")
            return False

        # Determine target group and viewbox
        if target_axis == 'left':
            target_group_id = 0
            target_viewbox = self.plot_item.getViewBox()
        else:  # target_axis == 'right'
            # Create right axis if it doesn't exist
            if self.right_viewbox is None:
                self._create_right_axis()
            target_group_id = 1
            target_viewbox = self.right_viewbox

            # Ensure Group 1 exists
            if target_group_id not in self.plot_groups:
                self.plot_groups[target_group_id] = {'plot_item': self.plot_item, 'tags': [], 'mean': None}

        if DEBUG:
            print(f"\n{'='*60}")
            print(f"[MOVE_PLOT] Moving {tag_name} from {current_axis} (Group {current_group_id}) to {target_axis} (Group {target_group_id})")

        # Remove from legend first
        try:
            if self.legend is not None:
                self.legend.removeItem(plot_data_item)
        except Exception as e:
            if DEBUG:
                print(f"[MOVE_PLOT] Warning: Could not remove from legend: {e}")

        # Remove from current viewbox
        current_viewbox.removeItem(plot_data_item)

        # Add to target viewbox
        if target_axis == 'right':
            # For right axis, add to the right viewbox
            target_viewbox.addItem(plot_data_item)
            # Manually add to legend (required for ViewBox items)
            self.legend.addItem(plot_data_item, tag_name)
        else:
            # For left axis, add to main plot item
            # Check if item is not already in the PlotItem to avoid warning
            if plot_data_item not in self.plot_item.listDataItems():
                self.plot_item.addItem(plot_data_item)
            # Legend entry is created automatically when adding to PlotItem

        # Update plot_items dictionary
        plot_info['axis'] = target_axis
        plot_info['viewbox'] = target_viewbox
        plot_info['group_id'] = target_group_id

        # Update group bookkeeping
        # Remove from old group's tag list
        if current_group_id in self.plot_groups:
            if tag_name in self.plot_groups[current_group_id]['tags']:
                self.plot_groups[current_group_id]['tags'].remove(tag_name)

            # If group becomes empty, reset its mean
            if len(self.plot_groups[current_group_id]['tags']) == 0:
                self.plot_groups[current_group_id]['mean'] = None
                if DEBUG:
                    print(f"[MOVE_PLOT] Group {current_group_id} is now empty, reset mean")

        # Add to new group's tag list
        if target_group_id in self.plot_groups:
            if tag_name not in self.plot_groups[target_group_id]['tags']:
                self.plot_groups[target_group_id]['tags'].append(tag_name)

            # Update group mean if this is the first tag
            if self.plot_groups[target_group_id]['mean'] is None:
                # Calculate mean from this plot's data
                data = plot_data_item.getData()
                if data[1] is not None and len(data[1]) > 0:
                    new_mean = np.nanmean(np.abs(data[1]))
                    self.plot_groups[target_group_id]['mean'] = new_mean
                    if DEBUG:
                        print(f"[MOVE_PLOT] Set Group {target_group_id} mean to {new_mean:.4f}")

        # Update tag-to-group mapping
        self.tag_to_group[tag_name] = target_group_id

        # Update left axis mean tracking (for legacy compatibility)
        if target_axis == 'left':
            data = plot_data_item.getData()
            if data[1] is not None and len(data[1]) > 0:
                new_mean = np.nanmean(np.abs(data[1]))
                if self.left_axis_data_mean is None:
                    self.left_axis_data_mean = new_mean
                else:
                    # Recalculate average of all left axis plots
                    left_plots = [p for p in self.plot_items.values() if p['axis'] == 'left']
                    if len(left_plots) > 0:
                        means = []
                        for p in left_plots:
                            p_data = p['plot_item'].getData()
                            if p_data[1] is not None and len(p_data[1]) > 0:
                                means.append(np.nanmean(np.abs(p_data[1])))
                        if means:
                            self.left_axis_data_mean = np.mean(means)
        elif current_axis == 'left':
            # Recalculate left axis mean after removing a plot
            left_plots = [p for p in self.plot_items.values() if p['axis'] == 'left']
            if len(left_plots) == 0:
                self.left_axis_data_mean = None
            else:
                means = []
                for p in left_plots:
                    p_data = p['plot_item'].getData()
                    if p_data[1] is not None and len(p_data[1]) > 0:
                        means.append(np.nanmean(np.abs(p_data[1])))
                if means:
                    self.left_axis_data_mean = np.mean(means)

        # Update axis labels with units
        self._update_axis_labels()

        # Remove right axis if no longer needed
        if current_axis == 'right':
            right_plots = [p for p in self.plot_items.values() if p['axis'] == 'right']
            if len(right_plots) == 0:
                self._remove_right_axis()
                if DEBUG:
                    print(f"[MOVE_PLOT] Removed empty right axis")

        # Update viewbox ranges to show data properly
        try:
            target_viewbox.autoRange()
            if current_viewbox != target_viewbox:
                current_viewbox.autoRange()
        except Exception as e:
            if DEBUG:
                print(f"[MOVE_PLOT] Warning: Could not auto-range viewboxes: {e}")

        if DEBUG:
            print(f"[MOVE_PLOT] Successfully moved {tag_name} to {target_axis} axis")
            print(f"{'='*60}\n")

        return True

    @pyqtSlot(bool)
    def set_y_axis_lock(self, is_locked: bool):
        """
        Enable or disable Y-axis mouse interaction on all plots.

        Args:
            is_locked: True to lock Y-axis (disable mouse zoom/pan on Y), False to unlock
        """
        if DEBUG:
            print(f"[Y-AXIS LOCK] {'ENABLED' if is_locked else 'DISABLED'}")

        # Update all managed plot items
        for plot_item in self.managed_plot_items:
            # setMouseEnabled(x=True, y=False) means Y is disabled, X is still enabled
            plot_item.getViewBox().setMouseEnabled(x=True, y=not is_locked)

        # Also update right viewbox if it exists
        if self.right_viewbox:
            self.right_viewbox.setMouseEnabled(x=True, y=not is_locked)

    def reset(self):
        """
        Reset the PlotManager to its initial state.
        Clears all plots, groups, and resets axis configurations.
        """
        # Clear all plots
        self.clear_all_plots()

        # Reset group management
        self.plot_groups = {0: {'plot_item': self.plot_item, 'tags': [], 'mean': None}}
        self.tag_to_group = {}
        self.next_group_id = 0
        self.pending_tags = {}

        # Reset axis state
        self.left_axis_data_mean = None
        if self.right_viewbox is not None:
            self._remove_right_axis()

        # Reset color index
        self.color_index = 0

        # Reset active plot count
        self.active_plot_count = 0

        # Reset viewbox to default ranges
        self.plot_item.getViewBox().enableAutoRange()
        self.plot_item.getViewBox().autoRange()

        # Clear chart customizations
        self.custom_title = None
        self.custom_left_label = None
        self.custom_right_label = None

        # Reset axis labels to defaults
        self.plot_item.setLabel('left', 'Value (Primary)')
        self.plot_item.setLabel('bottom', 'Time')

        # Clear chart title
        self.plot_item.setTitle("")

    def set_chart_customizations(self, title: str, left_label: str, right_label: str):
        """
        Apply custom chart title and axis labels.

        Args:
            title: Custom chart title (empty string to clear)
            left_label: Custom left Y-axis label (empty string for auto-generated)
            right_label: Custom right Y-axis label (empty string for auto-generated)
        """
        # Store customizations
        self.custom_title = title if title else None
        self.custom_left_label = left_label if left_label else None
        self.custom_right_label = right_label if right_label else None

        # Apply chart title with styling (larger, bold)
        if self.custom_title:
            self.plot_item.setTitle(
                f'<span style="font-size: 16pt; font-weight: bold">{self.custom_title}</span>'
            )
        else:
            self.plot_item.setTitle("")

        # Apply left axis label
        if self.custom_left_label:
            self.plot_item.setLabel('left', self.custom_left_label)
        else:
            # Revert to auto-generated label
            self._update_axis_labels()

        # Apply right axis label (if right axis exists)
        if self.right_axis:
            if self.custom_right_label:
                self.right_axis.setLabel(self.custom_right_label)
            else:
                # Revert to auto-generated label
                self._update_axis_labels()

    def get_chart_customizations(self) -> tuple:
        """
        Get the current chart customizations.

        Returns:
            Tuple of (title, left_label, right_label)
        """
        return (
            self.custom_title or "",
            self.custom_left_label or self._get_current_left_label(),
            self.custom_right_label or self._get_current_right_label()
        )

    def _get_current_left_label(self) -> str:
        """Get the current left axis label."""
        return self.plot_item.getAxis('left').labelText or "Value (Primary)"

    def _get_current_right_label(self) -> str:
        """Get the current right axis label."""
        if self.right_axis:
            return self.right_axis.labelText or "Value (Secondary)"
        return "Value (Secondary)"

    def has_right_axis(self) -> bool:
        """
        Check if the right axis currently exists.

        Returns:
            True if right axis exists, False otherwise
        """
        return self.right_axis is not None

    def export_to_png(self, filepath: str) -> tuple[bool, str]:
        """
        Export the current plot to a PNG file with publication-quality settings.

        This method temporarily switches the plot appearance to white background with
        black foreground (suitable for technical reports), exports at high resolution
        (2400px width ≈ 8 inches at 300 DPI), then restores the original appearance.

        Args:
            filepath: Full path where the PNG file should be saved

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Save original colors
            original_bg = self.plot_widget.backgroundBrush()

            # Hide crosshairs and tooltip during export
            for plot_item, lines in self.crosshair_lines.items():
                lines['v'].setVisible(False)
                lines['h'].setVisible(False)

            if self.tooltip:
                self.tooltip.setVisible(False)

            # Fix legend scaling: disable ItemIgnoresTransformations flag
            # This allows the legend to scale properly at high export resolutions
            original_legend_flag = self.legend.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
            self.legend.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)

            # Temporarily switch to white background with black foreground for export
            self.plot_widget.setBackground(config.EXPORT_BACKGROUND_COLOR)

            # Store original pen colors
            original_pens = {}
            for tag_name, plot_info in self.plot_items.items():
                plot_data_item = plot_info['plot_item']
                original_pens[tag_name] = plot_data_item.opts['pen']
                # Keep original colors instead of forcing black for better visibility

            # Create exporter with high-quality settings
            exporter = pg.exporters.ImageExporter(self.plot_item)

            # Configure export parameters for publication quality
            exporter.parameters()['width'] = config.EXPORT_WIDTH_PIXELS

            # Export to file
            exporter.export(filepath)

            # Restore original appearance
            self.plot_widget.setBackground(original_bg)
            for tag_name, original_pen in original_pens.items():
                if tag_name in self.plot_items:
                    self.plot_items[tag_name]['plot_item'].setPen(original_pen)

            # Restore legend flag
            if original_legend_flag:
                self.legend.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

            # Show crosshairs and tooltip again
            for plot_item, lines in self.crosshair_lines.items():
                lines['v'].setVisible(True)
                lines['h'].setVisible(True)

            if self.tooltip:
                self.tooltip.setVisible(True)

            return True, f"Plot exported successfully to {filepath}"

        except Exception as e:
            # Attempt to restore original appearance even if export failed
            try:
                self.plot_widget.setBackground(original_bg)
                for tag_name, original_pen in original_pens.items():
                    if tag_name in self.plot_items:
                        self.plot_items[tag_name]['plot_item'].setPen(original_pen)

                # Restore legend flag
                if original_legend_flag:
                    self.legend.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

                # Show crosshairs and tooltip again
                for plot_item, lines in self.crosshair_lines.items():
                    lines['v'].setVisible(True)
                    lines['h'].setVisible(True)

                if self.tooltip:
                    self.tooltip.setVisible(True)
            except:
                pass

            return False, f"Failed to export plot: {str(e)}"
