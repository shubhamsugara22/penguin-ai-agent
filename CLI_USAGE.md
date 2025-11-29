# CLI Usage Guide

## Overview

The GitHub Maintainer Agent CLI provides a command-line interface for analyzing GitHub repositories, generating maintenance suggestions, and creating GitHub issues.

## Prerequisites

1. Set up environment variables:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

2. Or create a `.env` file in the project root:
   ```
   GITHUB_TOKEN=your_github_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Basic Usage

### Analyze all repositories for a user

```bash
python main.py analyze username
```

This will:
- Fetch all public repositories for the user
- Analyze each repository's health
- Generate maintenance suggestions
- Prompt for approval before creating issues

### Analyze with filters

```bash
# Filter by programming language
python main.py analyze username --language Python

# Filter by last update date
python main.py analyze username --updated-after 2024-01-01

# Combine multiple filters
python main.py analyze username --language Python --updated-after 2024-01-01 --visibility public
```

### Automation levels

```bash
# Manual approval (default) - prompts for each suggestion
python main.py analyze username --automation manual

# Auto-approve all suggestions
python main.py analyze username --automation auto

# Ask for approval (same as manual)
python main.py analyze username --automation ask
```

### Focus areas

```bash
# Focus on specific areas
python main.py analyze username --focus tests,docs,security

# This will prioritize suggestions related to tests, documentation, and security
```

### Exclude repositories

```bash
# Exclude specific repositories from analysis
python main.py analyze username --exclude repo1,repo2,repo3
```

### Custom labels

```bash
# Add custom labels to created issues
python main.py analyze username --labels "maintenance,automated"
```

### Quiet mode

```bash
# Suppress progress output, only show final results
python main.py analyze username --quiet
```

### Logging

```bash
# Set log level
python main.py analyze username --log-level DEBUG
```

## Complete Examples

### Example 1: Analyze Python repositories updated in 2024

```bash
python main.py analyze myusername \
  --language Python \
  --updated-after 2024-01-01 \
  --focus tests,docs \
  --automation manual
```

### Example 2: Auto-create issues for all repositories

```bash
python main.py analyze myusername \
  --automation auto \
  --labels "maintenance,automated"
```

### Example 3: Analyze with exclusions and custom focus

```bash
python main.py analyze myusername \
  --exclude archived-repo,old-project \
  --focus security,ci-cd \
  --automation manual
```

## Interactive Approval

When using manual approval mode, you'll be presented with suggestions and can:

- **[a]** - Approve all suggestions
- **[n]** - Approve none (skip issue creation)
- **[s]** - Select specific suggestions to approve
- **[q]** - Quit without creating issues

When selecting specific suggestions:
- Enter numbers separated by commas: `1,3,5`
- Use ranges: `1-3,5,7-9`
- Enter `all` to approve all
- Enter `none` to skip all

## Output

The CLI provides:

1. **Progress updates** during analysis:
   - 🚀 Initialization
   - 📥 Fetching repositories
   - 🔍 Analyzing repositories
   - 💡 Generating suggestions
   - ✋ Requesting approvals
   - 📝 Creating issues
   - ✅ Finalizing
   - 🎉 Complete

2. **Suggestion details**:
   - Title and description
   - Category (bug, enhancement, documentation, refactor, security)
   - Priority (high, medium, low)
   - Estimated effort (small, medium, large)
   - Labels
   - Rationale

3. **Final results**:
   - Session ID
   - Repositories analyzed
   - Suggestions generated
   - Issues created (with URLs)
   - Performance metrics
   - Errors encountered

## Error Handling

The CLI handles various error scenarios:

- **Missing credentials**: Clear error message with setup instructions
- **Invalid GitHub token**: Validation and helpful guidance
- **API rate limits**: Graceful handling with user notification
- **Network errors**: Retry logic and error reporting
- **Keyboard interrupt**: Clean exit with Ctrl+C

## Exit Codes

- `0` - Success
- `1` - Configuration or runtime error
- `130` - Interrupted by user (Ctrl+C)

## Tips

1. **Start with filters**: Use `--language` and `--updated-after` to focus on active repositories
2. **Use focus areas**: Specify `--focus` to get targeted suggestions
3. **Test with manual mode**: Use `--automation manual` first to review suggestions
4. **Enable auto mode for routine maintenance**: Use `--automation auto` once you trust the suggestions
5. **Check logs**: Use `--log-level DEBUG` for troubleshooting
6. **Use quiet mode for scripts**: Add `--quiet` when running in automated scripts

## Help

For detailed help on all options:

```bash
python main.py --help
python main.py analyze --help
```
