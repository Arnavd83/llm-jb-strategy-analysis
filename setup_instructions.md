# PAIR Framework Setup Instructions

## Prerequisites

1. **Python 3.10 or 3.11** (required by the project)
2. **UV package manager** (recommended) or pip

## Installation Steps

### Option 1: Using UV (Recommended)

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Option 2: Using pip

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: If requirements.txt doesn't exist, install directly from pyproject.toml:
```bash
pip install -e .
```

## Setting Up API Keys

1. Copy the environment template:
```bash
cp env.template .env
```

2. Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_actual_key_here
ANTHROPIC_API_KEY=your_actual_key_here
TOGETHER_API_KEY=your_actual_key_here
GOOGLE_API_KEY=your_actual_key_here
```

## Verifying Installation

Run the test script:
```bash
python test_pair.py
```

All tests should pass if everything is set up correctly.

## Running Your First Experiment

Quick test with limited scope:
```bash
python run_pair.py data/forbidden_questions.csv \
  --strategies role_play encoding \
  --max-questions-per-category 2 \
  --max-iterations 5
```

## Troubleshooting

### Missing Dependencies
If you get import errors, ensure you've activated the virtual environment and installed all dependencies.

### API Key Errors
- Make sure your `.env` file exists and contains valid API keys
- Verify keys are exported: `echo $OPENAI_API_KEY`
- You can also export directly: `export OPENAI_API_KEY=your_key_here`

### UV Not Found
If UV is not installed, you can install it with:
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Or use pip instead (see Option 2 above)

### Python Version Issues
This project requires Python 3.10 or 3.11. Check your version:
```bash
python3 --version
```

If you need to install a specific version:
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`
- Or use pyenv: `pyenv install 3.11.0`
