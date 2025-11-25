"""
Main Agent: Orchestrator for the multi-agent pipeline.
"""
# FIX: Use absolute imports
from project.agents.planner import Planner
from project.agents.worker import Worker
from project.agents.evaluator import Evaluator
from project.memory.session_memory import SessionMemory
from project.core.observability import logger
from project.config import Config
from typing import Dict

class MainAgent:
    def __init__(self, mock_mode: bool = None):
        # Initialize components
        self.planner = Planner()
        self.worker = Worker()
        self.evaluator = Evaluator()
        self.memory = SessionMemory(max_history=8)
        
        # Set mock mode from config or parameter
        self.mock_mode = mock_mode if mock_mode is not None else Config.MOCK_MODE
        self.planner.mock_mode = self.mock_mode
        self.worker.mock_mode = self.mock_mode
        self.evaluator.mock_mode = self.mock_mode
        
        logger.log("MainAgent", f"Initialized in {'MOCK' if self.mock_mode else 'LIVE'} mode")
    
    def handle_message(self, user_input: str) -> Dict:
        """Process a single user message through the pipeline."""
        logger.log("System", "Processing new message", 
                  data={"input_preview": user_input[:50] + "..."})
        
        try:
            # 1. Update Memory
            self.memory.add_message("user", user_input)
            history_str = self.memory.get_history_string()
            
            # 2. Planner
            plan = self.planner.plan(user_input, history_str)
            
            # 3. Worker
            worker_res = self.worker.work(plan)
            
            # 4. Evaluator
            eval_res = self.evaluator.evaluate(worker_res)
            
            final_response = eval_res.get("final_response")
            
            # 5. Update Memory
            self.memory.add_message("assistant", final_response)
            
            # 6. Compile results
            return {
                "response": final_response,
                "plan": plan,
                "tools_used": worker_res.get("tools_used", []),
                "safety_status": eval_res.get("status"),
                "conversation_stats": self.memory.get_stats(),
                "logs": logger.get_logs()
            }
            
        except Exception as e:
            logger.log("MainAgent", f"Pipeline error: {e}")
            error_response = "I apologize, but I'm experiencing technical difficulties. Please try again later."
            self.memory.add_message("assistant", error_response)
            
            return {
                "response": error_response,
                "plan": {"emotion": "error", "risk_level": "LOW", "action": "chat"},
                "tools_used": [],
                "safety_status": "REJECTED",
                "conversation_stats": self.memory.get_stats(),
                "logs": logger.get_logs()
            }
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation."""
        return self.memory.get_conversation_summary()
    
    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()
        logger.log("MainAgent", "Conversation memory cleared")