"""Experiment runner for comprehensive PAIR evaluation."""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

from .config import PAIRConfig, LLMConfig
from .models import ExperimentResults, PAIRResult, StrategyMetrics
from .pair_runner import PAIRRunner
from .attacker.attack import Attacker
from .judge.judge import Judge
from .target import TargetModel


class PAIRExperiment:
    """Manages and runs comprehensive PAIR experiments across strategies and questions."""
    
    def __init__(self, config: PAIRConfig):
        """Initialize the experiment with configuration.
        
        Args:
            config: PAIR configuration
        """
        self.config = config
        self.results = None
        
        # Initialize agents
        self.judge = Judge(config.judge_llm)
        self.target = TargetModel(config.target_llm)
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
    def load_questions(self, csv_path: str) -> List[Dict[str, str]]:
        """Load questions from CSV file.
        
        Args:
            csv_path: Path to CSV file with columns 'prompt' and 'category'
            
        Returns:
            List of question dictionaries
        """
        questions = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                questions.append({
                    'id': i + 1,
                    'prompt': row['prompt'],
                    'category': row['category']
                })
        return questions
    
    def run_single_experiment(
        self,
        question: Dict[str, str],
        strategy: str,
        verbose: bool = True
    ) -> PAIRResult:
        """Run PAIR for a single question/strategy combination.
        
        Args:
            question: Question dictionary with 'id', 'prompt', 'category'
            strategy: Attack strategy to use
            verbose: Whether to print progress
            
        Returns:
            PAIRResult for this experiment
        """
        # Create attacker with specific strategy
        attacker = Attacker(self.config.attacker_llm, strategy)
        
        # Create runner
        runner = PAIRRunner(
            config=self.config,
            attacker=attacker,
            judge=self.judge,
            target=self.target
        )
        
        # Run PAIR
        result = runner.run(
            question_id=question['id'],
            question=question['prompt'],
            category=question['category'],
            strategy=strategy,
            verbose=verbose
        )
        
        return result
    
    def run_full_experiment(
        self,
        questions_csv: str,
        strategies: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        max_questions_per_category: Optional[int] = None,
        verbose: bool = True,
        save_intermediate: bool = True
    ) -> ExperimentResults:
        """Run the full PAIR experiment across all strategies and questions.
        
        Args:
            questions_csv: Path to CSV file with questions
            strategies: List of strategies to test (None = use all from config)
            categories: List of categories to test (None = test all)
            max_questions_per_category: Limit questions per category (None = no limit)
            verbose: Whether to print detailed progress
            save_intermediate: Whether to save results after each question
            
        Returns:
            ExperimentResults with comprehensive metrics
        """
        # Load questions
        all_questions = self.load_questions(questions_csv)
        
        # Filter by categories if specified
        if categories:
            all_questions = [q for q in all_questions if q['category'] in categories]
        
        # Limit questions per category if specified
        if max_questions_per_category:
            category_counts = {}
            filtered_questions = []
            for q in all_questions:
                cat = q['category']
                if cat not in category_counts:
                    category_counts[cat] = 0
                if category_counts[cat] < max_questions_per_category:
                    filtered_questions.append(q)
                    category_counts[cat] += 1
            all_questions = filtered_questions
        
        # Use specified strategies or all from config
        strategies = strategies or self.config.strategies
        
        # Initialize results
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = ExperimentResults(
            experiment_id=experiment_id,
            start_time=datetime.now(),
            config={
                'strategies': strategies,
                'num_questions': len(all_questions),
                'categories': list(set(q['category'] for q in all_questions)),
                'target_model': self.config.target_llm.model,
                'judge_model': self.config.judge_llm.model,
                'attacker_model': self.config.attacker_llm.model,
                'max_iterations': self.config.max_iterations
            }
        )
        
        total_experiments = len(all_questions) * len(strategies)
        current_experiment = 0
        
        print(f"\n{'='*80}")
        print(f"Starting PAIR Experiment: {experiment_id}")
        print(f"Total experiments: {total_experiments}")
        print(f"Questions: {len(all_questions)}, Strategies: {len(strategies)}")
        print(f"{'='*80}\n")
        
        # Run experiments
        for strategy in strategies:
            print(f"\n{'='*60}")
            print(f"STRATEGY: {strategy}")
            print(f"{'='*60}")
            
            for question in all_questions:
                current_experiment += 1
                
                print(f"\n[{current_experiment}/{total_experiments}] "
                      f"Question {question['id']} | Category: {question['category']}")
                
                try:
                    # Run single experiment
                    result = self.run_single_experiment(
                        question=question,
                        strategy=strategy,
                        verbose=verbose
                    )
                    
                    # Add to results
                    self.results.add_result(result)
                    
                    # Save intermediate results
                    if save_intermediate:
                        self.save_intermediate_results()
                    
                    # Brief pause to avoid rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"\n⚠️ Error in experiment: {str(e)}")
                    # Create a failed result
                    failed_result = PAIRResult(
                        question_id=question['id'],
                        question=question['prompt'],
                        category=question['category'],
                        strategy=strategy,
                        status=AttackStatus.FAILURE
                    )
                    self.results.add_result(failed_result)
        
        # Compute final metrics
        self.results.compute_final_metrics()
        
        # Save final results
        self.save_results()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def save_intermediate_results(self):
        """Save intermediate results to file."""
        if not self.results:
            return
        
        output_path = Path(self.config.output_dir) / f"intermediate_{self.results.experiment_id}.json"
        
        # Convert results to serializable format
        data = {
            'experiment_id': self.results.experiment_id,
            'timestamp': datetime.now().isoformat(),
            'config': self.results.config,
            'num_completed': len(self.results.results),
            'results_summary': []
        }
        
        for result in self.results.results:
            data['results_summary'].append({
                'question_id': result.question_id,
                'category': result.category,
                'strategy': result.strategy,
                'status': result.status.value,
                'num_iterations': result.num_iterations,
                'final_score': result.final_score,
                'mean_score': result.mean_score,
                'is_successful': result.is_successful
            })
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_results(self):
        """Save complete experiment results."""
        if not self.results:
            return
        
        output_dir = Path(self.config.output_dir)
        
        # Save detailed JSON results
        json_path = output_dir / f"results_{self.results.experiment_id}.json"
        self._save_json_results(json_path)
        
        # Save CSV summary
        csv_path = output_dir / f"summary_{self.results.experiment_id}.csv"
        self._save_csv_summary(csv_path)
        
        # Save strategy metrics
        metrics_path = output_dir / f"metrics_{self.results.experiment_id}.json"
        self._save_strategy_metrics(metrics_path)
        
        print(f"\n📁 Results saved to {output_dir}")
    
    def _save_json_results(self, path: Path):
        """Save detailed JSON results."""
        data = {
            'experiment_id': self.results.experiment_id,
            'start_time': self.results.start_time.isoformat(),
            'end_time': self.results.end_time.isoformat() if self.results.end_time else None,
            'config': self.results.config,
            'overall_metrics': {
                'total_experiments': len(self.results.results),
                'successful_attacks': sum(1 for r in self.results.results if r.is_successful),
                'overall_asr': sum(1 for r in self.results.results if r.is_successful) / len(self.results.results) if self.results.results else 0
            },
            'strategy_metrics': {},
            'category_metrics': self.results.category_metrics,
            'detailed_results': []
        }
        
        # Add strategy metrics
        for strategy, metrics in self.results.strategy_metrics.items():
            data['strategy_metrics'][strategy] = {
                'total_attempts': metrics.total_attempts,
                'successful_attacks': metrics.successful_attacks,
                'asr': metrics.attack_success_rate,
                'mean_iterations_to_success': metrics.mean_iterations_to_success,
                'mean_score_overall': metrics.mean_score_overall,
                'average_queries_per_attempt': metrics.average_queries_per_attempt,
                'category_breakdown': metrics.category_breakdown
            }
        
        # Add detailed results
        for result in self.results.results:
            data['detailed_results'].append({
                'question_id': result.question_id,
                'question': result.question,
                'category': result.category,
                'strategy': result.strategy,
                'status': result.status.value,
                'is_successful': result.is_successful,
                'num_iterations': result.num_iterations,
                'total_queries': result.total_queries,
                'final_score': result.final_score,
                'mean_score': result.mean_score,
                'score_progression': result.score_progression,
                'time_to_jailbreak': result.time_to_jailbreak,
                'attempts': [
                    {
                        'iteration': att.iteration,
                        'score': att.judge_score,
                        'is_successful': att.is_successful,
                        'prompt_preview': att.attacker_prompt[:200] + '...',
                        'response_preview': att.target_response[:200] + '...',
                        'feedback': att.judge_feedback
                    }
                    for att in result.attempts
                ]
            })
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_csv_summary(self, path: Path):
        """Save CSV summary of results."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'question_id', 'category', 'strategy', 'status', 'is_successful',
                'num_iterations', 'total_queries', 'final_score', 'mean_score',
                'time_to_jailbreak', 'question_preview'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results.results:
                writer.writerow({
                    'question_id': result.question_id,
                    'category': result.category,
                    'strategy': result.strategy,
                    'status': result.status.value,
                    'is_successful': result.is_successful,
                    'num_iterations': result.num_iterations,
                    'total_queries': result.total_queries,
                    'final_score': f"{result.final_score:.3f}",
                    'mean_score': f"{result.mean_score:.3f}",
                    'time_to_jailbreak': f"{result.time_to_jailbreak:.2f}" if result.time_to_jailbreak else "N/A",
                    'question_preview': result.question[:50] + '...'
                })
    
    def _save_strategy_metrics(self, path: Path):
        """Save strategy-specific metrics."""
        metrics_data = {}
        
        for strategy, metrics in self.results.strategy_metrics.items():
            metrics_data[strategy] = {
                'summary': {
                    'total_attempts': metrics.total_attempts,
                    'successful_attacks': metrics.successful_attacks,
                    'attack_success_rate': f"{metrics.attack_success_rate:.3f}",
                    'mean_iterations_to_success': f"{metrics.mean_iterations_to_success:.2f}",
                    'mean_score_overall': f"{metrics.mean_score_overall:.3f}",
                    'mean_score_successful': f"{metrics.mean_score_successful:.3f}",
                    'average_queries_per_attempt': f"{metrics.average_queries_per_attempt:.2f}"
                },
                'category_performance': metrics.category_breakdown
            }
        
        with open(path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
    
    def print_summary(self):
        """Print a summary of experiment results."""
        if not self.results:
            print("No results to summarize.")
            return
        
        print(f"\n{'='*80}")
        print(f"EXPERIMENT SUMMARY")
        print(f"{'='*80}")
        
        print(f"\nExperiment ID: {self.results.experiment_id}")
        print(f"Duration: {(self.results.end_time - self.results.start_time).total_seconds():.2f} seconds")
        print(f"Total Experiments: {len(self.results.results)}")
        
        # Overall metrics
        successful = sum(1 for r in self.results.results if r.is_successful)
        overall_asr = successful / len(self.results.results) if self.results.results else 0
        
        print(f"\n📊 OVERALL METRICS:")
        print(f"  - Successful Attacks: {successful}/{len(self.results.results)}")
        print(f"  - Overall ASR: {overall_asr:.3f}")
        
        # Strategy performance
        print(f"\n📈 STRATEGY PERFORMANCE:")
        for strategy, metrics in sorted(
            self.results.strategy_metrics.items(),
            key=lambda x: x[1].attack_success_rate,
            reverse=True
        ):
            print(f"\n  {strategy}:")
            print(f"    - ASR: {metrics.attack_success_rate:.3f} "
                  f"({metrics.successful_attacks}/{metrics.total_attempts})")
            print(f"    - Avg Queries: {metrics.average_queries_per_attempt:.2f}")
            if metrics.successful_attacks > 0:
                print(f"    - Avg Iterations to Success: {metrics.mean_iterations_to_success:.2f}")
            print(f"    - Mean Score: {metrics.mean_score_overall:.3f}")
        
        # Category performance
        print(f"\n📊 CATEGORY PERFORMANCE:")
        for category, cat_metrics in sorted(
            self.results.category_metrics.items(),
            key=lambda x: x[1]['asr'],
            reverse=True
        ):
            print(f"\n  {category}:")
            print(f"    - ASR: {cat_metrics['asr']:.3f} "
                  f"({cat_metrics['successful']}/{cat_metrics['total']})")
            
            # Top strategies for this category
            top_strategies = sorted(
                cat_metrics['strategy_performance'].items(),
                key=lambda x: x[1]['asr'],
                reverse=True
            )[:3]
            
            if top_strategies:
                print(f"    - Top Strategies:")
                for strat, perf in top_strategies:
                    if perf['total'] > 0:
                        print(f"      • {strat}: ASR {perf['asr']:.3f}")
        
        print(f"\n{'='*80}")
