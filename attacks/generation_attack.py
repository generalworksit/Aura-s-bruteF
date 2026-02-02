#!/usr/bin/env python3
"""
Aura's Bruter - Generation Attack Mode
Generate password combinations based on character sets
"""

import itertools
import string
from typing import Iterator, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class CharsetConfig:
    """Configuration for character sets."""
    lowercase: bool = True
    uppercase: bool = False
    digits: bool = False
    symbols: bool = False
    custom: str = ""
    
    def get_charset(self) -> str:
        """Build the character set string."""
        chars = ""
        
        if self.lowercase:
            chars += string.ascii_lowercase
        if self.uppercase:
            chars += string.ascii_uppercase
        if self.digits:
            chars += string.digits
        if self.symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if self.custom:
            # Add custom chars, avoiding duplicates
            for c in self.custom:
                if c not in chars:
                    chars += c
        
        return chars


class GenerationAttack:
    """
    Password generation attack using character set combinations.
    
    Features:
    - Configurable character sets (lower, upper, digits, symbols)
    - Custom character sets
    - Min/max length configuration
    - Lazy generation (memory efficient)
    - Resume from specific position
    """
    
    def __init__(
        self,
        username: str,
        charset_config: Optional[CharsetConfig] = None,
        min_length: int = 1,
        max_length: int = 4,
        prefix: str = "",
        suffix: str = ""
    ):
        """
        Initialize generation attack.
        
        Args:
            username: Target username (single user for this mode)
            charset_config: Character set configuration
            min_length: Minimum password length
            max_length: Maximum password length
            prefix: Optional prefix for all passwords
            suffix: Optional suffix for all passwords
        """
        self.username = username
        self.charset = charset_config or CharsetConfig()
        self.min_length = max(1, min_length)
        self.max_length = max(self.min_length, max_length)
        self.prefix = prefix
        self.suffix = suffix
        
        self._chars = self.charset.get_charset()
    
    @property
    def total_combinations(self) -> int:
        """Calculate total number of combinations."""
        total = 0
        charset_len = len(self._chars)
        
        for length in range(self.min_length, self.max_length + 1):
            total += charset_len ** length
        
        return total
    
    def estimate_time(self, attempts_per_second: float = 10.0) -> dict:
        """
        Estimate time to complete the attack.
        
        Returns:
            Dict with total, seconds, and human-readable time
        """
        total = self.total_combinations
        seconds = total / attempts_per_second
        
        # Convert to human-readable
        if seconds < 60:
            human = f"{seconds:.1f} seconds"
        elif seconds < 3600:
            human = f"{seconds / 60:.1f} minutes"
        elif seconds < 86400:
            human = f"{seconds / 3600:.1f} hours"
        elif seconds < 31536000:
            human = f"{seconds / 86400:.1f} days"
        else:
            human = f"{seconds / 31536000:.1f} years"
        
        return {
            "total_combinations": total,
            "estimated_seconds": seconds,
            "human_readable": human,
            "at_speed": f"{attempts_per_second}/sec"
        }
    
    def generate(self, skip: int = 0) -> Iterator[Tuple[str, str, int, int]]:
        """
        Generate password combinations.
        
        Args:
            skip: Number of combinations to skip (for resume)
            
        Yields:
            Tuple of (username, password, current_index, 0)
        """
        current_idx = 0
        
        for length in range(self.min_length, self.max_length + 1):
            for combo in itertools.product(self._chars, repeat=length):
                if current_idx < skip:
                    current_idx += 1
                    continue
                
                password = self.prefix + ''.join(combo) + self.suffix
                yield (self.username, password, current_idx, 0)
                current_idx += 1
    
    def generate_batch(self, batch_size: int = 1000, skip: int = 0) -> Iterator[list]:
        """
        Generate passwords in batches for better performance.
        
        Yields:
            List of (username, password, index, 0) tuples
        """
        batch = []
        
        for cred in self.generate(skip=skip):
            batch.append(cred)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        if batch:
            yield batch
    
    def get_stats(self) -> dict:
        """Get statistics about the generation configuration."""
        return {
            "username": self.username,
            "charset": self._chars,
            "charset_size": len(self._chars),
            "min_length": self.min_length,
            "max_length": self.max_length,
            "prefix": self.prefix or "(none)",
            "suffix": self.suffix or "(none)",
            "total_combinations": self.total_combinations,
            "components": {
                "lowercase": self.charset.lowercase,
                "uppercase": self.charset.uppercase,
                "digits": self.charset.digits,
                "symbols": self.charset.symbols,
                "custom": self.charset.custom or "(none)"
            }
        }
    
    @staticmethod
    def get_charset_presets() -> dict:
        """Get common charset presets."""
        return {
            "lowercase": CharsetConfig(lowercase=True),
            "lowercase+digits": CharsetConfig(lowercase=True, digits=True),
            "lowercase+uppercase": CharsetConfig(lowercase=True, uppercase=True),
            "alphanumeric": CharsetConfig(lowercase=True, uppercase=True, digits=True),
            "all": CharsetConfig(lowercase=True, uppercase=True, digits=True, symbols=True),
            "digits_only": CharsetConfig(digits=True),
            "pin": CharsetConfig(digits=True),  # Same as digits_only
        }


class SmartGenerationAttack(GenerationAttack):
    """
    Smart password generation with common patterns.
    
    Generates passwords based on common patterns like:
    - word + digits (admin123)
    - Word with capital (Admin123)
    - word + year (password2024)
    - word + symbols (admin!)
    """
    
    COMMON_YEARS = [str(y) for y in range(2020, 2027)]
    COMMON_SUFFIXES = ["123", "1234", "12345", "!", "@", "#", "1", "01", "001"]
    COMMON_WORDS = [
        "password", "admin", "root", "user", "test", "login",
        "welcome", "master", "letmein", "monkey", "dragon", "qwerty"
    ]
    
    def __init__(self, username: str, base_words: list = None):
        """
        Initialize smart generation.
        
        Args:
            username: Target username
            base_words: Custom base words to use
        """
        super().__init__(
            username=username,
            charset_config=CharsetConfig(),
            min_length=1,
            max_length=12
        )
        self.base_words = base_words or self.COMMON_WORDS
        self._generated_passwords: Set[str] = set()
    
    @property
    def total_combinations(self) -> int:
        """Approximate count of combinations."""
        # This is an estimate
        return len(self.base_words) * (
            1 +  # Original word
            1 +  # Capitalized
            len(self.COMMON_SUFFIXES) * 2 +  # With suffixes
            len(self.COMMON_YEARS) * 2  # With years
        )
    
    def generate(self, skip: int = 0) -> Iterator[Tuple[str, str, int, int]]:
        """Generate smart password combinations."""
        current_idx = 0
        
        for word in self.base_words:
            variants = self._generate_variants(word)
            
            for password in variants:
                if password in self._generated_passwords:
                    continue
                    
                self._generated_passwords.add(password)
                
                if current_idx < skip:
                    current_idx += 1
                    continue
                
                yield (self.username, password, current_idx, 0)
                current_idx += 1
    
    def _generate_variants(self, word: str) -> list:
        """Generate password variants from a base word."""
        variants = [
            word,                          # original
            word.capitalize(),             # Capitalized
            word.upper(),                  # UPPERCASE
            word.lower(),                  # lowercase
        ]
        
        # Add suffixes
        for suffix in self.COMMON_SUFFIXES:
            variants.append(word + suffix)
            variants.append(word.capitalize() + suffix)
        
        # Add years
        for year in self.COMMON_YEARS:
            variants.append(word + year)
            variants.append(word.capitalize() + year)
        
        # Common substitutions (leet speak)
        leet = word.replace('a', '@').replace('e', '3').replace('i', '1').replace('o', '0')
        if leet != word:
            variants.append(leet)
            variants.append(leet + "123")
        
        return variants


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    console.print("[yellow]Generation Attack Module - Demo Mode[/yellow]\n")
    
    # Show charset options
    table = Table(title="Charset Options")
    table.add_column("Option", style="cyan")
    table.add_column("Characters", style="white")
    table.add_column("Count", style="green")
    
    table.add_row("lowercase", "a-z", "26")
    table.add_row("uppercase", "A-Z", "26")
    table.add_row("digits", "0-9", "10")
    table.add_row("symbols", "!@#$%^&*()_+-=[]{}|;:,.<>?", "27")
    table.add_row("custom", "User-defined characters", "Variable")
    
    console.print(table)
    
    # Show time estimates for different configs
    console.print("\n[green]Time Estimates (at 10 attempts/sec):[/green]")
    
    configs = [
        ("4 chars, lowercase", CharsetConfig(lowercase=True), 4, 4),
        ("4 chars, alphanumeric", CharsetConfig(lowercase=True, digits=True), 4, 4),
        ("6 chars, lowercase", CharsetConfig(lowercase=True), 6, 6),
        ("6 chars, all", CharsetConfig(lowercase=True, uppercase=True, digits=True, symbols=True), 6, 6),
    ]
    
    estimate_table = Table()
    estimate_table.add_column("Configuration", style="cyan")
    estimate_table.add_column("Combinations", style="yellow")
    estimate_table.add_column("Estimated Time", style="red")
    
    for name, charset, min_len, max_len in configs:
        gen = GenerationAttack(
            username="test",
            charset_config=charset,
            min_length=min_len,
            max_length=max_len
        )
        estimate = gen.estimate_time(10.0)
        estimate_table.add_row(
            name,
            f"{estimate['total_combinations']:,}",
            estimate['human_readable']
        )
    
    console.print(estimate_table)
