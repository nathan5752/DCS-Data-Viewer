"""Generate test data with duplicate timestamps for testing append functionality."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate data that overlaps with the second half of the existing test data
# Existing data: Jan 1, 2025 12:00:00 to 13:00:00 (360 points)
# This file: Jan 1, 2025 12:30:00 to 13:30:00 (360 points) - 180 duplicates
num_points = 360  # 1 hour total
base_time = datetime(2025, 1, 1, 12, 0, 0)
start_time = base_time + timedelta(minutes=30)  # Start at 12:30
timestamps = [start_time + timedelta(seconds=i*10) for i in range(num_points)]

# Create data dictionary
data = {"Timestamp": timestamps}

# Same 5 tags but with slightly different values (to show that new data overwrites)
tags = [
    {"name": "PIT-0721", "description": "Reactor Pressure", "unit": "bar(a)",
     "values": 6 + 2.5 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.15, num_points)},
    {"name": "TIT-0534", "description": "Feed Temperature", "unit": "°C",
     "values": 65 + 22 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.6, num_points)},
    {"name": "FIT-0892", "description": "Product Flow Rate", "unit": "m³/h",
     "values": 520 + 210 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 6, num_points)},
    {"name": "LIT-1205", "description": "Tank Level", "unit": "mm",
     "values": 1600 + 520 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 12, num_points)},
    {"name": "AIT-0445", "description": "Valve Position", "unit": "mA",
     "values": 13 + 4.2 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.06, num_points)},
]

for tag in tags:
    data[tag["name"]] = tag["values"]

# Create DataFrame
df = pd.DataFrame(data)

# Create Excel file
with pd.ExcelWriter("test_data_append_duplicate.xlsx", engine='openpyxl') as writer:
    # Write data starting at row 4 (0-indexed row 3), without headers
    df.to_excel(writer, index=False, header=False, startrow=3)
    worksheet = writer.sheets['Sheet1']

    # Write tag names (row 1)
    worksheet['A1'] = 'Instrument Tag'
    for idx, tag in enumerate(tags, start=2):
        worksheet.cell(row=1, column=idx, value=tag["name"])

    # Write descriptions (row 2)
    worksheet['A2'] = 'Description'
    for idx, tag in enumerate(tags, start=2):
        worksheet.cell(row=2, column=idx, value=tag["description"])

    # Write units (row 3)
    worksheet['A3'] = 'Units'
    for idx, tag in enumerate(tags, start=2):
        worksheet.cell(row=3, column=idx, value=tag["unit"])

print("Test append data with duplicates generated: test_data_append_duplicate.xlsx")
print(f"  - 360 data points (1 hour at 10-second intervals)")
print(f"  - Starts 30 minutes ago (overlapping with ~180 timestamps from existing data)")
print(f"  - Same 5 tags with slightly different values")
print(f"  - Tag Row: 1, Description Row: 2, Units Row: 3, Data Start Row: 4")
print("\nThis file can be used to test duplicate timestamp detection when appending.")
