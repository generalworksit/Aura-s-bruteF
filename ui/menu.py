#!/usr/bin/env python3
"""
Aura's Bruter - Interactive Menu System
Rich TUI menus for user interaction with clean screen management
Uses Rich Panel for perfect box alignment
"""

import sys
import shutil
import time as time_module
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align
from rich.text import Text
from rich.box import ROUNDED, DOUBLE
from typing import Optional, List, Tuple, Callable


console = Console()


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


def render_header():
    """Render a compact header for menu screens."""
    header = Text()
    header.append("AURA'S BRUTER", style="bold cyan")
    header.append(" - ", style="dim")
    header.append("Security Testing Tool", style="dim white")
    
    console.print(Align.center(header))
    
    # Add author line
    author = Text("Created by generalworksit", style="dim italic yellow")
    console.print(Align.center(author))
    console.print()


class Menu:
    """Base class for interactive menus using Rich Panel for alignment."""
    
    def __init__(self, title: str, options: List[Tuple[str, str, Callable]] = None):
        """
        Initialize menu.
        
        Args:
            title: Menu title
            options: List of (key, label, callback) tuples
        """
        self.title = title
        self.options = options or []
    
    def add_option(self, key: str, label: str, callback: Callable = None):
        """Add a menu option."""
        self.options.append((key, label, callback))
    
    def display(self, show_header: bool = True) -> str:
        """Display the menu and return selected key."""
        if show_header:
            render_header()
        
        # Build menu content as Text with emojis in labels (not box chars)
        menu_content = Text()
        
        for key, label, _ in self.options:
            menu_content.append(f"  [{key}]  ", style="bold cyan")
            menu_content.append(f"{label}\n", style="white")
        
        # Use Rich Panel for perfect box alignment
        panel = Panel(
            menu_content,
            title=f"[bold cyan]{self.title}[/bold cyan]",
            title_align="center",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 3),
            width=min(50, get_terminal_width() - 4)  # Adaptive width
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
        """Display menu and execute selected callback."""
        choice = self.display(show_header=show_header)
        
        for key, label, callback in self.options:
            if key.lower() == choice and callback:
                return callback()
        
        return None


def create_main_menu() -> Menu:
    """Create the main protocol selection menu with emojis."""
    menu = Menu("SELECT PROTOCOL")
    menu.add_option("1", "SSH Brute Force        [SSH]")
    menu.add_option("2", "FTP Brute Force        [FTP]")
    menu.add_option("3", "Telnet Brute Force     [TEL]")
    menu.add_option("4", "Settings               [CFG]")
    menu.add_option("5", "Resume Session         [RES]")
    menu.add_option("6", "Exit                   [BYE]")
    return menu


def create_attack_mode_menu() -> Menu:
    """Create the attack mode selection menu."""
    menu = Menu("SELECT ATTACK MODE")
    menu.add_option("1", "Dictionary Attack      [wordlist]")
    menu.add_option("2", "Generation Attack      [charset]")
    menu.add_option("3", "Smart Attack           [patterns]")
    menu.add_option("0", "Back                   [<--]")
    return menu


def create_settings_menu() -> Menu:
    """Create the settings menu."""
    menu = Menu("SETTINGS")
    menu.add_option("1", "Rate Limiting          [delay]")
    menu.add_option("2", "Notifications          [alert]")
    menu.add_option("3", "Thread Count           [perf]")
    menu.add_option("4", "Session Settings       [save]")
    menu.add_option("0", "Back                   [<--]")
    return menu


def render_config_panel(title: str, description: str):
    """Render a configuration screen panel."""
    render_header()
    
    content = Text()
    content.append(description, style="dim")
    
    panel = Panel(
        content,
        title=f"[cyan]{title}[/cyan]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        width=min(60, get_terminal_width() - 4)
    )
    console.print(Align.center(panel))
    console.print()


def render_target_screen():
    """Render the target configuration screen."""
    render_config_panel(
        "Target Configuration",
        "Enter target information\nExample: 192.168.1.100 or example.com"
    )


def get_target_input() -> Tuple[str, int]:
    """Get target host and port from user."""
    clear_screen()
    render_target_screen()
    
    host = Prompt.ask("[cyan]Target host[/cyan]")
    port = IntPrompt.ask("[cyan]Port[/cyan]", default=22)
    
    return host, port


def render_dictionary_config_screen():
    """Render the dictionary configuration screen."""
    render_config_panel(
        "Dictionary Mode",
        "Dictionary Attack Configuration\n\n"
        "You can use:\n"
        "- Separate username and password files\n"
        "- Combined combo file (user:pass format)\n"
        "- Custom schema for combo parsing"
    )


def get_dictionary_config() -> dict:
    """Get dictionary attack configuration."""
    clear_screen()
    render_dictionary_config_screen()
    
    use_combo = Confirm.ask("[cyan]Use combo file (user:pass)?[/cyan]", default=False)
    
    if use_combo:
        combo_file = Prompt.ask("[cyan]Combo file path[/cyan]")
        schema = Prompt.ask(
            "[cyan]Schema[/cyan]",
            default="{user}:{pass}",
            show_default=True
        )
        return {
            "mode": "combo",
            "combo_file": combo_file,
            "schema": schema
        }
    else:
        users_file = Prompt.ask("[cyan]Users file path[/cyan]")
        passwords_file = Prompt.ask("[cyan]Passwords file path[/cyan]")
        return {
            "mode": "separate",
            "users_file": users_file,
            "passwords_file": passwords_file
        }


def render_generation_config_screen():
    """Render the generation configuration screen."""
    render_config_panel(
        "Generation Mode",
        "Generation Attack Configuration\n\n"
        "Select character sets to use:\n"
        "- Lowercase (a-z): 26 chars\n"
        "- Uppercase (A-Z): 26 chars\n"
        "- Digits (0-9): 10 chars\n"
        "- Symbols (!@#$...): 27 chars"
    )


def get_generation_config() -> dict:
    """Get generation attack configuration."""
    clear_screen()
    render_generation_config_screen()
    
    username = Prompt.ask("[cyan]Target username[/cyan]", default="root")
    
    console.print("\n[bold cyan]Character Sets:[/bold cyan]")
    lowercase = Confirm.ask("  Include lowercase (a-z)?", default=True)
    uppercase = Confirm.ask("  Include uppercase (A-Z)?", default=False)
    digits = Confirm.ask("  Include digits (0-9)?", default=True)
    symbols = Confirm.ask("  Include symbols (!@#$...)?", default=False)
    
    custom = Prompt.ask(
        "[cyan]Custom characters (leave empty for none)[/cyan]",
        default=""
    )
    
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


def render_rate_limit_screen():
    """Render the rate limiting configuration screen."""
    render_config_panel(
        "Rate Limiting",
        "Rate Limiting Configuration\n\n"
        "Helps avoid detection and blocking:\n"
        "- Normal mode: Fast with adaptive delays\n"
        "- Stealth mode: Very slow, careful attacks"
    )


def get_rate_limit_config() -> dict:
    """Get rate limiting configuration."""
    clear_screen()
    render_rate_limit_screen()
    
    enabled = Confirm.ask("[cyan]Enable rate limiting?[/cyan]", default=True)
    
    if not enabled:
        return {"enabled": False}
    
    stealth = Confirm.ask("[cyan]Enable stealth mode?[/cyan]", default=False)
    
    if stealth:
        return {
            "enabled": True,
            "stealth_mode": True,
            "base_delay": 5.0
        }
    
    base_delay = float(Prompt.ask(
        "[cyan]Base delay between attempts (seconds)[/cyan]",
        default="0.5"
    ))
    
    randomize = Confirm.ask("[cyan]Randomize delays (+-30%)?[/cyan]", default=True)
    
    return {
        "enabled": True,
        "stealth_mode": False,
        "base_delay": base_delay,
        "randomize": randomize
    }


def render_notification_screen():
    """Render the notification configuration screen."""
    render_config_panel(
        "Notifications",
        "Notification Configuration\n\n"
        "Get alerts when credentials are found:\n"
        "- Telegram: Create a bot via @BotFather\n"
        "- Discord: Create a webhook in your server"
    )


def get_notification_config() -> dict:
    """Get notification configuration."""
    clear_screen()
    render_notification_screen()
    
    config = {"telegram": {}, "discord": {}}
    
    # Telegram
    use_telegram = Confirm.ask("[cyan]Enable Telegram notifications?[/cyan]", default=False)
    if use_telegram:
        token = Prompt.ask("[cyan]Bot token[/cyan]")
        chat_id = Prompt.ask("[cyan]Your chat ID[/cyan]")
        config["telegram"] = {
            "enabled": True,
            "token": token,
            "chat_id": chat_id
        }
    else:
        config["telegram"] = {"enabled": False}
    
    # Discord
    use_discord = Confirm.ask("[cyan]Enable Discord notifications?[/cyan]", default=False)
    if use_discord:
        webhook = Prompt.ask("[cyan]Webhook URL[/cyan]")
        config["discord"] = {
            "enabled": True,
            "webhook_url": webhook
        }
    else:
        config["discord"] = {"enabled": False}
    
    return config


def render_session_list_screen(sessions: list):
    """Render the session selection screen."""
    render_header()
    
    if not sessions:
        # Show message in panel
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
    table = Table(
        title="Saved Sessions",
        border_style="cyan",
        box=ROUNDED,
        width=min(70, get_terminal_width() - 4)
    )
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
    """Display session list and get user selection."""
    clear_screen()
    render_session_list_screen(sessions)
    
    if not sessions:
        return None
    
    choice = IntPrompt.ask(
        "[cyan]Select session number (0 to cancel)[/cyan]",
        default=0
    )
    
    if choice == 0 or choice > len(sessions):
        return None
    
    return sessions[choice - 1]["session_id"]


def render_confirm_attack_screen(config: dict):
    """Render the attack confirmation screen."""
    render_header()
    
    # Build config display
    content = Text()
    for key, value in config.items():
        if isinstance(value, dict):
            content.append(f"{key}: ", style="cyan")
            content.append(f"{value}\n", style="white")
        else:
            content.append(f"{key}: ", style="cyan")
            content.append(f"{value}\n", style="white")
    
    panel = Panel(
        content,
        title="[bold yellow]Attack Configuration[/bold yellow]",
        border_style="yellow",
        box=ROUNDED,
        padding=(1, 2),
        width=min(60, get_terminal_width() - 4)
    )
    
    console.print(Align.center(panel))
    console.print()


def confirm_attack(config: dict) -> bool:
    """Display attack configuration and confirm."""
    clear_screen()
    render_confirm_attack_screen(config)
    
    return Confirm.ask("[bold yellow]Start attack?[/bold yellow]", default=True)


def show_time_estimate(estimate: dict):
    """Display time estimate for generation attack."""
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


def render_main_menu() -> str:
    """Render and display main menu, return choice."""
    clear_screen()
    menu = create_main_menu()
    return menu.display()


def render_attack_mode_menu() -> str:
    """Render and display attack mode menu, return choice."""
    clear_screen()
    menu = create_attack_mode_menu()
    return menu.display()


def render_settings_menu() -> str:
    """Render and display settings menu, return choice."""
    clear_screen()
    menu = create_settings_menu()
    return menu.display()


if __name__ == "__main__":
    # Demo menus
    console.print("[yellow]Menu System Demo[/yellow]\n")
    
    choice = render_main_menu()
    console.print(f"\nSelected: {choice}")
