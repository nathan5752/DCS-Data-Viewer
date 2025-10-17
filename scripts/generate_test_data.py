"""
Test data generator for creating sample Excel files with time-series data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_test_data(
    output_file: str = "test_data.xlsx",
    num_days: int = 7,
    sample_rate_seconds: int = 1,
    num_tags: int = 5
):
    """
    Generate a test Excel file with synthetic time-series data.

    Args:
        output_file: Output filename
        num_days: Number of days of data to generate
        sample_rate_seconds: Sampling interval in seconds
        num_tags: Number of instrument tags to generate
    """
    # Calculate number of data points
    num_points = num_days * 24 * 3600 // sample_rate_seconds

    print(f"Generating {num_points:,} data points for {num_tags} tags...")

    # Generate timestamps
    start_time = datetime.now() - timedelta(days=num_days)
    timestamps = [start_time + timedelta(seconds=i*sample_rate_seconds) for i in range(num_points)]

    # Define different tag configurations with different value ranges
    tag_configs = [
        {"name": "PIT-0721", "description": "Reactor Pressure", "unit": "bar(a)", "min": 0, "max": 10, "noise": 0.1, "trend": 0.0001},
        {"name": "TIT-0534", "description": "Feed Temperature", "unit": "°C", "min": 20, "max": 100, "noise": 0.5, "trend": 0.0005},
        {"name": "FIT-0892", "description": "Product Flow Rate", "unit": "m³/h", "min": 0, "max": 1000, "noise": 5, "trend": 0.001},
        {"name": "LIT-1205", "description": "Tank Level", "unit": "mm", "min": 500, "max": 3000, "noise": 10, "trend": 0.002},
        {"name": "AIT-0445", "description": "Valve Position", "unit": "mA", "min": 4, "max": 20, "noise": 0.05, "trend": 0.0001},
        {"name": "PDIT-0893", "description": "Differential Pressure", "unit": "kPa", "min": 0, "max": 500, "noise": 2, "trend": 0.0008},
        {"name": "TIT-0721", "description": "Outlet Temperature", "unit": "°F", "min": 70, "max": 250, "noise": 1, "trend": 0.0003},
        {"name": "FIT-1156", "description": "Cooling Water Flow", "unit": "L/min", "min": 0, "max": 100, "noise": 0.5, "trend": 0.0002},
    ]

    # Use only the requested number of tags
    tag_configs = tag_configs[:num_tags]

    # Create data dictionary
    data = {"Timestamp": timestamps}

    # Generate data for each tag
    for config in tag_configs:
        # Generate base sinusoidal pattern
        t = np.arange(num_points)
        base_value = (config["max"] + config["min"]) / 2
        amplitude = (config["max"] - config["min"]) / 3

        # Sinusoidal variation + linear trend + random noise
        values = (
            base_value +
            amplitude * np.sin(2 * np.pi * t / (24 * 3600 / sample_rate_seconds)) +  # Daily cycle
            config["trend"] * t +  # Slow trend
            np.random.normal(0, config["noise"], num_points)  # Random noise
        )

        # Clip to min/max
        values = np.clip(values, config["min"], config["max"])

        data[config["name"]] = values

    # Create DataFrame
    df = pd.DataFrame(data)

    # Create Excel file with proper header structure
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Write data starting at row 4 (0-indexed row 3), without headers
        df.to_excel(writer, index=False, header=False, startrow=3)

        # Get the worksheet
        worksheet = writer.sheets['Sheet1']

        # Write tag names (row 1)
        worksheet['A1'] = 'Instrument Tag'
        for idx, config in enumerate(tag_configs, start=2):
            worksheet.cell(row=1, column=idx, value=config["name"])

        # Write descriptions (row 2)
        worksheet['A2'] = 'Description'
        for idx, config in enumerate(tag_configs, start=2):
            worksheet.cell(row=2, column=idx, value=config["description"])

        # Write units (row 3)
        worksheet['A3'] = 'Units'
        for idx, config in enumerate(tag_configs, start=2):
            worksheet.cell(row=3, column=idx, value=config["unit"])

    print(f"Test data generated successfully: {output_file}")
    print(f"Configuration:")
    print(f"  - Tag Row: 1")
    print(f"  - Description Row: 2")
    print(f"  - Units Row: 3")
    print(f"  - Data Start Row: 4")
    print(f"  - Total Rows: {num_points + 3}")
    print(f"  - Tags: {', '.join([c['name'] for c in tag_configs])}")


def generate_append_data(
    output_file: str = "append_data.xlsx",
    num_days: int = 2,
    sample_rate_seconds: int = 1,
    num_tags: int = 5
):
    """
    Generate additional test data for appending.

    Args:
        output_file: Output filename
        num_days: Number of days of data to generate
        sample_rate_seconds: Sampling interval in seconds
        num_tags: Number of instrument tags to generate
    """
    # Start from current time to simulate new data
    generate_test_data(output_file, num_days, sample_rate_seconds, num_tags)
    print(f"\nAppend data generated: {output_file}")


if __name__ == '__main__':
    # Generate main test file (7 days of data at 1Hz)
    print("=" * 60)
    print("Generating main test data file...")
    print("=" * 60)
    generate_test_data("test_data.xlsx", num_days=7, sample_rate_seconds=1, num_tags=5)

    print("\n" + "=" * 60)
    print("Generating append test data file...")
    print("=" * 60)
    generate_append_data("append_data.xlsx", num_days=2, sample_rate_seconds=1, num_tags=5)

    print("\n" + "=" * 60)
    print("Test data generation complete!")
    print("=" * 60)
