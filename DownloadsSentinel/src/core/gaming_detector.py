import psutil
import time
import logging
import sys

# Import Windows-specific libraries only on Windows
if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes
    user32 = ctypes.windll.user32
else:
    user32 = None
    ctypes = None

class GamingDetector:
    """
    Detects if the user is busy (e.g., gaming or high CPU load).
    Used to pause file processing during intensive tasks.
    """

    def __init__(self, cpu_threshold=85):
        self.cpu_threshold = cpu_threshold
        self.last_check = 0
        self.cached_result = False
        self.cache_duration = 2  # Cache result for 2 seconds to avoid spamming API
        self.logger = logging.getLogger("GamingDetector")

    def get_screen_size(self):
        """Returns the resolution of the primary monitor."""
        if user32:
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return 1920, 1080 # Fallback for non-Windows or testing

    def is_fullscreen(self):
        """
        Checks if the foreground window is full screen.
        Logic: Foreground window size >= Screen size (with small tolerance for borders).
        """
        if not user32:
            return False

        try:
            hwnd = user32.GetForegroundWindow()
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            win_w = rect.right - rect.left
            win_h = rect.bottom - rect.top
            
            screen_w, screen_h = self.get_screen_size()
            
            # Allow small tolerance for borderless/fullscreen variations
            tolerance = 10
            is_fs = (win_w >= screen_w - tolerance) and (win_h >= screen_h - tolerance)
            
            self.logger.debug(f"Window: {win_w}x{win_h}, Screen: {screen_w}x{screen_h}, Fullscreen: {is_fs}")
            return is_fs
        except Exception as e:
            self.logger.error(f"Fullscreen check error: {e}")
            return False

    def is_high_load(self):
        """Checks if global CPU usage covers the threshold."""
        # interval=None is non-blocking but requires a previous call or internal timer in psutil
        # We'll use a very short interval if needed, or rely on instant read
        usage = psutil.cpu_percent(interval=0.1)
        return usage > self.cpu_threshold

    def is_user_busy(self):
        """
        Returns True if the user is Gaming or doing high-load work.
        Cached to prevent excessive polling in tight loops.
        """
        now = time.time()
        if now - self.last_check < self.cache_duration:
            return self.cached_result

        # Check conditions
        busy = self.is_fullscreen() or self.is_high_load()
        
        self.last_check = now
        self.cached_result = busy
        return busy

# Standalone test
if __name__ == "__main__":
    detector = GamingDetector()
    print("Monitoring user status... (Press Ctrl+C to stop)")
    try:
        while True:
            status = "BUSY (Gaming/High Load)" if detector.is_user_busy() else "IDLE"
            print(f"Status: {status} | CPU: {psutil.cpu_percent()}%", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
