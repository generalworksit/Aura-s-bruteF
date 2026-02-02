#!/usr/bin/env python3
"""
Aura's Bruter - Logger
Structured logging and result export
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class AuraLogger:
    """
    Logger for Aura's Bruter.
    Handles both console and file logging, plus result exports.
    """
    
    def __init__(self, logs_dir: str = "logs", log_level: int = logging.INFO):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger("aura_bruter")
        self.logger.setLevel(log_level)
        
        # File handler
        log_file = self.logs_dir / f"aura_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Results storage
        self._credentials: List[Dict[str, str]] = []
        self._attack_log: List[Dict[str, Any]] = []
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def log_attack_start(
        self,
        target: str,
        port: int,
        protocol: str,
        mode: str,
        total_combinations: int
    ):
        """Log the start of an attack."""
        entry = {
            "event": "attack_start",
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "port": port,
            "protocol": protocol,
            "mode": mode,
            "total_combinations": total_combinations
        }
        self._attack_log.append(entry)
        self.logger.info(
            f"Attack started: {target}:{port} ({protocol}) - "
            f"{total_combinations:,} combinations"
        )
    
    def log_attack_end(
        self,
        tested: int,
        found: int,
        duration: float,
        status: str = "completed"
    ):
        """Log the end of an attack."""
        entry = {
            "event": "attack_end",
            "timestamp": datetime.now().isoformat(),
            "tested": tested,
            "found": found,
            "duration_seconds": duration,
            "status": status
        }
        self._attack_log.append(entry)
        self.logger.info(
            f"Attack {status}: Tested {tested:,}, Found {found}, "
            f"Duration {duration:.1f}s"
        )
    
    def log_credential_found(
        self,
        username: str,
        password: str,
        target: str,
        protocol: str
    ):
        """Log a found credential."""
        cred = {
            "username": username,
            "password": password,
            "target": target,
            "protocol": protocol,
            "found_at": datetime.now().isoformat()
        }
        self._credentials.append(cred)
        self.logger.info(f"CREDENTIAL FOUND: {username}:{password} @ {target}")
    
    def export_credentials(self, format: str = "json") -> str:
        """
        Export found credentials to file.
        
        Args:
            format: Export format ('json', 'csv', 'txt')
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filepath = self.logs_dir / f"credentials_{timestamp}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._credentials, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            filepath = self.logs_dir / f"credentials_{timestamp}.csv"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("username,password,target,protocol,found_at\n")
                for cred in self._credentials:
                    f.write(f"{cred['username']},{cred['password']},"
                           f"{cred['target']},{cred['protocol']},{cred['found_at']}\n")
        
        elif format == "txt":
            filepath = self.logs_dir / f"credentials_{timestamp}.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("AURA'S BRUTER - FOUND CREDENTIALS\n")
                f.write("=" * 50 + "\n\n")
                for cred in self._credentials:
                    f.write(f"Target:   {cred['target']}\n")
                    f.write(f"Protocol: {cred['protocol']}\n")
                    f.write(f"Username: {cred['username']}\n")
                    f.write(f"Password: {cred['password']}\n")
                    f.write(f"Found:    {cred['found_at']}\n")
                    f.write("-" * 50 + "\n")
        
        else:
            raise ValueError(f"Unknown format: {format}")
        
        return str(filepath)
    
    def export_attack_log(self) -> str:
        """Export attack log to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.logs_dir / f"attack_log_{timestamp}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._attack_log, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def get_credentials(self) -> List[Dict[str, str]]:
        """Get all found credentials."""
        return self._credentials.copy()
    
    def clear(self):
        """Clear stored credentials and logs."""
        self._credentials.clear()
        self._attack_log.clear()


# Global logger instance
_logger: Optional[AuraLogger] = None


def get_logger() -> AuraLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = AuraLogger()
    return _logger


if __name__ == "__main__":
    # Demo
    from rich.console import Console
    console = Console()
    
    logger = AuraLogger()
    
    # Simulate some logging
    logger.log_attack_start("192.168.1.100", 22, "SSH", "dictionary", 50000)
    logger.log_credential_found("admin", "password123", "192.168.1.100:22", "SSH")
    logger.log_credential_found("root", "toor", "192.168.1.100:22", "SSH")
    logger.log_attack_end(50000, 2, 1523.5)
    
    # Export
    json_path = logger.export_credentials("json")
    txt_path = logger.export_credentials("txt")
    
    console.print(f"[green]Exported to:[/green]")
    console.print(f"  - {json_path}")
    console.print(f"  - {txt_path}")
