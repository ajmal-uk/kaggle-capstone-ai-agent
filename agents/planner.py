"""
Planner Agent: Analyzes user input and creates a safe, actionable plan.
"""
import json
from typing import Dict
from core.context_engineering import PLANNER_PROMPT
from core.a2a_protocol import PlannerOutput
from core.observability import logger
from core.gemini_client import GeminiClient

class Planner:
    def __init__(self):
        self.client = GeminiClient(PLANNER_PROMPT)
        self.mock_mode = False  # Will be set from config
        
    def plan(self, user_input: str, history_str: str) -> Dict:
        logger.log("Planner", "Analyzing user input...", 
                  data={"input_length": len(user_input)})
        
        # Mock mode for testing
        if hasattr(self, 'mock_mode') and self.mock_mode:
            return self._mock_plan(user_input)
        
        # Prepare prompt with safety context
        prompt = f"""
        Analyze this conversation and provide a structured plan.
        
        CONVERSATION HISTORY:
        {history_str}
        
        CURRENT USER INPUT:
        {user_input}
        
        Remember: Output ONLY valid JSON with no additional text.
        """
        
        response_data = self.client.generate_json(prompt)
        
        if not response_data:
            logger.log("Planner", "Failed to get valid response, using fallback")
            return PlannerOutput(
                emotion="unknown",
                risk_level="LOW",
                action="chat",
                instruction="Apologize for technical issues and encourage user to share more.",
                technique_suggestion="none",
                needs_validation=True
            ).to_dict()
        
        # Validate required fields
        required_fields = ["emotion", "risk_level", "action", "instruction"]
        for field in required_fields:
            if field not in response_data:
                response_data[field] = "unknown" if field == "emotion" else \
                                     "LOW" if field == "risk_level" else \
                                     "chat" if field == "action" else \
                                     "Respond supportively."
        
        logger.log("Planner", "Analysis complete", data=response_data)
        return response_data
    
    def _mock_plan(self, user_input: str) -> Dict:
        """Mock planning for testing without API credits."""
        user_lower = user_input.lower()
        
        # Crisis detection (HIGH priority)
        crisis_keywords = ["kill myself", "end it all", "want to die", "suicide", "self harm"]
        if any(word in user_lower for word in crisis_keywords):
            return PlannerOutput(
                emotion="crisis",
                risk_level="HIGH",
                action="emergency_protocol",
                instruction="Provide emergency disclaimer only. Do not give advice.",
                technique_suggestion="none",
                needs_validation=False
            ).to_dict()
        
        # Anxiety detection
        anxiety_keywords = ["anxious", "panic", "can't breathe", "overwhelmed", "stressed"]
        if any(word in user_lower for word in anxiety_keywords):
            return PlannerOutput(
                emotion="anxiety",
                risk_level="LOW",
                action="provide_grounding",
                instruction="Guide user through box breathing with calm, simple language.",
                technique_suggestion="box_breathing",
                needs_validation=True
            ).to_dict()
        
        # Sadness detection
        sadness_keywords = ["sad", "depressed", "hopeless", "down"]
        if any(word in user_lower for word in sadness_keywords):
            return PlannerOutput(
                emotion="sadness",
                risk_level="LOW",
                action="provide_grounding",
                instruction="Validate feelings and offer 54321 grounding technique.",
                technique_suggestion="54321_grounding",
                needs_validation=True
            ).to_dict()
        
        # Default: supportive chat
        return PlannerOutput(
            emotion="neutral",
            risk_level="LOW",
            action="chat",
            instruction="Respond with warm, supportive validation of their experience.",
            technique_suggestion="none",
            needs_validation=True
        ).to_dict()