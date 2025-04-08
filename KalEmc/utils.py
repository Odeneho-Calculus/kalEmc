import logging
import os
import platform
import subprocess
import time
from threading import Timer

logger = logging.getLogger(__name__)

def setup_autostart(app_path):
    """Configure the application to start automatically on system boot"""
    system = platform.system()
    
    try:
        if system == "Windows":
            import winreg
            startup_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(startup_key, "EyeMouseAssistant", 0, winreg.REG_SZ, f'"{app_path}"')
            winreg.CloseKey(startup_key)
            return True
            
        elif system == "Darwin":  # macOS
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.eyemouse.assistant.plist")
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.eyemouse.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            with open(plist_path, "w") as f:
                f.write(plist_content)
                
            subprocess.run(["launchctl", "load", plist_path])
            return True
            
        elif system == "Linux":
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            
            desktop_file = os.path.join(autostart_dir, "eyemouse-assistant.desktop")
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Eye Mouse Assistant
Exec={app_path}
Terminal=false
X-GNOME-Autostart-enabled=true
"""
            with open(desktop_file, "w") as f:
                f.write(desktop_content)
                
            os.chmod(desktop_file, 0o755)
            return True
            
        else:
            logger.error(f"Unsupported operating system: {system}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up autostart: {e}")
        return False
    
def check_permissions():
    """Check if the application has the necessary permissions"""
    system = platform.system()
    permissions = {
        "camera": False,
        "microphone": False,
        "accessibility": False
    }
    
    try:
        if system == "Darwin":  # macOS
            # Check camera
            camera_check = subprocess.run(["tccutil", "status", "Camera"], 
                                          capture_output=True, text=True)
            permissions["camera"] = "ALLOWED" in camera_check.stdout
            
            # Check microphone
            mic_check = subprocess.run(["tccutil", "status", "Microphone"], 
                                       capture_output=True, text=True)
            permissions["microphone"] = "ALLOWED" in mic_check.stdout
            
            # Check accessibility
            access_check = subprocess.run(["tccutil", "status", "Accessibility"], 
                                          capture_output=True, text=True)
            permissions["accessibility"] = "ALLOWED" in access_check.stdout
            
        elif system == "Windows":
            # Limited permission check on Windows
            import winreg
            try:
                # Check if webcam access is potentially blocked
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam")
                permissions["camera"] = True
            except:
                permissions["camera"] = False
            
            try:
                # Check if microphone access is potentially blocked
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone")
                permissions["microphone"] = True
            except:
                permissions["microphone"] = False
                
            # Accessibility is harder to check on Windows
            permissions["accessibility"] = True
            
        elif system == "Linux":
            # Linux doesn't have a unified permission system
            # Just check if devices exist
            permissions["camera"] = os.path.exists("/dev/video0")
            permissions["microphone"] = os.path.exists("/dev/snd/pcmC0D0c")
            permissions["accessibility"] = True
            
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        
    return permissions

def delayed_execution(func, delay=5):
    """Execute a function after a delay"""
    timer = Timer(delay, func)
    timer.daemon = True
    timer.start()
    return timer

def get_system_info():
    """Get basic system information"""
    system_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }
    
    logger.info(f"System info: {system_info}")
    return system_info

def create_config_dir():
    """Create configuration directory if it doesn't exist"""
    config_dir = get_config_dir()
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_dir():
    """Get the configuration directory path"""
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), "EyeMouseAssistant")
    elif system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/EyeMouseAssistant")
    else:  # Linux
        return os.path.expanduser("~/.config/eyemouse-assistant")

def save_settings(settings):
    """Save settings to a configuration file"""
    import json
    config_dir = create_config_dir()
    config_file = os.path.join(config_dir, "settings.json")
    
    try:
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Settings saved to {config_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False

def load_settings():
    """Load settings from configuration file"""
    import json
    config_dir = get_config_dir()
    config_file = os.path.join(config_dir, "settings.json")
    
    # Default settings
    default_settings = {
        "wake_word": "wake up",
        "sleep_word": "go to sleep",
        "sensitivity": 10,
        "smoothing": 0.7,
        "autostart": False
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                settings = json.load(f)
                # Merge with defaults in case new settings were added
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
            logger.info(f"Settings loaded from {config_file}")
            return settings
        else:
            logger.info("No settings file found, using defaults")
            return default_settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return default_settings

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)