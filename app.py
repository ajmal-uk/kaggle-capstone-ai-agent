import gradio as gr
import os
import sys
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- 1. SETUP LOGGING ---
LOG_FILE = "spaces_app.log"
logger.add(LOG_FILE, rotation="1 MB", format="{time:HH:mm:ss} | {level} | {message}")

# --- 2. IMPORT AGENT ---
try:
    # FIX: Import from project package
    from project.main_agent import MainAgent
    from project.config import Config
    
    # Validation logic
    try:
        Config.validate()
        logger.info("Configuration validated successfully.")
        
        # Debug Print (Safe)
        key_count = len(Config.GEMINI_API_KEYS)
        mode = "MOCK" if Config.MOCK_MODE else "LIVE"
        print(f"--- SYSTEM STARTUP: {mode} MODE ({key_count} keys loaded) ---")

    except Exception as e:
        logger.warning(f"Config validation failed: {e}")

    # Initialize Global Agent
    agent_instance = MainAgent()
    logger.info("MainAgent initialized successfully.")

except ImportError as e:
    logger.error(f"Failed to import project modules: {e}")
    raise e

# --- 3. UI LOGIC ---

def get_live_logs():
    """Reads the last N chars of the log file."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return f.read()[-3000:]
        except Exception:
            return "Logs loading..."
    return "Logs initializing..."

def response_generator(message, history):
    """
    Generator function for ChatInterface.
    """
    if not message:
        return ""
        
    logger.info(f"User Input: {message}")
    
    try:
        # Run the agent
        result_dict = agent_instance.handle_message(message)
        response_text = result_dict.get("response", "Error: No response text found.")
        
        # Log specific actions
        action = result_dict.get('plan', {}).get('action')
        logger.info(f"Agent Action: {action}")

        # Safety visual indicator
        if result_dict.get("safety_status") == "REJECTED":
             response_text = "🛡️ **Safety Alert:** " + response_text
             logger.warning("Safety guardrail triggered.")
             
        return response_text

    except Exception as e:
        logger.error(f"Runtime Error: {e}")
        return f"An internal error occurred: {str(e)}"

# --- 4. UI LAYOUT ---

with gr.Blocks(title="Mental Health Companion") as demo:
    
    # CSS Injection
    gr.HTML("""
    <style>
    .chatbot {min_height: 400px;}
    #log_panel {background-color: #1e1e1e; color: #00ff00; font-family: 'Courier New', monospace; font-size: 12px;}
    </style>
    """)

    gr.Markdown("## 🌿 Mental Health First-Step Companion\n*A Multi-Agent System: Planner → Worker → Evaluator*")

    with gr.Row():
        # Left Column: Chat Interface
        with gr.Column(scale=2):
            chat_interface = gr.ChatInterface(
                fn=response_generator,
            )
        
        # Right Column: Logs
        with gr.Column(scale=1):
            with gr.Accordion("🛠️ Live System Logs", open=True):
                logs_display = gr.TextArea(
                    elem_id="log_panel", 
                    interactive=False, 
                    lines=25, 
                    label="Agent Thought Process",
                    value="Waiting for logs..."
                )
                # Manual Refresh Button (Backup)
                btn_refresh = gr.Button("Refresh Logs", size="sm")
    
    # --- EVENT HANDLING ---
    
    # 1. Manual Refresh
    btn_refresh.click(get_live_logs, None, logs_display)
    
    # 2. Auto Refresh (Using Timer component if available, otherwise safe fallback)
    # This fixes the "every=1" crash.
    try:
        timer = gr.Timer(value=2)
        timer.tick(get_live_logs, None, logs_display)
    except AttributeError:
        # Fallback for older Gradio versions without Timer
        demo.load(get_live_logs, None, logs_display)

# --- 5. LAUNCH ---
if __name__ == "__main__":
    # Check environment
    is_spaces = "SPACE_ID" in os.environ
    
    if is_spaces:
        demo.queue().launch(server_name="0.0.0.0", server_port=7860)
    else:
        print("--- LAUNCHING LOCALLY ---")
        print("Click here to open: http://127.0.0.1:7860")
        demo.queue().launch(server_name="127.0.0.1", server_port=7860)