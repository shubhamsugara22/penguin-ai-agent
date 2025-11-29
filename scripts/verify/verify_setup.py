"""Verification script to check project setup without requiring all dependencies."""

import os
import sys
from pathlib import Path


def check_directory_structure():
    """Verify that all required directories exist."""
    print("Checking directory structure...")
    
    required_dirs = [
        "src",
        "src/agents",
        "src/tools",
        "src/models",
        "src/memory",
        "tests",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists() and full_path.is_dir():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_required_files():
    """Verify that all required files exist."""
    print("\nChecking required files...")
    
    required_files = [
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "ReadME.md",
        "src/__init__.py",
        "src/config.py",
        "src/logging_config.py",
        "src/agents/__init__.py",
        "src/tools/__init__.py",
        "src/models/__init__.py",
        "src/memory/__init__.py",
        "tests/__init__.py",
        "tests/test_config.py",
        "tests/test_logging_config.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists() and full_path.is_file():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_imports():
    """Verify that core modules can be imported."""
    print("\nChecking module imports...")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    modules_to_test = [
        ("src.config", "Config"),
        ("src.logging_config", "setup_logging"),
    ]
    
    all_imported = True
    for module_name, class_or_func in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_func])
            getattr(module, class_or_func)
            print(f"  ✓ {module_name}.{class_or_func}")
        except Exception as e:
            print(f"  ✗ {module_name}.{class_or_func} - ERROR: {e}")
            all_imported = False
    
    return all_imported


def check_config_functionality():
    """Test basic config functionality without environment variables."""
    print("\nChecking config functionality...")
    
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    try:
        from src.config import Config
        
        # Test token masking
        test_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        masked = Config._mask_token(test_token)
        
        if masked.startswith("ghp_") and "..." in masked and masked.endswith("wxyz"):
            print(f"  ✓ Token masking works: {masked}")
        else:
            print(f"  ✗ Token masking failed: {masked}")
            return False
        
        # Test config creation
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key_1234567890"
        )
        
        if config.github_token and config.gemini_api_key:
            print(f"  ✓ Config object creation works")
        else:
            print(f"  ✗ Config object creation failed")
            return False
        
        # Test sanitized config
        sanitized = config.get_sanitized_config()
        if "..." in sanitized["github_token"] and "..." in sanitized["gemini_api_key"]:
            print(f"  ✓ Config sanitization works")
        else:
            print(f"  ✗ Config sanitization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Config functionality check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_logging_functionality():
    """Test basic logging functionality."""
    print("\nChecking logging functionality...")
    
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    try:
        from src.logging_config import CredentialSanitizer
        
        # Test token sanitization
        test_text = "Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz for auth"
        sanitized = CredentialSanitizer.sanitize(test_text)
        
        if "[REDACTED]" in sanitized and "ghp_" not in sanitized:
            print(f"  ✓ Credential sanitization works")
        else:
            print(f"  ✗ Credential sanitization failed: {sanitized}")
            return False
        
        # Test dict sanitization
        test_dict = {"token": "secret123", "username": "testuser"}
        sanitized_dict = CredentialSanitizer.sanitize_dict(test_dict)
        
        if sanitized_dict["token"] == "[REDACTED]" and sanitized_dict["username"] == "testuser":
            print(f"  ✓ Dictionary sanitization works")
        else:
            print(f"  ✗ Dictionary sanitization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Logging functionality check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("GitHub Maintainer Agent - Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Directory Structure", check_directory_structure()))
    results.append(("Required Files", check_required_files()))
    results.append(("Module Imports", check_imports()))
    results.append(("Config Functionality", check_config_functionality()))
    results.append(("Logging Functionality", check_logging_functionality()))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{check_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Project setup is complete.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
