# Authentication and Security

This document describes the authentication and security features implemented in the GitHub Maintainer Agent.

## Overview

The authentication system provides secure credential management, token validation, and comprehensive logging sanitization to protect sensitive information.

## Features

### 1. Secure Credential Storage

Credentials are stored securely using environment variables:

- `GITHUB_TOKEN`: GitHub personal access token
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Google AI API key

**Best Practices:**
- Never commit credentials to version control
- Use `.env` files for local development (excluded from git)
- Use secure secret management in production (e.g., AWS Secrets Manager, Azure Key Vault)

### 2. Token Validation on Startup

The system validates credentials before starting analysis:

```python
from src.auth import validate_startup_credentials
from src.config import get_config

config = get_config()
is_valid, error_message = validate_startup_credentials(config)

if not is_valid:
    print(f"Error: {error_message}")
    sys.exit(1)
```

**Validation Checks:**
- GitHub token format (40+ characters)
- GitHub token prefix (ghp_, gho_, ghs_, github_pat_)
- GitHub API authentication (makes test API call)
- Gemini API key format (20+ characters)

### 3. Token Sanitization

All logging automatically sanitizes tokens to prevent leakage:

```python
from src.logging_config import CredentialSanitizer

# Sanitize strings
text = "My token is ghp_1234567890abcdefghijklmnopqrstuvwxyz"
safe_text = CredentialSanitizer.sanitize(text)
# Result: "My token is [REDACTED]"

# Sanitize dictionaries
data = {
    'token': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
    'username': 'testuser'
}
safe_data = CredentialSanitizer.sanitize_dict(data)
# Result: {'token': '[REDACTED]', 'username': 'testuser'}
```

**Supported Token Patterns:**
- GitHub personal access tokens: `ghp_*`
- GitHub OAuth tokens: `gho_*`
- GitHub server tokens: `ghs_*`
- GitHub fine-grained tokens: `github_pat_*`
- Google API keys: `AIza*`
- Bearer tokens: `Bearer *`

### 4. Secure API Authentication

All GitHub API calls include authentication headers:

```python
from src.tools.github_client import GitHubClient

client = GitHubClient()  # Automatically uses token from config
repos = client.get('/user/repos')
```

**Security Features:**
- Tokens never logged in plain text
- Automatic retry with exponential backoff
- Rate limit detection and handling
- Clear error messages without exposing credentials

### 5. User Guidance on Auth Failure

When authentication fails, users receive helpful guidance:

```
GitHub authentication failed. Your token may be invalid or expired.
To create a new token:
1. Go to https://github.com/settings/tokens
2. Click 'Generate new token' (classic)
3. Select scopes: 'repo', 'read:user'
4. Copy the token and set it as GITHUB_TOKEN environment variable
```

## Usage

### Setting Up Credentials

1. **Create a GitHub Personal Access Token:**
   - Visit https://github.com/settings/tokens
   - Click "Generate new token" (classic)
   - Select scopes: `repo`, `read:user`
   - Copy the generated token

2. **Get a Google AI API Key:**
   - Visit https://ai.google.dev/tutorials/setup
   - Create a new API key
   - Copy the key

3. **Set Environment Variables:**

   **Linux/Mac:**
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   export GEMINI_API_KEY="your_gemini_key_here"
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:GITHUB_TOKEN="ghp_your_token_here"
   $env:GEMINI_API_KEY="your_gemini_key_here"
   ```

   **Using .env file:**
   ```
   GITHUB_TOKEN=ghp_your_token_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

### Validating Credentials

```python
from src.config import get_config
from src.auth import AuthenticationManager

config = get_config()
auth_manager = AuthenticationManager(config)

# Validate GitHub token
result = auth_manager.validate_github_token()
if result.is_valid:
    print(f"Authenticated as: {result.username}")
else:
    print(f"Error: {result.error_message}")

# Validate all credentials
success, error_msg = auth_manager.validate_credentials_on_startup()
if not success:
    print(f"Validation failed: {error_msg}")
```

## Security Best Practices

### 1. Never Log Tokens

Always use the sanitization utilities:

```python
from src.logging_config import get_logger, CredentialSanitizer

logger = get_logger(__name__)

# BAD - Don't do this
logger.info(f"Using token: {token}")

# GOOD - Sanitize first
logger.info(f"Using token: {CredentialSanitizer.sanitize(token)}")

# BETTER - Use structured logging (automatically sanitizes)
logger.info("Token validated", extra={'token': token})
```

### 2. Mask Tokens in Display

When showing configuration to users:

```python
from src.auth import AuthenticationManager

# Display masked token
masked = AuthenticationManager.sanitize_token_for_display(token)
print(f"Token: {masked}")  # Shows: ghp_...wxyz
```

### 3. Check for Token Leakage

Audit strings for accidental token exposure:

```python
from src.auth import AuthenticationManager

text = "Some log message or output"
if AuthenticationManager.check_token_in_string(text):
    logger.error("WARNING: Token detected in output!")
```

### 4. Secure Error Handling

Never include tokens in error messages:

```python
try:
    client.make_request()
except AuthenticationError as e:
    # GOOD - Generic error message
    logger.error("Authentication failed")
    
    # BAD - Don't include token
    # logger.error(f"Auth failed with token {token}")
```

## Testing

Run authentication tests:

```bash
# Run all authentication tests
python run_auth_tests.py

# Verify authentication features
python verify_auth.py
```

## Troubleshooting

### "GitHub token appears invalid"

**Cause:** Token is too short or has wrong format

**Solution:**
1. Check that token is 40+ characters
2. Verify token starts with `ghp_`, `gho_`, `ghs_`, or `github_pat_`
3. Generate a new token if needed

### "GitHub authentication failed"

**Cause:** Token is invalid, expired, or lacks required scopes

**Solution:**
1. Verify token is correct
2. Check token hasn't expired
3. Ensure token has `repo` and `read:user` scopes
4. Generate a new token with correct scopes

### "Gemini API key appears invalid"

**Cause:** API key is too short or incorrect

**Solution:**
1. Check that key is 20+ characters
2. Verify key is from Google AI Studio
3. Generate a new key if needed

### Rate Limit Errors

**Cause:** Too many API requests

**Solution:**
1. Wait for rate limit to reset (shown in error message)
2. Use a different GitHub token
3. Reduce number of repositories being analyzed

## API Reference

### AuthenticationManager

```python
class AuthenticationManager:
    def __init__(self, config: Config)
    def validate_github_token() -> TokenValidationResult
    def validate_credentials_on_startup() -> Tuple[bool, Optional[str]]
    def get_github_client() -> GitHubClient
    
    @staticmethod
    def sanitize_token_for_display(token: str) -> str
    
    @staticmethod
    def check_token_in_string(text: str) -> bool
```

### CredentialSanitizer

```python
class CredentialSanitizer:
    @classmethod
    def sanitize(cls, text: str) -> str
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]
```

### TokenValidationResult

```python
@dataclass
class TokenValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    username: Optional[str] = None
    scopes: Optional[list] = None
```

## Related Documentation

- [Configuration](../src/config.py) - Environment variable management
- [Logging](../src/logging_config.py) - Structured logging with sanitization
- [GitHub Client](../src/tools/github_client.py) - Authenticated API client
