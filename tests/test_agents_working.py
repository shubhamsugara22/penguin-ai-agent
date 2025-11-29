#!/usr/bin/env python3
"""
Test script to verify agents are working
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.agents.coordinator import CoordinatorAgent
from src.tools.github_tools import RepositoryFilters
from src.models.session import UserPreferences

def test_agents():
    """Test that agents are working"""
    
    print("=" * 80)
    print("Testing AI Agents")
    print("=" * 80)
    
    # Create coordinator
    print("\n1. Creating Coordinator Agent...")
    try:
        coordinator = CoordinatorAgent()
        print("   ✓ Coordinator created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create coordinator: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with a single repo
    print("\n2. Testing analysis on a single repository...")
    username = "shubhamsugara22"
    
    # Create filters to get just one recent repo
    filters = RepositoryFilters(
        language="Python",
        updated_after="2024-11-01"
    )
    
    # Create preferences
    preferences = UserPreferences(user_id=username)
    preferences.automation_level = "auto"  # Auto-approve for testing
    
    print(f"   Analyzing repos for: {username}")
    print(f"   Filters: Python, updated after 2024-11-01")
    
    try:
        result = coordinator.analyze_repositories(
            username=username,
            filters=filters,
            user_preferences=preferences
        )
        
        print(f"\n   ✓ Analysis complete!")
        print(f"   - Session ID: {result.session_id}")
        print(f"   - Repositories analyzed: {len(result.repositories_analyzed)}")
        print(f"   - Suggestions generated: {len(result.suggestions)}")
        print(f"   - Issues created: {len([i for i in result.issues_created if i.success])}")
        print(f"   - Execution time: {result.metrics.execution_time_seconds:.2f}s")
        print(f"   - API calls: {result.metrics.api_calls_made}")
        print(f"   - Tokens used: {result.metrics.tokens_used}")
        
        if result.repositories_analyzed:
            print(f"\n   Analyzed repositories:")
            for repo in result.repositories_analyzed[:5]:
                print(f"   - {repo}")
        
        if result.suggestions:
            print(f"\n   Generated suggestions:")
            for i, suggestion in enumerate(result.suggestions[:3], 1):
                print(f"   {i}. [{suggestion.priority}] {suggestion.title}")
                print(f"      Repository: {suggestion.repository.full_name}")
                print(f"      Category: {suggestion.category}")
        
        if result.issues_created:
            print(f"\n   Created issues:")
            for issue in result.issues_created:
                if issue.success:
                    print(f"   ✓ {issue.issue_url}")
                else:
                    print(f"   ❌ Failed: {issue.error_message}")
        
        print("\n" + "=" * 80)
        print("✓ Agents are working correctly!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n   ❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_agents()
