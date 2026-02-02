#!/usr/bin/env python3
"""
Aura's Bruter - Display Utilities
Progress bars, stats display, and formatting utilities
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align
from typing import Dict, Any
from datetime import timedelta
import time


console = Console()


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 0:
        return "Unknown"
    return str(timedelta(seconds=int(seconds)))


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def format_speed(speed: float) -> str:
    """Format speed as attempts/second."""
    return f"{speed:.1f}/sec"


def display_server_info(info: dict):
    """Display server information panel."""
    table = Table(show_header=False, border_style="cyan", box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Host", info.get("host", "N/A"))
    table.add_row("Port", str(info.get("port", "N/A")))
    
    if info.get("port_open"):
        table.add_row("Status", "[green]✓ Port Open[/green]")
    else:
        table.add_row("Status", "[red]✗ Port Closed[/red]")
    
    banner = info.get("banner") or info.get("welcome")
    if banner:
        # Truncate long banners
        if len(banner) > 50:
            banner = banner[:47] + "..."
        table.add_row("Banner", f"[dim]{banner}[/dim]")
    
    panel = Panel(table, title="[bold cyan]Server Info[/bold cyan]", border_style="cyan")
    console.print(panel)


def display_attack_config(config: dict):
    """Display attack configuration."""
    table = Table(show_header=False, border_style="yellow", box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in config.items():
        if isinstance(value, bool):
            value = "[green]Yes[/green]" if value else "[red]No[/red]"
        elif isinstance(value, dict):
            continue  # Skip nested dicts
        table.add_row(key.replace("_", " ").title(), str(value))
    
    panel = Panel(table, title="[bold yellow]Attack Config[/bold yellow]", border_style="yellow")
    console.print(panel)


def display_credentials_found(credentials: list):
    """Display found credentials in a nice table."""
    if not credentials:
        console.print("[dim]No credentials found yet.[/dim]")
        return
    
    table = Table(
        title="[bold green]🔓 Found Credentials[/bold green]",
        border_style="green"
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Username", style="cyan")
    table.add_column("Password", style="yellow")
    table.add_column("Found At", style="dim")
    
    for i, cred in enumerate(credentials, 1):
        table.add_row(
            str(i),
            cred.get("username", ""),
            cred.get("password", ""),
            cred.get("found_at", "")[:19] if cred.get("found_at") else ""
        )
    
    console.print(table)


def display_final_stats(stats: Dict[str, Any]):
    """Display final attack statistics."""
    console.print()
    
    # Create summary panel
    summary = Table(show_header=False, box=None, padding=(0, 1))
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="white")
    
    summary.add_row("Total Tested", format_number(stats.get("tested", 0)))
    summary.add_row("Successful", f"[bold green]{stats.get('successful', 0)}[/bold green]")
    summary.add_row("Failed", format_number(stats.get("failed", 0)))
    summary.add_row("Errors", f"[red]{stats.get('errors', 0)}[/red]")
    summary.add_row("Duration", format_duration(stats.get("elapsed", 0)))
    summary.add_row("Avg Speed", format_speed(stats.get("speed", 0)))
    
    panel = Panel(
        summary,
        title="[bold]Attack Summary[/bold]",
        border_style="cyan"
    )
    console.print(panel)


def display_help():
    """Display help information."""
    help_text = """
[bold cyan]Aura's Bruter - Help[/bold cyan]

[bold]Keyboard Shortcuts:[/bold]
  [cyan]Ctrl+C[/cyan]  - Stop current attack
  [cyan]Ctrl+Z[/cyan]  - Pause attack (resume with any key)

[bold]Attack Modes:[/bold]
  [cyan]Dictionary[/cyan]  - Use wordlist files for usernames and passwords
  [cyan]Generation[/cyan]  - Generate passwords from character sets
  [cyan]Smart[/cyan]       - Use common password patterns

[bold]Rate Limiting:[/bold]
  [cyan]Normal[/cyan]   - Fast with adaptive delays (0.5s base)
  [cyan]Stealth[/cyan]  - Very slow (5-15s delays) to avoid detection

[bold]Files:[/bold]
  [cyan]config.json[/cyan]    - Main configuration file
  [cyan]sessions/[/cyan]      - Saved attack sessions
  [cyan]logs/[/cyan]          - Attack logs
  [cyan]wordlists/[/cyan]     - Default wordlist files

[bold]CLI Usage:[/bold]
  python aura_bruter.py --help
  python aura_bruter.py --ssh --dict -H 192.168.1.1 -u users.txt -p pass.txt
  python aura_bruter.py --resume session_id
"""
    console.print(Panel(help_text, title="[bold]Help[/bold]", border_style="cyan"))


def display_version():
    """Display version information."""
    version_text = """
[bold cyan]Aura's Bruter[/bold cyan]
Version: 1.0.0

Multi-Protocol Brute Force Security Testing Tool
Supports: SSH, FTP, Telnet

[dim]For educational purposes only.
Only use on systems you own or have permission to test.[/dim]
"""
    console.print(Panel(version_text, border_style="cyan"))


def create_live_stats_layout(stats: Dict[str, Any]) -> Layout:
    """Create a live updating stats layout."""
    layout = Layout()
    
    # Header
    header = Table.grid()
    header.add_row(
        f"[bold cyan]Target:[/bold cyan] {stats.get('target', 'N/A')}",
        f"[bold cyan]Protocol:[/bold cyan] {stats.get('protocol', 'N/A')}"
    )
    
    # Progress
    progress_text = Text()
    progress_pct = stats.get("progress", 0)
    progress_text.append(f"Progress: {progress_pct:.1f}% ")
    
    # Progress bar
    bar_width = 30
    filled = int(bar_width * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    progress_text.append(f"[{bar}]", style="cyan")
    
    # Stats
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Key")
    stats_table.add_column("Value")
    
    stats_table.add_row("Tested", format_number(stats.get("tested", 0)))
    stats_table.add_row("Found", f"[green]{stats.get('found', 0)}[/green]")
    stats_table.add_row("Speed", format_speed(stats.get("speed", 0)))
    stats_table.add_row("Elapsed", format_duration(stats.get("elapsed", 0)))
    stats_table.add_row("ETA", format_duration(stats.get("eta", 0)))
    
    layout.split_column(
        Layout(Panel(header, border_style="cyan"), size=3),
        Layout(Align.center(progress_text), size=3),
        Layout(Panel(stats_table, title="Stats", border_style="cyan"))
    )
    
    return layout


if __name__ == "__main__":
    # Demo displays
    console.print("[yellow]Display Utilities Demo[/yellow]\n")
    
    # Demo server info
    display_server_info({
        "host": "192.168.1.100",
        "port": 22,
        "port_open": True,
        "banner": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
    })
    
    console.print()
    
    # Demo credentials
    display_credentials_found([
        {"username": "admin", "password": "password123", "found_at": "2024-02-02T14:30:00"},
        {"username": "root", "password": "toor", "found_at": "2024-02-02T14:31:00"},
    ])
    
    console.print()
    
    # Demo stats
    display_final_stats({
        "tested": 15000,
        "successful": 2,
        "failed": 14998,
        "errors": 0,
        "elapsed": 1523.5,
        "speed": 9.85
    })
