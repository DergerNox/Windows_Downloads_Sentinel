import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies before import
sys.modules['psutil'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['ctypes.windll'] = MagicMock()
sys.modules['ctypes.windll.user32'] = MagicMock()

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.gaming_detector import GamingDetector

class TestGamingDetector(unittest.TestCase):
    
    @patch('core.gaming_detector.psutil.cpu_percent')
    def test_high_load(self, mock_cpu):
        detector = GamingDetector(cpu_threshold=80)
        
        mock_cpu.return_value = 85.0
        self.assertTrue(detector.is_high_load())
        
        mock_cpu.return_value = 10.0
        self.assertFalse(detector.is_high_load())

    @patch('core.gaming_detector.ctypes.windll.user32')
    def test_fullscreen_detection_logic(self, mock_user32):
        # Mock screen size
        mock_user32.GetSystemMetrics.side_effect = [1920, 1080] # W, H
        pass

if __name__ == '__main__':
    unittest.main()
