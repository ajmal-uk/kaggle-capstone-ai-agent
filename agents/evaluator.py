"""
Evaluator Agent: Safety and quality assurance gatekeeper.
"""
import re
from typing import Dict
from core.context_engineering import EVALUATOR_PROMPT
from core.a2a_protocol import EvaluatorOutput
from core.observability import logger
from core.gemini_client import GeminiClient

class Evaluator:
    def __init__(self):
        self.client = GeminiClient(EVALUATOR_PROMPT)
        self.mock_mode = False
        
        # Safety filters
        self.banned_phrases = [
            r"\bdiagnos(e|is)\b", r"\bmedication\b", r"\bprescri(be|ption)\b",
            r"\btherap(y|ist)\b.*\b(recommend|suggest)", r"\bguarantee\b", r"\bcure\b"
        ]
        self.crisis_keywords = ["suicide", "self-harm", "kill myself", "end it all"]
        
    def evaluate(self, worker_output: Dict) -> Dict:
        draft = worker_output.get("draft_response", "")
        tools_used = worker_output.get("tools_used", [])
        
        logger.log("Evaluator", "Starting safety evaluation", 
                  data={"draft_length": len(draft), "tools": tools_used})
        
        # Mock mode
        if hasattr(self, 'mock_mode') and self.mock_mode:
            return self._mock_evaluate(draft)
        
        # Quick safety checks
        if self._contains_medical_advice(draft):
            logger.log("Evaluator", "REJECTED: Medical advice detected")
            return EvaluatorOutput(
                status="REJECTED",
                feedback="Contains medical advice or diagnosis language.",
                final_response=self._get_fallback_response()
            ).to_dict()
        
        if self._contains_harmful_content(draft):
            logger.log("Evaluator", "REJECTED: Harmful content detected")
            return EvaluatorOutput(
                status="REJECTED",
                feedback="Potentially harmful content detected.",
                final_response=self._get_fallback_response()
            ).to_dict()
        
        # Use LLM for deeper evaluation
        prompt = f"""
        DRAFT RESPONSE TO EVALUATE:
        {draft}
        
        TOOLS USED: {', '.join(tools_used)}
        
        Provide your safety evaluation JSON.
        """
        
        evaluation = self.client.generate_json(prompt)
        
        if not evaluation:
            logger.log("Evaluator", "Evaluation failed, using fallback")
            return EvaluatorOutput(
                status="REJECTED",
                feedback="Evaluation error.",
                final_response=self._get_fallback_response()
            ).to_dict()
        
        # Post-process evaluation
        if evaluation.get("status") == "APPROVED":
            final_response = draft
        else:
            final_response = evaluation.get("sanitized_response", self._get_fallback_response())
        
        logger.log("Evaluator", f"Evaluation result: {evaluation.get('status')}")
        
        return EvaluatorOutput(
            status=evaluation.get("status", "REJECTED"),
            feedback=evaluation.get("feedback", "Safety check failed."),
            final_response=final_response
        ).to_dict()
    
    def _contains_medical_advice(self, text: str) -> bool:
        """Check for prohibited medical language."""
        text_lower = text.lower()
        for pattern in self.banned_phrases:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _contains_harmful_content(self, text: str) -> bool:
        """Check for harmful or dangerous suggestions."""
        return any(keyword in text.lower() for keyword in ["self-harm", "hurt yourself"])
    
    def _get_fallback_response(self) -> str:
        """Safe fallback message for rejected responses."""
        return """
        I apologize, but I cannot provide the requested advice. Please consider reaching out to:
        
        **988 Suicide & Crisis Lifeline**: 988 (US)
        **NHS 111** (UK)
        **Kiran Helpline**: 1800-599-0019 (India)
        
        For professional mental health support, consult a licensed therapist or counselor.
        """
    
    def _mock_evaluate(self, draft: str) -> Dict:
        """Mock evaluation for testing."""
        # Simple mock logic
        if "diagnosis" in draft.lower() or "medication" in draft.lower():
            return EvaluatorOutput(
                status="REJECTED",
                feedback="Mock: Medical advice detected",
                final_response=self._get_fallback_response()
            ).to_dict()
        
        return EvaluatorOutput(
            status="APPROVED",
            feedback="Mock: Safe and supportive",
            final_response=draft
        ).to_dict()