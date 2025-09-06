"""Main entry point for running PAIR experiments."""

import argparse
import os
import sys
from pathlib import Path

from .config import PAIRConfig, LLMConfig, get_default_config
from .experiment import PAIRExperiment


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run PAIR (Prompt Automatic Iterative Refinement) experiments"
    )
    
    # Required arguments
    parser.add_argument(
        "questions_csv",
        type=str,
        help="Path to CSV file containing questions (with 'prompt' and 'category' columns)"
    )
    
    # Model configuration
    parser.add_argument(
        "--attacker-provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "together", "google"],
        help="LLM provider for attacker agent"
    )
    parser.add_argument(
        "--attacker-model",
        type=str,
        default=None,
        help="Model name for attacker (defaults to provider default)"
    )
    
    parser.add_argument(
        "--judge-provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "together", "google"],
        help="LLM provider for judge agent"
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Model name for judge (defaults to provider default)"
    )
    
    parser.add_argument(
        "--target-provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "together", "google"],
        help="LLM provider for target model"
    )
    parser.add_argument(
        "--target-model",
        type=str,
        default=None,
        help="Model name for target (defaults to provider default)"
    )
    
    # Experiment configuration
    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        default=None,
        help="List of strategies to test (defaults to all)"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=None,
        help="List of categories to test (defaults to all)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum iterations per question"
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=50,
        help="Maximum queries per question"
    )
    parser.add_argument(
        "--judge-threshold",
        type=float,
        default=0.7,
        help="Score threshold for successful jailbreak"
    )
    parser.add_argument(
        "--max-questions-per-category",
        type=int,
        default=None,
        help="Limit number of questions per category"
    )
    
    # Output configuration
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to save results"
    )
    parser.add_argument(
        "--no-save-intermediate",
        action="store_true",
        help="Don't save intermediate results"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output during execution"
    )
    
    # Advanced options
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for LLM generation"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Maximum tokens for LLM generation"
    )
    
    return parser


def create_llm_config(provider: str, model: str = None, temperature: float = 0.7, max_tokens: int = 1000) -> LLMConfig:
    """Create LLM configuration from command line arguments."""
    # Get default config for provider
    config = get_default_config(provider)
    
    # Override with command line arguments
    if model:
        config.model = model
    config.temperature = temperature
    config.max_tokens = max_tokens
    
    return config


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate questions file exists
    if not os.path.exists(args.questions_csv):
        print(f"Error: Questions file not found: {args.questions_csv}")
        sys.exit(1)
    
    # Create LLM configurations
    try:
        attacker_config = create_llm_config(
            args.attacker_provider,
            args.attacker_model,
            args.temperature,
            args.max_tokens
        )
        
        judge_config = create_llm_config(
            args.judge_provider,
            args.judge_model,
            args.temperature * 0.5,  # Lower temperature for judge
            args.max_tokens
        )
        
        target_config = create_llm_config(
            args.target_provider,
            args.target_model,
            args.temperature,
            args.max_tokens
        )
    except Exception as e:
        print(f"Error creating LLM configurations: {e}")
        sys.exit(1)
    
    # Create PAIR configuration
    pair_config = PAIRConfig(
        attacker_llm=attacker_config,
        judge_llm=judge_config,
        target_llm=target_config,
        max_iterations=args.max_iterations,
        max_queries_per_question=args.max_queries,
        judge_score_threshold=args.judge_threshold,
        output_dir=args.output_dir,
        save_intermediate_results=not args.no_save_intermediate,
        verbose=not args.quiet
    )
    
    # Override strategies if specified
    if args.strategies:
        pair_config.strategies = args.strategies
    
    # Print configuration
    if not args.quiet:
        print("\n" + "="*80)
        print("PAIR EXPERIMENT CONFIGURATION")
        print("="*80)
        print(f"\nModels:")
        print(f"  Attacker: {attacker_config.provider} - {attacker_config.model}")
        print(f"  Judge: {judge_config.provider} - {judge_config.model}")
        print(f"  Target: {target_config.provider} - {target_config.model}")
        print(f"\nStrategies: {pair_config.strategies}")
        print(f"Categories: {args.categories or 'All'}")
        print(f"Max iterations: {args.max_iterations}")
        print(f"Max queries: {args.max_queries}")
        print(f"Judge threshold: {args.judge_threshold}")
        print(f"\nOutput directory: {args.output_dir}")
        print("="*80 + "\n")
    
    # Create and run experiment
    try:
        experiment = PAIRExperiment(pair_config)
        results = experiment.run_full_experiment(
            questions_csv=args.questions_csv,
            strategies=args.strategies,
            categories=args.categories,
            max_questions_per_category=args.max_questions_per_category,
            verbose=not args.quiet,
            save_intermediate=not args.no_save_intermediate
        )
        
        print(f"\n✅ Experiment completed successfully!")
        print(f"Results saved to: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Experiment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during experiment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
