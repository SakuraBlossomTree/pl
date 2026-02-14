"""Cross-platform keyboard input handling."""
import sys
import select
import threading
import time
import logging
from typing import Callable, Optional


class KeyboardHandler:
    """Handle keyboard input in a cross-platform way."""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._windows_mode = sys.platform == "win32"
    
    def start(self):
        """Start the keyboard handler."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the keyboard handler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _run(self):
        """Main input loop."""
        if self._windows_mode:
            self._run_windows()
        else:
            self._run_unix()
    
    def _run_unix(self):
        """Run on Unix-like systems."""
        try:
            import termios
            import tty
            
            # Save terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            
            # Set to raw mode
            tty.setcbreak(sys.stdin.fileno())
            
            try:
                while self.running:
                    # Check for input with timeout
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        mapped_key = self._map_key(key)
                        if mapped_key:
                            self.callback(mapped_key)
                    
                    time.sleep(0.01)
                    
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
        except Exception as e:
            print(f"Keyboard handler error: {e}")
    
    def _run_windows(self):
        """Run on Windows."""
        try:
            import msvcrt
            
            while self.running:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    
                    # Debug: print raw key codes (disabled)
                    # print(f"[DEBUG] Raw key: {key!r}", flush=True)
                    
                    # Handle special keys
                    if key == b'\x00' or key == b'\xe0':
                        # Extended key
                        key = msvcrt.getch()
                        mapped_key = self._map_windows_special(key)
                    else:
                        try:
                            mapped_key = self._map_key(key.decode('utf-8'))
                        except:
                            mapped_key = None
                    
                    if mapped_key:
                        logging.debug(f"Key pressed: {mapped_key}")
                        self.callback(mapped_key)
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Keyboard handler error: {e}")
    
    def _map_windows_special(self, key: bytes) -> Optional[str]:
        """Map Windows special keys."""
        key_map = {
            b'H': 'up',
            b'P': 'down',
            b'K': 'left',
            b'M': 'right',
        }
        return key_map.get(key)
    
    def _map_key(self, key: str) -> Optional[str]:
        """Map a key to a standardized name."""
        # Control characters
        if key == '\x03':  # Ctrl+C
            return 'ctrl+c'
        elif key == '\x04':  # Ctrl+D
            return 'ctrl+d'
        elif key == '\x08':  # Backspace (Windows)
            return 'backspace'
        elif key == '\x7f':  # Backspace (Unix)
            return 'backspace'
        elif key == '\x1b':  # Escape
            return 'esc'
        elif key == '\r' or key == '\n':  # Enter
            return 'enter'
        elif key == '\t':  # Tab
            return 'tab'
        elif key == ' ':
            return 'space'
        
        # Escape sequences for arrow keys (Unix)
        if key == '\x1b':
            # Read the rest of the sequence
            import select
            if select.select([sys.stdin], [], [], 0.05)[0]:
                seq = sys.stdin.read(2)
                if seq == '[A':
                    return 'up'
                elif seq == '[B':
                    return 'down'
                elif seq == '[C':
                    return 'right'
                elif seq == '[D':
                    return 'left'
            return 'esc'
        
        # Printable characters
        if key.isprintable():
            return key.lower()
        
        return None


def get_key() -> Optional[str]:
    """Get a single key press (blocking)."""
    if sys.platform == "win32":
        try:
            import msvcrt
            key = msvcrt.getch()
            
            if key == b'\x00' or key == b'\xe0':
                key = msvcrt.getch()
                key_map = {
                    b'H': 'up',
                    b'P': 'down',
                    b'K': 'left',
                    b'M': 'right',
                }
                return key_map.get(key)
            
            # Control characters
            if key == b'\x03':
                return 'ctrl+c'
            elif key == b'\x04':
                return 'ctrl+d'
            elif key == b'\x08':
                return 'backspace'
            elif key == b'\r':
                return 'enter'
            elif key == b'\t':
                return 'tab'
            elif key == b' ':
                return 'space'
            
            try:
                return key.decode('utf-8').lower()
            except:
                return None
                
        except:
            return None
    else:
        try:
            import termios
            import tty
            
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            
            try:
                key = sys.stdin.read(1)
                
                if key == '\x03':
                    return 'ctrl+c'
                elif key == '\x04':
                    return 'ctrl+d'
                elif key == '\x1b':
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        seq = sys.stdin.read(2)
                        if seq == '[A':
                            return 'up'
                        elif seq == '[B':
                            return 'down'
                        elif seq == '[C':
                            return 'right'
                        elif seq == '[D':
                            return 'left'
                    return 'esc'
                elif key == '\x7f':
                    return 'backspace'
                elif key == '\r':
                    return 'enter'
                elif key == '\t':
                    return 'tab'
                elif key == ' ':
                    return 'space'
                elif key.isprintable():
                    return key.lower()
                    
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
        except:
            return None
    
    return None
