"""
Windows Downloads Sentinel - Main Entry Point (SentinelMaster)

Process A: The Master (GUI & Watcher)
Runs on the Main Thread. Critical constraint: Must remain under 15MB RAM and 0.1% CPU.
"""
import os
import json
import multiprocessing
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

from core.gaming_detector import GamingDetector
from core.watcher import FileWatcher
from core.task_dispatcher import TaskDispatcher
from core.sentinel_worker import worker_process_entry
from ui.tray import TrayIcon


class SentinelMaster:
    """
    The application entry point.
    Initializes the multiprocessing.Queue, starts the Worker Process,
    and launches the System Tray icon.
    """
    
    def __init__(self):
        self.config = None
        self.secrets = None
        self.config_path = None
        
        # IPC Queue (multiprocessing-safe)
        self.job_queue = multiprocessing.Queue()
        
        # Components
        self.detector = None
        self.dispatcher = None
        self.watcher = None
        self.tray = None
        
        # Worker Process
        self.worker_process = None
    
    def setup_logging(self):
        """Configure logging for the master process."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, 'sentinel.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] %(message)s',
            handlers=[
                RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def get_base_path(self):
        """Get the base path for resources. Handles PyInstaller bundled exe."""
        if getattr(sys, 'frozen', False):
            # Running as bundled exe - use _MEIPASS for bundled files
            return sys._MEIPASS
        else:
            # Running as script
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def load_config(self):
        """Load configuration files."""
        base_dir = self.get_base_path()
        self.config_path = os.path.join(base_dir, 'config', 'config.json')
        secrets_path = os.path.join(base_dir, 'config', 'secrets.json')
        
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.secrets = {}
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                self.secrets = json.load(f)
    
    def check_first_run(self):
        """Check if this is the first run and show settings if so."""
        if not self.config.get("general", {}).get("setup_complete", False):
            logging.info("First run detected. Opening Settings...")
            self._launch_settings_blocking()
            # Reload config after settings are saved
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            # Mark setup as complete
            self.config.setdefault("general", {})["setup_complete"] = True
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
    
    def _launch_settings_blocking(self):
        """Launches the settings window and waits for it to close."""
        from ui.settings import open_settings
        open_settings(self.config_path)
    
    def start_worker(self):
        """Start the worker process."""
        self.worker_process = multiprocessing.Process(
            target=worker_process_entry,
            args=(self.job_queue, self.config, self.secrets),
            daemon=True
        )
        self.worker_process.start()
        logging.info(f"Worker Process Started (PID: {self.worker_process.pid})")
    
    def stop_worker(self):
        """Stop the worker process."""
        if self.worker_process and self.worker_process.is_alive():
            self.worker_process.terminate()
            self.worker_process.join(timeout=5)
            logging.info("Worker Process Stopped")
    
    def _scan_existing_files(self):
        """
        Periodically scan the downloads folder for unorganized files.
        
        This method iterates through the downloads directory, filtering out:
        - Directories
        - Temporary download files (.crdownload, .part, etc.)
        - Files currently being written (checked via modification time)
        
        Valid files are passed to the Watcher's processing logic to be queued.
        """
        dl_path = os.path.expandvars(
            self.config["general"].get("downloads_path", "%USERPROFILE%\\Downloads")
        )
        
        if not os.path.exists(dl_path):
            return

        logging.info("Starting periodic file scan...")
        
        try:
            # Sequential Iteration
            for filename in os.listdir(dl_path):
                file_path = os.path.join(dl_path, filename)
                
                # Basic checks
                if os.path.isdir(file_path):
                    continue
                    
                if filename.endswith(('.crdownload', '.part', '.tmp', '.download')):
                    continue
                
                # Check modification time to avoid active downloads race condition
                # Skip files modified in the last 10 seconds
                try:
                    if time.time() - os.path.getmtime(file_path) < 10:
                        continue
                except OSError:
                    continue

                # Reuse Watcher logic (includes file locking check)
                if self.watcher:
                    self.watcher.process_existing_file(file_path)
                    
        except Exception as e:
            logging.error(f"Error during periodic scan: {e}")

    def main(self):
        """Main entry point."""
        self.setup_logging()
        logging.info("Starting Windows Downloads Sentinel...")
        
        self.load_config()
        self.check_first_run()
        
        # 1. Initialize Components
        self.detector = GamingDetector(
            cpu_threshold=self.config["performance"].get("cpu_threshold", 85)
        )
        self.dispatcher = TaskDispatcher(self.detector, self.job_queue)
        
        # Downloads path from config
        dl_path = os.path.expandvars(
            self.config["general"].get("downloads_path", "%USERPROFILE%\\Downloads")
        )
        
        self.watcher = FileWatcher(dl_path, self.dispatcher.on_file_created)
        
        self.tray = TrayIcon(
            on_quit_callback=self._quit_app,
            on_settings_callback=self._launch_settings_blocking
        )
        
        # 2. Start Worker Process
        self.start_worker()
        
        # 3. Start Dispatcher (buffer monitor)
        self.dispatcher.start()
        
        # 4. Start Watcher
        self.watcher.start()
        
        # 5. Start Tray (non-blocking)
        print("Sentinel Active. Check System Tray.")
        self.tray.run()
        
        # Initial Scan
        self._scan_existing_files()
        last_scan_time = time.time()
        
        self.running = True
        
        # Keep main thread alive & Periodic Scan Loop
        try:
            while self.running:
                time.sleep(1)
                
                # Check Scan Interval
                interval_minutes = self.config["general"].get("scan_interval_minutes", 60)
                interval_seconds = interval_minutes * 60
                
                if time.time() - last_scan_time > interval_seconds:
                    self._scan_existing_files()
                    last_scan_time = time.time()
                    # Reload config in case settings changed scan interval
                    self.load_config()
                    
        except KeyboardInterrupt:
            self._quit_app()
    
    def _quit_app(self):
        """Shutdown all components."""
        print("Shutting down...")
        self.running = False
        self.watcher.stop()
        self.dispatcher.stop()
        self.stop_worker()
        if self.tray:
            self.tray.stop()
        # Ensure we exit if called from a thread
        sys.exit(0)


def main():
    """Entry point for script execution."""
    # Required for Windows multiprocessing
    if sys.platform == 'win32':
        multiprocessing.freeze_support()
        
        # Single Instance Lock
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        mutex_name = "Global\\WindowsDownloadsSentinelMutex"
        # CreateMutexW(security_attributes, initial_owner, name)
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        
        if last_error == 183: # ERROR_ALREADY_EXISTS
            # App is already running
            user32.MessageBoxW(0, "Windows Downloads Sentinel is already running.", "Windows Downloads Sentinel", 0x30)
            return

    master = SentinelMaster()
    master.main()


if __name__ == "__main__":
    main()
