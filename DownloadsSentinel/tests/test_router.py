import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock dependencies before import
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
# We also need to mock local_client imports if they use requests at top level
# (They do invoke requests inside methods, but import is top level)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai.router import Router

# Mock config
MOCK_CONFIG = {
    "privacy": {
        "mode": "LOCAL",
        "sensitive_keywords": ["tax", "bank"]
    },
    "ai": {
        "local_url": "foo"
    }
}
MOCK_SECRETS = {}

class TestRouter(unittest.TestCase):
    def test_tier1_rules(self):
        router = Router(MOCK_CONFIG, MOCK_SECRETS)
        self.assertEqual(router.route("setup.exe"), "Installers")
        self.assertEqual(router.route("image.jpg"), "Images")
        self.assertEqual(router.route("document.pdf"), "Documents")

    def test_tier2_privacy(self):
        router = Router(MOCK_CONFIG, MOCK_SECRETS)
        self.assertEqual(router.route("my_tax_report.txt"), "Secure_Vault")
        self.assertEqual(router.route("bank_statement.pdf"), "Secure_Vault")

    def test_tier3_local_fallback(self):
        # Mock the local client
        router = Router(MOCK_CONFIG, MOCK_SECRETS)
        router.local_ai.classify = MagicMock(return_value="Documents")
        
        # Unknown extension, no keywords -> Tier 3
        self.assertEqual(router.route("unknown_file.xyz"), "Documents")

if __name__ == '__main__':
    unittest.main()
