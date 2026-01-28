"""
WorkflowEngine - The Router

Decides the path of the file based on config (Tier 1 → Tier 2 → Tier 3).
"""
import os
import shutil
import time
import logging

from ai.rule_engine import RuleEngine
from ai.privacy_filter import PrivacyFilter
from ai.gemini_client import GeminiClient
from ai.local_client import LocalAIHost


class WorkflowEngine:
    """The router. Decides the path of the file through the tiers."""
    
    def __init__(self, config: dict, secrets: dict):
        self.config = config
        self.secrets = secrets
        self.logger = logging.getLogger("WorkflowEngine")
        
        # Initialize tier engines
        sensitive_keywords = config.get("privacy", {}).get("sensitive_keywords", [])
        self.rule_engine = RuleEngine()
        self.privacy_filter = PrivacyFilter(sensitive_keywords)
        
        # Tier 3 clients (lazy loaded)
        self._gemini_client = None
        self._local_client = None
        
        # AI mode from config
        self.ai_mode = config.get("privacy", {}).get("mode", "CLOUD")  # CLOUD, LOCAL, RULES_ONLY
    
    @property
    def gemini_client(self):
        """Lazy-load Gemini client."""
        if self._gemini_client is None:
            api_key = self.secrets.get("GEMINI_API_KEY", "")
            model_name = self.config.get("ai", {}).get("model_name", "gemini-1.5-flash")
            if api_key:
                self._gemini_client = GeminiClient(api_key, model_name)
        return self._gemini_client
    
    @property
    def local_client(self):
        """Lazy-load Local AI client."""
        if self._local_client is None:
            local_url = self.config.get("ai", {}).get("local_url", "http://localhost:11434/v1/chat/completions")
            self._local_client = LocalAIHost(local_url)
        return self._local_client
    
    def route_to_engine(self, filename: str) -> tuple[str, str]:
        """
        Route file through tiers and return (category, tier_used).
        """
        # Tier 0: Privacy Filter (Highest Priority)
        if self.privacy_filter.is_sensitive(filename):
            return self.privacy_filter.get_secure_destination(), "Tier0_Privacy"
        
        # Tier 1: Rule Engine (Fast)
        category = self.rule_engine.classify(filename)
        if category:
            return category, "Tier1_Rules"
        
        # Tier 2/3: AI (if not RULES_ONLY mode)
        if self.ai_mode == "RULES_ONLY":
            return "Other", "Tier1_Fallback"
        
        # Tier 3: AI Classification
        if self.ai_mode == "CLOUD" and self.gemini_client:
            category = self.gemini_client.classify(filename)
            return category, "Tier3_Cloud"
        elif self.ai_mode == "LOCAL" and self.local_client:
            category = self.local_client.classify(filename)
            return category, "Tier3_Local"
        
        # Fallback
        return "Other", "Fallback"
    
    def process_file(self, file_path: str) -> bool:
        """
        Process a file: classify and move it.
        Returns True on success.
        """
        filename = os.path.basename(file_path)
        category, tier = self.route_to_engine(filename)
        
        self.logger.info(f"[{tier}] {filename} → {category}")
        
        return self._move_file(file_path, category)
    
    def _move_file(self, file_path: str, category: str) -> bool:
        """Move file to categorized subfolder with retry logic."""
        max_retries = 5
        base_dir = os.path.dirname(file_path)
        target_dir = os.path.join(base_dir, category)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        filename = os.path.basename(file_path)
        destination = os.path.join(target_dir, filename)

        for attempt in range(max_retries):
            try:
                if not os.path.exists(file_path):
                    self.logger.warning(f"File vanished: {file_path}")
                    return False

                shutil.move(file_path, destination)
                self.logger.info(f"Moved {filename} to {category}")
                return True
            except PermissionError:
                self.logger.warning(f"File locked: {filename}. Retry ({attempt + 1}/{max_retries})...")
                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Error moving file: {e}")
                return False
        
        self.logger.error(f"Failed to move {filename} after {max_retries} attempts.")
        return False
