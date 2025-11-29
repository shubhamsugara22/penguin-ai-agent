"""Demo script for the Coordinator Agent.

This script demonstrates the complete workflow orchestration using the
Coordinator Agent to analyze repositories, generate suggestions, and create issues.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents import CoordinatorAgent, ProgressEvent
from src.tools.github_tools import RepositoryFilters
from src.models.session import UserPreferences
from src.models.maintenance import MaintenanceSuggestion
from typing import List


def progress_callback(event: ProgressEvent):
    """Callback for progress updates."""
    if event.total > 0:
        print(f"[{event.stage}] {event.message} ({event.current}/{event.total})")
    else:
        print(f"[{event.stage}] {event.message}")


def approval_callback(suggestions: List[MaintenanceSuggestion]) -> List[MaintenanceSuggestion]:
    """Callback for suggestion approvals (interactive)."""
    print("\n" + "="*80)
    print("MAINTENANCE SUGGESTIONS")
    print("="*80)
    
    approved = []
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. [{suggestion.priority.upper()}] {suggestion.title}")
        print(f"   Repository: {suggestion.repository.full_name}")
        print(f"   Category: {suggestion.category}")
        print(f"   Effort: {suggestion.estimated_effort}")
        print(f"   Description: {suggestion.description[:100]}...")
        
        # For demo purposes, auto-approve high priority suggestions
        if suggestion.priority == "high":
            print("   ✓ AUTO-APPROVED (high priority)")
            approved.append(suggestion)
        else:
            print("   ✗ SKIPPED (not high priority)")
    
    print(f"\nApproved {len(approved)} out of {len(suggestions)} suggestions")
    return approved


def main():
    """Run the coordinator demo."""
    print("="*80)
    print("COORDINATOR AGENT DEMO")
    print("="*80)
    
    # Check for required environment variables
    if not os.getenv('GITHUB_TOKEN'):
        print("\nError: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub personal access token:")
        print("  export GITHUB_TOKEN='your_token_here'")
        return
    
    if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
        print("\nError: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
        print("Please set your Google AI Studio API key:")
        print("  export GEMINI_API_KEY='your_key_here'")
        return
    
    # Get username from command line or use default
    username = sys.argv[1] if len(sys.argv) > 1 else "octocat"
    
    print(f"\nAnalyzing repositories for user: {username}")
    print("-"*80)
    
    # Create filters (only repos updated in last year)
    filters = RepositoryFilters(
        updated_after=datetime.now() - timedelta(days=365),
        archived=False
    )
    
    # Create user preferences
    preferences = UserPreferences(
        user_id=username,
        automation_level="manual",  # Use manual approval
        focus_areas=["tests", "documentation", "ci-cd"]
    )
    
    # Create coordinator agent
    coordinator = CoordinatorAgent()
    
    try:
        # Run analysis workflow
        result = coordinator.analyze_repositories(
            username=username,
            filters=filters,
            user_preferences=preferences,
            progress_callback=progress_callback,
            approval_callback=approval_callback
        )
        
        # Display results
        print("\n" + "="*80)
        print("ANALYSIS RESULTS")
        print("="*80)
        
        print(f"\nSession ID: {result.session_id}")
        print(f"Username: {result.username}")
        print(f"Repositories Analyzed: {len(result.repositories_analyzed)}")
        
        if result.repositories_analyzed:
            print("\nRepositories:")
            for repo in result.repositories_analyzed:
                print(f"  - {repo}")
        
        print(f"\nSuggestions Generated: {len(result.suggestions)}")
        print(f"Issues Created: {len([i for i in result.issues_created if i.success])}")
        
        if result.issues_created:
            print("\nCreated Issues:")
            for issue in result.issues_created:
                if issue.success:
                    print(f"  ✓ {issue.issue_url}")
                else:
                    print(f"  ✗ Failed: {issue.error_message}")
        
        print("\nMetrics:")
        print(f"  - Execution Time: {result.metrics.execution_time_seconds:.2f}s")
        print(f"  - API Calls: {result.metrics.api_calls_made}")
        print(f"  - Tokens Used: {result.metrics.tokens_used}")
        print(f"  - Errors: {result.metrics.errors_encountered}")
        
        if result.errors:
            print("\nErrors:")
            for repo, error in result.errors:
                print(f"  - {repo}: {error}")
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
