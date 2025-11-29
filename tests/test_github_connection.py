#!/usr/bin/env python3
"""
Quick test script to verify GitHub connection and find repos
"""
import os
import sys
from dotenv import load_dotenv
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_github_connection():
    """Test GitHub API connection and list repos"""
    
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("❌ GITHUB_TOKEN not found in .env file")
        print("\nPlease add your GitHub token to .env:")
        print("GITHUB_TOKEN=ghp_your_token_here")
        return
    
    print("=" * 80)
    print("GitHub Connection Test")
    print("=" * 80)
    
    # Test 1: Verify token
    print("\n1. Testing GitHub token...")
    headers = {'Authorization': f'token {token}'}
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✓ Token is valid!")
            print(f"   ✓ Authenticated as: {user_data['login']}")
            print(f"   ✓ Name: {user_data.get('name', 'N/A')}")
            authenticated_user = user_data['login']
        elif response.status_code == 401:
            print("   ❌ Token is invalid or expired")
            print("   Please generate a new token at: https://github.com/settings/tokens")
            return
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return
    
    # Test 2: List your own repos
    print(f"\n2. Fetching repositories for {authenticated_user}...")
    
    try:
        response = requests.get(
            f'https://api.github.com/users/{authenticated_user}/repos',
            headers=headers,
            params={'per_page': 100, 'sort': 'updated'}
        )
        
        if response.status_code == 200:
            repos = response.json()
            print(f"   ✓ Found {len(repos)} repositories")
            
            if repos:
                print("\n   Your repositories:")
                for i, repo in enumerate(repos[:10], 1):  # Show first 10
                    visibility = "🔒 Private" if repo['private'] else "🌐 Public"
                    updated = repo['updated_at'][:10]
                    print(f"   {i}. {repo['name']} ({visibility}) - Updated: {updated}")
                
                if len(repos) > 10:
                    print(f"   ... and {len(repos) - 10} more")
            else:
                print("   ⚠️  No repositories found")
                print("   This account has no repositories yet")
        else:
            print(f"   ❌ Error fetching repos: {response.status_code}")
            print(f"   {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 3: Check rate limits
    print("\n3. Checking API rate limits...")
    
    try:
        response = requests.get('https://api.github.com/rate_limit', headers=headers)
        
        if response.status_code == 200:
            rate_data = response.json()
            core = rate_data['rate']
            print(f"   ✓ Remaining requests: {core['remaining']}/{core['limit']}")
            print(f"   ✓ Resets at: {core['reset']}")
        else:
            print(f"   ⚠️  Could not check rate limits")
    except Exception as e:
        print(f"   ⚠️  Error checking rate limits: {e}")
    
    # Test 4: Test with a different username
    print("\n4. Testing with a known GitHub user (octocat)...")
    
    try:
        response = requests.get(
            'https://api.github.com/users/octocat/repos',
            headers=headers,
            params={'per_page': 5}
        )
        
        if response.status_code == 200:
            repos = response.json()
            print(f"   ✓ Successfully fetched octocat's repos ({len(repos)} found)")
            if repos:
                print(f"   Example: {repos[0]['name']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✓ Connection test complete!")
    print("=" * 80)
    
    print("\n💡 Next steps:")
    print(f"   1. Use your username: python main.py analyze {authenticated_user}")
    print("   2. Or try a public user: python main.py analyze octocat")
    print("   3. Add filters: python main.py analyze {authenticated_user} --language Python")

if __name__ == '__main__':
    test_github_connection()
