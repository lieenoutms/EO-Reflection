# memory_reader.py
import win32gui
import win32process
import pymem


class MemoryReader:
    def __init__(self, window_title, npc_addr_str, player_addr_str, health_addr_str, map_id_str):
        """
        :param window_title: Title (or part of it) of the target window.
        :param npc_addr_str: NPC address as a hex string (e.g. "0x12345678").
        :param player_addr_str: Player address as a hex string.
        :param health_addr_str: Health address as a hex string.
        :param map_id_str: Map ID address as a hex string.
        """
        self.window_title = window_title
        self.npc_addr_str = npc_addr_str
        self.player_addr_str = player_addr_str
        self.health_addr_str = health_addr_str
        self.map_id_str = map_id_str

    def find_window_by_title(self, title):
        """Return the first window handle that contains the title."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
                hwnds.append(hwnd)
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None

    def read_values(self):
        """Open the target process and read integer values from the given addresses."""
        hwnd = self.find_window_by_title(self.window_title)
        if hwnd is None:
            return f"Window '{self.window_title}' not found!"

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception as e:
            return f"Error getting PID: {e}"

        try:
            pm = pymem.Pymem()
            pm.open_process(pid)
        except Exception as e:
            return f"Failed to open process: {e}"

        try:
            npc_addr = int(self.npc_addr_str, 16)
            player_addr = int(self.player_addr_str, 16)
            health_addr = int(self.health_addr_str, 16)
            map_id_addr = int(self.map_id_str, 16)

            npc_value = pm.read_int(npc_addr)
            player_value = pm.read_int(player_addr)
            health_value = pm.read_int(health_addr)
            map_id_value = pm.read_int(map_id_addr)

            msg = (f"NPC: {npc_value} | Player: {player_value} | "
                   f"Health: {health_value} | Map ID: {map_id_value}")
            return msg
        except Exception as e:
            return f"Memory read error: {e}"
