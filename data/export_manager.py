"""
Excel export functionality for time-series data.
"""

import pandas as pd
from typing import Tuple, Optional, Dict, List
from openpyxl.styles import Font


def _aggregate_data(df: pd.DataFrame, interval: str, stats: List[str]) -> pd.DataFrame:
    """
    Aggregates time-series DataFrame to specified interval.

    Args:
        df: DataFrame with datetime index (or first column as datetime)
        interval: Pandas offset alias (e.g., '1T', '5S', '1H')
        stats: List of aggregation functions (e.g., ['mean', 'min', 'max'])

    Returns:
        Aggregated DataFrame with flattened column names (e.g., 'Tag1_mean')

    Example:
        Input columns: ['Time', 'Tag1', 'Tag2']
        Stats: ['mean', 'min', 'max']
        Output columns: ['Time', 'Tag1_mean', 'Tag1_min', 'Tag1_max',
                         'Tag2_mean', 'Tag2_min', 'Tag2_max']
    """
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        timestamp_col = df.columns[0]
        df = df.set_index(timestamp_col)
        df.index = pd.to_datetime(df.index)

    # Resample creates multi-level columns: ('Tag1', 'mean'), ('Tag1', 'min'), ...
    aggregated_df = df.resample(interval).agg(stats)

    # Flatten column names: ('Tag1', 'mean') -> 'Tag1_mean'
    aggregated_df.columns = ['_'.join(col).strip() for col in aggregated_df.columns.values]

    # Remove intervals with no data (all NaN)
    aggregated_df.dropna(how='all', inplace=True)

    return aggregated_df.reset_index()


def export_to_excel(
    df: pd.DataFrame,
    filepath: str,
    tag_info: Optional[Dict[str, Dict]] = None,
    interval: Optional[str] = None,
    stats: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Export DataFrame to Excel with optional aggregation.

    Args:
        df: DataFrame with timestamp column + tag columns
        filepath: Full path to .xlsx file
        tag_info: Optional dict with 'units' and 'descriptions' dicts
        interval: Optional pandas offset for aggregation (e.g., '1T')
        stats: Optional list of stats (e.g., ['mean', 'min', 'max'])

    Returns:
        (success: bool, message: str)
    """
    try:
        # Aggregate if requested
        if interval and stats:
            df = _aggregate_data(df, interval, stats)

            # Check if aggregation resulted in empty DataFrame
            if df.empty:
                return False, "Aggregation resulted in no data. Try a smaller interval."
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write data without headers starting from row 3
            df.to_excel(writer, sheet_name='Data', index=False, header=False, startrow=2)

            workbook = writer.book
            worksheet = writer.sheets['Data']

            # Manually write tag names (column headers) to row 1
            for col_idx, col_name in enumerate(df.columns, start=1):
                cell = worksheet.cell(row=1, column=col_idx, value=col_name)
                cell.font = Font(bold=True)  # Bold the header

            # Write units in row 2 (empty string if not available)
            if tag_info and 'units' in tag_info:
                units = tag_info['units']
                for col_idx, col_name in enumerate(df.columns, start=1):
                    # Extract base tag name: 'Tag1_mean' -> 'Tag1'
                    tag_name = col_name.split('_')[0] if '_' in col_name else col_name
                    unit = units.get(tag_name, '')
                    worksheet.cell(row=2, column=col_idx, value=unit)

            # Freeze top 2 rows (header + units)
            worksheet.freeze_panes = 'A3'

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_len = len(str(cell.value))
                        if cell_len > max_length:
                            max_length = cell_len
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        return True, f"Successfully exported to {filepath}"

    except PermissionError:
        return False, f"Permission denied: {filepath}. Please close the file if it's open."
    except ValueError as e:
        if 'rule' in str(e).lower():
            return False, f"Invalid aggregation interval: {interval}. Use format like '1T' (1 minute), '5S' (5 seconds)."
        return False, f"Error during aggregation: {str(e)}"
    except Exception as e:
        return False, f"Error exporting to Excel: {str(e)}"
