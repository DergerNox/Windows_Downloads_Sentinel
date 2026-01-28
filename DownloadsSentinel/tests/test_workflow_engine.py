import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock dependencies before import
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai.workflow_engine import WorkflowEngine

# Mock config
MOCK_CONFIG = {
    "privacy": {
        "mode": "LOCAL",
        "sensitive_keywords": ["tax", "bank"]
    },
    "ai": {
        "local_url": "foo",
        "text_model": "test-model",
        "vision_model": "test-vision"
    }
}
MOCK_SECRETS = {}

class TestWorkflowEngine(unittest.TestCase):
    def test_tier1_rules(self):
        engine = WorkflowEngine(MOCK_CONFIG, MOCK_SECRETS)
        self.assertEqual(engine.route_to_engine("setup.exe")[0], "Installers")
        self.assertEqual(engine.route_to_engine("image.jpg")[0], "Images")
        self.assertEqual(engine.route_to_engine("document.pdf")[0], "Documents")

    def test_tier2_privacy(self):
        engine = WorkflowEngine(MOCK_CONFIG, MOCK_SECRETS)
        self.assertEqual(engine.route_to_engine("my_tax_report.txt")[0], "Secure_Vault")
        self.assertEqual(engine.route_to_engine("bank_statement.pdf")[0], "Secure_Vault")

    def test_tier3_local_fallback(self):
        # Mock the local client
        engine = WorkflowEngine(MOCK_CONFIG, MOCK_SECRETS)

        # Inject mock client
        mock_client = MagicMock()
        mock_client.classify.return_value = "Documents"
        engine._local_client = mock_client

        # Unknown extension, no keywords -> Tier 3
        # Mode is LOCAL in MOCK_CONFIG
        self.assertEqual(engine.route_to_engine("unknown_file.xyz")[0], "Documents")

if __name__ == '__main__':
    unittest.main()
