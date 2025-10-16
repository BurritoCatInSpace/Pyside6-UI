"""Console utility functions for controlling console window visibility."""

import sys
import platform
from typing import Optional


def hide_console_window() -> bool:
    """
    Hide the console window on Windows.
    
    Returns:
        bool: True if successfully hidden or not needed, False if hiding failed
    """
    if platform.system().lower() != "windows":
        return True  # Not needed on non-Windows platforms
    
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get console window handle
        console_window = kernel32.GetConsoleWindow()
        if console_window:
            # Hide the console window (SW_HIDE = 0)
            user32.ShowWindow(console_window, 0)
            return True
        return True  # No console window found, which is fine
    except Exception:
        # If hiding fails, return False but don't crash
        return False


def show_console_window() -> bool:
    """
    Show the console window on Windows.
    
    Returns:
        bool: True if successfully shown or not needed, False if showing failed
    """
    if platform.system().lower() != "windows":
        return True  # Not needed on non-Windows platforms
    
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get console window handle
        console_window = kernel32.GetConsoleWindow()
        if console_window:
            # Show the console window (SW_SHOW = 1)
            user32.ShowWindow(console_window, 1)
            return True
        return True  # No console window found, which is fine
    except Exception:
        # If showing fails, return False but don't crash
        return False


def set_console_visibility(show: bool) -> bool:
    """
    Set console window visibility based on SHOW_CONSOLE constant.
    
    Args:
        show (bool): True to show console, False to hide
        
    Returns:
        bool: True if operation succeeded or not needed, False if failed
    """
    if show:
        return show_console_window()
    else:
        return hide_console_window()


def apply_console_setting() -> bool:
    """
    Apply console visibility setting based on the SHOW_CONSOLE constant.
    
    Returns:
        bool: True if operation succeeded or not needed, False if failed
    """
    try:
        # Import SHOW_CONSOLE constant - try platforms first, fallback to GUI app constants
        try:
            from platforms.constants import SHOW_CONSOLE
        except ImportError:
            try:
                # If running from GUI directory, try parent directory
                import sys
                import os
                parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from platforms.constants import SHOW_CONSOLE
            except ImportError:
                from ..constants import SHOW_CONSOLE
        
        return set_console_visibility(SHOW_CONSOLE)
    except ImportError:
        # If import fails, default to hiding console (production behavior)
        return set_console_visibility(False)
