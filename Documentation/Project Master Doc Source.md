Windows Downloads Sentinel v2.0 - Master Design DocumentProject NameWindows Downloads SentinelVersion 1.0.0 (Architecture Final)StatusReady for ImplementationTarget PlatformWindows 10/11 (x64)Dev EnvironmentGoogle Antigravity (Planning) -> Local Windows (Execution)PART I: PRODUCT REQUIREMENT DOCUMENT (PRD)1. Executive SummaryDownloads Sentinel is a "Performance-First" background utility that autonomously organizes the user's Downloads folder. Unlike typical organizers, it uses a Hybrid AI Engine (Cloud + Local) to sort files contextually but prioritizes system resources above all else. It features a unique "Gamer Mode" that guarantees 0% FPS drop by pausing execution during high-load scenarios.2. Core Philosophy & ConstraintsPerformance First: The application must run on an average PC (8GB RAM) without slowing it down.Zero-Inference Rule: If the user is gaming, the app does NOTHING.Privacy Airlock: Sensitive financial/legal documents never leave the local machine.No "Dependency Hell": Avoid massive GPU drivers (CUDA); rely on CPU-optimized quantization.3. Key FeaturesGamer Mode (Adaptive Scheduling): Detects Full-Screen applications or CPU usage >85%. Instantly pauses the Worker process.Hybrid AI Engine:Tier 1 (Rules): Instant Regex sorting (e.g., .exe -> Software).Tier 2 (Cloud): Google Gemini 1.5 Flash for general file categorization (if enabled).Tier 3 (Local Fallback): Qwen 0.5B (via Ollama) for offline/privacy mode.Ghost UI: A System Tray-only interface with a separate, lightweight Settings window.4. System Architecture DiagramThe system uses a Master-Worker Pattern to isolate the UI from heavy AI processing.graph TD
    %% --- Styles ---
    classDef resourceLight fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef resourceHeavy fill:#ffecb3,stroke:#ff6f00,stroke-width:2px,stroke-dasharray: 5 5;
    classDef queue fill:#fff9c4,stroke:#fbc02d,stroke-width:3px;

    subgraph HostMachine [💻 Host PC - Windows]
        %% MASTER PROCESS
        subgraph MasterProcess [Process A: MASTER (UI/Watcher)]
            TrayIcon[Google Tray Icon]:::resourceLight
            Watcher[File Watcher]:::resourceLight
            GamingDetector[🎮 Gamer Mode Detector]:::resourceLight
            Dispatcher{Dispatcher}:::resourceLight
            
            TrayIcon --> Watcher
            Watcher --> GamingDetector
            GamingDetector --"User Busy?"--> Dispatcher
        end

        %% QUEUE
        JobQueue((📬 IPC Queue)):::queue

        %% WORKER PROCESS
        subgraph WorkerProcess [Process B: WORKER (AI Engine)]
            QueueListener[Queue Listener]:::resourceHeavy
            WorkflowEngine{Router}:::resourceHeavy
            
            subgraph AI_Tiers [Intelligence Layers]
                RuleEngine[Tier 1: Regex]
                PrivacyFilter[Tier 2: Keyword Block]
                CloudClient[Tier 3: Gemini API]
                LocalAIHost[Tier 3: Ollama/Qwen]
            end
            
            FileMover[File Mover]:::resourceHeavy
        end

        %% CONNECTIONS
        Dispatcher --"Idle"--> JobQueue
        Dispatcher --"Busy"--> PendingList[Buffer]
        JobQueue --> QueueListener
        QueueListener --> WorkflowEngine
        WorkflowEngine --> AI_Tiers
        AI_Tiers --> FileMover
    end
PART II: TECHNICAL DESIGN DOCUMENT (TDD)5. Process Specifications5.1 Process A: MainProcess (Master)Role: Light footprint (<25MB RAM). Handles User Interface and File Watching.Constraint: NEVER performs blocking I/O or AI inference.Libraries: pystray (Tray), watchdog (Files), ctypes (WinAPI), customtkinter (Settings).5.2 Process B: WorkerProcess (Worker)Role: Heavy lifting. Handles AI inference and File I/O.Memory Budget: Dynamic. Must perform Garbage Collection (GC) aggressively after every task.Libraries: google.generativeai (Cloud), requests (Ollama), shutil (File Ops).6. Project Structure (Antigravity Layout)The AI Agent must generate this exact directory structure:DownloadsSentinel/
├── config/
│   ├── config.json          # User settings
│   └── secrets.json         # API Keys (Encrypted)
├── logs/                    # Rotating log files
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry Point (Process A)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── gaming_detector.py # WIN32 API Logic
│   │   ├── watcher.py       # Watchdog Observer
│   │   ├── worker.py        # Process B Main Loop
│   │   └── dispatcher.py    # Queue Manager
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── router.py        # Logic: Regex vs Cloud vs Local
│   │   ├── gemini_client.py # Cloud Logic
│   │   └── local_client.py  # Ollama Logic
│   └── ui/
│   │   ├── __init__.py
│   │   ├── tray.py          # Pystray Icon
│   │   └── settings.py      # CustomTkinter Window
├── tests/
│   ├── test_detector.py     # Gamer Mode Unit Tests
│   └── test_router.py       # AI Routing Tests
├── requirements.txt
└── README.md
7. Component Details7.1 core/gaming_detector.pyResponsibility: The "Traffic Light" for the system.Dependencies: ctypes.windll.user32, psutil.Methods:is_fullscreen(): Checks if the foreground window resolution equals the screen resolution.is_high_load(): Checks if global CPU usage > 85%.is_user_busy(): Returns True if either condition is met.7.2 ai/router.py (The Routing Logic)def route_file(file_path):
    # Tier 1: Fast Rules
    if file_extension in [".exe", ".msi", ".zip"]:
        return "Installers"
    
    # Tier 2: Privacy Airlock
    if "bank" in filename or "tax" in filename:
        return "Secure_Vault" # Force Local move, NO AI

    # Tier 3: AI Inference
    if config.MODE == "CLOUD":
        return GeminiClient.classify(file_path)
    else:
        return LocalClient.classify(file_path) # Qwen/Moondream
7.3 config.json Schema{
  "general": { "run_at_startup": true },
  "privacy": {
    "mode": "CLOUD",
    "sensitive_keywords": ["bank", "tax", "cv", "password"]
  },
  "performance": {
    "gamer_mode": true,
    "cpu_threshold": 85
  }
}
8. Testing Strategy8.1 The "Gamer Certification" TestScenario: Launch a full-screen game (e.g., Cyberpunk, Warzone).Action: Drop 50 files into Downloads.Pass Criteria: The Worker process must NOT start. RAM usage must stay <25MB.8.2 The "Privacy Airlock" TestScenario: Create a dummy file named my_bitcoin_wallet_password.txt.Action: Enable "Cloud Mode".Pass Criteria: The file is moved to ~Secured/, and Zero network requests are sent to Google APIs.PART III: ROADMAP9. Future Plans (v2.1+)"Unzip & Clean" Protocol: Automatically extract single-folder Zips and delete the archive.Context-Aware Routing: Detect active window (e.g., "Photoshop") and route images to Project_Assets/.Desktop Butler: Auto-archive screenshots older than 24 hours.