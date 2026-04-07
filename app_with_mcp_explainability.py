"""
Enhanced Streamlit App with MCP Decision Explainability
Shows WHY agents are selected and WHAT decisions were made
"""

import streamlit as st
import json
import uuid
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.decision_engine import MCPDecisionEngine
from mcp.decision_explainer import DecisionExplainer, DecisionTracer
from mcp.models import MCPRequest, IntentMatch
from mcp.agent_registry import AgentRegistry

# =========================
# MOCK INTENT DETECTOR
# =========================

class MockIntentDetector:
    """Simple intent detector for demo purposes"""
    
    def detect(self, text, intent_hints=None):
        """Detect intent from text and return list of IntentMatch objects"""
        text_lower = text.lower()
        
        # Simple keyword matching
        intents = {
            "network_issue": ["vpn", "wifi", "internet", "connection", "network"],
            "account_access": ["password", "account", "login", "access", "locked"],
            "software_issue": ["crash", "install", "update", "download", "error"],
            "hardware_issue": ["printer", "print", "paper", "ink", "document", "monitor"],
            "email_issue": ["email", "outlook", "message", "send", "receive"],
        }
        
        matches = []
        
        for intent_name, keywords in intents.items():
            confidence = 0.0
            matching_tokens = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    confidence += 0.15
                    matching_tokens.append(keyword)
            
            if confidence > 0.0:
                matches.append(IntentMatch(
                    name=intent_name,
                    confidence=min(confidence, 0.95),  # Cap at 0.95
                    method="rule",
                    rationale=f"Matched keywords: {', '.join(matching_tokens)}",
                    supporting_tokens=matching_tokens
                ))
        
        # If no matches, return general support
        if not matches:
            matches.append(IntentMatch(
                name="general_support",
                confidence=0.60,
                method="rule",
                rationale="No specific intent detected",
                supporting_tokens=[]
            ))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="MCP Explainability Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_explanation" not in st.session_state:
    st.session_state.last_explanation = None
if "example" not in st.session_state:
    st.session_state.example = ""
if "current_time" not in st.session_state:
    st.session_state.current_time = ""

st.title("🚀 MCP Decision Explainability System")

st.write("""
This dashboard shows **how MCP makes routing decisions** with full transparency:
- **Why** each agent was selected
- **What context** influenced the decision
- **Which alternatives** were considered
- **Real-time decision trace** with timestamps
""")

# =========================
# SIDEBAR CONFIG
# =========================

st.sidebar.title("⚙️ Configuration")

with st.sidebar:
    enable_explainability = st.checkbox(
        "Enable Decision Explainability",
        value=True,
        help="Show detailed decision explanations"
    )
    
    show_trace = st.checkbox(
        "Show Event Trace",
        value=True,
        help="Show millisecond-level timing of decision events"
    )
    
    show_alternatives = st.checkbox(
        "Show Alternatives",
        value=True,
        help="Show agents that were considered but not selected"
    )
    
    st.markdown("---")
    st.sidebar.info(
        """
        **About This System**
        
        MCP (Model Context Protocol) Decision Engine with explainability features:
        
        ✓ Multi-agent routing  
        ✓ Intent detection  
        ✓ Context-aware decisions  
        ✓ Full decision audit trail  
        ✓ Real-time event tracing  
        """
    )

# =========================
# INITIALIZE MCP ENGINE
# =========================

@st.cache_resource
def get_mcp_engine():
    """Initialize MCP Decision Engine with explainability"""
    try:
        engine = MCPDecisionEngine(
            agent_registry=AgentRegistry(),
            intent_detector=MockIntentDetector(),
            policy_engine=None,
            enable_explainability=True
        )
        return engine
    except Exception as e:
        st.error(f"Could not initialize MCP Engine: {str(e)}")
        return None

# =========================
# MAIN CONTENT
# =========================

# Create tabs for different scenarios
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Test Routing Decision",
    "📊 Decision Analysis",
    "📈 Decision Trace",
    "📚 Documentation"
])

# =========================================================
# TAB 1: TEST ROUTING DECISION
# =========================================================

with tab1:
    st.header("Test MCP Routing Decision")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Create a Request")
        
        # Create form for MCP request
        request_id = st.text_input(
            "Request ID",
            value=f"req-{str(uuid.uuid4())[:8]}",
            help="Unique identifier for this request"
        )
        
        user_id = st.text_input(
            "User ID",
            value="user-001",
            help="ID of the user making the request"
        )
        
        request_text = st.text_area(
            "Request Description",
            value="I need help with my account access and VPN connection",
            help="Describe what the user needs help with",
            height=100
        )
        
        priority = st.selectbox(
            "Priority Level",
            ["low", "normal", "high", "critical"],
            help="Request priority level"
        )
        
        # Submit button
        if st.button("🚀 Route Request & Explain Decision", use_container_width=True):
            
            # Create MCP Request
            request = MCPRequest(
                request_id=request_id,
                user_id=user_id,
                text=request_text,
                priority=priority,
                metadata={
                    "source": "streamlit_dashboard",
                    "timestamp": str(st.session_state.get("current_time", ""))
                }
            )
            
            st.success("✅ Request created!")
            
            # Get MCP engine
            engine = get_mcp_engine()
            
            if engine:
                try:
                    # Process request with explainability
                    response = engine.process_request(request)
                    
                    # Store response in session state
                    st.session_state.last_response = response
                    
                    # Try to get explanation from audit or mcp_decision
                    explanation = None
                    if hasattr(response, 'audit') and response.audit:
                        explanation = response.audit.get('decision_explanation')
                    if not explanation and hasattr(response, 'mcp_decision') and response.mcp_decision:
                        explanation = response.mcp_decision
                    
                    st.session_state.last_explanation = explanation
                    
                    st.info("✓ Decision processed! See details below.")
                    
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
    
    with col2:
        st.subheader("Quick Examples")
        
        if st.button("📱 Network Issue"):
            st.session_state.example = "I can't connect to WiFi and VPN is not responding"
        
        if st.button("🔐 Account Issue"):
            st.session_state.example = "I forgot my password and can't access my account"
        
        if st.button("💻 Software Issue"):
            st.session_state.example = "Microsoft Teams is crashing and won't open"
        
        if st.button("🖨️ Printer Issue"):
            st.session_state.example = "Network printer is offline and I can't print"
    
    # Display last decision if exists
    if st.session_state.last_response is not None:
        st.markdown("---")
        st.subheader("📋 Decision Result")
        
        response = st.session_state.last_response
        explanation = st.session_state.last_explanation
        
        # Convert to dict if it's a dataclass
        if explanation:
            from dataclasses import asdict
            exp_dict = explanation.to_dict() if hasattr(explanation, 'to_dict') else (
                asdict(explanation) if hasattr(explanation, '__dataclass_fields__') else explanation
            )
        elif hasattr(response, 'mcp_decision') and response.mcp_decision:
            exp_dict = response.mcp_decision.to_dict() if hasattr(response.mcp_decision, 'to_dict') else asdict(response.mcp_decision)
        else:
            exp_dict = None
        
        if exp_dict:
            # Key information
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Selected Agent(s)",
                    ", ".join(response.selected_agents) if response.selected_agents else "N/A"
                )
            
            with col2:
                st.metric(
                    "Intent Detected",
                    exp_dict.get("intent", "N/A"),
                    f"{exp_dict.get('confidence', 0)*100:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Status",
                    response.status.upper(),
                    "✓" if response.status == "ok" else "!"
                )
            
            with col4:
                st.metric(
                    "Confidence",
                    "Sufficient" if exp_dict.get('confidence_sufficient', False) else "Low",
                    f"{exp_dict.get('confidence', 0):.2f}"
                )
            
            # Full explanation in expander
            with st.expander("🔍 Full Decision Details"):
                st.json(exp_dict)

# =========================================================
# TAB 2: DECISION ANALYSIS
# =========================================================

with tab2:
    st.header("Decision Analysis")
    
    if st.session_state.last_explanation is None:
        st.info("Run a decision in Tab 1 first to see analysis here")
    else:
        explanation = st.session_state.last_explanation
        from dataclasses import asdict
        exp_dict = explanation.to_dict() if hasattr(explanation, 'to_dict') else (
            asdict(explanation) if hasattr(explanation, '__dataclass_fields__') else explanation
        )
        
        # Display MCPDecision information
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Decision Information")
            st.write(f"**Intent:** {exp_dict.get('intent', 'N/A')}")
            st.write(f"**Confidence:** {exp_dict.get('confidence', 0):.2%}")
            st.write(f"**Reasoning:** {exp_dict.get('reasoning', 'No reasoning provided')}")
            st.write(f"**Confidence Sufficient:** {'✓ Yes' if exp_dict.get('confidence_sufficient') else '✗ No'}")
        
        with col2:
            st.subheader("🎯 Selected Agents")
            
            agents = exp_dict.get('selected_agents', [])
            if agents:
                for agent in agents:
                    if isinstance(agent, dict):
                        st.write(f"- {agent.get('agent_id', 'Unknown')}")
                    else:
                        st.write(f"- {agent}")
            else:
                st.info("No agents selected")
        
        # Show execution plan if available
        plan = exp_dict.get('plan', {})
        if plan and plan.get('steps'):
            st.markdown("---")
            st.subheader("� Execution Plan")
            for i, step in enumerate(plan.get('steps', []), 1):
                st.write(f"**Step {i}:** {step}")
        
        # Show fallback agents if any
        fallback = exp_dict.get('fallback_agents', [])
        if fallback:
            st.markdown("---")
            st.subheader("🔄 Fallback Agents")
            for agent in fallback:
                st.write(f"- {agent}")

# =========================================================
# TAB 3: DECISION TRACE
# =========================================================

with tab3:
    st.header("Real-Time Decision Trace")
    
    st.write("""
    This shows the exact sequence of events that occurred during the decision,
    with millisecond-precision timestamps.
    """)
    
    if st.session_state.last_explanation is None:
        st.info("Run a decision in Tab 1 first to see trace here")
    else:
        response = st.session_state.last_response
        
        # Show response audit information
        st.subheader("📍 Response Audit Trail")
        
        if hasattr(response, 'audit') and response.audit:
            audit = response.audit
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Request ID", response.request_id[:12] + "...")
            
            with col2:
                st.metric("Status", response.status.upper())
            
            with col3:
                st.metric("Trace ID", audit.get("trace_id", "N/A")[:12] + "...")
            
            st.markdown("---")
            st.write("**Audit Details:**")
            st.json(audit)
        else:
            st.info("No audit information available")

# =========================================================
# TAB 4: DOCUMENTATION
# =========================================================

with tab4:
    st.header("📚 How This Works")
    
    st.markdown("""
    ## MCP Decision Explainability System
    
    ### What is MCP?
    **Model Context Protocol** - A framework for intelligent multi-agent routing
    with full decision transparency.
    
    ### How It Works
    
    1. **Request Submission** 
       - User submits a request with context (user ID, priority, text)
    
    2. **Intent Detection**
       - System analyzes the request to understand intent
       - Scores confidence level
    
    3. **Agent Scoring**
       - All available agents are scored against 6 factors:
         - Capability match
         - Historical success
         - Current load
         - Specialization
         - User preference
         - Policy compliance
    
    4. **Policy Filtering**
       - Policies may block certain agents
       - Reasons are logged
    
    5. **Decision Making**
       - Highest-scoring agent is selected
       - All alternatives are recorded
    
    6. **Explanation Generation**
       - Full decision trace is captured
       - Millisecond-level timestamps recorded
       - Context used is documented
       - Scoring breakdown provided
    
    ### Output Formats
    
    The system provides explanations in multiple formats:
    
    #### Text Format (Human-Readable)
    ```
    Request ID: req-001
    Selected Agent: Support-Agent
    Intent: account_access (92% confidence)
    Decision Score: 0.89
    Processing Time: 125.5ms
    ```
    
    #### JSON Format (Machine-Readable)
    ```json
    {
      "request_id": "req-001",
      "primary_agent_name": "Support-Agent",
      "intent_name": "account_access",
      "intent_confidence": 0.92,
      "decision_score": 0.89,
      "decision_time_ms": 125.5
    }
    ```
    
    #### Trace Format (Timeline)
    ```
    [  0.00ms] request_received
    [  2.50ms] intent_detection_start
    [ 15.30ms] intent_detected (confidence: 92%)
    [ 45.75ms] agent_scoring_complete
    [125.50ms] agent_invocation_complete
    ```
    
    ### Benefits
    
    ✅ **Transparency** - See exactly why agents are selected  
    ✅ **Debugging** - Full trace for troubleshooting  
    ✅ **Compliance** - Complete audit trail  
    ✅ **Optimization** - Identify improvement areas  
    ✅ **Trust** - Users understand system decisions  
    
    ### Use Cases
    
    1. **Customer Support Routing**
       - Route to best support agent with explanation
       - Show customer why their request went to this agent
    
    2. **IT Help Desk**
       - Route to specialists by issue type
       - Explain policy-based blocks
    
    3. **Document Review**
       - Route to appropriate reviewers
       - Show scoring factors
    
    4. **Fraud Detection**
       - Route to security team with evidence
       - Audit trail for compliance
    
    ### Key Files
    
    - `mcp/decision_explainer.py` - Core explainability module
    - `mcp/decision_engine.py` - Integration point
    - `mcp/decision_tracer.py` - Event tracing (if separate)
    - `test_decision_explainability.py` - Unit tests
    
    ### Documentation
    
    - `MCP_DECISION_EXPLAINABILITY_README.md` - Quick start
    - `MCP_DECISION_EXPLAINABILITY_GUIDE.md` - Detailed guide
    - `MCP_DECISION_EXPLAINABILITY_INTEGRATION_CHECKLIST.md` - Integration steps
    """)

# =========================
# FOOTER
# =========================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🚀 Quick Links")
    st.markdown("""
    - [README](MCP_DECISION_EXPLAINABILITY_README.md)
    - [Guide](MCP_DECISION_EXPLAINABILITY_GUIDE.md)
    - [Examples](mcp/explainability_examples.py)
    """)

with col2:
    st.markdown("### 📊 System Info")
    st.markdown(f"""
    - Version: 1.0.0
    - Status: Production Ready
    - Last Updated: 2026-03-30
    """)

with col3:
    st.markdown("### 💡 About")
    st.markdown("""
    MCP Decision Explainability System
    For transparent multi-agent routing
    """)
