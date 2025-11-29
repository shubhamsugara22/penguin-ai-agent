"""Demo script showing how to use GitHub API tools.

This script demonstrates the usage of the GitHub tools for:
- Listing repositories
- Fetching repository overview
- Fetching repository history
- Creating issues

Requirements:
- Set GITHUB_TOKEN environment variable with a valid GitHub personal access token
- Set GEMINI_API_KEY environment variable (required by config)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import (
    GitHubClient,
    list_repos,
    get_repo_overview,
    get_repo_history,
    create_issue,
    RepositoryFilters,
    GitHubAPIError,
    AuthenticationError,
    RateLimitError
)
from datetime import datetime, timedelta


def demo_list_repos():
    """Demo: List repositories for a user."""
    print("\n" + "="*60)
    print("DEMO: List Repositories")
    print("="*60)
    
    username = "octocat"  # Example GitHub user
    
    try:
        # List all repositories
        print(f"\nFetching repositories for user: {username}")
        repos = list_repos(username)
        print(f"Found {len(repos)} repositories")
        
        # Show first 3 repos
        for i, repo in enumerate(repos[:3], 1):
            print(f"\n{i}. {repo.full_name}")
            print(f"   URL: {repo.url}")
            print(f"   Updated: {repo.updated_at}")
            print(f"   Visibility: {repo.visibility}")
        
        # Demo with filters
        print("\n" + "-"*60)
        print("Applying filters: Python repos updated in last year")
        
        one_year_ago = datetime.now() - timedelta(days=365)
        filters = RepositoryFilters(
            updated_after=one_year_ago,
            language="Python",
            visibility="public"
        )
        
        filtered_repos = list_repos(username, filters=filters)
        print(f"Found {len(filtered_repos)} matching repositories")
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("Please check your GITHUB_TOKEN environment variable")
    except GitHubAPIError as e:
        print(f"❌ API error: {e}")


def demo_repo_overview():
    """Demo: Get repository overview."""
    print("\n" + "="*60)
    print("DEMO: Repository Overview")
    print("="*60)
    
    repo_name = "octocat/Hello-World"
    
    try:
        print(f"\nFetching overview for: {repo_name}")
        overview = get_repo_overview(repo_name)
        
        print(f"\n📦 Repository: {overview.repository.full_name}")
        print(f"   Owner: {overview.repository.owner}")
        print(f"   Default branch: {overview.repository.default_branch}")
        
        print(f"\n📊 Languages:")
        for lang, bytes_count in list(overview.languages.items())[:5]:
            print(f"   - {lang}: {bytes_count:,} bytes")
        
        print(f"\n📁 Top-level files ({len(overview.file_structure)} items):")
        for file in overview.file_structure[:10]:
            print(f"   - {file}")
        
        print(f"\n✅ Features:")
        print(f"   - CI/CD configured: {overview.has_ci_config}")
        print(f"   - Tests present: {overview.has_tests}")
        print(f"   - CONTRIBUTING file: {overview.has_contributing}")
        
        if overview.readme_content:
            readme_preview = overview.readme_content[:200].replace('\n', ' ')
            print(f"\n📄 README preview:")
            print(f"   {readme_preview}...")
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except GitHubAPIError as e:
        print(f"❌ API error: {e}")


def demo_repo_history():
    """Demo: Get repository history."""
    print("\n" + "="*60)
    print("DEMO: Repository History")
    print("="*60)
    
    repo_name = "octocat/Hello-World"
    
    try:
        print(f"\nFetching history for: {repo_name}")
        history = get_repo_history(repo_name, limit=5)
        
        print(f"\n📈 Activity Statistics:")
        print(f"   Total commits: {history.commit_count}")
        print(f"   Last commit: {history.last_commit_date}")
        print(f"   Contributors: {history.contributors_count}")
        
        print(f"\n🐛 Issues:")
        print(f"   Open: {history.open_issues_count}")
        print(f"   Closed: {history.closed_issues_count}")
        
        print(f"\n🔀 Pull Requests:")
        print(f"   Open: {history.open_prs_count}")
        print(f"   Merged: {history.merged_prs_count}")
        
        print(f"\n📝 Recent Commits ({len(history.recent_commits)}):")
        for i, commit in enumerate(history.recent_commits, 1):
            print(f"   {i}. {commit.message[:60]}")
            print(f"      by {commit.author} on {commit.date.strftime('%Y-%m-%d')}")
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except GitHubAPIError as e:
        print(f"❌ API error: {e}")


def demo_rate_limit_handling():
    """Demo: Rate limit information."""
    print("\n" + "="*60)
    print("DEMO: Rate Limit Handling")
    print("="*60)
    
    try:
        client = GitHubClient()
        
        # Make a simple request to update rate limit info
        client.get('/user')
        
        rate_limit = client.get_rate_limit_status()
        print(f"\n⏱️  Rate Limit Status:")
        print(f"   Remaining requests: {rate_limit['remaining']}")
        print(f"   Resets at: {rate_limit['reset_time']}")
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except RateLimitError as e:
        print(f"⚠️  Rate limit exceeded: {e}")
        print(f"   Resets at: {e.reset_time}")
    except GitHubAPIError as e:
        print(f"❌ API error: {e}")


def demo_create_issue():
    """Demo: Create issue (commented out to avoid creating real issues)."""
    print("\n" + "="*60)
    print("DEMO: Create Issue (Dry Run)")
    print("="*60)
    
    print("\nThis demo shows how to create an issue:")
    print("""
    result = create_issue(
        repo_full_name="owner/repo",
        title="Add documentation for new feature",
        body="We need to document the new authentication flow...",
        labels=["documentation", "enhancement"]
    )
    
    if result.success:
        print(f"✅ Issue created: {result.issue_url}")
        print(f"   Issue number: #{result.issue_number}")
    else:
        print(f"❌ Failed to create issue: {result.error_message}")
    """)
    
    print("\n⚠️  Note: Uncomment the code above to actually create issues")
    print("   Make sure you have write access to the repository!")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("GitHub Tools Demo")
    print("="*60)
    print("\nThis demo showcases the GitHub API tools functionality.")
    print("Make sure GITHUB_TOKEN and GEMINI_API_KEY are set in your environment.")
    
    try:
        # Run demos
        demo_list_repos()
        demo_repo_overview()
        demo_repo_history()
        demo_rate_limit_handling()
        demo_create_issue()
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
