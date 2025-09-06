"""Analysis and visualization tools for PAIR experiment results."""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime


class PAIRAnalyzer:
    """Analyze and visualize PAIR experiment results."""
    
    def __init__(self, results_path: str):
        """Initialize analyzer with results file.
        
        Args:
            results_path: Path to JSON results file
        """
        self.results_path = Path(results_path)
        self.output_dir = self.results_path.parent
        
        # Load results
        with open(results_path, 'r') as f:
            self.data = json.load(f)
        
        # Convert to DataFrame for easier analysis
        self.df = self._create_dataframe()
        
        # Set style for visualizations
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame."""
        records = []
        
        for result in self.data['detailed_results']:
            record = {
                'question_id': result['question_id'],
                'category': result['category'],
                'strategy': result['strategy'],
                'status': result['status'],
                'is_successful': result['is_successful'],
                'num_iterations': result['num_iterations'],
                'total_queries': result['total_queries'],
                'final_score': result['final_score'],
                'mean_score': result['mean_score'],
                'time_to_jailbreak': result.get('time_to_jailbreak'),
                'question': result['question']
            }
            
            # Add score progression info
            if result.get('score_progression'):
                record['first_score'] = result['score_progression'][0] if result['score_progression'] else 0
                record['score_improvement'] = result['final_score'] - record['first_score']
                record['max_score'] = max(result['score_progression']) if result['score_progression'] else 0
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def generate_all_visualizations(self):
        """Generate all analysis visualizations."""
        print("Generating analysis visualizations...")
        
        # Create analysis subdirectory
        viz_dir = self.output_dir / f"analysis_{self.data['experiment_id']}"
        viz_dir.mkdir(exist_ok=True)
        
        # Generate visualizations
        self.plot_strategy_performance(viz_dir)
        self.plot_category_performance(viz_dir)
        self.plot_strategy_category_heatmap(viz_dir)
        self.plot_iteration_distribution(viz_dir)
        self.plot_score_progression(viz_dir)
        self.plot_time_analysis(viz_dir)
        self.plot_query_efficiency(viz_dir)
        
        # Generate report
        self.generate_report(viz_dir)
        
        print(f"✅ Analysis complete! Results saved to: {viz_dir}")
    
    def plot_strategy_performance(self, output_dir: Path):
        """Plot strategy performance metrics."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # ASR by strategy
        strategy_asr = self.df.groupby('strategy')['is_successful'].mean().sort_values(ascending=False)
        ax = axes[0, 0]
        strategy_asr.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title('Attack Success Rate by Strategy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy')
        ax.set_ylabel('ASR')
        ax.set_ylim(0, 1)
        ax.axhline(y=self.df['is_successful'].mean(), color='red', linestyle='--', label='Overall ASR')
        ax.legend()
        
        # Mean iterations to success
        successful_df = self.df[self.df['is_successful']]
        if not successful_df.empty:
            mean_iterations = successful_df.groupby('strategy')['num_iterations'].mean().sort_values()
            ax = axes[0, 1]
            mean_iterations.plot(kind='bar', ax=ax, color='lightcoral')
            ax.set_title('Mean Iterations to Success by Strategy', fontsize=14, fontweight='bold')
            ax.set_xlabel('Strategy')
            ax.set_ylabel('Iterations')
        
        # Score distribution by strategy
        ax = axes[1, 0]
        strategies = self.df['strategy'].unique()
        score_data = [self.df[self.df['strategy'] == s]['final_score'].values for s in strategies]
        ax.boxplot(score_data, labels=strategies)
        ax.set_title('Score Distribution by Strategy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy')
        ax.set_ylabel('Final Score')
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        
        # Success rate over iterations
        ax = axes[1, 1]
        for strategy in self.df['strategy'].unique()[:5]:  # Top 5 strategies
            strategy_df = self.df[self.df['strategy'] == strategy]
            iterations = range(1, self.data['config']['max_iterations'] + 1)
            success_by_iter = []
            
            for i in iterations:
                success_count = len(strategy_df[(strategy_df['is_successful']) & (strategy_df['num_iterations'] <= i)])
                total_count = len(strategy_df)
                success_by_iter.append(success_count / total_count if total_count > 0 else 0)
            
            ax.plot(iterations, success_by_iter, label=strategy, marker='o')
        
        ax.set_title('Cumulative Success Rate by Iteration', fontsize=14, fontweight='bold')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Cumulative ASR')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'strategy_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_category_performance(self, output_dir: Path):
        """Plot category performance metrics."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # ASR by category
        category_asr = self.df.groupby('category')['is_successful'].mean().sort_values(ascending=False)
        ax = axes[0, 0]
        category_asr.plot(kind='bar', ax=ax, color='lightgreen')
        ax.set_title('Attack Success Rate by Category', fontsize=14, fontweight='bold')
        ax.set_xlabel('Category')
        ax.set_ylabel('ASR')
        ax.set_ylim(0, 1)
        ax.set_xticklabels(category_asr.index, rotation=45, ha='right')
        
        # Questions per category
        ax = axes[0, 1]
        category_counts = self.df.groupby('category').size()
        category_counts.plot(kind='bar', ax=ax, color='orange')
        ax.set_title('Number of Questions by Category', fontsize=14, fontweight='bold')
        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        ax.set_xticklabels(category_counts.index, rotation=45, ha='right')
        
        # Mean score by category
        ax = axes[1, 0]
        mean_scores = self.df.groupby('category')['mean_score'].mean().sort_values(ascending=False)
        mean_scores.plot(kind='bar', ax=ax, color='purple')
        ax.set_title('Mean Score by Category', fontsize=14, fontweight='bold')
        ax.set_xlabel('Category')
        ax.set_ylabel('Mean Score')
        ax.set_xticklabels(mean_scores.index, rotation=45, ha='right')
        
        # Category difficulty (inverse of ASR)
        ax = axes[1, 1]
        category_difficulty = 1 - category_asr
        category_difficulty = category_difficulty.sort_values(ascending=False)
        category_difficulty.plot(kind='bar', ax=ax, color='crimson')
        ax.set_title('Category Difficulty (1 - ASR)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Category')
        ax.set_ylabel('Difficulty')
        ax.set_xticklabels(category_difficulty.index, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'category_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_strategy_category_heatmap(self, output_dir: Path):
        """Plot heatmap of strategy performance across categories."""
        # Create pivot table of ASR by strategy and category
        pivot_table = pd.pivot_table(
            self.df,
            values='is_successful',
            index='strategy',
            columns='category',
            aggfunc='mean'
        )
        
        # Create heatmap
        plt.figure(figsize=(14, 10))
        sns.heatmap(
            pivot_table,
            annot=True,
            fmt='.3f',
            cmap='RdYlGn',
            vmin=0,
            vmax=1,
            cbar_kws={'label': 'Attack Success Rate'}
        )
        
        plt.title('Strategy Performance Across Categories (ASR)', fontsize=16, fontweight='bold')
        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Strategy', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'strategy_category_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_iteration_distribution(self, output_dir: Path):
        """Plot distribution of iterations needed for successful attacks."""
        successful_df = self.df[self.df['is_successful']]
        
        if successful_df.empty:
            print("No successful attacks to analyze iteration distribution.")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Histogram of iterations to success
        ax = axes[0]
        ax.hist(successful_df['num_iterations'], bins=range(1, self.data['config']['max_iterations'] + 2), 
                edgecolor='black', alpha=0.7, color='steelblue')
        ax.set_title('Distribution of Iterations to Success', fontsize=14, fontweight='bold')
        ax.set_xlabel('Number of Iterations')
        ax.set_ylabel('Frequency')
        ax.axvline(successful_df['num_iterations'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {successful_df["num_iterations"].mean():.2f}')
        ax.legend()
        
        # CDF of iterations to success
        ax = axes[1]
        sorted_iterations = np.sort(successful_df['num_iterations'])
        cdf = np.arange(1, len(sorted_iterations) + 1) / len(sorted_iterations)
        ax.plot(sorted_iterations, cdf, marker='o', linestyle='-', linewidth=2, markersize=4)
        ax.set_title('Cumulative Distribution of Iterations to Success', fontsize=14, fontweight='bold')
        ax.set_xlabel('Number of Iterations')
        ax.set_ylabel('Cumulative Probability')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'iteration_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_score_progression(self, output_dir: Path):
        """Plot score progression analysis."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Average score progression by iteration
        ax = axes[0, 0]
        max_iterations = self.data['config']['max_iterations']
        
        # Calculate average scores by iteration across all attempts
        iteration_scores = {i: [] for i in range(1, max_iterations + 1)}
        
        for result in self.data['detailed_results']:
            for i, score in enumerate(result.get('score_progression', []), 1):
                if i <= max_iterations:
                    iteration_scores[i].append(score)
        
        avg_scores = []
        iterations = []
        for i in range(1, max_iterations + 1):
            if iteration_scores[i]:
                avg_scores.append(np.mean(iteration_scores[i]))
                iterations.append(i)
        
        ax.plot(iterations, avg_scores, marker='o', linewidth=2, markersize=6, color='darkblue')
        ax.set_title('Average Score Progression by Iteration', fontsize=14, fontweight='bold')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Average Score')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0.7, color='red', linestyle='--', label='Success Threshold')
        ax.legend()
        
        # Score improvement distribution
        ax = axes[0, 1]
        score_improvements = self.df['score_improvement'].dropna()
        if not score_improvements.empty:
            ax.hist(score_improvements, bins=20, edgecolor='black', alpha=0.7, color='green')
            ax.set_title('Distribution of Score Improvements', fontsize=14, fontweight='bold')
            ax.set_xlabel('Score Improvement (Final - First)')
            ax.set_ylabel('Frequency')
            ax.axvline(0, color='red', linestyle='--', label='No Improvement')
            ax.legend()
        
        # First vs Final score scatter
        ax = axes[1, 0]
        if 'first_score' in self.df.columns:
            ax.scatter(self.df['first_score'], self.df['final_score'], alpha=0.6)
            ax.plot([0, 1], [0, 1], 'r--', label='No Change')
            ax.plot([0, 1], [0.7, 0.7], 'g--', label='Success Threshold')
            ax.set_title('First Score vs Final Score', fontsize=14, fontweight='bold')
            ax.set_xlabel('First Score')
            ax.set_ylabel('Final Score')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.legend()
        
        # Max score achieved by strategy
        ax = axes[1, 1]
        if 'max_score' in self.df.columns:
            strategy_max_scores = self.df.groupby('strategy')['max_score'].mean().sort_values(ascending=False)
            strategy_max_scores.plot(kind='bar', ax=ax, color='coral')
            ax.set_title('Average Maximum Score by Strategy', fontsize=14, fontweight='bold')
            ax.set_xlabel('Strategy')
            ax.set_ylabel('Average Max Score')
            ax.axhline(y=0.7, color='red', linestyle='--', label='Success Threshold')
            ax.set_xticklabels(strategy_max_scores.index, rotation=45, ha='right')
            ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'score_progression.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_time_analysis(self, output_dir: Path):
        """Plot time-based analysis."""
        # Filter for successful attacks with time data
        time_df = self.df[self.df['is_successful'] & self.df['time_to_jailbreak'].notna()]
        
        if time_df.empty:
            print("No time data available for successful attacks.")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Time to jailbreak by strategy
        ax = axes[0]
        strategy_times = time_df.groupby('strategy')['time_to_jailbreak'].mean().sort_values()
        strategy_times.plot(kind='bar', ax=ax, color='teal')
        ax.set_title('Average Time to Jailbreak by Strategy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy')
        ax.set_ylabel('Time (seconds)')
        ax.set_xticklabels(strategy_times.index, rotation=45, ha='right')
        
        # Time vs iterations scatter
        ax = axes[1]
        ax.scatter(time_df['num_iterations'], time_df['time_to_jailbreak'], alpha=0.6)
        ax.set_title('Time to Jailbreak vs Number of Iterations', fontsize=14, fontweight='bold')
        ax.set_xlabel('Number of Iterations')
        ax.set_ylabel('Time (seconds)')
        
        # Add regression line
        z = np.polyfit(time_df['num_iterations'], time_df['time_to_jailbreak'], 1)
        p = np.poly1d(z)
        ax.plot(time_df['num_iterations'], p(time_df['num_iterations']), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'time_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_query_efficiency(self, output_dir: Path):
        """Plot query efficiency metrics."""
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Queries per attempt by strategy
        ax = axes[0]
        strategy_queries = self.df.groupby('strategy')['total_queries'].mean().sort_values()
        strategy_queries.plot(kind='bar', ax=ax, color='indigo')
        ax.set_title('Average Queries per Attempt by Strategy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy')
        ax.set_ylabel('Average Queries')
        ax.set_xticklabels(strategy_queries.index, rotation=45, ha='right')
        
        # Query efficiency (ASR / avg queries)
        ax = axes[1]
        strategy_asr = self.df.groupby('strategy')['is_successful'].mean()
        efficiency = strategy_asr / strategy_queries
        efficiency = efficiency.sort_values(ascending=False)
        efficiency.plot(kind='bar', ax=ax, color='gold')
        ax.set_title('Query Efficiency by Strategy (ASR / Avg Queries)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strategy')
        ax.set_ylabel('Efficiency Score')
        ax.set_xticklabels(efficiency.index, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'query_efficiency.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self, output_dir: Path):
        """Generate a comprehensive markdown report."""
        report_path = output_dir / 'analysis_report.md'
        
        with open(report_path, 'w') as f:
            # Header
            f.write(f"# PAIR Experiment Analysis Report\n\n")
            f.write(f"**Experiment ID:** {self.data['experiment_id']}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Configuration summary
            f.write("## Experiment Configuration\n\n")
            f.write(f"- **Target Model:** {self.data['config']['target_model']}\n")
            f.write(f"- **Judge Model:** {self.data['config']['judge_model']}\n")
            f.write(f"- **Attacker Model:** {self.data['config']['attacker_model']}\n")
            f.write(f"- **Strategies Tested:** {len(self.data['config']['strategies'])}\n")
            f.write(f"- **Categories Tested:** {len(self.data['config']['categories'])}\n")
            f.write(f"- **Total Questions:** {self.data['config']['num_questions']}\n")
            f.write(f"- **Max Iterations:** {self.data['config']['max_iterations']}\n\n")
            
            # Overall metrics
            f.write("## Overall Results\n\n")
            total_attempts = len(self.df)
            successful_attempts = self.df['is_successful'].sum()
            overall_asr = successful_attempts / total_attempts if total_attempts > 0 else 0
            
            f.write(f"- **Total Experiments:** {total_attempts}\n")
            f.write(f"- **Successful Attacks:** {successful_attempts}\n")
            f.write(f"- **Overall ASR:** {overall_asr:.3f}\n")
            f.write(f"- **Average Iterations:** {self.df['num_iterations'].mean():.2f}\n")
            f.write(f"- **Average Queries:** {self.df['total_queries'].mean():.2f}\n\n")
            
            # Top strategies
            f.write("## Top Performing Strategies\n\n")
            strategy_asr = self.df.groupby('strategy')['is_successful'].mean().sort_values(ascending=False)
            
            f.write("| Rank | Strategy | ASR | Avg Iterations | Avg Queries |\n")
            f.write("|------|----------|-----|----------------|-------------|\n")
            
            for i, (strategy, asr) in enumerate(strategy_asr.head(10).items(), 1):
                strategy_df = self.df[self.df['strategy'] == strategy]
                avg_iter = strategy_df['num_iterations'].mean()
                avg_queries = strategy_df['total_queries'].mean()
                f.write(f"| {i} | {strategy} | {asr:.3f} | {avg_iter:.2f} | {avg_queries:.2f} |\n")
            
            f.write("\n")
            
            # Category analysis
            f.write("## Category Analysis\n\n")
            category_asr = self.df.groupby('category')['is_successful'].mean().sort_values(ascending=False)
            
            f.write("| Category | ASR | Total Questions | Successful |\n")
            f.write("|----------|-----|-----------------|------------|\n")
            
            for category, asr in category_asr.items():
                cat_df = self.df[self.df['category'] == category]
                total = len(cat_df)
                successful = cat_df['is_successful'].sum()
                f.write(f"| {category} | {asr:.3f} | {total} | {successful} |\n")
            
            f.write("\n")
            
            # Best strategy per category
            f.write("## Best Strategy per Category\n\n")
            f.write("| Category | Best Strategy | ASR |\n")
            f.write("|----------|---------------|-----|\n")
            
            for category in self.df['category'].unique():
                cat_df = self.df[self.df['category'] == category]
                cat_strategy_asr = cat_df.groupby('strategy')['is_successful'].mean()
                if not cat_strategy_asr.empty:
                    best_strategy = cat_strategy_asr.idxmax()
                    best_asr = cat_strategy_asr.max()
                    f.write(f"| {category} | {best_strategy} | {best_asr:.3f} |\n")
            
            f.write("\n")
            
            # Key insights
            f.write("## Key Insights\n\n")
            
            # Most effective strategies
            top_strategies = strategy_asr.head(3)
            f.write(f"1. **Most Effective Strategies:** ")
            f.write(", ".join([f"{s} (ASR: {asr:.3f})" for s, asr in top_strategies.items()]))
            f.write("\n\n")
            
            # Most vulnerable categories
            top_categories = category_asr.head(3)
            f.write(f"2. **Most Vulnerable Categories:** ")
            f.write(", ".join([f"{c} (ASR: {asr:.3f})" for c, asr in top_categories.items()]))
            f.write("\n\n")
            
            # Efficiency analysis
            f.write(f"3. **Efficiency Analysis:**\n")
            successful_df = self.df[self.df['is_successful']]
            if not successful_df.empty:
                f.write(f"   - Average iterations to success: {successful_df['num_iterations'].mean():.2f}\n")
                f.write(f"   - Fastest successful attack: {successful_df['num_iterations'].min()} iterations\n")
                f.write(f"   - Most persistent successful attack: {successful_df['num_iterations'].max()} iterations\n")
            
            f.write("\n")
            
            # Score progression
            if 'score_improvement' in self.df.columns:
                avg_improvement = self.df['score_improvement'].mean()
                f.write(f"4. **Score Progression:**\n")
                f.write(f"   - Average score improvement: {avg_improvement:.3f}\n")
                f.write(f"   - Percentage with positive improvement: "
                       f"{(self.df['score_improvement'] > 0).mean() * 100:.1f}%\n")
            
            f.write("\n## Visualizations\n\n")
            f.write("The following visualizations have been generated:\n\n")
            f.write("1. `strategy_performance.png` - Strategy performance metrics\n")
            f.write("2. `category_performance.png` - Category vulnerability analysis\n")
            f.write("3. `strategy_category_heatmap.png` - Strategy effectiveness across categories\n")
            f.write("4. `iteration_distribution.png` - Distribution of iterations to success\n")
            f.write("5. `score_progression.png` - Score progression analysis\n")
            f.write("6. `time_analysis.png` - Time-based performance metrics\n")
            f.write("7. `query_efficiency.png` - Query efficiency analysis\n")
        
        print(f"📄 Report generated: {report_path}")


def analyze_results(results_path: str):
    """Main function to analyze PAIR results.
    
    Args:
        results_path: Path to the JSON results file
    """
    analyzer = PAIRAnalyzer(results_path)
    analyzer.generate_all_visualizations()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <results_json_path>")
        sys.exit(1)
    
    analyze_results(sys.argv[1])
