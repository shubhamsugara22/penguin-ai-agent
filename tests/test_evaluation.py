"""Tests for the evaluation framework."""

import pytest
from datetime import datetime

from src.models.repository import Repository
from src.models.health import HealthSnapshot, RepositoryProfile
from src.models.maintenance import MaintenanceSuggestion
from evaluation.test_dataset import (
    get_test_repositories,
    get_test_repository,
    ExpectedSuggestion,
    TestRepository
)
from evaluation.evaluators import (
    SuggestionQualityEvaluator,
    DeduplicationEvaluator,
    AnalysisCompletenessEvaluator
)


class TestTestDataset:
    """Tests for test dataset."""
    
    def test_get_test_repositories(self):
        """Test getting test repositories."""
        repos = get_test_repositories()
        assert len(repos) > 0
        assert all(isinstance(r, TestRepository) for r in repos)
    
    def test_get_test_repository(self):
        """Test getting specific test repository."""
        repo = get_test_repository("octocat/Hello-World")
        assert repo.full_name == "octocat/Hello-World"
        assert isinstance(repo, TestRepository)
    
    def test_get_test_repository_not_found(self):
        """Test getting non-existent repository."""
        with pytest.raises(ValueError):
            get_test_repository("nonexistent/repo")
    
    def test_expected_suggestion_matches(self):
        """Test expected suggestion matching."""
        expected = ExpectedSuggestion(
            category='documentation',
            title_keywords=['README', 'documentation'],
            description_keywords=['improve', 'documentation'],
            priority='medium'
        )
        
        # Create matching suggestion
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        suggestion = MaintenanceSuggestion(
            id='test-1',
            repository=repo,
            category='documentation',
            priority='medium',
            title='Improve README documentation',
            description='Add more details to improve the documentation',
            rationale='Better docs help users',
            estimated_effort='small',
            labels=['documentation']
        )
        
        assert expected.matches(suggestion)
    
    def test_expected_suggestion_no_match(self):
        """Test expected suggestion not matching."""
        expected = ExpectedSuggestion(
            category='documentation',
            title_keywords=['README'],
            description_keywords=['improve'],
            priority='medium'
        )
        
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Wrong category
        suggestion = MaintenanceSuggestion(
            id='test-1',
            repository=repo,
            category='bug',
            priority='medium',
            title='Improve README documentation',
            description='Add more details to improve the documentation',
            rationale='Better docs help users',
            estimated_effort='small',
            labels=['documentation']
        )
        
        assert not expected.matches(suggestion)


class TestDeduplicationEvaluator:
    """Tests for deduplication evaluator."""
    
    def test_no_duplicates(self):
        """Test evaluation with no duplicates."""
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        suggestions1 = [
            MaintenanceSuggestion(
                id='1',
                repository=repo,
                category='documentation',
                priority='medium',
                title='Add README',
                description='Create README file',
                rationale='Docs are important',
                estimated_effort='small',
                labels=['documentation']
            )
        ]
        
        suggestions2 = [
            MaintenanceSuggestion(
                id='2',
                repository=repo,
                category='enhancement',
                priority='high',
                title='Add tests',
                description='Create test suite',
                rationale='Tests are important',
                estimated_effort='large',
                labels=['testing']
            )
        ]
        
        evaluator = DeduplicationEvaluator()
        result = evaluator.evaluate(suggestions1, suggestions2, repo_changed=False)
        
        assert result.score == 1.0
        assert result.passed
        assert result.details['duplicate_count'] == 0
    
    def test_with_duplicates(self):
        """Test evaluation with duplicates."""
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        suggestions1 = [
            MaintenanceSuggestion(
                id='1',
                repository=repo,
                category='documentation',
                priority='medium',
                title='Add README',
                description='Create README file',
                rationale='Docs are important',
                estimated_effort='small',
                labels=['documentation']
            )
        ]
        
        suggestions2 = [
            MaintenanceSuggestion(
                id='2',
                repository=repo,
                category='documentation',
                priority='medium',
                title='Add README',  # Same title
                description='Create README file',
                rationale='Docs are important',
                estimated_effort='small',
                labels=['documentation']
            )
        ]
        
        evaluator = DeduplicationEvaluator()
        result = evaluator.evaluate(suggestions1, suggestions2, repo_changed=False)
        
        assert result.score < 1.0
        assert result.details['duplicate_count'] == 1
    
    def test_repo_changed(self):
        """Test evaluation when repository changed."""
        evaluator = DeduplicationEvaluator()
        result = evaluator.evaluate([], [], repo_changed=True)
        
        assert result.score == 1.0
        assert result.passed


class TestAnalysisCompletenessEvaluator:
    """Tests for analysis completeness evaluator."""
    
    def test_complete_analysis(self):
        """Test evaluation with complete analysis."""
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        health = HealthSnapshot(
            activity_level='active',
            test_coverage='good',
            documentation_quality='excellent',
            ci_cd_status='configured',
            dependency_status='current',
            overall_health_score=0.9,
            issues_identified=[]
        )
        
        profile = RepositoryProfile(
            repository=repo,
            purpose='A test repository',
            tech_stack=['Python'],
            key_files=['README.md', 'setup.py'],
            health=health,
            last_analyzed=datetime.now(),
            analysis_version='1.0.0'
        )
        
        test_repo = TestRepository(
            full_name='test/test',
            description='Test repository',
            characteristics={},
            expected_suggestions=[],
            expected_health_score_range=(0.8, 1.0),
            expected_activity_level='active'
        )
        
        evaluator = AnalysisCompletenessEvaluator()
        result = evaluator.evaluate(profile, test_repo)
        
        assert result.score > 0.8
        assert result.passed
        assert result.details['health_score_in_range']
        assert result.details['activity_level_correct']
    
    def test_incomplete_analysis(self):
        """Test evaluation with incomplete analysis."""
        repo = Repository(
            name='test',
            full_name='test/test',
            owner='test',
            url='https://github.com/test/test',
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        health = HealthSnapshot(
            activity_level='stale',  # Wrong activity level
            test_coverage='good',
            documentation_quality='excellent',
            ci_cd_status='configured',
            dependency_status='current',
            overall_health_score=0.5,  # Out of range
            issues_identified=[]
        )
        
        profile = RepositoryProfile(
            repository=repo,
            purpose='',  # Empty purpose
            tech_stack=[],  # Empty tech stack
            key_files=[],  # Empty key files
            health=health,
            last_analyzed=datetime.now(),
            analysis_version='1.0.0'
        )
        
        test_repo = TestRepository(
            full_name='test/test',
            description='Test repository',
            characteristics={},
            expected_suggestions=[],
            expected_health_score_range=(0.8, 1.0),
            expected_activity_level='active'
        )
        
        evaluator = AnalysisCompletenessEvaluator()
        result = evaluator.evaluate(profile, test_repo)
        
        assert result.score < 0.8
        assert not result.passed
        assert not result.details['health_score_in_range']
        assert not result.details['activity_level_correct']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
