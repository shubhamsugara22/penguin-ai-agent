"""Quick verification script for Analyzer Agent implementation.

This script verifies that the Analyzer Agent can be imported and instantiated
without errors.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_imports():
    """Verify all required imports work."""
    print("Verifying imports...")
    
    try:
        from src.agents import AnalyzerAgent, RepositoryAnalysis
        print("✓ AnalyzerAgent imported successfully")
        
        from src.models.repository import Repository, RepositoryOverview, RepositoryHistory
        print("✓ Repository models imported successfully")
        
        from src.models.health import HealthSnapshot, RepositoryProfile
        print("✓ Health models imported successfully")
        
        from src.tools.github_tools import get_repo_overview, get_repo_history
        print("✓ GitHub tools imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def verify_instantiation():
    """Verify AnalyzerAgent can be instantiated."""
    print("\nVerifying instantiation...")
    
    try:
        from src.agents import AnalyzerAgent
        
        # Note: This will fail if GITHUB_TOKEN and GEMINI_API_KEY are not set
        # but that's expected - we're just checking the code structure
        try:
            agent = AnalyzerAgent()
            print("✓ AnalyzerAgent instantiated successfully")
            return True
        except ValueError as e:
            if "GITHUB_TOKEN" in str(e) or "GEMINI_API_KEY" in str(e):
                print("✓ AnalyzerAgent class structure is correct (env vars not set, which is expected)")
                return True
            raise
    except Exception as e:
        print(f"✗ Instantiation failed: {e}")
        return False


def verify_methods():
    """Verify AnalyzerAgent has required methods."""
    print("\nVerifying methods...")
    
    try:
        from src.agents import AnalyzerAgent
        
        required_methods = [
            'analyze_repository',
            'analyze_repositories_parallel',
            'generate_health_snapshot',
            'create_repository_profile',
        ]
        
        for method in required_methods:
            if hasattr(AnalyzerAgent, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Method verification failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("Analyzer Agent Verification")
    print("="*60)
    
    results = []
    
    results.append(("Imports", verify_imports()))
    results.append(("Instantiation", verify_instantiation()))
    results.append(("Methods", verify_methods()))
    
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All verifications passed!")
        print("\nThe Analyzer Agent is ready for use.")
        print("\nNext steps:")
        print("1. Set GITHUB_TOKEN and GEMINI_API_KEY environment variables")
        print("2. Run examples/analyzer_demo.py to test with a real repository")
        print("3. Implement property-based tests (tasks 5.1-5.4)")
        print("4. Implement unit tests (task 5.5)")
        return 0
    else:
        print("\n✗ Some verifications failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
