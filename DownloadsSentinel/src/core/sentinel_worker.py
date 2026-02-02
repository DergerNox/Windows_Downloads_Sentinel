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
import threading

from ai.workflow_engine import WorkflowEngine


import concurrent.futures

class SentinelWorker:
    """
    The infinite loop listener.
    Waits for items in the Queue.
    Processes items in PARALLEL using a ThreadPoolExecutor.
    """
    
    IDLE_TIMEOUT = 60  # seconds
    MAX_WORKERS = 4    # maximum concurrent tasks
    
    def __init__(self, job_queue: multiprocessing.Queue, config: dict, secrets: dict):
        self.job_queue = job_queue
        self.config = config
        self.secrets = secrets
        self.is_running = False
        self.logger = None
        self.workflow_engine = None
        self.last_task_time = time.time()
        self.executor = None
        self.active_tasks = 0
        self._lock = threading.Lock() # For active_tasks counter

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
    
    def _task_done_callback(self, future):
        """Callback when a thread finishes a task."""
        with self._lock:
            self.active_tasks -= 1
        # Update timestamp to prevent premature cleanup
        self.last_task_time = time.time()
        
        try:
            future.result() # Raise exceptions if any occurred
        except Exception as e:
            if self.logger:
                self.logger.error(f"Thread task error: {e}")

    def run_worker_loop(self):
        """
        Main Worker Loop.
        Runs in separate process.
        """
        self._setup_logging()
        self.logger.info("Worker Process Started (PID: {})".format(os.getpid()))
        self.is_running = True
        self.last_task_time = time.time()
        
        # Initialize ThreadPool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        
        while self.is_running:
            try:
                # Non-blocking get with timeout
                file_path = self.job_queue.get(timeout=2)
                
                # Reset idle timer
                self.last_task_time = time.time()
                
                # Submit task to ThreadPool
                with self._lock:
                    self.active_tasks += 1
                
                future = self.executor.submit(self.handle_task, file_path)
                future.add_done_callback(self._task_done_callback)
                
            except queue.Empty:
                # Check if we've been idle too long AND no active tasks
                with self._lock:
                    is_idle = (self.active_tasks == 0)
                
                if is_idle:
                    idle_time = time.time() - self.last_task_time
                    if idle_time > self.IDLE_TIMEOUT:
                        self.perform_cleanup()
                continue
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Worker Error: {e}")
        
        # Shutdown executor on exit
        if self.executor:
            # wait=True ensures pending tasks complete before killing the process
            self.executor.shutdown(wait=True)

    def handle_task(self, file_path: str):
        """Process a single file task."""
        # Ensure engine is initialized (thread-safe check needed if not already init)
        # Since _init_engine is simple lazy load, we can call it here.
        # Ideally WorkflowEngine should be thread-safe.
        self._init_engine()
        
        if self.logger:
            self.logger.info(f"Processing: {file_path}")
        
        try:
            self.workflow_engine.process_file(file_path)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Task failed for {file_path}: {e}")
    
    def perform_cleanup(self):
        """Release resources after idle timeout."""
        # Only cleanup if engine is loaded
        if self.workflow_engine:
            if self.logger:
                self.logger.info("Idle timeout reached. Performing cleanup...")
            
            # Unload local AI models if loaded
            if self.workflow_engine._local_client:
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
