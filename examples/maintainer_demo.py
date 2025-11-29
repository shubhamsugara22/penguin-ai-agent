"""Demo script for the Maintainer Agent.

This script demonstrates how to use the Maintainer Agent to generate
maintenance suggestions and create GitHub issues.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.maintainer import MaintainerAgent
from src.agents.analyzer import AnalyzerAgent
from src.memory.memory_bank import MemoryBank
from src.models.session import UserPreferences
from src.tools.github_tools import list_repos
from src.config import get_config


def main():
    """Run the Maintainer Agent demo."""
    print("=" * 80)
    print("Maintainer Agent Demo")
    print("=" * 80)
    
    # Verify configuration
    try:
        config = get_config()
        print(f"\n✓ Configuration loaded")
        print(f"  - GitHub token: {'*' * 20}")
        print(f"  - Gemini API key: {'*' * 20}")
    except Exception as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease set the following environment variables:")
        print("  - GITHUB_TOKEN: Your GitHub personal access token")
        print("  - GEMINI_API_KEY: Your Google Gemini API key")
        return
    
    # Initialize agents
    print("\n" + "=" * 80)
    print("Initializing Agents")
    print("=" * 80)
    
    memory_bank = MemoryBank()
    analyzer = AnalyzerAgent()
    maintainer = MaintainerAgent(memory_bank=memory_bank)
    
    print("\n✓ Analyzer Agent initialized")
    print("✓ Maintainer Agent initialized")
    print("✓ Memory Bank initialized")
    
    # Get user input
    print("\n" + "=" * 80)
    print("Repository Selection")
    print("=" * 80)
    
    username = input("\nEnter GitHub username (or press Enter for demo): ").strip()
    if not username:
        print("\nUsing demo mode with mock data...")
        # Create mock repository profile for demo
        from src.models.repository import Repository
        from src.models.health import HealthSnapshot, RepositoryProfile
        from datetime import datetime
        
        mock_repo = Repository(
            name="demo-repo",
            full_name="demo-user/demo-repo",
            owner="demo-user",
            url="https://github.com/demo-user/demo-repo",
            default_branch="main",
            visibility="public",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )
        
        mock_health = HealthSnapshot(
            activity_level="moderate",
            test_coverage="none",
            documentation_quality="basic",
            ci_cd_status="missing",
            dependency_status="unknown",
            overall_health_score=0.45,
            issues_identified=[
                "No tests detected",
                "No CI/CD configuration found",
                "Documentation could be improved"
            ]
        )
        
        mock_profile = RepositoryProfile(
            repository=mock_repo,
            purpose="A demo repository for testing the maintainer agent",
            tech_stack=["Python", "JavaScript"],
            key_files=["README.md", "setup.py", "package.json"],
            health=mock_health,
            last_analyzed=datetime.now(),
            analysis_version="1.0.0"
        )
        
        profiles = [mock_profile]
        
    else:
        # Fetch and analyze real repositories
        print(f"\nFetching repositories for {username}...")
        
        try:
            repos = list_repos(username)
            print(f"✓ Found {len(repos)} repositories")
            
            # Limit to first 3 for demo
            repos = repos[:3]
            print(f"  Analyzing first {len(repos)} repositories...")
            
            # Analyze repositories
            print("\nAnalyzing repositories...")
            analyses = analyzer.analyze_repositories_parallel(repos, max_workers=2)
            
            profiles = [analysis.profile for analysis in analyses]
            print(f"✓ Analyzed {len(profiles)} repositories")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return
    
    # Create user preferences
    print("\n" + "=" * 80)
    print("User Preferences")
    print("=" * 80)
    
    preferences = UserPreferences(
        user_id=username or "demo-user",
        automation_level="manual",
        preferred_labels=["maintenance", "ai-generated"],
        excluded_repos=[],
        focus_areas=["tests", "docs", "ci-cd"]
    )
    
    print(f"\n✓ User preferences configured")
    print(f"  - Automation level: {preferences.automation_level}")
    print(f"  - Focus areas: {', '.join(preferences.focus_areas)}")
    
    # Generate suggestions
    print("\n" + "=" * 80)
    print("Generating Maintenance Suggestions")
    print("=" * 80)
    
    print("\nGenerating suggestions...")
    suggestions = maintainer.generate_suggestions(profiles, preferences)
    
    print(f"\n✓ Generated {len(suggestions)} suggestions")
    
    # Display suggestions
    print("\n" + "=" * 80)
    print("Maintenance Suggestions")
    print("=" * 80)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion.title}")
        print(f"   Repository: {suggestion.repository.full_name}")
        print(f"   Category: {suggestion.category}")
        print(f"   Priority: {suggestion.priority}")
        print(f"   Effort: {suggestion.estimated_effort}")
        print(f"   Labels: {', '.join(suggestion.labels)}")
        print(f"\n   Description:")
        print(f"   {suggestion.description[:200]}...")
        print(f"\n   Rationale:")
        print(f"   {suggestion.rationale[:200]}...")
    
    # Ask about creating issues
    if suggestions:
        print("\n" + "=" * 80)
        print("Issue Creation")
        print("=" * 80)
        
        create_issues = input("\nWould you like to create GitHub issues? (yes/no): ").strip().lower()
        
        if create_issues == "yes":
            print("\nCreating issues...")
            
            for suggestion in suggestions:
                print(f"\n  Creating issue: {suggestion.title}")
                
                result = maintainer.create_github_issue(suggestion, preferences)
                
                if result.success:
                    print(f"  ✓ Issue created: {result.issue_url}")
                else:
                    print(f"  ✗ Failed: {result.error_message}")
        else:
            print("\nSkipping issue creation.")
    
    print("\n" + "=" * 80)
    print("Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
