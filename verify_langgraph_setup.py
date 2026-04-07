#!/usr/bin/env python3
"""
Quick verification script to ensure LangGraph + Groq setup is working correctly.
This script checks:
1. All required packages are installed
2. Environment variables are set
3. Import paths are correct
4. LangGraph graph can be created
"""

import sys
import os
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_packages():
    """Check if all required packages are installed"""
    print_header("1. CHECKING REQUIRED PACKAGES")
    
    packages = {
        'langgraph': 'langgraph',
        'langchain': 'langchain',
        'langchain_core': 'langchain-core',
        'langchain_groq': 'langchain-groq',
        'groq': 'groq',
        'transformers': 'transformers',
        'sentence_transformers': 'sentence-transformers',
        'faiss': 'faiss-cpu',
    }
    
    all_ok = True
    for import_name, pip_name in packages.items():
        try:
            __import__(import_name)
            print_success(f"{import_name} installed")
        except ImportError:
            print_error(f"{import_name} NOT installed (pip install {pip_name})")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists and contains GROQ_API_KEY"""
    print_header("2. CHECKING ENVIRONMENT CONFIGURATION")
    
    env_path = Path("Customer_support_agent/.env")
    
    if not env_path.exists():
        print_error(f".env file not found at {env_path}")
        return False
    
    print_success(f".env file found at {env_path}")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print_error("GROQ_API_KEY not set in .env file")
        return False
    
    print_success("GROQ_API_KEY is set")
    print(f"  API Key: {api_key[:10]}...{api_key[-4:]} (masked)")
    
    groq_model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
    print_success(f"GROQ_MODEL: {groq_model}")
    
    return True

def check_imports():
    """Check if key imports work"""
    print_header("3. CHECKING KEY IMPORTS")
    
    try:
        from langgraph.graph import StateGraph, END
        print_success("langgraph.graph imports successful")
    except ImportError as e:
        print_error(f"langgraph.graph import failed: {e}")
        return False
    
    try:
        from langchain_groq import ChatGroq
        print_success("langchain_groq imports successful")
    except ImportError as e:
        print_error(f"langchain_groq import failed: {e}")
        return False
    
    try:
        from langchain_core.prompts import ChatPromptTemplate
        print_success("langchain_core imports successful")
    except ImportError as e:
        print_error(f"langchain_core import failed: {e}")
        return False
    
    try:
        from Customer_support_agent.support_agent_graph import create_support_agent_graph
        print_success("support_agent_graph imports successful")
    except ImportError as e:
        print_error(f"support_agent_graph import failed: {e}")
        return False
    
    return True

def check_graph_creation():
    """Check if LangGraph can be created"""
    print_header("4. CHECKING LANGGRAPH CREATION")
    
    try:
        from Customer_support_agent.support_agent_graph import create_support_agent_graph
        graph = create_support_agent_graph()
        print_success("LangGraph created successfully")
        print(f"  Graph compiled: {graph is not None}")
        return True
    except Exception as e:
        print_error(f"Failed to create LangGraph: {e}")
        return False

def check_apis():
    """Check if APIs are running"""
    print_header("5. CHECKING IF APIs ARE RUNNING (optional)")
    
    import subprocess
    import time
    
    # Check if support agent is running
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/health"],
        capture_output=True,
        timeout=2
    )
    
    if result.returncode == 0:
        status_code = result.stdout.decode().strip()
        if status_code == "200":
            print_success("Support Agent API running on port 8000")
        else:
            print_warning(f"Support Agent API not responding (HTTP {status_code})")
    else:
        print_warning("Support Agent API not running on port 8000 (not started yet)")

def main():
    print_header("LANGGRAPH + GROQ SETUP VERIFICATION")
    print("This script verifies your LangGraph and Groq integration setup.\n")
    
    results = {
        'Packages': check_packages(),
        'Environment': check_env_file(),
        'Imports': check_imports(),
        'Graph Creation': check_graph_creation(),
    }
    
    try:
        check_apis()
    except Exception:
        print_warning("API check skipped (curl not available)")
    
    # Summary
    print_header("SUMMARY")
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = GREEN if passed else RED
        print(f"{color}{status}{RESET} - {check}")
    
    print()
    if all_passed:
        print_success("All checks passed! Your LangGraph setup is ready.")
        print(f"\n{BLUE}Next steps:{RESET}")
        print("1. Start the support agent: python Customer_support_agent/main.py")
        print("2. Run the dashboard: streamlit run app.py")
        print("3. Test LangGraph: python test_langgraph.py")
    else:
        print_error("Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
