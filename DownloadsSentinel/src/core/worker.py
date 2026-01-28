import logging
import sys
import os
import time
import queue
import gc

# Add src to path if ncecessary (though main.py handles it, direct imports are safer)
from ai.router import Router

class Worker:
    def __init__(self, job_queue, config, secrets):
        self.job_queue = job_queue
        self.router = Router(config, secrets)
        self.is_running = False
        self.logger = logging.getLogger("Worker")

    def run(self):
        """
        Main Worker Loop.
        Consumes files from the queue and routes them.
        """
        self.is_running = True
        self.logger.info("Started.")
        
        while self.is_running:
            try:
                # Block for 1 second, then check is_running
                file_path = self.job_queue.get(timeout=1)
                
                self.logger.info(f"Processing: {file_path}")
                category = self.router.route(file_path)
                self.router.move_file(file_path, category)
                
                self.job_queue.task_done()
                
                # Aggressive GC as per requirements
                gc.collect()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error: {e}")

    def stop(self):
        self.is_running = False
