# Evaluation Framework Documentation

## Overview

The evaluation framework provides comprehensive assessment of the GitHub Maintainer Agent's performance across three key dimensions:

1. **Suggestion Quality**: Evaluates the relevance, actionability, and impact of generated maintenance suggestions using LLM-as-judge
2. **Analysis Completeness**: Verifies that repository analysis includes all required fields and produces accurate health assessments
3. **Deduplication Accuracy**: Tests the agent's ability to avoid generating duplicate suggestions across multiple runs

## Quick Start

### Running the Evaluation Suite

```bash
# Run complete evaluation on all test repositories
python run_evaluation.py

# Run evaluation on specific repositories
python run_evaluation.py --repos octocat/Hello-World torvalds/linux

# Skip deduplication test (faster)
python run_evaluation.py --skip-deduplication

# Specify output directory
python run_evaluation.py --output-dir my_results

# Set log level
python run_evaluation.py --log-level DEBUG
```

### Running the Demo

```bash
# See evaluation framework in action
python examples/evaluation_demo.py
```

## Architecture

### Test Dataset

The evaluation framework uses a curated set of well-known GitHub repositories with documented characteristics:

- **octocat/Hello-World**: Classic GitHub test repository
- **torvalds/linux**: Linux kernel (highly active)
- **rails/rails**: Ruby on Rails framework
- **python/cpython**: Python implementation
- **microsoft/vscode**: Visual Studio Code

Each test repository includes:
- Expected health score range
- Expected activity level
- Expected suggestions (if any)
- Known characteristics (tests, CI/CD, documentation)

### Evaluators

#### SuggestionQualityEvaluator

Uses Gemini LLM as a judge to evaluate each suggestion on:
- **Relevance**: Is it relevant to the repository's health issues?
- **Actionability**: Is it specific and actionable?
- **Impact**: Would it meaningfully improve the repository?
- **Appropriateness**: Is the priority and effort estimate reasonable?
- **Clarity**: Is the description clear and helpful?

**Scoring**:
- LLM Quality Score (70%): Average score from LLM-as-judge
- Expected Match Score (30%): Percentage of expected suggestions generated
- **Pass Threshold**: 0.7

#### AnalysisCompletenessEvaluator

Verifies that repository analysis is complete and accurate:
- **Field Completeness (60%)**: All required fields present
- **Health Score Accuracy (20%)**: Health score in expected range
- **Activity Level Accuracy (20%)**: Activity level matches expectations

**Pass Threshold**: 0.8

#### DeduplicationEvaluator

Tests deduplication by running analysis twice:
- Counts duplicate suggestions (by title)
- Calculates accuracy: `1.0 - (duplicates / total_suggestions)`
- **Pass Threshold**: 0.9 (< 10% duplicates)

### Evaluation Runner

The `EvaluationRunner` orchestrates the evaluation process:

1. Loads test repositories
2. For each repository:
   - Runs analysis using AnalyzerAgent
   - Generates suggestions using MaintainerAgent
   - Evaluates completeness
   - Evaluates suggestion quality
   - Optionally tests deduplication
3. Aggregates results
4. Generates reports

## Output

### Text Report

Human-readable report with:
- Overall statistics
- Average scores for each metric
- Per-repository results
- Pass/fail status

Example:
```
================================================================================
EVALUATION REPORT
================================================================================
Timestamp: 2024-11-29T10:30:00
Total Repositories: 5
Successful Evaluations: 5
Failed Evaluations: 0
Total Execution Time: 45.23s

AVERAGE SCORES
--------------------------------------------------------------------------------
Suggestion Quality: 0.85 / 1.00
Analysis Completeness: 0.92 / 1.00
Deduplication Accuracy: 0.95 / 1.00
```

### JSON Results

Machine-readable results with detailed metrics for programmatic analysis and tracking over time.

## Programmatic Usage

```python
from evaluation.runner import EvaluationRunner
from evaluation.test_dataset import get_test_repositories

# Create runner
runner = EvaluationRunner()

# Run evaluation
summary = runner.run_evaluation()

# Access results
print(f"Average Quality Score: {summary.average_quality_score:.2f}")
print(f"Successful Evaluations: {summary.successful_evaluations}")

# Generate report
report = runner.generate_report(summary, 'report.txt')

# Save JSON results
runner.save_results_json(summary, 'results.json')
```

## Adding Test Repositories

To add a new test repository, edit `evaluation/test_dataset.py`:

```python
TestRepository(
    full_name="owner/repo",
    description="Description of the repository",
    characteristics={
        'has_tests': True,
        'has_ci': True,
        'has_readme': True,
        'has_contributing': False,
        'activity_level': 'active',
        'languages': ['Python'],
        'last_commit_days_ago': 5
    },
    expected_suggestions=[
        ExpectedSuggestion(
            category='documentation',
            title_keywords=['CONTRIBUTING'],
            description_keywords=['contribution', 'guidelines'],
            priority='medium'
        )
    ],
    expected_health_score_range=(0.7, 0.9),
    expected_activity_level='active'
)
```

## CI/CD Integration

Integrate evaluation into your CI/CD pipeline:

```yaml
# .github/workflows/evaluation.yml
name: Agent Evaluation

on:
  push:
    branches: [main]
  pull_request:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run evaluation
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: python run_evaluation.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: evaluation_results/
```

## Troubleshooting

### API Rate Limits

If you encounter GitHub API rate limits:
- Use a personal access token with higher rate limits
- Reduce the number of test repositories
- Add delays between evaluations

### LLM Evaluation Failures

If LLM-as-judge evaluations fail:
- Check your Gemini API key
- Verify API quota
- Review logs for specific error messages
- The system will fall back to basic scoring (0.5) if LLM fails

### Memory Issues

For large-scale evaluations:
- Run evaluations in batches
- Use `--repos` to evaluate specific repositories
- Increase system memory allocation

## Best Practices

1. **Run Regularly**: Run evaluations after significant changes to agent logic
2. **Track Over Time**: Save JSON results to track performance trends
3. **Set Baselines**: Establish baseline scores for your agent
4. **Investigate Failures**: When scores drop, investigate specific failures
5. **Update Test Data**: Keep test repositories current and relevant
6. **Document Changes**: Document why scores change after modifications

## Metrics Interpretation

### Suggestion Quality Score

- **0.9-1.0**: Excellent - Suggestions are highly relevant and actionable
- **0.7-0.9**: Good - Suggestions are generally useful with minor issues
- **0.5-0.7**: Fair - Suggestions need improvement
- **< 0.5**: Poor - Significant issues with suggestion generation

### Analysis Completeness Score

- **0.9-1.0**: Excellent - Complete and accurate analysis
- **0.8-0.9**: Good - Minor gaps in analysis
- **0.6-0.8**: Fair - Some important fields missing
- **< 0.6**: Poor - Significant gaps in analysis

### Deduplication Accuracy Score

- **0.95-1.0**: Excellent - Minimal or no duplicates
- **0.9-0.95**: Good - Few duplicates
- **0.8-0.9**: Fair - Some duplicates present
- **< 0.8**: Poor - Too many duplicates

## Future Enhancements

Potential improvements to the evaluation framework:

1. **Benchmark Dataset**: Larger, more diverse set of test repositories
2. **Human Evaluation**: Collect human judgments for comparison
3. **Regression Testing**: Automated detection of performance regressions
4. **A/B Testing**: Compare different agent configurations
5. **Cost Tracking**: Monitor API costs during evaluation
6. **Performance Profiling**: Identify bottlenecks in agent execution
7. **Multi-Language Support**: Test repositories in various programming languages
8. **Edge Case Testing**: Specific tests for error conditions and edge cases
