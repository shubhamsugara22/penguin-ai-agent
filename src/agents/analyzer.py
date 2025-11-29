"""Analyzer Agent for repository analysis and health assessment.

This agent examines repository structure, code, and history to generate
health assessments and compact repository profiles.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

import google.generativeai as genai

from ..models.repository import Repository, RepositoryOverview, RepositoryHistory
from ..models.health import HealthSnapshot, RepositoryProfile
from ..tools.github_tools import get_repo_overview, get_repo_history
from ..tools.github_client import GitHubClient, RepositoryNotFoundError, GitHubAPIError
from ..config import get_config
from ..observability import get_metrics_collector

logger = logging.getLogger(__name__)

# Analysis version for tracking changes in analysis logic
ANALYSIS_VERSION = "1.0.0"


class RepositoryAnalysis:
    """Complete analysis result for a repository."""
    
    def __init__(
        self,
        repository: Repository,
        overview: RepositoryOverview,
        history: RepositoryHistory,
        health: HealthSnapshot,
        profile: RepositoryProfile
    ):
        """Initialize repository analysis.
        
        Args:
            repository: Basic repository information
            overview: Repository content overview
            history: Repository activity history
            health: Health assessment
            profile: Compact repository profile
        """
        self.repository = repository
        self.overview = overview
        self.history = history
        self.health = health
        self.profile = profile


class AnalyzerAgent:
    """Agent responsible for analyzing repositories and assessing health."""
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        """Initialize the Analyzer Agent.
        
        Args:
            github_client: Optional GitHub client instance
        """
        self.github_client = github_client or GitHubClient()
        
        # Initialize Gemini
        config = get_config()
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("Analyzer Agent initialized")
    
    def analyze_repository(self, repo: Repository) -> RepositoryAnalysis:
        """Analyze a single repository.
        
        Args:
            repo: Repository to analyze
            
        Returns:
            RepositoryAnalysis with complete analysis results
            
        Raises:
            RepositoryNotFoundError: If repository doesn't exist
            GitHubAPIError: If API request fails
        """
        metrics = get_metrics_collector()
        start_time = time.time()
        
        logger.info(
            f"Analyzing repository: {repo.full_name}",
            extra={
                'agent': 'AnalyzerAgent',
                'event': 'analyze_repository_start',
                'repository': repo.full_name
            }
        )
        
        try:
            # Fetch repository data
            overview = get_repo_overview(repo.full_name, self.github_client)
            history = get_repo_history(repo.full_name, limit=100, client=self.github_client)
            
            # Generate health snapshot using LLM
            health = self.generate_health_snapshot(overview, history)
            
            # Create repository profile
            profile = self.create_repository_profile(repo, overview, history, health)
            
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_analysis_duration(repo.full_name, duration_ms, success=True)
            
            logger.info(
                f"Successfully analyzed {repo.full_name}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'analyze_repository_complete',
                    'repository': repo.full_name,
                    'metrics': {
                        'duration_ms': duration_ms,
                        'health_score': health.overall_health_score,
                        'issues_found': len(health.issues_identified)
                    }
                }
            )
            
            return RepositoryAnalysis(
                repository=repo,
                overview=overview,
                history=history,
                health=health,
                profile=profile
            )
            
        except RepositoryNotFoundError:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_analysis_duration(repo.full_name, duration_ms, success=False, error='not_found')
            metrics.record_error('repository_not_found')
            
            logger.error(
                f"Repository not found: {repo.full_name}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'analyze_repository_error',
                    'repository': repo.full_name
                }
            )
            raise
        except GitHubAPIError as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_analysis_duration(repo.full_name, duration_ms, success=False, error=str(e))
            metrics.record_error('github_api_error')
            
            logger.error(
                f"Failed to analyze {repo.full_name}: {e}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'analyze_repository_error',
                    'repository': repo.full_name,
                    'extra_data': {'error': str(e)}
                }
            )
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_analysis_duration(repo.full_name, duration_ms, success=False, error=str(e))
            metrics.record_error('unexpected_error')
            
            logger.error(
                f"Unexpected error analyzing {repo.full_name}: {e}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'analyze_repository_error',
                    'repository': repo.full_name,
                    'extra_data': {'error': str(e)}
                },
                exc_info=True
            )
            raise
    
    def analyze_repositories_parallel(
        self,
        repos: List[Repository],
        max_workers: Optional[int] = None
    ) -> List[RepositoryAnalysis]:
        """Analyze multiple repositories in parallel.
        
        Args:
            repos: List of repositories to analyze
            max_workers: Maximum number of parallel workers (defaults to config)
            
        Returns:
            List of RepositoryAnalysis results
        """
        if max_workers is None:
            config = get_config()
            max_workers = config.max_parallel_repos
        
        logger.info(f"Analyzing {len(repos)} repositories with {max_workers} workers")
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_repo = {
                executor.submit(self.analyze_repository, repo): repo
                for repo in repos
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    analysis = future.result()
                    results.append(analysis)
                except Exception as e:
                    logger.error(f"Failed to analyze {repo.full_name}: {e}")
                    errors.append((repo, e))
        
        logger.info(
            f"Completed analysis: {len(results)} successful, {len(errors)} failed"
        )
        
        return results

    
    def generate_health_snapshot(
        self,
        overview: RepositoryOverview,
        history: RepositoryHistory
    ) -> HealthSnapshot:
        """Generate health assessment from repository data using LLM reasoning.
        
        Args:
            overview: Repository content overview
            history: Repository activity history
            
        Returns:
            HealthSnapshot with health assessment
        """
        metrics = get_metrics_collector()
        start_time = time.time()
        
        logger.info(
            f"Generating health snapshot for {overview.repository.full_name}",
            extra={
                'agent': 'AnalyzerAgent',
                'event': 'generate_health_snapshot_start',
                'repository': overview.repository.full_name
            }
        )
        
        # Prepare compact context for LLM
        context = self._prepare_health_context(overview, history)
        
        # Create prompt for health assessment
        prompt = self._create_health_assessment_prompt(context)
        
        try:
            # Call LLM for health assessment
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
            metrics.record_api_call('gemini', 'generate_health_snapshot', duration_ms, success=True)
            
            # Parse LLM response
            health = self._parse_health_response(response.text, overview, history)
            
            logger.info(
                f"Health snapshot generated for {overview.repository.full_name}: "
                f"score={health.overall_health_score:.2f}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'generate_health_snapshot_complete',
                    'repository': overview.repository.full_name,
                    'metrics': {
                        'duration_ms': duration_ms,
                        'health_score': health.overall_health_score,
                        'activity_level': health.activity_level
                    }
                }
            )
            
            return health
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_api_call('gemini', 'generate_health_snapshot', duration_ms, success=False, error=str(e))
            metrics.record_error('llm_error')
            metrics.record_recovery('fallback_health_assessment')
            
            logger.error(
                f"Failed to generate health snapshot: {e}",
                extra={
                    'agent': 'AnalyzerAgent',
                    'event': 'generate_health_snapshot_error',
                    'repository': overview.repository.full_name,
                    'extra_data': {'error': str(e), 'using_fallback': True}
                }
            )
            # Fallback to rule-based assessment
            return self._fallback_health_assessment(overview, history)
    
    def create_repository_profile(
        self,
        repo: Repository,
        overview: RepositoryOverview,
        history: RepositoryHistory,
        health: HealthSnapshot
    ) -> RepositoryProfile:
        """Create compact repository profile for memory storage.
        
        Args:
            repo: Repository information
            overview: Repository content overview
            history: Repository activity history
            health: Health snapshot
            
        Returns:
            RepositoryProfile with compact summary
        """
        logger.info(f"Creating repository profile for {repo.full_name}")
        
        # Prepare compact context for LLM
        context = self._prepare_profile_context(overview, history)
        
        # Create prompt for profile generation
        prompt = self._create_profile_prompt(context)
        
        try:
            # Call LLM for profile generation
            response = self.model.generate_content(prompt)
            
            # Parse LLM response
            profile_data = self._parse_profile_response(response.text)
            
            # Create profile
            profile = RepositoryProfile(
                repository=repo,
                purpose=profile_data['purpose'],
                tech_stack=profile_data['tech_stack'],
                key_files=profile_data['key_files'],
                health=health,
                last_analyzed=datetime.now(),
                analysis_version=ANALYSIS_VERSION
            )
            
            logger.info(f"Repository profile created for {repo.full_name}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create repository profile: {e}")
            # Fallback to basic profile
            return self._fallback_repository_profile(repo, overview, health)
    
    def _prepare_health_context(
        self,
        overview: RepositoryOverview,
        history: RepositoryHistory
    ) -> Dict[str, Any]:
        """Prepare compact context for health assessment.
        
        This implements context compaction to stay within token limits.
        
        Args:
            overview: Repository content overview
            history: Repository activity history
            
        Returns:
            Compact context dictionary
        """
        # Calculate days since last commit
        days_since_commit = (datetime.now() - history.last_commit_date).days
        
        # Get top languages
        top_languages = sorted(
            overview.languages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Compact README (first 500 chars)
        readme_summary = None
        if overview.readme_content:
            readme_summary = overview.readme_content[:500]
        
        return {
            'repo_name': overview.repository.full_name,
            'days_since_commit': days_since_commit,
            'commit_count': history.commit_count,
            'contributors_count': history.contributors_count,
            'open_issues': history.open_issues_count,
            'closed_issues': history.closed_issues_count,
            'open_prs': history.open_prs_count,
            'has_tests': overview.has_tests,
            'has_ci_config': overview.has_ci_config,
            'has_contributing': overview.has_contributing,
            'has_readme': overview.readme_content is not None,
            'readme_summary': readme_summary,
            'top_languages': [lang for lang, _ in top_languages],
            'file_count': len(overview.file_structure)
        }
    
    def _create_health_assessment_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for LLM health assessment.
        
        Args:
            context: Compact repository context
            
        Returns:
            Prompt string
        """
        return f"""Analyze the health of this GitHub repository and provide an assessment.

Repository: {context['repo_name']}

Activity Metrics:
- Days since last commit: {context['days_since_commit']}
- Total commits: {context['commit_count']}
- Contributors: {context['contributors_count']}
- Open issues: {context['open_issues']}
- Closed issues: {context['closed_issues']}
- Open PRs: {context['open_prs']}

Quality Indicators:
- Has tests: {context['has_tests']}
- Has CI/CD: {context['has_ci_config']}
- Has CONTRIBUTING guide: {context['has_contributing']}
- Has README: {context['has_readme']}
- Top languages: {', '.join(context['top_languages'])}
- File count: {context['file_count']}

README Summary:
{context['readme_summary'] or 'No README found'}

Provide a health assessment in the following JSON format:
{{
  "activity_level": "active|moderate|stale|abandoned",
  "test_coverage": "good|partial|none|unknown",
  "documentation_quality": "excellent|good|basic|poor",
  "ci_cd_status": "configured|missing",
  "dependency_status": "current|outdated|unknown",
  "overall_health_score": 0.0-1.0,
  "issues_identified": ["issue1", "issue2", ...]
}}

Guidelines:
- activity_level: "active" if <30 days, "moderate" if <90 days, "stale" if <180 days, "abandoned" if >180 days
- test_coverage: "good" if has tests and CI, "partial" if has tests only, "none" if no tests, "unknown" if unclear
- documentation_quality: Based on README quality, CONTRIBUTING, and inline docs
- overall_health_score: 0.0 (poor) to 1.0 (excellent) based on all factors
- issues_identified: List specific problems found (max 5)

Respond with ONLY the JSON object, no additional text."""
    
    def _parse_health_response(
        self,
        response_text: str,
        overview: RepositoryOverview,
        history: RepositoryHistory
    ) -> HealthSnapshot:
        """Parse LLM response into HealthSnapshot.
        
        Args:
            response_text: LLM response text
            overview: Repository overview (for fallback)
            history: Repository history (for fallback)
            
        Returns:
            HealthSnapshot object
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate and create HealthSnapshot
            health = HealthSnapshot(
                activity_level=data['activity_level'],
                test_coverage=data['test_coverage'],
                documentation_quality=data['documentation_quality'],
                ci_cd_status=data['ci_cd_status'],
                dependency_status=data['dependency_status'],
                overall_health_score=float(data['overall_health_score']),
                issues_identified=data['issues_identified']
            )
            
            # Validate the health snapshot
            health.validate()
            
            return health
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM health response: {e}")
            # Fallback to rule-based assessment
            return self._fallback_health_assessment(overview, history)
    
    def _fallback_health_assessment(
        self,
        overview: RepositoryOverview,
        history: RepositoryHistory
    ) -> HealthSnapshot:
        """Generate health assessment using rule-based logic (fallback).
        
        Args:
            overview: Repository content overview
            history: Repository activity history
            
        Returns:
            HealthSnapshot object
        """
        logger.info("Using fallback health assessment")
        
        # Determine activity level
        days_since_commit = (datetime.now() - history.last_commit_date).days
        if days_since_commit < 30:
            activity_level = "active"
        elif days_since_commit < 90:
            activity_level = "moderate"
        elif days_since_commit < 180:
            activity_level = "stale"
        else:
            activity_level = "abandoned"
        
        # Determine test coverage
        if overview.has_tests and overview.has_ci_config:
            test_coverage = "good"
        elif overview.has_tests:
            test_coverage = "partial"
        else:
            test_coverage = "none"
        
        # Determine documentation quality
        has_readme = overview.readme_content is not None
        readme_length = len(overview.readme_content) if has_readme else 0
        
        if has_readme and readme_length > 1000 and overview.has_contributing:
            documentation_quality = "excellent"
        elif has_readme and readme_length > 500:
            documentation_quality = "good"
        elif has_readme:
            documentation_quality = "basic"
        else:
            documentation_quality = "poor"
        
        # CI/CD status
        ci_cd_status = "configured" if overview.has_ci_config else "missing"
        
        # Dependency status (unknown without deeper analysis)
        dependency_status = "unknown"
        
        # Calculate overall health score
        score = 0.0
        
        # Activity contributes 30%
        activity_scores = {"active": 1.0, "moderate": 0.7, "stale": 0.4, "abandoned": 0.1}
        score += activity_scores[activity_level] * 0.3
        
        # Tests contribute 25%
        test_scores = {"good": 1.0, "partial": 0.6, "none": 0.0, "unknown": 0.3}
        score += test_scores[test_coverage] * 0.25
        
        # Documentation contributes 20%
        doc_scores = {"excellent": 1.0, "good": 0.75, "basic": 0.5, "poor": 0.0}
        score += doc_scores[documentation_quality] * 0.2
        
        # CI/CD contributes 15%
        score += (1.0 if ci_cd_status == "configured" else 0.0) * 0.15
        
        # Contributors contribute 10%
        if history.contributors_count > 10:
            score += 1.0 * 0.1
        elif history.contributors_count > 3:
            score += 0.7 * 0.1
        elif history.contributors_count > 1:
            score += 0.4 * 0.1
        else:
            score += 0.2 * 0.1
        
        # Identify issues
        issues = []
        if activity_level in ["stale", "abandoned"]:
            issues.append(f"Repository is {activity_level} (last commit {days_since_commit} days ago)")
        if test_coverage == "none":
            issues.append("No tests detected")
        if not overview.has_ci_config:
            issues.append("No CI/CD configuration found")
        if documentation_quality == "poor":
            issues.append("Missing or inadequate README")
        if not overview.has_contributing:
            issues.append("No CONTRIBUTING guide found")
        
        return HealthSnapshot(
            activity_level=activity_level,
            test_coverage=test_coverage,
            documentation_quality=documentation_quality,
            ci_cd_status=ci_cd_status,
            dependency_status=dependency_status,
            overall_health_score=score,
            issues_identified=issues
        )

    
    def _prepare_profile_context(
        self,
        overview: RepositoryOverview,
        history: RepositoryHistory
    ) -> Dict[str, Any]:
        """Prepare compact context for profile generation.
        
        Args:
            overview: Repository content overview
            history: Repository activity history
            
        Returns:
            Compact context dictionary
        """
        # Get top languages
        top_languages = sorted(
            overview.languages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Compact README (first 1000 chars)
        readme_summary = None
        if overview.readme_content:
            readme_summary = overview.readme_content[:1000]
        
        # Get key files (limit to top 20)
        key_files = overview.file_structure[:20]
        
        return {
            'repo_name': overview.repository.full_name,
            'readme_summary': readme_summary,
            'top_languages': [lang for lang, _ in top_languages],
            'file_structure': key_files,
            'has_tests': overview.has_tests,
            'has_ci_config': overview.has_ci_config,
            'contributors_count': history.contributors_count
        }
    
    def _create_profile_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for LLM profile generation.
        
        Args:
            context: Compact repository context
            
        Returns:
            Prompt string
        """
        return f"""Analyze this GitHub repository and create a compact profile.

Repository: {context['repo_name']}

README Summary:
{context['readme_summary'] or 'No README found'}

Top Languages: {', '.join(context['top_languages'])}

File Structure (top-level):
{chr(10).join('- ' + f for f in context['file_structure'][:10])}

Quality Indicators:
- Has tests: {context['has_tests']}
- Has CI/CD: {context['has_ci_config']}
- Contributors: {context['contributors_count']}

Provide a compact profile in the following JSON format:
{{
  "purpose": "Brief 1-2 sentence description of what this repository does",
  "tech_stack": ["technology1", "technology2", ...],
  "key_files": ["file1", "file2", ...]
}}

Guidelines:
- purpose: Concise description based on README and file structure
- tech_stack: List main technologies/frameworks (max 5)
- key_files: List important files like README, main source files, config files (max 10)

Respond with ONLY the JSON object, no additional text."""
    
    def _parse_profile_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into profile data.
        
        Args:
            response_text: LLM response text
            
        Returns:
            Profile data dictionary
            
        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
        
        json_str = response_text[json_start:json_end]
        data = json.loads(json_str)
        
        # Validate required fields
        if 'purpose' not in data or not data['purpose']:
            raise ValueError("Missing or empty 'purpose' field")
        if 'tech_stack' not in data or not isinstance(data['tech_stack'], list):
            raise ValueError("Missing or invalid 'tech_stack' field")
        if 'key_files' not in data or not isinstance(data['key_files'], list):
            raise ValueError("Missing or invalid 'key_files' field")
        
        return data
    
    def _fallback_repository_profile(
        self,
        repo: Repository,
        overview: RepositoryOverview,
        health: HealthSnapshot
    ) -> RepositoryProfile:
        """Generate repository profile using rule-based logic (fallback).
        
        Args:
            repo: Repository information
            overview: Repository content overview
            health: Health snapshot
            
        Returns:
            RepositoryProfile object
        """
        logger.info("Using fallback repository profile")
        
        # Generate basic purpose from repo name
        purpose = f"A {repo.name.replace('-', ' ').replace('_', ' ')} project"
        
        # Extract tech stack from languages
        tech_stack = list(overview.languages.keys())[:5]
        
        # Identify key files
        key_files = []
        important_patterns = [
            'README', 'LICENSE', 'CONTRIBUTING', 'setup.py', 'package.json',
            'requirements.txt', 'Dockerfile', 'Makefile', '.gitignore'
        ]
        
        for file in overview.file_structure:
            for pattern in important_patterns:
                if pattern.lower() in file.lower():
                    key_files.append(file)
                    break
            if len(key_files) >= 10:
                break
        
        return RepositoryProfile(
            repository=repo,
            purpose=purpose,
            tech_stack=tech_stack,
            key_files=key_files,
            health=health,
            last_analyzed=datetime.now(),
            analysis_version=ANALYSIS_VERSION
        )
