import pystray
from PIL import Image
import threading
import sys
import os


class TrayIcon:
    def __init__(self, on_quit_callback, on_settings_callback):
        self.on_quit_callback = on_quit_callback
        self.on_settings_callback = on_settings_callback
        self.icon = None

    def create_image(self):
        """Load the custom icon from assets folder."""
        # Get path to assets/icon.ico relative to this file
        # This file is in src/ui/tray.py, assets is at project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "assets", "icon.ico")
        
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        else:
            # Fallback: generate a simple icon
            from PIL import ImageDraw
            width = 64
            height = 64
            color1 = (0, 120, 215)
            color2 = (255, 255, 255)
            image = Image.new('RGB', (width, height), color1)
            dc = ImageDraw.Draw(image)
            dc.rectangle((width // 2 - 10, height // 2 - 10, width // 2 + 10, height // 2 + 10), fill=color2)
            return image

    def on_quit(self, icon, item):
        icon.stop()
        if self.on_quit_callback:
            self.on_quit_callback()

    def on_settings(self, icon, item):
        if self.on_settings_callback:
            # Run settings in a new thread so tkinter event loop works properly
            settings_thread = threading.Thread(target=self.on_settings_callback, daemon=True)
            settings_thread.start()

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem("Settings", self.on_settings),
            pystray.MenuItem("Quit", self.on_quit)
        )

        self.icon = pystray.Icon("WindowsDownloadSentinel", self.create_image(), "Downloads Sentinel", menu)
        self.icon.run_detached()  # Non-blocking, runs in separate thread

    def stop(self):
        if self.icon:
            self.icon.stop()
