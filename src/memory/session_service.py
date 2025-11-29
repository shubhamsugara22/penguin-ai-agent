"""Session management service for in-memory session state."""

import uuid
from typing import Dict, Optional
from datetime import datetime

from ..models import SessionState, SessionMetrics


class SessionService:
    """Manages in-memory session state for analysis runs."""
    
    def __init__(self):
        """Initialize the session service with empty storage."""
        self._sessions: Dict[str, SessionState] = {}
        self._current_session_id: Optional[str] = None
    
    def create_session(self, username: str) -> SessionState:
        """
        Create a new session for a user.
        
        Args:
            username: GitHub username for the session
            
        Returns:
            SessionState: The newly created session
        """
        session_id = str(uuid.uuid4())
        session = SessionState(
            session_id=session_id,
            username=username,
            repositories_analyzed=[],
            suggestions_generated=[],
            issues_created=[],
            start_time=datetime.now(),
            metrics=SessionMetrics()
        )
        
        self._sessions[session_id] = session
        self._current_session_id = session_id
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SessionState if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def get_current_session(self) -> Optional[SessionState]:
        """
        Get the current active session.
        
        Returns:
            SessionState if there is a current session, None otherwise
        """
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None
    
    def update_session(self, session: SessionState) -> None:
        """
        Update an existing session.
        
        Args:
            session: The session to update
            
        Raises:
            ValueError: If session doesn't exist
        """
        if session.session_id not in self._sessions:
            raise ValueError(f"Session {session.session_id} not found")
        
        session.validate()
        self._sessions[session.session_id] = session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._current_session_id == session_id:
                self._current_session_id = None
            return True
        return False
    
    def list_sessions(self) -> Dict[str, SessionState]:
        """
        List all sessions.
        
        Returns:
            Dictionary of session_id to SessionState
        """
        return self._sessions.copy()
    
    def clear_all_sessions(self) -> None:
        """Clear all sessions from memory."""
        self._sessions.clear()
        self._current_session_id = None
