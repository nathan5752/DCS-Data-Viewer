"""
Data management module for loading, saving, and appending time-series data.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from tzlocal import get_localzone
import config


class DataManager:
    """Manages data loading, saving, and appending operations."""

    def __init__(self):
        self.dataframe: Optional[pd.DataFrame] = None
        self.timestamp_column: Optional[str] = None
        self.descriptions: dict = {}  # Store descriptions for each tag: {tag_name: description_string}
        self.units: dict = {}  # Store units for each tag: {tag_name: unit_string}

    def detect_blank_columns(self, filepath: str, tag_row: int) -> Tuple[bool, str, int]:
        """
        Detect blank columns at the left of the Excel file.

        Args:
            filepath: Path to the Excel file
            tag_row: Row number containing tag names (1-indexed)

        Returns:
            Tuple of (success, message, blank_column_count)
        """
        try:
            # Read just the tag row to check for blank columns
            df = pd.read_excel(filepath, header=tag_row - 1, nrows=1)

            # Count blank columns from the left
            blank_count = 0
            for col in df.columns:
                # Check if column name is blank/empty/NaN
                if pd.isna(col) or str(col).strip() == '' or str(col).lower().startswith('unnamed'):
                    blank_count += 1
                else:
                    # Stop at first non-blank column
                    break

            return True, "", blank_count

        except Exception as e:
            return False, f"Error detecting blank columns: {str(e)}", 0

    def load_excel(
        self,
        filepath: str,
        tag_row: int,
        description_row: Optional[int],
        units_row: Optional[int],
        data_start_row: int,
        skip_blank_columns: int = 0
    ) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Load data from an Excel file.

        Args:
            filepath: Path to the Excel file
            tag_row: Row number containing tag names (1-indexed)
            description_row: Row number containing tag descriptions (1-indexed, optional)
            units_row: Row number containing units (1-indexed, optional)
            data_start_row: Row number where data starts (1-indexed)
            skip_blank_columns: Number of blank columns to skip from the left

        Returns:
            Tuple of (success, message, dataframe)
        """
        try:
            # Determine which columns to use (skip blank columns if needed)
            usecols = None
            if skip_blank_columns > 0:
                # Read all columns first to determine total count
                temp_df = pd.read_excel(filepath, header=tag_row - 1, nrows=0)
                total_cols = len(temp_df.columns)
                # Use columns starting from skip_blank_columns onwards
                usecols = list(range(skip_blank_columns, total_cols))

            # Read the Excel file
            # Skip rows before the tag row, then read the tag row as header
            df = pd.read_excel(
                filepath,
                header=tag_row - 1,
                skiprows=range(0, tag_row - 1),
                usecols=usecols
            )

            # Extract description and units rows before dropping them (if they exist between tag_row and data_start_row)
            if data_start_row > tag_row + 1:
                # Extract descriptions (if description_row is provided)
                if description_row is not None:
                    # After reading with header=tag_row-1, df.iloc[0] is the row after the header
                    # So description_row corresponds to df.iloc[description_row - tag_row - 1]
                    description_row_index = description_row - tag_row - 1
                    if 0 <= description_row_index < len(df):
                        description_series = df.iloc[description_row_index]
                        # Store descriptions for each column (tag)
                        self.descriptions = {}
                        for col_name, desc_value in description_series.items():
                            # Convert to string and handle NaN
                            desc_str = str(desc_value) if pd.notna(desc_value) else 'N/A'
                            self.descriptions[col_name] = desc_str
                    else:
                        self.descriptions = {}
                else:
                    # No description row provided
                    self.descriptions = {}

                # Extract units (if units_row is provided)
                if units_row is not None:
                    units_row_index = units_row - tag_row - 1
                    if 0 <= units_row_index < len(df):
                        units_series = df.iloc[units_row_index]
                        # Store units for each column (tag)
                        self.units = {}
                        for col_name, unit_value in units_series.items():
                            # Convert to string and handle NaN
                            unit_str = str(unit_value) if pd.notna(unit_value) else 'N/A'
                            self.units[col_name] = unit_str
                    else:
                        self.units = {}
                else:
                    # No units row provided
                    self.units = {}
            else:
                # No rows between tag and data start
                self.descriptions = {}
                self.units = {}

            # Drop rows before data starts (including units row)
            rows_to_drop = data_start_row - tag_row - 1
            if rows_to_drop > 0:
                df = df.iloc[rows_to_drop:]

            # Reset index
            df = df.reset_index(drop=True)

            # Parse the first column as timestamps
            first_col = df.columns[0]
            # Let pandas auto-detect the timestamp format for maximum compatibility
            df[first_col] = pd.to_datetime(df[first_col], errors='coerce')

            # Remove rows with invalid timestamps
            initial_count = len(df)
            df = df.dropna(subset=[first_col])
            dropped_count = initial_count - len(df)

            if len(df) == 0:
                return False, "No valid timestamp data found in the file.", None

            # Sort by timestamp
            df = df.sort_values(by=first_col)

            # Store timestamp column name
            self.timestamp_column = first_col
            self.dataframe = df

            message = f"Successfully loaded {len(df)} rows from {len(df.columns) - 1} tags."
            if dropped_count > 0:
                message += f" ({dropped_count} rows with invalid timestamps were removed.)"

            return True, message, df

        except FileNotFoundError:
            return False, (
                f"File not found: {filepath}\n\n"
                f"Please check:\n"
                f"• File path is correct\n"
                f"• File has not been moved or deleted\n"
                f"• You have permission to access this location"
            ), None
        except PermissionError:
            return False, (
                f"Permission denied: {filepath}\n\n"
                f"Possible solutions:\n"
                f"• Close the file if it's open in Excel or another program\n"
                f"• Check the file is not read-only\n"
                f"• Ensure you have permission to access this location"
            ), None
        except Exception as e:
            return False, (
                f"Error loading Excel file: {str(e)}\n\n"
                f"Possible causes:\n"
                f"• File may be corrupted or in an unsupported format\n"
                f"• Use 'Check Data Quality' to validate the file first\n"
                f"• Ensure the file is a valid Excel file (.xlsx or .xls)"
            ), None

    def save_session(self, filepath: str) -> Tuple[bool, str]:
        """
        Save the current dataframe to an HDF5 session file.

        Args:
            filepath: Path where the session file should be saved

        Returns:
            Tuple of (success, message)
        """
        if self.dataframe is None:
            return False, "No data to save."

        try:
            self.dataframe.to_hdf(filepath, key=config.HDF5_KEY, mode='w')
            return True, f"Session saved successfully to {filepath}"

        except PermissionError:
            return False, (
                f"Permission denied: {filepath}\n\n"
                f"Possible solutions:\n"
                f"• Close the file if it's open in another program\n"
                f"• Check the file is not read-only\n"
                f"• Ensure you have write permission to this location\n"
                f"• Try saving to a different location"
            )
        except Exception as e:
            return False, (
                f"Error saving session: {str(e)}\n\n"
                f"Possible causes:\n"
                f"• Insufficient disk space\n"
                f"• Invalid file path or filename\n"
                f"• Try saving to a different location"
            )

    def load_session(self, filepath: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Load a dataframe from an HDF5 session file.

        Args:
            filepath: Path to the session file

        Returns:
            Tuple of (success, message, dataframe)
        """
        try:
            df = pd.read_hdf(filepath, key=config.HDF5_KEY)

            # Store timestamp column name (should be the first column)
            self.timestamp_column = df.columns[0]
            self.dataframe = df

            message = f"Successfully loaded session: {len(df)} rows, {len(df.columns) - 1} tags."
            return True, message, df

        except FileNotFoundError:
            return False, (
                f"Session file not found: {filepath}\n\n"
                f"Please check:\n"
                f"• File path is correct\n"
                f"• File has not been moved or deleted\n"
                f"• You have permission to access this location"
            ), None
        except PermissionError:
            return False, (
                f"Permission denied: {filepath}\n\n"
                f"Possible solutions:\n"
                f"• Close the file if it's open in another program\n"
                f"• Check the file is not read-only\n"
                f"• Ensure you have permission to access this location"
            ), None
        except Exception as e:
            return False, (
                f"Error loading session: {str(e)}\n\n"
                f"Possible causes:\n"
                f"• File may be corrupted or incompatible\n"
                f"• Session was created with a different version\n"
                f"• File is not a valid session file (.h5)"
            ), None

    def append_data(
        self,
        new_filepath: str,
        tag_row: int,
        description_row: Optional[int],
        units_row: Optional[int],
        data_start_row: int,
        skip_blank_columns: int = 0
    ) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Append data from a new Excel file to the existing dataframe.
        Checks for duplicate timestamps and requests user confirmation if found.

        Args:
            new_filepath: Path to the Excel file to append
            tag_row: Row number containing tag names (1-indexed)
            description_row: Row number containing tag descriptions (1-indexed, optional)
            units_row: Row number containing units (1-indexed, optional)
            data_start_row: Row number where data starts (1-indexed)
            skip_blank_columns: Number of blank columns to skip from the left

        Returns:
            Tuple of (success, message, dataframe)
            If duplicates detected: (False, "DUPLICATES_DETECTED", metadata_dict)
        """
        if self.dataframe is None:
            return False, "No existing data to append to. Load data first.", None

        # Save the original dataframe BEFORE loading new data
        # (load_excel modifies self.dataframe as a side effect)
        original_df = self.dataframe.copy()
        original_timestamp_column = self.timestamp_column

        # Load the new data using the same method
        success, message, new_df = self.load_excel(
            new_filepath, tag_row, description_row, units_row, data_start_row, skip_blank_columns
        )

        if not success:
            # Restore original dataframe if load failed
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return False, f"Failed to load new data: {message}", None

        try:

            # Check for duplicate timestamps
            existing_timestamps = set(original_df[original_timestamp_column])
            new_timestamps = set(new_df[self.timestamp_column])
            duplicate_timestamps = existing_timestamps.intersection(new_timestamps)

            if len(duplicate_timestamps) > 0:
                # Duplicates detected - restore original dataframe and return metadata
                self.dataframe = original_df
                self.timestamp_column = original_timestamp_column

                metadata = {
                    'duplicate_count': len(duplicate_timestamps),
                    'existing_date_range': (
                        original_df[original_timestamp_column].min(),
                        original_df[original_timestamp_column].max()
                    ),
                    'new_date_range': (
                        new_df[self.timestamp_column].min(),
                        new_df[self.timestamp_column].max()
                    ),
                    'new_filepath': new_filepath,
                    'tag_row': tag_row,
                    'description_row': description_row,
                    'units_row': units_row,
                    'data_start_row': data_start_row,
                    'skip_blank_columns': skip_blank_columns
                }
                return False, "DUPLICATES_DETECTED", metadata

            # No duplicates - restore original dataframe and proceed with append
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return self._perform_append(new_df)

        except Exception as e:
            # Restore original dataframe on error
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return False, f"Error appending data: {str(e)}", None

    def append_data_confirmed(
        self,
        new_filepath: str,
        tag_row: int,
        description_row: Optional[int],
        units_row: Optional[int],
        data_start_row: int,
        skip_blank_columns: int = 0
    ) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Append data without checking for duplicates (user already confirmed).

        Args:
            new_filepath: Path to the Excel file to append
            tag_row: Row number containing tag names (1-indexed)
            description_row: Row number containing tag descriptions (1-indexed, optional)
            units_row: Row number containing units (1-indexed, optional)
            data_start_row: Row number where data starts (1-indexed)
            skip_blank_columns: Number of blank columns to skip from the left

        Returns:
            Tuple of (success, message, dataframe)
        """
        if self.dataframe is None:
            return False, "No existing data to append to. Load data first.", None

        # Save the original dataframe BEFORE loading new data
        original_df = self.dataframe.copy()
        original_timestamp_column = self.timestamp_column

        # Load the new data using the same method
        success, message, new_df = self.load_excel(
            new_filepath, tag_row, description_row, units_row, data_start_row, skip_blank_columns
        )

        if not success:
            # Restore original dataframe if load failed
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return False, f"Failed to load new data: {message}", None

        try:
            # Restore original dataframe before appending
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return self._perform_append(new_df)
        except Exception as e:
            # Restore original dataframe on error
            self.dataframe = original_df
            self.timestamp_column = original_timestamp_column
            return False, f"Error appending data: {str(e)}", None

    def _perform_append(self, new_df: pd.DataFrame) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Internal method to perform the actual append operation.

        Args:
            new_df: The new dataframe to append

        Returns:
            Tuple of (success, message, dataframe)
        """
        # Get the original dataframe
        original_df = self.dataframe

        # Store date range info for message
        original_min = original_df[self.timestamp_column].min()
        original_max = original_df[self.timestamp_column].max()
        new_min = new_df[self.timestamp_column].min()
        new_max = new_df[self.timestamp_column].max()

        # Concatenate the dataframes
        combined_df = pd.concat([original_df, new_df], ignore_index=True)

        # Remove duplicates based on timestamp, keeping the last occurrence
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=[self.timestamp_column],
            keep='last'
        )
        duplicates_removed = initial_count - len(combined_df)

        # Sort by timestamp
        combined_df = combined_df.sort_values(by=self.timestamp_column)
        combined_df = combined_df.reset_index(drop=True)

        self.dataframe = combined_df

        # Build enhanced message with date range information
        message = f"Successfully appended data. Total: {len(combined_df)} rows."
        message += f"\nNew data range: {new_min.strftime('%Y-%m-%d %H:%M:%S')} to {new_max.strftime('%Y-%m-%d %H:%M:%S')}"

        # Check if historical data was added
        if new_min < original_min:
            historical_count = len(new_df[new_df[self.timestamp_column] < original_min])
            message += f"\n({historical_count} rows added before existing data start)"

        if duplicates_removed > 0:
            message += f"\n({duplicates_removed} duplicate timestamps removed - new data kept)"

        return True, message, combined_df

    def get_tag_list(self) -> list:
        """
        Get list of available tags (all columns except timestamp).

        Returns:
            List of tag names
        """
        if self.dataframe is None or self.timestamp_column is None:
            return []

        return [col for col in self.dataframe.columns if col != self.timestamp_column]

    def get_data_for_tag(self, tag_name: str) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """
        Get timestamp and value data for a specific tag.

        Args:
            tag_name: Name of the tag

        Returns:
            Tuple of (timestamps, values) or (None, None) if tag not found
        """
        if self.dataframe is None or tag_name not in self.dataframe.columns:
            return None, None

        timestamps = self.dataframe[self.timestamp_column]
        values = self.dataframe[tag_name]

        return timestamps, values

    def get_unit_for_tag(self, tag_name: str) -> str:
        """
        Get the unit string for a specific tag.

        Args:
            tag_name: Name of the tag

        Returns:
            Unit string, or 'N/A' if not found
        """
        return self.units.get(tag_name, 'N/A')

    def get_description_for_tag(self, tag_name: str) -> str:
        """
        Get the description string for a specific tag.

        Args:
            tag_name: Name of the tag

        Returns:
            Description string, or 'N/A' if not found
        """
        return self.descriptions.get(tag_name, 'N/A')

    def get_data_for_tags_in_range(
        self,
        tag_names: list,
        start_time,
        end_time
    ) -> Optional[pd.DataFrame]:
        """
        Get data for specific tags within time range.

        Args:
            tag_names: List of tag names to include
            start_time: Start datetime
            end_time: End datetime

        Returns:
            DataFrame with timestamp column + selected tag columns,
            filtered to time range. Returns None if no data.
        """
        if self.dataframe is None or self.dataframe.empty:
            return None

        # Select columns (timestamp + requested tags)
        columns = [self.timestamp_column] + [tag for tag in tag_names if tag in self.dataframe.columns]
        if len(columns) == 1:  # Only timestamp, no valid tags
            return None

        df_subset = self.dataframe[columns]  # No copy yet
        timestamp_col = df_subset.columns[0]

        # --- TIMEZONE CONVERSION FIX ---
        # The plot displays times in local timezone, but DataFrame has naive timestamps
        # (which are treated as UTC when plotted). We need to convert local→UTC for comparison.

        try:
            # Get the system's actual local timezone (e.g., 'America/Chicago')
            local_tz = get_localzone()

            # Convert naive local time from plot to timezone-aware UTC
            start_ts_utc = pd.Timestamp(start_time).tz_localize(local_tz).tz_convert('UTC')
            end_ts_utc = pd.Timestamp(end_time).tz_localize(local_tz).tz_convert('UTC')

            # Make a copy and convert DataFrame's naive timestamps to UTC-aware
            df_utc = df_subset.copy()
            df_utc[timestamp_col] = df_utc[timestamp_col].dt.tz_localize('UTC')

            # Both sides are now UTC-aware - comparison will work correctly
            mask = (df_utc[timestamp_col] >= start_ts_utc) & (df_utc[timestamp_col] <= end_ts_utc)
            df_filtered = df_utc.loc[mask]

            # Convert UTC back to local timezone, THEN strip timezone info
            if not df_filtered.empty:
                df_filtered = df_filtered.copy()
                # KEY FIX: tz_convert() to local first, then tz_localize(None)
                df_filtered[timestamp_col] = df_filtered[timestamp_col].dt.tz_convert(local_tz).dt.tz_localize(None)

            return df_filtered if not df_filtered.empty else None

        except Exception as e:
            # Prevent crashes on timezone errors
            print(f"Error during timezone conversion: {e}")
            return None

    def get_full_data_for_tags(self, tag_names: list) -> Optional[pd.DataFrame]:
        """
        Get full dataset for specific tags (no time filtering).

        Args:
            tag_names: List of tag names to include

        Returns:
            DataFrame with timestamp column + selected tag columns.
            Returns None if no data.
        """
        if self.dataframe is None or self.dataframe.empty:
            return None

        columns = [self.timestamp_column] + [tag for tag in tag_names if tag in self.dataframe.columns]
        if len(columns) == 1:
            return None

        return self.dataframe[columns].copy()

    def reset_session(self):
        """
        Reset all session data, clearing the dataframe and metadata.
        This returns the DataManager to its initial state.
        """
        self.dataframe = None
        self.timestamp_column = None
        self.descriptions = {}
        self.units = {}

    def has_data(self) -> bool:
        """
        Check if data is currently loaded.

        Returns:
            True if data is loaded, False otherwise
        """
        return self.dataframe is not None
