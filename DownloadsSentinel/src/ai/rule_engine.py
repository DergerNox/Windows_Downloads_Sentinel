"""
RuleEngine - Tier 1 Fast Matching

Handles extension-based routing without AI.
"""
import os


class RuleEngine:
    """Fast regex/extension matching. Handles .jpg, .exe, .zip immediately."""
    
    def __init__(self):
        self.extension_map = {
            # Installers
            ".exe": "Installers",
            ".msi": "Installers",
            ".dmg": "Installers",
            # Archives
            ".zip": "Archives",
            ".rar": "Archives",
            ".7z": "Archives",
            ".tar": "Archives",
            ".gz": "Archives",
            # Images
            ".jpg": "Images",
            ".jpeg": "Images",
            ".png": "Images",
            ".gif": "Images",
            ".webp": "Images",
            ".bmp": "Images",
            ".svg": "Images",
            # Videos
            ".mp4": "Videos",
            ".mkv": "Videos",
            ".avi": "Videos",
            ".mov": "Videos",
            ".webm": "Videos",
            # Audio
            ".mp3": "Audio",
            ".wav": "Audio",
            ".flac": "Audio",
            ".m4a": "Audio",
            ".ogg": "Audio",
            # Documents
            ".pdf": "Documents",
            ".doc": "Documents",
            ".docx": "Documents",
            ".xls": "Documents",
            ".xlsx": "Documents",
            ".ppt": "Documents",
            ".pptx": "Documents",
            ".txt": "Documents",
            # Code
            ".py": "Code",
            ".js": "Code",
            ".html": "Code",
            ".css": "Code",
            ".java": "Code",
            ".cpp": "Code",
            ".c": "Code",
            ".h": "Code",
        }
        
        self.keyword_map = {
            "invoice": "Financial",
            "receipt": "Financial",
            "contract": "Legal",
            "agreement": "Legal",
        }
    
    def match_extension(self, filename: str) -> str | None:
        """
        Match file by extension.
        Returns category or None if no match.
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        return self.extension_map.get(ext)
    
    def match_simple_keyword(self, filename: str) -> str | None:
        """
        Match file by simple keyword in filename.
        Returns category or None if no match.
        """
        lower_name = filename.lower()
        for keyword, category in self.keyword_map.items():
            if keyword in lower_name:
                return category
        return None
    
    def classify(self, filename: str) -> str | None:
        """
        Attempt Tier 1 classification.
        Returns category or None to escalate to next tier.
        """
        # Try extension first
        result = self.match_extension(filename)
        if result:
            return result
        
        # Try keywords
        result = self.match_simple_keyword(filename)
        if result:
            return result
        
        return None
