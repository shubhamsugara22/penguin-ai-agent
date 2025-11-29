"""Simple test runner for authentication tests."""

import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for testing
os.environ['GITHUB_TOKEN'] = 'ghp_' + 'x' * 36
os.environ['GEMINI_API_KEY'] = 'test_key_1234567890'

from tests.test_auth import (
    TestTokenValidationResult,
    TestAuthenticationManager,
    TestValidateStartupCredentials,
    TestTokenSecurityAudit
)

def run_tests():
    """Run all authentication tests."""
    print("Running Authentication Tests...")
    print("=" * 80)
    
    test_classes = [
        TestTokenValidationResult,
        TestAuthenticationManager,
        TestValidateStartupCredentials,
        TestTokenSecurityAudit
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 80)
        
        # Get all test methods
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            test_instance = test_class()
            
            try:
                # Run setup if exists
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test
                method = getattr(test_instance, method_name)
                method()
                
                print(f"  ✓ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ✗ {method_name}: {str(e)}")
                failed_tests += 1
    
    print("\n" + "=" * 80)
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
    
    return failed_tests == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
