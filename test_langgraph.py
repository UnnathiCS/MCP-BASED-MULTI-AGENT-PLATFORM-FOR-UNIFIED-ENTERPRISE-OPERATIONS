#!/usr/bin/env python3
"""
Test script to verify LangGraph is actually being used and not falling back to rules.
This will show you exactly what the LLM is deciding vs what the rule-based system would decide.
"""

import requests
import json
import sys

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

# Test queries
TEST_QUERIES = [
    {
        "query": "My VPN keeps dropping",
        "expected_from_llm": "Should understand frustration + system issue",
        "rule_based_would_say": "AUTO_RESOLVE (we have VPN policy)"
    },
    {
        "query": "System is completely down, nobody can access anything",
        "expected_from_llm": "Should recognize CRITICAL urgency",
        "rule_based_would_say": "ESCALATE (outage detected)"
    },
    {
        "query": "Can I please get access to the development database?",
        "expected_from_llm": "Should need more context/approval",
        "rule_based_would_say": "HUMAN_REVIEW (access request)"
    }
]

def test_support_agent():
    """Test the support agent with LangGraph"""
    
    print(f"\n{BOLD}{BLUE}{'='*80}{END}")
    print(f"{BOLD}{BLUE}LangGraph Support Agent - Testing Script{END}")
    print(f"{BOLD}{BLUE}{'='*80}{END}\n")
    
    # Check if agent is running
    try:
        health = requests.get("http://localhost:8000/health", timeout=2)
        print(f"{GREEN}✅ Support Agent is running on port 8000{END}\n")
    except:
        print(f"{RED}❌ Support Agent is NOT running on port 8000{END}")
        print(f"   Start it with: cd Customer_support_agent && python -m uvicorn main:app --port 8000")
        sys.exit(1)
    
    # Run tests
    for i, test_case in enumerate(TEST_QUERIES, 1):
        print(f"{BOLD}{YELLOW}Test {i}/{len(TEST_QUERIES)}: {test_case['query'][:50]}...{END}")
        print(f"{YELLOW}{'─'*70}{END}")
        
        try:
            # Test via debug endpoint (shows full LangGraph execution)
            response = requests.post(
                "http://localhost:8000/debug/test-langgraph",
                json={"ticket_id": f"test-{i}", "message": test_case['query']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("langgraph_result", {})
                
                print(f"{BLUE}📊 LangGraph Decision:{END}")
                print(f"   Decision: {BOLD}{result.get('decision', 'N/A')}{END}")
                print(f"   Reason: {result.get('reason', 'N/A')[:100]}...")
                print(f"   Severity: {result.get('severity', 'N/A')}")
                print(f"   Answer: {result.get('answer', 'N/A')[:80]}...\n")
                
                print(f"{BLUE}📈 Processing Steps:{END}")
                for step in result.get('processing_steps', []):
                    print(f"   ✓ {step}")
                print()
                
                print(f"{BLUE}🧠 LangGraph Reasoning Process:{END}")
                print(result.get('agent_thoughts', 'No reasoning'))
                print()
                
            else:
                print(f"{RED}❌ Error: {response.status_code}{END}")
                print(f"Response: {response.text}\n")
                
        except Exception as e:
            print(f"{RED}❌ Error testing: {e}{END}\n")
        
        print()

def show_workflow_diagram():
    """Show the LangGraph workflow visualization"""
    print(f"\n{BOLD}{YELLOW}Getting LangGraph Workflow Visualization...{END}")
    print(f"{YELLOW}{'─'*70}{END}\n")
    
    try:
        response = requests.get("http://localhost:8000/graph/visualization", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(data.get('visualization', 'No visualization available'))
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Could not fetch visualization: {e}")

def main():
    """Main test runner"""
    
    # Show workflow
    show_workflow_diagram()
    
    # Run tests
    test_support_agent()
    
    # Summary
    print(f"{BOLD}{GREEN}{'='*80}{END}")
    print(f"{BOLD}{GREEN}✅ Testing Complete!{END}")
    print(f"{BOLD}{GREEN}{'='*80}{END}\n")
    
    print("What you should see:")
    print("  1. ✅ Support Agent running")
    print("  2. 4 processing steps executed (policy → sentiment → classify → llm)")
    print("  3. LLM providing DIFFERENT decisions than simple rules")
    print("  4. Detailed reasoning showing HOW the LLM decided\n")
    
    print("If you see 'Falling back to rule-based decision':")
    print("  → Your GROQ_API_KEY may be invalid or not set")
    print("  → Check: cat Customer_support_agent/.env")
    print("  → Get key from: https://console.groq.com/\n")

if __name__ == "__main__":
    main()
