"""
MCP UNIFIED AGENT SYSTEM
Single Screen - Intelligent Routing - Complete Transparency

User types problem → MCP decides which agent → Agent executes → Show result
"""

import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================
SUPPORT_API = "http://127.0.0.1:8000"
DOCUMENT_API = "http://127.0.0.1:8001"
REQUEST_TIMEOUT = 30

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="MCP Agent System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 MCP Unified Agent System")
st.markdown("*One interface. Intelligent routing. Complete transparency.*")

# ============================================================================
# SESSION STATE
# ============================================================================
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ============================================================================
# AGENT STATUS
# ============================================================================
def check_agent_status():
    """Check if agents are running"""
    status = {}
    
    try:
        r = requests.get(f"{SUPPORT_API}/health", timeout=2)
        status["support"] = "🟢 Online" if r.status_code == 200 else "🔴 Offline"
    except:
        status["support"] = "🔴 Offline"
    
    try:
        r = requests.get(f"{DOCUMENT_API}/health", timeout=2)
        status["documents"] = "🟢 Online" if r.status_code == 200 else "🔴 Offline"
    except:
        status["documents"] = "🔴 Offline"
    
    return status

# ============================================================================
# MCP INTENT DETECTION
# ============================================================================
def detect_intent(user_input: str) -> Dict:
    """
    Analyze user input and determine if it's support or document review
    """
    user_lower = user_input.lower()
    
    # Support keywords
    support_keywords = [
        "vpn", "network", "internet", "wifi", "connection",
        "login", "password", "account", "access", "email",
        "crash", "error", "bug", "issue", "help",
        "teams", "outlook", "problem", "not working",
        "cant", "can't", "unable", "blocked"
    ]
    
    # Document keywords
    doc_keywords = [
        "contract", "review", "pdf", "document", "analyze",
        "risk", "liability", "clause", "agreement", "nda",
        "policy", "terms", "assessment", "upload", "file",
        "check", "examine", "evaluate", "assess"
    ]
    
    support_score = sum(1 for kw in support_keywords if kw in user_lower)
    doc_score = sum(1 for kw in doc_keywords if kw in user_lower)
    
    if doc_score > support_score and doc_score > 0:
        return {
            "agent": "documents",
            "agent_name": "Document Review Agent",
            "category": "Document Analysis",
            "confidence": min(0.98, (doc_score / 3.0))
        }
    else:
        return {
            "agent": "support",
            "agent_name": "Customer Support Agent",
            "category": "IT Support",
            "confidence": min(0.98, max(0.65, (support_score / 3.0)))
        }

# ============================================================================
# EXECUTE SUPPORT REQUEST
# ============================================================================
def execute_support(user_input: str, request_id: str) -> Dict:
    """Send to Support Agent"""
    try:
        response = requests.post(
            f"{SUPPORT_API}/it-support/text",
            json={"ticket_id": request_id, "message": user_input},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "error": f"Agent returned {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot connect to Support Agent (port 8000)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============================================================================
# EXECUTE DOCUMENT REQUEST
# ============================================================================
def execute_document(user_input: str, request_id: str, uploaded_file) -> Dict:
    """Send to Document Agent"""
    try:
        if uploaded_file is None:
            return {"status": "error", "error": "Document Agent requires a PDF file"}
        
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post(
            f"{DOCUMENT_API}/review",
            files=files,
            timeout=120
        )
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "error": f"Agent returned {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot connect to Document Agent (port 8001)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============================================================================
# SIDEBAR - AGENT STATUS & CONTROLS
# ============================================================================
with st.sidebar:
    st.markdown("## 📊 System Status")
    agent_status = check_agent_status()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Support Agent**  \n{agent_status['support']}")
    with col2:
        st.markdown(f"**Document Agent**  \n{agent_status['documents']}")
    
    st.markdown("---")
    
    st.markdown("## 📖 How It Works")
    st.markdown("""
    1. Type your problem or task
    2. MCP analyzes and detects category
    3. Best agent is selected automatically
    4. Agent popup appears with your input
    5. Agent processes and returns output
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_result = None
        st.rerun()

# ============================================================================
# MAIN INPUT SECTION
# ============================================================================
st.markdown("## 📝 Describe Your Problem or Task")

col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_area(
        "What do you need help with?",
        placeholder="Example: My VPN connection keeps dropping\nOR: Please review this contract for risks",
        height=120,
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 📎 Upload (Optional)")
    uploaded_file = st.file_uploader(
        "PDF file",
        type=["pdf"],
        label_visibility="collapsed"
    )

# ============================================================================
# SUBMIT BUTTON
# ============================================================================
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    submit_btn = st.button("🚀 Submit", use_container_width=True, type="primary")

with col2:
    clear_btn = st.button("Clear", use_container_width=True)

if clear_btn:
    user_input = ""
    uploaded_file = None
    st.rerun()

# ============================================================================
# PROCESS REQUEST
# ============================================================================
if submit_btn and user_input.strip():
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # MCP: Detect Intent
    intent = detect_intent(user_input)
    
    # Show MCP Decision
    st.markdown("---")
    st.markdown("## 🧠 MCP Decision")
    
    decision_col1, decision_col2, decision_col3 = st.columns(3)
    
    with decision_col1:
        st.metric("Category Detected", intent["category"])
    
    with decision_col2:
        st.metric("Agent Selected", intent["agent_name"])
    
    with decision_col3:
        st.metric("Confidence", f"{intent['confidence']*100:.0f}%")
    
    # Execute Agent
    st.markdown("---")
    st.markdown(f"## 🤖 {intent['agent_name']}")
    
    with st.spinner(f"🔄 {intent['agent_name']} processing..."):
        if intent["agent"] == "support":
            result = execute_support(user_input, request_id)
        else:
            result = execute_document(user_input, request_id, uploaded_file)
        
        execution_time = (time.time() - start_time) * 1000
    
    # Display Result
    if result["status"] == "error":
        st.error(f"❌ {result['error']}")
    else:
        st.success("✅ Request processed successfully")
        
        data = result["data"]
        
        # Support Agent Response
        if intent["agent"] == "support":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", data.get("status", "N/A"))
            with col2:
                st.metric("Priority", data.get("priority", "N/A"))
            with col3:
                st.metric("Ticket ID", data.get("ticket_id", "")[:8])
            
            with st.container(border=True):
                st.markdown("### 📋 Solution")
                st.markdown(data.get("solution", "No solution provided"))
            
            if "analysis" in data and data["analysis"]:
                with st.expander("📊 Detailed Analysis"):
                    st.json(data["analysis"])
        
        # Document Agent Response
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Document Type", data.get("document_type", "Unknown"))
            with col2:
                st.metric("Risk Level", data.get("risk_level", "Unknown"))
            with col3:
                st.metric("Compliance Score", f"{data.get('compliance_score', 0):.1f}%")
            
            # Clause Analysis
            if "clause_analysis" in data and data["clause_analysis"]:
                st.markdown("### 📄 Clause Analysis")
                with st.container(border=True):
                    for clause_name, clause_data in data["clause_analysis"].items():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            status = clause_data.get("status", "Unknown")
                            similarity = clause_data.get("similarity_score", 0)
                            st.markdown(f"**{clause_name}** - {status} ({similarity:.0%})")
                        with col2:
                            if status == "Found":
                                st.markdown("✅")
                            else:
                                st.markdown("⚠️")
                        
                        snippet = clause_data.get("snippet", "")
                        if snippet:
                            st.caption(f"_{snippet[:100]}..._")
                        
                        issue = clause_data.get("issue")
                        if issue:
                            st.warning(f"⚠️ {issue}")
                        
                        st.divider()
            
            # Explanation
            if "explanation" in data and data["explanation"]:
                with st.expander("📊 Detailed Analysis"):
                    st.markdown(data["explanation"])
            
            # Suggestions
            if "suggestions" in data and data["suggestions"]:
                st.markdown("### 💡 Recommendations")
                with st.container(border=True):
                    for i, suggestion in enumerate(data["suggestions"], 1):
                        st.markdown(f"**{i}. {suggestion}**")
            
            # Support Ticket (if high risk)
            if "support_ticket" in data and data["support_ticket"]:
                st.info("🔔 High Risk Alert - Support Ticket Created")
                with st.expander("Support Ticket Details"):
                    st.json(data["support_ticket"])
            
            # Full JSON view
            with st.expander("📋 Full Analysis JSON"):
                st.json(data)
        
        # Add to history
        st.session_state.history.append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input[:50],
            "agent": intent["agent_name"],
            "status": "success"
        })
        
        st.session_state.last_result = {
            "intent": intent,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Show metrics
        st.markdown("---")
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Processing Time", f"{execution_time:.0f}ms")
        with metric_col2:
            st.metric("Request ID", request_id)
        with metric_col3:
            st.metric("Total Requests", len(st.session_state.history))

# ============================================================================
# HISTORY
# ============================================================================
if st.session_state.history:
    st.markdown("---")
    st.markdown("## 📜 Request History")
    
    with st.expander(f"📋 {len(st.session_state.history)} requests"):
        for i, entry in enumerate(reversed(st.session_state.history), 1):
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.caption(f"**{i}. {entry['input']}**")
            with col2:
                st.caption(f"→ {entry['agent']}")
            with col3:
                st.caption(entry['timestamp'][:19])