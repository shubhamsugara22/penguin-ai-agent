"""Demo script showing data models in action."""

import sys
from datetime import datetime

sys.path.insert(0, 'src')

from models import (
    Repository,
    RepositoryOverview,
    HealthSnapshot,
    RepositoryProfile,
    MaintenanceSuggestion,
    SessionState,
    UserPreferences,
)


def main():
    """Demonstrate data model usage."""
    
    # Create a repository
    repo = Repository(
        name="awesome-project",
        full_name="developer/awesome-project",
        owner="developer",
        url="https://github.com/developer/awesome-project",
        default_branch="main",
        visibility="public",
        created_at=datetime(2023, 1, 15),
        updated_at=datetime(2024, 11, 29)
    )
    
    print("Repository created:")
    print(f"  Name: {repo.name}")
    print(f"  Owner: {repo.owner}")
    print(f"  Visibility: {repo.visibility}")
    print()
    
    # Create a health snapshot
    health = HealthSnapshot(
        activity_level="active",
        test_coverage="partial",
        documentation_quality="good",
        ci_cd_status="configured",
        dependency_status="current",
        overall_health_score=0.75,
        issues_identified=[
            "Test coverage could be improved",
            "Some documentation is outdated"
        ]
    )
    
    print("Health Assessment:")
    print(f"  Activity: {health.activity_level}")
    print(f"  Tests: {health.test_coverage}")
    print(f"  Docs: {health.documentation_quality}")
    print(f"  CI/CD: {health.ci_cd_status}")
    print(f"  Overall Score: {health.overall_health_score}")
    print(f"  Issues: {len(health.issues_identified)}")
    print()
    
    # Create a repository profile
    profile = RepositoryProfile(
        repository=repo,
        purpose="A web application for managing developer workflows",
        tech_stack=["Python", "FastAPI", "PostgreSQL", "React"],
        key_files=["main.py", "requirements.txt", "README.md", "docker-compose.yml"],
        health=health,
        last_analyzed=datetime.now(),
        analysis_version="1.0.0"
    )
    
    print("Repository Profile:")
    print(f"  Purpose: {profile.purpose}")
    print(f"  Tech Stack: {', '.join(profile.tech_stack)}")
    print(f"  Key Files: {len(profile.key_files)}")
    print()
    
    # Create a maintenance suggestion
    suggestion = MaintenanceSuggestion(
        id="sug-001",
        repository=repo,
        category="enhancement",
        priority="medium",
        title="Improve test coverage",
        description="Add unit tests for the API endpoints in the /api directory",
        rationale="Current test coverage is at 60%. Increasing coverage will improve code quality and catch bugs earlier.",
        estimated_effort="medium",
        labels=["testing", "enhancement", "good-first-issue"]
    )
    
    print("Maintenance Suggestion:")
    print(f"  ID: {suggestion.id}")
    print(f"  Category: {suggestion.category}")
    print(f"  Priority: {suggestion.priority}")
    print(f"  Title: {suggestion.title}")
    print(f"  Effort: {suggestion.estimated_effort}")
    print(f"  Labels: {', '.join(suggestion.labels)}")
    print()
    
    # Create a session
    session = SessionState(
        session_id="sess-20241129-001",
        username="developer",
        repositories_analyzed=["awesome-project"],
        suggestions_generated=[suggestion]
    )
    
    print("Session State:")
    print(f"  Session ID: {session.session_id}")
    print(f"  Username: {session.username}")
    print(f"  Repos Analyzed: {len(session.repositories_analyzed)}")
    print(f"  Suggestions: {len(session.suggestions_generated)}")
    print()
    
    # Create user preferences
    prefs = UserPreferences(
        user_id="developer",
        automation_level="ask",
        preferred_labels=["bug", "enhancement", "documentation"],
        excluded_repos=["old-archived-repo"],
        focus_areas=["tests", "security", "documentation"]
    )
    
    print("User Preferences:")
    print(f"  User: {prefs.user_id}")
    print(f"  Automation: {prefs.automation_level}")
    print(f"  Focus Areas: {', '.join(prefs.focus_areas)}")
    print()
    
    # Demonstrate serialization
    print("Serialization Demo:")
    profile_json = profile.to_json()
    print(f"  Profile serialized to JSON ({len(profile_json)} bytes)")
    
    profile_restored = RepositoryProfile.from_json(profile_json)
    print(f"  Profile restored from JSON")
    print(f"  Validation: {'✓ PASSED' if profile.repository.name == profile_restored.repository.name else '✗ FAILED'}")
    print()
    
    print("="*60)
    print("✓ All data models working correctly!")
    print("="*60)


if __name__ == "__main__":
    main()
