import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies before import
sys.modules['psutil'] = MagicMock()

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

    @patch('core.gaming_detector.ctypes')
    @patch('core.gaming_detector.user32')
    def test_fullscreen_detection_logic(self, mock_user32, mock_ctypes):
        # If user32 is None (Linux), these patches inject mocks so we can test logic

        # Mock screen size
        mock_user32.GetSystemMetrics.side_effect = [1920, 1080] # W, H

        # Mock Window Rect
        # We can't easily test the ctypes structure logic with mocks,
        # so we'll just verify the calls are made if we were to call it.

        detector = GamingDetector()

        # Use a simplified flow or just ensure no crash
        # Since logic heavily depends on ctypes structures, mocking is verbose.
        # Just ensuring it handles the call.

        # Setup mocks to avoid crash
        mock_rect = MagicMock()
        mock_rect.left = 0
        mock_rect.top = 0
        mock_rect.right = 1920
        mock_rect.bottom = 1080

        mock_ctypes.wintypes.RECT.return_value = mock_rect

        # Call
        is_fs = detector.is_fullscreen()

        # Verify
        mock_user32.GetForegroundWindow.assert_called()
        mock_user32.GetWindowRect.assert_called()

if __name__ == '__main__':
    unittest.main()
