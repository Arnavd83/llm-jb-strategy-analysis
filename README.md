# LLM Jailbreak Strategy Analysis

This project analyzes red-teaming strategies for large language models.

## Setup

1. Clone the repository
2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```
3. Install dependencies (when available):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run PAIR (script form)

```bash
uv run python pair/main.py \
  --n-streams 4 \
  --n-iterations 2 \
  --strategy authority_endorsement \
  --attack-model gpt-3.5-turbo-1106 \
  --target-model gpt-3.5-turbo-1106 \
  --judge-model gpt-3.5-turbo-1106 -v
```

### Run PAIR (module form)

All intra-package imports are package-qualified, so you can also run with `-m`:

```bash
uv run python -m pair.main \
  --n-streams 4 \
  --n-iterations 2 \
  --strategy roleplaying,logical_appeal \
  --attack-model gpt-3.5-turbo-1106 \
  --target-model gpt-3.5-turbo-1106 \
  --judge-model gpt-3.5-turbo-1106 -v
```

### Strategy selection

- `--strategy` accepts a single strategy or a comma-separated list. The attacker’s conversations rotate among the selected strategies.
- Default strategy: `authority_endorsement`.
- Valid strategies (from `pair/system_prompts_fixed.py::ATTACK_STRATEGIES`):
  - `roleplaying`
  - `logical_appeal`
  - `authority_endorsement`
- If an invalid strategy is provided or the list becomes empty after parsing, the program exits with: `unrecognizable strategy`.

### Logging (Weights & Biases)

- Run config includes selected `strategies` and `strategy_default`.
- The logged table includes a per-row `strategy` column (reflecting the exact assignment for each conversation).

### Environment variables

Ensure relevant API keys are available in the environment (or set in a `.env` file loaded via `dotenv`):

- `OPENAI_API_KEY` (for GPT models)
- `TOGETHER_API_KEY` (for certain open-source models)
- `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` as needed

### Testing

Run tests with:

```bash
uv run pytest -q
```

Note: Some tests are illustrative and may perform API calls (network-dependent). They can fail without the appropriate keys or connectivity.
