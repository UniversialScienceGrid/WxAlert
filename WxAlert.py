import tkinter as tk
from tkinter import simpledialog, messagebox
import ftplib
import time
import os
import json
from io import BytesIO
import xml.etree.ElementTree as ET
import base64
from PIL import Image, ImageTk

APP_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'WxAlert')
CONFIG_FILE = os.path.join(APP_DATA_DIR, 'config.json')
os.makedirs(APP_DATA_DIR, exist_ok=True)

STATE_MAP = {
    "Queensland": "IDQ21037.xml",
    "New South Wales": "IDN21037.xml",
    "Victoria": "IDV21033.xml",
    "South Australia": "IDS21037.xml",
    "Western Australia": "IDW21037.xml",
    "Tasmania": "IDT21037.xml",
    "Northern Territory": "IDD21037.xml",
    "Australian Capital Territory": "IDN21037.xml"
}

SEVERITY_LEVELS = {
    "All Clear": {"color": "green", "icon": "✅"},
    "Minor": {"color": "gold", "icon": "⚠️"},
    "Major": {"color": "red", "icon": "❗"},
    "Deadly": {"color": "black", "text_color": "white", "icon": "☠️"},
    "Default": {"color": "darkorange", "icon": "📢"}
}


def determine_severity(warning_title, warning_text):
    title_lower = warning_title.lower()
    text_lower = warning_text.lower()
    
    # Mark heavy rain / flash flood warnings as Major
    if "heavy rainfall" in text_lower or "flash flooding" in text_lower:
        return "Major"
    if "tornado" in title_lower or "destructive" in title_lower:
        return "Deadly"
    if "severe" in title_lower or "fire" in title_lower:
        return "Major"
    if "strong wind" in title_lower or "hazardous surf" in title_lower:
        return "Minor"
    if "cancellation" in title_lower:
        return "All Clear"
    return "Default"

class WeatherAlertApp:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()

    def display_alert(self, alert_data):
        severity_name = determine_severity(alert_data["title"], alert_data["message"])
        config = SEVERITY_LEVELS.get(severity_name, SEVERITY_LEVELS["Default"])
        if severity_name == "All Clear":
            return

        alert_window = tk.Toplevel(self.master)
        alert_window.attributes('-fullscreen', True)
        alert_window.configure(bg=config["color"])

        text_frame = tk.Frame(alert_window, bg=config["color"])
        text_frame.place(relx=0, rely=0, relwidth=0.7, relheight=1)
        icon_label = tk.Label(text_frame, text=config["icon"], font=("Arial", 60),
                              bg=config["color"], fg=config.get("text_color", "black"))
        icon_label.pack(pady=20)
        title_label = tk.Label(text_frame, text=alert_data["title"], font=("Arial", 30, "bold"),
                               wraplength=alert_window.winfo_screenwidth() * 0.65,
                               bg=config["color"], fg=config.get("text_color", "black"))
        title_label.pack(pady=20)
        message_label = tk.Label(text_frame, text=alert_data["message"], font=("Arial", 16),
                                 justify=tk.LEFT, wraplength=alert_window.winfo_screenwidth() * 0.65,
                                 bg=config["color"], fg=config.get("text_color", "black"))
        message_label.pack(pady=15)
        resume_label = tk.Label(text_frame, text="\nPress any key to close this alert.", font=("Arial", 16),
                                bg=config["color"], fg=config.get("text_color", "black"))
        resume_label.pack(pady=20)

        image_frame = tk.Frame(alert_window, bg="black")
        image_frame.place(relx=0.7, rely=0, relwidth=0.3, relheight=1)
        image_label = tk.Label(image_frame, bg="black")
        image_label.pack(expand=True, padx=10, pady=10)
        if alert_data.get("image_base64"):
            try:
                image_data = base64.b64decode(alert_data["image_base64"])
                img_obj = Image.open(BytesIO(image_data))
                img_obj.thumbnail((alert_window.winfo_screenwidth() * 0.3,
                                   alert_window.winfo_screenheight()))
                photo_img = ImageTk.PhotoImage(img_obj)
                image_label.config(image=photo_img)
                image_label.image = photo_img
            except Exception:
                error_label = tk.Label(image_frame, text="Map image corrupted or unavailable.",
                                       font=("Arial", 16), bg="black", fg="white",
                                       wraplength=alert_window.winfo_screenwidth() * 0.25)
                error_label.pack(expand=True)
        else:
            no_image_label = tk.Label(image_frame, text="No map provided with this warning.",
                                      font=("Arial", 16), bg="black", fg="white",
                                      wraplength=alert_window.winfo_screenwidth() * 0.25)
            no_image_label.pack(expand=True)

        alert_window.bind('<Key>', lambda e: alert_window.destroy())
        alert_window.focus_set()
        self.master.wait_window(alert_window)

def fetch_and_parse_warning(config):
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

        area_element = root.find(".//text[@type='warning_area_summary']/p")
        if area_element is None or area_element.text is None:
            return None
        area_desc = area_element.text

        if config["town"].lower() in area_desc.lower():
            title_element = root.find(".//text[@type='warning_title']/p")
            title = title_element.text.strip() if title_element is not None else "Weather Warning"

            headline_element = root.find(".//text[@type='warning_headline']")
            headline = headline_element.text.strip() if headline_element is not None else ""

            situation_element = root.find(".//text[@type='synoptic_situation']/p")
            situation = situation_element.text.strip() if situation_element is not None else ""

            full_message = f"{headline}\n\n{situation}".strip()

            warning_id = root.find('.//amoc/identifier').text + root.find('.//amoc/issue-time-utc').text

            image_element = root.find(".//element[@type='warning_image']")
            image_base64 = image_element.text.strip() if image_element is not None else None

            return {"id": warning_id, "title": title, "message": full_message, "image_base64": image_base64}

    except Exception as e:
        print(f"Error fetching warning: {e}")
        return None

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def run_first_time_setup():
    root = tk.Tk()
    root.withdraw()
    state_options = "\n".join(STATE_MAP.keys())
    state_prompt = f"Welcome to WxAlert!\n\nPlease select your State by typing its name exactly as shown below:\n\n{state_options}"
    user_state = ""
    while user_state not in STATE_MAP:
        user_state = simpledialog.askstring("WxAlert Setup (1/2) - State", state_prompt)
        if user_state is None: return None

    town_prompt = "Enter your nearest Town or City (e.g., Toowoomba, Cairns, Ipswich, etc.):"
    user_town = ""
    while not user_town:
        user_town = simpledialog.askstring("WxAlert Setup (2/2) - Town/City", town_prompt)
        if user_town is None: return None
        if not user_town.strip():
            messagebox.showwarning("Invalid Town", "Town/City name cannot be blank.")
            user_town = ""

    config_data = {"state": user_state, "town": user_town.strip(), "warning_file": STATE_MAP[user_state]}
    save_config(config_data)
    messagebox.showinfo("Setup Complete", f"WxAlert is now configured for '{user_town}, {user_state}'.")
    return config_data

def main_loop(config):
    root_tk = tk.Tk()
    app = WeatherAlertApp(root_tk)
    processed_warning_id = None

    while True:
        try:
            warning = fetch_and_parse_warning(config)
            if warning and warning["id"] != processed_warning_id:
                app.display_alert(warning)
                processed_warning_id = warning["id"]
            elif not warning:
                processed_warning_id = None
            time.sleep(300)  # check every 5 minutes
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Critical error in main loop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    config = load_config()
    if not config:
        config = run_first_time_setup()
    if config:
        main_loop(config)
