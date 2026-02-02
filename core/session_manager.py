#!/usr/bin/env python3
"""
Aura's Bruter - Session Manager
Save, load, and resume interrupted attack sessions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class AttackProgress:
    """Tracks the progress of an attack."""
    total_combinations: int = 0
    tested: int = 0
    current_user_index: int = 0
    current_pass_index: int = 0
    found_count: int = 0


@dataclass
class SessionData:
    """Complete session data for save/resume."""
    session_id: str
    protocol: str  # ssh, ftp, telnet
    mode: str  # dictionary, generation
    target_host: str
    target_port: int
    
    # Attack configuration
    attack_config: Dict[str, Any]
    
    # Progress tracking
    progress: AttackProgress
    
    # Found credentials
    found_credentials: List[Dict[str, str]]
    
    # Timestamps
    created_at: str
    updated_at: str
    
    # Status
    status: str  # running, paused, completed, failed


class SessionManager:
    """
    Manages attack sessions including save, load, and resume functionality.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.current_session: Optional[SessionData] = None
        self.auto_save_interval = 100  # Save every N attempts
        self.attempts_since_save = 0
    
    def create_session(
        self,
        protocol: str,
        mode: str,
        target_host: str,
        target_port: int,
        attack_config: Dict[str, Any],
        total_combinations: int
    ) -> SessionData:
        """Create a new attack session."""
        now = datetime.now()
        session_id = f"aura_{now.strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = SessionData(
            session_id=session_id,
            protocol=protocol,
            mode=mode,
            target_host=target_host,
            target_port=target_port,
            attack_config=attack_config,
            progress=AttackProgress(total_combinations=total_combinations),
            found_credentials=[],
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            status="running"
        )
        
        self.save()
        return self.current_session
    
    def save(self) -> str:
        """Save current session to file."""
        if not self.current_session:
            raise ValueError("No active session to save")
        
        self.current_session.updated_at = datetime.now().isoformat()
        
        filepath = self.sessions_dir / f"{self.current_session.session_id}.json"
        
        # Convert dataclass to dict
        data = {
            "session_id": self.current_session.session_id,
            "protocol": self.current_session.protocol,
            "mode": self.current_session.mode,
            "target_host": self.current_session.target_host,
            "target_port": self.current_session.target_port,
            "attack_config": self.current_session.attack_config,
            "progress": asdict(self.current_session.progress),
            "found_credentials": self.current_session.found_credentials,
            "created_at": self.current_session.created_at,
            "updated_at": self.current_session.updated_at,
            "status": self.current_session.status
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.attempts_since_save = 0
        return str(filepath)
    
    def load(self, session_path: str) -> SessionData:
        """Load a session from file."""
        filepath = Path(session_path)
        
        if not filepath.exists():
            # Try in sessions directory
            filepath = self.sessions_dir / session_path
            if not filepath.exists():
                filepath = self.sessions_dir / f"{session_path}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {session_path}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.current_session = SessionData(
            session_id=data["session_id"],
            protocol=data["protocol"],
            mode=data["mode"],
            target_host=data["target_host"],
            target_port=data["target_port"],
            attack_config=data["attack_config"],
            progress=AttackProgress(**data["progress"]),
            found_credentials=data["found_credentials"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=data["status"]
        )
        
        return self.current_session
    
    def update_progress(
        self,
        tested: int = None,
        user_index: int = None,
        pass_index: int = None,
        auto_save: bool = True
    ):
        """Update the current session progress."""
        if not self.current_session:
            return
        
        if tested is not None:
            self.current_session.progress.tested = tested
        if user_index is not None:
            self.current_session.progress.current_user_index = user_index
        if pass_index is not None:
            self.current_session.progress.current_pass_index = pass_index
        
        self.attempts_since_save += 1
        
        # Auto-save periodically
        if auto_save and self.attempts_since_save >= self.auto_save_interval:
            self.save()
    
    def add_credential(self, username: str, password: str):
        """Add a found credential to the session."""
        if not self.current_session:
            return
        
        self.current_session.found_credentials.append({
            "username": username,
            "password": password,
            "found_at": datetime.now().isoformat()
        })
        self.current_session.progress.found_count += 1
        
        # Always save when credential is found
        self.save()
    
    def complete(self, status: str = "completed"):
        """Mark the session as complete."""
        if self.current_session:
            self.current_session.status = status
            self.save()
    
    def pause(self):
        """Pause the current session."""
        if self.current_session:
            self.current_session.status = "paused"
            self.save()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        sessions = []
        
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "protocol": data["protocol"],
                    "target": f"{data['target_host']}:{data['target_port']}",
                    "progress": f"{data['progress']['tested']}/{data['progress']['total_combinations']}",
                    "found": data['progress']['found_count'],
                    "status": data["status"],
                    "updated_at": data["updated_at"]
                })
            except Exception:
                continue
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        filepath = self.sessions_dir / f"{session_id}.json"
        
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def get_resume_info(self) -> Dict[str, Any]:
        """Get information needed to resume the current session."""
        if not self.current_session:
            return {}
        
        return {
            "start_user_index": self.current_session.progress.current_user_index,
            "start_pass_index": self.current_session.progress.current_pass_index,
            "already_tested": self.current_session.progress.tested,
            "previous_credentials": self.current_session.found_credentials
        }


if __name__ == "__main__":
    # Demo the session manager
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    sm = SessionManager()
    
    # Create a demo session
    session = sm.create_session(
        protocol="ssh",
        mode="dictionary",
        target_host="192.168.1.100",
        target_port=22,
        attack_config={
            "users_file": "users.txt",
            "passwords_file": "passwords.txt",
            "threads": 10
        },
        total_combinations=50000
    )
    
    console.print(f"[green]Created session: {session.session_id}[/green]")
    
    # Simulate some progress
    for i in range(250):
        sm.update_progress(tested=i+1, user_index=i // 100, pass_index=i % 100)
        
        # Simulate finding a credential
        if i == 123:
            sm.add_credential("admin", "password123")
    
    # List sessions
    table = Table(title="Saved Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Protocol", style="magenta")
    table.add_column("Target", style="yellow")
    table.add_column("Progress", style="green")
    table.add_column("Found", style="red")
    table.add_column("Status", style="blue")
    
    for sess in sm.list_sessions():
        table.add_row(
            sess["session_id"],
            sess["protocol"],
            sess["target"],
            sess["progress"],
            str(sess["found"]),
            sess["status"]
        )
    
    console.print(table)
