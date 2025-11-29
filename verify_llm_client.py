"""Verification script for LLM client implementation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.gemini_client import GeminiClient, LLMError, LLMAuthenticationError
from src.config import get_config


def test_client_initialization():
    """Test that client can be initialized."""
    print("Testing client initialization...")
    try:
        client = GeminiClient()
        print("✓ Client initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


def test_simple_generation():
    """Test simple text generation."""
    print("\nTesting simple text generation...")
    try:
        client = GeminiClient()
        response = client.generate(
            prompt="Say 'Hello, World!' and nothing else.",
            temperature=0.0,
            max_output_tokens=20
        )
        
        print(f"✓ Generation successful")
        print(f"  Response: {response.text[:100]}")
        print(f"  Tokens: {response.total_tokens} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
        return True
    except LLMAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("  Please check your GEMINI_API_KEY in .env file")
        return False
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def test_json_generation():
    """Test JSON generation and parsing."""
    print("\nTesting JSON generation...")
    try:
        client = GeminiClient()
        
        prompt = """Generate a simple JSON object with the following structure:
{
  "status": "ok",
  "message": "test message",
  "count": 42
}

Respond with ONLY the JSON object, no additional text."""
        
        json_data = client.generate_json(prompt, temperature=0.0)
        
        print(f"✓ JSON generation successful")
        print(f"  Parsed JSON: {json_data}")
        
        # Validate structure
        if 'status' in json_data and 'message' in json_data and 'count' in json_data:
            print("✓ JSON structure is valid")
            return True
        else:
            print("✗ JSON structure is invalid")
            return False
            
    except Exception as e:
        print(f"✗ JSON generation failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid input."""
    print("\nTesting error handling...")
    try:
        client = GeminiClient(max_retries=1)
        
        # Try with empty prompt (should handle gracefully)
        try:
            response = client.generate(prompt="", temperature=0.0)
            print("✓ Empty prompt handled")
        except LLMError as e:
            print(f"✓ Empty prompt raised LLMError as expected: {type(e).__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_api_key_validation():
    """Test API key validation."""
    print("\nTesting API key validation...")
    try:
        client = GeminiClient()
        is_valid = client.validate_api_key()
        
        if is_valid:
            print("✓ API key is valid")
            return True
        else:
            print("✗ API key validation failed")
            return False
    except Exception as e:
        print(f"✗ API key validation test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("LLM Client Verification")
    print("=" * 60)
    
    # Check if API key is configured
    try:
        # Set a dummy GitHub token if not set (we only need Gemini API key for this test)
        if not os.getenv('GITHUB_TOKEN'):
            os.environ['GITHUB_TOKEN'] = 'dummy_token_for_testing'
        
        config = get_config()
        if not config.gemini_api_key:
            print("\n✗ GEMINI_API_KEY not configured")
            print("  Please set GEMINI_API_KEY in your .env file")
            return False
    except Exception as e:
        print(f"\n✗ Failed to load config: {e}")
        return False
    
    # Run tests
    results = []
    results.append(test_client_initialization())
    results.append(test_simple_generation())
    results.append(test_json_generation())
    results.append(test_error_handling())
    results.append(test_api_key_validation())
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
