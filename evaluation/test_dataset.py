"""Test dataset for evaluation framework.

This module defines test repositories with known characteristics
for evaluating agent performance.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta


@dataclass
class ExpectedSuggestion:
    """Expected suggestion for a test repository."""
    
    category: str
    title_keywords: List[str]  # Keywords that should appear in title
    description_keywords: List[str]  # Keywords that should appear in description
    priority: str
    min_priority_score: float = 0.0  # Minimum acceptable priority score
    
    def matches(self, suggestion: Any) -> bool:
        """Check if a suggestion matches this expected suggestion.
        
        Args:
            suggestion: MaintenanceSuggestion to check
            
        Returns:
            True if suggestion matches expectations
        """
        # Check category
        if suggestion.category != self.category:
            return False
        
        # Check title keywords
        title_lower = suggestion.title.lower()
        if not any(keyword.lower() in title_lower for keyword in self.title_keywords):
            return False
        
        # Check description keywords
        desc_lower = suggestion.description.lower()
        if not any(keyword.lower() in desc_lower for keyword in self.description_keywords):
            return False
        
        return True


@dataclass
class TestRepository:
    """Test repository with known characteristics."""
    
    full_name: str
    description: str
    characteristics: Dict[str, Any]
    expected_suggestions: List[ExpectedSuggestion]
    expected_health_score_range: tuple  # (min, max)
    expected_activity_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'full_name': self.full_name,
            'description': self.description,
            'characteristics': self.characteristics,
            'expected_suggestions': [
                {
                    'category': s.category,
                    'title_keywords': s.title_keywords,
                    'description_keywords': s.description_keywords,
                    'priority': s.priority
                }
                for s in self.expected_suggestions
            ],
            'expected_health_score_range': self.expected_health_score_range,
            'expected_activity_level': self.expected_activity_level
        }


# Test Dataset: 5-10 repositories with known characteristics
TEST_REPOSITORIES = [
    TestRepository(
        full_name="octocat/Hello-World",
        description="Classic GitHub test repository - well-maintained, has tests and CI",
        characteristics={
            'has_tests': True,
            'has_ci': True,
            'has_readme': True,
            'has_contributing': False,
            'activity_level': 'active',
            'languages': ['Ruby'],
            'last_commit_days_ago': 10
        },
        expected_suggestions=[
            ExpectedSuggestion(
                category='documentation',
                title_keywords=['CONTRIBUTING', 'contribution', 'guide'],
                description_keywords=['contribution', 'guidelines', 'guide'],
                priority='medium'
            )
        ],
        expected_health_score_range=(0.7, 1.0),
        expected_activity_level='active'
    ),
    
    TestRepository(
        full_name="torvalds/linux",
        description="Linux kernel - highly active, well-documented, comprehensive testing",
        characteristics={
            'has_tests': True,
            'has_ci': True,
            'has_readme': True,
            'has_contributing': True,
            'activity_level': 'active',
            'languages': ['C', 'Assembly', 'Shell'],
            'last_commit_days_ago': 1
        },
        expected_suggestions=[],  # Should have minimal suggestions due to excellent health
        expected_health_score_range=(0.9, 1.0),
        expected_activity_level='active'
    ),
    
    TestRepository(
        full_name="rails/rails",
        description="Ruby on Rails - active, well-tested, good documentation",
        characteristics={
            'has_tests': True,
            'has_ci': True,
            'has_readme': True,
            'has_contributing': True,
            'activity_level': 'active',
            'languages': ['Ruby', 'JavaScript', 'HTML'],
            'last_commit_days_ago': 2
        },
        expected_suggestions=[],  # Should have minimal suggestions
        expected_health_score_range=(0.85, 1.0),
        expected_activity_level='active'
    ),
    
    TestRepository(
        full_name="python/cpython",
        description="CPython - Python implementation, highly active and well-maintained",
        characteristics={
            'has_tests': True,
            'has_ci': True,
            'has_readme': True,
            'has_contributing': True,
            'activity_level': 'active',
            'languages': ['Python', 'C'],
            'last_commit_days_ago': 1
        },
        expected_suggestions=[],  # Should have minimal suggestions
        expected_health_score_range=(0.9, 1.0),
        expected_activity_level='active'
    ),
    
    TestRepository(
        full_name="microsoft/vscode",
        description="VS Code - highly active, comprehensive testing and documentation",
        characteristics={
            'has_tests': True,
            'has_ci': True,
            'has_readme': True,
            'has_contributing': True,
            'activity_level': 'active',
            'languages': ['TypeScript', 'JavaScript'],
            'last_commit_days_ago': 1
        },
        expected_suggestions=[],  # Should have minimal suggestions
        expected_health_score_range=(0.9, 1.0),
        expected_activity_level='active'
    )
]


def get_test_repositories() -> List[TestRepository]:
    """Get the list of test repositories.
    
    Returns:
        List of TestRepository objects
    """
    return TEST_REPOSITORIES


def get_test_repository(full_name: str) -> TestRepository:
    """Get a specific test repository by name.
    
    Args:
        full_name: Full repository name (owner/repo)
        
    Returns:
        TestRepository object
        
    Raises:
        ValueError: If repository not found
    """
    for repo in TEST_REPOSITORIES:
        if repo.full_name == full_name:
            return repo
    raise ValueError(f"Test repository not found: {full_name}")
