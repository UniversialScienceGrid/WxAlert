import tkinter as tk
from tkinter import simpledialog, messagebox
import ftplib
import socket
import json
import time
import os
import sys
from io import BytesIO
import xml.etree.ElementTree as ET

# --- LOCATION DATABASE (Now simplified to be State-based) ---
# This dictionary maps a State to its main severe weather warning file.
STATE_MAP = {
    "Queensland": "IDQ21037.xml",
    "New South Wales": "IDN21037.xml",
    "Victoria": "IDV21033.xml",
    "South Australia": "IDS21037.xml",
    "Western Australia": "IDW21037.xml",
    "Tasmania": "IDT21037.xml",
    "Northern Territory": "IDD21037.xml",
    "Australian Capital Territory": "IDN21037.xml" # ACT warnings are in the NSW file
}

CONFIG_FILE = "config.json"

# --- Severity mapping and the WeatherAlertApp class are the same ---
SEVERITY_LEVELS = {
    "All Clear": {"color": "green", "icon": "✅"}, "Minor": {"color": "gold", "icon": "⚠️"},
    "Major": {"color": "red", "icon": "❗"}, "Deadly": {"color": "black", "text_color": "white", "icon": "☠️"},
    "Default": {"color": "darkorange", "icon": "📢"}
}

def determine_severity(warning_title):
    # (This function is unchanged)
    title_lower = warning_title.lower()
    if "cancellation" in title_lower: return "All Clear"
    if "tornado" in title_lower or "destructive" in title_lower: return "Deadly"
    if "severe" in title_lower or "fire" in title_lower: return "Major"
    if "strong wind" in title_lower or "hazardous surf" in title_lower: return "Minor"
    return "Default"

class WeatherAlertApp:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()

    def display_alert(self, alert_data):
        # (This class is unchanged)
        severity_name = determine_severity(alert_data["title"])
        config = SEVERITY_LEVELS.get(severity_name, SEVERITY_LEVELS["Default"])
        if severity_name == "All Clear": return # Don't pop up for cancellations

        alert_window = tk.Toplevel(self.master)
        alert_window.attributes('-fullscreen', True)
        alert_window.configure(bg=config["color"])
        center_frame = tk.Frame(alert_window, bg=config["color"])
        center_frame.pack(expand=True)
        icon_label = tk.Label(center_frame, text=config["icon"], font=("Arial", 60), bg=config["color"], fg=config.get("text_color", "black"))
        icon_label.pack(pady=20)
        title_label = tk.Label(center_frame, text=alert_data["title"], font=("Arial", 30, "bold"), wraplength=alert_window.winfo_screenwidth() - 100, bg=config["color"], fg=config.get("text_color", "black"))
        title_label.pack(pady=10)
        message_label = tk.Label(center_frame, text=alert_data["message"], font=("Arial", 18), wraplength=alert_window.winfo_screenwidth() - 100, bg=config["color"], fg=config.get("text_color", "black"))
        message_label.pack(pady=5)
        resume_label = tk.Label(center_frame, text="\nPress any key to close this alert.", font=("Arial", 16), bg=config["color"], fg=config.get("text_color", "black"))
        resume_label.pack(pady=20)
        alert_window.bind('<Key>', lambda e: alert_window.destroy())
        alert_window.focus_set()
        self.master.wait_window(alert_window)

# --- Upgraded Configuration Functions ---
def load_config():
    """Tries to load the configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_config(data):
    """Saves the given data to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def run_first_time_setup():
    """Displays dialog boxes for the user to select their State and Town."""
    root = tk.Tk()
    root.withdraw()

    # --- Step 1: Get the State ---
    state_options = "\n".join(STATE_MAP.keys())
    state_prompt = f"Welcome to WxAlert!\n\nPlease select your State by typing its name exactly as shown below:\n\n{state_options}"
    user_state = ""
    while user_state not in STATE_MAP:
        user_state = simpledialog.askstring("WxAlert Setup (1/2) - State", state_prompt)
        if user_state is None:
            messagebox.showerror("Setup Cancelled", "WxAlert cannot run without a location. The program will now exit.")
            return None
        if user_state not in STATE_MAP:
            messagebox.showwarning("Invalid State", f"'{user_state}' is not a valid location. Please try again.")

    # --- Step 2: Get the Town ---
    town_prompt = "Now, please enter the name of your nearest Town or City.\n\n(e.g., Toowoomba, Cairns, Ipswich, etc.)"
    user_town = ""
    while not user_town:
        user_town = simpledialog.askstring("WxAlert Setup (2/2) - Town/City", town_prompt)
        if user_town is None:
            messagebox.showerror("Setup Cancelled", "WxAlert cannot run without a location. The program will now exit.")
            return None
        if not user_town.strip():
            messagebox.showwarning("Invalid Town", "Town/City name cannot be blank.")
            user_town = "" # Reset to re-trigger the loop

    # --- Step 3: Save the configuration ---
    config_data = {
        "state": user_state,
        "town": user_town.strip(),
        "warning_file": STATE_MAP[user_state]
    }
    save_config(config_data)
    
    messagebox.showinfo("Setup Complete", f"WxAlert is now configured for '{user_town}, {user_state}'.\n\nThe program will now run silently in the background.")
    return config_data

# --- Modified Core Functions ---
def fetch_and_parse_warning(config):
    """Connects to the BoM FTP and checks the state-wide file for the user's town."""
    try:
        ftp = ftplib.FTP("ftp.bom.gov.au", timeout=20)
        ftp.login()
        ftp.cwd("/anon/gen/fwo/")
        
        flo = BytesIO()
        ftp.retrbinary(f"RETR {config['warning_file']}", flo.write)
        ftp.quit()
        flo.seek(0)
        
        tree = ET.parse(flo)
        root = tree.getroot()

        # Define the paths to find the data in the real XML structure
        path_to_area = ".//text[@type='warning_area_summary']/p"
        path_to_title = ".//text[@type='warning_title']/p"
        path_to_headline = ".//text[@type='warning_headline']"
        path_to_situation = ".//text[@type='synoptic_situation']/p"
        
        area_element = root.find(path_to_area)
        if area_element is None or area_element.text is None: return None

        area_desc = area_element.text
        warning_id = root.find('.//amoc/identifier').text + root.find('.//amoc/issue-time-utc').text

        # This is the new, more inclusive check!
        if config["town"].lower() in area_desc.lower():
            title = root.find(path_to_title).text
            headline = root.find(path_to_headline).text
            situation = root.find(path_to_situation).text
            full_message = f"{headline}\n\n{situation}"
            
            return {"id": warning_id, "title": title.strip(), "message": full_message.strip()}
            
    except ftplib.error_perm: return None # No active warning file, this is normal.
    except Exception as e:
        # Silently log errors to the console without crashing the background process
        print(f"An error occurred during check: {e}")
        return None
    return None

def main_loop(config):
    """The main function that runs the check periodically."""
    root_tk = tk.Tk()
    app = WeatherAlertApp(root_tk)
    processed_warning_id = None
    
    # Hide the console window on subsequent runs if this is a bundled .exe
    # (This is more advanced and requires a different compilation flag)
    
    while True:
        try:
            warning = fetch_and_parse_warning(config)
            
            if warning:
                if warning["id"] != processed_warning_id:
                    app.display_alert(warning)
                    processed_warning_id = warning["id"]
            else:
                processed_warning_id = None

            time.sleep(300) # Check every 5 minutes
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"A critical error occurred in the main loop: {e}")
            time.sleep(300) # Wait before retrying

# --- Main Program Execution ---
if __name__ == "__main__":
    config = load_config()

    if config is None:
        print("No configuration file found. Starting first-time setup...")
        config = run_first_time_setup()

    if config:
        print(f"--- WxAlert Starting ---")
        print(f"Monitoring for '{config['town']}' in file '{config['warning_file']}' every 5 minutes.")
        print("This window can be minimized. To stop, close the window or press Ctrl+C.")
        main_loop(config)
    else:
        print("Setup was cancelled. Exiting program.")
        sys.exit()