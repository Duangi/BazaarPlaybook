import win32gui
import ctypes
import os
from ctypes import windll, wintypes
from typing import Optional, Tuple
from loguru import logger

from platforms.interfaces.window import WindowManager


class WindowsWindowManager(WindowManager):
    """Windows 平台窗口管理器实现"""
    
    def is_focus_valid(self, game_title: str = "The Bazaar") -> bool:
        """
        Returns True if the foreground window is either:
        1. The Game (title match)
        2. The Application itself (Process ID match)
        """
        try:
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
        except Exception as e:
            logger.error(f"is_focus_valid error: {e}")
            return False

    def get_window_rect(self, window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
        """
        Finds a window by title and returns its rectangle (left, top, width, height).
        """
        try:
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
        except Exception as e:
            logger.error(f"get_window_rect error: {e}")
            return None

    def get_mouse_pos_relative(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """
        Returns mouse position relative to the given window coordinates.
        """
        try:
            pt = wintypes.POINT()
            windll.user32.GetCursorPos(ctypes.byref(pt))
            return (pt.x - window_x, pt.y - window_y)
        except Exception as e:
            logger.error(f"get_mouse_pos_relative error: {e}")
            return (0, 0)

    def is_window_foreground(self, window_title: str) -> bool:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            text = win32gui.GetWindowText(hwnd)
            return window_title.lower() in text.lower()
        except Exception as e:
            logger.error(f"is_window_foreground error: {e}")
            return False

    def get_foreground_window_title(self) -> str:
        """Returns the title of the foreground window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return ""
            return win32gui.GetWindowText(hwnd)
        except Exception as e:
            logger.error(f"get_foreground_window_title error: {e}")
            return ""

    def restore_focus_to_game(self, game_title: str = "The Bazaar") -> bool:
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
            logger.error(f"restore_focus_to_game error: {e}")
        return False
