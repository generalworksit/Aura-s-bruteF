#!/usr/bin/env python3
"""
Aura's Bruter - Main Entry Point
Multi-Protocol Brute Force Security Testing Tool
"""

import sys
import os
import json
import argparse
import signal
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.prompt import Confirm

# Import UI components
from ui.banner import show_welcome, clear_screen
from ui.menu import (
    create_main_menu, create_attack_mode_menu, create_settings_menu,
    get_target_input, get_dictionary_config, get_generation_config,
    get_rate_limit_config, get_telegram_config, select_session,
    confirm_attack, show_time_estimate, render_main_menu, render_settings_menu,
    render_attack_mode_menu, show_validation_error, render_header,
    render_settings_status, get_tool_selection, get_random_tip
)
from ui.display import display_server_info, display_help, display_version

# Import core components
from core.rate_limiter import RateLimiter, RateLimitConfig
from core.session_manager import SessionManager
from core.notifier import Notifier, NotificationConfig
from core.attack_engine import AttackEngine
from core.telegram_bot import TelegramBot, TelegramConfig, create_from_config

# Import protocol attackers
from protocols.ssh_attack import SSHAttacker
from protocols.ftp_attack import FTPAttacker
from protocols.telnet_attack import TelnetAttacker

# Import attack modes
from attacks.dictionary_attack import DictionaryAttack
from attacks.generation_attack import GenerationAttack, CharsetConfig, SmartGenerationAttack


console = Console()

# Global state
current_engine = None
current_monitor = None
config = {}
session_manager = None
telegram_bot = None


def load_config():
    """Load configuration from config.json."""
    global config
    config_path = Path(__file__).parent / "config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
    else:
        config = {}
    
    return config


def save_config():
    """Save configuration to config.json."""
    config_path = Path(__file__).parent / "config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global current_engine, current_monitor
    
    console.print("\n[yellow]Interrupt received. Stopping...[/yellow]")
    
    if current_monitor:
        current_monitor.stop()
    
    if current_engine and current_engine.is_running():
        current_engine.stop()
    else:
        sys.exit(0)


def get_attacker(protocol: str, host: str, port: int):
    """Get the appropriate attacker for the protocol."""
    attackers = {
        "ssh": (SSHAttacker, 22),
        "ftp": (FTPAttacker, 21),
        "telnet": (TelnetAttacker, 23)
    }
    
    if protocol not in attackers:
        raise ValueError(f"Unknown protocol: {protocol}")
    
    attacker_class, default_port = attackers[protocol]
    return attacker_class(host, port or default_port, timeout=config.get("attack", {}).get("timeout", 10))


def validate_target(protocol: str, host: str, port: int) -> tuple:
    """
    Validate target before attack.
    Returns (valid, error_type, error_message)
    """
    console.print("\n[cyan]Validating target...[/cyan]")
    
    attacker = get_attacker(protocol, host, port)
    
    # Use the validation method if available (FTP has it)
    if hasattr(attacker, 'validate_target'):
        result = attacker.validate_target()
        if not result.valid:
            return False, result.error_type, result.error
        return True, None, None
    
    # Fallback: just check if port is open
    if not attacker.check_port_open():
        return False, "refused", f"Port {port} is not reachable"
    
    return True, None, None


def run_attack(protocol: str, mode: str, attack_config: dict, target_config: dict, skip_validation: bool = False):
    """Run an attack with the specified configuration."""
    global current_engine, current_monitor, telegram_bot
    
    host = target_config["host"]
    port = target_config["port"]
    
    # Validate target first (unless skipped for resume)
    if not skip_validation:
        valid, error_type, error_msg = validate_target(protocol, host, port)
        if not valid:
            show_validation_error(error_type, error_msg, host, port)
            return
    
    # Create attacker
    attacker = get_attacker(protocol, host, port)
    
    # Display server info
    console.print("\n[cyan]Checking target...[/cyan]")
    server_info = attacker.get_server_info()
    display_server_info(server_info)
    
    # Create rate limiter
    rl_config = config.get("rate_limiting", {})
    rate_limiter = RateLimiter(RateLimitConfig(
        enabled=rl_config.get("enabled", True),
        base_delay=rl_config.get("base_delay", 0.5),
        stealth_mode=rl_config.get("stealth_mode", False),
        randomize=rl_config.get("randomize", True)
    ))
    
    # Create notifier
    notifier = Notifier.from_config_file(str(Path(__file__).parent / "config.json"))
    
    # Create Telegram bot if enabled
    telegram_bot = create_from_config(config)
    
    # Create session manager
    global session_manager
    session_manager = SessionManager(str(Path(__file__).parent / "sessions"))
    
    # Create attack generator based on mode
    if mode == "dictionary":
        if attack_config.get("mode") == "combo":
            attack = DictionaryAttack(
                combo_file=attack_config["combo_file"],
                schema=attack_config.get("schema", "{user}:{pass}")
            )
        else:
            attack = DictionaryAttack(
                users_file=attack_config["users_file"],
                passwords_file=attack_config["passwords_file"]
            )
        
        # Validate files
        validation = attack.validate_files()
        if not validation["valid"]:
            for error in validation["errors"]:
                console.print(f"[red]Error: {error}[/red]")
            return
        
        attack.load()
        total = attack.total_combinations
        generator = attack.generate()
        
    elif mode == "generation":
        charset = CharsetConfig(
            lowercase=attack_config["charset"].get("lowercase", True),
            uppercase=attack_config["charset"].get("uppercase", False),
            digits=attack_config["charset"].get("digits", False),
            symbols=attack_config["charset"].get("symbols", False),
            custom=attack_config["charset"].get("custom", "")
        )
        
        attack = GenerationAttack(
            username=attack_config["username"],
            charset_config=charset,
            min_length=attack_config.get("min_length", 1),
            max_length=attack_config.get("max_length", 4),
            prefix=attack_config.get("prefix", ""),
            suffix=attack_config.get("suffix", "")
        )
        
        total = attack.total_combinations
        
        # Show time estimate
        estimate = attack.estimate_time(attempts_per_second=10)
        show_time_estimate(estimate)
        
        if not Confirm.ask("[yellow]Continue with this attack?[/yellow]", default=True):
            return
        
        generator = attack.generate()
        
    elif mode == "smart":
        attack = SmartGenerationAttack(
            username=attack_config.get("username", "root")
        )
        total = attack.total_combinations
        generator = attack.generate()
    
    else:
        console.print(f"[red]Unknown attack mode: {mode}[/red]")
        return
    
    # Create session
    session_manager.create_session(
        protocol=protocol,
        mode=mode,
        target_host=host,
        target_port=port,
        attack_config=attack_config,
        total_combinations=total
    )
    
    # Create and run engine
    threads = config.get("attack", {}).get("threads", 10)
    
    current_engine = AttackEngine(
        attacker=attacker,
        rate_limiter=rate_limiter,
        session_manager=session_manager,
        notifier=notifier,
        threads=threads
    )
    
    console.print(f"\n[bold green]Starting attack with {threads} threads...[/bold green]\n")
    
    # Start Telegram bot if enabled
    if telegram_bot and telegram_bot.config.enabled:
        telegram_bot.start()
        telegram_bot.set_attack_engine(current_engine)  # Connect for status commands
        telegram_bot.send_start(f"{host}:{port}", protocol, total)
    
    try:
        # Run the attack (AttackEngine has its own progress display)
        current_engine.start(generator, total)
        
    except KeyboardInterrupt:
        current_engine.stop()
        console.print("\n[yellow]Attack stopped.[/yellow]")
    
    finally:
        # Send final summary via Telegram
        if telegram_bot and telegram_bot.is_available:
            summary = {
                "target": f"{host}:{port}",
                "protocol": protocol,
                "tested": current_engine.stats.tested,
                "found": current_engine.stats.successful,
                "elapsed": current_engine.stats.format_elapsed(),
                "rate": f"{current_engine.stats.speed:.1f}/s",
                "credentials": current_engine.stats.found_credentials,
                "stage": "completed" if not current_engine._stop_event.is_set() else "stopped"
            }
            telegram_bot.send_summary(summary)
            telegram_bot.stop()
        
        # Mark session complete
        session_manager.complete()
    
    # Wait for user before returning to menu
    console.print("\n[dim]Press Enter to return to menu...[/dim]")
    input()


def resume_session():
    """Resume a previous session."""
    global session_manager
    from rich.panel import Panel
    from rich.align import Align
    from rich.box import ROUNDED
    from rich.text import Text
    
    clear_screen()
    render_header()
    
    session_manager = SessionManager(str(Path(__file__).parent / "sessions"))
    
    sessions = session_manager.list_sessions()
    
    if not sessions:
        # Show message when no sessions
        content = Text("No saved sessions found.\n\nStart a new attack to create a session.", style="yellow")
        panel = Panel(
            Align.center(content),
            title="[yellow]Sessions[/yellow]",
            border_style="yellow",
            box=ROUNDED,
            padding=(1, 2),
            width=50
        )
        console.print(Align.center(panel))
        console.print()
        console.print("[dim]Press Enter to return to menu...[/dim]")
        input()
        return
    
    # Get session selection and action
    session_id, action = select_session(sessions)
    
    if not session_id or not action:
        return
    
    # Load session
    try:
        session = session_manager.load(session_id)
        
        if action == "view":
            # View found credentials
            from ui.menu import view_session_credentials
            view_session_credentials(session)
        elif action == "resume":
            # Resume attack
            console.print(f"\n[cyan]Resuming session: {session.session_id}[/cyan]")
            console.print(f"[dim]Progress: {session.progress.tested}/{session.progress.total_combinations}[/dim]")
            
            run_attack(
                protocol=session.protocol,
                mode=session.mode,
                attack_config=session.attack_config,
                target_config={
                    "host": session.target_host,
                    "port": session.target_port
                },
                skip_validation=True
            )
    except Exception as e:
        console.print(f"[red]Error loading session: {e}[/red]")
        console.print("[dim]Press Enter to return to menu...[/dim]")
        input()


def settings_menu():
    """Handle settings menu."""
    while True:
        # Show current settings status before the menu
        clear_screen()
        render_header()
        render_settings_status(config)
        
        choice = render_settings_menu(show_header=False)
        
        if choice == "0":
            break
        elif choice == "1":
            # Rate limiting
            rl_config = get_rate_limit_config()
            config["rate_limiting"] = rl_config
            save_config()
            clear_screen()
            console.print("[green]Rate limiting settings saved.[/green]")
            import time
            time.sleep(1)
        elif choice == "2":
            # Telegram notifications
            tg_config = get_telegram_config()
            config["telegram"] = tg_config
            save_config()
            clear_screen()
            console.print("[green]Telegram settings saved.[/green]")
            import time
            time.sleep(1)
        elif choice == "3":
            # Threads
            clear_screen()
            render_header()
            from rich.prompt import IntPrompt
            threads = IntPrompt.ask("[cyan]Number of threads[/cyan]", default=10)
            if "attack" not in config:
                config["attack"] = {}
            config["attack"]["threads"] = max(1, min(threads, 100))
            save_config()
            console.print(f"[green]Thread count set to {config['attack']['threads']}.[/green]")
            import time
            time.sleep(1)
        elif choice == "4":
            # Session settings
            clear_screen()
            render_header()
            from rich.prompt import Confirm as ConfirmPrompt
            auto_save = ConfirmPrompt.ask("[cyan]Auto-save sessions?[/cyan]", default=True)
            if "session" not in config:
                config["session"] = {}
            config["session"]["auto_save"] = auto_save
            save_config()
            console.print("[green]Session settings saved.[/green]")
            import time
            time.sleep(1)


def protocol_attack_flow(protocol: str):
    """Handle the attack flow for a protocol."""
    # Get target - pass protocol to show correct default port
    default_ports = {"ssh": 22, "ftp": 21, "telnet": 23}
    host, port = get_target_input(protocol)
    port = port or default_ports.get(protocol, 22)
    
    # Get attack mode
    mode_choice = render_attack_mode_menu()
    
    if mode_choice == "0":
        return
    
    modes = {"1": "dictionary", "2": "generation", "3": "smart"}
    mode = modes.get(mode_choice)
    
    if not mode:
        return
    
    # Get attack configuration
    if mode == "dictionary":
        attack_config = get_dictionary_config()
    elif mode == "generation":
        attack_config = get_generation_config()
    elif mode == "smart":
        from rich.prompt import Prompt
        username = Prompt.ask("[cyan]Target username[/cyan]", default="root")
        attack_config = {"username": username}
    
    # Confirm and run
    full_config = {
        "protocol": protocol.upper(),
        "host": host,
        "port": port,
        "mode": mode,
        **attack_config
    }
    
    if confirm_attack(full_config):
        run_attack(protocol, mode, attack_config, {"host": host, "port": port})


def main_interactive():
    """Run in interactive TUI mode."""
    load_config()
    
    # Show welcome banner and animation
    show_welcome(animate=True)
    
    # Accept disclaimer
    if not Confirm.ask("[bold red]I accept the terms and will use this tool responsibly[/bold red]", default=False):
        console.print("[yellow]You must accept the terms to use this tool.[/yellow]")
        sys.exit(0)
    
    # Main loop - clear screen after accepting terms
    while True:
        # Render main menu with clean screen
        choice = render_main_menu()
        
        if choice == "1":
            protocol_attack_flow("ssh")
        elif choice == "2":
            protocol_attack_flow("ftp")
        elif choice == "3":
            protocol_attack_flow("telnet")
        elif choice == "4":
            settings_menu()
        elif choice == "5":
            resume_session()
        elif choice == "6":
            clear_screen()
            console.print("[cyan]\n  Goodbye!\n[/cyan]")
            break


def main_cli(args):
    """Run in CLI mode with arguments."""
    load_config()
    
    # Determine protocol
    if args.ssh:
        protocol = "ssh"
    elif args.ftp:
        protocol = "ftp"
    elif args.telnet:
        protocol = "telnet"
    else:
        console.print("[red]Please specify a protocol: --ssh, --ftp, or --telnet[/red]")
        return
    
    # Check required arguments
    if not args.host:
        console.print("[red]Please specify target host with -H/--host[/red]")
        return
    
    # Determine mode and config
    if args.dict:
        mode = "dictionary"
        if args.combo:
            attack_config = {
                "mode": "combo",
                "combo_file": args.combo,
                "schema": args.schema or "{user}:{pass}"
            }
        else:
            if not args.users or not args.passwords:
                console.print("[red]Dictionary mode requires -u/--users and -p/--passwords[/red]")
                return
            attack_config = {
                "mode": "separate",
                "users_file": args.users,
                "passwords_file": args.passwords
            }
    elif args.gen:
        mode = "generation"
        if not args.user:
            console.print("[red]Generation mode requires --user[/red]")
            return
        attack_config = {
            "username": args.user,
            "charset": {
                "lowercase": args.lower,
                "uppercase": args.upper,
                "digits": args.digits,
                "symbols": args.symbols,
                "custom": args.custom or ""
            },
            "min_length": args.min_len,
            "max_length": args.max_len,
            "prefix": args.prefix or "",
            "suffix": args.suffix or ""
        }
    elif args.smart:
        mode = "smart"
        attack_config = {"username": args.user or "root"}
    else:
        console.print("[red]Please specify attack mode: --dict, --gen, or --smart[/red]")
        return
    
    # Override config with CLI args
    if args.threads:
        if "attack" not in config:
            config["attack"] = {}
        config["attack"]["threads"] = args.threads
    
    if args.no_rate_limit:
        config["rate_limiting"] = {"enabled": False}
    
    if args.stealth:
        config["rate_limiting"] = {"enabled": True, "stealth_mode": True}
    
    # Show minimal banner
    from ui.banner import display_static_banner
    display_static_banner()
    console.print()
    
    # Run attack
    run_attack(
        protocol=protocol,
        mode=mode,
        attack_config=attack_config,
        target_config={"host": args.host, "port": args.port}
    )


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Aura's Bruter - Multi-Protocol Brute Force Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s --ssh --dict -H 192.168.1.1 -u users.txt -p pass.txt
  %(prog)s --ftp --gen -H 192.168.1.1 --user admin --lower --digits --max-len 6
  %(prog)s --resume session_id
        """
    )
    
    # Protocol selection
    proto_group = parser.add_argument_group("Protocol")
    proto_group.add_argument("--ssh", action="store_true", help="SSH protocol")
    proto_group.add_argument("--ftp", action="store_true", help="FTP protocol")
    proto_group.add_argument("--telnet", action="store_true", help="Telnet protocol")
    
    # Target
    target_group = parser.add_argument_group("Target")
    target_group.add_argument("-H", "--host", help="Target host")
    target_group.add_argument("-P", "--port", type=int, help="Target port")
    
    # Attack mode
    mode_group = parser.add_argument_group("Attack Mode")
    mode_group.add_argument("--dict", action="store_true", help="Dictionary attack")
    mode_group.add_argument("--gen", action="store_true", help="Generation attack")
    mode_group.add_argument("--smart", action="store_true", help="Smart pattern attack")
    
    # Dictionary options
    dict_group = parser.add_argument_group("Dictionary Options")
    dict_group.add_argument("-u", "--users", help="Username wordlist file")
    dict_group.add_argument("-p", "--passwords", help="Password wordlist file")
    dict_group.add_argument("-c", "--combo", help="Combo file (user:pass)")
    dict_group.add_argument("--schema", help="Combo file schema (default: {user}:{pass})")
    
    # Generation options
    gen_group = parser.add_argument_group("Generation Options")
    gen_group.add_argument("--user", help="Target username for generation")
    gen_group.add_argument("--lower", action="store_true", help="Include lowercase")
    gen_group.add_argument("--upper", action="store_true", help="Include uppercase")
    gen_group.add_argument("--digits", action="store_true", help="Include digits")
    gen_group.add_argument("--symbols", action="store_true", help="Include symbols")
    gen_group.add_argument("--custom", help="Custom characters")
    gen_group.add_argument("--min-len", type=int, default=1, help="Min password length")
    gen_group.add_argument("--max-len", type=int, default=4, help="Max password length")
    gen_group.add_argument("--prefix", help="Password prefix")
    gen_group.add_argument("--suffix", help="Password suffix")
    
    # Performance
    perf_group = parser.add_argument_group("Performance")
    perf_group.add_argument("-t", "--threads", type=int, help="Number of threads")
    perf_group.add_argument("--no-rate-limit", action="store_true", help="Disable rate limiting")
    perf_group.add_argument("--stealth", action="store_true", help="Enable stealth mode")
    
    # Session
    sess_group = parser.add_argument_group("Session")
    sess_group.add_argument("--resume", metavar="SESSION_ID", help="Resume session")
    
    # Misc
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    parser.add_argument("--help-full", action="store_true", help="Show detailed help")
    
    return parser


def main():
    """Main entry point."""
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special cases
    if args.version:
        display_version()
        return
    
    if args.help_full:
        display_help()
        return
    
    if args.resume:
        load_config()
        global session_manager
        session_manager = SessionManager(str(Path(__file__).parent / "sessions"))
        session = session_manager.load(args.resume)
        run_attack(
            protocol=session.protocol,
            mode=session.mode,
            attack_config=session.attack_config,
            target_config={"host": session.target_host, "port": session.target_port},
            skip_validation=True
        )
        return
    
    # Check if CLI mode or interactive
    if args.host or args.ssh or args.ftp or args.telnet:
        main_cli(args)
    else:
        main_interactive()


if __name__ == "__main__":
    main()
