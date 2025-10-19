"""Generate test data without duplicate timestamps for testing append functionality."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate data that comes AFTER the existing test data
# Existing data: Jan 1, 2025 12:00:00 to 13:00:00 (360 points, ends at 12:59:50)
# This file: Jan 1, 2025 13:00:00 to 13:30:00 (180 points) - no duplicates
num_points = 180  # 30 minutes of new data
base_time = datetime(2025, 1, 1, 12, 0, 0)
start_time = base_time + timedelta(hours=1)  # Start at 13:00:00
timestamps = [start_time + timedelta(seconds=i*10) for i in range(num_points)]

# Create data dictionary
data = {"Timestamp": timestamps}

# Same 5 tags
tags = [
    {"name": "PIT-0721", "description": "Reactor Pressure", "unit": "bar(a)",
     "values": 5.5 + 2.2 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.12, num_points)},
    {"name": "TIT-0534", "description": "Feed Temperature", "unit": "°C",
     "values": 62 + 21 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.55, num_points)},
    {"name": "FIT-0892", "description": "Product Flow Rate", "unit": "m³/h",
     "values": 510 + 205 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 5.5, num_points)},
    {"name": "LIT-1205", "description": "Tank Level", "unit": "mm",
     "values": 1550 + 510 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 11, num_points)},
    {"name": "AIT-0445", "description": "Valve Position", "unit": "mA",
     "values": 12.5 + 4.1 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.055, num_points)},
]

for tag in tags:
    data[tag["name"]] = tag["values"]

# Create DataFrame
df = pd.DataFrame(data)

# Create Excel file
with pd.ExcelWriter("test_data_append_no_duplicate.xlsx", engine='openpyxl') as writer:
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

print("Test append data without duplicates generated: test_data_append_no_duplicate.xlsx")
print(f"  - 180 data points (30 minutes at 10-second intervals)")
print(f"  - Starts after existing data (no duplicate timestamps)")
print(f"  - Same 5 tags")
print(f"  - Tag Row: 1, Description Row: 2, Units Row: 3, Data Start Row: 4")
print("\nThis file can be used to test appending without duplicate detection.")
