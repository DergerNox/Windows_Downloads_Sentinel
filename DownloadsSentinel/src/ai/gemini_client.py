"""
GeminiClient - Tier 3 Cloud AI

Uses Google Gemini to classify files.
Can analyze file contents for ambiguous cases.
Updated to use the new google-genai SDK.
"""
from google import genai
import base64
import mimetypes
import os
import logging


class GeminiClient:
    """
    Cloud AI client using Google Gemini.
    Supports both filename-only and full content analysis.
    """
    
    # File size limit for content upload (10MB)
    MAX_CONTENT_SIZE = 10 * 1024 * 1024
    
    # Supported file types for content analysis
    TEXT_EXTENSIONS = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.logger = logging.getLogger("GEMINI")

    def classify(self, file_name: str) -> str:
        """
        Classifies the file based on its name only.
        Returns a category string.
        """
        self.logger.info(f"API Call (filename only): {file_name}")
        prompt = f"""
        You are a file organizer. Categorize the following file based on its name.
        Return ONLY the category name.
        Categories: Images, Documents, Installers, Audio, Video, Archives, Code, Other.
        
        File: {file_name}
        Category:
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result = response.text.strip()
            self.logger.info(f"Response: Category '{result}'")
            return result
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return "Other"
    
    def classify_with_content(self, file_path: str) -> str:
        """
        Classifies the file by analyzing its CONTENTS.
        Used for ambiguous filenames.
        Returns a category string.
        """
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        self.logger.info(f"API Call (with content): {filename}")
        
        try:
            file_size = os.path.getsize(file_path)
            
            # Check file size limit
            if file_size > self.MAX_CONTENT_SIZE:
                self.logger.warning(f"File too large ({file_size} bytes), falling back to filename")
                return self.classify(filename)
            
            # Determine analysis method based on file type
            if ext in self.TEXT_EXTENSIONS:
                return self._analyze_text_file(file_path, filename)
            elif ext in self.IMAGE_EXTENSIONS:
                return self._analyze_image_file(file_path, filename)
            else:
                # For other file types, try to read as text or fall back
                return self._analyze_binary_file(file_path, filename)
                
        except Exception as e:
            self.logger.error(f"Content analysis error: {e}")
            return "Other"
    
    def _analyze_text_file(self, file_path: str, filename: str) -> str:
        """Analyze text-based file content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 4000 characters (enough for context, fits in token limit)
                content_preview = f.read(4000)
            
            prompt = f"""
            Analyze this file and categorize it.
            Return ONLY the category name.
            Categories: Documents, Code, Financial, Spreadsheet, Config, Other.
            
            Filename: {filename}
            
            File Content (preview):
            ```
            {content_preview}
            ```
            
            Category:
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result = response.text.strip()
            self.logger.info(f"Text analysis result: '{result}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Text analysis error: {e}")
            return "Documents"
    
    def _analyze_image_file(self, file_path: str, filename: str) -> str:
        """Analyze image content using Gemini Vision."""
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'image/jpeg'
            
            prompt = """
            Analyze this image and categorize it.
            Return ONLY the category name.
            Categories: Photos, Screenshots, Art, Documents (scanned), Memes, Icons, Other.
            
            Category:
            """
            
            # New SDK uses inline data format
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    prompt,
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_data).decode('utf-8')
                        }
                    }
                ]
            )
            
            result = response.text.strip()
            self.logger.info(f"Image analysis result: '{result}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            return "Images"
    
    def _analyze_binary_file(self, file_path: str, filename: str) -> str:
        """For binary files, analyze the filename and extension."""
        # For binary files we can't easily analyze, just use filename
        return self.classify(filename)
