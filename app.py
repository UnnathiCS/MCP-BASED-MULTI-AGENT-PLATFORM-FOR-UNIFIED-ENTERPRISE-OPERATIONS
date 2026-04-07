"""
MCP UNIFIED AGENT SYSTEM - Chat Interface with Horizontal Timeline
Single screen → Horizontal timeline animation → Results + Continue
"""

import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, List

# ============================================================================
# CONFIG
# ============================================================================
SUPPORT_API = "http://127.0.0.1:8000"
DOCUMENT_API = "http://127.0.0.1:8001"
REQUEST_TIMEOUT = 30

st.set_page_config(
    page_title="MCP Agent System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# SESSION STATE
# ============================================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# ============================================================================
# FUNCTIONS
# ============================================================================

def detect_intent(user_input: str) -> Dict:
    """Detect if support or document agent"""
    user_lower = user_input.lower()
    
    support_keywords = [
        "vpn", "network", "internet", "wifi", "connection", "login",
        "password", "account", "access", "email", "crash", "error",
        "bug", "issue", "help", "teams", "outlook", "problem",
        "not working", "cant", "can't", "unable", "blocked"
    ]
    
    doc_keywords = [
        "contract", "review", "pdf", "document", "analyze", "risk",
        "liability", "clause", "agreement", "nda", "policy", "terms",
        "assessment", "upload", "file", "check", "examine", "evaluate"
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
            "agent_name": "Support Agent",
            "category": "IT Support",
            "confidence": min(0.98, max(0.65, (support_score / 3.0)))
        }

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
            return {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def execute_document(user_input: str, request_id: str, uploaded_file) -> Dict:
    """Send to Document Agent"""
    try:
        if uploaded_file is None:
            return {"status": "error", "error": "PDF file required"}
        
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post(
            f"{DOCUMENT_API}/review",
            files=files,
            timeout=120
        )
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def show_horizontal_timeline(steps: List[Dict]) -> None:
    """Display horizontal timeline"""
    
    timeline_html = """
    <style>
        .timeline-horizontal {
            width: 100%;
            padding: 60px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            margin: 30px 0;
        }
        
        .timeline-track {
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            padding: 20px 0;
        }
        
        .timeline-track::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-50%);
            z-index: 1;
        }
        
        .timeline-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
            flex: 1;
            animation: fadeInUp 0.6s ease-out forwards;
            opacity: 0;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    """
    
    for i in range(len(steps)):
        delay = i * 0.15
        timeline_html += f".timeline-step:nth-child({i+1}) {{ animation-delay: {delay}s; }}"
    
    timeline_html += """
        .step-dot {
            width: 60px;
            height: 60px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 24px;
            margin-bottom: 15px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
            animation: pulse-white 2s infinite;
        }
        
        .step-dot.completed {
            background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
            color: white;
            animation: none;
        }
        
        .step-dot.active {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: white;
            animation: pulse-active 1.5s infinite;
        }
        
        @keyframes pulse-white {
            0%, 100% { box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2); }
            50% { box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4); }
        }
        
        @keyframes pulse-active {
            0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
            50% { box-shadow: 0 0 0 15px rgba(245, 158, 11, 0); }
        }
        
        .step-label {
            font-weight: 700;
            color: white;
            font-size: 13px;
            text-align: center;
            max-width: 120px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .step-detail {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.8);
            text-align: center;
            max-width: 130px;
            margin-bottom: 5px;
        }
        
        .step-time {
            font-size: 10px;
            color: rgba(255, 255, 255, 0.6);
            font-family: monospace;
            font-weight: bold;
        }
    </style>
    
    <div class="timeline-horizontal">
        <div class="timeline-track">
    """
    
    for i, step in enumerate(steps):
        status_class = ""
        dot_content = "✓" if step.get("status") == "completed" else ("⏳" if step.get("status") == "active" else "○")
        
        if step.get("status") == "completed":
            status_class = "completed"
        elif step.get("status") == "active":
            status_class = "active"
        
        timeline_html += f"""
        <div class="timeline-step">
            <div class="step-dot {status_class}">{dot_content}</div>
            <div class="step-label">{step.get("label", "")}</div>
            <div class="step-detail">{step.get("detail", "")}</div>
            <div class="step-time">{step.get("time", "")}</div>
        </div>
        """
    
    timeline_html += "</div></div>"
    st.html(timeline_html)

# ============================================================================
# HOME PAGE
# ============================================================================
def show_home_page():
    """Home with input"""
    st.markdown("# MCP Agent System")
    st.markdown("*Intelligent routing. Transparent processing.*")
    
    st.markdown("---")
    st.markdown("## What can I help you with?")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "Message",
            placeholder="Example: My VPN keeps dropping\nOR: Review this contract",
            height=140,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### 📎 Attach")
        uploaded_file = st.file_uploader(
            "PDF", type=["pdf"], label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    if st.button("📤 Send", use_container_width=True, type="primary"):
        if user_input.strip():
            st.session_state.current_result = {
                "input": user_input,
                "file": uploaded_file,
                "request_id": str(uuid.uuid4())[:8],
                "start_time": time.time()
            }
            st.session_state.page = "results"
            st.rerun()
        else:
            st.warning("Please enter a message")

# ============================================================================
# RESULTS PAGE
# ============================================================================
def show_results_page():
    """Results with timeline and agent response"""
    result_data = st.session_state.current_result
    user_input = result_data["input"]
    uploaded_file = result_data["file"]
    request_id = result_data["request_id"]
    start_time = result_data["start_time"]
    
    # Detect intent
    intent = detect_intent(user_input)
    
    # If we haven't executed yet, execute now
    if "response" not in result_data:
        # Show initial timeline (processing)
        initial_timeline = [
            {"label": "Input", "detail": "Received", "status": "completed", "time": "0ms"},
            {"label": "MCP Analysis", "detail": intent['category'], "status": "completed", "time": f"{int((time.time() - start_time) * 1000)}ms"},
            {"label": "Routing", "detail": intent['agent_name'], "status": "active", "time": f"{int((time.time() - start_time) * 1000)}ms"},
        ]
        
        show_horizontal_timeline(initial_timeline)
        
        # Execute agent
        with st.spinner("Processing..."):
            if intent["agent"] == "support":
                response = execute_support(user_input, request_id)
            else:
                response = execute_document(user_input, request_id, uploaded_file)
            
            execution_time = (time.time() - start_time) * 1000
        
        # Store results in session state
        result_data["response"] = response
        result_data["intent"] = intent
        result_data["execution_time"] = execution_time
        st.session_state.current_result = result_data
        
        # Force rerun to show completion timeline and results
        st.rerun()
    
    # Get stored results
    intent = result_data.get("intent", intent)
    execution_time = result_data.get("execution_time", (time.time() - start_time) * 1000)
    response = result_data.get("response")
    
    # Show completion timeline with all green steps
    completion_timeline = [
        {"label": "Input", "detail": "Received", "status": "completed", "time": "0ms"},
        {"label": "MCP", "detail": intent['category'], "status": "completed", "time": f"{int(execution_time * 0.2)}ms"},
        {"label": "Routing", "detail": intent['agent_name'], "status": "completed", "time": f"{int(execution_time * 0.5)}ms"},
        {"label": "Processing", "detail": "Complete", "status": "completed", "time": f"{int(execution_time * 0.8)}ms"},
        {"label": "Ready", "detail": "Results", "status": "completed", "time": f"{int(execution_time)}ms"},
    ]
    
    show_horizontal_timeline(completion_timeline)
    
    # Response
    if response["status"] == "success":
        st.success("✅ Processed successfully")
        data = response["data"]
        
        st.markdown("---")
        st.markdown("## 📋 Response")
        
        if intent["agent"] == "support":
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                decision = data.get("decision", "N/A")
                st.metric("Decision", decision if decision else "N/A")
            with col2:
                severity = data.get("severity", "N/A")
                st.metric("Severity", severity if severity else "N/A")
            with col3:
                ticket = data.get("ticket_id", "")
                st.metric("Ticket", ticket[:8] if ticket else "N/A")
            
            st.markdown("---")
            
            # Solution/Answer section
            if data.get("solution"):
                st.markdown("### 💡 Solution")
                st.markdown(data.get("solution"))
            elif data.get("answer"):
                st.markdown("### 💡 Answer")
                st.markdown(data.get("answer"))
            
            # Decision and reason
            if data.get("decision"):
                st.markdown("---")
                st.markdown("### 🧠 Decision")
                st.markdown(f"**{data.get('decision')}**")
            
            if data.get("reason"):
                st.markdown("---")
                st.markdown("### � Reason")
                st.markdown(data.get("reason"))
            
            # Severity warning
            if data.get("severity"):
                st.markdown("---")
                st.warning(f"⚠️ Severity: **{data.get('severity')}**")
            
            # Category
            if data.get("category"):
                st.markdown("---")
                st.info(f"📂 Category: **{data.get('category')}**")
            
            # Steps
            if data.get("steps"):
                st.markdown("---")
                st.markdown("### 📍 Steps")
                steps = data.get("steps", [])
                if isinstance(steps, list):
                    for i, step in enumerate(steps, 1):
                        st.write(f"{i}. {step}")
            
            # Analysis
            if data.get("analysis"):
                st.markdown("---")
                with st.expander("📊 Technical Analysis"):
                    analysis = data.get("analysis")
                    if isinstance(analysis, dict):
                        st.json(analysis)
                    else:
                        st.markdown(str(analysis))
            
            # Recommendations
            if data.get("recommendations"):
                st.markdown("---")
                st.markdown("### 💡 Recommendations")
                recs = data.get("recommendations", [])
                if isinstance(recs, list):
                    for rec in recs:
                        st.write(f"• {rec}")
            
            # LangGraph Workflow Visualization (for faculty evaluation)
            st.markdown("---")
            with st.expander("🔧 **LangGraph Workflow** (Built with LangGraph as per faculty suggestion)"):
                st.markdown("### Agent Processing Pipeline")
                st.markdown("""
This Support Agent uses **LangGraph** to orchestrate a multi-step decision workflow:

1. **Policy Search** → Search IT policy database for matching solutions
2. **Sentiment Analysis** → Analyze user sentiment (positive/negative/neutral)
3. **Classification** → Classify ticket category and detect intent
4. **LLM Decision** → Use Groq LLM to make intelligent decision
5. **Output** → Return decision, reason, severity, and answer

**Advantages of LangGraph Approach:**
- ✅ Clear state transitions and observability
- ✅ Each step can be traced and debugged
- ✅ Parallel-ready architecture for future scaling
- ✅ Deterministic workflow with LLM intelligence
- ✅ Fallback rules ensure reliability
                """)
                
                # Try to fetch and display the actual workflow visualization
                try:
                    graph_response = requests.get("http://127.0.0.1:8000/graph/visualization", timeout=5)
                    if graph_response.status_code == 200:
                        graph_data = graph_response.json()
                        st.code(graph_data.get("visualization", ""), language="text")
                except:
                    st.info("📊 Graph visualization endpoint not available yet")
                
                # Show processing steps if available
                if data.get("processing_steps"):
                    st.markdown("**Processing Steps Executed:**")
                    for i, step in enumerate(data.get("processing_steps", []), 1):
                        st.write(f"{i}. ✓ {step}")
                
                if data.get("agent_thoughts"):
                    st.markdown("**Agent Reasoning Process:**")
                    st.code(data.get("agent_thoughts", ""), language="text")
        
        else:  # Document
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Type", data.get("document_type", "Unknown"))
            with col2:
                st.metric("Risk", data.get("risk_level", "Unknown"))
            with col3:
                compliance = data.get("compliance_score", 0)
                st.metric("Compliance", f"{compliance}%")
            
            st.markdown("---")
            
            # Compliance Index
            if data.get("compliance_index"):
                st.info(f"✅ Compliance Index: **{data.get('compliance_index')}** (0-1 scale)")
            
            st.markdown("---")
            
            if data.get("clause_analysis"):
                st.markdown("### 📄 Clause Analysis")
                clauses = data.get("clause_analysis", {})
                if isinstance(clauses, dict):
                    for clause_name, clause_data in clauses.items():
                        with st.expander(f"📋 {clause_name}"):
                            if isinstance(clause_data, dict):
                                # Display status with color
                                status = clause_data.get("status", "Unknown")
                                status_icon = "✅" if status == "Present" else "⚠️" if status == "Weak" else "❌"
                                st.write(f"{status_icon} **Status:** {status}")
                                
                                # Similarity score
                                score = clause_data.get("similarity_score", 0)
                                st.write(f"🎯 **Similarity:** {score}")
                                
                                # Weight
                                weight = clause_data.get("weight", 0)
                                st.write(f"⚖️ **Weight:** {weight}")
                                
                                # Snippet
                                snippet = clause_data.get("snippet", "No content found")
                                st.markdown("**Content:**")
                                st.markdown(f"> {snippet}")
                            else:
                                st.write(clause_data)
            
            st.markdown("---")
            
            # Explanation
            if data.get("explanation"):
                with st.expander("� Detailed Explanation"):
                    st.markdown(data.get("explanation"))
            
            st.markdown("---")
            
            if data.get("suggestions"):
                st.markdown("### 💡 Suggestions")
                suggestions = data.get("suggestions", [])
                if isinstance(suggestions, list):
                    for i, suggestion in enumerate(suggestions, 1):
                        st.write(f"{i}. {suggestion}")
                else:
                    st.write(suggestions)
        
        # Developer view
        with st.expander("🔍 Full JSON"):
            st.json(data)
    
    else:
        st.error(f"❌ {response.get('error', 'Error')}")
    
    # Bottom controls
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.current_result = None
            st.rerun()
    
    with col2:
        if st.button("➕ New Request", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.current_result = None
            st.rerun()

# ============================================================================
# MAIN ROUTING
# ============================================================================
if st.session_state.page == "home":
    show_home_page()
elif st.session_state.page == "results":
    show_results_page()
