"""
CSV to Excel Converter for DCS Data Viewer

Converts CSV files to the Excel format required by DCS Data Viewer.

Output Format:
  Row 1: Tag names (column headers from CSV)
  Row 2: Descriptions (derived from tag names)
  Row 3: Units (empty)
  Row 4+: Data rows

Usage:
  python scripts/csv_to_excel.py input.csv output.xlsx
  python scripts/csv_to_excel.py input.csv output.xlsx --force  # Overwrite without asking
  python scripts/csv_to_excel.py --help                         # Show this help
"""

import sys
import argparse
from pathlib import Path
import pandas as pd


def confirm_overwrite(filepath):
    """
    Ask user for confirmation before overwriting an existing file.

    Args:
        filepath: Path to the file to check

    Returns:
        True if user confirms or file doesn't exist, False otherwise
    """
    if not Path(filepath).exists():
        return True

    while True:
        response = input(f"Warning: '{filepath}' already exists. Overwrite? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("Please answer 'y' or 'n'")


def convert_csv_to_excel(csv_path, excel_path, force=False):
    """
    Convert CSV file to DCS Data Viewer Excel format.

    Args:
        csv_path: Path to input CSV file
        excel_path: Path to output Excel file
        force: If True, overwrite without asking

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if input file exists
        if not Path(csv_path).exists():
            print(f"Error: Input file '{csv_path}' not found.")
            return False

        # Check for overwrite unless force is enabled
        if not force and not confirm_overwrite(excel_path):
            print("Conversion cancelled.")
            return False

        # Read CSV file
        print(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)

        # Validate data
        if df.empty:
            print("Error: CSV file is empty.")
            return False

        if len(df.columns) < 2:
            print("Error: CSV must have at least 2 columns (timestamp + at least one tag).")
            return False

        print(f"Found {len(df.columns)} columns and {len(df)} rows")

        # Create Excel file with DCS Data Viewer format
        print(f"Creating Excel file: {excel_path}")

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Prepare data structure
            # Row 1: Tag names (column headers)
            tag_names = list(df.columns)

            # Row 2: Descriptions (same as tag names for simplicity)
            descriptions = [f"{tag} (from CSV)" for tag in tag_names]

            # Row 3: Units (empty)
            units = ['datetime' if i == 0 else '' for i in range(len(tag_names))]

            # Combine metadata rows with data
            metadata_df = pd.DataFrame([
                tag_names,      # Row 1: Tags
                descriptions,   # Row 2: Descriptions
                units           # Row 3: Units
            ])

            # Write metadata rows (rows 1-3)
            metadata_df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)

            # Write data rows (starting at row 4)
            df.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=3)

        print("\nConversion successful!")
        print(f"\nLoad into DCS Data Viewer with these parameters:")
        print(f"  Tag Row: 1")
        print(f"  Description Row: 2 (enabled)")
        print(f"  Units Row: 3 (enabled)")
        print(f"  Data Start Row: 4")
        print(f"\nNote: First column should be timestamps in datetime format.")
        print(f"      If conversion failed, ensure your CSV has proper datetime values in column 1.")

        return True

    except pd.errors.EmptyDataError:
        print(f"Error: CSV file '{csv_path}' is empty or invalid.")
        return False
    except pd.errors.ParserError as e:
        print(f"Error: Failed to parse CSV file: {e}")
        return False
    except PermissionError:
        print(f"Error: Permission denied. Cannot write to '{excel_path}'.")
        print("      Make sure the file is not open in Excel.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main entry point for the CSV to Excel converter."""
    parser = argparse.ArgumentParser(
        description='Convert CSV files to Excel format for DCS Data Viewer',
        epilog="""
Examples:
  python scripts/csv_to_excel.py data.csv output.xlsx
  python scripts/csv_to_excel.py data.csv output.xlsx --force

CSV Requirements:
  • First column must be timestamps (datetime format)
  • Subsequent columns are tag values
  • File must have headers in first row
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'input_csv',
        help='Path to input CSV file'
    )

    parser.add_argument(
        'output_excel',
        help='Path to output Excel file (*.xlsx)'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite output file without asking for confirmation'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0'
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate output file extension
    if not args.output_excel.lower().endswith('.xlsx'):
        print("Warning: Output file should have .xlsx extension")
        print(f"         Adding .xlsx to filename")
        args.output_excel += '.xlsx'

    # Perform conversion
    success = convert_csv_to_excel(args.input_csv, args.output_excel, args.force)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
