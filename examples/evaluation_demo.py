#!/usr/bin/env python3
"""Demo script for the evaluation framework.

This script demonstrates how to use the evaluation framework
to assess agent performance.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.test_dataset import get_test_repositories
from evaluation.evaluators import (
    DeduplicationEvaluator,
    AnalysisCompletenessEvaluator
)
from src.models.repository import Repository
from src.models.health import HealthSnapshot, RepositoryProfile
from src.models.maintenance import MaintenanceSuggestion
from datetime import datetime


def demo_test_dataset():
    """Demonstrate test dataset functionality."""
    print("=" * 80)
    print("TEST DATASET DEMO")
    print("=" * 80)
    
    repos = get_test_repositories()
    print(f"\nFound {len(repos)} test repositories:\n")
    
    for repo in repos:
        print(f"Repository: {repo.full_name}")
        print(f"  Description: {repo.description}")
        print(f"  Expected Health Score: {repo.expected_health_score_range}")
        print(f"  Expected Activity: {repo.expected_activity_level}")
        print(f"  Expected Suggestions: {len(repo.expected_suggestions)}")
        print()


def demo_deduplication_evaluator():
    """Demonstrate deduplication evaluator."""
    print("=" * 80)
    print("DEDUPLICATION EVALUATOR DEMO")
    print("=" * 80)
    
    # Create test repository
    repo = Repository(
        name='test-repo',
        full_name='test/test-repo',
        owner='test',
        url='https://github.com/test/test-repo',
        default_branch='main',
        visibility='public',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create suggestions for first run
    suggestions_run1 = [
        MaintenanceSuggestion(
            id='1',
            repository=repo,
            category='documentation',
            priority='medium',
            title='Add comprehensive README',
            description='Create detailed README with examples',
            rationale='Good documentation improves adoption',
            estimated_effort='medium',
            labels=['documentation', 'good-first-issue']
        ),
        MaintenanceSuggestion(
            id='2',
            repository=repo,
            category='enhancement',
            priority='high',
            title='Add test suite',
            description='Create comprehensive test coverage',
            rationale='Tests ensure code quality',
            estimated_effort='large',
            labels=['testing', 'enhancement']
        )
    ]
    
    # Create suggestions for second run (with one duplicate)
    suggestions_run2 = [
        MaintenanceSuggestion(
            id='3',
            repository=repo,
            category='documentation',
            priority='medium',
            title='Add comprehensive README',  # Duplicate!
            description='Create detailed README with examples',
            rationale='Good documentation improves adoption',
            estimated_effort='medium',
            labels=['documentation', 'good-first-issue']
        ),
        MaintenanceSuggestion(
            id='4',
            repository=repo,
            category='enhancement',
            priority='medium',
            title='Set up CI/CD pipeline',
            description='Configure GitHub Actions',
            rationale='Automated testing catches bugs early',
            estimated_effort='medium',
            labels=['ci-cd', 'automation']
        )
    ]
    
    # Evaluate deduplication
    evaluator = DeduplicationEvaluator()
    result = evaluator.evaluate(suggestions_run1, suggestions_run2, repo_changed=False)
    
    print(f"\nRun 1 Suggestions: {len(suggestions_run1)}")
    for s in suggestions_run1:
        print(f"  - {s.title}")
    
    print(f"\nRun 2 Suggestions: {len(suggestions_run2)}")
    for s in suggestions_run2:
        print(f"  - {s.title}")
    
    print(f"\nDeduplication Results:")
    print(f"  Score: {result.score:.2f}")
    print(f"  Passed: {result.passed}")
    print(f"  Duplicates Found: {result.details['duplicate_count']}")
    if result.details['duplicate_titles']:
        print(f"  Duplicate Titles: {', '.join(result.details['duplicate_titles'])}")
    print()


def demo_completeness_evaluator():
    """Demonstrate analysis completeness evaluator."""
    print("=" * 80)
    print("ANALYSIS COMPLETENESS EVALUATOR DEMO")
    print("=" * 80)
    
    # Create test repository
    repo = Repository(
        name='test-repo',
        full_name='test/test-repo',
        owner='test',
        url='https://github.com/test/test-repo',
        default_branch='main',
        visibility='public',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create health snapshot
    health = HealthSnapshot(
        activity_level='active',
        test_coverage='good',
        documentation_quality='excellent',
        ci_cd_status='configured',
        dependency_status='current',
        overall_health_score=0.92,
        issues_identified=[]
    )
    
    # Create repository profile
    profile = RepositoryProfile(
        repository=repo,
        purpose='A well-maintained test repository for demonstrating evaluation',
        tech_stack=['Python', 'JavaScript'],
        key_files=['README.md', 'setup.py', 'package.json', '.github/workflows/ci.yml'],
        health=health,
        last_analyzed=datetime.now(),
        analysis_version='1.0.0'
    )
    
    # Get test repository from dataset
    from evaluation.test_dataset import TestRepository
    test_repo = TestRepository(
        full_name='test/test-repo',
        description='Test repository',
        characteristics={},
        expected_suggestions=[],
        expected_health_score_range=(0.8, 1.0),
        expected_activity_level='active'
    )
    
    # Evaluate completeness
    evaluator = AnalysisCompletenessEvaluator()
    result = evaluator.evaluate(profile, test_repo)
    
    print(f"\nRepository Profile:")
    print(f"  Purpose: {profile.purpose}")
    print(f"  Tech Stack: {', '.join(profile.tech_stack)}")
    print(f"  Key Files: {len(profile.key_files)}")
    print(f"  Health Score: {profile.health.overall_health_score:.2f}")
    print(f"  Activity Level: {profile.health.activity_level}")
    
    print(f"\nCompleteness Results:")
    print(f"  Score: {result.score:.2f}")
    print(f"  Passed: {result.passed}")
    print(f"  Present Fields: {result.details['present_fields']}/{result.details['total_fields']}")
    print(f"  Health Score in Range: {result.details['health_score_in_range']}")
    print(f"  Activity Level Correct: {result.details['activity_level_correct']}")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("*" * 80)
    print("EVALUATION FRAMEWORK DEMO")
    print("*" * 80)
    print("\n")
    
    demo_test_dataset()
    demo_deduplication_evaluator()
    demo_completeness_evaluator()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nTo run the full evaluation suite:")
    print("  python run_evaluation.py")
    print("\nFor more information, see evaluation/README.md")
    print()


if __name__ == '__main__':
    main()
