# Evaluation Framework

This directory contains the evaluation framework for the GitHub Maintainer Agent. The framework provides comprehensive evaluation of agent performance across multiple dimensions.

## Overview

The evaluation framework assesses three key aspects of agent performance:

1. **Suggestion Quality**: Uses LLM-as-judge to evaluate the relevance, actionability, and impact of generated maintenance suggestions
2. **Analysis Completeness**: Verifies that repository analysis includes all required fields and produces accurate health assessments
3. **Deduplication Accuracy**: Tests the agent's ability to avoid generating duplicate suggestions across multiple runs

## Components

### Test Dataset (`test_dataset.py`)

Defines a curated set of test repositories with known characteristics:

- **octocat/Hello-World**: Classic GitHub test repository
- **torvalds/linux**: Linux kernel (highly active, well-maintained)
- **rails/rails**: Ruby on Rails framework
- **python/cpython**: Python implementation
- **microsoft/vscode**: Visual Studio Code

Each test repository includes:
- Expected health score range
- Expected activity level
- Expected suggestions (if any)
- Known characteristics (tests, CI/CD, documentation, etc.)

### Evaluators (`evaluators.py`)

Three specialized evaluators:

#### SuggestionQualityEvaluator
- Uses Gemini LLM as a judge to score suggestions (0.0 to 1.0)
- Evaluates relevance, actionability, impact, appropriateness, and clarity
- Checks if generated suggestions match expected suggestions
- Pass threshold: 0.7

#### DeduplicationEvaluator
- Runs analysis twice on the same repository
- Counts duplicate suggestions (by title)
- Calculates deduplication accuracy
- Pass threshold: 0.9 (< 10% duplicates)

#### AnalysisCompletenessEvaluator
- Verifies all required fields are present in repository profile
- Checks health snapshot completeness
- Validates health score is in expected range
- Validates activity level matches expectations
- Pass threshold: 0.8

### Evaluation Runner (`runner.py`)

Orchestrates the evaluation process:

1. Loads test repositories
2. Runs analysis on each repository
3. Generates suggestions
4. Executes all evaluators
5. Aggregates results
6. Generates reports

## Usage

### Run Complete Evaluation Suite

```bash
python run_evaluation.py
```

This will:
- Evaluate all test repositories
- Run all evaluators
- Generate text and JSON reports in `evaluation_results/`

### Run with Options

```bash
# Specify output directory
python run_evaluation.py --output-dir my_results

# Skip deduplication test (faster)
python run_evaluation.py --skip-deduplication

# Evaluate specific repositories only
python run_evaluation.py --repos octocat/Hello-World torvalds/linux

# Set log level
python run_evaluation.py --log-level DEBUG
```

### Programmatic Usage

```python
from evaluation.runner import EvaluationRunner
from evaluation.test_dataset import get_test_repositories

# Create runner
runner = EvaluationRunner()

# Run evaluation
summary = runner.run_evaluation()

# Generate report
report = runner.generate_report(summary, 'report.txt')
print(report)

# Save JSON results
runner.save_results_json(summary, 'results.json')
```

## Output

### Text Report (`evaluation_report.txt`)

Human-readable report with:
- Overall statistics
- Average scores for each metric
- Per-repository results
- Pass/fail status for each evaluation

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

REPOSITORY RESULTS
--------------------------------------------------------------------------------

Repository: octocat/Hello-World
  Execution Time: 8.45s
  Suggestions Generated: 2
  Quality Score: 0.82 [PASS]
  Completeness Score: 0.90 [PASS]
  Deduplication Score: 1.00 [PASS]
...
```

### JSON Results (`evaluation_results.json`)

Machine-readable results with detailed metrics:

```json
{
  "total_repositories": 5,
  "successful_evaluations": 5,
  "failed_evaluations": 0,
  "average_quality_score": 0.85,
  "average_completeness_score": 0.92,
  "average_deduplication_score": 0.95,
  "total_execution_time_seconds": 45.23,
  "timestamp": "2024-11-29T10:30:00",
  "repository_results": [...]
}
```

## Evaluation Metrics

### Suggestion Quality Score

Combines two components:
- **LLM Quality Score (70%)**: Average score from LLM-as-judge for each suggestion
- **Expected Match Score (30%)**: Percentage of expected suggestions that were generated

**Pass Threshold**: 0.7

### Analysis Completeness Score

Combines three components:
- **Field Completeness (60%)**: Percentage of required fields present
- **Health Score Accuracy (20%)**: Whether health score is in expected range
- **Activity Level Accuracy (20%)**: Whether activity level matches expectations

**Pass Threshold**: 0.8

### Deduplication Accuracy Score

Calculated as: `1.0 - (duplicates / total_suggestions)`

**Pass Threshold**: 0.9 (< 10% duplicates)

## Adding New Test Repositories

To add a new test repository, edit `test_dataset.py`:

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

## Continuous Evaluation

The evaluation framework can be integrated into CI/CD pipelines:

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

## Future Enhancements

Potential improvements to the evaluation framework:

1. **Benchmark Dataset**: Create a larger, more diverse set of test repositories
2. **Human Evaluation**: Collect human judgments for comparison with LLM-as-judge
3. **Regression Testing**: Track scores over time to detect performance regressions
4. **A/B Testing**: Compare different agent configurations
5. **Cost Tracking**: Monitor API costs during evaluation
6. **Performance Profiling**: Identify bottlenecks in agent execution
