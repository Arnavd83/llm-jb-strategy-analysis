"""PAIR (Prompt Automatic Iterative Refinement) framework for LLM jailbreak analysis."""

from .config import PAIRConfig, LLMConfig, get_default_config, DEFAULT_CONFIGS
from .models import (
    AttackStatus,
    AttackAttempt,
    PAIRResult,
    StrategyMetrics,
    ExperimentResults
)
from .attacker.attack import Attacker
from .judge.judge import Judge
from .target import TargetModel
from .pair_runner import PAIRRunner
from .experiment import PAIRExperiment
from .analysis import PAIRAnalyzer, analyze_results

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "PAIRConfig",
    "LLMConfig",
    "get_default_config",
    "DEFAULT_CONFIGS",
    
    # Models
    "AttackStatus",
    "AttackAttempt",
    "PAIRResult",
    "StrategyMetrics",
    "ExperimentResults",
    
    # Core components
    "Attacker",
    "Judge",
    "TargetModel",
    "PAIRRunner",
    
    # Experiment management
    "PAIRExperiment",
    
    # Analysis
    "PAIRAnalyzer",
    "analyze_results"
]
