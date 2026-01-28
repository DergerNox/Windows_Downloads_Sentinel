import os
import shutil
import logging
from ai.gemini_client import GeminiClient
from ai.local_client import LocalClient

class Router:
    def __init__(self, config, secrets):
        self.config = config
        self.secrets = secrets
        self.logger = logging.getLogger("Router")
        self.tier1_rules = {
            ".exe": "Installers", ".msi": "Installers", 
            ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
            ".jpg": "Images", ".png": "Images", ".gif": "Images",
            ".pdf": "Documents", ".docx": "Documents", ".txt": "Documents",
            ".mp3": "Audio", ".wav": "Audio",
            ".mp4": "Video", ".mkv": "Video", ".avi": "Video",
            ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code"
        }
        
        self.sensitive_keywords = self.config.get("privacy", {}).get("sensitive_keywords", [])
        
        # Initialize AI Clients
        self.gemini = None
        if "GEMINI_API_KEY" in self.secrets:
            self.gemini = GeminiClient(self.secrets["GEMINI_API_KEY"], self.config.get("ai", {}).get("model_name", "gemini-1.5-flash"))
            
        self.local_ai = LocalClient(
            self.config.get("ai", {}).get("local_url"),
            "qwen:0.5b" # Hardcoded backup model for now
        )

    def route(self, file_path):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        # Tier 0: Privacy Airlock (Highest Priority)
        # Check this BEFORE extensions to ensure sensitive files are not misrouted
        lower_name = filename.lower()
        for keyword in self.sensitive_keywords:
            if keyword in lower_name:
                self.logger.info(f"Privacy Airlock Triggered for: {filename}")
                return "Secure_Vault"

        # Tier 1: Regex / Extension Rules
        if ext in self.tier1_rules:
            return self.tier1_rules[ext]

        # Tier 3: AI Inference
        mode = self.config.get("privacy", {}).get("mode", "CLOUD")
        
        if mode == "CLOUD" and self.gemini:
            return self.gemini.classify(filename)
        elif mode == "LOCAL" or not self.gemini:
            # Fallback to Local if Cloud is disabled or not configured
            return self.local_ai.classify(filename)
            
        return "Other"
    
    def move_file(self, file_path, category):
        """Moves the file to the categorized subfolder with retry logic."""
        import time
        max_retries = 5
        base_dir = os.path.dirname(file_path)
        target_dir = os.path.join(base_dir, category)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        filename = os.path.basename(file_path)
        destination = os.path.join(target_dir, filename)

        for attempt in range(max_retries):
            try:
                # Check if file still exists (it might have been moved manually or deleted)
                if not os.path.exists(file_path):
                    self.logger.warning(f"File vanished before move: {file_path}")
                    return False

                shutil.move(file_path, destination)
                self.logger.info(f"Moved {filename} to {category}")
                return True
            except PermissionError:
                # File is locked (common during download or copy)
                self.logger.warning(f"File locked: {filename}. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(1.0) # Wait 1 second
            except Exception as e:
                # Other errors are likely fatal
                self.logger.error(f"Error moving file: {e}")
                return False
        
        self.logger.error(f"Failed to move {filename} after {max_retries} attempts (File Locked).")
        return False
