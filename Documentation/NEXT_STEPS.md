Markdown

# Windows Downloads Sentinel v1.0 - Validation & Launch Protocol

**Current Status:** Feature Complete ✅
**Objective:** Validate non-functional constraints (Performance & Privacy) before general usage.

This document outlines the strict testing procedure required to certify v1.0.0.

---

## Phase 1: Environment Setup

Before running tests, ensure the local environment is correctly configured.

- [ ] **Dependency Installation**
  ```bash
  pip install -r requirements.txt
[ ] Secrets Configuration Rename config/secrets_template.json to config/secrets.json and populate:

JSON

{
  "GEMINI_API_KEY": "your_actual_api_key_here"
}
[ ] Config Verification Ensure config/config.json is set to default:

JSON

{
  "mode": "CLOUD",
  "gamer_mode_enabled": true
}
Phase 2: The "Gamer Certification" Test (Critical)
Reference: Master Doc Section 8.1

Goal: Prove the "Zero-Inference Rule" (No CPU/Network usage during gaming).

Launch Sentinel: Run python src/main.py. Verify the Tray Icon appears.

Open Task Manager: Locate python.exe (Master) and filter for worker.py (Worker).

Simulate Game State:

Option A: Launch a genuine full-screen game (Cyberpunk, COD, etc.).

Option B: Open a 4K YouTube video in Full Screen (simulates Window State: Maximized).

The Stress Test:

While the "game" is running, drop 50 dummy files into the Downloads folder.

Verification Criteria:

[ ] The Tray Icon must NOT animate/change state.

[ ] The Worker Process must NOT appear in Task Manager.

[ ] Files must remain in Downloads (queued) until the game closes.

Cleanup: Close the game. Verify the Worker launches within 10 seconds and processes the queue.

Phase 3: The "Privacy Airlock" Test
Reference: Master Doc Section 8.2

Goal: Verify sensitive files bypass the AI Cloud API entirely.

Prepare Logs: Open src/logs/sentinel.log (tail or keep open).

Create Bait File: Create a file named my_bitcoin_wallet_password.txt.

Action: Drop the file into Downloads.

Verification Criteria:

[ ] File moves to ~/Documents/Secure_Vault (or configured secure path).

[ ] Log file shows: [ROUTER] Privacy Airlock Triggered for: my_bitcoin_wallet_password.txt.

[ ] Log file shows: [GEMINI] API Call is ABSENT for this specific timestamp.

Phase 4: Functional AI Test (Hybrid Engine)
Goal: Ensure Tier 3 (Cloud AI) works for non-sensitive files.

Test Payload: Drop a generic PDF, e.g., invoice_template_generic.pdf.

Verification:

[ ] File moves to ~/Documents/Financial (or similar category).

[ ] Log file confirms: [GEMINI] Response: Category 'Financial'.

Phase 5: Build & Freeze
Once all tests pass, generate the executable for standalone usage.

[ ] Build Command:

Bash

pyinstaller --noconsole --onefile --icon=assets/icon.ico --name="DownloadsSentinel" src/main.py
[ ] Final Check: Run the resulting .exe on a fresh reboot to test the "Run on Startup" logic.

Sign-off: If all checkboxes are cleared, v1.0.0 is ready for release.