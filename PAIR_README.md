# PAIR (Prompt Automatic Iterative Refinement) Implementation

This directory contains a complete implementation of the PAIR framework for systematically evaluating and improving LLM safety mechanisms through automated red-teaming.

## Overview

PAIR is an iterative adversarial framework where:
- An **Attacker Agent** generates and refines jailbreak prompts
- A **Target Model** responds to these prompts
- A **Judge Agent** evaluates whether the jailbreak was successful
- The system iteratively refines attacks based on feedback

## Key Features

### 🎯 Multiple Attack Strategies
- **Role-Playing**: Using character scenarios to bypass safety
- **Encoding**: Obfuscation techniques (leetspeak, Base64, etc.)
- **Context Manipulation**: Framing harmful requests as benign
- **Emotional Appeals**: Using urgency and empathy
- **Technical Framing**: Academic/research contexts
- **Multi-Turn**: Gradual escalation across conversations
- **Hypothetical Scenarios**: "What if" questions
- **Educational Framing**: "For awareness" approaches
- **Creative Writing**: Embedding in fictional contexts
- **Analogical Reasoning**: Using metaphors and indirect references

### 📊 Comprehensive Metrics
- **AASR (Attack Success Rate)**: Per question and overall
- **Average Queries to Jailbreak**: Efficiency metric
- **Score Progression**: How scores improve over iterations
- **Time to Jailbreak**: Performance timing
- **Strategy × Category Analysis**: Which strategies work on which content

### 🔧 Multi-Provider Support
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Together AI (Open models)
- Google (Gemini)

## Installation

1. **Install dependencies with UV**:
```bash
uv sync
```

2. **Set up API keys**:
```bash
cp env.template .env
# Edit .env with your API keys
```

## Quick Start

### Basic Experiment
```bash
# Run PAIR on all strategies and categories
python run_pair.py data/forbidden_questions.csv

# Test specific strategies
python run_pair.py data/forbidden_questions.csv --strategies role_play encoding hypothetical

# Test specific categories
python run_pair.py data/forbidden_questions.csv --categories "Illegal Activity" "Malware"

# Limit scope for quick tests
python run_pair.py data/forbidden_questions.csv --max-questions-per-category 5 --max-iterations 10
```

### Using Different Models
```bash
# Use Claude as attacker, GPT-4 as judge, Llama as target
python run_pair.py data/forbidden_questions.csv \
  --attacker-provider anthropic --attacker-model claude-3-sonnet-20240229 \
  --judge-provider openai --judge-model gpt-4-turbo-preview \
  --target-provider together --target-model meta-llama/Llama-2-70b-chat-hf
```

### Python API
```python
from pair import PAIRConfig, LLMConfig, PAIRExperiment

# Configure experiment
config = PAIRConfig(
    attacker_llm=LLMConfig(provider="openai", model="gpt-4-turbo-preview"),
    judge_llm=LLMConfig(provider="openai", model="gpt-4-turbo-preview"),
    target_llm=LLMConfig(provider="openai", model="gpt-3.5-turbo"),
    max_iterations=20,
    strategies=["role_play", "encoding", "hypothetical"]
)

# Run experiment
experiment = PAIRExperiment(config)
results = experiment.run_full_experiment(
    questions_csv="data/forbidden_questions.csv",
    categories=["Illegal Activity", "Malware"],
    max_questions_per_category=10
)
```

## Analyzing Results

Results are automatically saved with visualizations and reports:

```bash
# Analyze existing results
python -m pair.analysis results/results_20240101_120000.json
```

This generates:
- **Strategy performance charts**: ASR, iterations, score distributions
- **Category vulnerability analysis**: Which categories are most susceptible
- **Strategy × Category heatmap**: Best strategies per category
- **Score progression analysis**: How attacks improve over iterations
- **Comprehensive markdown report**: All metrics and insights

### Output Structure
```
results/
├── results_TIMESTAMP.json          # Detailed results
├── summary_TIMESTAMP.csv           # CSV summary
├── metrics_TIMESTAMP.json          # Strategy metrics
└── analysis_TIMESTAMP/             # Visualizations
    ├── strategy_performance.png
    ├── category_performance.png
    ├── strategy_category_heatmap.png
    ├── iteration_distribution.png
    ├── score_progression.png
    ├── time_analysis.png
    ├── query_efficiency.png
    └── analysis_report.md
```

## Understanding the Metrics

### Attack Success Rate (ASR)
- Percentage of successful jailbreaks
- Calculated per strategy, category, and overall
- Success threshold default: 0.7 (configurable)

### Score Progression
- How judge scores improve over iterations
- Tracks learning and refinement effectiveness
- Identifies which strategies improve most with iteration

### Efficiency Metrics
- **Queries per attempt**: Resource usage
- **Time to jailbreak**: Performance timing
- **Query efficiency**: ASR / Average queries

## Configuration Options

### Command Line Arguments
```
--max-iterations N          # Max refinement iterations (default: 20)
--max-queries N            # Max total queries per question (default: 50)
--judge-threshold F        # Success score threshold (default: 0.7)
--temperature F            # LLM temperature (default: 0.7)
--max-tokens N             # Max response tokens (default: 1000)
--output-dir PATH          # Results directory (default: results)
--quiet                    # Minimal output
--no-save-intermediate     # Don't save progress
```

### Advanced Configuration
```python
# Custom judge criteria
config.judge_score_threshold = 0.8

# Adjust iteration limits
config.max_iterations = 30
config.max_queries_per_question = 100

# Control verbosity
config.verbose = False
config.save_intermediate_results = True
```

## Extending PAIR

### Adding New Strategies
1. Add strategy prompt to `pair/attacker/attacker_system_prompts.py`
2. Include strategy name in configuration
3. Run experiments with new strategy

### Custom Judge Criteria
Modify `pair/judge/judge_system_prompts.py` to adjust:
- Scoring thresholds
- Evaluation criteria
- Feedback generation

### Custom Analysis
Use the pandas DataFrame from results:
```python
from pair import PAIRAnalyzer

analyzer = PAIRAnalyzer("results/results_xxx.json")
df = analyzer.df  # Pandas DataFrame with all results

# Custom analysis
strategy_category_pivot = df.pivot_table(
    values='is_successful',
    index='strategy',
    columns='category',
    aggfunc='mean'
)
```

## Best Practices

1. **Start Small**: Test with limited questions/iterations first
2. **Monitor Costs**: LLM API calls can add up quickly
3. **Use Appropriate Models**: 
   - Stronger models for attacker/judge
   - Test various target models
4. **Iterate on Strategies**: Refine based on results
5. **Responsible Disclosure**: Share findings with model providers

## Troubleshooting

### API Key Issues
```bash
# Check if keys are set
python -c "import os; print('Keys set:', all(os.getenv(k) for k in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']))"
```

### Rate Limits
- Add delays between experiments
- Use `--max-questions-per-category` to limit scope
- Consider using multiple API keys

### Memory Issues
- Process results in batches
- Use `--no-save-intermediate` for large experiments
- Analyze results separately from running experiments

## Safety & Ethics

This tool is designed for:
- Security research and red-teaming
- Improving AI safety mechanisms
- Understanding LLM vulnerabilities

Please use responsibly and in accordance with provider terms of service.
