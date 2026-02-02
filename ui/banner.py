#!/usr/bin/env python3
"""
Aura's Bruter - RGB Animated Banner
Beautiful terminal banner with rainbow animation effect
"""

import time
import sys
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

console = Console()

BANNER_ART = r"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     █████╗ ██╗   ██╗██████╗  █████╗ ███████╗                      ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔════╝                      ║
    ║    ███████║██║   ██║██████╔╝███████║███████╗                      ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══██║╚════██║                      ║
    ║    ██║  ██║╚██████╔╝██║  ██║██║  ██║███████║                      ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝                      ║
    ║                                                                   ║
    ║    ██████╗ ██████╗ ██╗   ██╗████████╗███████╗██████╗              ║
    ║    ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗             ║
    ║    ██████╔╝██████╔╝██║   ██║   ██║   █████╗  ██████╔╝             ║
    ║    ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ██╔══██╗             ║
    ║    ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║             ║
    ║    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝             ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║     🔐 Multi-Protocol Brute Force Security Testing Tool 🔐       ║
    ║                      [ SSH | FTP | Telnet ]                       ║
    ║                         Version 1.0.0                             ║
    ╚═══════════════════════════════════════════════════════════════════╝
"""

# RGB color palette for rainbow effect
RAINBOW_COLORS = [
    "#FF0000",  # Red
    "#FF4500",  # Orange Red
    "#FF8C00",  # Dark Orange
    "#FFD700",  # Gold
    "#ADFF2F",  # Green Yellow
    "#00FF00",  # Lime
    "#00FA9A",  # Medium Spring Green
    "#00FFFF",  # Cyan
    "#1E90FF",  # Dodger Blue
    "#9370DB",  # Medium Purple
    "#FF00FF",  # Magenta
    "#FF1493",  # Deep Pink
]

def get_rainbow_text(text: str, offset: int = 0) -> Text:
    """Create rainbow-colored text with offset for animation."""
    result = Text()
    color_count = len(RAINBOW_COLORS)
    
    for i, char in enumerate(text):
        color_idx = (i + offset) % color_count
        result.append(char, style=RAINBOW_COLORS[color_idx])
    
    return result


def animate_banner(duration: float = 2.0, fps: int = 15):
    """Animate the banner with flowing rainbow colors."""
    lines = BANNER_ART.strip().split('\n')
    frame_delay = 1.0 / fps
    total_frames = int(duration * fps)
    
    # Hide cursor during animation
    console.show_cursor(False)
    
    try:
        for frame in range(total_frames):
            # Clear screen and move to top
            console.clear()
            
            # Create animated text
            animated_text = Text()
            for line_idx, line in enumerate(lines):
                rainbow_line = get_rainbow_text(line, offset=frame + line_idx)
                animated_text.append(rainbow_line)
                animated_text.append("\n")
            
            # Center and display
            console.print(Align.center(animated_text))
            
            time.sleep(frame_delay)
        
        # Final static display with gradient
        display_static_banner()
        
    finally:
        console.show_cursor(True)


def display_static_banner():
    """Display the final static banner with a nice gradient."""
    console.clear()
    lines = BANNER_ART.strip().split('\n')
    
    # Create gradient from cyan to magenta
    gradient_colors = [
        "#00FFFF", "#00E5FF", "#00CCFF", "#00B2FF", "#0099FF",
        "#007FFF", "#0066FF", "#1A4DFF", "#3333FF", "#4D1AFF",
        "#6600FF", "#7F00FF", "#9900FF", "#B200FF", "#CC00FF",
        "#E500FF", "#FF00FF"
    ]
    
    result = Text()
    for line_idx, line in enumerate(lines):
        color_idx = min(line_idx, len(gradient_colors) - 1)
        result.append(line + "\n", style=gradient_colors[color_idx])
    
    console.print(Align.center(result))


def display_disclaimer():
    """Display legal disclaimer."""
    disclaimer = """
[bold red]⚠️  LEGAL DISCLAIMER  ⚠️[/bold red]

[yellow]This tool is intended for [bold]EDUCATIONAL PURPOSES ONLY[/bold].[/yellow]

[white]• Only use on systems you OWN or have EXPLICIT PERMISSION to test
• Unauthorized access to computer systems is ILLEGAL
• The author is NOT responsible for any misuse of this tool
• You are solely responsible for your actions[/white]

[dim]By continuing, you agree to use this tool responsibly and legally.[/dim]
"""
    
    panel = Panel(
        disclaimer,
        title="[bold red]📋 Terms of Use[/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(Align.center(panel))


def show_welcome(animate: bool = True):
    """Show the complete welcome screen with banner and disclaimer."""
    if animate:
        animate_banner(duration=1.5)
    else:
        display_static_banner()
    
    console.print()
    display_disclaimer()
    console.print()


if __name__ == "__main__":
    # Demo the banner
    show_welcome(animate=True)
