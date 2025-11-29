"""Tests for the Maintainer Agent."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.agents.maintainer import MaintainerAgent
from src.models.repository import Repository
from src.models.health import HealthSnapshot, RepositoryProfile
from src.models.maintenance import MaintenanceSuggestion, IssueResult
from src.models.session import UserPreferences
from src.memory.memory_bank import MemoryBank


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    return Repository(
        name="test-repo",
        full_name="test-user/test-repo",
        owner="test-user",
        url="https://github.com/test-user/test-repo",
        default_branch="main",
        visibility="public",
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )


@pytest.fixture
def mock_health_snapshot():
    """Create a mock health snapshot."""
    return HealthSnapshot(
        activity_level="moderate",
        test_coverage="none",
        documentation_quality="basic",
        ci_cd_status="missing",
        dependency_status="unknown",
        overall_health_score=0.45,
        issues_identified=[
            "No tests detected",
            "No CI/CD configuration found"
        ]
    )


@pytest.fixture
def mock_profile(mock_repository, mock_health_snapshot):
    """Create a mock repository profile."""
    return RepositoryProfile(
        repository=mock_repository,
        purpose="A test repository",
        tech_stack=["Python"],
        key_files=["README.md", "setup.py"],
        health=mock_health_snapshot,
        last_analyzed=datetime.now(),
        analysis_version="1.0.0"
    )


@pytest.fixture
def mock_user_preferences():
    """Create mock user preferences."""
    return UserPreferences(
        user_id="test-user",
        automation_level="manual",
        preferred_labels=["maintenance"],
        excluded_repos=[],
        focus_areas=["tests", "docs"]
    )


@pytest.fixture
def mock_memory_bank():
    """Create a mock memory bank."""
    memory = Mock(spec=MemoryBank)
    memory.load_suggestions.return_value = []
    memory.save_suggestions.return_value = None
    return memory


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    return Mock()


@pytest.fixture
def maintainer_agent(mock_memory_bank, mock_github_client):
    """Create a MaintainerAgent with mocked dependencies."""
    with patch('src.agents.maintainer.genai'):
        agent = MaintainerAgent(
            memory_bank=mock_memory_bank,
            github_client=mock_github_client
        )
        return agent


def test_maintainer_agent_initialization(maintainer_agent):
    """Test that MaintainerAgent initializes correctly."""
    assert maintainer_agent is not None
    assert maintainer_agent.memory_bank is not None
    assert maintainer_agent.github_client is not None


def test_generate_suggestion_id(maintainer_agent):
    """Test suggestion ID generation."""
    id1 = maintainer_agent._generate_suggestion_id("repo1", "title1")
    id2 = maintainer_agent._generate_suggestion_id("repo1", "title1")
    id3 = maintainer_agent._generate_suggestion_id("repo2", "title1")
    
    # IDs should be unique (due to timestamp)
    assert id1 != id2
    # Different repos should produce different IDs
    assert id1 != id3


def test_fallback_suggestions(maintainer_agent, mock_profile):
    """Test fallback suggestion generation."""
    suggestions = maintainer_agent._fallback_suggestions(mock_profile)
    
    assert len(suggestions) > 0
    assert all(isinstance(s, MaintenanceSuggestion) for s in suggestions)
    
    # Check that suggestions address health issues
    titles = [s.title.lower() for s in suggestions]
    assert any("test" in title for title in titles)
    assert any("ci" in title or "cd" in title for title in titles)


def test_prioritize_suggestions(maintainer_agent, mock_repository):
    """Test suggestion prioritization."""
    suggestions = [
        MaintenanceSuggestion(
            id="1",
            repository=mock_repository,
            category="security",
            priority="high",
            title="Fix security issue",
            description="Fix it",
            rationale="Security",
            estimated_effort="small",
            labels=["security"]
        ),
        MaintenanceSuggestion(
            id="2",
            repository=mock_repository,
            category="documentation",
            priority="low",
            title="Update docs",
            description="Update it",
            rationale="Docs",
            estimated_effort="large",
            labels=["docs"]
        ),
        MaintenanceSuggestion(
            id="3",
            repository=mock_repository,
            category="bug",
            priority="high",
            title="Fix bug",
            description="Fix it",
            rationale="Bug",
            estimated_effort="medium",
            labels=["bug"]
        )
    ]
    
    prioritized = maintainer_agent.prioritize_suggestions(suggestions)
    
    # Security with high priority and small effort should be first
    assert prioritized[0].category == "security"
    # Documentation with low priority and large effort should be last
    assert prioritized[-1].category == "documentation"


def test_deduplicate_suggestions(maintainer_agent, mock_repository):
    """Test suggestion deduplication."""
    existing_suggestion = MaintenanceSuggestion(
        id="existing",
        repository=mock_repository,
        category="bug",
        priority="high",
        title="Fix existing bug",
        description="Fix it",
        rationale="Bug",
        estimated_effort="small",
        labels=["bug"]
    )
    
    # Mock memory bank to return existing suggestion
    maintainer_agent.memory_bank.load_suggestions.return_value = [existing_suggestion]
    
    new_suggestions = [
        MaintenanceSuggestion(
            id="new1",
            repository=mock_repository,
            category="bug",
            priority="high",
            title="Fix existing bug",  # Duplicate title
            description="Fix it",
            rationale="Bug",
            estimated_effort="small",
            labels=["bug"]
        ),
        MaintenanceSuggestion(
            id="new2",
            repository=mock_repository,
            category="enhancement",
            priority="medium",
            title="Add new feature",  # Unique title
            description="Add it",
            rationale="Feature",
            estimated_effort="medium",
            labels=["enhancement"]
        )
    ]
    
    unique = maintainer_agent._deduplicate_suggestions(
        mock_repository.full_name,
        new_suggestions
    )
    
    # Only the unique suggestion should remain
    assert len(unique) == 1
    assert unique[0].title == "Add new feature"


def test_format_issue_body(maintainer_agent, mock_repository):
    """Test issue body formatting."""
    suggestion = MaintenanceSuggestion(
        id="test",
        repository=mock_repository,
        category="bug",
        priority="high",
        title="Fix bug",
        description="This is a bug that needs fixing",
        rationale="Bugs are bad",
        estimated_effort="small",
        labels=["bug"]
    )
    
    body = maintainer_agent._format_issue_body(suggestion)
    
    assert "This is a bug that needs fixing" in body
    assert "Bugs are bad" in body
    assert "bug" in body
    assert "high" in body
    assert "small" in body


def test_create_github_issue_success(maintainer_agent, mock_repository, mock_user_preferences):
    """Test successful GitHub issue creation."""
    suggestion = MaintenanceSuggestion(
        id="test",
        repository=mock_repository,
        category="bug",
        priority="high",
        title="Fix bug",
        description="Fix it",
        rationale="Bug",
        estimated_effort="small",
        labels=["bug"]
    )
    
    # Mock successful issue creation
    with patch('src.agents.maintainer.create_issue') as mock_create:
        mock_create.return_value = IssueResult(
            success=True,
            issue_url="https://github.com/test-user/test-repo/issues/1",
            issue_number=1
        )
        
        result = maintainer_agent.create_github_issue(suggestion, mock_user_preferences)
        
        assert result.success
        assert result.issue_url == "https://github.com/test-user/test-repo/issues/1"
        assert result.issue_number == 1
        
        # Verify suggestion was saved to memory
        maintainer_agent.memory_bank.save_suggestions.assert_called_once()


def test_create_github_issue_failure(maintainer_agent, mock_repository):
    """Test failed GitHub issue creation."""
    suggestion = MaintenanceSuggestion(
        id="test",
        repository=mock_repository,
        category="bug",
        priority="high",
        title="Fix bug",
        description="Fix it",
        rationale="Bug",
        estimated_effort="small",
        labels=["bug"]
    )
    
    # Mock failed issue creation
    with patch('src.agents.maintainer.create_issue') as mock_create:
        mock_create.return_value = IssueResult(
            success=False,
            issue_url="",
            issue_number=0,
            error_message="API error"
        )
        
        result = maintainer_agent.create_github_issue(suggestion)
        
        assert not result.success
        assert result.error_message == "API error"
        
        # Verify suggestion was NOT saved to memory
        maintainer_agent.memory_bank.save_suggestions.assert_not_called()


def test_prepare_suggestion_context(maintainer_agent, mock_profile, mock_user_preferences):
    """Test suggestion context preparation."""
    context = maintainer_agent._prepare_suggestion_context(mock_profile, mock_user_preferences)
    
    assert context['repo_name'] == "test-user/test-repo"
    assert context['purpose'] == "A test repository"
    assert context['tech_stack'] == ["Python"]
    assert context['activity_level'] == "moderate"
    assert context['test_coverage'] == "none"
    assert context['focus_areas'] == ["tests", "docs"]


def test_generate_suggestions_with_excluded_repo(maintainer_agent, mock_profile):
    """Test that excluded repositories are skipped."""
    preferences = UserPreferences(
        user_id="test-user",
        automation_level="manual",
        preferred_labels=[],
        excluded_repos=["test-user/test-repo"],
        focus_areas=[]
    )
    
    suggestions = maintainer_agent.generate_suggestions([mock_profile], preferences)
    
    # Should return empty list since repo is excluded
    assert len(suggestions) == 0
