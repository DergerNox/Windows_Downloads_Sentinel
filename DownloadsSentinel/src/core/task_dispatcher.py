"""
TaskDispatcher - The Gatekeeper

Receives file events from Watchdog.
If GamingDetector says "Busy", buffers tasks.
If "Free", pushes to Queue.
"""
import multiprocessing
import time
import threading
import logging
from core.gaming_detector import GamingDetector


class TaskDispatcher:
    """
    The 'Gatekeeper'.
    Receives file events from Watchdog.
    If GamingDetector says 'Busy', it buffers tasks in a list.
    If 'Free', it pushes to Queue.
    """
    
    def __init__(self, detector: GamingDetector, job_queue: multiprocessing.Queue):
        self.detector = detector
        self.job_queue = job_queue
        self.pending_buffer = []  # Buffer for when User is Busy
        self.is_running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger("TaskDispatcher")

    def on_file_created(self, file_path: str):
        """Called by Watcher when a file is detected."""
        self.dispatch_or_queue(file_path)
    
    def dispatch_or_queue(self, file_path: str):
        """Dispatch to worker or queue for later."""
        with self._lock:
            if self.detector.is_user_busy():
                self.logger.info(f"User Busy. Buffering: {file_path}")
                self.pending_buffer.append(file_path)
            else:
                self.logger.info(f"User Idle. Dispatching: {file_path}")
                self.job_queue.put(file_path)

    def flush_pending_tasks(self):
        """Flush all buffered tasks to the queue."""
        with self._lock:
            if self.pending_buffer:
                self.logger.info(f"Flushing buffer ({len(self.pending_buffer)} items)...")
                for file_path in self.pending_buffer:
                    self.job_queue.put(file_path)
                self.pending_buffer.clear()

    def _buffer_monitor_loop(self):
        """Background thread to check buffer periodically."""
        while self.is_running:
            time.sleep(5)  # Check every 5 seconds
            if self.pending_buffer:
                if not self.detector.is_user_busy():
                    self.flush_pending_tasks()

    def start(self):
        """Start the buffer monitor thread."""
        self.is_running = True
        self._monitor_thread = threading.Thread(target=self._buffer_monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("TaskDispatcher started")

    def stop(self):
        """Stop the buffer monitor."""
        self.is_running = False
        self.logger.info("TaskDispatcher stopped")
