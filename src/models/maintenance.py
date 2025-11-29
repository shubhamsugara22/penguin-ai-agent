"""Maintenance suggestion data models."""

from dataclasses import dataclass
from typing import List
import json

from .repository import Repository


@dataclass
class MaintenanceSuggestion:
    """Actionable maintenance task."""
    
    id: str
    repository: Repository
    category: str  # bug, enhancement, documentation, refactor, security
    priority: str  # high, medium, low
    title: str
    description: str
    rationale: str
    estimated_effort: str  # small, medium, large
    labels: List[str]
    
    def validate(self) -> None:
        """Validate maintenance suggestion data integrity."""
        self.repository.validate()
        
        if not self.id:
            raise ValueError("id cannot be empty")
        
        valid_categories = ["bug", "enhancement", "documentation", "refactor", "security"]
        if self.category not in valid_categories:
            raise ValueError(f"Invalid category: {self.category}")
        
        valid_priorities = ["high", "medium", "low"]
        if self.priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {self.priority}")
        
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.description:
            raise ValueError("description cannot be empty")
        if not self.rationale:
            raise ValueError("rationale cannot be empty")
        
        valid_efforts = ["small", "medium", "large"]
        if self.estimated_effort not in valid_efforts:
            raise ValueError(f"Invalid estimated_effort: {self.estimated_effort}")
        
        if not isinstance(self.labels, list):
            raise ValueError("labels must be a list")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'repository': self.repository.to_dict(),
            'category': self.category,
            'priority': self.priority,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'estimated_effort': self.estimated_effort,
            'labels': self.labels
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MaintenanceSuggestion':
        """Deserialize from dictionary."""
        data = data.copy()
        data['repository'] = Repository.from_dict(data['repository'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MaintenanceSuggestion':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class IssueResult:
    """Result of creating a GitHub issue."""
    
    success: bool
    issue_url: str
    issue_number: int
    error_message: str = ""
    
    def validate(self) -> None:
        """Validate issue result data integrity."""
        if self.success and not self.issue_url:
            raise ValueError("issue_url cannot be empty when success is True")
        if self.success and self.issue_number <= 0:
            raise ValueError("issue_number must be positive when success is True")
        if not self.success and not self.error_message:
            raise ValueError("error_message cannot be empty when success is False")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'success': self.success,
            'issue_url': self.issue_url,
            'issue_number': self.issue_number,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IssueResult':
        """Deserialize from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IssueResult':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
