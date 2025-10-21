import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import math
import sys  # For global exception handling
import signal  # For signal handling on forced termination
import atexit  # Enhanced: Ensure atexit works with signals
from PIL import Image, ImageDraw  # Required: pip install pillow
import pystray  # Required: pip install pystray
from screengamma import get_gamma_ramp, set_gamma_ramp, backup_and_restore, set_gamma_ramp_all_screens

CONFIG_FILE = "config.json"


class ScreenGammaGUI:
    def __init__(self):
        self.original_ramp = get_gamma_ramp()  # Backup original values
        backup_and_restore(self.original_ramp)  # Register global restore (on normal exit)

        # Enhanced: Global exception handler to ensure recovery on crash
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._crash_handler

        # Enhanced: Signal handlers for forced termination (e.g., PyCharm stop button sends SIGINT)
        self._setup_signal_handlers()

        # Enhanced: Additional atexit for extra safety
        atexit.register(self._atexit_restore)

        self.root = tk.Tk()
        self.root.title("ScreenGamma Tuner")
        self.root.geometry("420x460")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Variables
        self.gamma_var = tk.DoubleVar(value=1.0)
        self.brightness_var = tk.DoubleVar(value=0.0)
        self.contrast_var = tk.DoubleVar(value=1.0)

        # Configuration (only one)
        self.config = self.load_config()

        self.setup_ui()

        # Apply configuration on startup (after UI initialization)
        self.apply_config()

        # Initial update (apply config values)
        self.update_gamma()

        # System tray
        self.setup_tray()

    def _setup_signal_handlers(self):
        """Setup signal handlers for SIGINT/SIGTERM to restore on forced exit"""
        def signal_handler(sig, frame):
            self._restore_gamma()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _atexit_restore(self):
        """Additional atexit handler for restore"""
        self._restore_gamma()

    def _restore_gamma(self):
        """Centralized restore function"""
        try:
            set_gamma_ramp(self.original_ramp)
        except Exception:
            pass  # Ignore failed recovery

    def _crash_handler(self, exc_type, exc_value, exc_traceback):
        """Restore original values on crash"""
        self._restore_gamma()
        # Call original hook to print error
        self._original_excepthook(exc_type, exc_value, exc_traceback)

    def load_config(self):
        """Load a single configuration from JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to load configuration: {e}\nUsing default configuration.")
        return {'gamma': 1.0, 'brightness': 0.0, 'contrast': 1.0}

    def save_config(self):
        """Save configuration to JSON"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def save_to_config(self):
        """Save current values to configuration"""
        self.config = {
            'gamma': self.gamma_var.get(),
            'brightness': self.brightness_var.get(),
            'contrast': self.contrast_var.get()
        }
        self.save_config()
        if hasattr(self, 'status'):
            self.status.config(text="Configuration saved", fg="blue")

    def load_from_config(self):
        """Load configuration and apply (thread-safe)"""
        # Ensure execution in main thread
        def _load():
            self.gamma_var.set(self.config['gamma'])
            self.brightness_var.set(self.config['brightness'])
            self.contrast_var.set(self.config['contrast'])
            self.update_gamma()
            if hasattr(self, 'status'):
                self.status.config(text="Configuration loaded", fg="blue")

        self.root.after(0, _load)

    def apply_config(self):
        """Apply configuration (set variables only, no update; for startup)"""
        self.gamma_var.set(self.config['gamma'])
        self.brightness_var.set(self.config['brightness'])
        self.contrast_var.set(self.config['contrast'])

    def on_closing(self):
        # Minimize to tray instead of closing
        self.root.withdraw()
        if hasattr(self, 'icon'):
            self.icon.visible = True
            # Show balloon tip
            self.root.after_idle(lambda: self.icon.notify("Window minimized to tray", "ScreenGamma Tuner"))

    def setup_tray(self):
        """Setup system tray (simple gear icon + left-click activation)"""
        # Create a simple gear icon
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        # Gear body: circle
        draw.ellipse([16, 16, 48, 48], fill='gray')
        # Add teeth: radial lines
        for i in range(8):
            angle = i * 45 * math.pi / 180
            x1 = 32 + 20 * math.cos(angle)
            y1 = 32 + 20 * math.sin(angle)
            x2 = 32 + 25 * math.cos(angle)
            y2 = 32 + 25 * math.sin(angle)
            draw.line((x1, y1, x2, y2), fill='black', width=2)

        menu = pystray.Menu(
            pystray.MenuItem("📥 Load Configuration", self._tray_callback(self.load_from_config)),
            pystray.MenuItem("🔄 Reset", self._tray_callback(self.reset)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📱 Show Window", self._tray_callback(self.show_window), default=True),  # Default: left-click to show window
            pystray.MenuItem("❌ Quit", self._tray_callback(self.quit_app))
        )
        self.icon = pystray.Icon("ScreenGamma", image, "ScreenGamma Tuner", menu)

        # Run tray in a separate thread
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def _tray_callback(self, func):
        """Tray menu callback wrapper: ensure execution in main thread"""
        def wrapper(icon, item):
            self.root.after(0, func)

        return wrapper

    def show_window(self):
        """Show the window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        """Quit the app completely (restore original values)"""
        self.save_to_config()  # Save current configuration
        self._restore_gamma()  # Force restore
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.quit()

    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="ScreenGamma Tuner", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        # Main frame
        frame = ttk.Frame(self.root, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Slider configurations
        sliders_config = [
            ("Gamma (0.3-4.0)", self.gamma_var, 0.3, 4.0, 0.1),
            ("Brightness (-1~1)", self.brightness_var, -1.0, 1.0, 0.1),
            ("Contrast (0.1-3.0)", self.contrast_var, 0.1, 3.0, 0.1)
        ]

        for label_text, var, from_val, to_val, res in sliders_config:
            slider_frame = self.create_slider_frame(frame, label_text, var, from_val, to_val, res)
            slider_frame.pack(fill=tk.X, pady=5)

        # Reset button
        reset_btn = tk.Button(frame, text="Reset", bg="#81A1C1", fg="white",
                              font=("Arial", 11, "bold"), command=self.reset, width=12, pady=5)
        reset_btn.pack(pady=10)

        # Configuration buttons (only one)
        config_frame = tk.Frame(frame)
        config_frame.pack(pady=5)
        tk.Button(config_frame, text="Save", font=("Arial", 10, "bold"),
                  command=self.save_to_config, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(config_frame, text="Load", font=("Arial", 10, "bold"),
                  command=self.load_from_config, width=15).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status = tk.Label(frame, text="Ready", fg="green", font=("Arial", 10))
        self.status.pack(pady=10)

    def create_slider_frame(self, parent, label_text, var, from_val, to_val, res):
        """Create slider + increment/decrement button frame"""
        frame = ttk.Frame(parent)
        tk.Label(frame, text=label_text, font=("Arial", 10)).pack(anchor="w")

        control_frame = tk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=2)

        # Slider
        scale = tk.Scale(control_frame, from_=from_val, to=to_val, resolution=res,
                         variable=var, orient=tk.HORIZONTAL, command=self.update_gamma, length=320)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Increment/decrement buttons
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="+", font=("Arial", 10, "bold"), width=2,
                  command=lambda: self.adjust_value(var, 0.1, from_val, to_val)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="-", font=("Arial", 10, "bold"), width=2,
                  command=lambda: self.adjust_value(var, -0.1, from_val, to_val)).pack(side=tk.LEFT, padx=2)

        return frame

    def adjust_value(self, var, delta, min_val, max_val):
        """Adjust value using increment/decrement buttons (generic)"""
        value = var.get() + delta
        value = max(min_val, min(max_val, value))
        var.set(value)
        self.update_gamma()

    def reset(self):
        """Reset to default (thread-safe)"""
        # Ensure execution in main thread
        def _reset():
            self.gamma_var.set(1.0)
            self.brightness_var.set(0.0)
            self.contrast_var.set(1.0)
            self.update_gamma()
            if hasattr(self, 'status'):
                self.status.config(text="Reset to Default!", fg="orange")

        self.root.after(0, _reset)

    def update_gamma(self, *args):
        """Update gamma (with exception handling)"""
        try:
            gamma = self.gamma_var.get()
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()
            set_gamma_ramp_all_screens(gamma, brightness, contrast)  # Call without checking success
            if hasattr(self, 'status'):
                self.status.config(text=f"Live: G={gamma:.1f} B={brightness:.1f} C={contrast:.1f}", fg="green")
        except Exception as e:
            if hasattr(self, 'status'):
                self.status.config(text=f"❌ Update failed: {str(e)}", fg="red")
            else:
                # Ignore on startup, UI not ready
                pass

    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            # If mainloop crashes, restore
            self._restore_gamma()
            raise  # Re-raise to print error
        finally:
            # Ensure recovery
            self._restore_gamma()


if __name__ == "__main__":
    app = ScreenGammaGUI()
    app.run()