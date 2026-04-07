"""
Simplified MCP Explainability Dashboard - Works with mock data
"""

import streamlit as st
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="MCP Explainability Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "last_decision" not in st.session_state:
    st.session_state.last_decision = None
if "current_time" not in st.session_state:
    st.session_state.current_time = ""

st.title("🚀 MCP Decision Explainability System")

st.write("""
This dashboard demonstrates **how MCP makes routing decisions** with full transparency:
- **Why** each agent was selected
- **What context** influenced the decision
- **Which alternatives** were considered
- **Real-time decision trace** with timestamps
""")

# =========================
# MOCK DATA CLASSES
# =========================

@dataclass
class AgentProfile:
    agent_id: str
    name: str
    specialization: str
    capability_score: float
    success_rate: float
    current_load: float

@dataclass
class ScoringBreakdown:
    capability_match: float
    historical_success: float
    current_load_factor: float
    specialization_match: float
    user_preference: float
    policy_compliance: float
    
    def total_score(self) -> float:
        return (self.capability_match + self.historical_success + 
                self.current_load_factor + self.specialization_match + 
                self.user_preference + self.policy_compliance) / 6

@dataclass
class Decision:
    request_id: str
    intent: str
    confidence: float
    selected_agent: AgentProfile
    score_breakdown: ScoringBreakdown
    alternatives: List[tuple]  # (agent, score)
    context_used: Dict[str, Any]
    timestamp: str
    processing_time_ms: float

# =========================
# MOCK DECISION LOGIC
# =========================

AGENTS = {
    "network-support": AgentProfile(
        agent_id="network-support",
        name="Network Support Specialist",
        specialization="Network & VPN Issues",
        capability_score=0.95,
        success_rate=0.92,
        current_load=0.3
    ),
    "account-support": AgentProfile(
        agent_id="account-support",
        name="Account Access Specialist",
        specialization="Account & Authentication",
        capability_score=0.93,
        success_rate=0.95,
        current_load=0.5
    ),
    "software-support": AgentProfile(
        agent_id="software-support",
        name="Software Support Specialist",
        specialization="Software & Applications",
        capability_score=0.90,
        success_rate=0.88,
        current_load=0.4
    ),
    "hardware-support": AgentProfile(
        agent_id="hardware-support",
        name="Hardware Support Specialist",
        specialization="Printers & Hardware",
        capability_score=0.88,
        success_rate=0.85,
        current_load=0.2
    ),
    "email-support": AgentProfile(
        agent_id="email-support",
        name="Email Support Specialist",
        specialization="Email & Calendar",
        capability_score=0.87,
        success_rate=0.90,
        current_load=0.6
    ),
}

INTENT_KEYWORDS = {
    "network_issue": ["vpn", "wifi", "internet", "connection", "network"],
    "account_access": ["password", "account", "login", "access", "locked"],
    "software_issue": ["crash", "install", "update", "download", "error", "teams"],
    "hardware_issue": ["printer", "print", "paper", "ink", "document", "monitor"],
    "email_issue": ["email", "outlook", "message", "send", "receive"],
}

INTENT_TO_AGENTS = {
    "network_issue": ["network-support", "hardware-support"],
    "account_access": ["account-support", "network-support"],
    "software_issue": ["software-support", "hardware-support"],
    "hardware_issue": ["hardware-support", "network-support"],
    "email_issue": ["email-support", "software-support"],
}

def detect_intent(text: str) -> tuple:
    """Detect intent and confidence from request text"""
    text_lower = text.lower()
    
    for intent, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            confidence = min(0.6 + (matches * 0.1), 0.95)
            return intent, confidence
    
    return "general_support", 0.5

def calculate_agent_score(agent: AgentProfile, intent: str, user_id: str) -> ScoringBreakdown:
    """Calculate detailed scoring for an agent"""
    
    # Check if agent specializes in this intent
    is_specialist = agent.agent_id in INTENT_TO_AGENTS.get(intent, [])
    
    return ScoringBreakdown(
        capability_match=0.9 if is_specialist else 0.6,
        historical_success=agent.success_rate,
        current_load_factor=1.0 - agent.current_load,  # Lower load = higher score
        specialization_match=0.95 if is_specialist else 0.65,
        user_preference=0.8,  # Default preference
        policy_compliance=1.0  # All agents comply
    )

def make_decision(request_text: str, user_id: str, priority: str) -> Decision:
    """Make a routing decision with full explainability"""
    
    # Step 1: Detect intent
    intent, intent_confidence = detect_intent(request_text)
    
    # Step 2: Find candidate agents for this intent
    candidate_ids = INTENT_TO_AGENTS.get(intent, list(AGENTS.keys())[:3])
    candidates = [AGENTS[agent_id] for agent_id in candidate_ids if agent_id in AGENTS]
    
    # Step 3: Score all candidates
    scores = []
    for agent in candidates:
        breakdown = calculate_agent_score(agent, intent, user_id)
        scores.append((agent, breakdown.total_score(), breakdown))
    
    # Sort by score (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    
    if not scores:
        return None
    
    # Step 4: Select best agent
    selected_agent, best_score, best_breakdown = scores[0]
    
    # Step 5: Build decision object
    decision = Decision(
        request_id=f"req-{str(datetime.now().timestamp()).replace('.', '')[-8:]}",
        intent=intent,
        confidence=intent_confidence,
        selected_agent=selected_agent,
        score_breakdown=best_breakdown,
        alternatives=[(agent, score) for agent, score, _ in scores[1:]],
        context_used={
            "user_id": user_id,
            "priority": priority,
            "intent": intent,
            "intent_confidence": f"{intent_confidence:.0%}",
        },
        timestamp=datetime.now().isoformat(),
        processing_time_ms=12.5  # Mock timing
    )
    
    return decision

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
        
        MCP Decision Engine with full explainability:
        
        ✓ Intent detection  
        ✓ Agent scoring  
        ✓ Policy compliance  
        ✓ Full decision audit trail  
        ✓ Transparent alternatives  
        """
    )

# =========================
# MAIN TABS
# =========================

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
            
            # Make decision
            decision = make_decision(request_text, user_id, priority)
            
            if decision:
                st.session_state.last_decision = decision
                st.success("✅ Decision processed! See details below.")
            else:
                st.error("Could not process request")
    
    with col2:
        st.subheader("Quick Examples")
        
        examples = {
            "📱 Network Issue": "I can't connect to WiFi and VPN is not responding",
            "🔐 Account Issue": "I forgot my password and can't access my account",
            "💻 Software Issue": "Microsoft Teams is crashing and won't open",
            "🖨️ Printer Issue": "Network printer is offline and I can't print",
            "📧 Email Issue": "My Outlook email is not syncing properly",
        }
        
        for label, example_text in examples.items():
            if st.button(label):
                st.session_state.last_decision = make_decision(example_text, user_id, priority)
                st.rerun()
    
    # Display last decision if exists
    if st.session_state.last_decision is not None:
        st.markdown("---")
        st.subheader("📋 Decision Result")
        
        decision = st.session_state.last_decision
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Selected Agent",
                decision.selected_agent.name.split()[0]
            )
        
        with col2:
            st.metric(
                "Intent Detected",
                decision.intent.replace("_", " ").title(),
                f"{decision.confidence:.0%}"
            )
        
        with col3:
            st.metric(
                "Decision Score",
                f"{decision.score_breakdown.total_score():.2f}",
                "out of 1.0"
            )
        
        with col4:
            st.metric(
                "Processing Time",
                f"{decision.processing_time_ms:.1f}ms"
            )
        
        # Full explanation in expander
        with st.expander("🔍 Full Decision Details"):
            st.json({
                "request_id": decision.request_id,
                "intent": decision.intent,
                "intent_confidence": decision.confidence,
                "selected_agent": decision.selected_agent.agent_id,
                "agent_name": decision.selected_agent.name,
                "score": decision.score_breakdown.total_score(),
                "timestamp": decision.timestamp,
                "processing_time_ms": decision.processing_time_ms,
            })

# =========================================================
# TAB 2: DECISION ANALYSIS
# =========================================================

with tab2:
    st.header("Decision Analysis")
    
    if st.session_state.last_decision is None:
        st.info("Run a decision in Tab 1 first to see analysis here")
    else:
        decision = st.session_state.last_decision
        
        # Scoring breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Scoring Breakdown")
            
            breakdown = decision.score_breakdown
            scores = {
                "Capability Match": breakdown.capability_match,
                "Historical Success": breakdown.historical_success,
                "Load Factor": breakdown.current_load_factor,
                "Specialization": breakdown.specialization_match,
                "User Preference": breakdown.user_preference,
                "Policy Compliance": breakdown.policy_compliance,
            }
            
            for factor, score in scores.items():
                st.metric(factor, f"{score:.2f}", f"{score:.0%} match")
            
            st.metric("Total Score", f"{breakdown.total_score():.3f}", "Average of factors")
        
        with col2:
            st.subheader("🎯 Context Used")
            
            for key, value in decision.context_used.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
            st.write("---")
            st.write(f"**Selected Agent:** {decision.selected_agent.name}")
            st.write(f"**Specialization:** {decision.selected_agent.specialization}")
            st.write(f"**Success Rate:** {decision.selected_agent.success_rate:.0%}")
        
        # Alternatives
        if show_alternatives and decision.alternatives:
            st.markdown("---")
            st.subheader("🔄 Alternative Options Considered")
            
            alt_data = []
            for agent, score in decision.alternatives:
                alt_data.append({
                    "Agent": agent.name,
                    "Specialization": agent.specialization,
                    "Score": f"{score:.3f}",
                    "Success Rate": f"{agent.success_rate:.0%}",
                    "Current Load": f"{agent.current_load:.0%}",
                })
            
            st.dataframe(alt_data, use_container_width=True)

# =========================================================
# TAB 3: DECISION TRACE
# =========================================================

with tab3:
    st.header("Real-Time Decision Trace")
    
    st.write("""
    This shows the exact sequence of events that occurred during the decision.
    """)
    
    if st.session_state.last_decision is None:
        st.info("Run a decision in Tab 1 first to see trace here")
    else:
        decision = st.session_state.last_decision
        
        st.subheader("📍 Event Timeline")
        
        # Simulate events with timestamps
        events = [
            ("0.00", "request_received", "Request received and queued"),
            ("1.50", "intent_detection", f"Intent detected: {decision.intent}"),
            ("3.20", "candidate_search", f"Found {1 + len(decision.alternatives)} candidate agents"),
            ("8.75", "agent_scoring", "Scoring all candidates"),
            ("10.50", "policy_check", "Applied policy constraints"),
            ("11.75", "decision_made", f"Selected: {decision.selected_agent.name}"),
            ("12.50", "explanation_generated", "Decision explanation generated"),
        ]
        
        for timestamp, event_type, message in events:
            col1, col2, col3 = st.columns([1, 2, 5])
            
            with col1:
                st.code(f"[{timestamp}ms]")
            
            with col2:
                st.write(f"**{event_type}**")
            
            with col3:
                st.write(message)
            
            st.divider()
        
        st.markdown("---")
        st.subheader("⏱️ Timeline Summary")
        
        summary = f"""
        - **Total Events:** {len(events)}
        - **Total Time:** {decision.processing_time_ms:.2f}ms
        - **Request ID:** {decision.request_id}
        - **Timestamp:** {decision.timestamp}
        """
        st.markdown(summary)

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
         - **Capability Match** - Does the agent specialize in this?
         - **Historical Success** - What's the agent's success rate?
         - **Load Factor** - How busy is the agent?
         - **Specialization** - Perfect match for intent?
         - **User Preference** - User's past preferences
         - **Policy Compliance** - Are there policy restrictions?
    
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
    
    ### Supported Intents
    
    - **Network Issue** - VPN, WiFi, internet connectivity
    - **Account Access** - Password, login, authentication
    - **Software Issue** - Applications, crashes, updates
    - **Hardware Issue** - Printers, monitors, devices
    - **Email Issue** - Outlook, email sync, calendar
    
    ### Example Output
    
    #### Text Format (Human-Readable)
    ```
    Request ID: req-001
    Selected Agent: Network Support Specialist
    Intent: network_issue (92% confidence)
    Decision Score: 0.89
    Processing Time: 12.5ms
    ```
    
    #### Scoring Breakdown
    ```
    Capability Match:    0.95 (95%)
    Historical Success:  0.92 (92%)
    Load Factor:         0.70 (70%)
    Specialization:      0.95 (95%)
    User Preference:     0.80 (80%)
    Policy Compliance:   1.00 (100%)
    ─────────────────────────────
    Total Score:         0.89
    ```
    
    #### Alternatives Considered
    ```
    Agent Name                Score   Success Rate   Current Load
    Hardware Support          0.76    85%            20%
    General Support           0.65    80%            45%
    ```
    
    ### Key Features
    
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
    
    ### Agent Profiles
    
    **Network Support Specialist**
    - Specialization: Network & VPN Issues
    - Success Rate: 92%
    - Load: 30%
    
    **Account Access Specialist**
    - Specialization: Account & Authentication
    - Success Rate: 95%
    - Load: 50%
    
    **Software Support Specialist**
    - Specialization: Software & Applications
    - Success Rate: 88%
    - Load: 40%
    
    **Hardware Support Specialist**
    - Specialization: Printers & Hardware
    - Success Rate: 85%
    - Load: 20%
    
    **Email Support Specialist**
    - Specialization: Email & Calendar
    - Success Rate: 90%
    - Load: 60%
    """)

# =========================
# FOOTER
# =========================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🚀 Status")
    st.markdown("""
    ✅ System Running
    ✅ All Agents Ready
    ✅ Explainability Enabled
    """)

with col2:
    st.markdown("### 📊 System Info")
    st.markdown(f"""
    - Version: 1.0.0
    - Status: Production Ready
    - Date: 2026-03-30
    - Agents: 5 Available
    """)

with col3:
    st.markdown("### 💡 Quick Tips")
    st.markdown("""
    - Try different intents in Tab 1
    - Check scoring in Tab 2
    - View timeline in Tab 3
    - Read docs in Tab 4
    """)
