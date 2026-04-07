"""
MCP Unified Agent System
- Single interface for all user requests
- MCP analyzes and routes to appropriate agent
- Agent executes and returns result
- Full decision transparency
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import time

# ============================================================================
# CONFIGURATION
# ============================================================================
SUPPORT_API = "http://127.0.0.1:8000"
DOCUMENT_API = "http://127.0.0.1:8001"

# MCP Agent Registry
AGENTS = {
    "support": {
        "name": "Customer Support Agent",
        "description": "Handles IT support, account issues, connectivity problems, software issues",
        "capabilities": ["network_issues", "account_access", "software_help", "email_support", "vpn_issues"],
        "port": 8000,
        "endpoint": "/it-support/text",
    },
    "documents": {
        "name": "Document Review Agent",
        "description": "Analyzes documents, PDFs, contracts, policies for risk and recommendations",
        "capabilities": ["contract_review", "document_analysis", "risk_assessment", "policy_review"],
        "port": 8001,
        "endpoint": "/review",
    }
}

# ============================================================================
# STREAMLIT PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="MCP Unified Agent System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "last_decision" not in st.session_state:
    st.session_state.last_decision = None

if "agent_response" not in st.session_state:
    st.session_state.agent_response = None

if "trace_data" not in st.session_state:
    st.session_state.trace_data = []

# ============================================================================
# MCP INTENT DETECTION ENGINE
# ============================================================================
class IntentDetector:
    """Analyzes user input and categorizes the problem"""
    
    @staticmethod
    def detect_intent(user_input: str) -> Dict:
        """
        Analyze user input and return:
        - Detected intent
        - Confidence score
        - Recommended agent
        """
        user_input_lower = user_input.lower()
        
        trace_start = time.time() * 1000
        
        # Support Keywords
        support_keywords = {
            "network": ["vpn", "network", "internet", "connection", "wifi", "ethernet"],
            "account": ["login", "password", "account", "access", "email", "credentials"],
            "software": ["crash", "error", "bug", "installation", "update", "application"],
            "printer": ["printer", "print", "paper", "toner", "print queue"],
            "email": ["email", "outlook", "gmail", "email client", "email account"],
            "security": ["security", "antivirus", "firewall", "malware", "virus"],
        }
        
        # Document Keywords
        document_keywords = {
            "contract": ["contract", "agreement", "nda", "service agreement"],
            "policy": ["policy", "procedure", "guideline", "standard"],
            "document": ["document", "analyze", "review", "risk", "clause", "liability"],
            "pdf": ["pdf", "upload", "file"],
        }
        
        # Detect category
        support_score = 0
        document_score = 0
        
        for category, keywords in support_keywords.items():
            support_score += sum(1 for kw in keywords if kw in user_input_lower)
        
        for category, keywords in document_keywords.items():
            document_score += sum(1 for kw in keywords if kw in user_input_lower)
        
        trace_intent = time.time() * 1000
        
        # Determine agent
        if document_score > support_score and document_score > 0:
            recommended_agent = "documents"
            confidence = min(0.95, (document_score / 3.0))
            category = "Document Review"
        else:
            recommended_agent = "support"
            confidence = min(0.95, (support_score / 3.0)) if support_score > 0 else 0.60
            category = "IT Support"
        
        trace_scoring = time.time() * 1000
        
        return {
            "category": category,
            "recommended_agent": recommended_agent,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().isoformat(),
            "trace": {
                "intent_detected_at_ms": round(trace_intent - trace_start, 2),
                "scoring_completed_at_ms": round(trace_scoring - trace_start, 2),
            }
        }

# ============================================================================
# AGENT SCORING ENGINE (MCP DECISION MAKER)
# ============================================================================
class AgentScorer:
    """Scores all agents and selects the best one"""
    
    @staticmethod
    def score_agents(intent: Dict, user_input: str) -> Dict:
        """
        Score all agents based on 6 factors
        """
        scoring_start = time.time() * 1000
        
        recommended = intent["recommended_agent"]
        
        scores = {}
        
        for agent_key, agent_info in AGENTS.items():
            # 1. Capability Match (0-1)
            is_recommended = 1.0 if agent_key == recommended else 0.5
            
            # 2. Historical Success (mock: 0.85-0.98)
            success_rate = 0.95 if agent_key == recommended else 0.80
            
            # 3. Load Factor (mock: current availability)
            load_factor = 0.95
            
            # 4. Specialization (0-1)
            specialization = 0.98 if agent_key == recommended else 0.65
            
            # 5. Policy Compliance (0-1)
            policy_compliance = 1.0
            
            # 6. User Preference (mock: 0.85)
            user_preference = 0.88
            
            # Calculate final score
            weights = {
                "capability": 0.25,
                "success_rate": 0.20,
                "load_factor": 0.10,
                "specialization": 0.25,
                "policy": 0.10,
                "preference": 0.10
            }
            
            final_score = (
                is_recommended * weights["capability"] +
                success_rate * weights["success_rate"] +
                load_factor * weights["load_factor"] +
                specialization * weights["specialization"] +
                policy_compliance * weights["policy"] +
                user_preference * weights["preference"]
            )
            
            scores[agent_key] = {
                "agent_name": agent_info["name"],
                "capability_match": round(is_recommended, 2),
                "success_rate": round(success_rate, 2),
                "load_factor": round(load_factor, 2),
                "specialization": round(specialization, 2),
                "policy_compliance": round(policy_compliance, 2),
                "user_preference": round(user_preference, 2),
                "final_score": round(final_score, 2),
            }
        
        scoring_done = time.time() * 1000
        
        # Select best agent
        best_agent = max(scores.items(), key=lambda x: x[1]["final_score"])
        
        return {
            "selected_agent_key": best_agent[0],
            "selected_agent_name": best_agent[1]["agent_name"],
            "selected_score": best_agent[1]["final_score"],
            "all_scores": scores,
            "trace": {
                "scoring_completed_at_ms": round(scoring_done - scoring_start, 2),
            }
        }

# ============================================================================
# AGENT EXECUTORS
# ============================================================================
class AgentExecutor:
    """Routes requests to appropriate agent"""
    
    @staticmethod
    def execute_support_request(user_input: str, request_id: str) -> Dict:
        """Send to Support Agent"""
        try:
            response = requests.post(
                f"{SUPPORT_API}/it-support/text",
                json={
                    "ticket_id": request_id,
                    "message": user_input
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "agent": "Customer Support Agent"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Support Agent returned {response.status_code}",
                    "agent": "Customer Support Agent"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "error": "Cannot connect to Support Agent (port 8000). Is it running?",
                "agent": "Customer Support Agent"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": "Customer Support Agent"
            }
    
    @staticmethod
    def execute_document_request(user_input: str, request_id: str, uploaded_file=None) -> Dict:
        """Send to Document Agent"""
        try:
            if uploaded_file is None:
                return {
                    "status": "error",
                    "error": "Document Agent requires a PDF file",
                    "agent": "Document Review Agent"
                }
            
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            response = requests.post(
                f"{DOCUMENT_API}/review",
                files=files,
                timeout=120
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "agent": "Document Review Agent"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Document Agent returned {response.status_code}",
                    "agent": "Document Review Agent"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "error": "Cannot connect to Document Agent (port 8001). Is it running?",
                "agent": "Document Review Agent"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": "Document Review Agent"
            }

# ============================================================================
# AGENT STATUS CHECKER
# ============================================================================
def check_agent_status():
    """Check if agents are running"""
    status = {}
    for agent_key, agent_info in AGENTS.items():
        try:
            response = requests.get(
                f"http://127.0.0.1:{agent_info['port']}/health",
                timeout=2
            )
            status[agent_key] = "🟢 Online" if response.status_code == 200 else "🔴 Offline"
        except:
            status[agent_key] = "🔴 Offline"
    return status

# ============================================================================
# UI COMPONENTS
# ============================================================================
def display_decision_tree(intent: Dict, scores: Dict):
    """Display the MCP decision-making process"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧠 MCP Decision Analysis")
        
        # Step 1: Intent Detection
        with st.container(border=True):
            st.markdown("**Step 1️⃣: Intent Detection**")
            st.markdown(f"**Category Detected:** {intent['category']}")
            st.markdown(f"**Confidence:** {intent['confidence'] * 100:.0f}%")
        
        # Step 2: Agent Scoring
        with st.container(border=True):
            st.markdown("**Step 2️⃣: Agent Scoring (6 Factors)**")
            
            selected_agent_key = scores["selected_agent_key"]
            selected_scores = scores["all_scores"][selected_agent_key]
            
            st.markdown(f"### ✅ Selected: {scores['selected_agent_name']}")
            st.markdown(f"**Final Score:** `{scores['selected_score']:.2f}` / 1.00")
            
            # Show scoring breakdown
            with st.expander("📊 Scoring Breakdown"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Capability Match", f"{selected_scores['capability_match']:.0%}")
                    st.metric("Success Rate", f"{selected_scores['success_rate']:.0%}")
                    st.metric("Load Factor", f"{selected_scores['load_factor']:.0%}")
                with col_b:
                    st.metric("Specialization", f"{selected_scores['specialization']:.0%}")
                    st.metric("Policy Compliance", f"{selected_scores['policy_compliance']:.0%}")
                    st.metric("User Preference", f"{selected_scores['user_preference']:.0%}")
    
    with col2:
        st.subheader("🤖 Other Agents Considered")
        
        for agent_key, agent_info in AGENTS.items():
            if agent_key != selected_agent_key:
                agent_scores = scores["all_scores"][agent_key]
                with st.container(border=True):
                    st.markdown(f"**{agent_info['name']}**")
                    st.markdown(f"Score: `{agent_scores['final_score']:.2f}` / 1.00")
                    st.markdown(f"_Why not selected: Lower specialization match ({agent_scores['specialization']:.0%})_")

def display_agent_response(response: Dict):
    """Display the agent's response"""
    
    if response["status"] == "error":
        st.error(f"❌ {response['agent']} Error: {response['error']}")
        return
    
    st.success(f"✅ Response from {response['agent']}")
    
    data = response.get("data", {})
    
    # Support Agent Response
    if "support" in response["agent"].lower():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", data.get("status", "N/A"))
        with col2:
            st.metric("Priority", data.get("priority", "N/A"))
        with col3:
            st.metric("Ticket ID", data.get("ticket_id", "N/A")[:8])
        
        with st.container(border=True):
            st.markdown("**📋 Solution Provided:**")
            st.markdown(data.get("solution", "No solution provided"))
        
        if "analysis" in data:
            with st.expander("📊 Detailed Analysis"):
                st.json(data["analysis"])
    
    # Document Agent Response
    elif "document" in response["agent"].lower():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_level = data.get("risk_level", "Unknown")
            st.metric("Risk Level", risk_level)
        
        with col2:
            risk_score = data.get("risk_score", 0)
            st.metric("Risk Score", f"{risk_score}/100")
        
        with col3:
            status = data.get("status", "N/A")
            st.metric("Status", status)
        
        # Clauses
        if "clauses" in data:
            with st.container(border=True):
                st.markdown("**📄 Clause Analysis:**")
                for clause in data["clauses"]:
                    with st.expander(f"📌 {clause.get('clause_name', 'Clause')} - {clause.get('status', 'OK')}"):
                        st.write(clause.get("description", ""))
                        if clause.get("issue"):
                            st.warning(f"⚠️ {clause.get('issue')}")
        
        # Recommendations
        if "recommendations" in data:
            with st.container(border=True):
                st.markdown("**💡 Recommendations:**")
                for i, rec in enumerate(data["recommendations"], 1):
                    st.markdown(f"{i}. {rec}")

def display_timeline(intent: Dict, scores: Dict):
    """Display processing timeline"""
    
    st.subheader("⏱️ Processing Timeline")
    
    total_time = (
        intent["trace"].get("intent_detected_at_ms", 0) +
        intent["trace"].get("scoring_completed_at_ms", 0) +
        scores["trace"].get("scoring_completed_at_ms", 0)
    )
    
    timeline_data = [
        ("🔍 Request Received", 0),
        ("🧠 Intent Detection", intent["trace"].get("intent_detected_at_ms", 0)),
        ("🤖 Agent Scoring", intent["trace"].get("scoring_completed_at_ms", 0)),
        ("✅ Decision Made", total_time),
    ]
    
    # Display timeline
    col1, col2 = st.columns(2)
    
    with col1:
        for event, time_ms in timeline_data:
            st.markdown(f"`{time_ms:6.2f}ms` → {event}")
    
    with col2:
        st.metric("Total Time", f"{total_time:.2f}ms")

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    # Header
    st.markdown("""
    # 🧠 MCP Unified Agent System
    
    *One interface. Intelligent routing. Complete transparency.*
    
    ---
    """)
    
    # Sidebar - Agent Status & Info
    with st.sidebar:
        st.markdown("## 📊 System Status")
        
        agent_status = check_agent_status()
        for agent_key, status in agent_status.items():
            st.markdown(f"**{AGENTS[agent_key]['name']}:** {status}")
        
        st.markdown("---")
        st.markdown("## 📖 How It Works")
        st.markdown("""
        1. **You submit a request** (text or document)
        2. **MCP analyzes the intent** (intent detection)
        3. **MCP scores all agents** (6-factor evaluation)
        4. **Best agent is selected** and routes request
        5. **Agent processes** and returns result
        6. **You see everything** - decision + solution
        """)
        
        st.markdown("---")
        st.markdown("## 🔧 Settings")
        show_trace = st.checkbox("Show Detailed Timeline", value=True)
        show_scores = st.checkbox("Show Agent Scoring", value=True)
    
    # Main Content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📝 Describe Your Problem or Task")
        st.markdown("_I need help with... OR I want to review..._")
        
        user_input = st.text_area(
            "What do you need?",
            placeholder="Example: My VPN connection keeps dropping\nOR: Review this contract for risks",
            height=120,
            label_visibility="collapsed"
        )
    
    with col2:
        # File upload option
        st.markdown("## 📎 Upload File (Optional)")
        uploaded_file = st.file_uploader(
            "Choose a PDF to review",
            type=["pdf"],
            label_visibility="collapsed"
        )
    
    # Submit Button
    col1, col2, col3 = st.columns(3)
    with col1:
        submit_button = st.button("🚀 Submit Request", use_container_width=True, type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        st.empty()
    
    if clear_button:
        st.session_state.conversation_history = []
        st.session_state.last_decision = None
        st.session_state.agent_response = None
        st.rerun()
    
    # Process Request
    if submit_button and user_input.strip():
        request_id = str(uuid.uuid4())[:8]
        
        with st.spinner("🧠 MCP analyzing your request..."):
            # Step 1: Detect Intent
            intent = IntentDetector.detect_intent(user_input)
            
            # Step 2: Score Agents
            scores = AgentScorer.score_agents(intent, user_input)
            
            # Step 3: Execute Agent
            selected_agent = scores["selected_agent_key"]
            
            if selected_agent == "support":
                agent_response = AgentExecutor.execute_support_request(user_input, request_id)
            else:
                agent_response = AgentExecutor.execute_document_request(
                    user_input, request_id, uploaded_file
                )
            
            # Store in session
            st.session_state.last_decision = {
                "intent": intent,
                "scores": scores,
                "response": agent_response,
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id
            }
            
            st.session_state.conversation_history.append({
                "user_input": user_input,
                "decision": st.session_state.last_decision,
                "timestamp": datetime.now().isoformat()
            })
        
        # Display Results
        st.markdown("---")
        
        # Decision Tree
        if show_scores:
            display_decision_tree(intent, scores)
            st.markdown("---")
        
        # Agent Response
        st.markdown("## 🎯 Agent Response")
        display_agent_response(agent_response)
        
        # Timeline
        if show_trace:
            st.markdown("---")
            display_timeline(intent, scores)
        
        st.markdown("---")
        st.success("✅ Request processed successfully!")
    
    # History
    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("## 📜 Request History")
        
        with st.expander(f"📋 {len(st.session_state.conversation_history)} requests"):
            for i, entry in enumerate(reversed(st.session_state.conversation_history), 1):
                decision = entry["decision"]
                agent_name = decision["scores"]["selected_agent_name"]
                user_text = entry["user_input"][:50] + "..." if len(entry["user_input"]) > 50 else entry["user_input"]
                
                st.markdown(f"**{i}. {user_text}**")
                st.caption(f"→ Routed to: {agent_name} | Time: {entry['timestamp']}")

if __name__ == "__main__":
    main()
