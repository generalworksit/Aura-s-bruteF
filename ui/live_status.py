#!/usr/bin/env python3
"""
Aura's Bruter - Live Attack Status Display
Uses Rich Live for real-time, non-scrolling status updates
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED


console = Console()


@dataclass
class AttackStats:
    """Track attack statistics."""
    target_host: str = ""
    target_port: int = 0
    protocol: str = ""
    
    # Progress
    total_attempts: int = 0
    tested: int = 0
    
    # Timing
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    # Status
    stage: str = "idle"  # idle, checking, running, stopped, completed, error
    last_error: Optional[str] = None
    
    # Results
    found_credentials: List[Dict[str, str]] = field(default_factory=list)
    
    @property
    def elapsed_seconds(self) -> float:
        if not self.start_time:
            return 0
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def elapsed_str(self) -> str:
        secs = int(self.elapsed_seconds)
        hours, remainder = divmod(secs, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    
    @property
    def rate(self) -> float:
        elapsed = self.elapsed_seconds
        if elapsed > 0:
            return self.tested / elapsed
        return 0
    
    @property
    def rate_str(self) -> str:
        return f"{self.rate:.1f}/s"
    
    @property
    def progress_percent(self) -> float:
        if self.total_attempts > 0:
            return (self.tested / self.total_attempts) * 100
        return 0
    
    @property
    def eta_str(self) -> str:
        if self.rate > 0 and self.total_attempts > 0:
            remaining = self.total_attempts - self.tested
            eta_secs = remaining / self.rate
            if eta_secs < 3600:
                return f"{int(eta_secs // 60)}m {int(eta_secs % 60)}s"
            elif eta_secs < 86400:
                return f"{int(eta_secs // 3600)}h {int((eta_secs % 3600) // 60)}m"
            else:
                return f"{int(eta_secs // 86400)}d {int((eta_secs % 86400) // 3600)}h"
        return "--:--"
    
    @property
    def found_count(self) -> int:
        return len(self.found_credentials)


class LiveStatus:
    """Live updating status display using Rich."""
    
    def __init__(self, stats: AttackStats):
        self.stats = stats
        self._live: Optional[Live] = None
        self._running = False
    
    def create_status_table(self) -> Table:
        """Create the status display table."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan", width=15)
        table.add_column("Value", style="white")
        
        # Target info
        table.add_row("Target", f"{self.stats.target_host}:{self.stats.target_port}")
        table.add_row("Protocol", self.stats.protocol.upper())
        table.add_row("", "")  # Spacer
        
        # Status
        stage_colors = {
            "idle": "dim",
            "checking": "yellow",
            "running": "green",
            "stopped": "yellow",
            "completed": "green bold",
            "error": "red"
        }
        stage_style = stage_colors.get(self.stats.stage, "white")
        table.add_row("Status", Text(self.stats.stage.upper(), style=stage_style))
        
        # Progress
        table.add_row("Progress", f"{self.stats.tested:,} / {self.stats.total_attempts:,}")
        table.add_row("Percentage", f"{self.stats.progress_percent:.1f}%")
        table.add_row("", "")  # Spacer
        
        # Timing
        table.add_row("Elapsed", self.stats.elapsed_str)
        table.add_row("Rate", self.stats.rate_str)
        table.add_row("ETA", self.stats.eta_str)
        table.add_row("", "")  # Spacer
        
        # Results
        found_style = "green bold" if self.stats.found_count > 0 else "dim"
        table.add_row("Found", Text(str(self.stats.found_count), style=found_style))
        
        # Last error
        if self.stats.last_error:
            error_text = self.stats.last_error[:40]
            if len(self.stats.last_error) > 40:
                error_text += "..."
            table.add_row("Last Error", Text(error_text, style="red"))
        
        return table
    
    def create_panel(self) -> Panel:
        """Create the full status panel."""
        table = self.create_status_table()
        
        # Add found credentials if any
        if self.stats.found_credentials:
            creds = Text("\n\nFound Credentials:\n", style="green bold")
            for cred in self.stats.found_credentials[-5:]:  # Show last 5
                creds.append(f"  {cred['username']}:{cred['password']}\n", style="green")
            table = Table.grid()
            table.add_row(self.create_status_table())
            table.add_row(creds)
        
        return Panel(
            Align.center(self.create_status_table()),
            title="[bold cyan]Attack Status[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
    
    def start(self):
        """Start live display."""
        self._running = True
        self._live = Live(
            self.create_panel(),
            console=console,
            refresh_per_second=2,
            transient=False
        )
        self._live.start()
    
    def update(self):
        """Update the display."""
        if self._live:
            self._live.update(self.create_panel())
    
    def stop(self):
        """Stop live display."""
        self._running = False
        if self._live:
            self._live.stop()
            self._live = None


class AttackMonitor:
    """
    Monitor for attack progress with live terminal display.
    Thread-safe for use with multi-threaded attacks.
    """
    
    def __init__(self, target_host: str, target_port: int, protocol: str, total: int = 0):
        self.stats = AttackStats(
            target_host=target_host,
            target_port=target_port,
            protocol=protocol,
            total_attempts=total
        )
        self.display = LiveStatus(self.stats)
        self._lock = threading.Lock()
        self._callbacks: List[callable] = []
    
    def start(self):
        """Start monitoring."""
        self.stats.start_time = datetime.now()
        self.stats.stage = "running"
        self.display.start()
    
    def stop(self):
        """Stop monitoring."""
        self.display.stop()
    
    def update(self, tested: int = None, error: str = None, stage: str = None):
        """Update stats (thread-safe)."""
        with self._lock:
            if tested is not None:
                self.stats.tested = tested
            if error is not None:
                self.stats.last_error = error
            if stage is not None:
                self.stats.stage = stage
            self.stats.last_update = datetime.now()
        
        self.display.update()
        
        # Notify callbacks
        for cb in self._callbacks:
            try:
                cb(self.stats)
            except Exception:
                pass
    
    def add_credential(self, username: str, password: str):
        """Add found credential (thread-safe)."""
        with self._lock:
            self.stats.found_credentials.append({
                "username": username,
                "password": password,
                "found_at": datetime.now().isoformat()
            })
        self.display.update()
    
    def set_error(self, error: str):
        """Set last error."""
        self.update(error=error)
    
    def set_stage(self, stage: str):
        """Set current stage."""
        self.update(stage=stage)
    
    def increment(self, count: int = 1):
        """Increment tested count."""
        with self._lock:
            self.stats.tested += count
        self.display.update()
    
    def add_callback(self, callback: callable):
        """Add progress callback (for Telegram etc)."""
        self._callbacks.append(callback)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current stats as dict."""
        return {
            "target": f"{self.stats.target_host}:{self.stats.target_port}",
            "protocol": self.stats.protocol,
            "stage": self.stats.stage,
            "tested": self.stats.tested,
            "total": self.stats.total_attempts,
            "progress": f"{self.stats.progress_percent:.1f}%",
            "rate": self.stats.rate_str,
            "elapsed": self.stats.elapsed_str,
            "found": self.stats.found_count,
            "credentials": self.stats.found_credentials,
            "last_error": self.stats.last_error
        }


def demo():
    """Demo the live status display."""
    console.print("[cyan]Starting demo...[/cyan]")
    time.sleep(1)
    
    monitor = AttackMonitor(
        target_host="192.168.1.100",
        target_port=22,
        protocol="ssh",
        total=1000
    )
    
    monitor.start()
    
    try:
        for i in range(100):
            monitor.update(tested=i * 10)
            
            if i == 30:
                monitor.set_error("Connection timeout")
            
            if i == 50:
                monitor.add_credential("admin", "password123")
            
            time.sleep(0.1)
        
        monitor.set_stage("completed")
        time.sleep(2)
        
    finally:
        monitor.stop()
    
    console.print("\n[green]Demo complete![/green]")


if __name__ == "__main__":
    demo()
