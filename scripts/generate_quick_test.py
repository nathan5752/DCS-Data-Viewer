"""Quick test data generator with smaller dataset."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate just 1 hour of data at 10 second intervals (360 points)
num_points = 360
start_time = datetime.now() - timedelta(hours=1)
timestamps = [start_time + timedelta(seconds=i*10) for i in range(num_points)]

# Create data dictionary
data = {"Timestamp": timestamps}

# 5 tags with different value ranges
tags = [
    {"name": "PIT-0721", "description": "Reactor Pressure", "unit": "bar(a)", "values": 5 + 2 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.1, num_points)},
    {"name": "TIT-0534", "description": "Feed Temperature", "unit": "°C", "values": 60 + 20 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.5, num_points)},
    {"name": "FIT-0892", "description": "Product Flow Rate", "unit": "m³/h", "values": 500 + 200 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 5, num_points)},
    {"name": "LIT-1205", "description": "Tank Level", "unit": "mm", "values": 1500 + 500 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 10, num_points)},
    {"name": "AIT-0445", "description": "Valve Position", "unit": "mA", "values": 12 + 4 * np.sin(np.linspace(0, 4*np.pi, num_points)) + np.random.normal(0, 0.05, num_points)},
]

for tag in tags:
    data[tag["name"]] = tag["values"]

# Create DataFrame
df = pd.DataFrame(data)

# Create Excel file
with pd.ExcelWriter("test_data.xlsx", engine='openpyxl') as writer:
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

print("Quick test data generated: test_data.xlsx")
print(f"  - 360 data points (1 hour at 10-second intervals)")
print(f"  - 5 tags with different value ranges")
print(f"  - Tag Row: 1, Description Row: 2, Units Row: 3, Data Start Row: 4")
