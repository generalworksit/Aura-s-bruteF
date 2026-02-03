#!/usr/bin/env python3
"""
Aura's Bruter - Banner Display
Uses Rich components exclusively for perfect alignment
Simple ASCII art that works in all terminals
"""

import time
import sys
import shutil
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.box import HEAVY, ROUNDED

console = Console()

# Simple ASCII banner using basic characters (no Unicode blocks)
BANNER_SIMPLE = r"""
    _   _   _ ____      _   _ ____  
   / \ | | | |  _ \    / \ ( ___) 
  / _ \| | | | |_) |  / _ \ \___ \ 
 / ___ \ |_| |  _ <  / ___ \ ___) |
/_/   \_\___/|_| \_\/_/   \_\____/ 
 ____  ____  _   _ _____ _____ ____  
| __ )|  _ \| | | |_   _| ____|  _ \ 
|  _ \| |_) | | | | | | |  _| | |_) |
| |_) |  _ <| |_| | | | | |___|  _ < 
|____/|_| \_\\___/  |_| |_____|_| \_\
"""

# Alternative simpler banner
BANNER_TEXT = """
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

# Rainbow colors for animation
RAINBOW = ["red", "yellow", "green", "cyan", "blue", "magenta"]

# Gradient colors
GRADIENT = ["cyan", "deep_sky_blue1", "dodger_blue1", "blue", "medium_purple", "magenta"]


def clear_screen():
    """Clear terminal screen."""
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="", flush=True)
    else:
        import os
        os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width() -> int:
    """Get terminal width safely."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def check_terminal(min_width: int = 60) -> bool:
    """Check if terminal is wide enough."""
    width = get_terminal_width()
    if width < min_width:
        console.print(f"[yellow]Terminal too narrow ({width} cols). Need at least {min_width}.[/yellow]")
        return False
    return True


def create_banner_text(use_colors: bool = True, color_offset: int = 0) -> Text:
    """Create banner as Rich Text with gradient colors."""
    lines = BANNER_TEXT.strip().split('\n')
    result = Text()
    
    for i, line in enumerate(lines):
        if use_colors:
            color_idx = (i + color_offset) % len(GRADIENT)
            result.append(line, style=GRADIENT[color_idx])
        else:
            result.append(line)
        result.append("\n")
    
    return result


def animate_banner(duration: float = 1.5, fps: int = 8):
    """Animate banner with color cycling using Rich."""
    if not check_terminal(60):
        return
    
    console.show_cursor(False)
    frame_delay = 1.0 / fps
    total_frames = int(duration * fps)
    
    try:
        for frame in range(total_frames):
            clear_screen()
            
            # Create animated banner
            banner = create_banner_text(use_colors=True, color_offset=frame)
            
            # Add info below banner
            banner.append("\n")
            
            color = RAINBOW[frame % len(RAINBOW)]
            banner.append("Multi-Protocol Brute Force Security Testing Tool\n", style=f"bold {color}")
            banner.append("[ SSH | FTP | Telnet ]\n", style=color)
            banner.append("Version 1.0.0\n", style="dim")
            
            # Use Rich Panel - handles alignment automatically
            panel = Panel(
                Align.center(banner),
                border_style=color,
                box=HEAVY,
                padding=(0, 2)
            )
            console.print(panel)
            
            time.sleep(frame_delay)
    finally:
        console.show_cursor(True)


def display_static_banner():
    """Display static banner with gradient using Rich Panel."""
    banner = create_banner_text(use_colors=True)
    
    # Add info
    banner.append("\n")
    banner.append("Multi-Protocol Brute Force Security Testing Tool\n", style="bold cyan")
    banner.append("[ SSH | FTP | Telnet ]\n", style="magenta")
    banner.append("Version 1.0.0\n", style="dim")
    banner.append("Created by generalworksit", style="italic yellow")
    
    panel = Panel(
        Align.center(banner),
        border_style="cyan",
        box=HEAVY,
        padding=(0, 2)
    )
    console.print(Align.center(panel))


def display_disclaimer():
    """Display legal disclaimer using Rich Panel."""
    content = Text()
    content.append("LEGAL DISCLAIMER\n\n", style="bold red")
    content.append("This tool is intended for ", style="yellow")
    content.append("EDUCATIONAL PURPOSES ONLY", style="bold yellow underline")
    content.append(".\n\n", style="yellow")
    
    content.append("- Only use on systems you OWN or have EXPLICIT PERMISSION to test\n", style="white")
    content.append("- Unauthorized access to computer systems is ILLEGAL\n", style="white")
    content.append("- The author is NOT responsible for any misuse of this tool\n", style="white")
    content.append("- You are solely responsible for your actions\n\n", style="white")
    
    content.append("By continuing, you agree to use this tool responsibly and legally.", style="dim")
    
    panel = Panel(
        Align.center(content),
        title="[red]Terms of Use[/red]",
        title_align="center",
        border_style="red",
        box=ROUNDED,
        padding=(1, 3)
    )
    console.print(Align.center(panel))


def show_welcome(animate: bool = True):
    """Main entry point for welcome screen."""
    clear_screen()
    
    if animate and check_terminal(60):
        animate_banner(duration=1.2)
        clear_screen()
    
    display_static_banner()
    console.print()
    display_disclaimer()
    console.print()


if __name__ == "__main__":
    show_welcome(animate=True)
