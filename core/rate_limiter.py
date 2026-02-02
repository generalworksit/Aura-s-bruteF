#!/usr/bin/env python3
"""
Aura's Bruter - Rate Limiter with Fail2Ban Bypass Techniques
Implements adaptive delays and stealth features
"""

import random
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    enabled: bool = True
    base_delay: float = 0.5
    stealth_mode: bool = False
    randomize: bool = True
    max_delay: float = 10.0
    backoff_multiplier: float = 1.5


class RateLimiter:
    """
    Advanced rate limiter with fail2ban bypass techniques.
    
    Techniques:
    1. Adaptive delay - increases delay after failures
    2. Random jitter - adds ±30% randomization to appear human
    3. Stealth mode - very slow, careful attempts
    4. Exponential backoff - backs off on consecutive failures
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.consecutive_failures = 0
        self.total_attempts = 0
        self.last_attempt_time = 0.0
        self._enabled = self.config.enabled
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    def toggle(self) -> bool:
        """Toggle rate limiting on/off."""
        self._enabled = not self._enabled
        return self._enabled
    
    def get_delay(self) -> float:
        """
        Calculate the delay before next attempt.
        
        Returns:
            Delay in seconds
        """
        if not self._enabled:
            return 0.0
        
        # Base delay
        if self.config.stealth_mode:
            # Stealth mode: 5-15 seconds between attempts
            delay = random.uniform(5.0, 15.0)
        else:
            delay = self.config.base_delay
            
            # Apply exponential backoff for consecutive failures
            if self.consecutive_failures > 0:
                backoff = min(
                    self.config.backoff_multiplier ** self.consecutive_failures,
                    self.config.max_delay / self.config.base_delay
                )
                delay *= backoff
        
        # Add random jitter (±30%)
        if self.config.randomize:
            jitter = random.uniform(0.7, 1.3)
            delay *= jitter
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        return delay
    
    def wait(self) -> float:
        """
        Wait for the calculated delay.
        
        Returns:
            Actual time waited in seconds
        """
        delay = self.get_delay()
        
        if delay > 0:
            time.sleep(delay)
        
        self.last_attempt_time = time.time()
        self.total_attempts += 1
        
        return delay
    
    def record_success(self):
        """Record a successful attempt - resets failure counter."""
        self.consecutive_failures = 0
    
    def record_failure(self):
        """Record a failed attempt - increases backoff."""
        self.consecutive_failures += 1
    
    def record_connection_error(self):
        """
        Record a connection error (might indicate blocking).
        Applies heavier backoff.
        """
        self.consecutive_failures += 3  # Triple penalty for connection errors
    
    def reset(self):
        """Reset all counters."""
        self.consecutive_failures = 0
        self.total_attempts = 0
        self.last_attempt_time = 0.0
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "enabled": self._enabled,
            "stealth_mode": self.config.stealth_mode,
            "total_attempts": self.total_attempts,
            "consecutive_failures": self.consecutive_failures,
            "current_delay": self.get_delay(),
            "base_delay": self.config.base_delay
        }
    
    def set_stealth_mode(self, enabled: bool):
        """Enable or disable stealth mode."""
        self.config.stealth_mode = enabled
    
    def set_base_delay(self, delay: float):
        """Set the base delay between attempts."""
        self.config.base_delay = max(0.1, min(delay, self.config.max_delay))


class ProxyRotator:
    """
    Rotate through SOCKS5/HTTP proxies to avoid IP blocking.
    """
    
    def __init__(self, proxies: list = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()
    
    def add_proxy(self, proxy: str):
        """Add a proxy to the rotation."""
        self.proxies.append(proxy)
    
    def get_next(self) -> Optional[str]:
        """Get the next available proxy."""
        if not self.proxies:
            return None
        
        available = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available:
            # Reset failed proxies and try again
            self.failed_proxies.clear()
            available = self.proxies
        
        if not available:
            return None
        
        proxy = available[self.current_index % len(available)]
        self.current_index += 1
        
        return proxy
    
    def mark_failed(self, proxy: str):
        """Mark a proxy as failed."""
        self.failed_proxies.add(proxy)
    
    def reset(self):
        """Reset proxy rotation."""
        self.current_index = 0
        self.failed_proxies.clear()


if __name__ == "__main__":
    # Demo the rate limiter
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    rl = RateLimiter(RateLimitConfig(
        enabled=True,
        base_delay=0.5,
        stealth_mode=False,
        randomize=True
    ))
    
    table = Table(title="Rate Limiter Demo")
    table.add_column("Attempt", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Delay", style="green")
    table.add_column("Consecutive Failures", style="red")
    
    for i in range(10):
        delay = rl.get_delay()
        status = "Success" if random.random() > 0.7 else "Failure"
        
        table.add_row(
            str(i + 1),
            status,
            f"{delay:.2f}s",
            str(rl.consecutive_failures)
        )
        
        if status == "Success":
            rl.record_success()
        else:
            rl.record_failure()
    
    console.print(table)
