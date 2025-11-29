#!/usr/bin/env python3
"""Main CLI entry point for GitHub Maintainer Agent.

This module provides a command-line interface for analyzing GitHub repositories,
generating maintenance suggestions, and creating GitHub issues.
"""

import sys
import argparse
import logging
from typing import List, Optional
from datetime import datetime

from src.config import get_config, Config
from src.auth import validate_startup_credentials
from src.agents.coordinator import CoordinatorAgent, ProgressEvent, AnalysisResult
from src.models.maintenance import MaintenanceSuggestion
from src.models.session import UserPreferences
from src.tools.github_tools import RepositoryFilters
from src.logging_config import setup_logging


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print a formatted header.
    
    Args:
        text: Header text to print
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print a success message.
    
    Args:
        text: Success message to print
    """
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print an error message.
    
    Args:
        text: Error message to print
    """
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print a warning message.
    
    Args:
        text: Warning message to print
    """
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print an info message.
    
    Args:
        text: Info message to print
    """
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def progress_callback(event: ProgressEvent) -> None:
    """Callback for progress updates during analysis.
    
    Args:
        event: Progress event with stage and message information
    """
    stage_icons = {
        'initialization': '🚀',
        'fetching': '📥',
        'analyzing': '🔍',
        'generating_suggestions': '💡',
        'requesting_approvals': '✋',
        'creating_issues': '📝',
        'finalizing': '✅',
        'complete': '🎉'
    }
    
    icon = stage_icons.get(event.stage, '•')
    
    if event.total > 0:
        progress_pct = (event.current / event.total) * 100
        print(f"{icon} [{event.stage}] {event.message} ({event.current}/{event.total} - {progress_pct:.0f}%)")
    else:
        print(f"{icon} [{event.stage}] {event.message}")
    
    # Print issue URL if available in metadata
    if event.metadata and 'issue_url' in event.metadata and event.metadata['issue_url']:
        print(f"   → {Colors.OKBLUE}{event.metadata['issue_url']}{Colors.ENDC}")


def approval_callback(suggestions: List[MaintenanceSuggestion]) -> List[MaintenanceSuggestion]:
    """Interactive callback for approving suggestions.
    
    Args:
        suggestions: List of suggestions to approve
        
    Returns:
        List of approved suggestions
    """
    if not suggestions:
        return []
    
    print_header("Maintenance Suggestions")
    print(f"Found {len(suggestions)} maintenance suggestions.\n")
    
    # Group suggestions by repository
    suggestions_by_repo = {}
    for suggestion in suggestions:
        repo_name = suggestion.repository.full_name
        if repo_name not in suggestions_by_repo:
            suggestions_by_repo[repo_name] = []
        suggestions_by_repo[repo_name].append(suggestion)
    
    # Display suggestions grouped by repository
    for repo_name, repo_suggestions in suggestions_by_repo.items():
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}Repository: {repo_name}{Colors.ENDC}")
        print(f"{'-' * 80}")
        
        for i, suggestion in enumerate(repo_suggestions, 1):
            priority_color = {
                'high': Colors.FAIL,
                'medium': Colors.WARNING,
                'low': Colors.OKGREEN
            }.get(suggestion.priority, '')
            
            print(f"\n{Colors.BOLD}[{i}] {suggestion.title}{Colors.ENDC}")
            print(f"    Category: {suggestion.category}")
            print(f"    Priority: {priority_color}{suggestion.priority.upper()}{Colors.ENDC}")
            print(f"    Effort: {suggestion.estimated_effort}")
            print(f"    Labels: {', '.join(suggestion.labels)}")
            print(f"\n    {Colors.OKCYAN}Description:{Colors.ENDC}")
            print(f"    {suggestion.description}")
            print(f"\n    {Colors.OKCYAN}Rationale:{Colors.ENDC}")
            print(f"    {suggestion.rationale}")
    
    # Ask for approval
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"\n{Colors.BOLD}Approval Options:{Colors.ENDC}")
    print("  [a] Approve all suggestions")
    print("  [n] Approve none (skip issue creation)")
    print("  [s] Select specific suggestions to approve")
    print("  [q] Quit without creating issues")
    
    while True:
        choice = input(f"\n{Colors.BOLD}Your choice: {Colors.ENDC}").strip().lower()
        
        if choice == 'a':
            print_success(f"Approved all {len(suggestions)} suggestions")
            return suggestions
        
        elif choice == 'n':
            print_warning("No suggestions approved")
            return []
        
        elif choice == 's':
            return select_suggestions(suggestions)
        
        elif choice == 'q':
            print_warning("Exiting without creating issues")
            sys.exit(0)
        
        else:
            print_error("Invalid choice. Please enter 'a', 'n', 's', or 'q'")


def select_suggestions(suggestions: List[MaintenanceSuggestion]) -> List[MaintenanceSuggestion]:
    """Allow user to select specific suggestions to approve.
    
    Args:
        suggestions: List of all suggestions
        
    Returns:
        List of selected suggestions
    """
    print(f"\n{Colors.BOLD}Select suggestions to approve:{Colors.ENDC}")
    print("Enter suggestion numbers separated by commas (e.g., 1,3,5)")
    print("Or enter ranges (e.g., 1-3,5,7-9)")
    print("Enter 'all' to approve all, or 'none' to skip")
    
    while True:
        selection = input(f"\n{Colors.BOLD}Selection: {Colors.ENDC}").strip().lower()
        
        if selection == 'all':
            return suggestions
        
        if selection == 'none':
            return []
        
        try:
            # Parse selection
            selected_indices = set()
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range
                    start, end = part.split('-')
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())
                    selected_indices.update(range(start_idx, end_idx + 1))
                else:
                    # Single number
                    selected_indices.add(int(part))
            
            # Validate indices
            if not all(1 <= idx <= len(suggestions) for idx in selected_indices):
                print_error(f"Invalid selection. Please enter numbers between 1 and {len(suggestions)}")
                continue
            
            # Get selected suggestions
            approved = [suggestions[idx - 1] for idx in sorted(selected_indices)]
            print_success(f"Approved {len(approved)} suggestion(s)")
            return approved
            
        except ValueError:
            print_error("Invalid format. Please use numbers, commas, and ranges (e.g., 1,3,5-7)")


def display_results(result: AnalysisResult) -> None:
    """Display analysis results organized by repository.
    
    Args:
        result: Analysis result to display
    """
    print_header("Analysis Results")
    
    # Display summary
    print(f"{Colors.BOLD}Session ID:{Colors.ENDC} {result.session_id}")
    print(f"{Colors.BOLD}Username:{Colors.ENDC} {result.username}")
    print(f"{Colors.BOLD}Repositories Analyzed:{Colors.ENDC} {len(result.repositories_analyzed)}")
    print(f"{Colors.BOLD}Suggestions Generated:{Colors.ENDC} {len(result.suggestions)}")
    print(f"{Colors.BOLD}Issues Created:{Colors.ENDC} {len([i for i in result.issues_created if i.success])}")
    
    # Display metrics
    metrics = result.metrics
    print(f"\n{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
    print(f"  Execution Time: {metrics.execution_time_seconds:.2f}s")
    print(f"  API Calls: {metrics.api_calls_made}")
    print(f"  Tokens Used: {metrics.tokens_used}")
    print(f"  Errors: {metrics.errors_encountered}")
    
    # Display repositories analyzed
    if result.repositories_analyzed:
        print(f"\n{Colors.BOLD}Repositories Analyzed:{Colors.ENDC}")
        for repo in result.repositories_analyzed:
            print(f"  • {repo}")
    
    # Display created issues grouped by repository
    if result.issues_created:
        print(f"\n{Colors.BOLD}Created Issues:{Colors.ENDC}")
        
        # Group by repository
        issues_by_repo = {}
        for issue in result.issues_created:
            if issue.success:
                repo_name = issue.repository.full_name
                if repo_name not in issues_by_repo:
                    issues_by_repo[repo_name] = []
                issues_by_repo[repo_name].append(issue)
        
        for repo_name, issues in issues_by_repo.items():
            print(f"\n  {Colors.OKBLUE}{repo_name}:{Colors.ENDC}")
            for issue in issues:
                print(f"    ✓ {issue.title}")
                print(f"      {Colors.OKCYAN}{issue.issue_url}{Colors.ENDC}")
    
    # Display errors if any
    if result.errors:
        print(f"\n{Colors.WARNING}Errors Encountered:{Colors.ENDC}")
        for repo, error in result.errors:
            print(f"  • {repo}: {error}")
    
    print()


def parse_filters(args: argparse.Namespace) -> Optional[RepositoryFilters]:
    """Parse command-line arguments into repository filters.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        RepositoryFilters if any filters specified, None otherwise
    """
    filters = {}
    
    if args.language:
        filters['language'] = args.language
    
    if args.updated_after:
        filters['updated_after'] = args.updated_after
    
    if args.visibility:
        filters['visibility'] = args.visibility
    
    if args.archived is not None:
        filters['archived'] = args.archived
    
    return RepositoryFilters(**filters) if filters else None


def parse_preferences(args: argparse.Namespace) -> UserPreferences:
    """Parse command-line arguments into user preferences.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        UserPreferences object
    """
    preferences = UserPreferences(user_id=args.username)
    
    if args.automation:
        preferences.automation_level = args.automation
    
    if args.labels:
        preferences.preferred_labels = args.labels.split(',')
    
    if args.exclude:
        preferences.excluded_repos = args.exclude.split(',')
    
    if args.focus:
        preferences.focus_areas = args.focus.split(',')
    
    return preferences


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="AI GitHub Maintainer Agent - Analyze repositories and generate maintenance suggestions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all repositories for a user
  python main.py analyze myusername

  # Analyze with filters
  python main.py analyze myusername --language Python --updated-after 2024-01-01

  # Auto-approve all suggestions
  python main.py analyze myusername --automation auto

  # Specify focus areas
  python main.py analyze myusername --focus tests,docs,security

  # Exclude specific repositories
  python main.py analyze myusername --exclude repo1,repo2
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze GitHub repositories'
    )
    analyze_parser.add_argument(
        'username',
        help='GitHub username to analyze'
    )
    
    # Filter options
    filter_group = analyze_parser.add_argument_group('Repository Filters')
    filter_group.add_argument(
        '--language',
        help='Filter by programming language (e.g., Python, JavaScript)'
    )
    filter_group.add_argument(
        '--updated-after',
        help='Filter by last update date (YYYY-MM-DD)'
    )
    filter_group.add_argument(
        '--visibility',
        choices=['public', 'private', 'all'],
        default='public',
        help='Filter by repository visibility (default: public)'
    )
    filter_group.add_argument(
        '--archived',
        action='store_true',
        default=None,
        help='Include archived repositories'
    )
    filter_group.add_argument(
        '--no-archived',
        dest='archived',
        action='store_false',
        help='Exclude archived repositories (default)'
    )
    
    # Preference options
    pref_group = analyze_parser.add_argument_group('User Preferences')
    pref_group.add_argument(
        '--automation',
        choices=['auto', 'manual', 'ask'],
        default='manual',
        help='Automation level for issue creation (default: manual)'
    )
    pref_group.add_argument(
        '--labels',
        help='Comma-separated list of preferred labels for issues'
    )
    pref_group.add_argument(
        '--exclude',
        help='Comma-separated list of repositories to exclude'
    )
    pref_group.add_argument(
        '--focus',
        help='Comma-separated list of focus areas (e.g., tests,docs,security)'
    )
    
    # Logging options
    analyze_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (overrides LOG_LEVEL env var)'
    )
    analyze_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output (only show final results)'
    )
    
    args = parser.parse_args()
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Handle analyze command
    if args.command == 'analyze':
        return run_analysis(args)
    
    return 0


def run_analysis(args: argparse.Namespace) -> int:
    """Run repository analysis.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load configuration
        print_info("Loading configuration...")
        config = get_config()
        
        # Setup logging
        log_level = args.log_level if hasattr(args, 'log_level') and args.log_level else config.log_level
        setup_logging(log_level)
        
        # Validate credentials on startup
        print_info("Validating credentials...")
        is_valid, error_message = validate_startup_credentials(config)
        if not is_valid:
            print_error("Credential validation failed:")
            print_error(error_message)
            return 1
        
        print_success("Credentials validated successfully")
        print_success("Configuration loaded successfully")
        
        # Parse filters and preferences
        filters = parse_filters(args)
        preferences = parse_preferences(args)
        
        # Display configuration
        print_header("GitHub Maintainer Agent")
        print(f"{Colors.BOLD}Username:{Colors.ENDC} {args.username}")
        
        if filters:
            print(f"{Colors.BOLD}Filters:{Colors.ENDC}")
            if filters.language:
                print(f"  Language: {filters.language}")
            if filters.updated_after:
                print(f"  Updated After: {filters.updated_after}")
            if filters.visibility:
                print(f"  Visibility: {filters.visibility}")
            if filters.archived is not None:
                print(f"  Archived: {filters.archived}")
        
        print(f"{Colors.BOLD}Automation Level:{Colors.ENDC} {preferences.automation_level}")
        
        if preferences.focus_areas:
            print(f"{Colors.BOLD}Focus Areas:{Colors.ENDC} {', '.join(preferences.focus_areas)}")
        
        if preferences.excluded_repos:
            print(f"{Colors.BOLD}Excluded Repos:{Colors.ENDC} {', '.join(preferences.excluded_repos)}")
        
        print()
        
        # Create coordinator agent
        print_info("Initializing agents...")
        coordinator = CoordinatorAgent()
        print_success("Agents initialized")
        
        # Run analysis
        print_info(f"Starting analysis for user: {args.username}")
        print()
        
        # Determine callbacks based on quiet flag
        progress_cb = None if args.quiet else progress_callback
        approval_cb = approval_callback if preferences.automation_level != 'auto' else None
        
        result = coordinator.analyze_repositories(
            username=args.username,
            filters=filters,
            user_preferences=preferences,
            progress_callback=progress_cb,
            approval_callback=approval_cb
        )
        
        # Display results
        display_results(result)
        
        # Success message
        successful_issues = len([i for i in result.issues_created if i.success])
        if successful_issues > 0:
            print_success(f"Analysis complete! Created {successful_issues} issue(s)")
        else:
            print_success("Analysis complete!")
        
        return 0
        
    except KeyboardInterrupt:
        print_warning("\n\nAnalysis interrupted by user")
        return 130
    
    except ValueError as e:
        print_error(f"Configuration error: {e}")
        return 1
    
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logging.exception("Unexpected error during analysis")
        return 1


if __name__ == '__main__':
    sys.exit(main())
