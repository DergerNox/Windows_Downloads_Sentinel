from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import logging
import time

class DownloadHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self._process_event(event.src_path)
            
    def on_moved(self, event):
        if not event.is_directory:
            self._process_event(event.dest_path)
            
    def _process_event(self, file_path):
        """Process file event with checks."""
        filename = os.path.basename(file_path)
        
        # 1. Ignore temporary/partial download files
        if filename.endswith(('.crdownload', '.part', '.tmp', '.download')):
            return

        # 2. Wait for file to be ready (released by browser)
        if self._wait_for_file_ready(file_path):
            self.callback(file_path)
            
    def _wait_for_file_ready(self, file_path, timeout=10):
        """
        Wait until file is not locked by another process (e.g. browser).
        Returns True if ready, False if timed out.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to rename file to itself - reliable way to check for exclusive access on Windows
                os.rename(file_path, file_path)
                return True
            except OSError:
                # File is locked, wait and retry
                time.sleep(1)
            except Exception:
                return False
        return False

class FileWatcher:
    def __init__(self, path, callback):
        self.path = path
        self.callback = callback
        self.observer = Observer()
        self.handler = DownloadHandler(self.callback)
        self.logger = logging.getLogger("FileWatcher")

    def start(self):
        if not os.path.exists(self.path):
            self.logger.warning(f"Path {self.path} does not exist.")
            return
            
        self.observer.schedule(self.handler, self.path, recursive=False)
        self.observer.start()
        self.logger.info(f"Watcher started on: {self.path}")

    def process_existing_file(self, file_path):
        """Manually trigger processing for an existing file (used by Scanner)."""
        self.handler._process_event(file_path)

    def stop(self):
        self.observer.stop()
        self.observer.join()
