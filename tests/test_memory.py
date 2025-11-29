"""Unit tests for memory management components."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.memory import SessionService, MemoryBank
from src.models import (
    SessionState,
    SessionMetrics,
    UserPreferences,
    RepositoryProfile,
    Repository,
    HealthSnapshot,
    MaintenanceSuggestion,
)


class TestSessionService:
    """Test SessionService for in-memory session management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = SessionService()
    
    def test_create_session(self):
        """Test creating a new session."""
        session = self.service.create_session("testuser")
        
        assert session.username == "testuser"
        assert session.session_id is not None
        assert len(session.repositories_analyzed) == 0
        assert isinstance(session.metrics, SessionMetrics)
    
    def test_get_session(self):
        """Test retrieving a session by ID."""
        session = self.service.create_session("testuser")
        
        retrieved = self.service.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved.username == "testuser"
    
    def test_get_nonexistent_session(self):
        """Test retrieving a session that doesn't exist."""
        retrieved = self.service.get_session("nonexistent-id")
        assert retrieved is None
    
    def test_get_current_session(self):
        """Test getting the current active session."""
        # No current session initially
        assert self.service.get_current_session() is None
        
        # Create a session
        session = self.service.create_session("testuser")
        
        # Should be the current session
        current = self.service.get_current_session()
        assert current is not None
        assert current.session_id == session.session_id
    
    def test_update_session(self):
        """Test updating an existing session."""
        session = self.service.create_session("testuser")
        
        # Modify the session
        session.repositories_analyzed.append("repo1")
        session.metrics.repos_analyzed = 1
        
        # Update it
        self.service.update_session(session)
        
        # Retrieve and verify
        retrieved = self.service.get_session(session.session_id)
        assert len(retrieved.repositories_analyzed) == 1
        assert retrieved.repositories_analyzed[0] == "repo1"
        assert retrieved.metrics.repos_analyzed == 1
    
    def test_update_nonexistent_session(self):
        """Test updating a session that doesn't exist."""
        session = SessionState(
            session_id="nonexistent",
            username="testuser"
        )
        
        with pytest.raises(ValueError, match="Session .* not found"):
            self.service.update_session(session)
    
    def test_delete_session(self):
        """Test deleting a session."""
        session = self.service.create_session("testuser")
        
        # Delete the session
        result = self.service.delete_session(session.session_id)
        assert result is True
        
        # Should no longer exist
        retrieved = self.service.get_session(session.session_id)
        assert retrieved is None
        
        # Current session should be cleared
        assert self.service.get_current_session() is None
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        result = self.service.delete_session("nonexistent-id")
        assert result is False
    
    def test_list_sessions(self):
        """Test listing all sessions."""
        # Initially empty
        sessions = self.service.list_sessions()
        assert len(sessions) == 0
        
        # Create multiple sessions
        session1 = self.service.create_session("user1")
        session2 = self.service.create_session("user2")
        
        # List should contain both
        sessions = self.service.list_sessions()
        assert len(sessions) == 2
        assert session1.session_id in sessions
        assert session2.session_id in sessions
    
    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        self.service.create_session("user1")
        self.service.create_session("user2")
        
        self.service.clear_all_sessions()
        
        sessions = self.service.list_sessions()
        assert len(sessions) == 0
        assert self.service.get_current_session() is None


class TestMemoryBank:
    """Test MemoryBank for long-term storage."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_bank = MemoryBank(storage_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_repository(self) -> Repository:
        """Helper to create a test repository."""
        return Repository(
            name="test-repo",
            full_name="user/test-repo",
            owner="user",
            url="https://github.com/user/test-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 11, 29)
        )
    
    def _create_test_health_snapshot(self) -> HealthSnapshot:
        """Helper to create a test health snapshot."""
        return HealthSnapshot(
            activity_level="active",
            test_coverage="good",
            documentation_quality="excellent",
            ci_cd_status="configured",
            dependency_status="current",
            overall_health_score=0.9,
            issues_identified=[]
        )
    
    def _create_test_profile(self) -> RepositoryProfile:
        """Helper to create a test repository profile."""
        return RepositoryProfile(
            repository=self._create_test_repository(),
            purpose="Test repository for unit tests",
            tech_stack=["Python", "pytest"],
            key_files=["README.md", "setup.py"],
            health=self._create_test_health_snapshot(),
            last_analyzed=datetime(2024, 11, 29),
            analysis_version="1.0.0"
        )
    
    # Repository Profile Tests
    
    def test_save_repository_profile(self):
        """Test saving a repository profile."""
        profile = self._create_test_profile()
        
        self.memory_bank.save_repository_profile(profile)
        
        # Verify file was created
        profile_path = self.memory_bank._get_profile_path("user/test-repo")
        assert profile_path.exists()
    
    def test_load_repository_profile(self):
        """Test loading a repository profile."""
        profile = self._create_test_profile()
        
        # Save it first
        self.memory_bank.save_repository_profile(profile)
        
        # Load it back
        loaded = self.memory_bank.load_repository_profile("user/test-repo")
        
        assert loaded is not None
        assert loaded.repository.full_name == "user/test-repo"
        assert loaded.purpose == "Test repository for unit tests"
        assert loaded.tech_stack == ["Python", "pytest"]
    
    def test_load_nonexistent_profile(self):
        """Test loading a profile that doesn't exist."""
        loaded = self.memory_bank.load_repository_profile("nonexistent/repo")
        assert loaded is None
    
    def test_delete_repository_profile(self):
        """Test deleting a repository profile."""
        profile = self._create_test_profile()
        
        # Save it first
        self.memory_bank.save_repository_profile(profile)
        
        # Delete it
        result = self.memory_bank.delete_repository_profile("user/test-repo")
        assert result is True
        
        # Should no longer exist
        loaded = self.memory_bank.load_repository_profile("user/test-repo")
        assert loaded is None
    
    def test_delete_nonexistent_profile(self):
        """Test deleting a profile that doesn't exist."""
        result = self.memory_bank.delete_repository_profile("nonexistent/repo")
        assert result is False
    
    def test_list_repository_profiles(self):
        """Test listing all repository profiles."""
        # Initially empty
        profiles = self.memory_bank.list_repository_profiles()
        assert len(profiles) == 0
        
        # Save multiple profiles
        profile1 = self._create_test_profile()
        self.memory_bank.save_repository_profile(profile1)
        
        profile2 = self._create_test_profile()
        profile2.repository.full_name = "user/another-repo"
        self.memory_bank.save_repository_profile(profile2)
        
        # List should contain both
        profiles = self.memory_bank.list_repository_profiles()
        assert len(profiles) == 2
        assert "user/test-repo" in profiles
        assert "user/another-repo" in profiles
    
    # User Preferences Tests
    
    def test_save_user_preferences(self):
        """Test saving user preferences."""
        prefs = UserPreferences(
            user_id="testuser",
            automation_level="auto",
            preferred_labels=["bug", "enhancement"],
            excluded_repos=["old-repo"],
            focus_areas=["tests", "docs"]
        )
        
        self.memory_bank.save_user_preferences(prefs)
        
        # Verify file was created
        prefs_path = self.memory_bank._get_preferences_path("testuser")
        assert prefs_path.exists()
    
    def test_load_user_preferences(self):
        """Test loading user preferences."""
        prefs = UserPreferences(
            user_id="testuser",
            automation_level="manual",
            preferred_labels=["security"],
            excluded_repos=[],
            focus_areas=["security"]
        )
        
        # Save it first
        self.memory_bank.save_user_preferences(prefs)
        
        # Load it back
        loaded = self.memory_bank.load_user_preferences("testuser")
        
        assert loaded is not None
        assert loaded.user_id == "testuser"
        assert loaded.automation_level == "manual"
        assert loaded.preferred_labels == ["security"]
    
    def test_load_nonexistent_preferences(self):
        """Test loading preferences that don't exist."""
        loaded = self.memory_bank.load_user_preferences("nonexistent")
        assert loaded is None
    
    def test_delete_user_preferences(self):
        """Test deleting user preferences."""
        prefs = UserPreferences(user_id="testuser")
        
        # Save it first
        self.memory_bank.save_user_preferences(prefs)
        
        # Delete it
        result = self.memory_bank.delete_user_preferences("testuser")
        assert result is True
        
        # Should no longer exist
        loaded = self.memory_bank.load_user_preferences("testuser")
        assert loaded is None
    
    # Suggestion History Tests
    
    def test_save_suggestions(self):
        """Test saving maintenance suggestions."""
        repo = self._create_test_repository()
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="documentation",
            priority="high",
            title="Add README",
            description="Repository needs a README file",
            rationale="README helps users understand the project",
            estimated_effort="small",
            labels=["documentation"]
        )
        
        self.memory_bank.save_suggestions("user/test-repo", [suggestion])
        
        # Verify file was created
        suggestions_path = self.memory_bank._get_suggestions_path("user/test-repo")
        assert suggestions_path.exists()
    
    def test_load_suggestions(self):
        """Test loading maintenance suggestions."""
        repo = self._create_test_repository()
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="bug",
            priority="medium",
            title="Fix bug",
            description="Bug description",
            rationale="Bug rationale",
            estimated_effort="medium",
            labels=["bug"]
        )
        
        # Save it first
        self.memory_bank.save_suggestions("user/test-repo", [suggestion])
        
        # Load it back
        loaded = self.memory_bank.load_suggestions("user/test-repo")
        
        assert len(loaded) == 1
        assert loaded[0].id == "sug-001"
        assert loaded[0].title == "Fix bug"
    
    def test_load_nonexistent_suggestions(self):
        """Test loading suggestions that don't exist."""
        loaded = self.memory_bank.load_suggestions("nonexistent/repo")
        assert len(loaded) == 0
    
    def test_save_multiple_suggestions(self):
        """Test saving multiple suggestions accumulates them."""
        repo = self._create_test_repository()
        
        suggestion1 = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="documentation",
            priority="high",
            title="Add README",
            description="Description",
            rationale="Rationale",
            estimated_effort="small",
            labels=["documentation"]
        )
        
        suggestion2 = MaintenanceSuggestion(
            id="sug-002",
            repository=repo,
            category="bug",
            priority="medium",
            title="Fix bug",
            description="Description",
            rationale="Rationale",
            estimated_effort="medium",
            labels=["bug"]
        )
        
        # Save first batch
        self.memory_bank.save_suggestions("user/test-repo", [suggestion1])
        
        # Save second batch
        self.memory_bank.save_suggestions("user/test-repo", [suggestion2])
        
        # Load all
        loaded = self.memory_bank.load_suggestions("user/test-repo")
        
        assert len(loaded) == 2
        assert loaded[0].id == "sug-001"
        assert loaded[1].id == "sug-002"
    
    def test_check_suggestion_exists(self):
        """Test checking if a suggestion exists."""
        repo = self._create_test_repository()
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="documentation",
            priority="high",
            title="Add README",
            description="Description",
            rationale="Rationale",
            estimated_effort="small",
            labels=["documentation"]
        )
        
        # Initially doesn't exist
        assert self.memory_bank.check_suggestion_exists("user/test-repo", "Add README") is False
        
        # Save it
        self.memory_bank.save_suggestions("user/test-repo", [suggestion])
        
        # Now it exists
        assert self.memory_bank.check_suggestion_exists("user/test-repo", "Add README") is True
        
        # Case insensitive
        assert self.memory_bank.check_suggestion_exists("user/test-repo", "add readme") is True
        
        # Different title doesn't exist
        assert self.memory_bank.check_suggestion_exists("user/test-repo", "Different Title") is False
    
    def test_delete_suggestions(self):
        """Test deleting suggestions."""
        repo = self._create_test_repository()
        
        suggestion = MaintenanceSuggestion(
            id="sug-001",
            repository=repo,
            category="bug",
            priority="high",
            title="Fix bug",
            description="Description",
            rationale="Rationale",
            estimated_effort="small",
            labels=["bug"]
        )
        
        # Save it first
        self.memory_bank.save_suggestions("user/test-repo", [suggestion])
        
        # Delete it
        result = self.memory_bank.delete_suggestions("user/test-repo")
        assert result is True
        
        # Should no longer exist
        loaded = self.memory_bank.load_suggestions("user/test-repo")
        assert len(loaded) == 0
    
    def test_clear_all_data(self):
        """Test clearing all data from memory bank."""
        # Save some data
        profile = self._create_test_profile()
        self.memory_bank.save_repository_profile(profile)
        
        prefs = UserPreferences(user_id="testuser")
        self.memory_bank.save_user_preferences(prefs)
        
        # Clear all
        self.memory_bank.clear_all_data()
        
        # Everything should be gone
        assert self.memory_bank.load_repository_profile("user/test-repo") is None
        assert self.memory_bank.load_user_preferences("testuser") is None
        assert len(self.memory_bank.list_repository_profiles()) == 0
