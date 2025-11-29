# Evaluation Framework Quick Start

## 5-Minute Quick Start

### 1. Run the Demo

```bash
python examples/evaluation_demo.py
```

This will show you:
- The test dataset
- How deduplication evaluation works
- How completeness evaluation works

### 2. Run Full Evaluation

```bash
python run_evaluation.py
```

This will:
- Analyze all 5 test repositories
- Generate suggestions
- Evaluate quality, completeness, and deduplication
- Create reports in `evaluation_results/`

### 3. View Results

```bash
# View text report
cat evaluation_results/evaluation_report.txt

# View JSON results
cat evaluation_results/evaluation_results.json
```

## Common Commands

```bash
# Run on specific repositories only
python run_evaluation.py --repos octocat/Hello-World torvalds/linux

# Skip deduplication test (faster)
python run_evaluation.py --skip-deduplication

# Change output directory
python run_evaluation.py --output-dir my_results

# Enable debug logging
python run_evaluation.py --log-level DEBUG
```

## Understanding the Output

### Text Report

```
AVERAGE SCORES
--------------------------------------------------------------------------------
Suggestion Quality: 0.85 / 1.00      # LLM-as-judge score
Analysis Completeness: 0.92 / 1.00   # Field completeness + accuracy
Deduplication Accuracy: 0.95 / 1.00  # 1.0 - (duplicates / total)
```

### Pass Thresholds

- **Suggestion Quality**: ≥ 0.7
- **Analysis Completeness**: ≥ 0.8
- **Deduplication Accuracy**: ≥ 0.9

### Score Interpretation

| Score | Quality | Completeness | Deduplication |
|-------|---------|--------------|---------------|
| 0.9-1.0 | Excellent | Complete | Minimal duplicates |
| 0.7-0.9 | Good | Minor gaps | Few duplicates |
| 0.5-0.7 | Fair | Some gaps | Some duplicates |
| < 0.5 | Poor | Major gaps | Many duplicates |

## Programmatic Usage

```python
from evaluation.runner import EvaluationRunner

# Create runner
runner = EvaluationRunner()

# Run evaluation
summary = runner.run_evaluation()

# Check results
print(f"Quality: {summary.average_quality_score:.2f}")
print(f"Completeness: {summary.average_completeness_score:.2f}")
print(f"Deduplication: {summary.average_deduplication_score:.2f}")

# Generate reports
runner.generate_report(summary, 'report.txt')
runner.save_results_json(summary, 'results.json')
```

## Troubleshooting

### "No module named 'evaluation'"

Make sure you're running from the `penguin-ai-agent` directory:
```bash
cd penguin-ai-agent
python run_evaluation.py
```

### API Rate Limits

If you hit GitHub API rate limits:
- Use a personal access token (set `GITHUB_TOKEN` in `.env`)
- Run on fewer repositories: `--repos octocat/Hello-World`

### LLM Evaluation Fails

If LLM-as-judge fails:
- Check your Gemini API key (set `GEMINI_API_KEY` in `.env`)
- Verify you have API quota
- The system will fall back to basic scoring (0.5)

## Next Steps

1. **Read Full Documentation**: See [README.md](README.md) for complete guide
2. **Add Test Repositories**: Edit `test_dataset.py` to add your own
3. **Integrate with CI/CD**: See [docs/EVALUATION.md](../docs/EVALUATION.md)
4. **Track Over Time**: Save JSON results to monitor trends

## Need Help?

- Full documentation: [evaluation/README.md](README.md)
- User guide: [docs/EVALUATION.md](../docs/EVALUATION.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
