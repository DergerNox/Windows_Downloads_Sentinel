"""
SentinelWorker - Process B

Runs in a separate OS Process for RAM isolation.
Implements 60-second idle timeout with cleanup.
"""
import multiprocessing
import queue
import time
import gc
import logging
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.workflow_engine import WorkflowEngine


class SentinelWorker:
    """
    The infinite loop listener.
    Waits for items in the Queue.
    If queue is empty for >60s, releases all resources (garbage collection).
    """
    
    IDLE_TIMEOUT = 60  # seconds
    
    def __init__(self, job_queue: multiprocessing.Queue, config: dict, secrets: dict):
        self.job_queue = job_queue
        self.config = config
        self.secrets = secrets
        self.is_running = False
        self.logger = None  # Set up in worker process
        self.workflow_engine = None  # Lazy load in worker process
        self.last_task_time = time.time()
    
    def _setup_logging(self):
        """Setup logging in worker process."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'worker.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("SentinelWorker")
    
    def _init_engine(self):
        """Initialize workflow engine (lazy load)."""
        if self.workflow_engine is None:
            self.workflow_engine = WorkflowEngine(self.config, self.secrets)
    
    def run_worker_loop(self):
        """
        Main Worker Loop.
        Runs in separate process.
        """
        self._setup_logging()
        self.logger.info("Worker Process Started (PID: {})".format(os.getpid()))
        self.is_running = True
        self.last_task_time = time.time()
        
        while self.is_running:
            try:
                # Non-blocking get with timeout
                file_path = self.job_queue.get(timeout=5)
                
                # Reset idle timer
                self.last_task_time = time.time()
                
                # Handle task
                self.handle_task(file_path)
                
            except queue.Empty:
                # Check if we've been idle too long
                idle_time = time.time() - self.last_task_time
                if idle_time > self.IDLE_TIMEOUT:
                    self.perform_cleanup()
                continue
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Worker Error: {e}")
    
    def handle_task(self, file_path: str):
        """Process a single file task."""
        self._init_engine()
        
        if self.logger:
            self.logger.info(f"Processing: {file_path}")
        
        try:
            self.workflow_engine.process_file(file_path)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Task failed for {file_path}: {e}")
    
    def perform_cleanup(self):
        """
        Release resources after idle timeout.
        Aggressive garbage collection for RAM management.
        """
        if self.logger:
            self.logger.info("Idle timeout reached. Performing cleanup...")
        
        # Unload local AI models if loaded
        if self.workflow_engine and self.workflow_engine._local_client:
            self.workflow_engine._local_client.unload_model()
        
        # Clear engine references
        self.workflow_engine = None
        
        # Aggressive GC
        gc.collect()
        
        if self.logger:
            self.logger.info("Cleanup complete. Resources released.")
        
        # Reset idle timer
        self.last_task_time = time.time()
    
    def stop(self):
        """Stop the worker loop."""
        self.is_running = False


def worker_process_entry(job_queue: multiprocessing.Queue, config: dict, secrets: dict):
    """Entry point for worker process."""
    worker = SentinelWorker(job_queue, config, secrets)
    worker.run_worker_loop()
