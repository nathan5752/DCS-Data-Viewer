# Application Icon

This folder contains the application icon used by DCS Data Viewer.

## Icon File Requirements

### For Windows (.ico format)

The application expects an icon file named `app_icon.ico` in this directory.

**File specifications:**
- **Format**: Windows Icon (.ico)
- **Recommended sizes**: The .ico file should contain multiple resolutions embedded:
  - 16x16 pixels (small icons, taskbar)
  - 32x32 pixels (standard window icons)
  - 48x48 pixels (large icons)
  - 256x256 pixels (high-resolution displays)

### Creating an Icon File

You can create a .ico file from an image using:

1. **Online tools**:
   - [ConvertICO](https://convertico.com/)
   - [ICO Convert](https://icoconvert.com/)

2. **Desktop software**:
   - GIMP (free): Export as .ico with multiple sizes
   - IrfanView (free): Save as .ico
   - Adobe Photoshop: Use ICO plugin

3. **Command line** (ImageMagick):
   ```bash
   magick convert icon.png -define icon:auto-resize=256,48,32,16 app_icon.ico
   ```

## Usage

Once you place `app_icon.ico` in this folder:

1. **For the application window**: The icon will automatically appear in the window's title bar when you run `python main.py`

2. **For the executable**: When you build the application with PyInstaller:
   ```bash
   pyinstaller dcs_data_viewer.spec
   ```
   The icon will be embedded in the .exe file and appear:
   - On the executable file in Windows Explorer
   - In the taskbar when the application runs
   - In the window title bar

## Design Recommendations

For best results:
- Use a simple, recognizable design that works at small sizes (16x16)
- Avoid fine details that won't be visible at small resolutions
- Use high contrast for visibility
- Consider the application's purpose (data visualization/industrial monitoring)
- Suggested themes: graphs, charts, data plots, industrial gauges

## License Note

Make sure you have the rights to use any icon you add to this folder. Consider using:
- Icons you create yourself
- Public domain icons
- Icons from services like [Flaticon](https://www.flaticon.com/) or [Icons8](https://icons8.com/) (check license terms)
