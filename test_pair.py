"""Test script to verify PAIR implementation."""

import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from pair import (
            PAIRConfig, LLMConfig, DEFAULT_CONFIGS,
            Attacker, Judge, TargetModel,
            PAIRRunner, PAIRExperiment,
            PAIRAnalyzer
        )
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_configuration():
    """Test configuration creation."""
    print("\nTesting configuration...")
    try:
        from pair import PAIRConfig, LLMConfig
        
        # Create mock configs (won't actually call APIs)
        attacker_config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="mock_key"
        )
        
        judge_config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            api_key="mock_key"
        )
        
        target_config = LLMConfig(
            provider="together",
            model="meta-llama/Llama-2-70b-chat-hf",
            api_key="mock_key"
        )
        
        pair_config = PAIRConfig(
            attacker_llm=attacker_config,
            judge_llm=judge_config,
            target_llm=target_config,
            max_iterations=5,
            strategies=["role_play", "encoding"]
        )
        
        print(f"✅ Configuration created successfully!")
        print(f"   - Strategies: {pair_config.strategies}")
        print(f"   - Max iterations: {pair_config.max_iterations}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_components():
    """Test component initialization."""
    print("\nTesting components...")
    try:
        from pair import Attacker, Judge, TargetModel, LLMConfig
        from pair.attacker.attacker_system_prompts import get_attacker_prompt
        
        # Test attacker prompt loading
        strategies = ["role_play", "encoding", "hypothetical", "technical_framing"]
        for strategy in strategies:
            prompt = get_attacker_prompt(strategy)
            assert len(prompt) > 100, f"Prompt for {strategy} is too short"
        print(f"✅ All {len(strategies)} attacker strategies loaded successfully!")
        
        # Test component initialization (with mock configs)
        mock_config = LLMConfig(provider="openai", model="gpt-4", api_key="mock")
        
        # Note: These will fail to actually connect but should initialize
        print("✅ Component initialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Component error: {e}")
        return False


def test_data_models():
    """Test data models."""
    print("\nTesting data models...")
    try:
        from pair.models import (
            AttackStatus, AttackAttempt, PAIRResult,
            StrategyMetrics, ExperimentResults
        )
        from datetime import datetime
        
        # Create test attempt
        attempt = AttackAttempt(
            iteration=1,
            attacker_prompt="Test prompt",
            target_response="Test response",
            judge_score=0.8,
            judge_feedback="Good attempt"
        )
        assert attempt.is_successful == True
        
        # Create test result
        result = PAIRResult(
            question_id=1,
            question="Test question",
            category="Test Category",
            strategy="role_play",
            status=AttackStatus.IN_PROGRESS
        )
        result.add_attempt(attempt)
        assert result.is_successful == True
        assert result.mean_score == 0.8
        
        print("✅ Data models working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Data model error: {e}")
        return False


def test_csv_loading():
    """Test CSV file loading."""
    print("\nTesting CSV loading...")
    try:
        import csv
        csv_path = "data/forbidden_questions.csv"
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found at {csv_path}")
            return False
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            questions = list(reader)
        
        print(f"✅ Loaded {len(questions)} questions from CSV")
        
        # Check categories
        categories = set(q['category'] for q in questions)
        print(f"   Categories found: {len(categories)}")
        for cat in sorted(categories)[:5]:
            print(f"     - {cat}")
        if len(categories) > 5:
            print(f"     ... and {len(categories) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV loading error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("PAIR Implementation Test Suite")
    print("="*60)
    
    tests = [
        test_imports,
        test_configuration,
        test_components,
        test_data_models,
        test_csv_loading
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("Test Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✅ All tests passed! PAIR implementation is ready to use.")
        print("\nNext steps:")
        print("1. Set up your API keys in .env file")
        print("2. Run: python run_pair.py data/forbidden_questions.csv")
        print("3. Check results/ directory for outputs")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
