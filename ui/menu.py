#!/usr/bin/env python3
"""
Aura's Bruter - Interactive Menu System
Rich TUI menus for user interaction with clean screen management
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align
from rich.text import Text
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


def render_header():
    """Render a compact header for menu screens."""
    header = Text()
    header.append("🔐 ", style="bold")
    header.append("AURA'S BRUTER", style="bold cyan")
    header.append(" - ", style="dim")
    header.append("Security Testing Tool", style="dim")
    console.print(Align.center(header))
    console.print()


class Menu:
    """Base class for interactive menus."""
    
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
        
        table = Table(
            show_header=False,
            border_style="cyan",
            box=None,
            padding=(0, 2)
        )
        table.add_column("Key", style="bold cyan", width=5)
        table.add_column("Option", style="white")
        
        for key, label, _ in self.options:
            table.add_row(f"[{key}]", label)
        
        panel = Panel(
            table,
            title=f"[bold cyan]{self.title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
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
    """Create the main protocol selection menu."""
    menu = Menu("SELECT PROTOCOL")
    menu.add_option("1", "🔐 SSH Brute Force")
    menu.add_option("2", "📁 FTP Brute Force")
    menu.add_option("3", "💻 Telnet Brute Force")
    menu.add_option("4", "⚙️  Settings")
    menu.add_option("5", "📋 Resume Session")
    menu.add_option("6", "🚪 Exit")
    return menu


def create_attack_mode_menu() -> Menu:
    """Create the attack mode selection menu."""
    menu = Menu("SELECT ATTACK MODE")
    menu.add_option("1", "📚 Dictionary Attack (wordlist files)")
    menu.add_option("2", "🔧 Generation Attack (character combinations)")
    menu.add_option("3", "🧠 Smart Attack (common patterns)")
    menu.add_option("0", "⬅️  Back")
    return menu


def create_settings_menu() -> Menu:
    """Create the settings menu."""
    menu = Menu("SETTINGS")
    menu.add_option("1", "⏱️  Rate Limiting")
    menu.add_option("2", "🔔 Notifications")
    menu.add_option("3", "🧵 Thread Count")
    menu.add_option("4", "💾 Session Settings")
    menu.add_option("0", "⬅️  Back")
    return menu


def render_target_screen():
    """Render the target configuration screen."""
    render_header()
    
    panel = Panel(
        "[bold]Enter target information[/bold]\n"
        "[dim]Example: 192.168.1.100 or example.com[/dim]",
        title="[cyan]Target Configuration[/cyan]",
        border_style="cyan"
    )
    console.print(panel)
    console.print()


def get_target_input() -> Tuple[str, int]:
    """Get target host and port from user."""
    clear_screen()
    render_target_screen()
    
    host = Prompt.ask("[cyan]Target host[/cyan]")
    port = IntPrompt.ask("[cyan]Port[/cyan]", default=22)
    
    return host, port


def render_dictionary_config_screen():
    """Render the dictionary configuration screen."""
    render_header()
    
    panel = Panel(
        "[bold]Dictionary Attack Configuration[/bold]\n\n"
        "[dim]You can use:[/dim]\n"
        "• Separate username and password files\n"
        "• Combined combo file (user:pass format)\n"
        "• Custom schema for combo parsing",
        title="[cyan]Dictionary Mode[/cyan]",
        border_style="cyan"
    )
    console.print(panel)
    console.print()


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
    render_header()
    
    panel = Panel(
        "[bold]Generation Attack Configuration[/bold]\n\n"
        "[dim]Select character sets to use:[/dim]\n"
        "• Lowercase (a-z): 26 chars\n"
        "• Uppercase (A-Z): 26 chars\n"
        "• Digits (0-9): 10 chars\n"
        "• Symbols (!@#$...): 27 chars",
        title="[cyan]Generation Mode[/cyan]",
        border_style="cyan"
    )
    console.print(panel)
    console.print()


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
    render_header()
    
    panel = Panel(
        "[bold]Rate Limiting Configuration[/bold]\n\n"
        "[dim]Helps avoid detection and blocking:[/dim]\n"
        "• Normal mode: Fast with adaptive delays\n"
        "• Stealth mode: Very slow, careful attacks",
        title="[cyan]Rate Limiting[/cyan]",
        border_style="cyan"
    )
    console.print(panel)
    console.print()


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
    
    randomize = Confirm.ask("[cyan]Randomize delays (±30%)?[/cyan]", default=True)
    
    return {
        "enabled": True,
        "stealth_mode": False,
        "base_delay": base_delay,
        "randomize": randomize
    }


def render_notification_screen():
    """Render the notification configuration screen."""
    render_header()
    
    panel = Panel(
        "[bold]Notification Configuration[/bold]\n\n"
        "[dim]Get alerts when credentials are found:[/dim]\n"
        "• Telegram: Create a bot via @BotFather\n"
        "• Discord: Create a webhook in your server",
        title="[cyan]Notifications[/cyan]",
        border_style="cyan"
    )
    console.print(panel)
    console.print()


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
        console.print("[yellow]No saved sessions found.[/yellow]")
        return
    
    table = Table(title="[bold]Saved Sessions[/bold]", border_style="cyan")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Session ID", style="white")
    table.add_column("Protocol", style="magenta")
    table.add_column("Target", style="yellow")
    table.add_column("Progress", style="green")
    table.add_column("Found", style="red")
    table.add_column("Status", style="blue")
    
    for i, sess in enumerate(sessions, 1):
        table.add_row(
            str(i),
            sess["session_id"],
            sess["protocol"],
            sess["target"],
            sess["progress"],
            str(sess["found"]),
            sess["status"]
        )
    
    console.print(table)
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
    
    table = Table(
        title="[bold]Attack Configuration[/bold]",
        show_header=False,
        border_style="yellow"
    )
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in config.items():
        if isinstance(value, dict):
            table.add_row(key, str(value))
        else:
            table.add_row(key, str(value))
    
    console.print(table)
    console.print()


def confirm_attack(config: dict) -> bool:
    """Display attack configuration and confirm."""
    clear_screen()
    render_confirm_attack_screen(config)
    
    return Confirm.ask("[bold yellow]Start attack?[/bold yellow]", default=True)


def show_time_estimate(estimate: dict):
    """Display time estimate for generation attack."""
    panel = Panel(
        f"[bold]Time Estimate[/bold]\n\n"
        f"Total combinations: [cyan]{estimate['total_combinations']:,}[/cyan]\n"
        f"Estimated time: [yellow]{estimate['human_readable']}[/yellow]\n"
        f"At speed: [dim]{estimate['at_speed']}[/dim]",
        title="[yellow]⚠️  Warning[/yellow]",
        border_style="yellow"
    )
    console.print(panel)


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
