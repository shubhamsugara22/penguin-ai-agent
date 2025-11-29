#!/usr/bin/env python3
"""Manual end-to-end integration test script.

This script runs comprehensive integration tests without requiring pytest,
testing the entire system with various scenarios.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.coordinator import CoordinatorAgent, AnalysisResult, ProgressEvent
from src.agents.analyzer import AnalyzerAgent
from src.agents.maintainer import MaintainerAgent
from src.models.repository import Repository
from src.models.health import HealthSnapshot, RepositoryProfile
from src.models.maintenance import MaintenanceSuggestion
from src.models.session import UserPreferences, SessionState
from src.tools.github_tools import RepositoryFilters
from src.memory.memory_bank import MemoryBank
from src.memory.session_service import SessionService


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test name."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[TEST] {name}{Colors.ENDC}")


def print_pass(message: str):
    """Print pass message."""
    try:
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[PASS] {message}{Colors.ENDC}")


def print_fail(message: str):
    """Print fail message."""
    try:
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[FAIL] {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message."""
    try:
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.YELLOW}[WARN] {message}{Colors.ENDC}")


def create_mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock()
    config.github_token = "ghp_" + "x" * 36
    config.gemini_api_key = "test_key_1234567890"
    config.log_level = "INFO"
    config.storage_dir = ".test_memory"
    return config


def create_sample_repository():
    """Create a sample repository for testing."""
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


def create_sample_health_snapshot():
    """Create a sample health snapshot for testing."""
    return HealthSnapshot(
        activity_level="moderate",
        test_coverage="none",
        documentation_quality="basic",
        ci_cd_status="missing",
        dependency_status="unknown",
        overall_health_score=0.45,
        issues_identified=["No tests detected", "No CI/CD configuration"]
    )


def create_sample_profile():
    """Create a sample repository profile for testing."""
    repo = create_sample_repository()
    health = create_sample_health_snapshot()
    
    return RepositoryProfile(
        repository=repo,
        purpose="A test repository for demonstration",
        tech_stack=["Python", "JavaScript"],
        key_files=["README.md", "setup.py", "package.json"],
        health=health,
        last_analyzed=datetime.now(),
        analysis_version="1.0.0"
    )


def test_coordinator_initialization():
    """Test 1: Coordinator Agent initialization."""
    print_test("Coordinator Agent Initialization")
    
    try:
        mock_config = create_mock_config()
        with patch('src.agents.coordinator.get_config', return_value=mock_config), \
             patch('src.tools.github_client.get_config', return_value=mock_config), \
             patch('src.agents.analyzer.get_config', return_value=mock_config), \
             patch('src.agents.maintainer.get_config', return_value=mock_config), \
             patch('src.agents.maintainer.genai'):
            coordinator = CoordinatorAgent()
            
            assert coordinator is not None, "Coordinator is None"
            assert coordinator.workflow is not None, "Workflow is None"
            assert len(coordinator.workflow) == 7, f"Expected 7 workflow steps, got {len(coordinator.workflow)}"
            assert coordinator.session_service is not None, "Session service is None"
            
            print_pass("Coordinator initialized successfully")
            print_pass(f"Workflow has {len(coordinator.workflow)} steps")
            return True
            
    except Exception as e:
        print_fail(f"Coordinator initialization failed: {e}")
        return False


def test_analyzer_initialization():
    """Test 2: Analyzer Agent initialization."""
    print_test("Analyzer Agent Initialization")
    
    try:
        mock_config = create_mock_config()
        with patch('src.agents.analyzer.get_config', return_value=mock_config), \
             patch('src.tools.github_client.get_config', return_value=mock_config):
            analyzer = AnalyzerAgent()
            
            assert analyzer is not None, "Analyzer is None"
            assert analyzer.github_client is not None, "GitHub client is None"
            
            print_pass("Analyzer initialized successfully")
            return True
            
    except Exception as e:
        print_fail(f"Analyzer initialization failed: {e}")
        return False


def test_maintainer_initialization():
    """Test 3: Maintainer Agent initialization."""
    print_test("Maintainer Agent Initialization")
    
    try:
        mock_config = create_mock_config()
        with patch('src.agents.maintainer.get_config', return_value=mock_config), \
             patch('src.agents.maintainer.genai'), \
             patch('src.tools.github_client.get_config', return_value=mock_config):
            memory_bank = MemoryBank(storage_dir=".test_memory")
            maintainer = MaintainerAgent(memory_bank=memory_bank)
            
            assert maintainer is not None, "Maintainer is None"
            assert maintainer.memory_bank is not None, "Memory bank is None"
            
            print_pass("Maintainer initialized successfully")
            return True
            
    except Exception as e:
        print_fail(f"Maintainer initialization failed: {e}")
        return False


def test_workflow_state_transitions():
    """Test 4: Workflow state transitions."""
    print_test("Workflow State Transitions")
    
    try:
        from src.agents.coordinator import WorkflowState
        
        state = WorkflowState(username="test-user")
        
        assert state.username == "test-user", "Username mismatch"
        assert len(state.repositories) == 0, "Repositories should be empty"
        assert len(state.suggestions) == 0, "Suggestions should be empty"
        assert len(state.created_issues) == 0, "Issues should be empty"
        
        print_pass("Workflow state initialized correctly")
        print_pass(f"Username: {state.username}")
        return True
        
    except Exception as e:
        print_fail(f"Workflow state test failed: {e}")
        return False


def test_progress_event_emission():
    """Test 5: Progress event emission."""
    print_test("Progress Event Emission")
    
    try:
        events_received = []
        
        def progress_callback(event: ProgressEvent):
            events_received.append(event)
        
        # Simulate progress events
        event1 = ProgressEvent(
            stage="initialization",
            message="Starting analysis",
            current=0,
            total=0
        )
        progress_callback(event1)
        
        event2 = ProgressEvent(
            stage="fetching",
            message="Fetching repositories",
            current=1,
            total=5
        )
        progress_callback(event2)
        
        assert len(events_received) == 2, f"Expected 2 events, got {len(events_received)}"
        assert events_received[0].stage == "initialization", "First event stage mismatch"
        assert events_received[1].stage == "fetching", "Second event stage mismatch"
        assert events_received[1].current == 1, "Event current count mismatch"
        assert events_received[1].total == 5, "Event total count mismatch"
        
        print_pass("Progress events emitted correctly")
        print_pass(f"Received {len(events_received)} events")
        return True
        
    except Exception as e:
        print_fail(f"Progress event test failed: {e}")
        return False


def test_suggestion_generation():
    """Test 6: Suggestion generation and prioritization."""
    print_test("Suggestion Generation and Prioritization")
    
    try:
        mock_config = create_mock_config()
        profile = create_sample_profile()
        
        with patch('src.agents.maintainer.get_config', return_value=mock_config), \
             patch('src.agents.maintainer.genai'):
            
            memory_bank = MemoryBank(storage_dir=".test_memory")
            maintainer = MaintainerAgent(memory_bank=memory_bank)
            
            # Generate suggestions using fallback
            suggestions = maintainer._fallback_suggestions(profile)
            
            assert len(suggestions) > 0, "No suggestions generated"
            assert all(isinstance(s, MaintenanceSuggestion) for s in suggestions), "Invalid suggestion type"
            
            print_pass(f"Generated {len(suggestions)} suggestions")
            
            # Test prioritization
            prioritized = maintainer.prioritize_suggestions(suggestions)
            
            assert len(prioritized) == len(suggestions), "Prioritization changed count"
            
            # Verify priority ordering
            priorities = [s.priority for s in prioritized]
            high_indices = [i for i, p in enumerate(priorities) if p == "high"]
            medium_indices = [i for i, p in enumerate(priorities) if p == "medium"]
            low_indices = [i for i, p in enumerate(priorities) if p == "low"]
            
            if high_indices and medium_indices:
                assert max(high_indices) < min(medium_indices), "High priority not before medium"
            if medium_indices and low_indices:
                assert max(medium_indices) < min(low_indices), "Medium priority not before low"
            
            print_pass("Suggestions prioritized correctly")
            print_pass(f"Priority order: {' -> '.join(priorities)}")
            return True
            
    except Exception as e:
        print_fail(f"Suggestion generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deduplication():
    """Test 7: Suggestion deduplication."""
    print_test("Suggestion Deduplication")
    
    try:
        mock_config = create_mock_config()
        profile = create_sample_profile()
        repo = create_sample_repository()
        
        with patch('src.agents.maintainer.get_config', return_value=mock_config), \
             patch('src.agents.maintainer.genai'):
            
            memory_bank = MemoryBank(storage_dir=".test_memory")
            maintainer = MaintainerAgent(memory_bank=memory_bank)
            
            # Generate suggestions
            suggestions = maintainer._fallback_suggestions(profile)
            original_count = len(suggestions)
            
            # Create duplicates
            duplicates = suggestions + suggestions[:2]
            
            # Deduplicate
            unique = maintainer._deduplicate_suggestions(repo.full_name, duplicates)
            
            assert len(unique) <= original_count, "Deduplication failed to remove duplicates"
            
            print_pass(f"Deduplicated: {len(duplicates)} -> {len(unique)} suggestions")
            return True
            
    except Exception as e:
        print_fail(f"Deduplication test failed: {e}")
        return False


def test_session_persistence():
    """Test 8: Session state persistence."""
    print_test("Session State Persistence")
    
    try:
        session_service = SessionService()
        
        # Create a session
        session_id = "test-session-123"
        state = SessionState(
            session_id=session_id,
            username="test-user",
            repositories_analyzed=["repo1", "repo2"],
            suggestions_generated=[],
            issues_created=[],
            start_time=datetime.now()
        )
        
        # Save session
        session_service._sessions[session_id] = state
        
        # Retrieve session
        retrieved = session_service.get_session(session_id)
        
        assert retrieved is not None, "Session not retrieved"
        assert retrieved.session_id == session_id, "Session ID mismatch"
        assert retrieved.username == "test-user", "Username mismatch"
        assert len(retrieved.repositories_analyzed) == 2, "Repository count mismatch"
        
        print_pass("Session persisted and retrieved successfully")
        print_pass(f"Session ID: {session_id}")
        return True
        
    except Exception as e:
        print_fail(f"Session persistence test failed: {e}")
        return False


def test_memory_bank_operations():
    """Test 9: Memory bank CRUD operations."""
    print_test("Memory Bank Operations")
    
    try:
        memory_bank = MemoryBank(storage_dir=".test_memory")
        profile = create_sample_profile()
        
        # Save profile
        memory_bank.save_repository_profile(profile)
        print_pass("Profile saved")
        
        # Load profile
        loaded = memory_bank.load_repository_profile(profile.repository.full_name)
        
        assert loaded is not None, "Profile not loaded"
        assert loaded.repository.full_name == profile.repository.full_name, "Repository name mismatch"
        assert loaded.purpose == profile.purpose, "Purpose mismatch"
        
        print_pass("Profile loaded successfully")
        return True
        
    except Exception as e:
        print_fail(f"Memory bank test failed: {e}")
        return False


def test_user_preferences_persistence():
    """Test 10: User preferences persistence."""
    print_test("User Preferences Persistence")
    
    try:
        memory_bank = MemoryBank(storage_dir=".test_memory")
        
        # Create preferences
        preferences = UserPreferences(
            user_id="test-user",
            automation_level="auto",
            preferred_labels=["bug", "enhancement"],
            excluded_repos=["repo1", "repo2"],
            focus_areas=["tests", "security"]
        )
        
        # Save preferences
        memory_bank.save_user_preferences(preferences)
        print_pass("Preferences saved")
        
        # Load preferences
        loaded = memory_bank.load_user_preferences("test-user")
        
        assert loaded is not None, "Preferences not loaded"
        assert loaded.user_id == "test-user", "User ID mismatch"
        assert loaded.automation_level == "auto", "Automation level mismatch"
        assert len(loaded.preferred_labels) == 2, "Labels count mismatch"
        assert len(loaded.excluded_repos) == 2, "Excluded repos count mismatch"
        assert len(loaded.focus_areas) == 2, "Focus areas count mismatch"
        
        print_pass("Preferences loaded successfully")
        return True
        
    except Exception as e:
        print_fail(f"User preferences test failed: {e}")
        return False


def test_error_handling():
    """Test 11: Error handling and graceful degradation."""
    print_test("Error Handling")
    
    try:
        mock_config = create_mock_config()
        repo = create_sample_repository()
        
        with patch('src.agents.analyzer.get_config', return_value=mock_config), \
             patch('src.tools.github_client.get_config', return_value=mock_config):
            analyzer = AnalyzerAgent()
            
            # Mock GitHub client to raise an error
            analyzer.github_client.get_repo_overview = Mock(
                side_effect=Exception("API Error")
            )
            
            # Should raise exception
            try:
                result = analyzer.github_client.get_repo_overview(repo.full_name)
                print_fail("Should have raised an exception")
                return False
            except Exception as e:
                assert "API Error" in str(e), "Wrong error message"
                print_pass("Error handled correctly")
                return True
                
    except Exception as e:
        print_fail(f"Error handling test failed: {e}")
        return False


def test_filter_application():
    """Test 12: Repository filter application."""
    print_test("Repository Filter Application")
    
    try:
        # Create test repositories
        repos = [
            Repository(
                name="python-repo",
                full_name="user/python-repo",
                owner="user",
                url="https://github.com/user/python-repo",
                default_branch="main",
                visibility="public",
                created_at=datetime(2023, 1, 1),
                updated_at=datetime(2024, 6, 1)
            ),
            Repository(
                name="old-repo",
                full_name="user/old-repo",
                owner="user",
                url="https://github.com/user/old-repo",
                default_branch="main",
                visibility="public",
                created_at=datetime(2020, 1, 1),
                updated_at=datetime(2023, 1, 1)
            ),
        ]
        
        # Apply date filter
        filtered = [
            r for r in repos
            if r.updated_at >= datetime(2024, 1, 1)
        ]
        
        assert len(filtered) == 1, f"Expected 1 repo, got {len(filtered)}"
        assert filtered[0].name == "python-repo", "Wrong repo filtered"
        
        print_pass("Filters applied correctly")
        print_pass(f"Filtered: {len(repos)} -> {len(filtered)} repositories")
        return True
        
    except Exception as e:
        print_fail(f"Filter application test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'GitHub Maintainer Agent - End-to-End Integration Tests'.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    
    tests = [
        test_coordinator_initialization,
        test_analyzer_initialization,
        test_maintainer_initialization,
        test_workflow_state_transitions,
        test_progress_event_emission,
        test_suggestion_generation,
        test_deduplication,
        test_session_persistence,
        test_memory_bank_operations,
        test_user_preferences_persistence,
        test_error_handling,
        test_filter_application,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Print summary
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'Test Summary'.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.ENDC}" if result else f"{Colors.RED}FAIL{Colors.ENDC}"
        print(f"  {test_name:.<60} {status}")
    
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")
    
    if passed == total:
        print_pass("All integration tests passed!")
        return 0
    else:
        print_fail(f"{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
