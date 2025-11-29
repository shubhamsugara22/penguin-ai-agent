"""Unit tests for data models."""

import pytest
from datetime import datetime
from src.models import (
    Repository,
    CommitSummary,
    RepositoryOverview,
    RepositoryHistory,
    HealthSnapshot,
    RepositoryProfile,
    MaintenanceSuggestion,
    IssueResult,
    SessionMetrics,
    SessionState,
    UserPreferences,
)


class TestRepository:
    """Test Repository model."""
    
    def test_repository_creation(self):
        """Test creating a repository instance."""
        repo = Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
        assert repo.name == "test-repo"
        assert repo.visibility == "public"
    
    def test_repository_validation(self):
        """Test repository validation."""
        repo = Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
        repo.validate()  # Should not raise
        
        # Test invalid visibility
        repo.visibility = "invalid"
        with pytest.raises(ValueError, match="Invalid visibility"):
            repo.validate()
    
    def test_repository_serialization(self):
        """Test repository serialization/deserialization."""
        repo = Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
        
        # Test dict round-trip
        repo_dict = repo.to_dict()
        repo_restored = Repository.from_dict(repo_dict)
        assert repo == repo_restored
        
        # Test JSON round-trip
        repo_json = repo.to_json()
        repo_from_json = Repository.from_json(repo_json)
        assert repo == repo_from_json


class TestHealthSnapshot:
    """Test HealthSnapshot model."""
    
    def test_health_snapshot_creation(self):
        """Test creating a health snapshot."""
        health = HealthSnapshot(
            activity_level="active",
            test_coverage="good",
            documentation_quality="excellent",
            ci_cd_status="configured",
            dependency_status="current",
            overall_health_score=0.9,
            issues_identified=["No issues found"]
        )
        assert health.activity_level == "active"
        assert health.overall_health_score == 0.9
    
    def test_health_snapshot_validation(self):
        """Test health snapshot validation."""
        health = HealthSnapshot(
            activity_level="active",
            test_coverage="good",
            documentation_quality="excellent",
            ci_cd_status="configured",
            dependency_status="current",
            overall_health_score=0.9,
            issues_identified=[]
        )
        health.validate()  # Should not raise
        
        # Test invalid score
        health.overall_health_score = 1.5
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            health.validate()
    
    def test_health_snapshot_serialization(self):
        """Test health snapshot serialization."""
        health = HealthSnapshot(
            activity_level="moderate",
            test_coverage="partial",
            documentation_quality="good",
            ci_cd_status="missing",
            dependency_status="outdated",
            overall_health_score=0.6,
            issues_identified=["Missing tests", "Outdated dependencies"]
        )
        
        health_dict = health.to_dict()
        health_restored = HealthSnapshot.from_dict(health_dict)
        assert health == health_restored


class TestMaintenanceSuggestion:
    """Test MaintenanceSuggestion model."""
    
    def test_suggestion_creation(self):
        """Test creating a maintenance suggestion."""
        repo = Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="documentation",
            priority="high",
            title="Add README",
            description="Repository needs a README file",
            rationale="README helps users understand the project",
            estimated_effort="small",
            labels=["documentation", "good-first-issue"]
        )
        assert suggestion.category == "documentation"
        assert suggestion.priority == "high"
    
    def test_suggestion_validation(self):
        """Test suggestion validation."""
        repo = Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="bug",
            priority="high",
            title="Fix bug",
            description="Bug description",
            rationale="Bug rationale",
            estimated_effort="medium",
            labels=["bug"]
        )
        suggestion.validate()  # Should not raise
        
        # Test invalid category
        suggestion.category = "invalid"
        with pytest.raises(ValueError, match="Invalid category"):
            suggestion.validate()


class TestSessionState:
    """Test SessionState model."""
    
    def test_session_state_creation(self):
        """Test creating a session state."""
        session = SessionState(
            session_id="sess-001",
            username="testuser"
        )
        assert session.session_id == "sess-001"
        assert session.username == "testuser"
        assert len(session.repositories_analyzed) == 0
    
    def test_session_state_validation(self):
        """Test session state validation."""
        session = SessionState(
            session_id="sess-001",
            username="testuser"
        )
        session.validate()  # Should not raise
        
        # Test empty session_id
        session.session_id = ""
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            session.validate()
    
    def test_session_state_serialization(self):
        """Test session state serialization."""
        session = SessionState(
            session_id="sess-001",
            username="testuser",
            repositories_analyzed=["repo1", "repo2"]
        )
        
        session_dict = session.to_dict()
        session_restored = SessionState.from_dict(session_dict)
        assert session.session_id == session_restored.session_id
        assert session.username == session_restored.username
        assert session.repositories_analyzed == session_restored.repositories_analyzed


class TestUserPreferences:
    """Test UserPreferences model."""
    
    def test_user_preferences_creation(self):
        """Test creating user preferences."""
        prefs = UserPreferences(
            user_id="user123",
            automation_level="manual",
            preferred_labels=["bug", "enhancement"],
            excluded_repos=["old-repo"],
            focus_areas=["tests", "docs"]
        )
        assert prefs.user_id == "user123"
        assert prefs.automation_level == "manual"
    
    def test_user_preferences_validation(self):
        """Test user preferences validation."""
        prefs = UserPreferences(user_id="user123")
        prefs.validate()  # Should not raise
        
        # Test invalid automation level
        prefs.automation_level = "invalid"
        with pytest.raises(ValueError, match="Invalid automation_level"):
            prefs.validate()
    
    def test_user_preferences_serialization(self):
        """Test user preferences serialization."""
        prefs = UserPreferences(
            user_id="user123",
            automation_level="auto",
            preferred_labels=["security"],
            excluded_repos=[],
            focus_areas=["security", "performance"]
        )
        
        prefs_dict = prefs.to_dict()
        prefs_restored = UserPreferences.from_dict(prefs_dict)
        assert prefs == prefs_restored


class TestSessionMetrics:
    """Test SessionMetrics model."""
    
    def test_session_metrics_creation(self):
        """Test creating session metrics."""
        metrics = SessionMetrics(
            repos_analyzed=5,
            suggestions_generated=10,
            issues_created=3,
            api_calls_made=25,
            tokens_used=5000,
            execution_time_seconds=45.5,
            errors_encountered=1
        )
        assert metrics.repos_analyzed == 5
        assert metrics.suggestions_generated == 10
    
    def test_session_metrics_validation(self):
        """Test session metrics validation."""
        metrics = SessionMetrics()
        metrics.validate()  # Should not raise
        
        # Test negative value
        metrics.repos_analyzed = -1
        with pytest.raises(ValueError, match="repos_analyzed cannot be negative"):
            metrics.validate()
