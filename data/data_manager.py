"""
Data management module for loading, saving, and appending time-series data.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
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
            # FIX: Add format to speed up parsing and resolve the UserWarning
            df[first_col] = pd.to_datetime(df[first_col], errors='coerce', format='ISO8601')

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
            return False, f"File not found: {filepath}", None
        except PermissionError:
            return False, f"Permission denied: {filepath}", None
        except Exception as e:
            return False, f"Error loading Excel file: {str(e)}", None

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
            return False, f"Permission denied: {filepath}"
        except Exception as e:
            return False, f"Error saving session: {str(e)}"

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
            return False, f"File not found: {filepath}", None
        except PermissionError:
            return False, f"Permission denied: {filepath}", None
        except Exception as e:
            return False, f"Error loading session: {str(e)}", None

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

        # Load the new data using the same method
        success, message, new_df = self.load_excel(
            new_filepath, tag_row, description_row, units_row, data_start_row, skip_blank_columns
        )

        if not success:
            return False, f"Failed to load new data: {message}", None

        try:
            # Get the original dataframe
            original_df = self.dataframe

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

            message = f"Successfully appended data. Total: {len(combined_df)} rows."
            if duplicates_removed > 0:
                message += f" ({duplicates_removed} duplicate timestamps removed.)"

            return True, message, combined_df

        except Exception as e:
            return False, f"Error appending data: {str(e)}", None

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
