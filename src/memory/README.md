# Memory Management Module

This module provides session and long-term memory management for the GitHub Maintainer Agent.

## Components

### SessionService

Manages in-memory session state for analysis runs.

**Features:**
- Create and manage analysis sessions
- Track current session
- Store session state including repositories analyzed, suggestions generated, and issues created
- Session metrics tracking

**Usage:**
```python
from src.memory import SessionService

service = SessionService()

# Create a new session
session = service.create_session("github_username")

# Get current session
current = service.get_current_session()

# Update session
session.repositories_analyzed.append("user/repo")
service.update_session(session)

# List all sessions
sessions = service.list_sessions()
```

### MemoryBank

Manages long-term storage using JSON files for repository profiles, user preferences, and suggestion history.

**Features:**
- Save/load repository profiles
- Save/load user preferences
- Track suggestion history to prevent duplicates
- Check if suggestions already exist
- Persistent storage across sessions

**Storage Structure:**
```
.github_maintainer_memory/
├── profiles/
│   └── user_repo.json
├── preferences/
│   └── username.json
└── suggestions/
    └── user_repo.json
```

**Usage:**
```python
from src.memory import MemoryBank

memory = MemoryBank(storage_dir=".github_maintainer_memory")

# Save repository profile
memory.save_repository_profile(profile)

# Load repository profile
profile = memory.load_repository_profile("user/repo")

# Save user preferences
memory.save_user_preferences(preferences)

# Load user preferences
prefs = memory.load_user_preferences("username")

# Save suggestions
memory.save_suggestions("user/repo", [suggestion1, suggestion2])

# Load suggestions
suggestions = memory.load_suggestions("user/repo")

# Check if suggestion exists
exists = memory.check_suggestion_exists("user/repo", "Add README")
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 1.5**: Store repository list in session state
- **Requirement 6.1**: Store repository profiles in long-term memory
- **Requirement 6.2**: Retrieve stored profiles for re-analysis
- **Requirement 6.4**: Check long-term memory to avoid repeating suggestions
- **Requirement 6.5**: Persist user preferences in long-term memory

## Testing

Unit tests are available in `tests/test_memory.py`. Run tests with:

```bash
pytest tests/test_memory.py -v
```
