"""
Worker Agent: Executes the plan and generates safe, supportive responses.
"""
from typing import Dict
# FIX: Use absolute imports
from project.core.context_engineering import WORKER_PROMPT
from project.core.a2a_protocol import WorkerOutput
from project.tools.tools import Tools
from project.core.observability import logger
from project.core.gemini_client import GeminiClient

class Worker:
    def __init__(self):
        self.client = GeminiClient(WORKER_PROMPT)
        self.mock_mode = False
        
    def work(self, planner_output: Dict) -> Dict:
        instruction = planner_output.get("instruction", "")
        action = planner_output.get("action", "")
        technique_suggestion = planner_output.get("technique_suggestion", "none")
        
        logger.log("Worker", "Executing plan", 
                  data={"action": action, "technique": technique_suggestion})
        
        # Mock mode
        if hasattr(self, 'mock_mode') and self.mock_mode:
            return self._mock_work(planner_output)
        
        # Gather context data
        context_data = ""
        tools_used = []
        
        if action == "provide_grounding" and technique_suggestion != "none":
            technique = Tools.get_grounding_technique(technique_suggestion)
            if technique:
                context_data = Tools.format_technique_steps(technique)
                tools_used.append(technique_suggestion)
                
        elif action == "provide_resources":
            helpline = Tools.get_helpline("Global")
            context_data = f"""
            Available Resources:
            - {helpline['name']}: {helpline['number']} ({helpline['hours']})
            - Website: {helpline['website']}
            
            For specific countries, provide the country code.
            """
            tools_used.append("helpline_search")
            
        elif action == "emergency_protocol":
            context_data = """
            EMERGENCY PROTOCOL: User may be in crisis.
            Provide ONLY emergency resources and safety disclaimer.
            Do NOT provide grounding techniques or advice.
            """
            tools_used.append("emergency_protocol")
        
        # Build prompt
        prompt = f"""
        USER NEED: {instruction}
        
        SUPPORT DATA:
        {context_data}
        
        Generate a safe, supportive response following your guidelines.
        """
        
        # Generate response
        draft = self.client.generate_response(prompt)
        
        if not draft:
            # Fallback response
            draft = "I apologize, but I'm having trouble generating a response. Please try again, or contact a mental health professional if you need immediate support."
        
        return WorkerOutput(
            draft_response=draft,
            tools_used=tools_used,
            technique_applied=technique_suggestion if action == "provide_grounding" else None
        ).to_dict()
    
    def _mock_work(self, planner_output: Dict) -> Dict:
        """Mock worker for testing - NOW RESPECTS TECHNIQUE SUGGESTION"""
        action = planner_output.get("action")
        technique = planner_output.get("technique_suggestion", "")
        
        if action == "emergency_protocol":
            draft = """
            ⚠️ **If you're in immediate danger, please contact emergency services now.**
            
            In the US: Call or text 988 (Suicide & Crisis Lifeline)
            In the UK: Call 111 (NHS)
            Global: Visit befrienders.org
            
            You matter. Please reach out for professional support.
            """
        elif action == "provide_grounding":
            if technique == "54321_grounding":
                draft = """
                I hear that you're feeling overwhelmed. Let's try the **5-4-3-2-1 Technique** to get grounded.
                
                1. **Look** for 5 things you can see.
                2. **Feel** 4 things you can touch.
                3. **Listen** for 3 things you can hear.
                4. **Smell** 2 things around you.
                5. **Taste** 1 thing.
                
                Take your time with each one. I'm here with you.
                """
            elif technique == "body_scan":
                draft = """
                Let's do a **Mindful Body Scan** to release tension.
                
                Sit comfortably and close your eyes if you wish.
                Starting at your toes, notice any tension. Breathe into it.
                Slowly move your attention up through your feet, legs, stomach...
                Continue all the way to the top of your head.
                Just observe without needing to change anything.
                """
            else:  # box_breathing or default
                draft = """
                Let's try **Box Breathing** to slow things down.
                
                1. **Inhale** for 4 counts...
                2. **Hold** for 4 counts...
                3. **Exhale** for 4 counts...
                4. **Hold** empty for 4 counts...
                
                Repeat this cycle 4 times. You are safe.
                """
        elif action == "provide_resources":
            draft = """
            Here are some trusted mental health resources:
            
            **988 Suicide & Crisis Lifeline**
            Call or text: 988
            Available 24/7
            Website: 988lifeline.org
            
            **Befrienders Worldwide**
            Visit: befrienders.org for global resources
            
            Remember, seeking help is a sign of strength.
            """
        else:
            draft = "Thank you for sharing. I'm here to listen and support you. What you're feeling is valid."
        
        # Add disclaimer
        draft += "\n\n*This is not a substitute for professional care.*"
        
        return WorkerOutput(
            draft_response=draft,
            tools_used=["mock_mode"],
            technique_applied=technique
        ).to_dict()