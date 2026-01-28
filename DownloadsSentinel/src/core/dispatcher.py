import queue
import time
import threading
import logging
from core.gaming_detector import GamingDetector

class Dispatcher:
    def __init__(self, detector: GamingDetector):
        self.detector = detector
        self.job_queue = queue.Queue() # Queue for Worker Process
        self.pending_buffer = []       # Buffer for when User is Busy
        self.is_running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger("Dispatcher")

    def handle_file_event(self, file_path):
        """Called by Watcher when a file is detected."""
        with self._lock:
            if self.detector.is_user_busy():
                self.logger.info(f"User Busy. Buffering: {file_path}")
                self.pending_buffer.append(file_path)
            else:
                self.logger.info(f"User Idle. Queuing: {file_path}")
                self.job_queue.put(file_path)

    def process_buffer(self):
        """
        Periodically checks if the user is free to process buffered files.
        Should be run in a separate thread.
        """
        while self.is_running:
            if self.pending_buffer:
                if not self.detector.is_user_busy():
                    with self._lock:
                        self.logger.info(f"Flushing buffer ({len(self.pending_buffer)} items)...")
                        for file_path in self.pending_buffer:
                            self.job_queue.put(file_path)
                        self.pending_buffer.clear()
            time.sleep(5) # Check every 5 seconds

    def start(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.process_buffer, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        self.is_running = False
