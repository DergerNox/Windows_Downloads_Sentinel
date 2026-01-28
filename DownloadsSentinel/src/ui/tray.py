import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os

class TrayIcon:
    def __init__(self, on_quit_callback, on_settings_callback):
        self.on_quit_callback = on_quit_callback
        self.on_settings_callback = on_settings_callback
        self.icon = None

    def create_image(self):
        """Generates a simple icon image (blue square with a white dot)."""
        # In a real app, load a .png or .ico file
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
            self.on_settings_callback()

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
