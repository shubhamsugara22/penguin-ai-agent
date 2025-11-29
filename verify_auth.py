#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verification script for authentication and security implementation."""

import os
import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import Config
from src.auth import AuthenticationManager, validate_startup_credentials
from src.logging_config import CredentialSanitizer


def test_token_sanitization():
    """Test that tokens are properly sanitized."""
    print("\n1. Testing Token Sanitization...")
    print("-" * 80)
    
    test_tokens = [
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "gho_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghs_1234567890abcdefghijklmnopqrstuvwxyz",
        "github_pat_" + "x" * 82,
        "AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz"
    ]
    
    for token in test_tokens:
        sanitized = CredentialSanitizer.sanitize(token)
        if token in sanitized:
            print(f"  ✗ FAILED: Token not sanitized: {token[:10]}...")
            return False
        print(f"  ✓ Token sanitized: {token[:10]}... -> {sanitized}")
    
    print("  ✓ All tokens properly sanitized")
    return True


def test_token_format_validation():
    """Test token format validation."""
    print("\n2. Testing Token Format Validation...")
    print("-" * 80)
    
    # Test valid token format
    valid_token = "ghp_" + "x" * 36
    config = Config(github_token=valid_token, gemini_api_key="test_key")
    
    if not config.validate_github_token():
        print(f"  ✗ FAILED: Valid token rejected")
        return False
    print(f"  ✓ Valid token accepted (40+ chars)")
    
    # Test invalid token format
    invalid_token = "short"
    config = Config(github_token=invalid_token, gemini_api_key="test_key")
    
    if config.validate_github_token():
        print(f"  ✗ FAILED: Invalid token accepted")
        return False
    print(f"  ✓ Invalid token rejected (too short)")
    
    return True


def test_auth_manager():
    """Test AuthenticationManager functionality."""
    print("\n3. Testing AuthenticationManager...")
    print("-" * 80)
    
    config = Config(
        github_token="ghp_" + "x" * 36,
        gemini_api_key="AIzaSyD" + "x" * 32
    )
    
    auth_manager = AuthenticationManager(config)
    
    # Test token sanitization
    sanitized = auth_manager.sanitize_token_for_display(config.github_token)
    if config.github_token in sanitized:
        print(f"  ✗ FAILED: Token not sanitized in display")
        return False
    print(f"  ✓ Token sanitized for display: {sanitized}")
    
    # Test token detection
    text_with_token = f"My token is {config.github_token}"
    if not auth_manager.check_token_in_string(text_with_token):
        print(f"  ✗ FAILED: Token not detected in string")
        return False
    print(f"  ✓ Token detected in string")
    
    text_without_token = "This is just normal text"
    if auth_manager.check_token_in_string(text_without_token):
        print(f"  ✗ FAILED: False positive token detection")
        return False
    print(f"  ✓ No false positive token detection")
    
    return True


def test_credential_dict_sanitization():
    """Test dictionary sanitization."""
    print("\n4. Testing Dictionary Sanitization...")
    print("-" * 80)
    
    test_dict = {
        'token': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
        'api_key': 'AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz',
        'username': 'testuser',
        'nested': {
            'password': 'secret123',
            'data': 'normal data'
        }
    }
    
    sanitized = CredentialSanitizer.sanitize_dict(test_dict)
    
    # Check sensitive keys are redacted
    if sanitized['token'] != '[REDACTED]':
        print(f"  ✗ FAILED: Token not redacted in dict")
        return False
    print(f"  ✓ Token key redacted")
    
    if sanitized['api_key'] != '[REDACTED]':
        print(f"  ✗ FAILED: API key not redacted in dict")
        return False
    print(f"  ✓ API key redacted")
    
    if sanitized['nested']['password'] != '[REDACTED]':
        print(f"  ✗ FAILED: Password not redacted in nested dict")
        return False
    print(f"  ✓ Nested password redacted")
    
    # Check normal data is preserved
    if sanitized['username'] != 'testuser':
        print(f"  ✗ FAILED: Normal data not preserved")
        return False
    print(f"  ✓ Normal data preserved")
    
    return True


def test_config_sanitization():
    """Test config sanitization."""
    print("\n5. Testing Config Sanitization...")
    print("-" * 80)
    
    config = Config(
        github_token="ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        gemini_api_key="AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz"
    )
    
    sanitized = config.get_sanitized_config()
    
    # Check tokens are masked
    if config.github_token in str(sanitized):
        print(f"  ✗ FAILED: GitHub token not masked in config")
        return False
    print(f"  ✓ GitHub token masked: {sanitized['github_token']}")
    
    if config.gemini_api_key in str(sanitized):
        print(f"  ✗ FAILED: Gemini API key not masked in config")
        return False
    print(f"  ✓ Gemini API key masked: {sanitized['gemini_api_key']}")
    
    return True


def main():
    """Run all verification tests."""
    print("=" * 80)
    print("Authentication and Security Verification")
    print("=" * 80)
    
    tests = [
        test_token_sanitization,
        test_token_format_validation,
        test_auth_manager,
        test_credential_dict_sanitization,
        test_config_sanitization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✓ All authentication and security features verified successfully!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
