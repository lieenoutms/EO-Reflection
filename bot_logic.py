
import win32gui
import win32con
import win32api
import win32process
import time
import inputs
import pymem
import math


class BotLogic:
    def __init__(self, gui):
        """
        :param gui: Reference to the main CTRLSenderApp instance (to access GUI widgets and update status)
        """
        self.gui = gui
        self.toggle_on = False
        self.running = True

    def find_window_by_title(self, title):
        """Return the first window handle that contains the title."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
                hwnds.append(hwnd)
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None

    def send_single_move(self, direction):
        """Send a single key press (or key sequence) to the target window."""
        window_title = self.gui.title_entry.get()
        hwnd = self.find_window_by_title(window_title)
        key_map = {
            'w': 0x57,  # W key
            's': 0x53,  # S key
            'a': 0x41,  # A key
            'd': 0x44,  # D key
            'f11': win32con.VK_F11,
            'f12': win32con.VK_F12,
            'f2': win32con.VK_F2
        }
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            key_code = key_map.get(direction)
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.05)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
            self.gui.update_status(f"{direction.upper()} sent to {window_title}", "green")
        else:
            self.gui.update_status(f"Window '{window_title}' not found!", "red")

    def send_arrow_key(self, direction):
        """Send an arrow key press to the target window."""
        arrow_map = {
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT
        }
        window_title = self.gui.title_entry.get()
        hwnd = self.find_window_by_title(window_title)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            key_code = arrow_map.get(direction)
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.05)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
            self.gui.update_status(f"Arrow {direction} sent", "green")
        else:
            self.gui.update_status(f"Window '{window_title}' not found!", "red")

    def get_player_position(self):
        """
        Reads the player's X and Y coordinates from memory.
        Assumes the player's address (from the Player Address field) points to a structure where:
          - Offset 0: X coordinate (float)
          - Offset 4: Y coordinate (float)
        """
        player_addr_str = self.gui.player_entry.get()
        window_title = self.gui.title_entry.get()
        hwnd = self.find_window_by_title(window_title)
        if not hwnd:
            self.gui.update_status("Target window not found", "red")
            return None
        try:
            # Retrieve the process ID from the window handle.
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            pm = pymem.Pymem()
            pm.open_process(pid)
            player_addr = int(player_addr_str, 16)
            x = pm.read_float(player_addr)
            y = pm.read_float(player_addr + 4)
            return (x, y)
        except Exception as e:
            self.gui.update_status(f"Error reading player position: {e}", "red")
            return None

    def move_to_target(self, target_x, target_y, tolerance=5.0):
        """
        Move the player toward a target coordinate by sending arrow key presses.
        The method repeatedly reads the player's current position and sends an arrow key based on the largest delta.
        """
        import math  # Ensure math is imported (or use the module-level import)
        while True:
            pos = self.get_player_position()
            if pos is None:
                break
            current_x, current_y = pos
            dx = target_x - current_x
            dy = target_y - current_y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance <= tolerance:
                self.gui.update_status("Arrived at target", "green")
                break
            # Decide whether to move horizontally or vertically based on which delta is greater.
            if abs(dx) > abs(dy):
                if dx > 0:
                    self.send_arrow_key('right')
                else:
                    self.send_arrow_key('left')
            else:
                if dy > 0:
                    self.send_arrow_key('down')
                else:
                    self.send_arrow_key('up')
            time.sleep(0.5)  # Adjust delay as needed for your game

    def auto_send_ctrl(self):
        """Continuously send a CTRL key press if toggled on."""
        while self.running:
            if self.toggle_on:
                window_title = self.gui.title_entry.get()
                hwnd = self.find_window_by_title(window_title)
                if hwnd:
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
                    time.sleep(0.05)
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
                else:
                    self.gui.update_status(f"Window '{window_title}' not found!", "red")
            time.sleep(1)

    def toggle_auto_ctrl(self):
        """Toggle the auto CTRL feature on or off."""
        self.toggle_on = not self.toggle_on
        status = "enabled" if self.toggle_on else "disabled"
        button_text = "Stop Auto CTRL" if self.toggle_on else "Start Auto CTRL"
        self.gui.auto_button.config(text=button_text)
        self.gui.update_status(f"Auto CTRL {status}", "green" if self.toggle_on else "red")

    def listen_to_xbox_controller(self):
        """Listen for Xbox controller events and trigger actions accordingly."""
        while self.running:
            try:
                events = inputs.get_gamepad()
                for event in events:
                    # Toggle Auto CTRL with the left joystick button
                    if event.ev_type == "Key" and event.code == "BTN_THUMBL" and event.state == 1:
                        self.toggle_auto_ctrl()
                    # Trigger F12 with the right joystick button
                    if event.ev_type == "Key" and event.code == "BTN_THUMBR" and event.state == 1:
                        window_title = self.gui.title_entry.get()
                        hwnd = self.find_window_by_title(window_title)
                        if hwnd:
                            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_F12, 0)
                            time.sleep(0.05)
                            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_F12, 0)
                            self.gui.update_status("F12 triggered by right joystick", "green")
                        else:
                            self.gui.update_status(f"Window '{window_title}' not found!", "red")
            except Exception as e:
                self.gui.update_status(f"Controller Error: {e}", "red")
