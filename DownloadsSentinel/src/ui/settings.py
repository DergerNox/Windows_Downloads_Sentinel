import customtkinter as ctk
from tkinter import filedialog
import json
import os
import sys
import winreg

APP_NAME = "WindowsDownloadsSentinel"

class SettingsWindow(ctk.CTk):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.title("Windows Downloads Sentinel - Settings")
        self.geometry("500x500")
        
        # Handle window close button (X)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1) # Spacer
        
        # Track if we should show cloud warning
        self.show_cloud_warning = True
        self._previous_ai_mode = "LOCAL (Ollama)"

        self.label = ctk.CTkLabel(self, text="Configuration", font=("Arial", 20))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        # Download Folder Frame
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_folder = ctk.CTkLabel(self.folder_frame, text="Download Folder Location:")
        self.lbl_folder.grid(row=0, column=0, padx=10, pady=10)
        
        self.folder_path_var = ctk.StringVar()
        self.entry_folder = ctk.CTkEntry(self.folder_frame, textvariable=self.folder_path_var, width=250)
        self.entry_folder.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self.folder_frame, text="Browse", width=70, command=self.browse_folder)
        self.btn_browse.grid(row=0, column=2, padx=10, pady=10)

        # Run on Startup Checkbox
        self.startup_var = ctk.BooleanVar()
        self.chk_startup = ctk.CTkCheckBox(self, text="Run on Windows Startup", variable=self.startup_var)
        self.chk_startup.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        # Gamer Mode Checkbox
        self.gamer_mode_var = ctk.BooleanVar()
        self.chk_gamer = ctk.CTkCheckBox(self, text="Pause during Fullscreen / High Load", variable=self.gamer_mode_var)
        self.chk_gamer.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        # AI API Checkbox
        self.ai_enabled_var = ctk.BooleanVar()
        self.chk_ai = ctk.CTkCheckBox(
            self, 
            text="Enable AI Classification", 
            variable=self.ai_enabled_var,
            command=self.on_ai_enabled_changed
        )
        self.chk_ai.grid(row=4, column=0, padx=20, pady=10, sticky="w")

        # AI Mode Dropdown
        self.ai_mode_frame = ctk.CTkFrame(self)
        self.ai_mode_frame.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        self.lbl_ai_mode = ctk.CTkLabel(self.ai_mode_frame, text="AI Provider:")
        self.lbl_ai_mode.grid(row=0, column=0, padx=10, pady=5)
        
        self.ai_mode_var = ctk.StringVar(value="LOCAL (Ollama)")  # Default to LOCAL
        self.dropdown_ai = ctk.CTkOptionMenu(
            self.ai_mode_frame, 
            values=["LOCAL (Ollama)", "CLOUD (Gemini)"],  # LOCAL first
            variable=self.ai_mode_var,
            command=self.on_ai_mode_changed,
            width=180,
            state="disabled"  # Start disabled, enable when AI is checked
        )
        self.dropdown_ai.grid(row=0, column=1, padx=10, pady=5)

        # CPU Threshold Slider
        self.lbl_cpu = ctk.CTkLabel(self, text="CPU Threshold: 85%")
        self.lbl_cpu.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.slider_cpu = ctk.CTkSlider(self, from_=50, to=100, command=self.update_cpu_label)
        self.slider_cpu.grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        # Save Button
        self.btn_save = ctk.CTkButton(self, text="Save & Close", command=self.save_settings)
        self.btn_save.grid(row=10, column=0, padx=20, pady=20)

        self.load_settings()
    
    def on_ai_enabled_changed(self):
        """Callback when AI enabled checkbox changes."""
        if self.ai_enabled_var.get():
            self.dropdown_ai.configure(state="normal")
            self.lbl_ai_mode.configure(text_color=("gray10", "gray90"))
        else:
            self.dropdown_ai.configure(state="disabled")
            self.lbl_ai_mode.configure(text_color="gray50")
    
    def on_ai_mode_changed(self, new_value):
        """Callback when AI mode dropdown changes."""
        if "CLOUD" in new_value and self.show_cloud_warning:
            self._show_cloud_privacy_warning()
    
    def _show_cloud_privacy_warning(self):
        """Show privacy warning for cloud mode."""
        # Create a custom dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Privacy Warning")
        dialog.geometry("420x220")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Warning message
        msg = ctk.CTkLabel(
            dialog, 
            text="⚠️ Cloud AI sends FILE CONTENTS to Google.\n\n"
                 "For ambiguous files, the actual content is uploaded\n"
                 "for better classification. Use LOCAL for full privacy.",
            font=("Arial", 12),
            wraplength=380
        )
        msg.pack(pady=20, padx=20)
        
        # Don't show again checkbox
        dont_show_var = ctk.BooleanVar()
        chk_dont_show = ctk.CTkCheckBox(dialog, text="Don't show this warning again", variable=dont_show_var)
        chk_dont_show.pack(pady=10)
        
        def on_ok():
            if dont_show_var.get():
                self.show_cloud_warning = False
            dialog.destroy()
        
        def on_cancel():
            # Revert to LOCAL
            self.ai_mode_var.set("LOCAL (Ollama)")
            dialog.destroy()
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="I Understand", command=on_ok, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=100).pack(side="left", padx=10)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Downloads Folder to Watch")
        if folder:
            self.folder_path_var.set(folder)

    def update_cpu_label(self, value):
        self.lbl_cpu.configure(text=f"CPU Threshold: {int(value)}%")

    def is_startup_enabled(self):
        """Check if app is registered in Windows startup."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                 r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def set_startup(self, enable):
        """Add or remove app from Windows startup."""
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        if enable:
            # Get the path to main.py (or the exe when built)
            main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py')
            startup_cmd = f'"{sys.executable}" "{main_script}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, startup_cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except WindowsError:
                pass  # Key doesn't exist
        winreg.CloseKey(key)

    def load_settings(self):
        # Load startup status from registry (default to True for first run)
        is_startup = self.is_startup_enabled()
        # If this is first run (no registry entry), default to True
        if not is_startup:
            # Check if config has setup_complete - if not, it's first run
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    if not data.get("general", {}).get("setup_complete", False):
                        is_startup = True  # Default to enabled on first run
        self.startup_var.set(is_startup)
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    # Performance settings
                    perf = data.get("performance", {})
                    self.gamer_mode_var.set(perf.get("gamer_mode", True))
                    cpu_val = perf.get("cpu_threshold", 85)
                    self.slider_cpu.set(cpu_val)
                    self.update_cpu_label(cpu_val)
                    # General settings
                    general = data.get("general", {})
                    dl_path = general.get("downloads_path", "%USERPROFILE%\\Downloads")
                    # Expand environment variables for display
                    self.folder_path_var.set(os.path.expandvars(dl_path))
                    # AI settings
                    ai_settings = data.get("ai", {})
                    self.ai_enabled_var.set(ai_settings.get("enabled", False))
                    # Load "don't show cloud warning" preference
                    self.show_cloud_warning = not ai_settings.get("cloud_warning_dismissed", False)
                    # AI mode (CLOUD or LOCAL) - default to LOCAL
                    privacy = data.get("privacy", {})
                    mode = privacy.get("mode", "LOCAL")
                    if mode == "CLOUD":
                        self.ai_mode_var.set("CLOUD (Gemini)")
                    else:
                        self.ai_mode_var.set("LOCAL (Ollama)")
                    # Sync dropdown state with checkbox
                    self.on_ai_enabled_changed()
            except Exception as e:
                # print(f"Error loading settings: {e}")
                pass

    def save_settings(self):
        # Handle startup registry
        self.set_startup(self.startup_var.get())
        
        # Read current config to preserve other keys
        current_config = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                current_config = json.load(f)
        
        if "performance" not in current_config:
            current_config["performance"] = {}
        if "general" not in current_config:
            current_config["general"] = {}
        if "ai" not in current_config:
            current_config["ai"] = {}
        if "privacy" not in current_config:
            current_config["privacy"] = {}
            
        current_config["performance"]["gamer_mode"] = self.gamer_mode_var.get()
        current_config["performance"]["cpu_threshold"] = int(self.slider_cpu.get())
        current_config["general"]["downloads_path"] = self.folder_path_var.get()
        current_config["general"]["run_at_startup"] = self.startup_var.get()
        current_config["ai"]["enabled"] = self.ai_enabled_var.get()
        current_config["ai"]["cloud_warning_dismissed"] = not self.show_cloud_warning
        
        # Save AI mode (convert display text to config value)
        mode_display = self.ai_mode_var.get()
        if "LOCAL" in mode_display:
            current_config["privacy"]["mode"] = "LOCAL"
        else:
            current_config["privacy"]["mode"] = "CLOUD"
        
        with open(self.config_path, 'w') as f:
            json.dump(current_config, f, indent=4)
            
        self.destroy()
    
    def on_close(self):
        """Handle window close button (X)."""
        self.quit()  # Exit mainloop
        self.destroy()

def open_settings(config_path):
    app = SettingsWindow(config_path)
    app.mainloop()

if __name__ == "__main__":
    # Assuming run from src/ui/ or similar, fix path to config
    # We will pass config path as arg or deduce it
    # For now, let's assume standard layout relative to this file
    # This file is in src/ui/settings.py. Config is in ../../config/config.json
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, 'config', 'config.json')
    open_settings(config_path)

