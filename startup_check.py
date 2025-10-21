#!/usr/bin/env python3
"""
Startup check for Professor Lock ChatKit Server
Tests all imports and dependencies before starting the server
"""

import sys
import os

def check_imports():
    """Check all required imports"""
    print("🔍 Checking imports...")
    
    try:
        import fastapi
        print("✅ FastAPI")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")
        return False
    
    try:
        from chatkit.server import ChatKitServer
        from chatkit.widgets import Card, Text, Title
        from chatkit.actions import ActionConfig
        print("✅ ChatKit")
    except ImportError as e:
        print(f"❌ ChatKit: {e}")
        return False
        
    try:
        from agents import Agent, Runner, function_tool
        print("✅ Agents")
    except ImportError as e:
        print(f"❌ Agents: {e}")
        return False
    
    try:
        import asyncpg
        print("✅ AsyncPG")
    except ImportError as e:
        print(f"❌ AsyncPG: {e}")
        return False
        
    try:
        import httpx
        print("✅ HTTPX")
    except ImportError as e:
        print(f"❌ HTTPX: {e}")
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔧 Checking environment...")
    
    port = os.getenv("PORT", "8000")
    print(f"✅ PORT: {port}")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...")
    else:
        print("⚠️  OPENAI_API_KEY: Not set")
    
    return True

def check_custom_modules():
    """Check our custom modules"""
    print("\n📦 Checking custom modules...")
    
    try:
        from parleyapp_tools import WebSearchTool, SportsDataTool, StatMuseTool, BettingAnalysisTool
        print("✅ parleyapp_tools")
    except ImportError as e:
        print(f"❌ parleyapp_tools: {e}")
        return False
    
    try:
        from parleyapp_widgets import (
            create_search_progress_widget,
            create_odds_comparison_widget,
            create_parlay_builder_widget
        )
        print("✅ parleyapp_widgets")
    except ImportError as e:
        print(f"❌ parleyapp_widgets: {e}")
        return False
    
    return True

def main():
    print("🚀 Professor Lock Server Startup Check")
    print("=" * 40)
    
    # Check all components
    imports_ok = check_imports()
    env_ok = check_environment()
    modules_ok = check_custom_modules()
    
    print("\n" + "=" * 40)
    if imports_ok and env_ok and modules_ok:
        print("✅ All checks passed! Server ready to start.")
        return 0
    else:
        print("❌ Some checks failed. Fix issues before starting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
