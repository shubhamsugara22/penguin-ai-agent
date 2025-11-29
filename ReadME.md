# GitHub Maintainer Agent

AI-powered multi-agent system for GitHub repository maintenance using LangGraph, Google ADK, and Gemini LLM.

## Overview

The GitHub Maintainer Agent analyzes your GitHub repositories, assesses their health, and generates actionable maintenance suggestions. It uses specialized AI agents to understand repository structure, identify improvement opportunities, and create GitHub issues for tracking maintenance tasks.

## Features

- **Multi-Agent Architecture**: Coordinator, Analyzer, and Maintainer agents work together
- **Repository Analysis**: Automated assessment of code structure, documentation, tests, and CI/CD
- **Health Snapshots**: Comprehensive health scoring for each repository
- **Smart Suggestions**: AI-generated, prioritized maintenance tasks
- **Memory System**: Remembers previous analyses to avoid duplicate suggestions
- **GitHub Integration**: Automatically creates issues from approved suggestions

## Setup

### Prerequisites

- Python 3.11 or higher
- GitHub personal access token
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd penguin-ai-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your tokens
```

Required environment variables:
- `GITHUB_TOKEN`: Your GitHub personal access token ([create one](https://github.com/settings/tokens))
- `GEMINI_API_KEY`: Your Google AI Studio API key ([get one](https://ai.google.dev/tutorials/setup))

### Development Setup

For development with additional tools:
```bash
pip install -e ".[dev]"
```

## Project Structure

```
penguin-ai-agent/
├── src/
│   ├── agents/          # Agent implementations (Coordinator, Analyzer, Maintainer)
│   ├── tools/           # GitHub API tools
│   ├── models/          # Data models and structures
│   ├── memory/          # Session and long-term memory
│   ├── config.py        # Configuration management
│   └── logging_config.py # Structured logging setup
├── tests/               # Test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Dependency list
└── .env.example         # Environment variable template
```

## Usage

Coming soon - CLI interface under development.

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Development

### Code Formatting

Format code with Black:
```bash
black src/ tests/
```

### Linting

Lint code with Ruff:
```bash
ruff check src/ tests/
```

## License

MIT License - see LICENSE file for details.
