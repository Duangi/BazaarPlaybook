import win32gui
import win32ui
import win32con
import ctypes
import os
from ctypes import windll, wintypes

def is_focus_valid(game_title="The Bazaar"):
    """
    Returns True if the foreground window is either:
    1. The Game (title match)
    2. The Application itself (Process ID match)
    """
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return False
        
    # 1. Title Check
    text = win32gui.GetWindowText(hwnd)
    if game_title.lower() in text.lower():
        return True
        
    # 2. PID Check (Is it us?)
    try:
        pid = ctypes.c_ulong()
        windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            return True
    except Exception:
        pass
        
    return False

def get_window_rect(window_title, exact_match=False):
    """
    Finds a window by title and returns its rectangle (left, top, width, height).
    """
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd and not exact_match:
        # Try fuzzy match
        def callback(h, ctx):
            text = win32gui.GetWindowText(h)
            if window_title.lower() in text.lower():
                ctx.append(h)
        found = []
        win32gui.EnumWindows(callback, found)
        if found:
            hwnd = found[0]

    if not hwnd:
        return None

    # GetWindowRect returns the bounding box including shadow/border
    # GetClientRect returns the inner area (0, 0, width, height)
    # We usually want ClientRect offset to Screen coordinates for capturing the game content only.
    
    rect = win32gui.GetClientRect(hwnd)
    # rect is (left, top, right, bottom) where left=0, top=0
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    
    # Map client point (0,0) to screen point
    pt = win32gui.ClientToScreen(hwnd, (0, 0))
    x, y = pt
    
    return (x, y, w, h)

def get_mouse_pos_relative(window_x, window_y):
    """
    Returns mouse position relative to the given window coordinates.
    """
    pt = wintypes.POINT()
    windll.user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x - window_x, pt.y - window_y)

def is_window_foreground(window_title):
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return False
    text = win32gui.GetWindowText(hwnd)
    return window_title.lower() in text.lower()

def get_foreground_window_title():
    """Returns the title of the foreground window."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return ""
    return win32gui.GetWindowText(hwnd)

def restore_focus_to_game(game_title="The Bazaar"):
    """
    Attempts to restore focus to a window with the given title.
    """
    try:
        hwnd = win32gui.FindWindow(None, game_title)
        if not hwnd:
            # Try fuzzy match
            def callback(h, ctx):
                text = win32gui.GetWindowText(h)
                if game_title.lower() in text.lower():
                    ctx.append(h)
            found = []
            win32gui.EnumWindows(callback, found)
            if found:
                hwnd = found[0]
        
        if hwnd:
            # Using win32gui.SetForegroundWindow can sometimes fail if the calling thread 
            # doesn't have permission. Attaching thread input can help, or simple try-catch.
            try:
                # Basic attempt
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                # If valid window but failed, sometimes need a little push (Alt key trick or AttachThreadInput)
                # For simplicity, we just log/pass. 
                pass
            return True
    
    except Exception as e:
        print(f"Failed to restore focus: {e}")
    return False


def is_process_running(process_name="TheBazaar.exe"):
    """
    Check if a process is currently running.
    Args:
        process_name: The name of the process (e.g., "TheBazaar.exe")
    Returns:
        True if the process is running, False otherwise.
    """
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                return True
        return False
    except ImportError:
        # If psutil is not installed, fallback to checking window existence
        # This is less reliable but works as a backup
        return get_window_rect("The Bazaar") is not None
    except Exception:
        return False
