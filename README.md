# WxAlert
A simple, fullscreen severe weather alert system for Australia that runs silently in the background.

![WxAlert Screenshot](screenshot.png)
---

## What is WxAlert?
WxAlert is a lightweight application that monitors the Australian Bureau of Meteorology (BoM) for severe weather warnings. When a warning is issued for your specific town or city, the program displays an unmissable, color-coded fullscreen alert to grab your attention.

It was built to be a simple, no-frills, and highly effective way to be notified of dangerous weather conditions without needing to constantly check a website.

## Features
- **Location-Specific:** On first run, you set your state and nearest town. The app will only alert you if your town is mentioned in a warning.
- **Background Monitoring:** The app runs silently as a background process, checking for new warnings every 5 minutes.
- **Unmissable Alerts:** Warnings are displayed fullscreen with color-coding for severity.
- **Free and Open-Source:** Built with community safety in mind, with no ads, tracking, or cost.

## Installation
You can download the latest version from the **[Releases Page](https://github.com/UniversialScienceGrid/WxAlert/releases)**. 

#### For Windows (Ready for Download)
1. Download the `WxAlert.exe` file.
2. Your browser or Windows Defender might show a security warning. This is a false positive because the app is new and not signed. Choose **"Keep"** and then on the Windows warning, click **"More info" -> "Run anyway"**.
3. Double-click `WxAlert.exe` to run the first-time setup.
4. After setup, the program will start running silently in the background.
5. **(Optional)** To have it start automatically, you can place a shortcut to the `.exe` inside your Startup folder.

#### For macOS (Help Needed!)
An official `.app` file is not yet available as I do not have access to a Mac to build it. There are two options for Mac users:

**Option 1 (Easiest): Run the Python Script Directly**
1.  Download and install the latest version of Python from [python.org](https://www.python.org).
2.  Download the `WxAlert.py` script from this repository.
3.  Open the **Terminal** app.
4.  Navigate to the folder where you saved the script (e.g., `cd Downloads`).
5.  Run the program with the command: `python3 WxAlert.py`
6.  The first-time setup will appear. After setup, you will need to leave the Terminal window open for the program to keep monitoring for warnings.

**Option 2 (For Developers): Help Build the `.app` File!**
If you have a Mac and would like to help the community, you can build the `.app` file yourself. See the "Help Wanted" section below.

## Help Wanted: macOS Builder
I am looking for a volunteer with a Mac to help build the `WxAlert.app` file for the community. The process only takes a few minutes:
1.  **Install Python** from [python.org](https://www.python.org).
2.  **Install PyInstaller** by opening the Terminal and running: `pip3 install pyinstaller`
3.  **Navigate** to the folder with the `WxAlert.py` script in your Terminal.
4.  **Run the build command:** `pyinstaller --onefile --windowed -n WxAlert WxAlert.py`
5.  The finished `WxAlert.app` will be inside the new `dist` folder.

If you successfully build the app, please get in touch or open an issue on this GitHub repository. I will add the file to the main releases page and give you full credit for your contribution!

## License
This project is licensed under the **MIT License**. See the `LICENSE` file for details. This means you are free to use, modify, and distribute this software. However, it is provided "AS IS" without any warranty.

## Disclaimer
WxAlert is a community-driven hobby project and is **not an official emergency service**. It relies on publicly available data which may have delays or inaccuracies. Always prioritize official advice from the **Bureau of Meteorology** and local emergency services for your safety. Do not rely solely on this application for life-and-death decisions.

## Acknowledgements
This project is powered by the publicly available data feeds from the [Australian Bureau of Meteorology (BoM)](http://www.bom.gov.au/).
