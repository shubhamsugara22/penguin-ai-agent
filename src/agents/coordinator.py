"""Coordinator Agent for orchestrating the multi-agent workflow.

This agent manages the overall workflow, coordinates between Analyzer and Maintainer
agents, handles session management, and manages user interactions.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from ..models.repository import Repository
from ..models.health import RepositoryProfile
from ..models.maintenance import MaintenanceSuggestion, IssueResult
from ..models.session import SessionState, SessionMetrics, UserPreferences
from ..tools.github_tools import list_repos, RepositoryFilters
from ..tools.github_client import GitHubClient, GitHubAPIError
from ..memory.session_service import SessionService
from ..memory.memory_bank import MemoryBank
from .analyzer import AnalyzerAgent, RepositoryAnalysis
from .maintainer import MaintainerAgent
from ..config import get_config
from ..observability import get_metrics_collector

logger = logging.getLogger(__name__)


class WorkflowState:
    """State for the coordinator workflow."""
    
    def __init__(
        self,
        username: str = '',
        filters: Optional[RepositoryFilters] = None,
        user_preferences: Optional[UserPreferences] = None,
        progress_callback: Optional[Callable] = None,
        approval_callback: Optional[Callable] = None
    ):
        """Initialize workflow state.
        
        Args:
            username: GitHub username
            filters: Optional repository filters
            user_preferences: Optional user preferences
            progress_callback: Optional callback for progress updates
            approval_callback: Optional callback for suggestion approvals
        """
        self.username = username
        self.filters = filters
        self.user_preferences = user_preferences
        self.session_id = ''
        self.repositories: List[Repository] = []
        self.analyses: List[RepositoryAnalysis] = []
        self.profiles: List[RepositoryProfile] = []
        self.suggestions: List[MaintenanceSuggestion] = []
        self.approved_suggestions: List[MaintenanceSuggestion] = []
        self.created_issues: List[IssueResult] = []
        self.errors: List[tuple] = []
        self.progress_callback = progress_callback
        self.approval_callback = approval_callback


class ProgressEvent:
    """Progress event for tracking workflow progress."""
    
    def __init__(
        self,
        stage: str,
        message: str,
        current: int = 0,
        total: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize progress event.
        
        Args:
            stage: Current workflow stage
            message: Progress message
            current: Current item number
            total: Total items
            metadata: Additional metadata
        """
        self.stage = stage
        self.message = message
        self.current = current
        self.total = total
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'stage': self.stage,
            'message': self.message,
            'current': self.current,
            'total': self.total,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class AnalysisResult:
    """Result of repository analysis workflow."""
    
    def __init__(
        self,
        session_id: str,
        username: str,
        repositories_analyzed: List[str],
        suggestions: List[MaintenanceSuggestion],
        issues_created: List[IssueResult],
        metrics: SessionMetrics,
        errors: List[tuple]
    ):
        """Initialize analysis result.
        
        Args:
            session_id: Session ID
            username: GitHub username
            repositories_analyzed: List of analyzed repository names
            suggestions: Generated maintenance suggestions
            issues_created: Created GitHub issues
            metrics: Session metrics
            errors: List of (repo_name, error) tuples
        """
        self.session_id = session_id
        self.username = username
        self.repositories_analyzed = repositories_analyzed
        self.suggestions = suggestions
        self.issues_created = issues_created
        self.metrics = metrics
        self.errors = errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'username': self.username,
            'repositories_analyzed': self.repositories_analyzed,
            'suggestions': [s.to_dict() for s in self.suggestions],
            'issues_created': [i.to_dict() for i in self.issues_created],
            'metrics': self.metrics.to_dict(),
            'errors': [(repo, str(err)) for repo, err in self.errors]
        }


class CoordinatorAgent:
    """Agent responsible for orchestrating the multi-agent workflow."""
    
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        memory_bank: Optional[MemoryBank] = None,
        github_client: Optional[GitHubClient] = None,
        analyzer_agent: Optional[AnalyzerAgent] = None,
        maintainer_agent: Optional[MaintainerAgent] = None
    ):
        """Initialize the Coordinator Agent.
        
        Args:
            session_service: Optional session service instance
            memory_bank: Optional memory bank instance
            github_client: Optional GitHub client instance
            analyzer_agent: Optional analyzer agent instance
            maintainer_agent: Optional maintainer agent instance
        """
        self.session_service = session_service or SessionService()
        self.memory_bank = memory_bank or MemoryBank()
        self.github_client = github_client or GitHubClient()
        self.analyzer_agent = analyzer_agent or AnalyzerAgent(self.github_client)
        self.maintainer_agent = maintainer_agent or MaintainerAgent(
            self.memory_bank,
            self.github_client
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("Coordinator Agent initialized")
    
    def _build_workflow(self) -> List[Callable]:
        """Build the workflow pipeline for repository analysis.
        
        Returns:
            List of workflow step functions in execution order
        """
        # Define workflow steps in order
        return [
            self._initialize_session_node,
            self._fetch_repositories_node,
            self._analyze_repositories_node,
            self._generate_suggestions_node,
            self._request_approvals_node,
            self._create_issues_node,
            self._finalize_session_node
        ]
    
    def analyze_repositories(
        self,
        username: str,
        filters: Optional[RepositoryFilters] = None,
        user_preferences: Optional[UserPreferences] = None,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
        approval_callback: Optional[Callable[[List[MaintenanceSuggestion]], List[MaintenanceSuggestion]]] = None
    ) -> AnalysisResult:
        """Main entry point for repository analysis workflow.
        
        Args:
            username: GitHub username to analyze
            filters: Optional repository filters
            user_preferences: Optional user preferences
            progress_callback: Optional callback for progress updates
            approval_callback: Optional callback for suggestion approvals
            
        Returns:
            AnalysisResult with complete analysis results
        """
        metrics = get_metrics_collector()
        metrics.start_session()
        
        logger.info(
            f"Starting repository analysis for user: {username}",
            extra={
                'agent': 'CoordinatorAgent',
                'event': 'workflow_start',
                'extra_data': {
                    'username': username,
                    'has_filters': filters is not None,
                    'has_preferences': user_preferences is not None
                }
            }
        )
        
        # Load user preferences from memory if not provided
        if user_preferences is None:
            user_preferences = self.memory_bank.load_user_preferences(username)
            if user_preferences is None:
                # Create default preferences
                user_preferences = UserPreferences(user_id=username)
        
        # Initialize workflow state
        state = WorkflowState(
            username=username,
            filters=filters,
            user_preferences=user_preferences,
            progress_callback=progress_callback,
            approval_callback=approval_callback
        )
        
        # Execute workflow steps sequentially
        try:
            for step in self.workflow:
                logger.debug(
                    f"Executing workflow step: {step.__name__}",
                    extra={
                        'agent': 'CoordinatorAgent',
                        'event': 'workflow_step',
                        'extra_data': {'step': step.__name__}
                    }
                )
                state = step(state)
            
            # Get session
            session = self.session_service.get_session(state.session_id)
            
            # Build result
            result = AnalysisResult(
                session_id=state.session_id,
                username=username,
                repositories_analyzed=[r.full_name for r in state.repositories],
                suggestions=state.suggestions,
                issues_created=state.created_issues,
                metrics=session.metrics if session else SessionMetrics(),
                errors=state.errors
            )
            
            # Get metrics summary
            metrics_summary = metrics.get_session_summary()
            
            logger.info(
                f"Analysis complete: {len(result.repositories_analyzed)} repos, "
                f"{len(result.suggestions)} suggestions, "
                f"{len(result.issues_created)} issues created",
                extra={
                    'agent': 'CoordinatorAgent',
                    'event': 'workflow_complete',
                    'metrics': metrics_summary
                }
            )
            
            return result
            
        except Exception as e:
            metrics.record_error('workflow_error')
            logger.error(
                f"Workflow execution failed: {e}",
                extra={
                    'agent': 'CoordinatorAgent',
                    'event': 'workflow_error',
                    'extra_data': {'error': str(e)}
                },
                exc_info=True
            )
            raise
    
    def _initialize_session_node(self, state: WorkflowState) -> WorkflowState:
        """Initialize session and load preferences.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Initializing session")
        
        # Emit progress event
        self._emit_progress(
            state,
            "initialization",
            f"Initializing session for user: {state.username}"
        )
        
        # Create session
        session = self.session_service.create_session(state.username)
        state.session_id = session.session_id
        
        logger.info(f"Session created: {session.session_id}")
        
        return state
    
    def _fetch_repositories_node(self, state: WorkflowState) -> WorkflowState:
        """Fetch repositories for the user.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Fetching repositories for user: {state.username}")
        
        # Emit progress event
        self._emit_progress(
            state,
            "fetching",
            f"Fetching repositories for {state.username}"
        )
        
        try:
            # Fetch repositories
            repositories = list_repos(
                state.username,
                filters=state.filters,
                client=self.github_client
            )
            
            state.repositories = repositories
            
            # Update session
            session = self.session_service.get_current_session()
            if session:
                session.repositories_analyzed = [r.full_name for r in repositories]
                self.session_service.update_session(session)
            
            logger.info(f"Found {len(repositories)} repositories")
            
        except GitHubAPIError as e:
            logger.error(f"Failed to fetch repositories: {e}")
            state.errors.append(('fetch_repositories', e))
            state.repositories = []
        
        return state
    
    def _analyze_repositories_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze repositories using Analyzer Agent with parallel processing.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        repositories = state.repositories
        
        if not repositories:
            logger.warning("No repositories to analyze")
            return state
        
        logger.info(f"Analyzing {len(repositories)} repositories")
        
        # Emit progress event
        self._emit_progress(
            state,
            "analyzing",
            f"Analyzing {len(repositories)} repositories",
            current=0,
            total=len(repositories)
        )
        
        # Analyze repositories in parallel
        analyses = self.analyzer_agent.analyze_repositories_parallel(repositories)
        
        # Extract profiles
        profiles = [analysis.profile for analysis in analyses]
        
        # Store profiles in memory
        for profile in profiles:
            try:
                self.memory_bank.save_repository_profile(profile)
                logger.debug(f"Saved profile for {profile.repository.full_name}")
            except Exception as e:
                logger.warning(f"Failed to save profile: {e}")
        
        state.analyses = analyses
        state.profiles = profiles
        
        # Update session metrics
        session = self.session_service.get_current_session()
        if session:
            session.metrics.repos_analyzed = len(analyses)
            self.session_service.update_session(session)
        
        # Emit progress event
        self._emit_progress(
            state,
            "analyzing",
            f"Completed analysis of {len(analyses)} repositories",
            current=len(analyses),
            total=len(repositories)
        )
        
        logger.info(f"Analysis complete: {len(analyses)} repositories analyzed")
        
        return state
    
    def _generate_suggestions_node(self, state: WorkflowState) -> WorkflowState:
        """Generate maintenance suggestions using Maintainer Agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        profiles = state.profiles
        
        if not profiles:
            logger.warning("No profiles to generate suggestions from")
            return state
        
        logger.info(f"Generating suggestions for {len(profiles)} repositories")
        
        # Emit progress event
        self._emit_progress(
            state,
            "generating_suggestions",
            f"Generating maintenance suggestions"
        )
        
        # Generate suggestions
        suggestions = self.maintainer_agent.generate_suggestions(
            profiles,
            state.user_preferences
        )
        
        state.suggestions = suggestions
        
        # Update session
        session = self.session_service.get_current_session()
        if session:
            session.suggestions_generated = suggestions
            session.metrics.suggestions_generated = len(suggestions)
            self.session_service.update_session(session)
        
        logger.info(f"Generated {len(suggestions)} suggestions")
        
        return state
    
    def _request_approvals_node(self, state: WorkflowState) -> WorkflowState:
        """Request user approval for suggestions.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        suggestions = state.suggestions
        
        if not suggestions:
            logger.info("No suggestions to approve")
            state.approved_suggestions = []
            return state
        
        logger.info(f"Requesting approval for {len(suggestions)} suggestions")
        
        # Emit progress event
        self._emit_progress(
            state,
            "requesting_approvals",
            f"Requesting approval for {len(suggestions)} suggestions"
        )
        
        # Check automation level
        automation_level = state.user_preferences.automation_level if state.user_preferences else "manual"
        
        if automation_level == "auto":
            # Auto-approve all suggestions
            approved = suggestions
            logger.info("Auto-approving all suggestions")
        elif automation_level == "manual" or automation_level == "ask":
            # Use approval callback if provided
            if state.approval_callback:
                approved = state.approval_callback(suggestions)
                logger.info(f"User approved {len(approved)} suggestions")
            else:
                # No callback provided, default to approving all
                approved = suggestions
                logger.warning("No approval callback provided, approving all suggestions")
        else:
            # Unknown automation level, default to manual
            approved = suggestions
            logger.warning(f"Unknown automation level: {automation_level}, approving all")
        
        state.approved_suggestions = approved
        
        logger.info(f"Approved {len(approved)} suggestions")
        
        return state
    
    def _create_issues_node(self, state: WorkflowState) -> WorkflowState:
        """Create GitHub issues for approved suggestions.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        approved_suggestions = state.approved_suggestions
        
        if not approved_suggestions:
            logger.info("No approved suggestions to create issues for")
            state.created_issues = []
            return state
        
        logger.info(f"Creating issues for {len(approved_suggestions)} suggestions")
        
        # Emit progress event
        self._emit_progress(
            state,
            "creating_issues",
            f"Creating GitHub issues",
            current=0,
            total=len(approved_suggestions)
        )
        
        created_issues = []
        
        for i, suggestion in enumerate(approved_suggestions):
            try:
                # Create issue
                result = self.maintainer_agent.create_github_issue(
                    suggestion,
                    state.user_preferences
                )
                
                created_issues.append(result)
                
                # Emit progress event
                self._emit_progress(
                    state,
                    "creating_issues",
                    f"Created issue for: {suggestion.title}",
                    current=i + 1,
                    total=len(approved_suggestions),
                    metadata={'issue_url': result.issue_url if result.success else None}
                )
                
                logger.info(
                    f"Created issue for {suggestion.repository.full_name}: "
                    f"{result.issue_url if result.success else 'FAILED'}"
                )
                
            except Exception as e:
                logger.error(f"Failed to create issue for {suggestion.title}: {e}")
                state.errors.append((suggestion.repository.full_name, e))
        
        state.created_issues = created_issues
        
        # Update session
        session = self.session_service.get_current_session()
        if session:
            session.issues_created = created_issues
            session.metrics.issues_created = len([i for i in created_issues if i.success])
            self.session_service.update_session(session)
        
        successful_issues = len([i for i in created_issues if i.success])
        logger.info(f"Created {successful_issues} issues successfully")
        
        return state
    
    def _finalize_session_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize session and calculate metrics.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info("Finalizing session")
        
        # Emit progress event
        self._emit_progress(
            state,
            "finalizing",
            "Finalizing session and calculating metrics"
        )
        
        # Get session
        session = self.session_service.get_current_session()
        
        if session:
            # Calculate execution time
            execution_time = (datetime.now() - session.start_time).total_seconds()
            session.metrics.execution_time_seconds = execution_time
            
            # Count errors
            session.metrics.errors_encountered = len(state.errors)
            
            # Update session
            self.session_service.update_session(session)
            
            logger.info(
                f"Session finalized: {session.metrics.repos_analyzed} repos analyzed, "
                f"{session.metrics.suggestions_generated} suggestions generated, "
                f"{session.metrics.issues_created} issues created, "
                f"{session.metrics.errors_encountered} errors, "
                f"{execution_time:.2f}s execution time"
            )
        
        # Emit final progress event
        self._emit_progress(
            state,
            "complete",
            "Analysis complete"
        )
        
        return state
    
    def _emit_progress(
        self,
        state: WorkflowState,
        stage: str,
        message: str,
        current: int = 0,
        total: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a progress event.
        
        Args:
            state: Current workflow state
            stage: Current workflow stage
            message: Progress message
            current: Current item number
            total: Total items
            metadata: Additional metadata
        """
        if state.progress_callback:
            event = ProgressEvent(stage, message, current, total, metadata)
            try:
                state.progress_callback(event)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        # Also log the progress
        if total > 0:
            logger.info(f"[{stage}] {message} ({current}/{total})")
        else:
            logger.info(f"[{stage}] {message}")
    
    def get_session_state(self, session_id: Optional[str] = None) -> Optional[SessionState]:
        """Retrieve session state.
        
        Args:
            session_id: Optional session ID (uses current session if not provided)
            
        Returns:
            SessionState if found, None otherwise
        """
        if session_id:
            return self.session_service.get_session(session_id)
        else:
            return self.session_service.get_current_session()
    
    def handle_user_approval(
        self,
        suggestions: List[MaintenanceSuggestion]
    ) -> List[MaintenanceSuggestion]:
        """Process user approval/rejection of suggestions.
        
        This is a default implementation that approves all suggestions.
        Override or provide a custom approval_callback for interactive approval.
        
        Args:
            suggestions: List of suggestions to approve
            
        Returns:
            List of approved suggestions
        """
        logger.info(f"Default approval handler: approving all {len(suggestions)} suggestions")
        return suggestions
