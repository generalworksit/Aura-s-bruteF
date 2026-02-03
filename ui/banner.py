#!/usr/bin/env python3
"""
Aura's Bruter - RGB Animated Banner
Beautiful terminal banner with rainbow animation effect
Uses Rich for proper alignment and box rendering
"""

import time
import sys
import shutil
import re
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.box import DOUBLE, ROUNDED

console = Console()

# ASCII art without box characters - let Rich handle the box
BANNER_ASCII = r"""
     █████╗ ██╗   ██╗██████╗  █████╗ ███████╗
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔════╝
    ███████║██║   ██║██████╔╝███████║███████╗
    ██╔══██║██║   ██║██╔══██╗██╔══██║╚════██║
    ██║  ██║╚██████╔╝██║  ██║██║  ██║███████║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

    ██████╗ ██████╗ ██╗   ██╗████████╗███████╗██████╗
    ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
    ██████╔╝██████╔╝██║   ██║   ██║   █████╗  ██████╔╝
    ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ██╔══██╗
    ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║
    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
"""

# Subtitle and version info (no emojis inside box for alignment)
SUBTITLE_TEXT = "Multi-Protocol Brute Force Security Testing Tool"
PROTOCOLS_TEXT = "[ SSH | FTP | Telnet ]"
VERSION_TEXT = "Version 1.0.0"
AUTHOR_TEXT = "Created by generalworksit"

# RGB color palette for rainbow effect
RAINBOW_COLORS = [
    "#FF0000", "#FF4500", "#FF8C00", "#FFD700", "#ADFF2F", "#00FF00",
    "#00FA9A", "#00FFFF", "#1E90FF", "#9370DB", "#FF00FF", "#FF1493",
]

# Gradient for static banner
GRADIENT_COLORS = [
    "#00FFFF", "#00E5FF", "#00CCFF", "#00B2FF", "#0099FF",
    "#007FFF", "#0066FF", "#1A4DFF", "#3333FF", "#4D1AFF",
    "#6600FF", "#7F00FF", "#9900FF", "#B200FF", "#CC00FF",
]


def clear_screen():
    """Clear the terminal screen."""
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="", flush=True)
    else:
        import os
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')


def get_terminal_width() -> int:
    """Get current terminal width."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def check_terminal_width(min_width: int = 70) -> bool:
    """Check if terminal is wide enough."""
    return get_terminal_width() >= min_width


def get_rainbow_text(text: str, offset: int = 0) -> Text:
    """Create rainbow-colored text with offset for animation."""
    result = Text()
    color_count = len(RAINBOW_COLORS)
    
    for i, char in enumerate(text):
        color_idx = (i + offset) % color_count
        result.append(char, style=RAINBOW_COLORS[color_idx])
    
    return result


def get_gradient_text(text: str, start_color_idx: int = 0) -> Text:
    """Create gradient-colored text."""
    result = Text()
    color_count = len(GRADIENT_COLORS)
    
    for i, char in enumerate(text):
        color_idx = (i + start_color_idx) % color_count
        result.append(char, style=GRADIENT_COLORS[color_idx])
    
    return result


def animate_banner(duration: float = 1.5, fps: int = 12):
    """
    Animate the banner with flowing rainbow colors.
    Uses Rich Panel for proper alignment.
    """
    lines = BANNER_ASCII.strip().split('\n')
    frame_delay = 1.0 / fps
    total_frames = int(duration * fps)
    
    # Check terminal width
    if not check_terminal_width(70):
        console.print("[yellow]Terminal too narrow for animation. Increase to 70+ columns.[/yellow]")
        return
    
    # Hide cursor during animation
    console.show_cursor(False)
    
    try:
        for frame in range(total_frames):
            # Clear and move to top for each frame
            clear_screen()
            
            # Create animated ASCII art text
            animated_text = Text()
            for line_idx, line in enumerate(lines):
                rainbow_line = get_rainbow_text(line, offset=frame + line_idx * 2)
                animated_text.append(rainbow_line)
                animated_text.append("\n")
            
            # Add subtitle with animation
            animated_text.append("\n")
            animated_text.append(get_rainbow_text(f"  {SUBTITLE_TEXT}  ", offset=frame))
            animated_text.append("\n")
            animated_text.append(get_rainbow_text(f"        {PROTOCOLS_TEXT}        ", offset=frame + 5))
            animated_text.append("\n")
            animated_text.append(get_rainbow_text(f"          {VERSION_TEXT}          ", offset=frame + 10))
            
            # Use Rich Panel for perfect box alignment
            panel = Panel(
                Align.center(animated_text),
                border_style=RAINBOW_COLORS[frame % len(RAINBOW_COLORS)],
                box=DOUBLE,
                padding=(0, 1)
            )
            
            console.print(panel)
            time.sleep(frame_delay)
        
    finally:
        console.show_cursor(True)


def display_static_banner():
    """Display the final static banner with a nice gradient using Rich Panel."""
    lines = BANNER_ASCII.strip().split('\n')
    
    # Build gradient ASCII art
    result = Text()
    for line_idx, line in enumerate(lines):
        color_idx = min(line_idx, len(GRADIENT_COLORS) - 1)
        result.append(line + "\n", style=GRADIENT_COLORS[color_idx])
    
    # Add subtitle info
    result.append("\n", style="dim")
    result.append(f"  {SUBTITLE_TEXT}  \n", style="bold cyan")
    result.append(f"        {PROTOCOLS_TEXT}        \n", style="magenta")
    result.append(f"          {VERSION_TEXT}          \n", style="dim white")
    result.append(f"       {AUTHOR_TEXT}       ", style="dim italic yellow")
    
    # Create panel with Rich (handles alignment perfectly)
    panel = Panel(
        Align.center(result),
        border_style="cyan",
        box=DOUBLE,
        padding=(0, 1)
    )
    
    console.print(Align.center(panel))


def display_disclaimer():
    """Display legal disclaimer using Rich Panel for perfect alignment."""
    # Build disclaimer content without emojis in title for alignment
    disclaimer_content = Text()
    disclaimer_content.append("LEGAL DISCLAIMER\n\n", style="bold red")
    disclaimer_content.append("This tool is intended for ", style="yellow")
    disclaimer_content.append("EDUCATIONAL PURPOSES ONLY", style="bold yellow")
    disclaimer_content.append(".\n\n", style="yellow")
    
    disclaimer_content.append("• Only use on systems you OWN or have EXPLICIT PERMISSION to test\n", style="white")
    disclaimer_content.append("• Unauthorized access to computer systems is ILLEGAL\n", style="white")
    disclaimer_content.append("• The author is NOT responsible for any misuse of this tool\n", style="white")
    disclaimer_content.append("• You are solely responsible for your actions\n\n", style="white")
    
    disclaimer_content.append("By continuing, you agree to use this tool responsibly and legally.", style="dim")
    
    # Use Rich Panel for perfect box
    panel = Panel(
        Align.center(disclaimer_content),
        title="Terms of Use",
        title_align="center",
        border_style="red",
        box=ROUNDED,
        padding=(1, 2)
    )
    
    console.print(Align.center(panel))


def render_welcome_screen(animate: bool = True):
    """
    Render the complete welcome screen.
    Handles animation, then clears and shows static banner + disclaimer.
    """
    if animate and check_terminal_width(70):
        # Run animation
        animate_banner(duration=1.5)
        # Clear after animation
        clear_screen()
    
    # Show static banner
    display_static_banner()
    console.print()
    
    # Show disclaimer
    display_disclaimer()
    console.print()


def show_welcome(animate: bool = True):
    """
    Show the complete welcome screen with banner and disclaimer.
    This is the main entry point for the welcome flow.
    """
    clear_screen()
    render_welcome_screen(animate=animate)


if __name__ == "__main__":
    # Demo the banner
    show_welcome(animate=True)
