#!/usr/bin/env python3
"""
Aura's Bruter - Dictionary Attack Mode
Attack using wordlist files for usernames and passwords
"""

import os
from typing import Iterator, Tuple, Optional, List
from pathlib import Path


class DictionaryAttack:
    """
    Dictionary-based attack using wordlist files.
    
    Supports:
    - Separate username and password files
    - Combined combo file (user:pass format)
    - Custom schema patterns
    """
    
    def __init__(
        self,
        users_file: str = None,
        passwords_file: str = None,
        combo_file: str = None,
        schema: str = "{user}:{pass}"
    ):
        """
        Initialize dictionary attack.
        
        Args:
            users_file: Path to username wordlist
            passwords_file: Path to password wordlist
            combo_file: Path to combined user:pass file
            schema: Format schema for combo file (e.g., "{user}:{pass}", "{pass}@{user}")
        """
        self.users_file = users_file
        self.passwords_file = passwords_file
        self.combo_file = combo_file
        self.schema = schema
        
        # Calculate positions
        self._users: List[str] = []
        self._passwords: List[str] = []
        self._combos: List[Tuple[str, str]] = []
        self._loaded = False
    
    def _load_file(self, filepath: str) -> List[str]:
        """Load lines from a file."""
        if not filepath or not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    
    def _parse_combo_line(self, line: str) -> Optional[Tuple[str, str]]:
        """Parse a combo line according to the schema."""
        line = line.strip()
        if not line:
            return None
        
        # Parse schema to find separator and order
        schema = self.schema.lower()
        
        # Common patterns
        if "{user}:{pass}" in schema or schema == "{user}:{pass}":
            if ':' in line:
                parts = line.split(':', 1)
                return (parts[0], parts[1])
        
        elif "{pass}:{user}" in schema:
            if ':' in line:
                parts = line.split(':', 1)
                return (parts[1], parts[0])
        
        elif "{user};{pass}" in schema:
            if ';' in line:
                parts = line.split(';', 1)
                return (parts[0], parts[1])
        
        elif "{user}|{pass}" in schema:
            if '|' in line:
                parts = line.split('|', 1)
                return (parts[0], parts[1])
        
        elif "{user} {pass}" in schema:
            if ' ' in line:
                parts = line.split(' ', 1)
                return (parts[0], parts[1])
        
        elif "{user}\t{pass}" in schema:
            if '\t' in line:
                parts = line.split('\t', 1)
                return (parts[0], parts[1])
        
        # Default: try colon separator
        if ':' in line:
            parts = line.split(':', 1)
            return (parts[0], parts[1])
        
        return None
    
    def load(self) -> int:
        """
        Load wordlists from files.
        
        Returns:
            Total number of combinations
        """
        if self.combo_file:
            # Load combo file
            lines = self._load_file(self.combo_file)
            for line in lines:
                combo = self._parse_combo_line(line)
                if combo:
                    self._combos.append(combo)
        else:
            # Load separate files
            self._users = self._load_file(self.users_file)
            self._passwords = self._load_file(self.passwords_file)
        
        self._loaded = True
        return self.total_combinations
    
    @property
    def total_combinations(self) -> int:
        """Get total number of credential combinations."""
        if self._combos:
            return len(self._combos)
        return len(self._users) * len(self._passwords)
    
    def generate(
        self,
        start_user_idx: int = 0,
        start_pass_idx: int = 0
    ) -> Iterator[Tuple[str, str, int, int]]:
        """
        Generate credential combinations.
        
        Yields:
            Tuple of (username, password, user_index, pass_index)
        """
        if not self._loaded:
            self.load()
        
        if self._combos:
            # Combo mode
            for i, (user, passwd) in enumerate(self._combos):
                if i < start_user_idx:
                    continue
                yield (user, passwd, i, 0)
        else:
            # Separate files mode
            for u_idx, user in enumerate(self._users):
                if u_idx < start_user_idx:
                    continue
                
                for p_idx, passwd in enumerate(self._passwords):
                    # Skip already tested combinations
                    if u_idx == start_user_idx and p_idx < start_pass_idx:
                        continue
                    
                    yield (user, passwd, u_idx, p_idx)
    
    def validate_files(self) -> dict:
        """Validate that the required files exist and are readable."""
        result = {
            "valid": True,
            "errors": [],
            "stats": {}
        }
        
        if self.combo_file:
            if not os.path.exists(self.combo_file):
                result["valid"] = False
                result["errors"].append(f"Combo file not found: {self.combo_file}")
            else:
                lines = self._load_file(self.combo_file)
                result["stats"]["combos"] = len(lines)
        else:
            if self.users_file:
                if not os.path.exists(self.users_file):
                    result["valid"] = False
                    result["errors"].append(f"Users file not found: {self.users_file}")
                else:
                    users = self._load_file(self.users_file)
                    result["stats"]["users"] = len(users)
            else:
                result["valid"] = False
                result["errors"].append("No users file specified")
            
            if self.passwords_file:
                if not os.path.exists(self.passwords_file):
                    result["valid"] = False
                    result["errors"].append(f"Passwords file not found: {self.passwords_file}")
                else:
                    passwords = self._load_file(self.passwords_file)
                    result["stats"]["passwords"] = len(passwords)
            else:
                result["valid"] = False
                result["errors"].append("No passwords file specified")
        
        return result
    
    def get_stats(self) -> dict:
        """Get statistics about the loaded wordlists."""
        return {
            "users_count": len(self._users),
            "passwords_count": len(self._passwords),
            "combos_count": len(self._combos),
            "total_combinations": self.total_combinations,
            "mode": "combo" if self._combos else "separate"
        }


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("[yellow]Dictionary Attack Module - Demo Mode[/yellow]")
    
    # Create demo files
    demo_users = ["admin", "root", "user", "test"]
    demo_passwords = ["password", "123456", "admin", "root", "test123"]
    
    table = Table(title="DictionaryAttack Options")
    table.add_column("Parameter", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("users_file", "Path to username wordlist file")
    table.add_row("passwords_file", "Path to password wordlist file")
    table.add_row("combo_file", "Path to combined user:pass file")
    table.add_row("schema", "Format schema for combo parsing")
    
    console.print(table)
    
    console.print("\n[green]Supported schemas:[/green]")
    schemas = [
        "{user}:{pass}  →  admin:password123",
        "{pass}:{user}  →  password123:admin",
        "{user};{pass}  →  admin;password123",
        "{user}|{pass}  →  admin|password123",
        "{user} {pass}  →  admin password123",
    ]
    for schema in schemas:
        console.print(f"  • {schema}")
