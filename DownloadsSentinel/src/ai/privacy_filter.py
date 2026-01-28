"""
PrivacyFilter - Tier 2 Security Gate

Scans filenames for sensitive keywords and routes to Secure Vault.
"""
import logging


class PrivacyFilter:
    """The 'Bouncer'. Scans filenames for sensitive keywords."""
    
    def __init__(self, sensitive_keywords: list[str] = None):
        self.logger = logging.getLogger("PrivacyFilter")
        self.sensitive_keywords = sensitive_keywords or [
            "bank", "tax", "cv", "password", "wallet", "invoice",
            "ssn", "social security", "credit card", "account",
            "passport", "license", "medical", "health"
        ]
    
    def is_sensitive(self, filename: str) -> bool:
        """
        Check if filename contains sensitive keywords.
        Returns True if file should be routed to Secure Vault.
        """
        lower_name = filename.lower()
        for keyword in self.sensitive_keywords:
            if keyword in lower_name:
                self.logger.info(f"Privacy Airlock Triggered: '{keyword}' in '{filename}'")
                return True
        return False
    
    def get_secure_destination(self) -> str:
        """Returns the secure folder name."""
        return "Secure_Vault"
