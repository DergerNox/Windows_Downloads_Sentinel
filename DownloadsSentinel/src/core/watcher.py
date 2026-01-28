from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

class DownloadHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            # Wait a brief moment to ensure file handle is released (very basic check)
            # In a real scenario, we might want robust retries
            self.callback(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.callback(event.dest_path)

class FileWatcher:
    def __init__(self, path, callback):
        self.path = path
        self.callback = callback
        self.observer = Observer()
        self.handler = DownloadHandler(self.callback)

    def start(self):
        if not os.path.exists(self.path):
            print(f"Warning: Path {self.path} does not exist.")
            return
            
        self.observer.schedule(self.handler, self.path, recursive=False)
        self.observer.start()
        print(f"Watcher started on: {self.path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
