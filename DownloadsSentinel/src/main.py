"""
Windows Downloads Sentinel - Main Entry Point (SentinelMaster)

Process A: The Master (GUI & Watcher)
Runs on the Main Thread. Critical constraint: Must remain under 15MB RAM and 0.1% CPU.
"""
import os
import json
import multiprocessing
import subprocess
import sys
import time
import logging
import logging.handlers

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
                logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
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
    
    def _launch_settings(self):
        """Launches the settings window as a separate process."""
        settings_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'settings.py')
        subprocess.Popen([sys.executable, settings_script])
    
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
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._quit_app()
    
    def _quit_app(self):
        """Shutdown all components."""
        print("Shutting down...")
        self.watcher.stop()
        self.dispatcher.stop()
        self.stop_worker()
        if self.tray:
            self.tray.stop()


def main():
    """Entry point for script execution."""
    # Required for Windows multiprocessing
    if sys.platform == 'win32':
        multiprocessing.freeze_support()
    
    master = SentinelMaster()
    master.main()


if __name__ == "__main__":
    main()
