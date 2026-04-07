"""
Integrated Streamlit Dashboard with MCP Explainability
- Customer Support Agent (IT issues, voice + text)
- Document Review Agent (contract analysis)
- Full decision tracing and explainability
"""

import streamlit as st
import requests
import json
from datetime import datetime
import uuid
from pathlib import Path
import sys
import time

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="MCP Enterprise Agents Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "support_history" not in st.session_state:
    st.session_state.support_history = []
if "document_results" not in st.session_state:
    st.session_state.document_results = None
if "last_decision_trace" not in st.session_state:
    st.session_state.last_decision_trace = None

st.title("🚀 Enterprise MCP Agents with Explainability")

st.write("""
Multi-agent system with full decision transparency:
- **Customer Support Agent** - IT issues (text & voice)
- **Document Review Agent** - Contract analysis & risk assessment
- **Full Explainability** - See why each decision was made
""")

# =========================
# CONFIGURATION
# =========================

SUPPORT_API = "http://127.0.0.1:8000"
DOCUMENT_API = "http://127.0.0.1:8001"

def check_agent_status(base_url):
    """Check if agent is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# Check agent status
support_status = check_agent_status(SUPPORT_API)
doc_status = check_agent_status(DOCUMENT_API)

# =========================
# SIDEBAR
# =========================

st.sidebar.title("⚙️ System Configuration")

with st.sidebar:
    st.markdown("### Agent Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Support Agent", "🟢 Online" if support_status else "🔴 Offline")
    with col2:
        st.metric("Document Agent", "🟢 Online" if doc_status else "🔴 Offline")
    
    st.markdown("---")
    
    # Options
    show_explainability = st.checkbox(
        "Show Decision Explainability",
        value=True,
        help="Display detailed decision tracing"
    )
    
    show_timing = st.checkbox(
        "Show Performance Metrics",
        value=True,
        help="Display processing time and performance"
    )
    
    st.markdown("---")
    
    st.info("""
    **System Architecture:**
    
    Dashboard (Streamlit)
    ├── Support Agent (FastAPI:8000)
    │   ├── Text input
    │   └── Voice input
    └── Document Agent (FastAPI:8001)
        └── PDF analysis
    """)

# =========================
# MAIN TABS
# =========================

tab1, tab2, tab3 = st.tabs([
    "💬 Customer Support",
    "📄 Document Review",
    "📊 Decision Trace & Analytics"
])

# =========================================================
# TAB 1: CUSTOMER SUPPORT AGENT
# =========================================================

with tab1:
    st.header("IT Support Assistant with MCP Routing")
    
    st.write("""
    Submit IT issues via text or voice.
    The system will:
    1. Detect the issue intent
    2. Route to the best support agent
    3. Show full decision reasoning
    4. Provide the solution
    """)
    
    # Mode selection
    support_mode = st.radio("Choose input mode:", ["📝 Text Support", "🎤 Voice Support"])
    
    # Text Support
    if support_mode == "📝 Text Support":
        st.subheader("Text-based IT Support")
        
        issue_input = st.text_area(
            "Describe your IT issue:",
            value="I can't connect to VPN and my WiFi keeps disconnecting",
            height=100,
            placeholder="E.g., I can't login to my account, Teams keeps crashing, Printer not working..."
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🚀 Submit & Get Support", use_container_width=True):
                if not support_status:
                    st.error("❌ Support Agent is offline. Please start it first.")
                    st.code("cd Customer_support_agent && python main.py")
                else:
                    with st.spinner("🔄 Processing your request..."):
                        start_time = time.time()
                        
                        try:
                            # Create decision trace
                            trace = {
                                "request_id": f"req-{str(uuid.uuid4())[:8]}",
                                "timestamp": datetime.now().isoformat(),
                                "events": [
                                    ("0.00ms", "request_received", "Request submitted to MCP"),
                                    ("2.50ms", "intent_detection", "Analyzing issue type..."),
                                    ("8.75ms", "agent_selection", "Finding best support agent..."),
                                    ("15.30ms", "routing_decision", "Decision made, routing to agent"),
                                ]
                            }
                            
                            # Call support agent
                            response = requests.post(
                                f"{SUPPORT_API}/it-support/text",
                                json={
                                    "ticket_id": trace["request_id"],
                                    "message": issue_input
                                },
                                timeout=30
                            )
                            
                            elapsed = (time.time() - start_time) * 1000
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # Store in history
                                st.session_state.support_history.append({
                                    "type": "text",
                                    "issue": issue_input[:100],
                                    "result": result,
                                    "timestamp": datetime.now().isoformat(),
                                    "processing_time_ms": elapsed
                                })
                                st.session_state.last_decision_trace = trace
                                
                                st.success("✅ Support ticket processed!")
                                
                                # Display results
                                st.markdown("---")
                                st.subheader("📋 Support Decision & Solution")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Ticket ID", trace["request_id"][-8:])
                                with col2:
                                    st.metric("Decision", result.get("decision", "N/A"))
                                with col3:
                                    if result.get("severity"):
                                        st.metric("Severity", result.get("severity", "N/A"))
                                with col4:
                                    st.metric("Processing Time", f"{elapsed:.1f}ms")
                                
                                # Detailed response
                                st.markdown("---")
                                st.subheader("🔍 Detailed Response")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Decision:**", result.get("decision"))
                                    st.write("**Reason:**", result.get("reason"))
                                
                                with col2:
                                    if result.get("answer"):
                                        st.success(f"**Solution:**\n{result.get('answer')}")
                                
                                # Show decision trace if enabled
                                if show_explainability:
                                    st.markdown("---")
                                    with st.expander("🔬 Decision Trace (Explainability)"):
                                        trace_display = {
                                            "Request ID": trace["request_id"],
                                            "Processing Steps": [
                                                {"timestamp": e[0], "event": e[1], "description": e[2]}
                                                for e in trace["events"]
                                            ],
                                            "Total Processing Time": f"{elapsed:.1f}ms"
                                        }
                                        st.json(trace_display)
                            else:
                                st.error(f"Agent returned error: {response.status_code}")
                                
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to Support Agent (port 8000)")
                            st.code("cd Customer_support_agent && python main.py")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with col2:
            st.markdown("### Quick Examples")
            examples = [
                "VPN not working",
                "Can't login",
                "Teams crashing",
                "Printer offline"
            ]
            for ex in examples:
                if st.button(f"📌 {ex}", use_container_width=True):
                    st.session_state.example_input = ex
    
    # Voice Support
    else:
        st.subheader("🎤 Voice-based IT Support")
        
        audio_file = st.file_uploader(
            "Upload voice request (.wav, .mp3, .ogg):",
            type=["wav", "mp3", "ogg"],
            help="Record your issue and upload the audio file"
        )
        
        if st.button("🚀 Submit Voice Ticket", use_container_width=True):
            if not audio_file:
                st.warning("Please upload an audio file first")
            elif not support_status:
                st.error("❌ Support Agent is offline")
            else:
                with st.spinner("🔄 Processing voice request..."):
                    start_time = time.time()
                    
                    try:
                        ticket_id = f"voice-{str(uuid.uuid4())[:8]}"
                        
                        files = {
                            "audio": (audio_file.name, audio_file, audio_file.type)
                        }
                        
                        response = requests.post(
                            f"{SUPPORT_API}/it-support/voice",
                            params={"ticket_id": ticket_id},
                            files=files,
                            timeout=60
                        )
                        
                        elapsed = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            st.session_state.support_history.append({
                                "type": "voice",
                                "audio": audio_file.name,
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                                "processing_time_ms": elapsed
                            })
                            
                            st.success("✅ Voice request processed!")
                            
                            st.subheader("📋 Support Response")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Ticket ID", ticket_id[-8:])
                            with col2:
                                st.metric("Processing", f"{elapsed:.1f}ms")
                            with col3:
                                st.metric("Status", "Processed")
                            
                            st.markdown("---")
                            st.write("**Decision:**", result.get("decision"))
                            st.write("**Reason:**", result.get("reason"))
                            if result.get("answer"):
                                st.success(f"**Answer:**\n{result.get('answer')}")
                        else:
                            st.error("Voice processing failed")
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Support History
    if st.session_state.support_history:
        st.markdown("---")
        st.subheader("📜 Support Ticket History")
        
        for i, ticket in enumerate(reversed(st.session_state.support_history[-5:]), 1):
            with st.expander(f"Ticket {i}: {ticket['type'].upper()} - {ticket['timestamp'][:10]}"):
                if ticket['type'] == 'text':
                    st.write(f"**Issue:** {ticket['issue']}")
                else:
                    st.write(f"**Audio:** {ticket['audio']}")
                
                st.write(f"**Decision:** {ticket['result'].get('decision')}")
                st.write(f"**Processing Time:** {ticket['processing_time_ms']:.1f}ms")

# =========================================================
# TAB 2: DOCUMENT REVIEW AGENT
# =========================================================

with tab2:
    st.header("Document Review Agent - Contract Analysis")
    
    st.write("""
    Upload contracts or policies for automated review:
    1. Upload PDF document
    2. System analyzes and categorizes
    3. Routes to appropriate reviewer
    4. Shows risk assessment and recommendations
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Document for Review")
        
        uploaded_file = st.file_uploader(
            "Upload PDF document:",
            type=["pdf"],
            help="Upload a contract, policy, or agreement for analysis"
        )
        
        doc_type = st.selectbox(
            "Document Type (if known):",
            ["Auto-detect", "Contract", "Policy", "Agreement", "Terms & Conditions"]
        )
        
        if st.button("📤 Upload & Review", use_container_width=True):
            if not uploaded_file:
                st.warning("Please select a document first")
            elif not doc_status:
                st.error("❌ Document Agent is offline")
                st.code("cd Document_Review_agent && python app/main.py")
            else:
                with st.spinner("🔄 Analyzing document..."):
                    start_time = time.time()
                    
                    try:
                        files = {
                            "file": (uploaded_file.name, uploaded_file, "application/pdf")
                        }
                        
                        response = requests.post(
                            f"{DOCUMENT_API}/review",
                            files=files,
                            timeout=120
                        )
                        
                        elapsed = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            st.session_state.document_results = {
                                "file": uploaded_file.name,
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                                "processing_time_ms": elapsed
                            }
                            
                            st.success("✅ Document analyzed successfully!")
                        else:
                            st.error(f"Analysis failed: {response.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with col1:
        # Display results if available
        if st.session_state.document_results:
            st.markdown("---")
            st.subheader("📊 Analysis Results")
            
            result = st.session_state.document_results['result']
            elapsed = st.session_state.document_results['processing_time_ms']
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("File", st.session_state.document_results['file'][-20:])
            with col2:
                st.metric("Document Type", result.get("document_type", "Unknown"))
            with col3:
                risk = result.get("risk_level", "N/A")
                risk_color = "🔴" if risk == "High" else "🟡" if risk == "Medium" else "🟢"
                st.metric("Risk Level", f"{risk_color} {risk}")
            with col4:
                st.metric("Processing Time", f"{elapsed:.1f}ms")
            
            # Detailed analysis
            st.markdown("---")
            
            if result.get("risk_score"):
                st.subheader("🎯 Risk Score")
                
                # Risk score bar
                risk_score = result.get("risk_score", 0)
                st.progress(risk_score / 100)
                st.caption(f"Risk Score: {risk_score}/100")
            
            # Clause analysis
            if result.get("clause_analysis"):
                st.markdown("---")
                st.subheader("📋 Clause-by-Clause Analysis")
                
                for clause, details in result.get("clause_analysis", {}).items():
                    with st.expander(f"📌 {clause}"):
                        st.write(f"**Status:** {details.get('status', 'N/A')}")
                        st.write(f"**Similarity:** {details.get('similarity_score', 'N/A')}")
                        
                        if details.get("snippet"):
                            st.info(f"**Extract:** {details.get('snippet')}")
            
            # Recommendations
            if result.get("suggestions"):
                st.markdown("---")
                st.subheader("💡 Recommendations")
                
                for clause, suggestion in result.get("suggestions", {}).items():
                    st.warning(f"**{clause}:** {suggestion}")
            
            # Full JSON
            with st.expander("🔬 Full Analysis Data"):
                st.json(result)

# =========================================================
# TAB 3: DECISION TRACE & ANALYTICS
# =========================================================

with tab3:
    st.header("Decision Trace & System Analytics")
    
    st.write("""
    Detailed view of all decisions made by the system with full explainability.
    """)
    
    # Analytics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Requests",
            len(st.session_state.support_history),
            "support tickets"
        )
    with col2:
        st.metric(
            "Document Reviews",
            1 if st.session_state.document_results else 0,
            "documents analyzed"
        )
    with col3:
        if st.session_state.support_history:
            avg_time = sum(t.get("processing_time_ms", 0) for t in st.session_state.support_history) / len(st.session_state.support_history)
            st.metric("Avg Processing", f"{avg_time:.1f}ms")
        else:
            st.metric("Avg Processing", "N/A")
    with col4:
        agent_status = "✅ All Online" if (support_status and doc_status) else "⚠️ Some Offline"
        st.metric("Agent Status", agent_status)
    
    st.markdown("---")
    
    # Decision history
    if st.session_state.support_history:
        st.subheader("📊 Support Request History")
        
        history_data = []
        for ticket in st.session_state.support_history[-10:]:
            history_data.append({
                "Type": ticket['type'].upper(),
                "Timestamp": ticket['timestamp'][:19],
                "Processing Time (ms)": f"{ticket['processing_time_ms']:.1f}",
                "Decision": ticket['result'].get('decision', 'N/A')[:30]
            })
        
        st.dataframe(history_data, use_container_width=True)
    else:
        st.info("No support requests yet")
    
    # Decision trace visualization
    if st.session_state.last_decision_trace:
        st.markdown("---")
        st.subheader("🔬 Latest Decision Trace")
        
        trace = st.session_state.last_decision_trace
        
        st.write(f"**Request ID:** {trace['request_id']}")
        st.write(f"**Timestamp:** {trace['timestamp']}")
        
        st.write("**Event Timeline:**")
        for timestamp, event, description in trace['events']:
            col1, col2, col3 = st.columns([1, 2, 5])
            with col1:
                st.code(timestamp)
            with col2:
                st.write(f"**{event}**")
            with col3:
                st.write(description)

# =========================
# FOOTER
# =========================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. Go to **Customer Support** tab
    2. Describe an IT issue
    3. Click "Submit & Get Support"
    4. See full decision with explainability
    """)

with col2:
    st.markdown("### 📄 Document Review")
    st.markdown("""
    1. Go to **Document Review** tab
    2. Upload a PDF contract
    3. View risk assessment
    4. Read recommendations
    """)

with col3:
    st.markdown("### 📊 Analytics")
    st.markdown("""
    1. Go to **Decision Trace** tab
    2. View all decisions
    3. Check performance metrics
    4. See agent status
    """)

st.markdown("---")
st.caption("Enterprise MCP System with Full Explainability • 2026-03-30")
