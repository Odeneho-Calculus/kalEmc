import threading
import logging
import sys
import os
import platform
import time

logger = logging.getLogger(__name__)

# Import necessary modules based on platform
if platform.system() == "Windows":
    import pystray
    from PIL import Image, ImageDraw
elif platform.system() == "Darwin":  # macOS
    import rumps
else:  # Linux
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import Gtk, AppIndicator3, GLib

from eye_mouse_controller import EyeMouseAssistant
from KalEmc.utils import load_settings, save_settings, setup_autostart, check_permissions, resource_path

class SystemTrayApp:
    def __init__(self):
        self.settings = load_settings()
        self.assistant = None
        self.assistant_thread = None
        
        # Create system tray based on platform
        self.create_tray_app()
        
    def create_tray_app(self):
        system = platform.system()
        
        if system == "Windows":
            self.create_windows_tray()
        elif system == "Darwin":  # macOS
            self.create_macos_tray()
        else:  # Linux
            self.create_linux_tray()
    
    def create_windows_tray(self):
        # Create a simple image for the systray icon
        icon = self.create_icon_image()
        
        # Create system tray menu
        menu_items = [
            pystray.MenuItem('Start Assistant', self.start_assistant),
            pystray.MenuItem('Stop Assistant', self.stop_assistant),
            pystray.MenuItem('Settings', self.show_settings),
            pystray.MenuItem('Exit', self.exit_app)
        ]
        menu = pystray.Menu(*menu_items)
        
        # Create system tray icon
        self.tray_icon = pystray.Icon("eye_mouse_assistant", icon, "Eye Mouse Assistant", menu)
        
        # Auto-start if configured
        if self.settings.get('autostart', False):
            self.start_assistant()
            
        # Run the system tray app
        self.tray_icon.run()
    
    def create_macos_tray(self):
        class MacOSTrayApp(rumps.App):
            def __init__(self, name, parent):
                super().__init__(name)
                self.parent = parent
                self.menu = ["Start Assistant", "Stop Assistant", "Settings", "Exit"]
                
                # Auto-start if configured
                if self.parent.settings.get('autostart', False):
                    self.parent.start_assistant()
            
            @rumps.clicked("Start Assistant")
            def start(self, _):
                self.parent.start_assistant()
            
            @rumps.clicked("Stop Assistant")
            def stop(self, _):
                self.parent.stop_assistant()
            
            @rumps.clicked("Settings")
            def settings(self, _):
                self.parent.show_settings()
            
            @rumps.clicked("Exit")
            def quit(self, _):
                self.parent.exit_app()
                rumps.quit_application()
        
        self.tray_app = MacOSTrayApp("Eye Mouse Assistant", self)
        self.tray_app.run()
    
    def create_linux_tray(self):
        # Create AppIndicator
        self.indicator = AppIndicator3.Indicator.new(
            "eye-mouse-assistant",
            "accessories-character-map",  # Default icon from theme
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # Create menu
        menu = Gtk.Menu()
        
        # Start item
        start_item = Gtk.MenuItem.new_with_label("Start Assistant")
        start_item.connect("activate", self.start_assistant)
        menu.append(start_item)
        
        # Stop item
        stop_item = Gtk.MenuItem.new_with_label("Stop Assistant")
        stop_item.connect("activate", self.stop_assistant)
        menu.append(stop_item)
        
        # Settings item
        settings_item = Gtk.MenuItem.new_with_label("Settings")
        settings_item.connect("activate", self.show_settings)
        menu.append(settings_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit item
        quit_item = Gtk.MenuItem.new_with_label("Exit")
        quit_item.connect("activate", self.exit_app)
        menu.append(quit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)
        
        # Auto-start if configured
        if self.settings.get('autostart', False):
            GLib.timeout_add(1000, self.start_assistant)
        
        # Run the main loop
        Gtk.main()
    
    def create_icon_image(self, size=64):
        """Create a simple eye icon for the system tray"""
        # Create a blank image with transparent background
        image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw an eye shape
        margin = 4
        draw.ellipse([margin, margin, size-margin, size-margin], outline=(0, 0, 0), width=2, fill=(255, 255, 255))
        
        # Draw pupil
        pupil_size = size // 3
        pupil_pos = (size // 2, size // 2)
        draw.ellipse([pupil_pos[0]-pupil_size//2, pupil_pos[1]-pupil_size//2, 
                     pupil_pos[0]+pupil_size//2, pupil_pos[1]+pupil_size//2], fill=(0, 0, 0))
        
        return image
    
    def start_assistant(self, *args):
        if self.assistant is None or not self.assistant_thread or not self.assistant_thread.is_alive():
            logger.info("Starting Eye Mouse Assistant")
            
            # Check permissions first
            permissions = check_permissions()
            if not all(permissions.values()):
                self.show_permission_dialog(permissions)
                return
                
            # Create and start the assistant
            self.assistant = EyeMouseAssistant(
                wake_word=self.settings.get('wake_word', "wake up"),
                sleep_word=self.settings.get('sleep_word', "go to sleep")
            )
            
            # Configure from settings
            if hasattr(self.assistant, 'gesture_controller'):
                self.assistant.gesture_controller.sensitivity = self.settings.get('sensitivity', 10)
                self.assistant.gesture_controller.smoothing = self.settings.get('smoothing', 0.7)
            
            # Start in separate thread
            self.assistant_thread = threading.Thread(target=self.assistant.start)
            self.assistant_thread.daemon = True
            self.assistant_thread.start()
            
            logger.info("Assistant started")
    
    def stop_assistant(self, *args):
        if self.assistant and self.assistant_thread and self.assistant_thread.is_alive():
            logger.info("Stopping Eye Mouse Assistant")
            self.assistant.stop()
            self.assistant_thread.join(timeout=2)
            self.assistant = None
            logger.info("Assistant stopped")
    
    def show_settings(self, *args):
        system = platform.system()
        
        if system == "Windows":
            self.show_windows_settings()
        elif system == "Darwin":
            self.show_macos_settings()
        else:
            self.show_linux_settings()
    
    def show_windows_settings(self):
        # Simple Windows settings dialog using tkinter
        import tkinter as tk
        from tkinter import ttk
        
        settings_window = tk.Tk()
        settings_window.title("Eye Mouse Assistant Settings")
        settings_window.geometry("400x300")
        
        # Wake word
        ttk.Label(settings_window, text="Wake Word:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        wake_word_var = tk.StringVar(value=self.settings.get('wake_word', "wake up"))
        ttk.Entry(settings_window, textvariable=wake_word_var).grid(column=1, row=0, padx=10, pady=10, sticky=tk.W+tk.E)
        
        # Sleep word
        ttk.Label(settings_window, text="Sleep Word:").grid(column=0, row=1, padx=10, pady=10, sticky=tk.W)
        sleep_word_var = tk.StringVar(value=self.settings.get('sleep_word', "go to sleep"))
        ttk.Entry(settings_window, textvariable=sleep_word_var).grid(column=1, row=1, padx=10, pady=10, sticky=tk.W+tk.E)
        
        # Sensitivity
        ttk.Label(settings_window, text="Sensitivity:").grid(column=0, row=2, padx=10, pady=10, sticky=tk.W)
        sensitivity_var = tk.DoubleVar(value=self.settings.get('sensitivity', 10))
        ttk.Scale(settings_window, from_=1, to=20, variable=sensitivity_var, orient=tk.HORIZONTAL).grid(
            column=1, row=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        # Smoothing
        ttk.Label(settings_window, text="Smoothing:").grid(column=0, row=3, padx=10, pady=10, sticky=tk.W)
        smoothing_var = tk.DoubleVar(value=self.settings.get('smoothing', 0.7))
        ttk.Scale(settings_window, from_=0, to=1, variable=smoothing_var, orient=tk.HORIZONTAL).grid(
            column=1, row=3, padx=10, pady=10, sticky=tk.W+tk.E)
        
        # Autostart
        autostart_var = tk.BooleanVar(value=self.settings.get('autostart', False))
        ttk.Checkbutton(settings_window, text="Start on system boot", variable=autostart_var).grid(
            column=0, row=4, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Save button
        def save_settings_callback():
            self.settings['wake_word'] = wake_word_var.get()
            self.settings['sleep_word'] = sleep_word_var.get()
            self.settings['sensitivity'] = sensitivity_var.get()
            self.settings['smoothing'] = smoothing_var.get()
            self.settings['autostart'] = autostart_var.get()
            
            save_settings(self.settings)
            
            # Update autostart
            if autostart_var.get():
                setup_autostart(sys.executable)
                
            # Apply settings if assistant is running
            if self.assistant and hasattr(self.assistant, 'gesture_controller'):
                self.assistant.gesture_controller.sensitivity = sensitivity_var.get()
                self.assistant.gesture_controller.smoothing = smoothing_var.get()
                
            settings_window.destroy()
        
        ttk.Button(settings_window, text="Save", command=save_settings_callback).grid(
            column=0, row=5, columnspan=2, padx=10, pady=20)
        
        settings_window.mainloop()
        
    def show_macos_settings(self):
        import rumps
        
        # Create a simple dialog with rumps
        response = rumps.Window(
            title="Eye Mouse Assistant Settings",
            message="Enter settings (comma-separated):\nwake_word, sleep_word, sensitivity, smoothing, autostart (True/False)",
            default_text=f"{self.settings.get('wake_word', 'wake up')}, "
                         f"{self.settings.get('sleep_word', 'go to sleep')}, "
                         f"{self.settings.get('sensitivity', 10)}, "
                         f"{self.settings.get('smoothing', 0.7)}, "
                         f"{self.settings.get('autostart', False)}"
        ).run()
        
        if response.clicked:
            try:
                values = [v.strip() for v in response.text.split(',')]
                if len(values) >= 5:
                    self.settings['wake_word'] = values[0]
                    self.settings['sleep_word'] = values[1]
                    self.settings['sensitivity'] = float(values[2])
                    self.settings['smoothing'] = float(values[3])
                    self.settings['autostart'] = values[4].lower() == 'true'
                    
                    save_settings(self.settings)
                    
                    # Update autostart
                    if self.settings['autostart']:
                        setup_autostart(sys.executable)
                        
                    # Apply settings if assistant is running
                    if self.assistant and hasattr(self.assistant, 'gesture_controller'):
                        self.assistant.gesture_controller.sensitivity = self.settings['sensitivity']
                        self.assistant.gesture_controller.smoothing = self.settings['smoothing']
                        
            except Exception as e:
                logger.error(f"Error parsing settings: {e}")
                rumps.alert("Error", f"Invalid settings format: {e}")
    
    def show_linux_settings(self):
        # Create a simple GTK dialog
        dialog = Gtk.Dialog(
            title="Eye Mouse Assistant Settings",
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.set_default_size(400, 300)
        
        # Content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        
        # Wake word
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox1.pack_start(Gtk.Label("Wake Word:"), False, False, 0)
        wake_word_entry = Gtk.Entry()
        wake_word_entry.set_text(self.settings.get('wake_word', "wake up"))
        hbox1.pack_start(wake_word_entry, True, True, 0)
        content_area.pack_start(hbox1, False, False, 0)
        
        # Sleep word
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox2.pack_start(Gtk.Label("Sleep Word:"), False, False, 0)
        sleep_word_entry = Gtk.Entry()
        sleep_word_entry.set_text(self.settings.get('sleep_word', "go to sleep"))
        hbox2.pack_start(sleep_word_entry, True, True, 0)
        content_area.pack_start(hbox2, False, False, 0)
        
        # Sensitivity
        hbox3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox3.pack_start(Gtk.Label("Sensitivity:"), False, False, 0)
        sensitivity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 20, 1)
        sensitivity_scale.set_value(self.settings.get('sensitivity', 10))
        hbox3.pack_start(sensitivity_scale, True, True, 0)
        content_area.pack_start(hbox3, False, False, 0)
        
        # Smoothing
        hbox4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox4.pack_start(Gtk.Label("Smoothing:"), False, False, 0)
        smoothing_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        smoothing_scale.set_value(self.settings.get('smoothing', 0.7))
        hbox4.pack_start(smoothing_scale, True, True, 0)
        content_area.pack_start(hbox4, False, False, 0)
        
        # Autostart
        autostart_check = Gtk.CheckButton.new_with_label("Start on system boot")
        autostart_check.set_active(self.settings.get('autostart', False))
        content_area.pack_start(autostart_check, False, False, 0)
        
        # Add buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        
        # Show the dialog
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Save settings
            self.settings['wake_word'] = wake_word_entry.get_text()
            self.settings['sleep_word'] = sleep_word_entry.get_text()
            self.settings['sensitivity'] = sensitivity_scale.get_value()
            self.settings['smoothing'] = smoothing_scale.get_value()
            self.settings['autostart'] = autostart_check.get_active()
            
            save_settings(self.settings)
            
            # Update autostart
            if autostart_check.get_active():
                setup_autostart(sys.executable)
                
            # Apply settings if assistant is running
            if self.assistant and hasattr(self.assistant, 'gesture_controller'):
                self.assistant.gesture_controller.sensitivity = self.settings['sensitivity']
                self.assistant.gesture_controller.smoothing = self.settings['smoothing']
                
        dialog.destroy()
    
    def show_permission_dialog(self, permissions):
        """Show dialog for missing permissions"""
        system = platform.system()
        
        missing = []
        for perm, granted in permissions.items():
            if not granted:
                missing.append(perm)
        
        if not missing:
            return
        
        missing_str = ", ".join(missing)
        
        if system == "Windows":
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("Missing Permissions", 
                                  f"The following permissions are required: {missing_str}\n\n"
                                  f"Please grant them in your system settings.")
            root.destroy()
        
        elif system == "Darwin":
            import rumps
            rumps.alert("Missing Permissions", 
                       f"The following permissions are required: {missing_str}\n\n"
                       f"Please grant them in System Preferences > Security & Privacy.")
        
        else:
            dialog = Gtk.MessageDialog(
                transient_for=None,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Missing Permissions"
            )
            dialog.format_secondary_text(
                f"The following permissions are required: {missing_str}\n\n"
                f"Please grant them in your system settings."
            )
            dialog.run()
            dialog.destroy()
    
    def exit_app(self, *args):
        logger.info("Exiting application")
        
        # Stop the assistant if running
        if self.assistant:
            self.stop_assistant()
        
        # Exit based on platform
        system = platform.system()
        if system == "Windows":
            self.tray_icon.stop()
        elif system == "Darwin":
            pass  # rumps.quit_application() is called in the menu handler
        else:  # Linux
            Gtk.main_quit()
        
        sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app = SystemTrayApp()