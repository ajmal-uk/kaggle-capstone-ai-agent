"""
Long-Term Memory Module: Persists user preferences and key facts.
"""
import json
import os
from typing import Dict, Any

class LongTermMemory:
    def __init__(self, storage_file: str = "user_long_term_data.json"):
        self.storage_file = storage_file
        self._load_memory()

    def _load_memory(self):
        """Load memory from JSON file or initialize empty."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"preferences": {}, "facts": {}}
        else:
            self.data = {"preferences": {}, "facts": {}}

    def _save_memory(self):
        """Persist memory to disk."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving long-term memory: {e}")

    def update_preference(self, key: str, value: str):
        """Save a user preference (e.g., 'preferred_technique': 'box_breathing')."""
        self.data["preferences"][key] = value
        self._save_memory()

    def get_preferences_string(self) -> str:
        """Format preferences for LLM context."""
        if not self.data["preferences"]:
            return "No known user preferences."
        
        return "KNOWN USER PREFERENCES:\n" + "\n".join(
            f"- {k}: {v}" for k, v in self.data["preferences"].items()
        )

    def clear(self):
        """Wipe memory (useful for demo/testing)."""
        self.data = {"preferences": {}, "facts": {}}
        self._save_memory()