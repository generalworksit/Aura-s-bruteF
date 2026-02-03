#!/usr/bin/env python3
"""
Aura's Bruter - Interactive Menu System
Uses Rich components exclusively for perfect alignment
No manual box drawing - guaranteed stable frames
"""

import sys
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align
from rich.text import Text
from rich.box import ROUNDED
from typing import Optional, List, Tuple, Callable


console = Console()

# Minimum terminal width for proper display
MIN_TERMINAL_WIDTH = 60


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


def check_terminal(show_warning: bool = True) -> bool:
    """Check if terminal is wide enough."""
    width = get_terminal_width()
    if width < MIN_TERMINAL_WIDTH:
        if show_warning:
            console.print(f"[yellow]Terminal too narrow ({width} cols). Need at least {MIN_TERMINAL_WIDTH}.[/yellow]")
        return False
    return True


def render_header():
    """Render compact header for menu screens - no emojis in fixed areas."""
    header = Text()
    header.append("AURA'S BRUTER", style="bold cyan")
    header.append(" - ", style="dim")
    header.append("Security Testing Tool", style="white")
    
    console.print(Align.center(header))
    
    author = Text("Created by generalworksit", style="dim italic yellow")
    console.print(Align.center(author))
    console.print()


class Menu:
    """Interactive menu using Rich Panel - guaranteed alignment."""
    
    def __init__(self, title: str, options: List[Tuple[str, str, Optional[Callable]]] = None):
        self.title = title
        self.options = options or []
    
    def add_option(self, key: str, label: str, callback: Callable = None):
        """Add menu option."""
        self.options.append((key, label, callback))
    
    def display(self, show_header: bool = True) -> str:
        """Display menu and return selected key."""
        if show_header:
            render_header()
        
        # Build menu content - use fixed-width format for stability
        menu_content = Text()
        
        for key, label, _ in self.options:
            menu_content.append(f"  [{key}]  ", style="bold cyan")
            menu_content.append(f"{label}\n", style="white")
        
        # Calculate panel width based on terminal
        term_width = get_terminal_width()
        panel_width = min(50, term_width - 4)
        
        panel = Panel(
            menu_content,
            title=f"[bold cyan]{self.title}[/bold cyan]",
            title_align="center",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 3),
            width=panel_width
        )
        
        console.print(Align.center(panel))
        console.print()
        
        valid_keys = [opt[0].lower() for opt in self.options]
        
        while True:
            choice = Prompt.ask(
                "[bold cyan]Select option[/bold cyan]",
                default=valid_keys[0] if valid_keys else ""
            ).lower()
            
            if choice in valid_keys:
                return choice
            
            console.print("[red]Invalid option. Please try again.[/red]")
    
    def run(self, show_header: bool = True) -> Optional[any]:
        """Display and execute selected callback."""
        choice = self.display(show_header=show_header)
        
        for key, label, callback in self.options:
            if key.lower() == choice and callback:
                return callback()
        
        return None


def create_main_menu() -> Menu:
    """Create main protocol selection menu."""
    menu = Menu("SELECT PROTOCOL")
    menu.add_option("1", "SSH Brute Force")
    menu.add_option("2", "FTP Brute Force")
    menu.add_option("3", "Telnet Brute Force")
    menu.add_option("4", "Settings")
    menu.add_option("5", "Resume Session")
    menu.add_option("6", "Exit")
    return menu


def create_attack_mode_menu() -> Menu:
    """Create attack mode selection menu."""
    menu = Menu("SELECT ATTACK MODE")
    menu.add_option("1", "Dictionary Attack")
    menu.add_option("2", "Generation Attack")
    menu.add_option("3", "Smart Attack")
    menu.add_option("0", "Back")
    return menu


def create_settings_menu() -> Menu:
    """Create settings menu."""
    menu = Menu("SETTINGS")
    menu.add_option("1", "Rate Limiting")
    menu.add_option("2", "Telegram Notifications")
    menu.add_option("3", "Thread Count")
    menu.add_option("4", "Session Settings")
    menu.add_option("0", "Back")
    return menu


def render_info_panel(title: str, lines: List[Tuple[str, str]]):
    """Render an info panel with key-value pairs."""
    content = Text()
    for label, value in lines:
        content.append(f"{label}: ", style="cyan")
        content.append(f"{value}\n", style="white")
    
    panel = Panel(
        content,
        title=f"[cyan]{title}[/cyan]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        width=min(60, get_terminal_width() - 4)
    )
    console.print(Align.center(panel))


def get_target_input() -> Tuple[str, int]:
    """Get target host and port."""
    clear_screen()
    render_header()
    
    render_info_panel("Target Configuration", [
        ("Enter", "Target host and port"),
        ("Example", "192.168.1.100 or domain.com")
    ])
    console.print()
    
    host = Prompt.ask("[cyan]Target host[/cyan]")
    port = IntPrompt.ask("[cyan]Port[/cyan]", default=22)
    
    return host, port


def get_dictionary_config() -> dict:
    """Get dictionary attack configuration."""
    clear_screen()
    render_header()
    
    render_info_panel("Dictionary Mode", [
        ("Option 1", "Separate user/password files"),
        ("Option 2", "Combined combo file (user:pass)")
    ])
    console.print()
    
    use_combo = Confirm.ask("[cyan]Use combo file?[/cyan]", default=False)
    
    if use_combo:
        combo_file = Prompt.ask("[cyan]Combo file path[/cyan]")
        schema = Prompt.ask("[cyan]Schema[/cyan]", default="{user}:{pass}")
        return {"mode": "combo", "combo_file": combo_file, "schema": schema}
    else:
        users_file = Prompt.ask("[cyan]Users file path[/cyan]")
        passwords_file = Prompt.ask("[cyan]Passwords file path[/cyan]")
        return {"mode": "separate", "users_file": users_file, "passwords_file": passwords_file}


def get_generation_config() -> dict:
    """Get generation attack configuration."""
    clear_screen()
    render_header()
    
    render_info_panel("Generation Mode", [
        ("Lowercase", "a-z (26 chars)"),
        ("Uppercase", "A-Z (26 chars)"),
        ("Digits", "0-9 (10 chars)"),
        ("Symbols", "Special characters")
    ])
    console.print()
    
    username = Prompt.ask("[cyan]Target username[/cyan]", default="root")
    
    console.print("\n[bold cyan]Character Sets:[/bold cyan]")
    lowercase = Confirm.ask("  Include lowercase?", default=True)
    uppercase = Confirm.ask("  Include uppercase?", default=False)
    digits = Confirm.ask("  Include digits?", default=True)
    symbols = Confirm.ask("  Include symbols?", default=False)
    
    custom = Prompt.ask("[cyan]Custom characters (optional)[/cyan]", default="")
    
    min_length = IntPrompt.ask("[cyan]Minimum length[/cyan]", default=1)
    max_length = IntPrompt.ask("[cyan]Maximum length[/cyan]", default=4)
    
    prefix = Prompt.ask("[cyan]Password prefix (optional)[/cyan]", default="")
    suffix = Prompt.ask("[cyan]Password suffix (optional)[/cyan]", default="")
    
    return {
        "username": username,
        "charset": {
            "lowercase": lowercase,
            "uppercase": uppercase,
            "digits": digits,
            "symbols": symbols,
            "custom": custom
        },
        "min_length": min_length,
        "max_length": max_length,
        "prefix": prefix,
        "suffix": suffix
    }


def get_telegram_config() -> dict:
    """Get Telegram configuration."""
    clear_screen()
    render_header()
    
    render_info_panel("Telegram Notifications", [
        ("Bot Token", "Get from @BotFather on Telegram"),
        ("Chat ID", "Your Telegram user/chat ID"),
        ("Purpose", "Receive attack status and results")
    ])
    console.print()
    
    enabled = Confirm.ask("[cyan]Enable Telegram notifications?[/cyan]", default=False)
    
    if not enabled:
        return {"enabled": False}
    
    token = Prompt.ask("[cyan]Bot token[/cyan]")
    chat_id = Prompt.ask("[cyan]Chat ID[/cyan]")
    
    console.print("\n[bold cyan]Notification Options:[/bold cyan]")
    send_progress = Confirm.ask("  Send progress updates?", default=True)
    send_found = Confirm.ask("  Send when credentials found?", default=True)
    send_summary = Confirm.ask("  Send final summary?", default=True)
    
    if send_progress:
        interval = IntPrompt.ask("  Progress update interval (seconds)", default=60)
    else:
        interval = 60
    
    return {
        "enabled": True,
        "token": token,
        "chat_id": chat_id,
        "send_progress": send_progress,
        "send_found": send_found,
        "send_summary": send_summary,
        "progress_interval": interval
    }


def get_rate_limit_config() -> dict:
    """Get rate limiting configuration."""
    clear_screen()
    render_header()
    
    render_info_panel("Rate Limiting", [
        ("Purpose", "Avoid detection and blocking"),
        ("Normal", "Fast with adaptive delays"),
        ("Stealth", "Very slow, careful attacks")
    ])
    console.print()
    
    enabled = Confirm.ask("[cyan]Enable rate limiting?[/cyan]", default=True)
    
    if not enabled:
        return {"enabled": False}
    
    stealth = Confirm.ask("[cyan]Enable stealth mode?[/cyan]", default=False)
    
    if stealth:
        return {"enabled": True, "stealth_mode": True, "base_delay": 5.0}
    
    base_delay = float(Prompt.ask("[cyan]Base delay (seconds)[/cyan]", default="0.5"))
    randomize = Confirm.ask("[cyan]Randomize delays?[/cyan]", default=True)
    
    return {
        "enabled": True,
        "stealth_mode": False,
        "base_delay": base_delay,
        "randomize": randomize
    }


def render_session_list(sessions: list):
    """Render session selection list."""
    render_header()
    
    if not sessions:
        content = Text("No saved sessions found.\n\nStart a new attack to create a session.", style="yellow")
        panel = Panel(
            Align.center(content),
            title="[yellow]Sessions[/yellow]",
            border_style="yellow",
            box=ROUNDED,
            padding=(1, 2),
            width=min(50, get_terminal_width() - 4)
        )
        console.print(Align.center(panel))
        console.print()
        console.print("[dim]Press Enter to go back...[/dim]")
        input()
        return
    
    # Build session table
    table = Table(border_style="cyan", box=ROUNDED, width=min(70, get_terminal_width() - 4))
    table.add_column("#", style="cyan", width=3)
    table.add_column("Session ID", style="white")
    table.add_column("Protocol", style="magenta")
    table.add_column("Target", style="yellow")
    table.add_column("Progress", style="green")
    table.add_column("Found", style="red")
    
    for i, sess in enumerate(sessions, 1):
        table.add_row(
            str(i),
            sess["session_id"][:16] + "...",
            sess["protocol"].upper(),
            sess["target"],
            sess["progress"],
            str(sess["found"])
        )
    
    console.print(Align.center(table))
    console.print()


def select_session(sessions: list) -> Optional[str]:
    """Display session list and get selection."""
    clear_screen()
    render_session_list(sessions)
    
    if not sessions:
        return None
    
    choice = IntPrompt.ask("[cyan]Select session (0 to cancel)[/cyan]", default=0)
    
    if choice == 0 or choice > len(sessions):
        return None
    
    return sessions[choice - 1]["session_id"]


def show_validation_error(error_type: str, error_msg: str, host: str, port: int):
    """Display target validation error."""
    clear_screen()
    render_header()
    
    error_details = {
        "dns": ("DNS Resolution Failed", "The hostname could not be resolved."),
        "refused": ("Connection Refused", "The target actively refused the connection."),
        "timeout": ("Connection Timeout", "The target did not respond in time."),
        "protocol": ("Protocol Error", "FTP handshake failed."),
        "network": ("Network Error", "A network error occurred."),
    }
    
    title, desc = error_details.get(error_type, ("Error", "An error occurred."))
    
    content = Text()
    content.append(f"{title}\n\n", style="bold red")
    content.append(f"Target: ", style="white")
    content.append(f"{host}:{port}\n", style="yellow")
    content.append(f"Error: ", style="white")
    content.append(f"{error_msg}\n\n", style="red")
    content.append(f"{desc}\n\n", style="dim")
    content.append("Check the target and try again.", style="dim italic")
    
    panel = Panel(
        Align.center(content),
        title="[red]Validation Failed[/red]",
        border_style="red",
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(Align.center(panel))
    console.print()
    console.print("[dim]Press Enter to return to menu...[/dim]")
    input()


def show_time_estimate(estimate: dict):
    """Display time estimate for attack."""
    content = Text()
    content.append("Time Estimate\n\n", style="bold")
    content.append(f"Total combinations: ", style="white")
    content.append(f"{estimate['total_combinations']:,}\n", style="cyan")
    content.append(f"Estimated time: ", style="white")
    content.append(f"{estimate['human_readable']}\n", style="yellow")
    content.append(f"At speed: ", style="white")
    content.append(f"{estimate['at_speed']}", style="dim")
    
    panel = Panel(
        content,
        title="[yellow]Warning[/yellow]",
        border_style="yellow",
        box=ROUNDED,
        padding=(1, 2),
        width=min(50, get_terminal_width() - 4)
    )
    console.print(Align.center(panel))


def confirm_attack(config: dict) -> bool:
    """Display config and confirm attack start."""
    clear_screen()
    render_header()
    
    content = Text()
    for key, value in config.items():
        if not isinstance(value, dict):
            content.append(f"{key}: ", style="cyan")
            content.append(f"{value}\n", style="white")
    
    panel = Panel(
        content,
        title="[yellow]Attack Configuration[/yellow]",
        border_style="yellow",
        box=ROUNDED,
        padding=(1, 2),
        width=min(60, get_terminal_width() - 4)
    )
    
    console.print(Align.center(panel))
    console.print()
    
    return Confirm.ask("[bold yellow]Start attack?[/bold yellow]", default=True)


def render_main_menu() -> str:
    """Render main menu and return choice."""
    clear_screen()
    menu = create_main_menu()
    return menu.display()


def render_attack_mode_menu() -> str:
    """Render attack mode menu and return choice."""
    clear_screen()
    menu = create_attack_mode_menu()
    return menu.display()


def render_settings_menu() -> str:
    """Render settings menu and return choice."""
    clear_screen()
    menu = create_settings_menu()
    return menu.display()


if __name__ == "__main__":
    console.print("[yellow]Menu System Demo[/yellow]\n")
    
    if not check_terminal():
        sys.exit(1)
    
    choice = render_main_menu()
    console.print(f"\nSelected: {choice}")
