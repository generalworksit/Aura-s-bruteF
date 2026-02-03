#!/usr/bin/env python3
"""
Aura's Bruter - Screen Manager
Clean terminal rendering with proper screen transitions
"""

import os
import sys
from rich.console import Console

console = Console()


def clear_screen():
    """
    Clear the terminal screen (cross-platform).
    Uses ANSI escape codes first, falls back to OS commands.
    """
    # Try ANSI escape codes first (works in most modern terminals)
    if sys.stdout.isatty():
        # \033[2J - Clear entire screen
        # \033[H - Move cursor to home position (top-left)
        print("\033[2J\033[H", end="", flush=True)
    else:
        # Fallback to OS-specific commands
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')


def render_screen(content_func, *args, **kwargs):
    """
    Render a screen by clearing first, then calling the content function.
    
    Args:
        content_func: Function that renders the screen content
        *args, **kwargs: Arguments to pass to content_func
    
    Returns:
        Whatever content_func returns
    """
    clear_screen()
    return content_func(*args, **kwargs)


class ScreenManager:
    """
    Manages screen transitions for a clean TUI experience.
    
    Usage:
        sm = ScreenManager()
        sm.render(render_main_menu)
        sm.render(render_protocol_menu, protocol="ssh")
    """
    
    def __init__(self):
        self.console = Console()
        self.history = []  # Track screen history for back navigation
    
    def clear(self):
        """Clear the terminal screen."""
        clear_screen()
    
    def render(self, screen_func, *args, push_history=True, **kwargs):
        """
        Clear screen and render new content.
        
        Args:
            screen_func: Function to render the screen
            *args, **kwargs: Arguments for screen_func
            push_history: Whether to add this screen to history
        
        Returns:
            Result from screen_func
        """
        self.clear()
        
        if push_history:
            self.history.append((screen_func, args, kwargs))
        
        return screen_func(*args, **kwargs)
    
    def go_back(self):
        """Go back to previous screen."""
        if len(self.history) > 1:
            self.history.pop()  # Remove current
            prev_func, prev_args, prev_kwargs = self.history[-1]
            self.clear()
            return prev_func(*prev_args, **prev_kwargs)
        return None
    
    def reset(self):
        """Clear history and screen."""
        self.history.clear()
        self.clear()


# Global screen manager instance
_screen_manager = None


def get_screen_manager() -> ScreenManager:
    """Get the global screen manager instance."""
    global _screen_manager
    if _screen_manager is None:
        _screen_manager = ScreenManager()
    return _screen_manager


if __name__ == "__main__":
    # Demo
    console.print("[yellow]Screen Manager Demo[/yellow]")
    console.print("[dim]Provides clean screen transitions[/dim]")
