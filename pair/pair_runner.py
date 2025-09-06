"""PAIR algorithm runner - orchestrates the attacker-target-judge loop."""

import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from .config import PAIRConfig
from .models import PAIRResult, AttackAttempt, AttackStatus
from .attacker.attack import Attacker
from .judge.judge import Judge
from .target import TargetModel


class PAIRRunner:
    """Orchestrates the PAIR algorithm for a single question/strategy combination."""
    
    def __init__(
        self,
        config: PAIRConfig,
        attacker: Attacker,
        judge: Judge,
        target: TargetModel
    ):
        """Initialize the PAIR runner.
        
        Args:
            config: PAIR configuration
            attacker: Initialized attacker agent
            judge: Initialized judge agent
            target: Initialized target model
        """
        self.config = config
        self.attacker = attacker
        self.judge = judge
        self.target = target
    
    def run(
        self,
        question_id: int,
        question: str,
        category: str,
        strategy: str,
        verbose: bool = True
    ) -> PAIRResult:
        """Run the PAIR algorithm for a single question.
        
        Args:
            question_id: Unique identifier for the question
            question: The harmful question to test
            category: Category of the question
            strategy: Attack strategy being used
            verbose: Whether to print progress
            
        Returns:
            PAIRResult with all attempts and metrics
        """
        # Initialize result
        result = PAIRResult(
            question_id=question_id,
            question=question,
            category=category,
            strategy=strategy,
            status=AttackStatus.IN_PROGRESS
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Testing Question {question_id}: {question[:50]}...")
            print(f"Category: {category}, Strategy: {strategy}")
            print(f"{'='*60}")
        
        # Track attempts for refinement
        previous_attempts = []
        
        for iteration in range(1, self.config.max_iterations + 1):
            if verbose:
                print(f"\n--- Iteration {iteration}/{self.config.max_iterations} ---")
            
            try:
                # Generate attack prompt
                if iteration == 1:
                    # Initial attack
                    attack_prompt = self.attacker.generate_initial_attack(question)
                else:
                    # Refined attack based on feedback
                    last_feedback = result.attempts[-1].judge_feedback
                    attack_prompt = self.attacker.refine_attack(
                        question,
                        previous_attempts,
                        last_feedback
                    )
                
                if verbose:
                    print(f"Attack prompt: {attack_prompt[:100]}...")
                
                # Query target model
                target_response = self.target.query(attack_prompt)
                
                if verbose:
                    print(f"Target response: {target_response[:100]}...")
                
                # Evaluate with judge
                score, evaluation = self.judge.evaluate(
                    original_question=question,
                    target_response=target_response,
                    attacker_prompt=attack_prompt
                )
                
                if verbose:
                    print(f"Judge score: {score:.2f} ({evaluation['classification']})")
                    print(f"Judge feedback: {evaluation['feedback'][:100]}...")
                
                # Create attempt record
                attempt = AttackAttempt(
                    iteration=iteration,
                    attacker_prompt=attack_prompt,
                    target_response=target_response,
                    judge_score=score,
                    judge_feedback=evaluation['feedback']
                )
                
                # Add to result
                result.add_attempt(attempt)
                
                # Track for refinement
                previous_attempts.append({
                    'prompt': attack_prompt,
                    'result': evaluation['classification'],
                    'score': score,
                    'feedback': evaluation['feedback']
                })
                
                # Check if successful
                if attempt.is_successful:
                    result.status = AttackStatus.SUCCESS
                    if verbose:
                        print(f"\n✅ SUCCESS! Jailbreak achieved in {iteration} iterations.")
                    break
                
                # Check query limit
                if result.total_queries >= self.config.max_queries_per_question:
                    result.status = AttackStatus.MAX_ITERATIONS_REACHED
                    if verbose:
                        print(f"\n❌ Max queries reached without success.")
                    break
                    
            except Exception as e:
                print(f"\n⚠️ Error in iteration {iteration}: {str(e)}")
                # Continue to next iteration
                continue
        
        else:
            # Loop completed without success
            result.status = AttackStatus.MAX_ITERATIONS_REACHED
            if verbose:
                print(f"\n❌ Max iterations reached without success.")
        
        # Set final status if not already set
        if result.status == AttackStatus.IN_PROGRESS:
            result.status = AttackStatus.FAILURE
        
        # Calculate final metrics
        result.end_time = datetime.now()
        
        if verbose:
            print(f"\nFinal Status: {result.status.value}")
            print(f"Total Queries: {result.total_queries}")
            print(f"Mean Score: {result.mean_score:.3f}")
            if result.is_successful:
                print(f"Time to Jailbreak: {result.time_to_jailbreak:.2f}s")
        
        return result
    
    def run_with_variations(
        self,
        question_id: int,
        question: str,
        category: str,
        strategy: str,
        num_variations: int = 3,
        verbose: bool = True
    ) -> List[PAIRResult]:
        """Run PAIR with multiple initial variations of the same strategy.
        
        Args:
            question_id: Unique identifier for the question
            question: The harmful question to test
            category: Category of the question
            strategy: Attack strategy being used
            num_variations: Number of initial variations to try
            verbose: Whether to print progress
            
        Returns:
            List of PAIRResults for each variation
        """
        # Generate initial variations
        initial_prompts = self.attacker.generate_strategy_variations(
            question,
            num_variations
        )
        
        results = []
        
        for i, initial_prompt in enumerate(initial_prompts):
            if verbose:
                print(f"\n\n🔄 Running variation {i+1}/{num_variations}")
            
            # Run PAIR with this initial prompt
            # Note: This would require modifying the run method to accept initial_prompt
            # For now, we'll use the standard run method
            result = self.run(
                question_id=question_id,
                question=question,
                category=category,
                strategy=strategy,
                verbose=verbose
            )
            
            results.append(result)
            
            # If any variation succeeds, we can stop early
            if result.is_successful and i < num_variations - 1:
                if verbose:
                    print(f"\n✅ Success found in variation {i+1}, skipping remaining variations.")
                break
        
        return results
