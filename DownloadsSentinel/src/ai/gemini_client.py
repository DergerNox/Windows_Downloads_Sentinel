import google.generativeai as genai
import json
import os
import logging

class GeminiClient:
    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = logging.getLogger("GEMINI")

    def classify(self, file_name):
        """
        Classifies the file based on its name using Gemini.
        Returns a category string.
        """
        self.logger.info(f"API Call initiated for: {file_name}")
        prompt = f"""
        You are a file organizer. Categorize the following file based on its name.
        Return ONLY the category name.
        Categories: Images, Documents, Installers, Audio, Video, Archives, Code, Other.
        
        File: {file_name}
        Category:
        """
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            self.logger.info(f"Response: Category '{result}'")
            return result
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return "Other"
