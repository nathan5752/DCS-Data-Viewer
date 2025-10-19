"""
Generate a sample CSV file for testing the csv_to_excel.py converter.

Creates a realistic industrial time-series dataset with:
- Timestamps (1-minute intervals)
- Temperature readings
- Pressure readings
- Flow rate
- Tank level

Usage:
    python scripts/generate_sample_csv.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sample_csv():
    """Generate sample CSV file with industrial time-series data."""

    # Generate timestamps (100 rows at 1-minute intervals)
    start_time = datetime(2025, 10, 19, 8, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(100)]

    # Generate realistic industrial data with some variation and trends
    np.random.seed(42)  # For reproducibility

    # Reactor Temperature (°C) - oscillating around 85°C
    temp_reactor = 85 + 3 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 0.5, 100)

    # Feed Temperature (°C) - steady around 25°C
    temp_feed = 25 + np.random.normal(0, 0.8, 100)

    # Reactor Pressure (bar) - slowly increasing
    pressure_reactor = 10.5 + np.linspace(0, 1.5, 100) + np.random.normal(0, 0.1, 100)

    # Feed Pressure (bar) - steady
    pressure_feed = 15.2 + np.random.normal(0, 0.2, 100)

    # Flow Rate (L/min) - with step change at halfway point
    flow_rate = np.concatenate([
        np.ones(50) * 120 + np.random.normal(0, 2, 50),
        np.ones(50) * 150 + np.random.normal(0, 2, 50)
    ])

    # Tank Level (%) - gradually draining
    tank_level = 95 - np.linspace(0, 30, 100) + np.random.normal(0, 1, 100)

    # Create DataFrame
    data = {
        'Timestamp': timestamps,
        'TT-101_ReactorTemp': np.round(temp_reactor, 2),
        'TT-102_FeedTemp': np.round(temp_feed, 2),
        'PT-201_ReactorPressure': np.round(pressure_reactor, 2),
        'PT-202_FeedPressure': np.round(pressure_feed, 2),
        'FT-301_FeedFlowRate': np.round(flow_rate, 2),
        'LT-401_TankLevel': np.round(tank_level, 2)
    }

    df = pd.DataFrame(data)

    # Save to CSV
    output_file = 'sample_industrial_data.csv'
    df.to_csv(output_file, index=False)

    print(f"Sample CSV file created: {output_file}")
    print(f"\nFile contains:")
    print(f"  - {len(df)} rows (timestamped data)")
    print(f"  - {len(df.columns)} columns (1 timestamp + 6 tags)")
    print(f"  - Time range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    print(f"\nTags included:")
    for col in df.columns[1:]:  # Skip timestamp column
        print(f"  • {col}")

    print(f"\nTo convert to Excel format:")
    print(f"  python scripts/csv_to_excel.py {output_file} sample_industrial_data.xlsx")

    return df


if __name__ == '__main__':
    generate_sample_csv()
