"""Session and metrics data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import json

from .maintenance import MaintenanceSuggestion, IssueResult


@dataclass
class SessionMetrics:
    """Metrics for observability."""
    
    repos_analyzed: int = 0
    suggestions_generated: int = 0
    issues_created: int = 0
    api_calls_made: int = 0
    tokens_used: int = 0
    execution_time_seconds: float = 0.0
    errors_encountered: int = 0
    
    def validate(self) -> None:
        """Validate session metrics data integrity."""
        if self.repos_analyzed < 0:
            raise ValueError("repos_analyzed cannot be negative")
        if self.suggestions_generated < 0:
            raise ValueError("suggestions_generated cannot be negative")
        if self.issues_created < 0:
            raise ValueError("issues_created cannot be negative")
        if self.api_calls_made < 0:
            raise ValueError("api_calls_made cannot be negative")
        if self.tokens_used < 0:
            raise ValueError("tokens_used cannot be negative")
        if self.execution_time_seconds < 0:
            raise ValueError("execution_time_seconds cannot be negative")
        if self.errors_encountered < 0:
            raise ValueError("errors_encountered cannot be negative")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'repos_analyzed': self.repos_analyzed,
            'suggestions_generated': self.suggestions_generated,
            'issues_created': self.issues_created,
            'api_calls_made': self.api_calls_made,
            'tokens_used': self.tokens_used,
            'execution_time_seconds': self.execution_time_seconds,
            'errors_encountered': self.errors_encountered
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionMetrics':
        """Deserialize from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SessionMetrics':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class SessionState:
    """State for current analysis session."""
    
    session_id: str
    username: str
    repositories_analyzed: List[str] = field(default_factory=list)
    suggestions_generated: List[MaintenanceSuggestion] = field(default_factory=list)
    issues_created: List[IssueResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    
    def validate(self) -> None:
        """Validate session state data integrity."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.username:
            raise ValueError("username cannot be empty")
        if not isinstance(self.repositories_analyzed, list):
            raise ValueError("repositories_analyzed must be a list")
        if not isinstance(self.suggestions_generated, list):
            raise ValueError("suggestions_generated must be a list")
        if not isinstance(self.issues_created, list):
            raise ValueError("issues_created must be a list")
        
        self.metrics.validate()
        
        for suggestion in self.suggestions_generated:
            suggestion.validate()
        
        for issue in self.issues_created:
            issue.validate()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'session_id': self.session_id,
            'username': self.username,
            'repositories_analyzed': self.repositories_analyzed,
            'suggestions_generated': [s.to_dict() for s in self.suggestions_generated],
            'issues_created': [i.to_dict() for i in self.issues_created],
            'start_time': self.start_time.isoformat(),
            'metrics': self.metrics.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Deserialize from dictionary."""
        data = data.copy()
        data['suggestions_generated'] = [
            MaintenanceSuggestion.from_dict(s) for s in data['suggestions_generated']
        ]
        data['issues_created'] = [
            IssueResult.from_dict(i) for i in data['issues_created']
        ]
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['metrics'] = SessionMetrics.from_dict(data['metrics'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SessionState':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class UserPreferences:
    """User configuration stored in long-term memory."""
    
    user_id: str
    automation_level: str = "manual"  # auto, manual, ask
    preferred_labels: List[str] = field(default_factory=list)
    excluded_repos: List[str] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)  # tests, docs, security, etc.
    
    def validate(self) -> None:
        """Validate user preferences data integrity."""
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        
        valid_automation_levels = ["auto", "manual", "ask"]
        if self.automation_level not in valid_automation_levels:
            raise ValueError(f"Invalid automation_level: {self.automation_level}")
        
        if not isinstance(self.preferred_labels, list):
            raise ValueError("preferred_labels must be a list")
        if not isinstance(self.excluded_repos, list):
            raise ValueError("excluded_repos must be a list")
        if not isinstance(self.focus_areas, list):
            raise ValueError("focus_areas must be a list")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'user_id': self.user_id,
            'automation_level': self.automation_level,
            'preferred_labels': self.preferred_labels,
            'excluded_repos': self.excluded_repos,
            'focus_areas': self.focus_areas
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserPreferences':
        """Deserialize from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UserPreferences':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
