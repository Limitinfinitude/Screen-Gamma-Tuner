import ctypes
from ctypes import wintypes
import atexit  # Optional: used for global restore registration, but already handled in GUI

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
GAMMA_RAMP_SIZE = 256

class GammaRamp(ctypes.Structure):
    _fields_ = [
        ("red", wintypes.USHORT * GAMMA_RAMP_SIZE),
        ("green", wintypes.USHORT * GAMMA_RAMP_SIZE),
        ("blue", wintypes.USHORT * GAMMA_RAMP_SIZE),
    ]

def get_gamma_ramp():
    """Get the current gamma ramp"""
    hdc = user32.GetDC(0)
    ramp = GammaRamp()
    gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    user32.ReleaseDC(0, hdc)
    return ramp

def set_gamma_ramp(ramp):
    """Set the gamma ramp (for single or primary screen)"""
    hdc = user32.GetDC(0)
    success = gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    user32.ReleaseDC(0, hdc)
    return success

def set_gamma_ramp_all_screens(gamma=1.0, brightness=0.0, contrast=1.0):
    """Set the gamma ramp for all screens (simplified, works for the primary screen; multi-screen support requires EnumDisplayDevices)"""
    original = get_gamma_ramp()
    for i in range(GAMMA_RAMP_SIZE):
        normalized = i / 255.0
        gamma_corrected = normalized ** (1.0 / max(gamma, 0.1))
        # Normalize brightness: -1 to 1 shifts the value, with a 30% range for realism
        val = gamma_corrected + brightness * 0.3
        val = max(0.0, min(1.0, val))
        # Contrast adjustment
        val = (val - 0.5) * contrast + 0.5
        val = max(0.0, min(1.0, val))
        val_16bit = int(val * 65535)
        original.red[i] = original.green[i] = original.blue[i] = wintypes.USHORT(val_16bit)
    return set_gamma_ramp(original)

def backup_and_restore(original_ramp):
    """Register the restore function (used with atexit)"""
    def restore():
        set_gamma_ramp(original_ramp)
    atexit.register(restore)
