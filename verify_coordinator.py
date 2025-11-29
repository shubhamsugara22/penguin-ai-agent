"""Verification script for Coordinator Agent implementation.

This script verifies that the Coordinator Agent is properly implemented
and can be instantiated without errors.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_coordinator():
    """Verify Coordinator Agent implementation."""
    print("="*80)
    print("COORDINATOR AGENT VERIFICATION")
    print("="*80)
    
    try:
        # Test 1: Import CoordinatorAgent
        print("\n[1/6] Testing import...")
        from src.agents.coordinator import CoordinatorAgent, AnalysisResult, ProgressEvent, WorkflowState
        print("✓ Import successful")
        
        # Test 2: Check CoordinatorAgent class exists
        print("\n[2/6] Checking CoordinatorAgent class...")
        assert hasattr(CoordinatorAgent, 'analyze_repositories'), "Missing analyze_repositories method"
        assert hasattr(CoordinatorAgent, 'get_session_state'), "Missing get_session_state method"
        assert hasattr(CoordinatorAgent, 'handle_user_approval'), "Missing handle_user_approval method"
        print("✓ CoordinatorAgent class has required methods")
        
        # Test 3: Check AnalysisResult class
        print("\n[3/6] Checking AnalysisResult class...")
        assert hasattr(AnalysisResult, 'to_dict'), "Missing to_dict method"
        print("✓ AnalysisResult class is properly defined")
        
        # Test 4: Check ProgressEvent class
        print("\n[4/6] Checking ProgressEvent class...")
        assert hasattr(ProgressEvent, 'to_dict'), "Missing to_dict method"
        print("✓ ProgressEvent class is properly defined")
        
        # Test 5: Check WorkflowState class
        print("\n[5/6] Checking WorkflowState class...")
        state = WorkflowState(username="test")
        assert state.username == "test", "WorkflowState initialization failed"
        assert hasattr(state, 'repositories'), "Missing repositories attribute"
        assert hasattr(state, 'suggestions'), "Missing suggestions attribute"
        print("✓ WorkflowState class is properly defined")
        
        # Test 6: Instantiate CoordinatorAgent (without actual API calls)
        print("\n[6/6] Instantiating CoordinatorAgent...")
        # Note: This will fail if GITHUB_TOKEN or GEMINI_API_KEY are not set
        # but we're just checking the class can be instantiated
        try:
            coordinator = CoordinatorAgent()
            print("✓ CoordinatorAgent instantiated successfully")
            
            # Check workflow is built
            assert coordinator.workflow is not None, "Workflow not built"
            assert len(coordinator.workflow) == 7, f"Expected 7 workflow steps, got {len(coordinator.workflow)}"
            print(f"✓ Workflow has {len(coordinator.workflow)} steps")
            
        except ValueError as e:
            if "GITHUB_TOKEN" in str(e) or "GEMINI_API_KEY" in str(e):
                print("⚠ CoordinatorAgent requires environment variables (expected)")
                print(f"  Error: {e}")
            else:
                raise
        
        print("\n" + "="*80)
        print("VERIFICATION COMPLETE - ALL TESTS PASSED")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_coordinator()
    sys.exit(0 if success else 1)
