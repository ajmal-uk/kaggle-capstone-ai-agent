#!/usr/bin/env python3
"""
Demo runner for Mental Health Companion.
"""
import sys
import os

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from main_agent import run_agent
from config import Config

def main():
    print("=" * 60)
    print("Mental Health First-Step Companion - Demo")
    print("=" * 60)
    print(f"Mode: {'MOCK (No API)' if Config.MOCK_MODE else 'LIVE (Using Gemini)'}")
    print("This is NOT a substitute for professional mental health care.")
    print("=" * 60)
    
    test_cases = [
        "I'm feeling really anxious about my exam tomorrow",
        "I'm overwhelmed and don't know what to do",
        "Can you help me calm down?",
        "Tell me about mental health resources"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"User: {test_input}")
        print("Agent processing...")
        
        response = run_agent(test_input)
        
        print(f"\nAgent Response:\n{response}")
        print("-" * 60)
    
    print("\nDemo complete. Run app.py for interactive mode.")

if __name__ == "__main__":
    # Validate config before running
    try:
        Config.validate()
        main()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please create a .env file with GEMINI_API_KEYS or set MOCK_MODE=True")
        sys.exit(1)