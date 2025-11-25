#!/usr/bin/env python3
"""
Interactive console application for Mental Health Companion.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from main_agent import MainAgent
from config import Config

def print_welcome():
    print("=" * 70)
    print("Mental Health First-Step Companion")
    print("=" * 70)
    print("A safe, non-medical support agent for grounding and resources.")
    print("⚠️  IMPORTANT: This is NOT a substitute for professional care.")
    print("⚠️  If in crisis, contact emergency services immediately.")
    print("=" * 70)
    print(f"Mode: {'MOCK (Testing)' if Config.MOCK_MODE else 'LIVE (Gemini API)'}")
    print("Commands: /quit, /clear, /stats, /help")
    print("=" * 70)

def print_help():
    print("\nAvailable Commands:")
    print("  /help     - Show this help")
    print("  /clear    - Clear conversation history")
    print("  /stats    - Show conversation statistics")
    print("  /quit     - Exit the application")
    print("\nHow to use:")
    print("  Simply type how you're feeling or what you need help with.")
    print("  The agent will provide grounding techniques or resources.\n")

def main():
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Create a .env file with: GEMINI_API_KEYS=your_key1,your_key2")
        print("Or set MOCK_MODE=True for testing")
        return
    
    agent = MainAgent()
    print_welcome()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Handle commands
            if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
                print("\nThank you for using the Mental Health Companion.")
                print("Take care. 💙")
                break
            
            elif user_input.lower() == "/help":
                print_help()
                continue
            
            elif user_input.lower() == "/clear":
                agent.clear_memory()
                print("\nConversation history cleared.")
                continue
            
            elif user_input.lower() == "/stats":
                stats = agent.get_conversation_summary()
                print(f"\n{stats}")
                continue
            
            # Skip empty input
            if not user_input:
                continue
            
            # Process message
            print("\nAgent: Thinking...")
            result = agent.handle_message(user_input)
            
            # Display response
            print(f"\n{result['response']}")
            
            # Show debug info in non-mock mode
            if not Config.MOCK_MODE and result['safety_status'] == 'REJECTED':
                print(f"\n[Debug: Response was modified for safety]")
            
        except KeyboardInterrupt:
            print("\n\nExiting... Take care!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try again or contact support if this persists.")

if __name__ == "__main__":
    main()