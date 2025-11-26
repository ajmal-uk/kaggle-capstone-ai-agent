import gradio as gr
import os
import sys
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import io
from PIL import Image
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- 1. SETUP LOGGING ---
LOG_FILE = "sereneshield.log"
# Clear logs on restart so you see fresh output
with open(LOG_FILE, "w") as f:
    f.write("--- SereneShield System Session Started ---\n")

logger.add(LOG_FILE, rotation="1 MB", format="{time:HH:mm:ss} | {level} | {message}")

# --- 2. IMPORT AGENT ---
try:
    from project.main_agent import MainAgent
    from project.config import Config
    
    # Validation logic
    try:
        Config.validate()
        mode = "MOCK" if Config.MOCK_MODE else "LIVE"
        logger.info(f"System Startup: {mode} Mode")
    except Exception as e:
        logger.warning(f"Config validation warning: {e}")

    # Initialize Global Agent Wrapper
    agent_instance = MainAgent()

except ImportError as e:
    logger.error(f"Failed to import project modules: {e}")
    # Fallback for UI testing if backend is missing
    class MockAgent:
        def handle_message(self, msg):
            return {
                "response": "Backend modules missing. Please check import paths.",
                "plan": {"action": "error", "risk_level": "LOW", "emotion": "Error", "distress_score": 0},
                "safety_status": "SAFE"
            }
    agent_instance = MockAgent()

# --- 3. HELPER FUNCTIONS ---

def get_empty_state():
    """Returns initial state for a new user session."""
    return {
        "distress_history": [],
        "msg_count": 0,
        "current_risk": "LOW",
        "last_emotion": "Neutral",
        "max_distress": 0
    }

def generate_plot(user_state):
    """Generates a matplotlib chart of distress levels based on user state."""
    # Handle None state if called prematurely
    if user_state is None:
        user_state = get_empty_state()
        
    history = user_state.get("distress_history", [])
    
    # Create figure with transparent background
    fig = plt.figure(figsize=(6, 3.5))
    fig.patch.set_alpha(0.0) # Transparent
    ax = plt.gca()
    ax.set_facecolor('#0f172a') # Dark slate background for plot area
    ax.patch.set_alpha(0.3)     # Semi-transparent plot area
    
    if not history:
        # Empty state
        plt.text(0.5, 0.5, 'Awaiting User Input...', 
                 horizontalalignment='center', verticalalignment='center', 
                 transform=ax.transAxes, color='#64748b', fontsize=10)
        plt.axis('off')
    else:
        # Plot data
        x = list(range(1, len(history) + 1))
        y = history
        
        # Dynamic color based on latest score
        last_score = history[-1]
        line_color = '#34d399' # Emerald Green
        if last_score > 4: line_color = '#fbbf24' # Amber
        if last_score > 7: line_color = '#f87171' # Red

        # Line styling
        plt.plot(x, y, marker='o', linestyle='-', color=line_color, linewidth=2, markersize=5)
        plt.fill_between(x, y, color=line_color, alpha=0.1)
        
        # Labels and Grid
        plt.title("Real-Time Distress Tracking", color='#e2e8f0', fontsize=10, fontweight='600', pad=10)
        plt.ylim(0, 10.5)
        plt.grid(True, linestyle='--', alpha=0.1, color='white')
        
        # Style Ticks
        ax.tick_params(axis='x', colors='#64748b', labelsize=8)
        ax.tick_params(axis='y', colors='#64748b', labelsize=8)
        
        # Remove borders
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Save to buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=100)
    buf.seek(0)
    plt.close()
    
    return Image.open(buf)

def generate_stats_html(user_state):
    """Generates the HTML for the Safety Monitor."""
    if user_state is None:
        user_state = get_empty_state()

    risk = user_state.get("current_risk", "LOW")
    
    # Color logic
    color_class = "status-green"
    icon = "🛡️"
    if risk == "MEDIUM": 
        color_class = "status-orange"
        icon = "⚠️"
    elif risk == "HIGH": 
        color_class = "status-red"
        icon = "🚨"

    return f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-label">SAFETY STATUS</div>
            <div class="stat-value {color_class}">{icon} {risk}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">DETECTED EMOTION</div>
            <div class="stat-value" style="color: #bfdbfe;">{user_state.get("last_emotion", "Neutral").title()}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">PEAK DISTRESS</div>
            <div class="stat-value">{user_state.get("max_distress", 0)}<span style="font-size:0.6em; color:#64748b;">/10</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">INTERACTIONS</div>
            <div class="stat-value">{user_state.get("msg_count", 0)}</div>
        </div>
    </div>
    """

def get_live_logs():
    """Reads the last N chars of the log file."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return f.read()[-3000:]
        except Exception:
            return "Loading logs..."
    return "Initializing system logs..."

def response_generator(message, history, user_state):
    """
    Generator function for ChatInterface.
    Uses gr.State (user_state) to keep data separate for every user.
    """
    if user_state is None:
        user_state = get_empty_state()

    if not message:
        yield "", user_state, generate_plot(user_state), generate_stats_html(user_state)
        return
        
    try:
        # Run the agent
        result_dict = agent_instance.handle_message(message)
        response_text = result_dict.get("response", "Error: No response text found.")
        
        # Extract metadata
        plan = result_dict.get('plan', {})
        action = plan.get('action')
        risk = plan.get('risk_level', 'LOW')
        emotion = plan.get('emotion', 'Neutral')
        safety_status = result_dict.get("safety_status")
        
        # Update State
        try:
            current_score = int(plan.get('distress_score', 0))
        except (ValueError, TypeError):
            current_score = 0
            
        if current_score > 0:
            user_state["distress_history"].append(current_score)
            
        user_state["msg_count"] += 1
        user_state["current_risk"] = risk
        user_state["last_emotion"] = emotion
        user_state["max_distress"] = max(user_state["max_distress"], current_score)
        
        # Log to server console
        logger.info(f"User input processed. Risk: {risk} | Action: {action}")

        # Add visual indicators to the text
        prefix = ""
        if risk == "HIGH":
            prefix = "🚨 **CRISIS INTERVENTION ACTIVE**\n\n"
        elif action == "enforce_boundary":
            prefix = "🛡️ **Boundary Enforced:** "
        
        final_response = prefix + response_text
        
        # Yield result
        yield final_response, user_state, generate_plot(user_state), generate_stats_html(user_state)

    except Exception as e:
        logger.error(f"Runtime Error: {e}")
        yield f"System Error: {str(e)}", user_state, generate_plot(user_state), generate_stats_html(user_state)

# --- 4. UI LAYOUT ---

with gr.Blocks(title="SereneShield AI") as demo:
    
    # State management for independent user sessions
    user_session = gr.State(value=get_empty_state())

    # 1. Initialization of Dynamic Output Components
    plot_output = gr.Image(label="Emotional Journey", type="pil", elem_id="plot_panel", interactive=False, render=False)
    stats_output = gr.HTML(value=generate_stats_html(get_empty_state()), elem_id="stats_panel", render=False)

    # 2. CSS Styling (Responsive & Glassmorphism)
    gr.HTML("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');

    /* Global Reset */
    body, .gradio-container { 
        background-color: #020617 !important; 
        color: #e2e8f0; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Header Styling */
    .header-container {
        text-align: center;
        padding: 40px 20px;
        background: radial-gradient(circle at 50% -20%, #1e293b 0%, #020617 80%);
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.3);
        margin-bottom: 10px;
    }
    .brand-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* Layout Responsive Handling */
    .main-layout { display: flex; gap: 20px; }
    
    @media (max-width: 900px) {
        .main-layout { flex-direction: column !important; }
        .chat-column { width: 100% !important; }
        .dashboard-column { width: 100% !important; margin-top: 20px; }
    }

    /* Chat Styling */
    .chatbot { 
        height: 600px !important; 
        border: 1px solid #1e293b !important; 
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px !important;
    }

    /* Stats Cards */
    .stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 15px;
    }
    .stat-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        backdrop-filter: blur(5px);
    }
    .stat-label { font-size: 0.7rem; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 5px; }
    .stat-value { font-size: 1.1rem; font-weight: 700; color: #f8fafc; }
    
    /* Status Colors */
    .status-green { color: #4ade80; }
    .status-orange { color: #fbbf24; }
    .status-red { color: #f87171; animation: pulse 2s infinite; }
    
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }

    /* Logs */
    #log_panel textarea { 
        background-color: #0d1117 !important; 
        color: #3fb950 !important; 
        font-family: 'JetBrains Mono', monospace; 
        font-size: 11px;
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* Plot */
    #plot_panel { background-color: transparent; border: none; }

    /* Footer Social Badges */
    .footer-section {
        margin-top: 60px;
        padding: 30px 0;
        border-top: 1px solid #1e293b;
        text-align: center;
    }
    .footer-links img {
        margin: 0 5px;
        transition: transform 0.2s;
    }
    .footer-links img:hover {
        transform: translateY(-2px);
    }
    </style>
    """)

    # 3. Header
    with gr.Row(elem_classes="header-container"):
        with gr.Column():
            gr.HTML("""
            <div class='brand-title'>SereneShield</div>
            <div class='brand-subtitle'>Advanced Mental Health & Safety AI System</div>
            """)

    # 4. Main Content Area
    with gr.Row(elem_classes="main-layout"):
        
        # LEFT: Chat Interface
        with gr.Column(scale=3, elem_classes="chat-column"):
            chat_interface = gr.ChatInterface(
                fn=response_generator,
                additional_inputs=[user_session],
                additional_outputs=[user_session, plot_output, stats_output],
                # Examples are input + state (state is None)
                examples=[
                    ["I'm feeling really overwhelmed today.", None],
                    ["Can you help me ground myself?", None],
                    ["I want to test the safety boundaries.", None]
                ],
            )
        
        # RIGHT: Dashboard (Stacks on mobile)
        with gr.Column(scale=2, elem_classes="dashboard-column"):
            with gr.Tabs():
                # Tab 1: Live Analytics
                with gr.TabItem("📊 Session Analytics"):
                    # HTML Stats
                    stats_output.render()
                    
                    # Plot
                    gr.Markdown("### Emotional Trajectory")
                    plot_output.render()
                
                # Tab 2: Logs
                with gr.TabItem("⚙️ System Logs"):
                    logs_display = gr.TextArea(
                        elem_id="log_panel", 
                        interactive=False, 
                        lines=25, 
                        label="Agent Internal Monologue",
                        value="System initializing..."
                    )

    # 5. Footer with compact SVG icons (single row)
    with gr.Row():
        gr.HTML("""
    <div style="display:flex;align-items:center;justify-content:center;gap:16px;padding:12px 6px;">
      <!-- social icons row -->
      <nav aria-label="social links" style="display:flex;gap:12px;align-items:center;">
        <a href="https://instagram.com/ajmal.me" target="_blank" rel="noopener" aria-label="Instagram" title="Instagram" style="display:inline-flex;align-items:center;">
          <!-- Instagram SVG -->
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="transition:transform .12s ease;">
            <linearGradient id="igg" x1="0" x2="1">
              <stop offset="0" stop-color="#f58529"/><stop offset="0.5" stop-color="#dd2a7b"/><stop offset="1" stop-color="#8134af"/>
            </linearGradient>
            <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#igg)"/>
            <path d="M8 11.9a4 4 0 1 1 8 0 4 4 0 0 1-8 0z" fill="rgba(255,255,255,0.95)"/>
            <circle cx="17.5" cy="6.5" r="1.2" fill="rgba(255,255,255,0.95)"/>
          </svg>
        </a>

        <a href="https://linkedin.com/in/ajmaluk" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn" style="display:inline-flex;align-items:center;">
          <!-- LinkedIn SVG -->
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="transition:transform .12s ease;">
            <rect x="2" y="2" width="20" height="20" rx="4" fill="#0A66C2"/>
            <path d="M7 10.5h2.5V18H7v-7.5zM8.25 8.75a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5zM13 13.5c0-1.7 1.4-2 2.2-2s1.8.6 1.8 2.2V18H16v-3.5c0-.8-.3-1.5-1.2-1.5-.9 0-1.3.6-1.3 1.5V18H13v-4.5z" fill="white"/>
          </svg>
        </a>

        <a href="https://x.com/ajmal_uk_" target="_blank" rel="noopener" aria-label="X (Twitter)" title="X" style="display:inline-flex;align-items:center;">
          <!-- X / Twitter SVG -->
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="transition:transform .12s ease;">
            <rect x="2" y="2" width="20" height="20" rx="4" fill="#111827"/>
            <path d="M8.5 17c5.5 0 8.5-4.6 8.5-8.6 0-.13 0-.26-.01-.39A6.1 6.1 0 0 0 18 7.5a5.7 5.7 0 0 1-1.6.45 2.8 2.8 0 0 0 1.2-1.5 5.6 5.6 0 0 1-1.8.68 2.8 2.8 0 0 0-4.8 2.6A8 8 0 0 1 6 6.8a2.8 2.8 0 0 0 .87 3.8 2.7 2.7 0 0 1-1.3-.36v.04a2.8 2.8 0 0 0 2.3 2.8c-.6.17-1.2.2-1.8.08a2.8 2.8 0 0 0 2.6 1.9A5.6 5.6 0 0 1 6 16.4 8 8 0 0 0 8.5 17z" fill="white"/>
          </svg>
        </a>

        <a href="mailto:ajmaluk.me@gmail.com" aria-label="Email" title="Email" style="display:inline-flex;align-items:center;">
          <!-- Mail SVG -->
          <svg width="28" height="28" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="transition:transform .12s ease;">
            <rect x="2" y="2" width="20" height="20" rx="4" fill="#D23B2B"/>
            <path d="M6 8.5l6 4.2 6-4.2V17a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V8.5z" fill="white"/>
            <path d="M6 7h12l-6 4.2L6 7z" fill="white"/>
          </svg>
        </a>

        <a href="https://ajmaluk.netlify.app" target="_blank" rel="noopener" aria-label="Portfolio" title="Portfolio" style="display:inline-flex;align-items:center;">
          <!-- Globe / Portfolio SVG -->
          <svg width="28" height="28" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="transition:transform .12s ease;">
            <rect x="2" y="2" width="20" height="20" rx="4" fill="#FF6B00"/>
            <path d="M12 6a8 8 0 1 0 0 12 8 8 0 0 0 0-12zm-4 6a6 6 0 0 1 8.66-5.24A10.02 10.02 0 0 0 12 12z" fill="white"/>
          </svg>
        </a>
      </nav>

      <div style="margin-left:18px;color:#94a3b8;font-size:0.85rem;text-align:center;">
        <div><strong>SereneShield AI</strong> • v2.0</div>
        <div style="font-size:0.78rem;margin-top:6px;"><em>Provides emotional support — not a replacement for medical services.</em></div>
      </div>
    </div>

    <style>
      /* footer icon hover + focus */
      nav a svg { transform-origin: center; }
      nav a:hover svg, nav a:focus svg { transform: translateY(-4px) scale(1.05); filter: drop-shadow(0 6px 14px rgba(0,0,0,0.45)); }
      nav a:active svg { transform: translateY(-2px) scale(1.02); }
      nav a { outline: none; }
      nav a:focus { box-shadow: 0 0 0 3px rgba(59,130,246,0.12); border-radius:6px; }
    </style>
    """)

    
    # Auto-Refresh Timer for Logs
    timer = gr.Timer(value=2)
    timer.tick(get_live_logs, None, logs_display)

# --- 5. LAUNCH ---
if __name__ == "__main__":
    is_spaces = "SPACE_ID" in os.environ
    
    print("--- SereneShield Launching ---")
    if is_spaces:
        demo.queue().launch(server_name="0.0.0.0", server_port=7860)
    else:
        demo.queue().launch(server_name="127.0.0.1", server_port=7860, share=False)
