"""Health assessment data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import List
import json

from .repository import Repository


@dataclass
class HealthSnapshot:
    """Repository health assessment."""
    
    activity_level: str  # active, moderate, stale, abandoned
    test_coverage: str  # good, partial, none, unknown
    documentation_quality: str  # excellent, good, basic, poor
    ci_cd_status: str  # configured, missing
    dependency_status: str  # current, outdated, unknown
    overall_health_score: float  # 0.0 to 1.0
    issues_identified: List[str]
    
    def validate(self) -> None:
        """Validate health snapshot data integrity."""
        valid_activity_levels = ["active", "moderate", "stale", "abandoned"]
        if self.activity_level not in valid_activity_levels:
            raise ValueError(f"Invalid activity_level: {self.activity_level}")
        
        valid_test_coverage = ["good", "partial", "none", "unknown"]
        if self.test_coverage not in valid_test_coverage:
            raise ValueError(f"Invalid test_coverage: {self.test_coverage}")
        
        valid_doc_quality = ["excellent", "good", "basic", "poor"]
        if self.documentation_quality not in valid_doc_quality:
            raise ValueError(f"Invalid documentation_quality: {self.documentation_quality}")
        
        valid_ci_cd = ["configured", "missing"]
        if self.ci_cd_status not in valid_ci_cd:
            raise ValueError(f"Invalid ci_cd_status: {self.ci_cd_status}")
        
        valid_dependency = ["current", "outdated", "unknown"]
        if self.dependency_status not in valid_dependency:
            raise ValueError(f"Invalid dependency_status: {self.dependency_status}")
        
        if not 0.0 <= self.overall_health_score <= 1.0:
            raise ValueError(f"overall_health_score must be between 0.0 and 1.0")
        
        if not isinstance(self.issues_identified, list):
            raise ValueError("issues_identified must be a list")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'activity_level': self.activity_level,
            'test_coverage': self.test_coverage,
            'documentation_quality': self.documentation_quality,
            'ci_cd_status': self.ci_cd_status,
            'dependency_status': self.dependency_status,
            'overall_health_score': self.overall_health_score,
            'issues_identified': self.issues_identified
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HealthSnapshot':
        """Deserialize from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HealthSnapshot':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class RepositoryProfile:
    """Compact repository summary for memory."""
    
    repository: Repository
    purpose: str  # LLM-generated description
    tech_stack: List[str]
    key_files: List[str]
    health: HealthSnapshot
    last_analyzed: datetime
    analysis_version: str
    
    def validate(self) -> None:
        """Validate repository profile data integrity."""
        self.repository.validate()
        self.health.validate()
        
        if not self.purpose:
            raise ValueError("purpose cannot be empty")
        if not isinstance(self.tech_stack, list):
            raise ValueError("tech_stack must be a list")
        if not isinstance(self.key_files, list):
            raise ValueError("key_files must be a list")
        if not self.analysis_version:
            raise ValueError("analysis_version cannot be empty")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'repository': self.repository.to_dict(),
            'purpose': self.purpose,
            'tech_stack': self.tech_stack,
            'key_files': self.key_files,
            'health': self.health.to_dict(),
            'last_analyzed': self.last_analyzed.isoformat(),
            'analysis_version': self.analysis_version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RepositoryProfile':
        """Deserialize from dictionary."""
        data = data.copy()
        data['repository'] = Repository.from_dict(data['repository'])
        data['health'] = HealthSnapshot.from_dict(data['health'])
        data['last_analyzed'] = datetime.fromisoformat(data['last_analyzed'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RepositoryProfile':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
