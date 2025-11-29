"""Maintainer Agent for generating and managing maintenance suggestions.

This agent converts health assessments into actionable maintenance tasks,
prioritizes suggestions, handles deduplication, and creates GitHub issues.
"""

import logging
import time
from typing import List, Optional
from datetime import datetime
import json
import hashlib

import google.generativeai as genai

from ..models.health import RepositoryProfile
from ..models.maintenance import MaintenanceSuggestion, IssueResult
from ..models.session import UserPreferences
from ..memory.memory_bank import MemoryBank
from ..tools.github_tools import create_issue
from ..tools.github_client import GitHubClient
from ..config import get_config
from ..observability import get_metrics_collector

logger = logging.getLogger(__name__)


class MaintainerAgent:
    """Agent responsible for generating maintenance suggestions and creating issues."""
    
    def __init__(
        self,
        memory_bank: Optional[MemoryBank] = None,
        github_client: Optional[GitHubClient] = None
    ):
        """Initialize the Maintainer Agent.
        
        Args:
            memory_bank: Optional memory bank instance for deduplication
            github_client: Optional GitHub client instance
        """
        self.memory_bank = memory_bank or MemoryBank()
        self.github_client = github_client or GitHubClient()
        
        # Initialize Gemini
        config = get_config()
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("Maintainer Agent initialized")
    
    def generate_suggestions(
        self,
        profiles: List[RepositoryProfile],
        user_preferences: Optional[UserPreferences] = None
    ) -> List[MaintenanceSuggestion]:
        """Generate maintenance suggestions from repository profiles.
        
        Args:
            profiles: List of repository profiles to analyze
            user_preferences: Optional user preferences for filtering
            
        Returns:
            List of MaintenanceSuggestion objects
        """
        metrics = get_metrics_collector()
        
        logger.info(
            f"Generating suggestions for {len(profiles)} repositories",
            extra={
                'agent': 'MaintainerAgent',
                'event': 'generate_suggestions_start',
                'extra_data': {'profile_count': len(profiles)}
            }
        )
        
        all_suggestions = []
        
        for profile in profiles:
            try:
                # Skip excluded repositories
                if user_preferences and profile.repository.full_name in user_preferences.excluded_repos:
                    logger.info(
                        f"Skipping excluded repository: {profile.repository.full_name}",
                        extra={
                            'agent': 'MaintainerAgent',
                            'event': 'skip_excluded_repo',
                            'repository': profile.repository.full_name
                        }
                    )
                    continue
                
                # Generate suggestions for this repository
                repo_suggestions = self._generate_repo_suggestions(profile, user_preferences)
                
                # Deduplicate against memory
                unique_suggestions = self._deduplicate_suggestions(
                    profile.repository.full_name,
                    repo_suggestions
                )
                
                # Record metrics for each suggestion
                for suggestion in unique_suggestions:
                    metrics.record_suggestion_generated(
                        profile.repository.full_name,
                        suggestion.category,
                        suggestion.priority
                    )
                
                all_suggestions.extend(unique_suggestions)
                
                logger.info(
                    f"Generated {len(unique_suggestions)} unique suggestions for {profile.repository.full_name}",
                    extra={
                        'agent': 'MaintainerAgent',
                        'event': 'repo_suggestions_generated',
                        'repository': profile.repository.full_name,
                        'metrics': {
                            'suggestion_count': len(unique_suggestions),
                            'duplicates_filtered': len(repo_suggestions) - len(unique_suggestions)
                        }
                    }
                )
                
            except Exception as e:
                metrics.record_error('suggestion_generation_error')
                logger.error(
                    f"Failed to generate suggestions for {profile.repository.full_name}: {e}",
                    extra={
                        'agent': 'MaintainerAgent',
                        'event': 'generate_suggestions_error',
                        'repository': profile.repository.full_name,
                        'extra_data': {'error': str(e)}
                    }
                )
                continue
        
        # Prioritize all suggestions
        prioritized = self.prioritize_suggestions(all_suggestions)
        
        logger.info(
            f"Generated {len(prioritized)} total suggestions",
            extra={
                'agent': 'MaintainerAgent',
                'event': 'generate_suggestions_complete',
                'metrics': {'total_suggestions': len(prioritized)}
            }
        )
        
        return prioritized
    
    def _generate_repo_suggestions(
        self,
        profile: RepositoryProfile,
        user_preferences: Optional[UserPreferences] = None
    ) -> List[MaintenanceSuggestion]:
        """Generate suggestions for a single repository using LLM.
        
        Args:
            profile: Repository profile
            user_preferences: Optional user preferences
            
        Returns:
            List of MaintenanceSuggestion objects
        """
        metrics = get_metrics_collector()
        start_time = time.time()
        
        # Prepare context for LLM
        context = self._prepare_suggestion_context(profile, user_preferences)
        
        # Create prompt for suggestion generation
        prompt = self._create_suggestion_prompt(context)
        
        try:
            # Call LLM for suggestion generation
            response = self.model.generate_content(prompt)
            
            # Record token usage if available
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                metrics.record_token_usage(
                    'gemini-1.5-flash',
                    usage.prompt_token_count,
                    usage.candidates_token_count
                )
            
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_api_call('gemini', 'generate_suggestions', duration_ms, success=True)
            
            # Parse LLM response
            suggestions = self._parse_suggestion_response(response.text, profile)
            
            logger.debug(
                f"LLM generated {len(suggestions)} suggestions for {profile.repository.full_name}",
                extra={
                    'agent': 'MaintainerAgent',
                    'event': 'llm_suggestions_generated',
                    'repository': profile.repository.full_name,
                    'metrics': {'duration_ms': duration_ms, 'suggestion_count': len(suggestions)}
                }
            )
            
            return suggestions
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_api_call('gemini', 'generate_suggestions', duration_ms, success=False, error=str(e))
            metrics.record_error('llm_error')
            metrics.record_recovery('fallback_suggestions')
            
            logger.error(
                f"Failed to generate suggestions via LLM: {e}",
                extra={
                    'agent': 'MaintainerAgent',
                    'event': 'llm_suggestions_error',
                    'repository': profile.repository.full_name,
                    'extra_data': {'error': str(e), 'using_fallback': True}
                }
            )
            # Fallback to rule-based suggestions
            return self._fallback_suggestions(profile)
    
    def _prepare_suggestion_context(
        self,
        profile: RepositoryProfile,
        user_preferences: Optional[UserPreferences] = None
    ) -> dict:
        """Prepare compact context for suggestion generation.
        
        Args:
            profile: Repository profile
            user_preferences: Optional user preferences
            
        Returns:
            Context dictionary
        """
        health = profile.health
        
        context = {
            'repo_name': profile.repository.full_name,
            'purpose': profile.purpose,
            'tech_stack': profile.tech_stack,
            'activity_level': health.activity_level,
            'test_coverage': health.test_coverage,
            'documentation_quality': health.documentation_quality,
            'ci_cd_status': health.ci_cd_status,
            'dependency_status': health.dependency_status,
            'overall_health_score': health.overall_health_score,
            'issues_identified': health.issues_identified,
            'focus_areas': user_preferences.focus_areas if user_preferences else []
        }
        
        return context
    
    def _create_suggestion_prompt(self, context: dict) -> str:
        """Create prompt for LLM suggestion generation.
        
        Args:
            context: Repository context
            
        Returns:
            Prompt string
        """
        focus_areas_text = ""
        if context['focus_areas']:
            focus_areas_text = f"\nUser Focus Areas: {', '.join(context['focus_areas'])}"
        
        return f"""Generate actionable maintenance suggestions for this GitHub repository.

Repository: {context['repo_name']}
Purpose: {context['purpose']}
Tech Stack: {', '.join(context['tech_stack'])}

Health Assessment:
- Activity Level: {context['activity_level']}
- Test Coverage: {context['test_coverage']}
- Documentation Quality: {context['documentation_quality']}
- CI/CD Status: {context['ci_cd_status']}
- Dependency Status: {context['dependency_status']}
- Overall Health Score: {context['overall_health_score']:.2f}

Issues Identified:
{chr(10).join('- ' + issue for issue in context['issues_identified'])}{focus_areas_text}

Generate 2-5 specific, actionable maintenance suggestions. For each suggestion, provide:

1. Category (bug, enhancement, documentation, refactor, security)
2. Priority (high, medium, low)
3. Title (concise, actionable)
4. Description (detailed, specific steps)
5. Rationale (why this is important)
6. Estimated Effort (small, medium, large)
7. Labels (2-4 relevant labels)

Respond in the following JSON format:
{{
  "suggestions": [
    {{
      "category": "documentation",
      "priority": "high",
      "title": "Add comprehensive README documentation",
      "description": "Create a detailed README with installation instructions, usage examples, and API documentation.",
      "rationale": "Good documentation improves adoption and reduces support burden.",
      "estimated_effort": "medium",
      "labels": ["documentation", "good-first-issue"]
    }}
  ]
}}

Guidelines:
- Focus on high-impact, actionable tasks
- Be specific about what needs to be done
- Consider the repository's purpose and tech stack
- Prioritize based on health issues identified
- Suggest realistic improvements
- Limit to 5 suggestions maximum

Respond with ONLY the JSON object, no additional text."""
    
    def _parse_suggestion_response(
        self,
        response_text: str,
        profile: RepositoryProfile
    ) -> List[MaintenanceSuggestion]:
        """Parse LLM response into MaintenanceSuggestion objects.
        
        Args:
            response_text: LLM response text
            profile: Repository profile
            
        Returns:
            List of MaintenanceSuggestion objects
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            suggestions = []
            for suggestion_data in data.get('suggestions', []):
                # Generate unique ID
                suggestion_id = self._generate_suggestion_id(
                    profile.repository.full_name,
                    suggestion_data['title']
                )
                
                suggestion = MaintenanceSuggestion(
                    id=suggestion_id,
                    repository=profile.repository,
                    category=suggestion_data['category'],
                    priority=suggestion_data['priority'],
                    title=suggestion_data['title'],
                    description=suggestion_data['description'],
                    rationale=suggestion_data['rationale'],
                    estimated_effort=suggestion_data['estimated_effort'],
                    labels=suggestion_data['labels']
                )
                
                # Validate the suggestion
                suggestion.validate()
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM suggestion response: {e}")
            # Fallback to rule-based suggestions
            return self._fallback_suggestions(profile)
    
    def _fallback_suggestions(
        self,
        profile: RepositoryProfile
    ) -> List[MaintenanceSuggestion]:
        """Generate suggestions using rule-based logic (fallback).
        
        Args:
            profile: Repository profile
            
        Returns:
            List of MaintenanceSuggestion objects
        """
        logger.info("Using fallback suggestion generation")
        
        suggestions = []
        health = profile.health
        
        # Suggestion 1: Add tests if missing
        if health.test_coverage == "none":
            suggestion_id = self._generate_suggestion_id(
                profile.repository.full_name,
                "Add test suite"
            )
            suggestions.append(MaintenanceSuggestion(
                id=suggestion_id,
                repository=profile.repository,
                category="enhancement",
                priority="high",
                title="Add test suite",
                description="Create a comprehensive test suite to ensure code quality and prevent regressions. "
                           "Include unit tests for core functionality and integration tests for key workflows.",
                rationale="Tests are essential for maintaining code quality and catching bugs early.",
                estimated_effort="large",
                labels=["testing", "enhancement", "good-first-issue"]
            ))
        
        # Suggestion 2: Add CI/CD if missing
        if health.ci_cd_status == "missing":
            suggestion_id = self._generate_suggestion_id(
                profile.repository.full_name,
                "Set up CI/CD pipeline"
            )
            suggestions.append(MaintenanceSuggestion(
                id=suggestion_id,
                repository=profile.repository,
                category="enhancement",
                priority="high",
                title="Set up CI/CD pipeline",
                description="Configure GitHub Actions (or similar) to automatically run tests, linting, "
                           "and other checks on every commit and pull request.",
                rationale="Automated CI/CD ensures code quality and catches issues before they reach production.",
                estimated_effort="medium",
                labels=["ci-cd", "enhancement", "automation"]
            ))
        
        # Suggestion 3: Improve documentation if poor
        if health.documentation_quality in ["poor", "basic"]:
            suggestion_id = self._generate_suggestion_id(
                profile.repository.full_name,
                "Improve documentation"
            )
            suggestions.append(MaintenanceSuggestion(
                id=suggestion_id,
                repository=profile.repository,
                category="documentation",
                priority="medium",
                title="Improve documentation",
                description="Enhance the README with clear installation instructions, usage examples, "
                           "API documentation, and contribution guidelines.",
                rationale="Good documentation improves adoption and reduces support burden.",
                estimated_effort="medium",
                labels=["documentation", "good-first-issue"]
            ))
        
        # Suggestion 4: Address stale/abandoned status
        if health.activity_level in ["stale", "abandoned"]:
            suggestion_id = self._generate_suggestion_id(
                profile.repository.full_name,
                "Review and update repository"
            )
            suggestions.append(MaintenanceSuggestion(
                id=suggestion_id,
                repository=profile.repository,
                category="refactor",
                priority="medium",
                title="Review and update repository",
                description="Review the repository for outdated dependencies, deprecated APIs, "
                           "and stale issues. Update or archive as appropriate.",
                rationale=f"Repository appears {health.activity_level} and may need attention.",
                estimated_effort="large",
                labels=["maintenance", "refactor"]
            ))
        
        return suggestions
    
    def prioritize_suggestions(
        self,
        suggestions: List[MaintenanceSuggestion]
    ) -> List[MaintenanceSuggestion]:
        """Prioritize suggestions by impact and effort.
        
        Args:
            suggestions: List of suggestions to prioritize
            
        Returns:
            Sorted list of suggestions (highest priority first)
        """
        logger.info(f"Prioritizing {len(suggestions)} suggestions")
        
        # Define priority scores
        priority_scores = {"high": 3, "medium": 2, "low": 1}
        effort_scores = {"small": 3, "medium": 2, "large": 1}
        category_scores = {
            "security": 5,
            "bug": 4,
            "enhancement": 3,
            "documentation": 2,
            "refactor": 1
        }
        
        def calculate_score(suggestion: MaintenanceSuggestion) -> float:
            """Calculate priority score for a suggestion."""
            priority = priority_scores.get(suggestion.priority, 1)
            effort = effort_scores.get(suggestion.estimated_effort, 1)
            category = category_scores.get(suggestion.category, 1)
            
            # Score = (priority + category * 2) * effort
            # Higher priority and category, lower effort = higher score
            return (priority + category * 2) * effort
        
        # Sort by score (descending)
        sorted_suggestions = sorted(
            suggestions,
            key=calculate_score,
            reverse=True
        )
        
        logger.info("Suggestions prioritized")
        
        return sorted_suggestions
    
    def _deduplicate_suggestions(
        self,
        repo_full_name: str,
        suggestions: List[MaintenanceSuggestion]
    ) -> List[MaintenanceSuggestion]:
        """Remove duplicate suggestions using memory bank.
        
        Args:
            repo_full_name: Full repository name
            suggestions: List of suggestions to deduplicate
            
        Returns:
            List of unique suggestions
        """
        # Load existing suggestions from memory
        existing_suggestions = self.memory_bank.load_suggestions(repo_full_name)
        existing_titles = {s.title.lower() for s in existing_suggestions}
        
        # Filter out duplicates
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.title.lower() not in existing_titles:
                unique_suggestions.append(suggestion)
            else:
                logger.debug(f"Skipping duplicate suggestion: {suggestion.title}")
        
        return unique_suggestions
    
    def create_github_issue(
        self,
        suggestion: MaintenanceSuggestion,
        user_preferences: Optional[UserPreferences] = None
    ) -> IssueResult:
        """Create a GitHub issue from a maintenance suggestion.
        
        Args:
            suggestion: Maintenance suggestion to create issue for
            user_preferences: Optional user preferences for labels
            
        Returns:
            IssueResult with creation status
        """
        logger.info(f"Creating issue for: {suggestion.title}")
        
        # Prepare issue body
        body = self._format_issue_body(suggestion)
        
        # Prepare labels
        labels = suggestion.labels.copy()
        if user_preferences and user_preferences.preferred_labels:
            # Add user's preferred labels
            labels.extend(user_preferences.preferred_labels)
            # Remove duplicates
            labels = list(set(labels))
        
        # Create the issue
        result = create_issue(
            repo_full_name=suggestion.repository.full_name,
            title=suggestion.title,
            body=body,
            labels=labels,
            client=self.github_client
        )
        
        # If successful, save suggestion to memory
        if result.success:
            try:
                self.memory_bank.save_suggestions(
                    suggestion.repository.full_name,
                    [suggestion]
                )
                logger.info(f"Saved suggestion to memory: {suggestion.title}")
            except Exception as e:
                logger.warning(f"Failed to save suggestion to memory: {e}")
        
        return result
    
    def _format_issue_body(self, suggestion: MaintenanceSuggestion) -> str:
        """Format issue body from suggestion.
        
        Args:
            suggestion: Maintenance suggestion
            
        Returns:
            Formatted issue body
        """
        body = f"""## Description

{suggestion.description}

## Rationale

{suggestion.rationale}

## Details

- **Category**: {suggestion.category}
- **Priority**: {suggestion.priority}
- **Estimated Effort**: {suggestion.estimated_effort}

---

*This issue was automatically generated by the AI GitHub Maintainer Agent.*
"""
        return body
    
    def _generate_suggestion_id(self, repo_full_name: str, title: str) -> str:
        """Generate a unique ID for a suggestion.
        
        Args:
            repo_full_name: Full repository name
            title: Suggestion title
            
        Returns:
            Unique suggestion ID
        """
        # Create hash from repo name, title, and timestamp
        content = f"{repo_full_name}:{title}:{datetime.now().isoformat()}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]
