"""
MCP UNIFIED AGENT SYSTEM
Horizontal Timeline + Results + Chat Interface

User types → Full-screen timeline animation → Results displayed → Continue or home
"""

import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, List

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
    initial_sidebar_state="collapsed"
)

# ============================================================================
# SESSION STATE
# ============================================================================
if "page" not in st.session_state:
    st.session_state.page = "home"  # home, processing, results
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "history" not in st.session_state:
    st.session_state.history = []

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
# TIMELINE VISUALIZATION
# ============================================================================
def show_horizontal_timeline(steps: List[Dict]) -> None:
    """Display horizontal animated timeline (full-screen style)"""
    
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
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    """
    
    for i in range(len(steps)):
        delay = i * 0.15
        timeline_html += f"""
        .timeline-step:nth-child({i+1}) {{
            animation-delay: {delay}s;
        }}
        """
    
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
            position: relative;
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
            0%, 100% {
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
            }
            50% {
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
            }
        }
        
        @keyframes pulse-active {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
            }
            50% {
                box-shadow: 0 0 0 15px rgba(245, 158, 11, 0);
            }
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
            <div class="step-label">{step.get("label", "Step")}</div>
            <div class="step-detail">{step.get("detail", "")}</div>
            <div class="step-time">{step.get("time", "")}</div>
        </div>
        """
    
    timeline_html += """
        </div>
    </div>
    """
    
    st.html(timeline_html)

# ============================================================================
# DISPLAY PAGES
# ============================================================================

def show_home_page():
    """Home page with chat-like input"""
    st.markdown("# 🧠 MCP Unified Agent System")
    st.markdown("*One interface. Intelligent routing. Complete transparency.*")
    
    st.markdown("---")
    
    # Input area
    st.markdown("## What do you need help with?")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "Input",
            placeholder="Example: My VPN connection keeps dropping\nOR: Please review this PDF contract",
            height=150,
            label_visibility="collapsed",
            key="input_text"
        )
    
    with col2:
        st.markdown("### 📎 Attach")
        uploaded_file = st.file_uploader(
            "PDF",
            type=["pdf"],
            label_visibility="collapsed",
            key="input_file"
        )
    
    # Submit
    st.markdown("---")
    col1, col2 = st.columns([2, 8])
    
    with col1:
        if st.button("� Send", use_container_width=True, type="primary", key="submit"):
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

def show_results_page():
    """Results page with timeline + response + chat bar"""
    result_data = st.session_state.current_result
    user_input = result_data["input"]
    uploaded_file = result_data["file"]
    request_id = result_data["request_id"]
    start_time = result_data["start_time"]
    
    # ========== HORIZONTAL TIMELINE ==========
    intent = detect_intent(user_input)
    
    timeline_steps = [
        {"label": "Input", "detail": "Request received", "status": "completed", "time": "0ms"},
        {"label": "MCP Analysis", "detail": f"{intent['category']}", "status": "completed", "time": f"{int((time.time() - start_time) * 1000)}ms"},
        {"label": "Agent", "detail": f"{intent['agent_name']}", "status": "active", "time": f"{int((time.time() - start_time) * 1000)}ms"},
    ]
    
    show_horizontal_timeline(timeline_steps)
    
    # ========== EXECUTE AGENT ==========
    with st.spinner(f"🔄 Processing with {intent['agent_name']}..."):
        if intent["agent"] == "support":
            response = execute_support(user_input, request_id)
        else:
            response = execute_document(user_input, request_id, uploaded_file)
        
        execution_time = (time.time() - start_time) * 1000
    
    # ========== UPDATE TIMELINE WITH RESULTS ==========
    if response["status"] == "success":
        completion_timeline = [
            {"label": "Input", "detail": "Request received", "status": "completed", "time": "0ms"},
            {"label": "MCP Analysis", "detail": f"{intent['category']}", "status": "completed", "time": f"{int(execution_time * 0.2)}ms"},
            {"label": "Agent", "detail": f"{intent['agent_name']}", "status": "completed", "time": f"{int(execution_time * 0.5)}ms"},
            {"label": "Processing", "detail": "Completed", "status": "completed", "time": f"{int(execution_time * 0.8)}ms"},
            {"label": "Results", "detail": "Ready", "status": "completed", "time": f"{int(execution_time)}ms"},
        ]
        
        show_horizontal_timeline(completion_timeline)
        st.success("✅ Request processed successfully")
        
        data = response["data"]
        
        # ========== DISPLAY RESPONSE ==========
        if intent["agent"] == "support":
            st.markdown("---")
            st.markdown("## 📋 Support Response")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                status = data.get("status", "N/A")
                st.metric("Status", f"{'✅' if status == 'Resolved' else '⏳'} {status}")
            with col2:
                priority = data.get("priority", "N/A")
                priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
                st.metric("Priority", f"{priority_icon} {priority}")
            with col3:
                ticket_id = data.get("ticket_id", "")[:8]
                st.metric("Ticket ID", ticket_id)
            
            st.markdown("---")
            with st.container(border=True):
                st.markdown("### 💡 Solution")
                st.markdown(data.get("solution", "No solution provided"))
            
            if "recommendations" in data and data["recommendations"]:
                st.markdown("---")
                st.markdown("### 💡 Recommendations")
                recs = data["recommendations"]
                if isinstance(recs, list):
                    for rec in recs:
                        st.markdown(f"• {rec}")
            
            if "analysis" in data and data["analysis"]:
                with st.expander("📊 Technical Analysis"):
                    if isinstance(data["analysis"], dict):
                        st.json(data["analysis"])
                    else:
                        st.markdown(data["analysis"])
        
        else:  # Document Agent
            st.markdown("---")
            st.markdown("## 📄 Document Review")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Doc Type", data.get("document_type", "Unknown"))
            with col2:
                risk_level = data.get("risk_level", "Unknown")
                risk_icon = {"High": "⚠️", "Medium": "⚠️", "Low": "✅"}.get(risk_level, "❓")
                st.metric("Risk Level", f"{risk_icon} {risk_level}")
            with col3:
                risk_score = data.get("risk_score", 0)
                st.metric("Risk Score", f"{risk_score}/100")
            
            if "clause_analysis" in data and data["clause_analysis"]:
                st.markdown("---")
                st.markdown("### 📋 Clauses")
                clauses = data["clause_analysis"]
                if isinstance(clauses, dict):
                    for clause_name, clause_data in clauses.items():
                        with st.expander(f"📌 {clause_name}"):
                            if isinstance(clause_data, dict):
                                st.json(clause_data)
                            else:
                                st.markdown(clause_data)
            
            if "recommendations" in data and data["recommendations"]:
                st.markdown("---")
                st.markdown("### 💡 Recommendations")
                recs = data["recommendations"]
                if isinstance(recs, list):
                    for rec in recs:
                        st.markdown(f"• {rec}")
        
        # Developer view
        with st.expander("🔍 Full JSON Response"):
            st.json(data)
    
    else:
        st.error(f"❌ Error: {response.get('error', 'Unknown error')}")
    
    # ========== BOTTOM CHAT-LIKE BAR ==========
    st.markdown("---")
    st.markdown("### � Continue or Start New")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.current_result = None
            st.rerun()
    
    with col2:
        if st.button("🔄 New Request", use_container_width=True):
            st.session_state.current_result = None
            st.session_state.page = "home"
            st.rerun()

# ============================================================================
# MAIN APP ROUTING
# ============================================================================
if st.session_state.page == "home":
    show_home_page()
elif st.session_state.page == "results":
    show_results_page()

            with col1:
                status = data.get("status", "N/A")
                if status == "Resolved":
                    st.markdown("### ✅ Status")
                    st.markdown(f"**{status}**")
                else:
                    st.markdown("### ⏳ Status")
                    st.markdown(f"**{status}**")
            with col2:
                priority = data.get("priority", "N/A")
                if priority == "High":
                    st.markdown("### 🔴 Priority")
                    st.markdown(f"**{priority}**")
                elif priority == "Medium":
                    st.markdown("### 🟡 Priority")
                    st.markdown(f"**{priority}**")
                else:
                    st.markdown("### 🟢 Priority")
                    st.markdown(f"**{priority}**")
            with col3:
                ticket_id = data.get("ticket_id", "")[:8]
                st.markdown("### 🎫 Ticket ID")
                st.markdown(f"**{ticket_id}**")
            
            # Solution
            st.markdown("---")
            with st.container(border=True):
                st.markdown("### 📋 Solution & Steps")
                solution = data.get("solution", "No solution provided")
                st.markdown(solution)
            
            # Decision/Reasoning
            if "decision" in data and data["decision"]:
                st.markdown("---")
                with st.expander("🧠 Decision Reasoning"):
                    st.markdown(data["decision"])
            
            # Reason
            if "reason" in data and data["reason"]:
                st.markdown("---")
                with st.expander("💡 Why This Solution"):
                    st.markdown(data["reason"])
            
            # Answer (alternative field)
            if "answer" in data and data["answer"]:
                st.markdown("---")
                with st.container(border=True):
                    st.markdown("### 🎯 Answer")
                    st.markdown(data["answer"])
            
            # Severity
            if "severity" in data and data["severity"]:
                st.markdown("---")
                st.warning(f"⚠️ **Severity Level:** {data['severity']}")
            
            # Category
            if "category" in data and data["category"]:
                st.markdown("---")
                st.info(f"📂 **Category:** {data['category']}")
            
            # Steps (if available)
            if "steps" in data and data["steps"]:
                st.markdown("---")
                st.markdown("### 📍 Step-by-Step Instructions")
                steps = data["steps"]
                if isinstance(steps, list):
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"**Step {i}:** {step}")
                else:
                    st.markdown(steps)
            
            # Detailed Analysis
            if "analysis" in data and data["analysis"]:
                st.markdown("---")
                with st.expander("📊 Detailed Technical Analysis"):
                    analysis = data["analysis"]
                    if isinstance(analysis, dict):
                        st.json(analysis)
                    else:
                        st.markdown(analysis)
            
            # Recommendations
            if "recommendations" in data and data["recommendations"]:
                st.markdown("---")
                st.markdown("### 💡 Additional Recommendations")
                recs = data["recommendations"]
                if isinstance(recs, list):
                    for i, rec in enumerate(recs, 1):
                        st.markdown(f"• {rec}")
                elif isinstance(recs, dict):
                    for key, val in recs.items():
                        st.markdown(f"**{key}:** {val}")
            
            # Full JSON (developer view)
            st.markdown("---")
            with st.expander("🔍 Full Response JSON (Developer View)"):
                st.json(data)
        
        # Document Agent Response
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Document Type", data.get("document_type", "Unknown"))
            with col2:
                risk_level = data.get("risk_level", "Unknown")
                if risk_level == "High":
                    st.markdown("### ⚠️ Risk Level")
                    st.markdown(f"**{risk_level}**")
                elif risk_level == "Medium":
                    st.markdown("### ⚠️ Risk Level")
                    st.markdown(f"**{risk_level}**")
                else:
                    st.markdown("### ✅ Risk Level")
                    st.markdown(f"**{risk_level}**")
            with col3:
                risk_score = data.get("risk_score", 0)
                st.metric("Risk Score", f"{risk_score}/100")
            
            # Clause Analysis - Enhanced Display
            if "clause_analysis" in data and data["clause_analysis"]:
                st.markdown("---")
                st.markdown("### 📄 Clause-by-Clause Analysis")
                
                clauses = data["clause_analysis"]
                if isinstance(clauses, dict):
                    for i, (clause_name, clause_data) in enumerate(clauses.items(), 1):
                        with st.container(border=True):
                            # Clause header with status
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.markdown(f"**Clause {i}: {clause_name}**")
                            with col2:
                                status = clause_data.get("status", "Unknown")
                                if status == "Found":
                                    st.markdown("✅ Found")
                                else:
                                    st.markdown("⚠️ Issue")
                            with col3:
                                sim = clause_data.get("similarity_score", 0)
                                if isinstance(sim, (int, float)):
                                    st.markdown(f"Match: {sim:.0%}")
                            
                            # Clause description
                            description = clause_data.get("description", "")
                            if description:
                                st.markdown(f"**Description:** {description}")
                            
                            # Snippet
                            snippet = clause_data.get("snippet", "")
                            if snippet:
                                st.markdown(f"**Preview:** _{snippet}_")
                            
                            # Issue details
                            issue = clause_data.get("issue")
                            if issue:
                                st.warning(f"⚠️ **Issue Identified:** {issue}")
                            
                            # Risk assessment
                            clause_risk = clause_data.get("risk_assessment")
                            if clause_risk:
                                st.info(f"📊 **Risk Assessment:** {clause_risk}")
                
                elif isinstance(clauses, list):
                    for i, clause in enumerate(clauses, 1):
                        with st.container(border=True):
                            st.markdown(f"**Clause {i}: {clause.get('clause_name', 'Unknown')}**")
                            if clause.get('description'):
                                st.markdown(f"**Description:** {clause.get('description')}")
                            if clause.get('status'):
                                st.markdown(f"**Status:** {clause.get('status')}")
                            if clause.get('issue'):
                                st.warning(f"⚠️ {clause.get('issue')}")
            
            # Explanation/Detailed Analysis
            if "explanation" in data and data["explanation"]:
                st.markdown("---")
                with st.expander("📊 Detailed Analysis Explanation"):
                    st.markdown(data["explanation"])
            
            # Suggestions/Recommendations - Enhanced Display
            if "suggestions" in data and data["suggestions"]:
                st.markdown("---")
                st.markdown("### 💡 Recommendations & Suggested Changes")
                with st.container(border=True):
                    suggestions = data["suggestions"]
                    if isinstance(suggestions, dict):
                        for clause, suggestion in suggestions.items():
                            st.markdown(f"**{clause}:**")
                            st.markdown(f"> {suggestion}")
                            st.divider()
                    elif isinstance(suggestions, list):
                        for i, suggestion in enumerate(suggestions, 1):
                            st.markdown(f"**{i}. {suggestion}**")
            
            # Support Ticket (if high risk)
            if "support_ticket" in data and data["support_ticket"]:
                st.markdown("---")
                st.info("🔔 **High Risk Alert** - Support Ticket Has Been Created")
                with st.expander("📋 Support Ticket Details"):
                    ticket = data["support_ticket"]
                    if isinstance(ticket, dict):
                        st.json(ticket)
                    else:
                        st.write(ticket)
            
            # Summary Section
            if "summary" in data and data["summary"]:
                st.markdown("---")
                with st.container(border=True):
                    st.markdown("### 📌 Summary")
                    st.markdown(data["summary"])
            
            # Full JSON view (for debugging)
            st.markdown("---")
            with st.expander("� Full Analysis JSON (Developer View)"):
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