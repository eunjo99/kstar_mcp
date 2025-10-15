#!/usr/bin/env python3
"""
KSTAR MCP PoC v2 - Main Entry Point

This is a proof-of-concept system that enables researchers to control KSTAR plasma 
parameters using natural language commands. The system translates natural language 
into EPICS control commands and provides real-time monitoring capabilities.

Key Features:
- Natural language to EPICS command translation
- Real-time plasma parameter monitoring
- Web-based interactive UI
- Demo mode for testing without EPICS hardware
- Integration with OpenAI LLM for command parsing

This PoC demonstrates a simple approach where target values are set and current 
values gradually follow the targets. Future versions will integrate with more 
sophisticated simulation models and machine learning algorithms.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.ui.demo_ui import DemoModeUI


def main():
    """Main execution function - starts the KSTAR MCP PoC v2 system"""
    
    # Load environment variables from .env file
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback to config.env.example if .env doesn't exist
        env_file = project_root / "config.env.example"
        if env_file.exists():
            load_dotenv(env_file)
    
    # Check if OpenAI API key is configured
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not configured.")
        print("   Running in demo mode (LLM functionality limited)")
        print("   To use full functionality:")
        print("   1. Copy config.env.example to .env")
        print("   2. Add your OPENAI_API_KEY to .env file")
        print("   3. Restart the application")
        print()
    
    print("🚀 KSTAR MCP PoC v2 Starting...")
    print("📋 Project Information:")
    print(f"   - Project root: {project_root}")
    print(f"   - OpenAI model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"   - EPICS server: {os.getenv('EPICS_CA_ADDR_LIST', '127.0.0.1')}")
    print(f"   - Server port: {os.getenv('PORT', '8000')}")
    
    # Start the UI server (demo mode)
    ui = DemoModeUI()
    ui.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000"))
    )


if __name__ == "__main__":
    main()
