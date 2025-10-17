# DCS Data Viewer

A desktop application for visualizing time-series data from industrial systems like PLCs or DCSs.

## Features

- **Excel Data Loading**: Import data with configurable row specifications
- **HDF5 Session Management**: Save/load sessions for fast access (10-100x faster than Excel)
- **Multi-Axis Plotting**: Automatic scale detection creates secondary Y-axes when needed
- **Interactive Tools**: Crosshair, tooltips, line highlighting, pan & zoom
- **Performance**: Handles 600,000+ data points per tag without lag
- **Data Appending**: Combine multiple files with automatic duplicate removal
- **PNG Export**: Export plots for reports and documentation
- **Y-Axis Lock**: Prevent accidental zooming while inspecting data

## Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Quick Start

1. Click **"Quick Start Guide"** button in the app for help
2. **Load Data**: Click "Load New Data" and select your Excel file
3. **Select Tags**: Check tags from the list to plot them
4. **Interact**: Left-click to pan, scroll wheel to zoom
5. **Save Session**: Save to .h5 format for instant loading later

## Excel File Format

```
Row 1: [Time]      [Tag1]    [Tag2]    [Tag3] ...
Row 2: [datetime]  [Desc1]   [Desc2]   [Desc3] ...
Row 3: [datetime]  [unit1]   [unit2]   [unit3] ...
Row 4: [timestamp] [value1]  [value2]  [value3] ...
...
```

**Default Settings**: Tag Row=1, Description Row=2, Units Row=3, Data Start=4

## Building & Testing

### Generate Test Data

```bash
# Generate test data (360 points, 1 hour)
python scripts/generate_quick_test.py
```

### Building Standalone Executable

**Prerequisites:**
- Python 3.8 or higher installed
- All project dependencies installed (`pip install -r requirements.txt`)
- PyInstaller installed (`pip install pyinstaller`)

**Build Steps:**

```bash
# 1. Install PyInstaller (if not already installed)
pip install pyinstaller

# 2. Build the executable using the spec file
pyinstaller dcs_data_viewer.spec

# 3. The executable will be in the dist/ directory
# Look for: dist/DCS_Data_Viewer.exe
```

**Expected Output:**
- **Location:** `dist/DCS_Data_Viewer.exe`
- **Size:** Approximately 68-100 MB (includes Python runtime and all dependencies)
- **Type:** Single-file executable (no console window)

**Testing the Executable:**

1. Navigate to the `dist` folder
2. Double-click `DCS_Data_Viewer.exe` to launch
3. Test basic functionality:
   - Click "Quick Start Guide" to see help
   - Load the test data file (`test_data.xlsx`)
   - Check/uncheck tags to verify plotting
   - Test pan/zoom controls
   - Try saving/loading a session

**Distribution:**
- The `.exe` file is self-contained and can be distributed standalone
- No Python installation required on the target machine
- Recommend testing on a clean Windows machine without Python installed

**Troubleshooting:**
- If build fails, ensure all dependencies are installed: `pip install -r requirements.txt`
- If executable crashes, check Windows Defender or antivirus isn't blocking it
- For "DLL load failed" errors, try rebuilding with `--clean` flag: `pyinstaller --clean dcs_data_viewer.spec`

## Architecture

```
ui/          - User interface (main_window, control_panel, tag_list, help_dialog)
data/        - Data management (Excel/HDF5 loading, saving, appending)
plotting/    - PyQtGraph plotting with multi-axis intelligence
utils/       - File dialogs and validation
config.py    - All constants and styling
```

---

**Version**: 1.0.0 | **License**: Provided as-is for industrial data visualization
