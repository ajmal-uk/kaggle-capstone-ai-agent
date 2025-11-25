"""
Provides data retrieval tools for the Worker agent.
"""
import json
from typing import Dict, List, Optional

# Comprehensive helpline database
HELPLINES = {
    "US": {
        "name": "988 Suicide & Crisis Lifeline",
        "number": "988",
        "website": "https://988lifeline.org",
        "hours": "24/7"
    },
    "UK": {
        "name": "NHS 111",
        "number": "111",
        "website": "https://www.nhs.uk",
        "hours": "24/7"
    },
    "IN": {
        "name": "Kiran Mental Health Helpline",
        "number": "1800-599-0019",
        "website": "https://nimhans.ac.in",
        "hours": "24/7"
    },
    "CA": {
        "name": "Crisis Services Canada",
        "number": "1-833-456-4566",
        "website": "https://www.crisisservicescanada.ca",
        "hours": "24/7"
    },
    "AU": {
        "name": "Lifeline Australia",
        "number": "13 11 14",
        "website": "https://www.lifeline.org.au",
        "hours": "24/7"
    },
    "Global": {
        "name": "Befrienders Worldwide",
        "number": "Visit befrienders.org",
        "website": "https://www.befrienders.org",
        "hours": "Varies by country"
    }
}

# Evidence-based grounding techniques
TECHNIQUES = {
    "box_breathing": {
        "name": "Box Breathing",
        "steps": [
            "Inhale slowly through your nose for 4 seconds",
            "Hold your breath for 4 seconds",
            "Exhale slowly through your mouth for 4 seconds",
            "Hold empty for 4 seconds",
            "Repeat 4-5 times"
        ],
        "description": "A calming technique used by first responders to regulate breathing"
    },
    "54321_grounding": {
        "name": "5-4-3-2-1 Grounding",
        "steps": [
            "Name 5 things you can SEE around you",
            "Name 4 things you can TOUCH",
            "Name 3 things you can HEAR",
            "Name 2 things you can SMELL",
            "Name 1 thing you can TASTE"
        ],
        "description": "A sensory awareness technique to reconnect with the present moment"
    },
    "body_scan": {
        "name": "Progressive Body Scan",
        "steps": [
            "Close your eyes and take 3 deep breaths",
            "Focus on your toes - tense for 5 seconds, then release",
            "Move to your calves - tense and release",
            "Continue upward: thighs, stomach, hands, arms, shoulders",
            "End with your face - scrunch, then relax"
        ],
        "description": "Progressive muscle relaxation to release physical tension"
    },
    "mindful_observation": {
        "name": "Mindful Observation",
        "steps": [
            "Pick one small object near you",
            "Observe it as if you've never seen it before",
            "Notice its color, texture, shape, weight",
            "Focus all attention on this object for 60 seconds"
        ],
        "description": "Focus attention to interrupt anxious thoughts"
    }
}

class Tools:
    @staticmethod
    def get_helpline(country_code: str = "Global") -> Dict:
        """Returns helpline info for a given country code."""
        return HELPLINES.get(country_code.upper(), HELPLINES["Global"])
    
    @staticmethod
    def get_all_country_codes() -> List[str]:
        """Get list of supported country codes."""
        return list(HELPLINES.keys())
    
    @staticmethod
    def get_grounding_technique(technique_name: str) -> Optional[Dict]:
        """Returns the complete technique details."""
        return TECHNIQUES.get(technique_name)
    
    @staticmethod
    def get_all_techniques() -> List[Dict]:
        """Get all available techniques."""
        return [
            {
                "name": tech["name"],
                "key": key,
                "description": tech["description"]
            }
            for key, tech in TECHNIQUES.items()
        ]
    
    @staticmethod
    def format_technique_steps(technique: Dict) -> str:
        """Format technique steps for user-friendly display."""
        if not technique:
            return "Take a deep breath and focus on the present moment."
        
        steps = f"**{technique['name']}**\n{technique['description']}\n\nSteps:\n"
        for i, step in enumerate(technique['steps'], 1):
            steps += f"{i}. {step}\n"
        return steps