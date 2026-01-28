"""
LocalAIHost - Tier 3 Local AI

Interfaces with Ollama. Manages model loading/unloading for RAM efficiency.
"""
import requests
import logging
import gc
import base64


class LocalAIHost:
    """
    RAM Manager. Interfaces with Ollama.
    Responsible for loading models only when needed and unloading after.
    """
    
    def __init__(self, api_url: str = "http://localhost:11434/v1/chat/completions",
                 text_model: str = "qwen2.5:0.5b", vision_model: str = "moondream"):
        self.api_url = api_url
        self.logger = logging.getLogger("LocalAIHost")
        self.model_loaded = False
        self.current_model = None
        
        # Model configs
        self.text_model = text_model
        self.vision_model = vision_model
    
    def load_model(self, model_name: str = None) -> bool:
        """
        Load a model into Ollama memory.
        Uses Ollama's /api/generate with keep_alive to preload.
        """
        model = model_name or self.text_model
        try:
            # Ollama preload endpoint
            response = requests.post(
                self.api_url.replace("/v1/chat/completions", "/api/generate"),
                json={"model": model, "prompt": "", "keep_alive": "5m"},
                timeout=30
            )
            if response.status_code == 200:
                self.model_loaded = True
                self.current_model = model
                self.logger.info(f"Model loaded: {model}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
        return False
    
    def unload_model(self) -> bool:
        """
        Unload model from Ollama memory.
        Uses keep_alive: 0 to immediately unload.
        """
        if not self.current_model:
            return True
            
        try:
            response = requests.post(
                self.api_url.replace("/v1/chat/completions", "/api/generate"),
                json={"model": self.current_model, "prompt": "", "keep_alive": "0"},
                timeout=10
            )
            if response.status_code == 200:
                self.model_loaded = False
                self.logger.info(f"Model unloaded: {self.current_model}")
                self.current_model = None
                gc.collect()
                return True
        except Exception as e:
            self.logger.error(f"Failed to unload model: {e}")
        return False
    
    def classify_text_qwen(self, filename: str) -> str:
        """
        Classify file using Qwen text model.
        """
        prompt = f"""Classify this filename into a category.
Return ONLY the category name.
Categories: Documents, Images, Videos, Audio, Archives, Installers, Code, Financial, Other

Filename: {filename}
Category:"""
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.text_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                category = result["choices"][0]["message"]["content"].strip()
                self.logger.info(f"Qwen classified '{filename}' as '{category}'")
                return category
        except Exception as e:
            self.logger.error(f"Qwen classification error: {e}")
        
        return "Other"
    
    def analyze_image_moondream(self, image_path: str) -> str:
        """
        Analyze image using Moondream vision model.
        Note: Requires base64 encoding of image for Ollama vision.
        """
        
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            response = requests.post(
                self.api_url.replace("/v1/chat/completions", "/api/generate"),
                json={
                    "model": self.vision_model,
                    "prompt": "What category does this image belong to? Return only: Photos, Screenshots, Documents, Art, Memes, Other",
                    "images": [image_data],
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                category = result.get("response", "Other").strip()
                self.logger.info(f"Moondream analyzed image as '{category}'")
                return category
        except Exception as e:
            self.logger.error(f"Moondream analysis error: {e}")
        
        return "Images"
    
    def classify(self, filename: str) -> str:
        """
        Main classification entry point.
        Uses text model by default.
        """
        return self.classify_text_qwen(filename)
