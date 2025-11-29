#!/usr/bin/env python3
"""
Debug script to test repository analysis step by step
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.tools.github_tools import list_repos, RepositoryFilters
from src.config import get_config

def debug_analysis():
    """Debug the analysis process step by step"""
    
    print("=" * 80)
    print("Debug Analysis")
    print("=" * 80)
    
    # Step 1: Load config
    print("\n1. Loading configuration...")
    try:
        config = get_config()
        print(f"   ✓ Config loaded")
        print(f"   ✓ GitHub token: {config.github_token[:10]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: Test list_repos without filters
    print("\n2. Testing list_repos (no filters)...")
    username = "shubhamsugara22"
    
    try:
        repos = list_repos(username)
        print(f"   ✓ Found {len(repos)} repositories")
        
        if repos:
            print("\n   First 5 repositories:")
            for i, repo in enumerate(repos[:5], 1):
                print(f"   {i}. {repo.name}")
                print(f"      - Full name: {repo.full_name}")
                print(f"      - Updated: {repo.updated_at}")
                print(f"      - Visibility: {repo.visibility}")
        else:
            print("   ⚠️  No repositories returned!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test with Python filter
    print("\n3. Testing list_repos (Python filter)...")
    
    try:
        filters = RepositoryFilters(language="Python")
        repos = list_repos(username, filters=filters)
        print(f"   ✓ Found {len(repos)} Python repositories")
        
        if repos:
            print("\n   Python repositories:")
            for i, repo in enumerate(repos[:5], 1):
                print(f"   {i}. {repo.name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Test with date filter
    print("\n4. Testing list_repos (date filter)...")
    
    try:
        filters = RepositoryFilters(updated_after="2024-01-01")
        repos = list_repos(username, filters=filters)
        print(f"   ✓ Found {len(repos)} repositories updated after 2024-01-01")
        
        if repos:
            print("\n   Recent repositories:")
            for i, repo in enumerate(repos[:5], 1):
                print(f"   {i}. {repo.name} (updated: {repo.updated_at})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ Debug complete!")
    print("=" * 80)

if __name__ == '__main__':
    debug_analysis()
