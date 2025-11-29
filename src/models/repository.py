"""Repository-related data models."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
import json


@dataclass
class Repository:
    """Basic repository information."""
    
    name: str
    full_name: str
    owner: str
    url: str
    default_branch: str
    visibility: str  # public, private
    created_at: datetime
    updated_at: datetime
    
    def validate(self) -> None:
        """Validate repository data integrity."""
        if not self.name:
            raise ValueError("Repository name cannot be empty")
        if not self.full_name:
            raise ValueError("Repository full_name cannot be empty")
        if not self.owner:
            raise ValueError("Repository owner cannot be empty")
        if not self.url:
            raise ValueError("Repository URL cannot be empty")
        if self.visibility not in ["public", "private"]:
            raise ValueError(f"Invalid visibility: {self.visibility}")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be after updated_at")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Repository':
        """Deserialize from dictionary."""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Repository':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class CommitSummary:
    """Summary of a single commit."""
    
    sha: str
    message: str
    author: str
    date: datetime
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'sha': self.sha,
            'message': self.message,
            'author': self.author,
            'date': self.date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CommitSummary':
        """Deserialize from dictionary."""
        data = data.copy()
        data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)


@dataclass
class RepositoryOverview:
    """Detailed repository content."""
    
    repository: Repository
    readme_content: Optional[str]
    file_structure: List[str]  # Top-level files and directories
    languages: Dict[str, int]  # Language -> bytes of code
    has_ci_config: bool
    has_tests: bool
    has_contributing: bool
    
    def validate(self) -> None:
        """Validate repository overview data integrity."""
        self.repository.validate()
        if not isinstance(self.file_structure, list):
            raise ValueError("file_structure must be a list")
        if not isinstance(self.languages, dict):
            raise ValueError("languages must be a dictionary")
        if not isinstance(self.has_ci_config, bool):
            raise ValueError("has_ci_config must be a boolean")
        if not isinstance(self.has_tests, bool):
            raise ValueError("has_tests must be a boolean")
        if not isinstance(self.has_contributing, bool):
            raise ValueError("has_contributing must be a boolean")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'repository': self.repository.to_dict(),
            'readme_content': self.readme_content,
            'file_structure': self.file_structure,
            'languages': self.languages,
            'has_ci_config': self.has_ci_config,
            'has_tests': self.has_tests,
            'has_contributing': self.has_contributing
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RepositoryOverview':
        """Deserialize from dictionary."""
        data = data.copy()
        data['repository'] = Repository.from_dict(data['repository'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RepositoryOverview':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class RepositoryHistory:
    """Repository activity data."""
    
    commit_count: int
    last_commit_date: datetime
    recent_commits: List[CommitSummary]
    open_issues_count: int
    closed_issues_count: int
    open_prs_count: int
    merged_prs_count: int
    contributors_count: int
    
    def validate(self) -> None:
        """Validate repository history data integrity."""
        if self.commit_count < 0:
            raise ValueError("commit_count cannot be negative")
        if self.open_issues_count < 0:
            raise ValueError("open_issues_count cannot be negative")
        if self.closed_issues_count < 0:
            raise ValueError("closed_issues_count cannot be negative")
        if self.open_prs_count < 0:
            raise ValueError("open_prs_count cannot be negative")
        if self.merged_prs_count < 0:
            raise ValueError("merged_prs_count cannot be negative")
        if self.contributors_count < 0:
            raise ValueError("contributors_count cannot be negative")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'commit_count': self.commit_count,
            'last_commit_date': self.last_commit_date.isoformat(),
            'recent_commits': [c.to_dict() for c in self.recent_commits],
            'open_issues_count': self.open_issues_count,
            'closed_issues_count': self.closed_issues_count,
            'open_prs_count': self.open_prs_count,
            'merged_prs_count': self.merged_prs_count,
            'contributors_count': self.contributors_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RepositoryHistory':
        """Deserialize from dictionary."""
        data = data.copy()
        data['last_commit_date'] = datetime.fromisoformat(data['last_commit_date'])
        data['recent_commits'] = [CommitSummary.from_dict(c) for c in data['recent_commits']]
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RepositoryHistory':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
