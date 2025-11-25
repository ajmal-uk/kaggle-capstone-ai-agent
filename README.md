# Mental Health First-Step Companion

A production-ready, safety-first AI agent system providing grounding support and mental health resources.

## Features

- **Multi-Agent Architecture**: Planner → Worker → Evaluator pipeline
- **Safety-First Design**: Comprehensive content filtering and evaluation
- **Evidence-Based Techniques**: 5-4-3-2-1 grounding, box breathing, body scan, mindful observation
- **Global Resources**: Official helplines for US, UK, India, Canada, Australia, and worldwide
- **Key Rotation**: Automatic fallback across multiple Gemini API keys
- **Observable**: Detailed logging for debugging and monitoring
- **Web UI**: Gradio interface for easy interaction

## Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone &lt;your-repo-url&gt;
cd mental-health-companion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your Gemini API keys or set MOCK_MODE=True