#!/usr/bin/env python3

"""
Test script to verify that the argument parsing works with enum names.
"""

import argparse
import sys
import os

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Model

def convert_model_name(model_name):
    """Convert enum name to full model name if needed"""
    try:
        # If it's an enum name, get the value
        return Model[model_name].value
    except KeyError:
        # If it's not an enum name, return as is (it's probably already the full name)
        return model_name

def test_argument_parsing():
    """Test that argument parsing works with enum names"""
    
    parser = argparse.ArgumentParser()
    
    # Attack model argument (copied from main.py)
    parser.add_argument(
        "--attack-model",
        default = "vicuna-13b-v1.5",
        help = "Name of attacking model.",
        choices=["vicuna-13b-v1.5", "llama-2-7b-chat-hf", "gpt-3.5-turbo-1106", "gpt-4-0125-preview", "claude-instant-1.2", "claude-2.1", "gemini-pro", 
        "mixtral","vicuna-7b-v1.5", "vicuna", "llama_2", "gpt_3_5", "gpt_4", "claude_1", "claude_2", "gemini"]
    )
    
    # Test cases
    test_cases = [
        ["--attack-model", "vicuna"],
        ["--attack-model", "vicuna-13b-v1.5"],
        ["--attack-model", "gpt_3_5"],
        ["--attack-model", "gpt-3.5-turbo-1106"],
    ]
    
    print("Testing argument parsing with enum names...")
    
    for test_case in test_cases:
        try:
            args = parser.parse_args(test_case)
            original_name = args.attack_model
            converted_name = convert_model_name(args.attack_model)
            print(f"✓ {original_name} -> {converted_name}")
        except SystemExit:
            print(f"✗ Failed to parse: {test_case}")
            return False
    
    # Test invalid choice
    try:
        args = parser.parse_args(["--attack-model", "invalid_model"])
        print("✗ Should have failed with invalid model")
        return False
    except SystemExit:
        print("✓ Correctly rejected invalid model name")
    
    return True

if __name__ == "__main__":
    success = test_argument_parsing()
    if success:
        print("\n✓ All argument parsing tests passed!")
        print("You can now use 'vicuna' instead of 'vicuna-13b-v1.5' as a parameter!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)
