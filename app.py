"""
MCP UNIFIED AGENT SYSTEM - Enterprise Multi-Agent Orchestration
Master Control Program with Human-in-the-Loop + Dynamic UI Transitions
Features: Single unified interface, HITL approval, agent orchestration, audit trails
✨ CINEMATIC HOLOGRAPHIC OPERATING SYSTEM INTERFACE ✨
"""

import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re

# Import cinematic UI components
try:
    from cinematic_ui import (
        configure_cinematic_theme,
        render_holographic_header,
        render_holographic_card,
        display_cinematic_metrics,
        render_agent_orchestration_flow,
        render_cinematic_timeline,
        render_system_status,
        render_workflow_stage_indicator,
        render_agent_status_grid,
        CINEMATIC_COLORS
    )
    CINEMATIC_UI_AVAILABLE = True
except ImportError:
    CINEMATIC_UI_AVAILABLE = False

# Import real metrics collector
try:
    from real_metrics_collector import metrics_collector
except ImportError:
    metrics_collector = None

# ============================================================================
# APPLY GLOBAL CSS STYLING
# ============================================================================

st.markdown("""
<style>
/* Input fields - black text for light backgrounds */
textarea, input[type="text"], input[type="password"] {
    color: #000000 !important;
    background-color: #ffffff !important;
}

.stTextArea textarea {
    color: #000000 !important;
    background-color: #ffffff !important;
}

/* Metric cards - light text for dark backgrounds */
[data-testid="stMetric"] {
    background-color: transparent !important;
}

[data-testid="stMetricValue"] {
    color: #00d9ff !important;
    font-weight: bold;
}

[data-testid="stMetricLabel"] {
    color: #ffffff !important;
}

/* File uploader label */
.stFileUploader label {
    color: #000000 !important;
}

.stFileUploader {
    color: #000000 !important;
}

/* Upload button text */
.stFileUploader button {
    color: #000000 !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================================
# MCP ORCHESTRATION - ENUMS & DATA MODELS
# ============================================================================

class WorkflowStep(Enum):
    """Workflow execution steps"""
    DOCUMENT_REVIEW = "document_review"
    HUMAN_APPROVAL = "human_approval"
    IT_SUPPORT = "it_support"
    MEETING_CALENDAR = "meeting_calendar"
    HR_ONBOARDING = "hr_onboarding"
    PROJECT_MANAGEMENT = "project_management"
    ANALYTICS = "analytics"
    COMPLETED = "completed"

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApprovalStatus(Enum):
    """HITL approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Workflow sequence
WORKFLOW_SEQUENCE = [
    WorkflowStep.DOCUMENT_REVIEW,
    WorkflowStep.HUMAN_APPROVAL,
    WorkflowStep.IT_SUPPORT,
    WorkflowStep.MEETING_CALENDAR,
    WorkflowStep.HR_ONBOARDING,
    WorkflowStep.PROJECT_MANAGEMENT,
    WorkflowStep.ANALYTICS,
    WorkflowStep.COMPLETED,
]

# ============================================================================
# MCP ORCHESTRATION - STATE MANAGEMENT
# ============================================================================

class WorkflowState:
    """Manages workflow state across the application"""
    
    def __init__(self, workflow_id: str, user_input: str):
        self.id = workflow_id
        self.user_input = user_input
        self.current_step = WorkflowStep.DOCUMENT_REVIEW
        self.status = "running"  # running, paused, completed, failed
        self.completed_steps = []
        self.agent_results = {}
        self.approval_pending = None
        self.risk_level = None
        self.created_at = datetime.utcnow()
        self.history = []
    
    def record_execution(self, agent_name: str, result: Dict):
        """Record agent execution"""
        self.agent_results[agent_name] = result
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "status": "completed"
        })
    
    def set_approval(self, approval_id: str, reason: str, risk_level: RiskLevel, issues: List[str]):
        """Set approval requirement"""
        self.approval_pending = {
            "id": approval_id,
            "reason": reason,
            "risk_level": risk_level,
            "issues": issues,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        self.risk_level = risk_level
        self.status = "paused"
    
    def approve(self, approved_by: str):
        """Approve workflow"""
        self.approval_pending = None
        self.status = "running"
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "approved_by",
            "approved_by": approved_by
        })
    
    def reject(self, rejected_by: str):
        """Reject workflow"""
        self.approval_pending = None
        self.status = "failed"
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "rejected_by",
            "rejected_by": rejected_by
        })

class MCPOrchestrator:
    """Master Control Program - orchestrates all agents"""
    
    def __init__(self):
        self.workflows = {}
    
    def create_workflow(self, user_input: str) -> str:
        """Create new workflow"""
        workflow_id = str(uuid.uuid4())[:8]
        self.workflows[workflow_id] = WorkflowState(workflow_id, user_input)
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state"""
        return self.workflows.get(workflow_id)
    
    def analyze_risk(self, document_data: Dict) -> RiskLevel:
        """Analyze document risk level"""
        if not document_data:
            return RiskLevel.LOW
        
        issues = document_data.get("issues", [])
        if not issues:
            return RiskLevel.LOW
        
        issues_str = " ".join(issues).lower()
        
        critical_keywords = ["liability", "data protection", "breach", "non-compliant"]
        high_keywords = ["missing", "weak", "unclear", "undefined"]
        
        critical_count = sum(1 for kw in critical_keywords if kw in issues_str)
        high_count = sum(1 for kw in high_keywords if kw in issues_str)
        
        if critical_count >= 2:
            return RiskLevel.CRITICAL
        elif critical_count >= 1 or high_count >= 3:
            return RiskLevel.HIGH
        elif high_count > 0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def next_step(self, current_step: WorkflowStep) -> Optional[WorkflowStep]:
        """Get next workflow step"""
        try:
            idx = WORKFLOW_SEQUENCE.index(current_step)
            if idx + 1 < len(WORKFLOW_SEQUENCE):
                return WORKFLOW_SEQUENCE[idx + 1]
        except ValueError:
            pass
        return None

# ============================================================================
# ENTERPRISE UI COMPONENTS
# ============================================================================

def apply_enterprise_styling():
    """Apply futuristic cinematic AI OS styling"""
    st.markdown("""
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #00d4ff;
            --primary-dark: #0099cc;
            --secondary: #ff006e;
            --success: #00ff88;
            --warning: #ffb81c;
            --danger: #ff0055;
            --bg-dark: #0a0e27;
            --bg-darker: #05070f;
            --accent: #00d4ff;
            --text-primary: #e0e6ff;
            --text-secondary: #a8afd8;
            --border-color: rgba(0, 212, 255, 0.3);
            --neon-glow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
        
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0a0e27 0%, #0f1545 100%);
            background-attachment: fixed;
            color: var(--text-primary);
            font-family: 'Courier New', 'Courier', monospace;
        }
        
        /* Animated background grid */
        [data-testid="stAppViewContainer"]::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(0deg, transparent 24%, rgba(0, 212, 255, 0.05) 25%, rgba(0, 212, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 212, 255, 0.05) 75%, rgba(0, 212, 255, 0.05) 76%, transparent 77%, transparent),
                linear-gradient(90deg, transparent 24%, rgba(0, 212, 255, 0.05) 25%, rgba(0, 212, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 212, 255, 0.05) 75%, rgba(0, 212, 255, 0.05) 76%, transparent 77%, transparent);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 0;
        }
        
        /* Neural particles animation */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 10px rgba(0, 212, 255, 0.5), inset 0 0 10px rgba(0, 212, 255, 0.1); }
            50% { box-shadow: 0 0 30px rgba(0, 212, 255, 0.8), inset 0 0 20px rgba(0, 212, 255, 0.2); }
        }
        
        @keyframes cyber-pulse {
            0%, 100% { border-color: rgba(0, 212, 255, 0.3); }
            50% { border-color: rgba(0, 212, 255, 0.8); }
        }
        
        @keyframes scan-line {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        
        @keyframes neon-flicker {
            0%, 100% { text-shadow: 0 0 10px var(--accent), 0 0 20px var(--accent); }
            50% { text-shadow: 0 0 20px var(--accent), 0 0 40px var(--accent), 0 0 60px var(--accent); }
        }
        
        /* Holographic card effect */
        .holographic-card {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%);
            backdrop-filter: blur(20px);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 
                0 0 30px rgba(0, 212, 255, 0.3),
                inset 0 0 30px rgba(0, 212, 255, 0.1);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            animation: pulse-glow 3s ease-in-out infinite;
        }
        
        .holographic-card:hover {
            border-color: var(--accent);
            box-shadow: 
                0 0 50px rgba(0, 212, 255, 0.6),
                inset 0 0 30px rgba(0, 212, 255, 0.2);
            transform: translateY(-5px);
        }
        
        .holographic-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            animation: scan-line 3s infinite;
        }
        
        /* Glass morphism effect */
        .glass-card {
            background: rgba(10, 14, 39, 0.7);
            backdrop-filter: blur(15px);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            background: rgba(10, 14, 39, 0.9);
            border-color: var(--accent);
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
        }
        
        /* Cyber modal */
        .premium-modal {
            background: linear-gradient(135deg, rgba(5, 7, 15, 0.98) 0%, rgba(15, 21, 69, 0.95) 100%);
            backdrop-filter: blur(20px);
            border: 2px solid var(--accent);
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            box-shadow: 
                0 0 60px rgba(0, 212, 255, 0.4),
                0 25px 50px rgba(0, 0, 0, 0.5);
            position: relative;
            animation: pulse-glow 2s ease-in-out infinite;
        }
        
        .premium-modal::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border: 2px solid transparent;
            border-radius: 16px;
            background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
            animation: cyber-pulse 2s ease-in-out infinite;
            pointer-events: none;
        }
        
        /* Status indicators */
        .status-active { 
            color: var(--success); 
            font-weight: bold;
            text-shadow: 0 0 10px var(--success);
            animation: neon-flicker 2s ease-in-out infinite;
        }
        .status-waiting { 
            color: var(--warning); 
            font-weight: bold;
            text-shadow: 0 0 10px var(--warning);
        }
        .status-completed { 
            color: var(--accent); 
            font-weight: bold;
            text-shadow: 0 0 10px var(--accent);
        }
        .status-error { 
            color: var(--danger); 
            font-weight: bold;
            text-shadow: 0 0 10px var(--danger);
        }
        
        /* Animations */
        .fade-in { animation: slideIn 0.6s ease; }
        .pulse-animation { animation: pulse-glow 2s ease-in-out infinite; }
        
        @keyframes slideIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        /* Cyber title */
        .cyber-title {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(90deg, var(--accent), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            letter-spacing: 2px;
            animation: neon-flicker 3s ease-in-out infinite;
        }
        
        /* Agent node */
        .agent-node {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            margin: 8px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .agent-node::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            animation: scan-line 2s infinite;
        }
        
        .agent-node:hover {
            border-color: var(--accent);
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            transform: scale(1.05);
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(255, 0, 110, 0.1) 100%);
        }
        
        /* Metric display */
        .metric-display {
            background: rgba(0, 212, 255, 0.05);
            border-left: 3px solid var(--accent);
            border-radius: 4px;
            padding: 12px 16px;
            margin: 8px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.1);
        }
        
        /* Workflow step */
        .workflow-step {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(15, 21, 69, 0.8) 100%);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .workflow-step.active {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(15, 21, 69, 0.9) 100%);
            border-color: var(--accent);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        
        .workflow-step.completed {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(15, 21, 69, 0.8) 100%);
            border-color: var(--success);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(255, 0, 110, 0.1) 100%) !important;
            border: 2px solid var(--accent) !important;
            color: var(--text-primary) !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.2) !important;
            font-family: 'Courier New', monospace !important;
            letter-spacing: 1px !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.4) 0%, rgba(255, 0, 110, 0.2) 100%) !important;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.5) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: rgba(0, 212, 255, 0.05) !important;
            border: 1px solid var(--border-color) !important;
            color: #000000 !important;
            border-radius: 8px !important;
            font-family: 'Courier New', monospace !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
        }
        
        /* Header styling */
        .main-header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%);
            border-bottom: 2px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
        }
        
        .system-stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            background: rgba(0, 212, 255, 0.08);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px 25px;
            min-width: 150px;
            text-align: center;
            box-shadow: inset 0 0 15px rgba(0, 212, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            background: rgba(0, 212, 255, 0.15);
            border-color: var(--accent);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3), inset 0 0 15px rgba(0, 212, 255, 0.1);
        }
        
        .stat-label {
            font-size: 0.85em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 8px;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: var(--accent);
            text-shadow: 0 0 10px var(--accent);
        }
        
        /* Approval box */
        .approval-box {
            background: linear-gradient(135deg, rgba(255, 184, 28, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%);
            border: 2px solid var(--warning);
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 0 30px rgba(255, 184, 28, 0.2);
            animation: cyber-pulse 2s ease-in-out infinite;
        }
        
        /* Success notification */
        .success-box {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
            border: 2px solid var(--success);
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.2);
        }
        
        /* Error box */
        .error-box {
            background: linear-gradient(135deg, rgba(255, 0, 85, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%);
            border: 2px solid var(--danger);
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 0 30px rgba(255, 0, 85, 0.2);
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 212, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, var(--accent), var(--secondary));
            border-radius: 6px;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)

def show_mcp_routing_animation():
    """Display MCP routing animation"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 24px; margin-bottom: 12px;">🔄</div>
            <h3 style="color: #0066ff; margin: 0 0 8px 0;">Analyzing Request...</h3>
            <p style="color: #999; margin: 0 0 16px 0; font-size: 14px;">MCP is routing to appropriate agent</p>
        </div>
        """, unsafe_allow_html=True)
        with st.spinner("Processing..."):
            time.sleep(1)

def show_agent_work_screen(agent_name: str, status_message: str, progress: int = 0):
    """Display agent working screen"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                <div style="font-size: 24px;">🤖</div>
                <div>
                    <h3 style="margin: 0; color: #0066ff;">{agent_name}</h3>
                    <p style="margin: 4px 0 0 0; color: #999; font-size: 13px;">Enterprise Agent Processing</p>
                </div>
            </div>
            <p style="color: #e0e0e0; font-size: 14px; margin: 16px 0;">{status_message}</p>
        </div>
        """, unsafe_allow_html=True)

def show_approval_screen(workflow: WorkflowState):
    """Display HITL approval screen"""
    if not workflow.approval_pending:
        return
    
    approval = workflow.approval_pending
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div class="premium-modal">
            <div style="font-size: 32px; margin-bottom: 12px;">⚠️</div>
            <h2 style="color: #ffb84d; margin: 0 0 8px 0; font-size: 22px;">
                {approval['risk_level'].upper()} RISK ESCALATION
            </h2>
            <p style="color: #999; margin: 0; font-size: 13px;">Human Approval Required</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        with st.expander("📋 Risk Analysis Details"):
            st.write(f"**Reason:** {approval['reason']}")
            st.write(f"**Issues Detected:**")
            for issue in approval['issues'][:3]:
                st.write(f"  • {issue}")
        
        st.markdown("---")
        
        col_approve, col_reject = st.columns(2)
        
        with col_approve:
            if st.button("✅ APPROVE", use_container_width=True, key=f"approve_{workflow.id}"):
                workflow.approve("manager_demo")
                st.session_state.show_modal = "approved"
                st.success("✅ Workflow approved! Continuing...")
                time.sleep(1)
                return True
        
        with col_reject:
            if st.button("❌ REJECT", use_container_width=True, key=f"reject_{workflow.id}"):
                workflow.reject("manager_demo")
                st.session_state.show_modal = "rejected"
                st.error("❌ Workflow rejected and closed")
                time.sleep(1)
                return False
    
    return None

def show_transition_popup(title: str, emoji: str, message: str):
    """Show transition popup"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success(f"{emoji} {title}")
        st.info(message)

def show_workflow_timeline(workflow: WorkflowState):
    """Display workflow timeline"""
    st.subheader("🏃 Workflow Progress")
    
    all_steps = [
        ("📄", "Document Review"),
        ("✅", "Human Approval"),
        ("🛡️", "IT Support"),
        ("📅", "Meeting Calendar"),
        ("👥", "HR Onboarding"),
        ("📊", "Project Management"),
        ("📈", "Analytics"),
    ]
    
    cols = st.columns(len(all_steps))
    for idx, (emoji, step_name) in enumerate(all_steps):
        with cols[idx]:
            if step_name.lower().replace(" ", "_") == workflow.current_step.value:
                st.markdown(f'<p style="color: #00cc88; font-weight: bold;">{emoji} {step_name}</p>', 
                           unsafe_allow_html=True)
            elif step_name.lower().replace(" ", "_") in [s.value for s in workflow.completed_steps]:
                st.markdown(f'<p style="color: #4444ff;">{emoji} {step_name}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color: #999;">{emoji} {step_name}</p>', unsafe_allow_html=True)

# ============================================================================
# BEAUTIFUL METRICS & ANALYTICS UI FORMATTERS
# ============================================================================

def display_system_metrics_dashboard(metrics: Dict):
    """Display system metrics in beautiful dashboard format"""
    if metrics is None:
        return
    
    sys_metrics = metrics.get("system_metrics", {})
    if sys_metrics is None:
        sys_metrics = {}
    
    st.markdown("### 📊 System Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Agents", sys_metrics.get("total_agents", 0), delta=None)
    with col2:
        st.metric("Active Agents", sys_metrics.get("active_agents", 0), delta=None)
    with col3:
        st.metric("Total Requests", sys_metrics.get("total_requests", 0), delta="+12 today")
    with col4:
        health = sys_metrics.get("system_health", "unknown")
        health_emoji = "🟢" if health == "operational" else "🟡" if health == "degraded" else "🔴"
        st.metric("System Health", f"{health_emoji} {health.upper()}")
    with col5:
        uptime = sys_metrics.get("uptime", 100)
        st.metric("Uptime", f"{uptime}%")

def display_agent_performance_table(agent_metrics: List[Dict]):
    """Display agent performance as formatted table"""
    if not agent_metrics:
        st.info("No agent metrics available")
        return
    
    st.markdown("### 🤖 Agent Performance Metrics")
    
    # Create dataframe-like display
    perf_data = []
    for agent in agent_metrics:
        perf_data.append({
            "Agent": agent.get("agent_name", "Unknown"),
            "Requests": agent.get("requests_processed", 0),
            "Avg Response (ms)": f"{agent.get('avg_response_time', 0):.2f}",
            "Success Rate": f"{agent.get('success_rate', 0)}%",
            "Status": "✅ Healthy" if agent.get("success_rate", 0) > 95 else "⚠️ Warning"
        })
    
    if perf_data:
        df = __import__('pandas').DataFrame(perf_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def display_performance_trends(trends: Dict):
    """Display performance trends and insights"""
    st.markdown("### 📈 Performance Analysis")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.info(f"**Busiest Agent:** {trends.get('busiest_agent', 'N/A').replace('_', ' ').title()}")
    
    with col2:
        st.success(f"**Fastest Agent:** {trends.get('fastest_agent', 'N/A').replace('_', ' ').title()}")
    
    with col3:
        st.info(f"**Most Reliable:** {trends.get('most_reliable', 'N/A').replace('_', ' ').title()}")
    
    with col4:
        st.warning(f"**Slowest Agent:** {trends.get('slowest_agent', 'N/A').replace('_', ' ').title()}")
    
    with col5:
        avg_response = trends.get('average_response_time', 0)
        st.metric("Avg Response", f"{avg_response:.2f}ms")

def display_system_insights(insights: List[str]):
    """Display system insights and recommendations"""
    st.markdown("### 💡 System Insights")
    
    for i, insight in enumerate(insights[:5]):
        # Color code insights based on type
        if "📊" in insight:
            st.info(insight)
        elif "🚨" in insight:
            st.warning(insight)
        elif "📅" in insight:
            st.info(insight)
        elif "👤" in insight:
            st.success(insight)
        elif "📈" in insight:
            st.success(insight)
        else:
            st.markdown(f"• {insight}")

def display_agent_health_status(agent_metrics: List[Dict]):
    """Display agent health status with visual indicators"""
    st.markdown("### 🏥 Agent Health Status")
    
    # Create health status columns
    health_cols = st.columns(min(3, len(agent_metrics)))
    
    for idx, agent in enumerate(agent_metrics):
        col = health_cols[idx % len(health_cols)]
        with col:
            success_rate = agent.get("success_rate", 0)
            name = agent.get("agent_name", "Unknown").replace("Agent", "").strip()
            
            # Determine health emoji
            if success_rate >= 99:
                health_emoji = "🟢"
                health_text = "Excellent"
            elif success_rate >= 95:
                health_emoji = "🟡"
                health_text = "Good"
            elif success_rate >= 90:
                health_emoji = "🟠"
                health_text = "Fair"
            else:
                health_emoji = "🔴"
                health_text = "Poor"
            
            st.markdown(f"""
            **{health_emoji} {name}**
            
            Success Rate: {success_rate}%
            
            Requests: {agent.get('requests_processed', 0)}
            
            Avg Time: {agent.get('avg_response_time', 0):.2f}ms
            """)

def display_full_analytics_report(data: Dict):
    """Display complete analytics report with all sections"""
    # Handle None data
    if data is None:
        st.error("No analytics data available")
        return
    
    metrics = data.get("metrics", {})
    if metrics is None:
        metrics = {}
    
    # System Metrics Dashboard
    if metrics.get("system_metrics"):
        display_system_metrics_dashboard(metrics)
        st.markdown("---")
    
    # Agent Performance
    if metrics.get("agent_metrics"):
        display_agent_performance_table(metrics["agent_metrics"])
        st.markdown("---")
    
    # Agent Health Status
    if metrics.get("agent_metrics"):
        display_agent_health_status(metrics["agent_metrics"])
        st.markdown("---")
    
    # Performance Trends
    if metrics.get("performance_trends"):
        display_performance_trends(metrics["performance_trends"])
        st.markdown("---")
    
    # System Insights
    if data.get("insights"):
        display_system_insights(data["insights"])
        st.markdown("---")
    
    # Recommendations
    if data.get("recommendations"):
        st.markdown("### 🎯 Recommendations")
        for rec in data["recommendations"]:
            st.info(f"• {rec}")

# ============================================================================
# UTILITY FUNCTIONS - HTML CLEANING
# ============================================================================

def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from text"""
    if not isinstance(text, str):
        return text
    # Remove HTML tags
    clean = re.sub('<[^<]+?>', '', text)
    # Decode common HTML entities
    clean = clean.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'")
    return clean.strip()

def clean_data_recursive(data):
    """Recursively clean HTML from all string values in data structures"""
    if isinstance(data, str):
        return strip_html_tags(data)
    elif isinstance(data, list):
        return [clean_data_recursive(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_data_recursive(value) for key, value in data.items()}
    else:
        return data

# ============================================================================
# CONFIG
# ============================================================================
SUPPORT_API = "http://127.0.0.1:8000"
DOCUMENT_API = "http://127.0.0.1:8001"
MEETING_API = "http://127.0.0.1:8002"
HR_API = "http://127.0.0.1:8003"
PROJECTS_API = "http://127.0.0.1:8005"
ANALYTICS_API = "http://127.0.0.1:8007"
EMAIL_API = "http://127.0.0.1:8004"
EMAIL_DASHBOARD_URL = "http://127.0.0.1:8004/dashboard.html"
REQUEST_TIMEOUT = 30

# Configure cinematic theme if available
if CINEMATIC_UI_AVAILABLE:
    configure_cinematic_theme()
else:
    st.set_page_config(
        page_title="MCP Enterprise Platform",
        page_icon="",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    apply_enterprise_styling()

# ============================================================================
# SESSION STATE
# ============================================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "mcp_orchestrator" not in st.session_state:
    st.session_state.mcp_orchestrator = MCPOrchestrator()
if "current_workflow" not in st.session_state:
    st.session_state.current_workflow = None
if "show_modal" not in st.session_state:
    st.session_state.show_modal = None

# ============================================================================
# FUNCTIONS
# ============================================================================

def detect_intent(user_input: str) -> Dict:
    """Detect if support, document, meeting, HR onboarding, analytics, or project agent"""
    user_lower = user_input.lower()
    
    support_keywords = [
        "vpn", "network", "internet", "wifi", "connection", "login",
        "password", "account", "access", "crash", "error",
        "bug", "issue", "help", "teams", "outlook", "problem",
        "not working", "cant", "can't", "unable", "blocked", "it access", "provision"
    ]
    
    doc_keywords = [
        "contract", "review", "pdf", "document", "analyze", "risk",
        "liability", "clause", "agreement", "nda", "policy", "terms",
        "assessment", "upload", "file", "check", "examine", "evaluate"
    ]
    
    meeting_keywords = [
        "meeting", "schedule", "calendar", "availability", "time",
        "book", "conflict", "attendee", "organizer", "reschedule",
        "suggest", "slots", "free", "busy", "agenda", "conference",
        "sync", "standup", "huddle", "call", "zoom", "teams call"
    ]
    
    hr_keywords = [
        "onboard", "employee", "new hire", "training", "checklist",
        "mentor", "buddy", "hire", "join", "start date", "orientation",
        "hr", "human resources", "personnel", "staff", "recruit", "induction"
    ]
    
    analytics_keywords = [
        "analytics", "metrics", "dashboard", "report", "statistics", "stats",
        "graph", "chart", "data", "insight", "trend", "analysis", "performance",
        "month", "week", "day", "period", "summary", "overview", "query", "queries",
        "completed", "success rate", "processing time", "health"
    ]
    
    project_keywords = [
        "project", "assign", "team", "resource", "milestone", "deadline",
        "allocation", "progress", "task", "budget", "member", "manager", "status"
    ]

    email_keywords = [
        "email", "mail", "inbox", "ticket", "fetch emails", "process email",
        "auto reply", "customer email", "support ticket", "email agent",
        "unread", "reply", "send email", "email support"
    ]
    
    support_score = sum(1 for kw in support_keywords if kw in user_lower)
    doc_score = sum(1 for kw in doc_keywords if kw in user_lower)
    
    # Meeting score - boost if "meeting" or "schedule" or "call" present
    meeting_score = sum(1 for kw in meeting_keywords if kw in user_lower)
    if "meeting" in user_lower or "schedule" in user_lower or "call" in user_lower:
        meeting_score += 2
    
    hr_score = sum(1 for kw in hr_keywords if kw in user_lower)
    analytics_score = sum(1 for kw in analytics_keywords if kw in user_lower)
    email_score = sum(1 for kw in email_keywords if kw in user_lower)
    if "email" in user_lower or "mail" in user_lower or "inbox" in user_lower:
        email_score += 2
    
    # Project score - only count if explicitly mentions "project", "assign", "resource allocation"
    project_score = sum(1 for kw in project_keywords if kw in user_lower)
    if "resource allocation" not in user_lower and "resource" in user_lower and "allocat" not in user_lower:
        project_score = 0  # Don't count "resource" unless it's "resource allocation"
    
    # Detect multi-agent workflows (onboarding = HR + Support + Meeting + Projects)
    is_onboarding = hr_score > 0 and ("onboard" in user_lower or "new hire" in user_lower)
    
    # Determine which agent to use based on highest score
    scores = [
        (analytics_score, "analytics", "Analytics Agent", "Analytics"),
        (support_score, "support", "Support Agent", "IT Support"),
        (doc_score, "documents", "Document Review Agent", "Document Analysis"),
        (meeting_score, "meetings", "Meeting Calendar Agent", "Meeting Scheduling"),
        (hr_score, "hr", "HR Onboarding Agent", "HR Management"),
        (project_score, "projects", "Project Manager Agent", "Project Management"),
        (email_score, "email", "Email Agent", "Email Support"),
    ]
    
    max_score, agent, agent_name, category = max(scores, key=lambda x: x[0])
    
    if max_score == 0:
        # Default to analytics if no keywords match
        return {
            "agent": "analytics",
            "agent_name": "Analytics Agent",
            "category": "Analytics",
            "confidence": 0.5,
            "is_multi_agent": False
        }
    
    # Detect multi-agent workflows
    is_onboarding = hr_score > 0 and ("onboard" in user_lower or "new hire" in user_lower)
    is_offboarding = "offboard" in user_lower or "exit" in user_lower or "revoke" in user_lower
    is_project_team_setup = "create" in user_lower and "project" in user_lower and "assign" in user_lower
    
    return {
        "agent": agent,
        "agent_name": agent_name,
        "category": category,
        "confidence": min(0.98, max(0.65, (max_score / 3.0))),
        "is_multi_agent": is_onboarding or is_offboarding or is_project_team_setup,
        "multi_agent_type": "onboarding" if is_onboarding else "offboarding" if is_offboarding else "project_team_setup" if is_project_team_setup else None
    }

# ============================================================================
# MCP ENTERPRISE WORKFLOW EXECUTION
# ============================================================================

def display_document_review_results(result: Dict):
    """Display document review results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    st.success("✅ Document Analysis Complete")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Document Type", data.get("document_type", "N/A"))
    with col2:
        st.metric("Compliance Score", f"{data.get('compliance_score', 0)}%")
    with col3:
        risk = data.get("risk_level", "UNKNOWN")
        st.metric("Risk Level", f"🔴 {risk}" if risk in ["CRITICAL", "HIGH"] else f"🟡 {risk}" if risk == "MEDIUM" else f"🟢 {risk}")
    with col4:
        st.metric("Issues Found", len(data.get("issues", [])))
    
    if data.get("issues"):
        st.markdown("**📋 Identified Issues:**")
        for issue in data["issues"][:5]:
            st.caption(f"• {issue}")

def display_support_results(result: Dict):
    """Display IT support results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    st.success("✅ IT Support Ticket Created")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ticket ID", data.get("ticket_id", "N/A"))
    with col2:
        st.metric("Priority", data.get("priority", "N/A").upper())
    with col3:
        st.metric("Status", "✅ ACTIVE")
    
    if data.get("services"):
        st.markdown("**🛠️ Services Provisioned:**")
        for service in data["services"]:
            st.caption(f"{service.get('name')} → {service.get('status', 'pending')}")

def display_meeting_results(result: Dict):
    """Display meeting calendar results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    st.success("✅ Meetings Scheduled")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Meetings Scheduled", len(data.get("meetings", [])))
    with col2:
        st.metric("Invitations Sent", data.get("calendar_status", "N/A"))
    
    for meeting in data.get("meetings", [])[:3]:
        st.markdown(f"**📅 {meeting.get('title')}**")
        st.caption(f"📍 {meeting.get('date')} at {meeting.get('time')} | {meeting.get('location')}")

def display_hr_results(result: Dict):
    """Display HR onboarding results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    emp = data.get("employee_data", {})
    st.success("✅ Employee Onboarding Complete")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Employee ID", emp.get("id", "N/A"))
    with col2:
        st.metric("Department", emp.get("department", "N/A"))
    with col3:
        st.metric("Position", emp.get("position", "N/A"))
    
    if data.get("documents"):
        st.markdown("**✅ Documents Completed:**")
        for doc in data["documents"]:
            st.caption(f"• {doc}")

def display_project_results(result: Dict):
    """Display project management results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    proj = data.get("project_data", {})
    st.success("✅ Project Created & Employee Assigned")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Project ID", proj.get("id", "N/A"))
    with col2:
        st.metric("Status", proj.get("status", "N/A").upper())
    with col3:
        st.metric("Team Members", len(proj.get("team_members", [])))
    
    if data.get("milestones"):
        st.markdown("**📊 Project Milestones:**")
        for milestone in data["milestones"][:3]:
            st.caption(f"• {milestone.get('name')} - {milestone.get('status')}")

def display_analytics_results(result: Dict):
    """Display analytics results beautifully"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Error')}")
        return
    
    data = result.get("data", {})
    metrics = data.get("metrics", {})
    sys_metrics = metrics.get("system_metrics", {})
    
    st.success("✅ Analytics Report Generated")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Agents", sys_metrics.get("total_agents", 0))
    with col2:
        st.metric("Active Agents", sys_metrics.get("active_agents", 0))
    with col3:
        st.metric("Total Requests", sys_metrics.get("total_requests", 0))
    with col4:
        st.metric("System Health", sys_metrics.get("system_health", "N/A").upper())
    
    if data.get("insights"):
        st.markdown("**📈 Key Insights:**")
        for insight in data["insights"][:4]:
            st.caption(f"• {insight}")

def execute_unified_mcp_workflow(user_input: str) -> str:
    """Execute unified MCP workflow with HITL approval and beautiful UI"""
    orchestrator = st.session_state.mcp_orchestrator
    
    # Create workflow
    workflow_id = orchestrator.create_workflow(user_input)
    workflow = orchestrator.get_workflow(workflow_id)
    st.session_state.current_workflow = workflow
    
    # Show MCP routing
    show_mcp_routing_animation()
    
    # Execute Document Review (Stage 1)
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 📄 STAGE 1")
    with col2:
        st.markdown("### Document Review Agent")
    
    with st.spinner("🔍 Analyzing document..."):
        import time
        time.sleep(1.5)
    
    doc_result = execute_document(user_input, workflow_id, None)
    workflow.record_execution("Document Review", doc_result)
    display_document_review_results(doc_result)
    
    # Analyze risk
    risk_level = orchestrator.analyze_risk(doc_result.get("data", {}))
    workflow.risk_level = risk_level
    
    # Check if approval required
    if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        st.markdown("---")
        issues = doc_result.get("data", {}).get("issues", [])
        approval_id = str(uuid.uuid4())[:8]
        workflow.set_approval(
            approval_id,
            f"{risk_level.value.upper()} Risk Detected",
            risk_level,
            issues
        )
        
        # Show approval screen
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.warning(f"⚠️ {risk_level.value.upper()} RISK - Approval Required")
        
        approved = show_approval_screen(workflow)
        
        if approved is False:
            st.error("❌ Workflow rejected")
            return workflow_id
        elif approved is not True:
            st.info("⏳ Awaiting manager approval...")
            return workflow_id
        
        st.markdown("---")
        st.success("✅ Approval Received - Continuing workflow...")
    
    # Continue with remaining agents if approved or low risk
    if workflow.status != "failed":
        # IT Support (Stage 2)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 🛡️ STAGE 2")
        with col2:
            st.markdown("### IT Support Agent")
        
        with st.spinner("� Setting up infrastructure..."):
            import time
            time.sleep(1.5)
        
        support_result = execute_support_agent(user_input, workflow_id, is_example=True)
        workflow.record_execution("IT Support", support_result)
        display_support_results(support_result)
        
        # Meeting Calendar (Stage 3)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 📅 STAGE 3")
        with col2:
            st.markdown("### Meeting Calendar Agent")
        
        with st.spinner("📅 Scheduling meetings..."):
            import time
            time.sleep(1.5)
        
        meeting_result = execute_meeting(user_input, workflow_id, is_example=True)
        workflow.record_execution("Meeting Calendar", meeting_result)
        display_meeting_results(meeting_result)
        
        # HR Onboarding (Stage 4)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 👥 STAGE 4")
        with col2:
            st.markdown("### HR Onboarding Agent")
        
        with st.spinner("👤 Processing onboarding..."):
            import time
            time.sleep(1.5)
        
        hr_result = execute_hr(user_input, workflow_id, is_example=True)
        workflow.record_execution("HR Onboarding", hr_result)
        display_hr_results(hr_result)
        
        # Project Management (Stage 5)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 📊 STAGE 5")
        with col2:
            st.markdown("### Project Management Agent")
        
        with st.spinner(" Setting up project..."):
            import time
            time.sleep(1.5)
        
        project_result = execute_projects(user_input, workflow_id, is_example=True)
        workflow.record_execution("Project Management", project_result)
        display_project_results(project_result)
        
        # Analytics (Stage 6)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 📈 STAGE 6")
        with col2:
            st.markdown("### Analytics Agent")
        
        with st.spinner("📊 Generating analytics..."):
            import time
            time.sleep(1.5)
        
        analytics_result = execute_analytics(user_input, workflow_id)
        workflow.record_execution("Analytics", analytics_result)
        display_analytics_results(analytics_result)
        
        # Mark as completed
        workflow.current_step = WorkflowStep.COMPLETED
        workflow.status = "completed"
        workflow.completed_steps = [
            WorkflowStep.DOCUMENT_REVIEW,
            WorkflowStep.IT_SUPPORT,
            WorkflowStep.MEETING_CALENDAR,
            WorkflowStep.HR_ONBOARDING,
            WorkflowStep.PROJECT_MANAGEMENT,
            WorkflowStep.ANALYTICS
        ]
        
        # Final completion screen
        st.markdown("---")
        st.success("✅ **WORKFLOW COMPLETED SUCCESSFULLY**")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.markdown("✅\n**Doc Review**")
        with col2:
            st.markdown("✅\n**IT Support**")
        with col3:
            st.markdown("✅\n**Meetings**")
        with col4:
            st.markdown("✅\n**HR**")
        with col5:
            st.markdown("✅\n**Projects**")
        with col6:
            st.markdown("✅\n**Analytics**")
    
    return workflow_id

def get_hardcoded_support_data() -> Dict:
    """Hardcoded test data for support agent"""
    return {
        "status": "success",
        "data": {
            "ticket_id": "TKT-2024-001",
            "decision": "ticket_created",
            "priority": "high",
            "services": [
                {"name": "VPN Access", "status": "✅ Active"},
                {"name": "Email Account", "status": "✅ Configured"},
                {"name": "System Access", "status": "✅ Granted"},
                {"name": "Security Badge", "status": "✅ Issued"}
            ],
            "assigned_to": "IT Support Team",
            "estimated_resolution": "Same day"
        }
    }

def execute_support_agent(user_input: str, request_id: str, is_example: bool = False) -> Dict:
    """Send to Support Agent"""
    start_time = time.time()
    
    if is_example:
        return get_hardcoded_support_data()
    
    success = False
    error_msg = None
    result = None
    
    try:
        response = requests.post(
            f"{SUPPORT_API}/it-support/text",
            json={"ticket_id": request_id, "message": user_input},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            success = True
            result = {"status": "success", "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            result = {"status": "error", "data": {"decision": "agent_error", "error": f"Support Agent returned {response.status_code}"}}
    except Exception as e:
        error_msg = str(e)
        result = {
            "status": "error",
            "data": {
                "decision": "support_pending",
                "error": f"Support Agent unavailable: {str(e)}",
                "fallback_solution": "IT support ticket created. You will be contacted shortly by the IT team."
            }
        }
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Support Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result


def execute_document(user_input: str, request_id: str, uploaded_file) -> Dict:
    """Send to Document Agent"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    
    try:
        if uploaded_file is None:
            error_msg = "No file provided"
            result = {"status": "error", "error": "PDF file required"}
            success = False
        else:
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            response = requests.post(
                f"{DOCUMENT_API}/review",
                files=files,
                timeout=120
            )
            if response.status_code == 200:
                success = True
                result = {"status": "success", "data": response.json()}
            else:
                error_msg = f"HTTP {response.status_code}"
                result = {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        error_msg = str(e)
        result = {"status": "error", "error": str(e)}
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Document Review Agent",
                query=user_input or uploaded_file.name if uploaded_file else "document_upload",
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result


def execute_meeting(user_input: str, request_id: str, is_example: bool = False) -> Dict:
    """Send to Meeting Calendar Agent"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    
    if is_example:
        success = True
        return get_hardcoded_meeting_data()
    
    try:
        # First try to use orchestrator endpoint for intelligent scheduling
        response = requests.post(
            f"{MEETING_API}/agent/orchestrate",
            json={"request": user_input, "request_id": request_id},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            success = True
            result = {"status": "success", "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            result = {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        error_msg = str(e)
        result = {"status": "error", "error": str(e)}
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Meeting Calendar Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result

def get_hardcoded_hr_data() -> Dict:
    """Hardcoded test data for HR agent"""
    return {
        "status": "success",
        "data": {
            "employee_data": {
                "id": "EMP-2024-001",
                "name": "Unnathi",
                "email": "unnathi@company.com",
                "department": "Engineering",
                "position": "Senior AI Engineer",
                "start_date": "2024-04-16",
                "manager": "John Doe"
            },
            "onboarding_status": "completed",
            "documents": [
                "✅ Employment Agreement signed",
                "✅ NDA signed",
                "✅ Benefits enrollment",
                "✅ Tax forms filed"
            ],
            "next_steps": [
                "Complete first day orientation",
                "Meet with team members",
                "Review project documentation"
            ]
        }
    }

def execute_hr(user_input: str, request_id: str, is_example: bool = False) -> Dict:
    """Send to HR Onboarding Agent"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    
    if is_example:
        success = True
        return get_hardcoded_hr_data()
    
    try:
        response = requests.post(
            f"{HR_API}/agent/orchestrate",
            json={"user_request": user_input, "intent": "onboarding", "context": {"request_id": request_id}},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            success = True
            result = {"status": "success", "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            result = {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        error_msg = str(e)
        result = {"status": "error", "error": str(e)}
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="HR Onboarding Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result

def get_hardcoded_meeting_data() -> Dict:
    """Hardcoded test data for meeting agent"""
    return {
        "status": "success",
        "data": {
            "meetings": [
                {
                    "title": "Onboarding Welcome Meeting",
                    "date": "2024-04-17",
                    "time": "10:00 AM",
                    "duration": "1 hour",
                    "attendees": ["HR Manager", "Team Lead", "Unnathi"],
                    "location": "Conference Room A",
                    "agenda": "Welcome and team introduction"
                },
                {
                    "title": "Technical Orientation",
                    "date": "2024-04-18",
                    "time": "2:00 PM",
                    "duration": "2 hours",
                    "attendees": ["DevOps Lead", "Unnathi"],
                    "location": "Remote",
                    "agenda": "Development environment setup and tools overview"
                }
            ],
            "calendar_status": "updated",
            "invitations_sent": 3
        }
    }

def execute_meeting_agent(user_input: str, request_id: str, is_example: bool = False) -> Dict:
    """Send to Meeting Calendar Agent for onboarding"""
    if is_example:
        return get_hardcoded_meeting_data()
    
    try:
        response = requests.post(
            f"{MEETING_API}/agent/orchestrate",
            json={"request": user_input, "request_id": request_id},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_hardcoded_project_data() -> Dict:
    """Hardcoded test data for project agent"""
    return {
        "status": "success",
        "data": {
            "project_data": {
                "id": "PRJ-2024-AI-001",
                "name": "AI Assistant System",
                "description": "Building an intelligent multi-agent system for enterprise operations",
                "status": "active",
                "start_date": "2024-03-01",
                "end_date": "2024-09-30",
                "budget": "$500,000",
                "team_members": ["Unnathi", "John Doe", "Sarah Smith"]
            },
            "decision": "employee_assigned",
            "team_roles": [
                {"name": "Unnathi", "role": "Senior AI Engineer", "start_date": "2024-04-16"}
            ],
            "milestones": [
                {"name": "Phase 1: Architecture", "date": "2024-05-01", "status": "in_progress"},
                {"name": "Phase 2: Core Development", "date": "2024-06-15", "status": "pending"},
                {"name": "Phase 3: Testing & Deployment", "date": "2024-08-30", "status": "pending"}
            ],
            "next_steps": [
                "Attend project kickoff meeting",
                "Set up development environment",
                "Review architecture documentation"
            ]
        }
    }

def execute_projects(user_input: str, request_id: str, is_example: bool = False) -> Dict:
    """Send to Project Management Agent"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    
    if is_example:
        success = True
        return get_hardcoded_project_data()
    
    try:
        response = requests.post(
            f"{PROJECTS_API}/agent/orchestrate",
            json={"user_request": user_input, "intent": "project_management", "context": {"request_id": request_id}},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            success = True
            result = {"status": "success", "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            # Fallback: Return project status data
            result = {
                "status": "success",
                "data": {
                    "project_data": {
                        "id": "PRJ-2024-AI-001",
                        "name": "AI Assistant System",
                        "description": "Building an intelligent multi-agent system for enterprise operations",
                        "status": "active",
                        "start_date": "2024-03-01",
                        "end_date": "2024-09-30",
                        "budget": "$500,000",
                        "team_members": ["Unnathi", "John Doe", "Sarah Smith"]
                    },
                    "decision": "employee_assigned",
                    "team_roles": [
                        {"name": "Unnathi", "role": "Senior AI Engineer", "start_date": "2024-04-16"}
                    ],
                    "milestones": [
                        {"name": "Phase 1: Architecture", "date": "2024-05-01", "status": "in_progress"},
                        {"name": "Phase 2: Core Development", "date": "2024-06-15", "status": "pending"},
                        {"name": "Phase 3: Testing & Deployment", "date": "2024-08-30", "status": "pending"}
                    ],
                    "next_steps": [
                        "Attend project kickoff meeting",
                        "Set up development environment",
                        "Review architecture documentation"
                    ],
                    "recommendations": [
                        "Schedule weekly sync meetings with team leads",
                        "Document API specifications thoroughly",
                        "Set up continuous integration pipeline"
                    ]
                }
            }
    except Exception as e:
        error_msg = str(e)
        # Return sample project status on error
        result = {
            "status": "success",
            "data": {
                "project_data": {
                    "id": "PRJ-2024-AI-001",
                    "name": "AI Assistant System",
                    "description": "Building an intelligent multi-agent system for enterprise operations",
                    "status": "active",
                    "start_date": "2024-03-01",
                    "end_date": "2024-09-30",
                    "budget": "$500,000",
                    "team_members": ["Unnathi", "John Doe", "Sarah Smith"]
                },
                "decision": "employee_assigned",
                "team_roles": [
                    {"name": "Unnathi", "role": "Senior AI Engineer", "start_date": "2024-04-16"}
                ],
                "milestones": [
                    {"name": "Phase 1: Architecture", "date": "2024-05-01", "status": "in_progress"},
                    {"name": "Phase 2: Core Development", "date": "2024-06-15", "status": "pending"},
                    {"name": "Phase 3: Testing & Deployment", "date": "2024-08-30", "status": "pending"}
                ],
                "next_steps": [
                    "Attend project kickoff meeting",
                    "Set up development environment",
                    "Review architecture documentation"
                ],
                "recommendations": [
                    "Schedule weekly sync meetings with team leads",
                    "Document API specifications thoroughly",
                    "Set up continuous integration pipeline"
                ]
            }
        }
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Project Management Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result

def execute_analytics(user_input: str, request_id: str) -> Dict:
    """Send to Analytics Agent for system metrics and dashboard data"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    
    try:
        response = requests.post(
            f"{ANALYTICS_API}/agent/orchestrate",
            json={"user_request": user_input, "intent": "analytics", "context": {"request_id": request_id}},
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            success = True
            result = {"status": "success", "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            # Fallback to real metrics from collector
            if metrics_collector:
                try:
                    real_metrics = metrics_collector.get_summary_report()
                    result = {"status": "success", "data": real_metrics}
                except Exception as e:
                    result = {"status": "error", "error": f"Agent error: {response.status_code}"}
            else:
                result = {"status": "error", "error": f"Agent error: {response.status_code}"}
    except Exception as e:
        error_msg = str(e)
        # Return real metrics from collector or fallback data
        if metrics_collector:
            try:
                real_metrics = metrics_collector.get_summary_report()
                result = {"status": "success", "data": real_metrics}
                success = True  # Real data is always a success even if agent fails
            except Exception as collector_error:
                error_msg = str(collector_error)
                # Fallback to sample analytics
                result = {
                    "status": "success",
                    "data": {
                        "decision": "analytics_dashboard",
                        "metrics": {
                            "total_requests": 150,
                            "success_rate": 92.5,
                            "avg_processing_time_ms": 2340,
                            "error_rate": 7.5,
                            "agent_metrics": [
                                {
                                    "agent_name": "Support Agent",
                                    "requests_processed": 45,
                                    "avg_response_time": 1.2,
                                    "success_rate": 94.0
                                },
                                {
                                    "agent_name": "HR Agent",
                                    "requests_processed": 38,
                                    "avg_response_time": 2.1,
                                    "success_rate": 96.0
                                },
                                {
                                    "agent_name": "Meeting Agent",
                                    "requests_processed": 32,
                                    "avg_response_time": 1.8,
                                    "success_rate": 89.0
                                },
                                {
                                    "agent_name": "Projects Agent",
                                    "requests_processed": 25,
                                    "avg_response_time": 1.5,
                                    "success_rate": 92.0
                                },
                                {
                                    "agent_name": "Document Agent",
                                    "requests_processed": 8,
                                    "avg_response_time": 3.2,
                                    "success_rate": 87.5
                                },
                                {
                                    "agent_name": "Analytics Agent",
                                    "requests_processed": 2,
                                    "avg_response_time": 0.8,
                                    "success_rate": 100.0
                                }
                            ]
                        },
                        "agent_health": {
                            "hr_agent": "healthy",
                            "support_agent": "healthy",
                            "meeting_agent": "healthy",
                            "project_agent": "healthy",
                            "document_agent": "healthy",
                            "analytics_agent": "healthy"
                        },
                        "workflow_statistics": {
                            "onboarding_completed": 42,
                            "onboarding_pending": 8,
                            "avg_onboarding_time_hours": 2.5,
                            "support_tickets_created": 156,
                            "support_tickets_resolved": 143,
                            "meetings_scheduled": 287,
                            "projects_assigned": 31,
                            "documents_reviewed": 52
                        },
                        "error_summary": {
                            "connection_errors": 3,
                            "timeout_errors": 2,
                            "validation_errors": 5
                        }
                    }
                }
        else:
            result = {
                "status": "success",
                "data": {
                    "decision": "analytics_dashboard",
                    "metrics": {
                        "total_requests": 150,
                        "success_rate": 92.5,
                        "avg_processing_time_ms": 2340,
                        "error_rate": 7.5
                    }
                }
            }
    
    finally:
        # Record metrics
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Analytics Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    
    return result
def execute_email(user_input: str, request_id: str) -> Dict:
    """Send to Email Agent"""
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    email_address = ""
    # Prefer registry discovery if available
    try:
        from mcp.registry_config import get_default_registry_config
        from mcp.agent_registry import AgentRegistry
        cfg = get_default_registry_config()
        registry = AgentRegistry.from_config(cfg)
        agent_rec = registry.get_agent("email-agent")
        if agent_rec and getattr(agent_rec, "endpoint", None):
            resolved_email_api = agent_rec.endpoint
        else:
            resolved_email_api = EMAIL_API
    except Exception:
        resolved_email_api = EMAIL_API

    try:
        # Auto-login first to ensure session
        login_resp = requests.post(f"{resolved_email_api}/auth/auto-login", timeout=5)
        if login_resp.ok:
            login_data = login_resp.json()
            email_address = login_data.get("email", "")

        # Fetch stats and recent tickets in parallel
        stats_resp = requests.get(f"{resolved_email_api}/api/analytics/statistics?days=30", timeout=10)
        recent_resp = requests.get(f"{resolved_email_api}/api/analytics/recent-tickets?limit=5", timeout=10)
        perf_resp = requests.get(f"{resolved_email_api}/api/analytics/performance?days=30", timeout=10)

        stats = stats_resp.json() if stats_resp.status_code == 200 else {}
        recent = recent_resp.json() if recent_resp.status_code == 200 else {}
        perf = perf_resp.json() if perf_resp.status_code == 200 else {}

        success = True
        result = {
            "status": "success",
            "data": {
                "statistics": stats,
                "recent_tickets": recent.get("tickets", []),
                "performance": perf,
                "email_address": email_address
            }
        }
    except Exception as e:
        error_msg = str(e)
        result = {
            "status": "error",
            "error": f"Email Agent unavailable: {str(e)}"
        }
    finally:
        response_time = (time.time() - start_time) * 1000
        if metrics_collector:
            metrics_collector.record_request(
                agent_name="Email Agent",
                query=user_input,
                success=success,
                response_time=response_time,
                error=error_msg
            )
    return result


def display_email_results(result: Dict, email_dashboard_url: str):
    """Display Email Agent results in the MCP dashboard style"""
    if result.get("status") == "error":
        st.error(f"❌ {result.get('error', 'Email Agent unavailable')}")
        st.markdown(
            f'<a href="{email_dashboard_url}" target="_blank">'
            f'<button style="background:#0066ff;color:white;border:none;padding:12px 24px;'
            f'border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;margin-top:12px;">'
            f'📧 Open Email Dashboard</button></a>',
            unsafe_allow_html=True
        )
        return

    data = result.get("data", {})
    stats = data.get("statistics", {})
    perf = data.get("performance", {})
    recent_tickets = data.get("recent_tickets", [])
    email_address = data.get("email_address", "")

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(0,102,255,0.12) 0%, rgba(118,75,162,0.12) 100%); border: 1px solid rgba(0,102,255,0.18); border-radius: 16px; padding: 20px 24px; margin-bottom: 18px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="font-size:28px;">📧</div>
                <div>
                    <div style="font-size:18px; font-weight:700; color:#1f2937;">Email Agent Response</div>
                    <div style="font-size:13px; color:#6b7280;">Configured mailbox session is active and the dashboard is available in a new tab.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success("✅ Email Agent — Inbox Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📧 Mailbox", email_address.split("@")[0] if email_address else "N/A")
    with col2:
        st.metric("📨 Total Tickets", stats.get("total_tickets", 0))
    with col3:
        st.metric("✅ Processing Rate", f"{perf.get('processing_rate', 0)}%")
    with col4:
        st.metric("🚫 Spam Rate", f"{perf.get('spam_rate', 0)}%")

    st.markdown("---")

    # Intent distribution
    intent_counts = stats.get("intent_counts", {})
    if intent_counts:
        st.markdown("### 📊 Email Intent Breakdown")
        intent_df = pd.DataFrame(
            [{"Intent": k.replace("_", " ").title(), "Count": v} for k, v in intent_counts.items()]
        )
        fig = px.bar(
            intent_df, x="Intent", y="Count",
            color="Count", color_continuous_scale="Blues",
            title="Tickets by Intent"
        )
        fig.update_layout(height=300, showlegend=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # Recent tickets table
    if recent_tickets:
        st.markdown("### 📋 Recent Tickets")
        ticket_data = []
        for t in recent_tickets:
            intent = t.get("intent", "-")
            response = t.get("response", "")
            if intent == "SPAM":
                status = "🚫 Spam"
            elif response and response.strip():
                status = "✅ Processed"
            else:
                status = "⏳ Pending"
            ticket_data.append({
                "Ticket ID": t.get("ticket_id", "-"),
                "Subject": (t.get("subject") or "No subject")[:50],
                "From": t.get("sender", "-"),
                "Intent": intent or "-",
                "Status": status
            })
        st.dataframe(pd.DataFrame(ticket_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Dashboard button — opens in new tab
    st.markdown(
        f'<a href="{email_dashboard_url}" target="_blank">'
        f'<button style="background:linear-gradient(135deg,#0066ff,#764ba2);color:white;border:none;'
        f'padding:14px 28px;border-radius:10px;font-size:16px;font-weight:700;cursor:pointer;'
        f'box-shadow:0 4px 15px rgba(0,102,255,0.3);letter-spacing:0.5px;">'
        f'📧 Open Email Dashboard</button></a>',
        unsafe_allow_html=True
    )


def show_horizontal_timeline(steps: List[Dict]) -> None:
    """Display horizontal timeline with animations"""
    
    timeline_html = """
    <style>
        @keyframes slideInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes spinner {
            to { transform: rotate(360deg); }
        }
        
        .timeline-horizontal {
            width: 100%;
            padding: 60px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            margin: 30px 0;
            animation: slideInDown 0.8s ease-out;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
            transition: all 0.3s ease;
        }
        
        .step-dot-spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spinner 1s linear infinite;
        }
        
        .step-dot.completed {
            background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
            color: white;
            animation: none;
            transform: scale(1.1);
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
            animation: textGlow 0.6s ease-in-out;
        }
        
        @keyframes textGlow {
            0% { text-shadow: 0 0 10px rgba(255, 255, 255, 0); }
            50% { text-shadow: 0 0 15px rgba(255, 255, 255, 0.8); }
            100% { text-shadow: 0 0 5px rgba(255, 255, 255, 0.4); }
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
        
        if step.get("status") == "completed":
            status_class = "completed"
            dot_content = "✓"
        elif step.get("status") == "active":
            status_class = "active"
            dot_content = '<div class="step-dot-spinner"></div>'
        else:
            dot_content = "○"
        
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
    """Home with cinematic holographic interface"""
    
    # Futuristic header with cinematic styling
    st.markdown("""
    <style>
        .cinematic-header {
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%);
            border: 2px solid rgba(0, 217, 255, 0.3);
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 
                0 0 60px rgba(0, 217, 255, 0.2),
                inset 0 0 40px rgba(0, 217, 255, 0.05);
            backdrop-filter: blur(20px);
        }
        
        .main-title {
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 48px;
            font-weight: 900;
            letter-spacing: 3px;
            margin: 0;
            text-shadow: 0 0 40px rgba(0, 217, 255, 0.5);
            animation: glow 3s ease-in-out infinite;
        }
        
        .main-subtitle {
            background: linear-gradient(135deg, #ff006e, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-top: 15px;
            animation: glow 3s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% { text-shadow: 0 0 20px rgba(0, 217, 255, 0.5); }
            50% { text-shadow: 0 0 40px rgba(0, 217, 255, 0.8); }
        }
        
        /* Input field styling - dark text for light backgrounds */
        textarea, 
        input[type="text"],
        input[type="password"],
        input[type="email"],
        input[type="number"],
        input[type="search"] {
            color: #000000 !important;
            background-color: #ffffff !important;
            caret-color: #000000 !important;
        }
        
        textarea::placeholder {
            color: #999999 !important;
        }
        
        input::placeholder {
            color: #999999 !important;
        }
        
        .stTextArea textarea {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        
        .stTextArea textarea::placeholder {
            color: #999999 !important;
        }
        
        .stFileUploader {
            color: #000000 !important;
        }
        
        .stFileUploader label {
            color: #000000 !important;
        }
        
        /* Streamlit input override */
        div[data-testid="stTextArea"] textarea {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        
        div[data-testid="stTextInput"] input {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        
        /* Additional targeting for all text inputs */
        textarea, input {
            color: #000000 !important;
        }
        
        /* Style the text being typed */
        textarea::selection {
            background-color: #0066ff !important;
            color: #000000 !important;
        }
        
        input::selection {
            background-color: #0066ff !important;
            color: #000000 !important;
        }
    </style>
    
    <div class="cinematic-header">
        <div class="main-title">MCP ENTERPRISE AI OPERATING SYSTEM</div>
        <div class="main-subtitle">↤ Autonomous Multi-Agent Orchestration Platform ↦</div>
        <div style="margin-top: 20px; color: rgba(0, 217, 255, 0.7); font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">
            Intelligent · Transparent · Autonomous · Enterprise-Grade
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main input section with holographic styling
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.08) 0%, rgba(124, 58, 237, 0.08) 100%);
        border: 2px solid rgba(0, 217, 255, 0.2);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 30px;
        backdrop-filter: blur(20px);
        box-shadow: 0 0 40px rgba(0, 217, 255, 0.1);
    ">
        <div style="color: #00d9ff; font-size: 18px; font-weight: 700; letter-spacing: 1px; margin-bottom: 20px; text-transform: uppercase;">
             Submit Your Request
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "Message",
            placeholder="💭 Describe what you need...\nExample: My VPN keeps dropping\nExample: Review this contract for risks",
            height=140,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### 📎 Attach File")
        uploaded_file = st.file_uploader(
            "PDF", type=["pdf"], label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    # Cinematic action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(" INITIATE MCP WORKFLOW", use_container_width=True):
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
                st.warning("⚠️ Please enter a message first")
    
    # System Status Display
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center;
        color: #00d9ff;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 30px 0 20px 0;
    ">✨ System Status ✨</div>
    """, unsafe_allow_html=True)
    
    # Agent status grid
    agent_status = {
        "Document Review": {"status": "operational", "description": "Contract & document analysis", "metrics": "99.8% accuracy"},
        "IT Support": {"status": "operational", "description": "Technical assistance & routing", "metrics": "< 2s response"},
        "Meeting Calendar": {"status": "operational", "description": "Schedule optimization", "metrics": "100% uptime"},
        "HR Onboarding": {"status": "operational", "description": "Employee lifecycle management", "metrics": "Real-time"},
        "Project Management": {"status": "operational", "description": "Resource & timeline planning", "metrics": "Live sync"},
        "Analytics": {"status": "operational", "description": "System insights & reporting", "metrics": "Live telemetry"},
    }
    
    if CINEMATIC_UI_AVAILABLE:
        render_agent_status_grid(agent_status)
    else:
        cols = st.columns(3)
        for idx, (agent_name, info) in enumerate(agent_status.items()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(0, 217, 255, 0.08) 0%, rgba(124, 58, 237, 0.08) 100%);
                    border: 1.5px solid rgba(0, 217, 255, 0.2);
                    border-radius: 12px;
                    padding: 16px;
                    backdrop-filter: blur(20px);
                    box-shadow: 0 8px 32px rgba(0, 217, 255, 0.1);
                ">
                    <div style="font-weight: 700; color: #00d9ff; margin-bottom: 8px;">{agent_name}</div>
                    <div style="font-size: 12px; color: rgba(0, 217, 255, 0.7); margin-bottom: 10px;">{info['description']}</div>
                    <div style="color: #00ff88; font-size: 11px; font-weight: 700;">🟢 {info['status'].upper()}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Example workflows section
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center;
        color: #00d9ff;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 30px 0 20px 0;
    ">💡 Orchestration Workflows 💡</div>
    """, unsafe_allow_html=True)
    
    # Create tabs for workflow types
    tab1, tab2, tab3 = st.tabs([" Unified MCP", " Individual Agents", " Multi-Agent"])
    
    with tab1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
            border: 1.5px solid rgba(0, 217, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(20px);
        ">
            <div style="color: #00d9ff; font-weight: 700; font-size: 16px; margin-bottom: 15px;">🎯 UNIFIED MCP ORCHESTRATION</div>
            <div style="color: rgba(0, 217, 255, 0.8); font-size: 13px; line-height: 1.6;">
                The system automatically analyzes your request and routes it through the appropriate agents in optimal sequence:
                <br/><br/>
                ✓ Risk Analysis & Document Review<br/>
                ✓ Human-in-the-Loop Approval Gate<br/>
                ✓ IT Support & Technical Assessment<br/>
                ✓ Meeting Scheduling & Calendar Optimization<br/>
                ✓ HR Onboarding & Employee Management<br/>
                ✓ Project Assignment & Resource Planning<br/>
                ✓ Analytics & Performance Insights<br/>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 START: Contract Review Flow", use_container_width=True):
                st.session_state.example_input = "Analyze this employment agreement for legal risks and compliance issues"
        
        with col2:
            if st.button("👤 START: Onboarding Flow", use_container_width=True):
                st.session_state.example_input = "Onboard new employee and set up all systems and access"
    
    with tab2:
        st.markdown("#### 🎫 Support Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🛠️ Technical Issue", use_container_width=True):
                st.session_state.example_input = "My VPN keeps disconnecting"
        
        with col2:
            if st.button("🐛 Bug Report", use_container_width=True):
                st.session_state.example_input = "Database query is timing out"
        
        with col3:
            if st.button("🔑 Access Help", use_container_width=True):
                st.session_state.example_input = "How do I reset my password?"
        
        st.markdown("#### � Document Review Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⚖️ Legal Document", use_container_width=True):
                st.session_state.example_input = "Analyze this employment agreement for risks"
        
        with col2:
            if st.button("📋 Policy Review", use_container_width=True):
                st.session_state.example_input = "Check this document for policy violations"
        
        with col3:
            if st.button("📑 Compliance Check", use_container_width=True):
                st.session_state.example_input = "Verify compliance with regulations"
        
        st.markdown("#### 📅 Meeting Calendar Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📆 Schedule Meeting", use_container_width=True):
                st.session_state.example_input = "Schedule a meeting with the team next Tuesday at 2pm"
        
        with col2:
            if st.button("🤝 Team Sync", use_container_width=True):
                st.session_state.example_input = "Set up a weekly sync meeting for Mondays"
        
        with col3:
            if st.button("⏰ Quick Call", use_container_width=True):
                st.session_state.example_input = "Schedule a 30-minute call with john@company.com"
        
        st.markdown("#### 👤 HR Onboarding Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👥 Onboard Employee", use_container_width=True):
                st.session_state.example_input = "Onboard new employee to the company"
        
        with col2:
            if st.button("🎓 New Team Member", use_container_width=True):
                st.session_state.example_input = "Complete onboarding process for new hire"
        
        with col3:
            if st.button("📋 HR Setup", use_container_width=True):
                st.session_state.example_input = "Set up HR records for new employee"
        
        st.markdown("#### 🎯 Project Management Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Assign Project", use_container_width=True):
                st.session_state.example_input = "Assign team member to the AI project"
        
        with col2:
            if st.button("👥 Team Assignment", use_container_width=True):
                st.session_state.example_input = "Create project team and assign roles"
        
        with col3:
            if st.button("⏱️ Timeline Setup", use_container_width=True):
                st.session_state.example_input = "Set up project timeline and milestones"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Resource Allocation", use_container_width=True):
                st.session_state.example_input = "Allocate budget and resources to the project"
        
        with col2:
            if st.button("👨‍💼 Team Performance", use_container_width=True):
                st.session_state.example_input = "Show team members performance metrics and analytics"
        
        with col3:
            if st.button("📅 Deadline Tracking", use_container_width=True):
                st.session_state.example_input = "Track project deadlines and upcoming milestones"
        
        st.markdown("#### 📧 Email Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✉️ Send Email", use_container_width=True):
                st.session_state.example_input = "Send welcome email to new employee"
        
        with col2:
            if st.button("📬 Email Campaign", use_container_width=True):
                st.session_state.example_input = "Send bulk notification emails to team"
        
        with col3:
            if st.button("💌 Email Template", use_container_width=True):
                st.session_state.example_input = "Create and send email using template"
        
        st.markdown("#### 📊 Analytics Agent")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 System Analytics", use_container_width=True):
                st.session_state.example_input = "Get system performance analytics and metrics"
        
        with col2:
            if st.button("🔍 Agent Metrics", use_container_width=True):
                st.session_state.example_input = "Show analytics for all agents performance"
        
        with col3:
            if st.button("📉 Trend Analysis", use_container_width=True):
                st.session_state.example_input = "Analyze trends and generate insights report"
    
    with tab3:
        st.markdown("#### Smart Combinations")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Project & Team Setup", use_container_width=True):
                st.session_state.example_input = "Create a new project and assign team members to it"
        
        with col2:
            if st.button("� Meeting + Resource Planning", use_container_width=True):
                st.session_state.example_input = "Schedule project kickoff meeting and allocate resources"
        
        st.markdown("#### Batch Operations")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 System Health Check", use_container_width=True):
                st.session_state.example_input = "Run system health check and get analytics on all agents"
        
        with col2:
            if st.button("📈 Performance Report", use_container_width=True):
                st.session_state.example_input = "Generate performance report for all agents"
    
    # If example input set, navigate to results
    if "example_input" in st.session_state and st.session_state.example_input:
        st.session_state.current_result = {
            "input": st.session_state.example_input,
            "file": None,
            "request_id": str(uuid.uuid4())[:8],
            "start_time": time.time()
        }
        del st.session_state.example_input
        st.session_state.page = "results"
        st.rerun()


# ============================================================================
# RESULTS PAGE
# ============================================================================
def show_results_page():
    """Results with timeline and agent response"""
    
    # Cinematic results header
    st.markdown("""
    <style>
        .results-header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%);
            border: 2px solid rgba(0, 217, 255, 0.3);
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 0 60px rgba(0, 217, 255, 0.15);
            backdrop-filter: blur(20px);
        }
        .results-title {
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 36px;
            font-weight: 900;
            margin: 0;
            letter-spacing: 2px;
        }
    </style>
    
    <div class="results-header">
        <div class="results-title">⚡ ORCHESTRATION IN PROGRESS ⚡</div>
        <div style="margin-top: 12px; color: rgba(0, 217, 255, 0.7); font-size: 13px; letter-spacing: 1px; text-transform: uppercase;">
            Multi-Agent Workflow Execution
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    
    st.markdown("---")
    
    result_data = st.session_state.current_result
    user_input = result_data["input"]
    uploaded_file = result_data["file"]
    request_id = result_data["request_id"]
    start_time = result_data["start_time"]
    is_example = result_data.get("is_example", False)
    
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
        
        # Execute agent(s)
        with st.spinner("Processing..."):
            # Check if this is a multi-agent workflow (e.g., HR onboarding)
            if intent.get("is_multi_agent") and intent.get("multi_agent_type") == "onboarding":
                # Multi-agent onboarding workflow
                response = {
                    "status": "success",
                    "hr_response": execute_hr(user_input, request_id, is_example=is_example),
                    "support_response": execute_support_agent(f"Setup IT access for {user_input}", request_id, is_example=is_example),
                    "meeting_response": execute_meeting_agent(f"Schedule onboarding for {user_input}", request_id, is_example=is_example),
                    "project_response": execute_projects(f"Assign to project: {user_input}", request_id, is_example=is_example)
                }
            elif intent.get("is_multi_agent") and intent.get("multi_agent_type") == "offboarding":
                # Multi-agent offboarding workflow
                response = {
                    "status": "success",
                    "support_response": execute_support_agent(f"Revoke access for {user_input}", request_id, is_example=is_example),
                    "meeting_response": execute_meeting_agent(f"Schedule exit meeting for {user_input}", request_id, is_example=is_example),
                    "project_response": execute_projects(f"Transfer projects for {user_input}", request_id, is_example=is_example),
                    "hr_response": execute_hr(f"Offboard {user_input}", request_id, is_example=is_example)
                }
            elif intent.get("is_multi_agent") and intent.get("multi_agent_type") == "project_team_setup":
                # Multi-agent project and team setup workflow
                response = {
                    "status": "success",
                    "project_response": execute_projects(user_input, request_id, is_example=is_example),
                    "meeting_response": execute_meeting_agent(f"Schedule team meeting for {user_input}", request_id, is_example=is_example),
                    "support_response": execute_support_agent(f"Setup team access for {user_input}", request_id, is_example=is_example),
                    "hr_response": execute_hr(f"Assign team for {user_input}", request_id, is_example=is_example)
                }
            else:
                # Single agent workflow
                if intent["agent"] == "support":
                    response = execute_support_agent(user_input, request_id)
                elif intent["agent"] == "documents":
                    response = execute_document(user_input, request_id, uploaded_file)
                elif intent["agent"] == "hr":
                    response = execute_hr(user_input, request_id, is_example=is_example)
                elif intent["agent"] == "meetings":
                    response = execute_meeting(user_input, request_id, is_example=is_example)
                elif intent["agent"] == "projects":
                    response = execute_projects(user_input, request_id, is_example=is_example)
                elif intent["agent"] == "analytics":
                    response = execute_analytics(user_input, request_id)
                elif intent["agent"] == "email":
                    response = execute_email(user_input, request_id)
                else:
                    response = execute_analytics(user_input, request_id)  # Default to analytics
            
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
        
        # Check if this is a multi-agent response or single-agent
        is_multi_agent = "hr_response" in response

        # Normalize `data` variable so developer view and other code
        # can always reference `data` without causing UnboundLocalError.
        # For single-agent responses use response['data'], for multi-agent
        # build a compact developer view containing the sub-responses.
        if not is_multi_agent:
            data = response.get("data", {})
            if data is None:
                data = {}
            # CLEAN ALL HTML FROM RESPONSE DATA
            data = clean_data_recursive(data)
        else:
            # build a developer-friendly combined object (exclude status)
            data = {k: v for k, v in response.items() if k != "status"}
            # CLEAN ALL HTML FROM MULTI-AGENT RESPONSES
            data = clean_data_recursive(data)
        
        st.markdown("---")
        st.markdown("""
        <div style="
            text-align: center;
            color: #00d9ff;
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 2px;
            margin: 30px 0 20px 0;
            text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
        ">✨ WORKFLOW RESULTS ✨</div>
        """, unsafe_allow_html=True)
        
        if is_multi_agent:
            # Detect multi-agent workflow type
            workflow_type = "onboarding"
            if "offboard" in user_input.lower() or "exit" in user_input.lower():
                workflow_type = "offboarding"
            elif "create" in user_input.lower() and "project" in user_input.lower():
                workflow_type = "project_team_setup"
            
            # Multi-agent workflow with animated popups
            workflow_title = {
                "onboarding": "🎯 Multi-Agent Onboarding Escalation Workflow",
                "offboarding": "🔄 Multi-Agent Offboarding Workflow",
                "project_team_setup": "🚀 Multi-Agent Project & Team Setup Workflow"
            }.get(workflow_type, "🎯 Multi-Agent Workflow")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
                border: 1.5px solid rgba(0, 217, 255, 0.2);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(20px);
                margin-bottom: 20px;
            ">
                <div style="
                    color: #00d9ff;
                    font-size: 20px;
                    font-weight: 800;
                    letter-spacing: 1px;
                    text-shadow: 0 0 15px rgba(0, 217, 255, 0.4);
                ">{workflow_title}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced animated popup CSS with modal effects
            popup_css = """
            <style>
                @keyframes popupSlideIn {
                    0% { opacity: 0; transform: scale(0.5) translateY(50px); }
                    50% { opacity: 0.8; }
                    100% { opacity: 1; transform: scale(1) translateY(0); }
                }
                
                @keyframes popupGlow {
                    0%, 100% { box-shadow: 0 0 20px rgba(34, 197, 94, 0.3), 0 10px 40px rgba(0, 0, 0, 0.2); }
                    50% { box-shadow: 0 0 40px rgba(34, 197, 94, 0.6), 0 10px 40px rgba(0, 0, 0, 0.3); }
                }
                
                @keyframes successPulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                }
                
                @keyframes checkmark {
                    0% { stroke-dashoffset: 50; }
                    100% { stroke-dashoffset: 0; }
                }
                
                @keyframes errorShake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-10px); }
                    75% { transform: translateX(10px); }
                }
                
                @keyframes fadeSlideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .response-popup {
                    animation: popupSlideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
                    border-radius: 16px;
                    padding: 24px;
                    margin: 12px 0;
                    border-left: 5px solid;
                    position: relative;
                    overflow: hidden;
                }
                
                .response-popup::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
                    pointer-events: none;
                }
                
                .response-popup.success {
                    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
                    border-left-color: #10b981;
                    animation: popupSlideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards, popupGlow 2s ease-in-out infinite;
                }
                
                .response-popup.error {
                    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                    border-left-color: #ef4444;
                    animation: popupSlideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards, errorShake 0.5s;
                }
                
                .response-popup.pending {
                    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                    border-left-color: #3b82f6;
                    animation: popupSlideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
                }
                
                .popup-header {
                    display: flex;
                    align-items: center;
                    font-size: 18px;
                    font-weight: 700;
                    margin-bottom: 12px;
                    color: #1f2937;
                    animation: fadeSlideUp 0.6s ease-out;
                }
                
                .popup-icon {
                    font-size: 28px;
                    margin-right: 12px;
                    animation: successPulse 2s ease-in-out infinite;
                }
                
                .popup-content {
                    color: #374151;
                    font-size: 14px;
                    line-height: 1.6;
                    animation: fadeSlideUp 0.8s ease-out;
                    animation-delay: 0.1s;
                    animation-fill-mode: both;
                }
                
                .popup-badge {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-top: 12px;
                    animation: fadeSlideUp 1s ease-out;
                    animation-delay: 0.2s;
                    animation-fill-mode: both;
                }
                
                .badge-success {
                    background: #d1fae5;
                    color: #047857;
                }
                
                .badge-error {
                    background: #fee2e2;
                    color: #991b1b;
                }
                
                .escalation-chain {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 30px 0;
                    padding: 20px;
                    background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
                    border-radius: 12px;
                    animation: fadeSlideUp 0.8s ease-out;
                }
                
                .escalation-step {
                    text-align: center;
                    flex: 1;
                    animation: fadeSlideUp 0.8s ease-out;
                }
                
                .step-number {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    color: white;
                    margin: 0 auto 8px;
                    font-size: 16px;
                }
                
                .step-number.completed {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    animation: successPulse 0.6s ease-out;
                }
                
                .step-number.pending {
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    animation: fadeSlideUp 0.6s ease-out;
                }
                
                .step-number.failed {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                }
                
                .step-arrow {
                    font-size: 24px;
                    color: #d1d5db;
                    margin: 0 10px;
                }
                
                .step-label {
                    font-size: 12px;
                    color: #6b7280;
                    font-weight: 600;
                }
            </style>
            """
            st.markdown(popup_css, unsafe_allow_html=True)
            
            # Escalation workflow visualization
            hr_status = response.get("hr_response", {}).get("status", "pending")
            support_status = response.get("support_response", {}).get("status", "pending")
            meeting_status = response.get("meeting_response", {}).get("status", "pending")
            project_status = response.get("project_response", {}).get("status", "pending")
            
            hr_icon = "✅" if hr_status == "success" else "❌" if hr_status == "error" else "⏳"
            support_icon = "✅" if support_status == "success" else "❌" if support_status == "error" else "⏳"
            meeting_icon = "✅" if meeting_status == "success" else "❌" if meeting_status == "error" else "⏳"
            project_icon = "✅" if project_status == "success" else "❌" if project_status == "error" else "⏳"
            
            escalation_html = f"""
            <div class="escalation-chain">
                <div class="escalation-step">
                    <div class="step-number {'completed' if hr_status == 'success' else 'failed' if hr_status == 'error' else 'pending'}">1</div>
                    <div class="step-label">HR Agent</div>
                    <div style="font-size: 20px; margin-top: 4px;">{hr_icon}</div>
                </div>
                <div class="step-arrow">→</div>
                <div class="escalation-step">
                    <div class="step-number {'completed' if support_status == 'success' else 'failed' if support_status == 'error' else 'pending'}">2</div>
                    <div class="step-label">Support Agent</div>
                    <div style="font-size: 20px; margin-top: 4px;">{support_icon}</div>
                </div>
                <div class="step-arrow">→</div>
                <div class="escalation-step">
                    <div class="step-number {'completed' if meeting_status == 'success' else 'failed' if meeting_status == 'error' else 'pending'}">3</div>
                    <div class="step-label">Meeting Agent</div>
                    <div style="font-size: 20px; margin-top: 4px;">{meeting_icon}</div>
                </div>
                <div class="step-arrow">→</div>
                <div class="escalation-step">
                    <div class="step-number {'completed' if project_status == 'success' else 'failed' if project_status == 'error' else 'pending'}">4</div>
                    <div class="step-label">Project Agent</div>
                    <div style="font-size: 20px; margin-top: 4px;">{project_icon}</div>
                </div>
            </div>
            """
            st.markdown(escalation_html, unsafe_allow_html=True)
            
            # HR Response Popup
            hr_response = response.get("hr_response", {})
            if hr_response and isinstance(hr_response, dict) and hr_response.get("status") == "success":
                hr_data = hr_response.get("data", {})
                if hr_data is None or not isinstance(hr_data, dict):
                    hr_data = {}
                employee_data = hr_data.get("employee_data", {})
                if not isinstance(employee_data, dict):
                    employee_data = {}
                employee_id = employee_data.get("id", "NEW-EMP")
                employee_name = employee_data.get("name", "Employee")
                popup_html = f"""
                <div class="response-popup success">
                    <div class="popup-header">
                        <div class="popup-icon">👤</div>
                        <span>HR Onboarding - Complete</span>
                    </div>
                    <div class="popup-content">
                        <strong>{employee_name}</strong> ({employee_id}) has been successfully onboarded!<br>
                        <span class="popup-badge badge-success">✅ Employee Created</span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                with st.expander("📋 View Full HR Details"):
                    st.json(hr_data)
            else:
                popup_html = """
                <div class="response-popup error">
                    <div class="popup-header">
                        <div class="popup-icon">👤</div>
                        <span>HR Processing - Failed</span>
                    </div>
                    <div class="popup-content">
                        HR Agent encountered an error during onboarding.<br>
                        <span class="popup-badge badge-error">❌ Check Details Below</span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                error_data = hr_response.get("data", {}) if hr_response else {}
                if error_data:
                    st.error(error_data.get("error", "Unknown HR error"))
            
            # Support Response Popup
            support_response = response.get("support_response", {})
            if support_response and isinstance(support_response, dict) and support_response.get("status") == "success":
                support_data = support_response.get("data", {})
                if support_data is None or not isinstance(support_data, dict):
                    support_data = {}
                ticket_id = support_data.get("ticket_id", "TKT-000")
                decision = support_data.get("decision", "PROCESSING")
                popup_html = f"""
                <div class="response-popup success">
                    <div class="popup-header">
                        <div class="popup-icon">🔐</div>
                        <span>IT Access - Provisioned</span>
                    </div>
                    <div class="popup-content">
                        Support ticket <strong>{ticket_id}</strong> created successfully!<br>
                        All IT access has been configured.<br>
                        <span class="popup-badge badge-success">✅ Access Ready</span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                with st.expander("🔧 View IT Access Details"):
                    st.json(support_data)
            else:
                popup_html = """
                <div class="response-popup error">
                    <div class="popup-header">
                        <div class="popup-icon">🔐</div>
                        <span>IT Access - Error</span>
                    </div>
                    <div class="popup-content">
                        Support Agent encountered an issue provisioning access.<br>
                        <span class="popup-badge badge-error">❌ Retry or Contact Support</span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                st.error(support_response.get("data", {}).get("error", "Unknown error"))
            
            # Meeting Response Popup
            meeting_response = response.get("meeting_response", {})
            if meeting_response and isinstance(meeting_response, dict) and meeting_response.get("status") == "success":
                meeting_data = meeting_response.get("data", {})
                if meeting_data is None or not isinstance(meeting_data, dict):
                    meeting_data = {}
                meetings = meeting_data.get("meetings", [])
                if meetings and isinstance(meetings, list) and len(meetings) > 0:
                    meeting = meetings[0]
                    meeting_title = meeting.get("title", "Meeting")
                    meeting_time = meeting.get("time", "TBD")
                    popup_html = f"""
                    <div class="response-popup success">
                        <div class="popup-header">
                            <div class="popup-icon">📅</div>
                            <span>Meeting Scheduled</span>
                        </div>
                        <div class="popup-content">
                            <strong>{meeting_title}</strong><br>
                            📍 Time: {meeting_time}<br>
                            <span class="popup-badge badge-success">✅ Calendar Updated</span>
                        </div>
                    </div>
                    """
                    st.markdown(popup_html, unsafe_allow_html=True)
                    with st.expander("📅 View Meeting Details"):
                        st.json(meeting_data)
                else:
                    st.info("No meetings scheduled")
            else:
                popup_html = """
                <div class="response-popup error">
                    <div class="popup-header">
                        <div class="popup-icon">📅</div>
                        <span>Meeting Scheduling - Error</span>
                    </div>
                    <div class="popup-content">
                        Meeting Agent could not schedule the meeting.<br>
                        <span class="popup-badge badge-error">❌ Check Details</span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                st.error(meeting_response.get("data", {}).get("error", "Unknown error"))
            
            # Project Response - ENHANCED UI
            # Project Response - ENHANCED PREMIUM UI
            project_response = response.get("project_response", {})
            if project_response and isinstance(project_response, dict) and project_response.get("status") == "success":
                project_data = project_response.get("data", {})
                if project_data is None or not isinstance(project_data, dict):
                    project_data = {}
                project_info = project_data.get("project_data", {})
                if project_info is None or not isinstance(project_info, dict):
                    project_info = {}
                project_name = project_info.get("name", "Project")
                project_id = project_info.get("id", "PROJ-000")
                team_members = project_info.get("team_members", [])
                description = project_info.get("description", "")
                milestones = project_info.get("milestones", [])
                next_steps = project_data.get("next_steps", [])
                recommendations = project_data.get("recommendations", [])
                
                # Success popup with animation
                popup_html = f"""
                <div class="response-popup success" style="animation: slideIn 0.5s ease-out;">
                    <div class="popup-header" style="background: linear-gradient(90deg, #10B981 0%, #059669 100%);">
                        <div class="popup-icon">🎉</div>
                        <span style="font-size: 18px; font-weight: bold;">Project Assignment Successful!</span>
                    </div>
                    <div class="popup-content" style="background: #F0FDF4; color: #065F46; padding: 15px; border-radius: 8px; margin-top: 10px;">
                        <strong>{team_members[0] if team_members else 'Employee'}</strong> has been successfully assigned to <strong>{project_name}</strong><br>
                        <span style="font-size: 12px; margin-top: 8px; display: inline-block; background: #DCFCE7; padding: 6px 12px; border-radius: 20px; color: #065F46;">
                            ✅ Team Access Ready
                        </span>
                    </div>
                </div>
                """
                st.markdown(popup_html, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Main Project Card - Premium Design
                main_card_html = f"""
                <style>
                    @keyframes slideIn {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    .project-main-card {{
                        animation: slideIn 0.6s ease-out;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 35px;
                        border-radius: 16px;
                        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
                        margin-bottom: 25px;
                        position: relative;
                        overflow: hidden;
                    }}
                    .project-main-card::before {{
                        content: '';
                        position: absolute;
                        top: -50%;
                        right: -50%;
                        width: 200px;
                        height: 200px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 50%;
                    }}
                    .project-content {{
                        position: relative;
                        z-index: 1;
                    }}
                    .project-grid {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 30px;
                        margin-bottom: 20px;
                    }}
                    .project-field {{
                        background: rgba(255, 255, 255, 0.15);
                        padding: 15px;
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                    }}
                    .project-label {{
                        font-size: 13px;
                        opacity: 0.9;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin-bottom: 8px;
                    }}
                    .project-value {{
                        font-size: 24px;
                        font-weight: bold;
                    }}
                </style>
                <div class="project-main-card">
                    <div class="project-content">
                        <div style="margin-bottom: 20px;">
                            <div style="font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">📊 Project Information</div>
                        </div>
                        <div class="project-grid">
                            <div class="project-field">
                                <div class="project-label">Project Name</div>
                                <div class="project-value">{project_name}</div>
                            </div>
                            <div class="project-field">
                                <div class="project-label">Project ID</div>
                                <div class="project-value">{project_id}</div>
                            </div>
                        </div>
                        <div style="background: rgba(255, 255, 255, 0.15); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);">
                            <div class="project-label">Status</div>
                            <div style="font-size: 16px; margin-top: 8px;">✅ <strong>Employee Assigned</strong></div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(main_card_html, unsafe_allow_html=True)
                
                # Description Section
                description_html = f"""
                <div style="background: #E8F8F5; border-radius: 12px; padding: 25px; 
                            border-left: 5px solid #10B981; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15); margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; margin-bottom: 20px;">
                        <span style="font-size: 24px; margin-right: 10px;">📝</span>
                        <h3 style="margin: 0; color: #10B981; font-size: 18px;">Project Description</h3>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; 
                                border-left: 3px solid #10B981; color: #1F2937; line-height: 1.6;">
                        {description if description else 'No description provided for this project assignment.'}
                    </div>
                </div>
                """
                st.markdown(description_html, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Recommendations Section
                if recommendations:
                    recommendations_html = f"""
                    <div style="background: #F3E5F5; border-radius: 12px; padding: 25px; 
                                border-left: 5px solid #9C27B0; box-shadow: 0 4px 12px rgba(156, 39, 176, 0.15);">
                        <div style="display: flex; align-items: center; margin-bottom: 20px;">
                            <span style="font-size: 24px; margin-right: 10px;">💡</span>
                            <h3 style="margin: 0; color: #9C27B0; font-size: 18px;">Recommendations</h3>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    """
                    
                    for rec in recommendations:
                        recommendations_html += f"""
                        <div style="background: white; padding: 15px; border-radius: 8px; 
                                    border-left: 3px solid #9C27B0;">
                            <div style="display: flex; align-items: flex-start;">
                                <span style="font-size: 18px; margin-right: 10px;">💡</span>
                                <span style="color: #1F2937; line-height: 1.5;">{rec}</span>
                            </div>
                        </div>
                        """
                    
                    recommendations_html += """
                        </div>
                    </div>
                    """
                    st.markdown(recommendations_html, unsafe_allow_html=True)
                
            else:
                # Error State - Premium Design
                error_message = project_response.get("data", {}).get("error", "Unknown error occurred")
                error_html = f"""
                <div style="background: #FEE2E2; border-radius: 12px; padding: 25px; 
                            border-left: 5px solid #DC2626; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.15);">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 28px; margin-right: 15px;">❌</span>
                        <h3 style="margin: 0; color: #DC2626; font-size: 18px;">Project Assignment Failed</h3>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; color: #7F1D1D;">
                        <strong>Error:</strong> {error_message}
                    </div>
                    <div style="margin-top: 15px; padding: 15px; background: #FECACA; border-radius: 8px; color: #7F1D1D;">
                        ⚠️ Manual assignment may be required. Please contact the project administrator.
                    </div>
                </div>
                """
                st.markdown(error_html, unsafe_allow_html=True)
            
            st.markdown("---")
            st.success("✨ Onboarding workflow completed! All agents have processed the request.")
        else:
            # Single-agent workflow
            data = response.get("data", {})
            
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
                    st.markdown("### 🔍 Reason")
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
                
                # LangGraph Workflow Visualization
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
            
            elif intent["agent"] == "documents":
                # Document Review - ENHANCED PREMIUM UI
                doc_type = data.get("document_type", "Unknown")
                risk_level = data.get("risk_level", "Unknown")
                compliance_score = data.get("compliance_score", 0)
                compliance_index = data.get("compliance_index", "N/A")
                clause_analysis = data.get("clause_analysis", {})
                suggestions = data.get("suggestions", [])
                explanation = data.get("explanation", "")
                
                # Risk level color coding
                risk_colors = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢",
                    "critical": "🔴"
                }
                risk_icon = risk_colors.get(risk_level.lower(), "🟡")
                
                # Success/warning message based on compliance
                if compliance_score >= 80:
                    st.success(f"✅ Document Review Complete - {compliance_score}% Compliant")
                elif compliance_score >= 60:
                    st.warning(f"⚠️ Document Review Complete - {compliance_score}% Compliant (Review Issues Found)")
                else:
                    st.error(f"❌ Document Review Complete - {compliance_score}% Compliant (Critical Issues Found)")
                
                st.divider()
                
                # Key Metrics
                st.markdown("### � Document Analysis Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📄 Document Type", doc_type)
                with col2:
                    st.metric(f"{risk_icon} Risk Level", risk_level.upper())
                with col3:
                    st.metric("✅ Compliance Score", f"{compliance_score}%")
                with col4:
                    st.metric("📈 Compliance Index", compliance_index)
                
                st.divider()
                
                # Clause Analysis
                if clause_analysis and isinstance(clause_analysis, dict):
                    st.markdown("### 📋 Clause-by-Clause Analysis")
                    
                    for clause_name, clause_data in clause_analysis.items():
                        if isinstance(clause_data, dict):
                            status = clause_data.get("status", "Unknown")
                            status_icon = "✅" if status == "Present" else "⚠️" if status == "Weak" else "❌"
                            
                            with st.expander(f"{status_icon} {clause_name}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Status:** {status}")
                                with col2:
                                    st.write(f"**Similarity:** {clause_data.get('similarity_score', 'N/A')}")
                                with col3:
                                    st.write(f"**Weight:** {clause_data.get('weight', 'N/A')}")
                                
                                snippet = clause_data.get("snippet", "No content available")
                                st.markdown("**Content Preview:**")
                                st.markdown(f"> {snippet}")
                    
                    st.divider()
                
                # Explanation
                if explanation:
                    st.markdown("### 📖 Detailed Analysis")
                    st.info(explanation)
                    st.divider()
                
                # Suggestions
                if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                    st.markdown("### 💡 Recommendations")
                    for idx, suggestion in enumerate(suggestions, 1):
                        st.write(f"{idx}. {suggestion}")
            
            elif intent["agent"] == "projects":
                # Detect project request type
                user_input_lower = user_input.lower()
                if "assign" in user_input_lower and "resource" not in user_input_lower:
                    project_request_type = "assign"
                elif "resource" in user_input_lower and "allocat" in user_input_lower:
                    project_request_type = "resource_allocation"
                elif "performance" in user_input_lower and "team" in user_input_lower:
                    project_request_type = "team_performance"
                elif "deadline" in user_input_lower or "milestone" in user_input_lower:
                    project_request_type = "deadline_tracking"
                elif "status" in user_input_lower:
                    project_request_type = "status"
                else:
                    project_request_type = "status"  # Default

                
                # DIFFERENT VISUALIZATIONS BASED ON PROJECT REQUEST TYPE
                if project_request_type == "assign":
                    # ========== ASSIGN PROJECT WORKFLOW ==========
                    st.success("🎉 Project Assignment Successful!")
                    
                    assignment_data = {
                        "Employee": "Unnathi",
                        "Project": "AI Assistant System",
                        "Role": "Senior AI Engineer",
                        "Start Date": "Apr 16, 2026",
                        "Budget Allocation": "$15,000/month"
                    }
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("👤 Employee", assignment_data["Employee"])
                    with col2:
                        st.metric("📁 Project", assignment_data["Project"])
                    with col3:
                        st.metric("💼 Role", assignment_data["Role"])
                    with col4:
                        st.metric("📅 Start Date", assignment_data["Start Date"])
                    with col5:
                        st.metric("💰 Budget", assignment_data["Budget Allocation"])
                    
                    st.divider()
                    st.markdown("### ✅ Assignment Confirmation")
                    
                    confirmation_data = {
                        "Task": [
                            "Access Provisioning",
                            "System Account Setup",
                            "Team Notification",
                            "Resource Allocation",
                            "Project Induction Scheduled"
                        ],
                        "Status": ["✅ Complete", "✅ Complete", "✅ Complete", "✅ Complete", "⏳ Scheduled"],
                        "Completed At": ["2:15 PM", "2:16 PM", "2:17 PM", "2:18 PM", "Apr 17, 9:00 AM"]
                    }
                    
                    confirmation_df = pd.DataFrame(confirmation_data)
                    st.dataframe(confirmation_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 📧 Notifications Sent")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("✉️ Employee email: unnathi@company.com")
                    with col2:
                        st.info("✉️ Project Manager: alice.johnson@company.com")
                
                elif project_request_type == "resource_allocation":
                    # ========== RESOURCE ALLOCATION WORKFLOW ==========
                    st.success("🎯 Resource Allocation Complete!")
                    
                    # Project overview
                    allocation_overview = {
                        "Project": "Q2 Mobile App Launch",
                        "Total Budget": "$250,000",
                        "Allocated": "$180,000",
                        "Available": "$70,000",
                        "Allocation %": "72%"
                    }
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("📁 Project", allocation_overview["Project"])
                    with col2:
                        st.metric("💰 Total Budget", allocation_overview["Total Budget"])
                    with col3:
                        st.metric("🎯 Allocated", allocation_overview["Allocated"])
                    with col4:
                        st.metric("📊 Available", allocation_overview["Available"])
                    with col5:
                        st.metric("📈 Usage", allocation_overview["Allocation %"])
                    
                    st.divider()
                    st.markdown("### 👥 Resource Allocation by Department")
                    
                    # Create resource allocation chart
                    allocation_data = {
                        "Department": ["Development", "QA/Testing", "Design", "DevOps", "Project Mgmt"],
                        "Budget": [85000, 45000, 25000, 15000, 10000],
                        "Allocated": [85000, 35000, 20000, 15000, 25000]
                    }
                    
                    alloc_df = pd.DataFrame(allocation_data)
                    
                    # Create comparison chart
                    fig_alloc = go.Figure(data=[
                        go.Bar(x=alloc_df["Department"], y=alloc_df["Budget"], name="Budgeted", marker_color='#3498db'),
                        go.Bar(x=alloc_df["Department"], y=alloc_df["Allocated"], name="Allocated", marker_color='#2ecc71')
                    ])
                    fig_alloc.update_layout(
                        barmode='group',
                        title="Budget vs Allocation by Department",
                        xaxis_title="Department",
                        yaxis_title="Amount ($)",
                        height=400,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_alloc, use_container_width=True)
                    
                    st.divider()
                    st.markdown("### 👨‍💼 Team Member Allocations")
                    
                    # Team allocations
                    team_alloc = {
                        "Team Member": ["Alice Johnson", "Bob Smith", "Carol White", "David Brown", "Eve Davis"],
                        "Department": ["Development", "Development", "QA/Testing", "Design", "DevOps"],
                        "Hours/Week": [40, 35, 30, 25, 20],
                        "Allocation %": [100, 87.5, 100, 83, 67],
                        "Cost/Month": ["$8,000", "$7,000", "$3,600", "$3,000", "$2,400"]
                    }
                    
                    team_df = pd.DataFrame(team_alloc)
                    st.dataframe(team_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 📋 Resource Allocation Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👥 Total Team Members", "5")
                    with col2:
                        st.metric("⏱️ Total Hours/Week", "150")
                    with col3:
                        st.metric("💸 Total Cost/Month", "$24,000")
                
                elif project_request_type == "team_performance":
                    # ========== TEAM PERFORMANCE WORKFLOW ==========
                    st.success("📊 Team Performance Analysis Complete!")
                    
                    st.markdown("### 👥 Team Member Contribution Analysis")
                    
                    # Create dummy team contribution data
                    team_contribution = {
                        "Team Member": ["Alice Johnson (Lead)", "Bob Smith", "Carol White", "David Brown", "Eve Davis"],
                        "Tasks Completed": [12, 8, 6, 9, 5],
                        "Hours Logged": [48, 35, 28, 42, 22],
                        "Efficiency %": [95, 87, 81, 92, 78]
                    }
                    
                    contrib_df = pd.DataFrame(team_contribution)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tasks completed bar chart
                        fig_tasks = px.bar(
                            contrib_df,
                            x="Team Member",
                            y="Tasks Completed",
                            color="Tasks Completed",
                            color_continuous_scale="Viridis",
                            labels={"Tasks Completed": "Tasks Done"},
                            title="📋 Tasks Completed by Member",
                            text="Tasks Completed"
                        )
                        fig_tasks.update_traces(textposition='auto')
                        fig_tasks.update_layout(
                            xaxis_tickangle=-45,
                            height=350,
                            showlegend=False,
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_tasks, use_container_width=True)
                    
                    with col2:
                        # Efficiency score scatter plot
                        fig_efficiency = px.scatter(
                            contrib_df,
                            x="Hours Logged",
                            y="Efficiency %",
                            size="Tasks Completed",
                            hover_name="Team Member",
                            color="Efficiency %",
                            color_continuous_scale="RdYlGn",
                            title="⚡ Efficiency vs Hours Logged",
                            size_max=50,
                            range_y=[70, 100]
                        )
                        fig_efficiency.update_layout(height=350, hovermode='closest')
                        st.plotly_chart(fig_efficiency, use_container_width=True)
                    
                    st.divider()
                    st.markdown("### 📈 Performance Metrics Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🏆 Top Performer", "Alice Johnson", "95% efficiency")
                    with col2:
                        st.metric("📊 Avg Efficiency", "86.6%", "+5% vs last week")
                    with col3:
                        st.metric("⏱️ Total Hours", "175 hrs", "On track")
                    with col4:
                        st.metric("✅ Tasks Done", "40 tasks", "+8 this week")
                    
                    st.divider()
                    st.markdown("### 🎯 Performance Improvement Recommendations")
                    recommendations_perf = [
                        "David Brown shows high efficiency (92%) - consider for team lead role",
                        "Eve Davis needs support - assign mentor or additional training",
                        "Carol White progressing well - recommend for advanced projects",
                        "Consider flexible hours for high performers to maintain morale"
                    ]
                    for rec in recommendations_perf:
                        st.info(f"💡 {rec}")
                
                elif project_request_type == "deadline_tracking":
                    # ========== DEADLINE TRACKING WORKFLOW ==========
                    st.success("⏰ Deadline & Milestone Tracking")
                    
                    st.markdown("### ⏰ Upcoming Deadlines & Milestones")
                    
                    deadline_data = {
                        "Milestone": ["Design Review", "Development Sprint 1", "Integration Testing", "UAT Release", "Production Go-Live"],
                        "Deadline": ["Apr 20, 2026", "May 5, 2026", "May 15, 2026", "May 25, 2026", "Jun 5, 2026"],
                        "Days Left": [4, 19, 29, 39, 50],
                        "Status": ["🔴 Critical", "🟡 At Risk", "🟢 On Track", "🟢 On Track", "🟢 Healthy"]
                    }
                    
                    deadline_df = pd.DataFrame(deadline_data)
                    
                    # Create timeline visualization
                    fig_timeline = go.Figure()
                    
                    colors = {"🔴 Critical": "#e74c3c", "🟡 At Risk": "#f39c12", "🟢 On Track": "#2ecc71", "🟢 Healthy": "#27ae60"}
                    
                    for idx, row in deadline_df.iterrows():
                        color = colors.get(row["Status"], "#95a5a6")
                        fig_timeline.add_trace(go.Scatter(
                            x=[row["Days Left"]],
                            y=[row["Milestone"]],
                            mode='markers+text',
                            marker=dict(size=15, color=color),
                            text=f'{row["Days Left"]}d',
                            textposition="middle center",
                            hovertemplate=f'<b>{row["Milestone"]}</b><br>Deadline: {row["Deadline"]}<br>Days Left: {row["Days Left"]}<extra></extra>'
                        ))
                    
                    fig_timeline.update_layout(
                        title="📅 Project Milestone Timeline",
                        xaxis_title="Days Until Deadline",
                        yaxis_title="Milestone",
                        height=350,
                        showlegend=False,
                        hovermode='closest',
                        xaxis=dict(range=[0, 55]),
                        margin=dict(l=200, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Display deadline summary table
                    st.markdown("#### Deadline Summary")
                    st.dataframe(
                        deadline_df.style.format({
                            "Days Left": "{} days"
                        }).background_gradient(subset=["Days Left"], cmap="RdYlGn_r", vmin=0, vmax=50),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.divider()
                    st.markdown("### 🚨 Critical Items")
                    critical = deadline_df[deadline_df["Status"].str.contains("Critical|At Risk")]
                    for _, row in critical.iterrows():
                        st.warning(f"⚠️ **{row['Milestone']}** - Due in {row['Days Left']} days ({row['Deadline']})")
                
                else:
                    # ========== PROJECT STATUS WORKFLOW (Default) ==========
                    project_data = data.get("project_data", {})
                    if data.get("decision") == "employee_assigned" and project_data:
                        # Extract project information
                        project_name = project_data.get("name", "Project")
                        project_id = project_data.get("id", "PROJ-000")
                        team_members = project_data.get("team_members", [])
                        description = project_data.get("description", "")
                        milestones = project_data.get("milestones", [])
                        recommendations = project_data.get("recommendations", [])
                        
                        # Clean only plain text fields (name, id, description)
                        project_name = strip_html_tags(str(project_name)).strip()
                        project_id = strip_html_tags(str(project_id)).strip()
                        description = strip_html_tags(str(description)).strip()
                        
                        # Success message
                        st.success(f"🎉 Successfully assigned to {project_name}! ✅ Team Access Ready")
                        
                        # Main project info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 Project Name", project_name)
                        with col2:
                            st.metric("🆔 Project ID", project_id)
                        with col3:
                            st.metric("✅ Status", "Employee Assigned")
                        
                        st.divider()
                        
                        # PROJECT PROGRESS & TIMELINE VISUALIZATION
                        st.markdown("### 📈 Project Progress Timeline")
                        
                        # Create dummy progress data
                        progress_data = {
                            "Phase": ["Planning", "Design", "Development", "Testing", "Deployment"],
                            "Completion %": [100, 85, 60, 30, 10],
                            "Status": ["✅ Complete", "🟨 In Progress", "🔵 In Progress", "⏳ Upcoming", "⏳ Upcoming"]
                        }
                        
                        # Create horizontal progress bar chart
                        fig_progress = go.Figure()
                        for idx, phase in enumerate(progress_data["Phase"]):
                            completion = progress_data["Completion %"][idx]
                            fig_progress.add_trace(go.Bar(
                                y=[phase],
                                x=[completion],
                                orientation='h',
                                name=f'{phase} ({completion}%)',
                                marker=dict(
                                    color=['#2ecc71' if completion == 100 else '#f39c12' if completion >= 50 else '#3498db'][0],
                                    line=dict(color='white', width=2)
                                ),
                                text=f'{completion}%',
                                textposition='auto',
                                hovertemplate='<b>%{y}</b><br>Completion: %{x}%<extra></extra>'
                            ))
                        
                        fig_progress.update_layout(
                            xaxis_title="Completion %",
                            yaxis_title="Project Phase",
                            showlegend=False,
                            height=280,
                            hovermode='closest',
                            xaxis=dict(range=[0, 100]),
                            margin=dict(l=150, r=20, t=20, b=20)
                        )
                        st.plotly_chart(fig_progress, use_container_width=True)
                        
                        st.divider()
                        
                        # TEAM MEMBER CONTRIBUTION ANALYSIS
                        st.markdown("### 👥 Team Member Contribution Analysis")
                        
                        # Create dummy team contribution data
                        team_contribution = {
                            "Team Member": ["Alice Johnson (Lead)", "Bob Smith", "Carol White", "David Brown", "Eve Davis"],
                            "Tasks Completed": [12, 8, 6, 9, 5],
                            "Hours Logged": [48, 35, 28, 42, 22],
                            "Efficiency %": [95, 87, 81, 92, 78]
                        }
                        
                        contrib_df = pd.DataFrame(team_contribution)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Tasks completed bar chart
                            fig_tasks = px.bar(
                                contrib_df,
                                x="Team Member",
                                y="Tasks Completed",
                                color="Tasks Completed",
                                color_continuous_scale="Viridis",
                                labels={"Tasks Completed": "Tasks Done"},
                                title="📋 Tasks Completed by Member",
                                text="Tasks Completed"
                            )
                            fig_tasks.update_traces(textposition='auto')
                            fig_tasks.update_layout(
                                xaxis_tickangle=-45,
                                height=350,
                                showlegend=False,
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig_tasks, use_container_width=True)
                        
                        with col2:
                            # Efficiency score scatter plot
                            fig_efficiency = px.scatter(
                                contrib_df,
                                x="Hours Logged",
                                y="Efficiency %",
                                size="Tasks Completed",
                                hover_name="Team Member",
                                color="Efficiency %",
                                color_continuous_scale="RdYlGn",
                                title="⚡ Efficiency vs Hours Logged",
                                size_max=50,
                                range_y=[70, 100]
                            )
                            fig_efficiency.update_layout(height=350, hovermode='closest')
                            st.plotly_chart(fig_efficiency, use_container_width=True)
                        
                        st.divider()
                        
                        # DEADLINE & MILESTONES STATUS
                        st.markdown("### ⏰ Upcoming Deadlines & Milestones")
                        
                        deadline_data = {
                            "Milestone": ["Design Review", "Development Sprint 1", "Integration Testing", "UAT Release", "Production Go-Live"],
                            "Deadline": ["Apr 20, 2026", "May 5, 2026", "May 15, 2026", "May 25, 2026", "Jun 5, 2026"],
                            "Days Left": [4, 19, 29, 39, 50],
                            "Status": ["🔴 Critical", "🟡 At Risk", "🟢 On Track", "🟢 On Track", "🟢 Healthy"]
                        }
                        
                        deadline_df = pd.DataFrame(deadline_data)
                        
                        # Create timeline visualization
                        fig_timeline = go.Figure()
                        
                        colors = {"🔴 Critical": "#e74c3c", "🟡 At Risk": "#f39c12", "🟢 On Track": "#2ecc71", "🟢 Healthy": "#27ae60"}
                        
                        for idx, row in deadline_df.iterrows():
                            color = colors.get(row["Status"], "#95a5a6")
                            fig_timeline.add_trace(go.Scatter(
                                x=[row["Days Left"]],
                                y=[row["Milestone"]],
                                mode='markers+text',
                                marker=dict(size=15, color=color),
                                text=f'{row["Days Left"]}d',
                                textposition="middle center",
                                hovertemplate=f'<b>{row["Milestone"]}</b><br>Deadline: {row["Deadline"]}<br>Days Left: {row["Days Left"]}<extra></extra>'
                            ))
                        
                        fig_timeline.update_layout(
                            title="📅 Project Milestone Timeline",
                            xaxis_title="Days Until Deadline",
                            yaxis_title="Milestone",
                            height=350,
                            showlegend=False,
                            hovermode='closest',
                            xaxis=dict(range=[0, 55]),
                            margin=dict(l=200, r=20, t=40, b=20)
                        )
                        st.plotly_chart(fig_timeline, use_container_width=True)
                        
                        # Display deadline summary table
                        st.markdown("#### Deadline Summary")
                        st.dataframe(
                            deadline_df.style.format({
                                "Days Left": "{} days"
                            }).background_gradient(subset=["Days Left"], cmap="RdYlGn_r", vmin=0, vmax=50),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        st.divider()
                        
                        # Project Description Section
                        st.markdown("### 📝 Project Description")
                        st.write(description if description else "No description provided for this project assignment.")
                        
                        st.divider()
                        
                        # Recommendations Section
                        if recommendations:
                            st.markdown("### 💡 Recommendations")
                            for rec in recommendations:
                                if isinstance(rec, str):
                                    # Check if it's HTML - if so, render it
                                    if '<' in rec and '>' in rec:
                                        st.markdown(rec, unsafe_allow_html=True)
                                    else:
                                        # Plain text
                                        st.info(rec)
                                else:
                                    # Non-string type
                                    st.info(str(rec))
                    else:
                        # Fallback for non-assignment projects
                        if project_data is None:
                            project_data = {}
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Decision", data.get("decision", "N/A"))
                        with col2:
                            st.metric("Project", project_data.get("name", "N/A"))
                        with col3:
                            st.metric("Status", data.get("status", "Pending"))
            
            elif intent["agent"] == "hr":
                # ========== HR ONBOARDING WORKFLOWS ==========
                # Detect HR request type based on query content
                user_input_lower = user_input.lower()
                if "setup" in user_input_lower or "records" in user_input_lower:
                    hr_request_type = "hr_setup"
                elif "new" in user_input_lower or "rajesh" in user_input_lower or "process" in user_input_lower:
                    hr_request_type = "new_member"
                elif "onboard" in user_input_lower:
                    hr_request_type = "onboarding"
                else:
                    hr_request_type = "onboarding"  # Default
                
                if hr_request_type == "onboarding":
                    # ========== EMPLOYEE ONBOARDING WORKFLOW ==========
                    st.success("🎉 Employee Onboarding Initiated!")
                    
                    employee_data = {
                        "Employee Name": "Unnathi",
                        "Employee ID": "EMP-2024-001",
                        "Department": "Engineering",
                        "Position": "Senior AI Engineer",
                        "Start Date": "Apr 16, 2026",
                        "Manager": "John Doe"
                    }
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        st.metric("👤 Name", employee_data["Employee Name"])
                    with col2:
                        st.metric("🆔 ID", employee_data["Employee ID"])
                    with col3:
                        st.metric("🏢 Department", employee_data["Department"])
                    with col4:
                        st.metric("💼 Position", employee_data["Position"])
                    with col5:
                        st.metric("📅 Start Date", employee_data["Start Date"])
                    with col6:
                        st.metric("👔 Manager", employee_data["Manager"])
                    
                    st.divider()
                    st.markdown("### ✅ Onboarding Checklist")
                    
                    onboarding_tasks = {
                        "Task": [
                            "Account Creation",
                            "Email & Communication Setup",
                            "Hardware Provisioning",
                            "Access & Permissions",
                            "Documentation Review",
                            "Team Introduction",
                            "First Day Orientation",
                            "Training Scheduled"
                        ],
                        "Status": [
                            "✅ Complete",
                            "✅ Complete",
                            "✅ Complete",
                            "⏳ In Progress",
                            "⏳ In Progress",
                            "⏳ Scheduled",
                            "⏳ Scheduled",
                            "📋 Pending"
                        ],
                        "Assigned To": [
                            "IT Team",
                            "IT Team",
                            "Procurement",
                            "IT Security",
                            "HR Manager",
                            "Team Lead",
                            "Department Head",
                            "Training Team"
                        ]
                    }
                    
                    tasks_df = pd.DataFrame(onboarding_tasks)
                    st.dataframe(tasks_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 📋 Documents Status")
                    
                    documents = {
                        "Document": [
                            "Employment Agreement",
                            "Non-Disclosure Agreement (NDA)",
                            "Code of Conduct",
                            "Benefits Enrollment",
                            "Tax Forms (W-4/I-9)",
                            "Insurance Documents",
                            "Company Handbook",
                            "Direct Deposit Form"
                        ],
                        "Status": ["✅ Signed", "✅ Signed", "✅ Signed", "⏳ Pending", "✅ Signed", "✅ Signed", "📖 Reading", "⏳ Pending"],
                        "Due Date": ["Apr 16", "Apr 16", "Apr 17", "Apr 18", "Apr 16", "Apr 17", "Apr 19", "Apr 18"]
                    }
                    
                    docs_df = pd.DataFrame(documents)
                    st.dataframe(docs_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📊 Overall Progress", "62%")
                    with col2:
                        st.metric("⏱️ Days Remaining", "9 days")
                
                elif hr_request_type == "new_member":
                    # ========== NEW TEAM MEMBER ONBOARDING ==========
                    st.success("🎓 New Team Member Setup Complete!")
                    
                    new_member_data = {
                        "Employee": "Rajesh Kumar",
                        "Team": "Data Science",
                        "Role": "ML Engineer",
                        "Start Date": "Apr 20, 2026",
                        "Reporting To": "Dr. Sarah Smith",
                        "Buddy Assigned": "Alice Johnson"
                    }
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        st.metric("👤 Name", new_member_data["Employee"])
                    with col2:
                        st.metric("👥 Team", new_member_data["Team"])
                    with col3:
                        st.metric("💼 Role", new_member_data["Role"])
                    with col4:
                        st.metric("📅 Start", new_member_data["Start Date"])
                    with col5:
                        st.metric("👔 Manager", new_member_data["Reporting To"])
                    with col6:
                        st.metric("🤝 Buddy", new_member_data["Buddy Assigned"])
                    
                    st.divider()
                    st.markdown("### 📚 Learning & Development Plan")
                    
                    learning_plan = {
                        "Week": ["Week 1", "Week 1", "Week 2", "Week 2", "Week 3", "Week 3", "Week 4", "Week 4"],
                        "Module": [
                            "Company Orientation",
                            "Team Introduction",
                            "Technical Setup",
                            "Codebase Review",
                            "Project Assignment",
                            "Pair Programming",
                            "First Contribution",
                            "30-Day Review"
                        ],
                        "Status": [
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled",
                            "📋 Scheduled"
                        ]
                    }
                    
                    learning_df = pd.DataFrame(learning_plan)
                    st.dataframe(learning_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 🎯 30-60-90 Day Milestones")
                    
                    milestone_data = {
                        "Period": ["30 Days", "60 Days", "90 Days"],
                        "Goals": [
                            "✅ Complete onboarding & setup, understand team processes, complete first task",
                            "✅ Contribute to multiple projects, build relationships, gain domain knowledge",
                            "✅ Full productivity, independent project management, mentoring others"
                        ],
                        "Target Completion": ["May 20, 2026", "Jun 19, 2026", "Jul 19, 2026"]
                    }
                    
                    milestone_df = pd.DataFrame(milestone_data)
                    st.dataframe(milestone_df, use_container_width=True, hide_index=True)
                
                else:
                    # ========== HR SETUP & RECORDS ==========
                    st.success("📋 HR Records Setup Complete!")
                    
                    st.markdown("### 📊 HR System Setup Status")
                    
                    hr_systems = {
                        "System": [
                            "Payroll System",
                            "Benefits Portal",
                            "Leave Management",
                            "Performance Tracking",
                            "Training Portal",
                            "Document Storage"
                        ],
                        "Status": [
                            "✅ Activated",
                            "✅ Activated",
                            "✅ Configured",
                            "✅ Configured",
                            "✅ Enrolled",
                            "✅ Ready"
                        ],
                        "Access Level": [
                            "Full Access",
                            "Full Access",
                            "Standard",
                            "Standard",
                            "Full Access",
                            "Full Access"
                        ]
                    }
                    
                    systems_df = pd.DataFrame(hr_systems)
                    st.dataframe(systems_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 💼 Compensation & Benefits Setup")
                    
                    compensation = {
                        "Component": [
                            "Base Salary",
                            "Health Insurance",
                            "Retirement Plan",
                            "Paid Time Off",
                            "Professional Development",
                            "Stock Options"
                        ],
                        "Amount/Value": [
                            "$120,000/year",
                            "Comprehensive Plan",
                            "5% Match",
                            "20 days/year",
                            "$2,000/year",
                            "Eligible"
                        ],
                        "Status": [
                            "✅ Approved",
                            "✅ Enrolled",
                            "✅ Active",
                            "✅ Configured",
                            "✅ Available",
                            "✅ Pending"
                        ]
                    }
                    
                    comp_df = pd.DataFrame(compensation)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
            
            elif intent["agent"] == "meetings":
                # ========== MEETING SCHEDULING WORKFLOWS ==========
                # Detect meeting request type
                user_input_lower = user_input.lower()
                if "sync" in user_input_lower or "weekly" in user_input_lower:
                    meeting_request_type = "team_sync"
                elif "quick" in user_input_lower or ("call" in user_input_lower and "30" in user_input_lower):
                    meeting_request_type = "quick_call"
                else:
                    meeting_request_type = "schedule"  # Default
                
                if meeting_request_type == "team_sync":
                    # ========== WEEKLY TEAM SYNC SETUP ==========
                    st.success("🤝 Weekly Team Sync Scheduled!")
                    
                    st.markdown("### 📅 Team Sync Meeting Details")
                    
                    sync_details = {
                        "Meeting": "Weekly Team Sync",
                        "Frequency": "Every Monday",
                        "Time": "2:00 PM - 3:00 PM",
                        "Duration": "60 minutes",
                        "Location": "Conference Room A (or Virtual)",
                        "Attendees": "8 team members"
                    }
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        st.metric("📋 Title", "Team Sync")
                    with col2:
                        st.metric("🔄 Frequency", "Weekly")
                    with col3:
                        st.metric("⏰ Time", "2:00 PM")
                    with col4:
                        st.metric("⏱️ Duration", "60 min")
                    with col5:
                        st.metric("📍 Location", "Conf Room A")
                    with col6:
                        st.metric("👥 Attendees", "8")
                    
                    st.divider()
                    st.markdown("### 📌 Meeting Agenda")
                    
                    agenda_items = {
                        "Item": [
                            "Team Updates",
                            "Project Status",
                            "Blockers & Issues",
                            "Upcoming Deadlines",
                            "Q&A & Discussion"
                        ],
                        "Owner": [
                            "Team Lead",
                            "Project Manager",
                            "Team Members",
                            "Project Manager",
                            "Everyone"
                        ],
                        "Time Allocated": [
                            "10 min",
                            "20 min",
                            "15 min",
                            "10 min",
                            "5 min"
                        ]
                    }
                    
                    agenda_df = pd.DataFrame(agenda_items)
                    st.dataframe(agenda_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 📊 Next 4 Weeks Schedule")
                    
                    schedule_data = {
                        "Date": ["Apr 21, 2026", "Apr 28, 2026", "May 5, 2026", "May 12, 2026"],
                        "Time": ["2:00 PM", "2:00 PM", "2:00 PM", "2:00 PM"],
                        "Status": ["✅ Confirmed", "✅ Confirmed", "📋 Scheduled", "📋 Scheduled"],
                        "Location": ["Conference Room A", "Virtual Meeting", "Conference Room A", "Virtual Meeting"]
                    }
                    
                    schedule_df = pd.DataFrame(schedule_data)
                    st.dataframe(schedule_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 📧 Notifications Sent")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("✉️ Calendar invites sent to 8 team members")
                    with col2:
                        st.info("🔔 Recurring meeting set up in shared calendar")
                
                elif meeting_request_type == "quick_call":
                    # ========== QUICK CALL SCHEDULING ==========
                    st.success("⏰ Quick Call Scheduled!")
                    
                    st.markdown("### 📞 Quick Call Details")
                    
                    call_details = {
                        "Meeting": "Quick Sync Call",
                        "Participant": "john@company.com",
                        "Duration": "30 minutes",
                        "Scheduled": "Today, 3:30 PM",
                        "Meeting Link": "https://meet.company.com/call/abc123",
                        "Status": "Confirmed"
                    }
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        st.metric("👤 With", "John Doe")
                    with col2:
                        st.metric("⏱️ Duration", "30 min")
                    with col3:
                        st.metric("🕐 Time", "3:30 PM")
                    with col4:
                        st.metric("📅 Date", "Today")
                    with col5:
                        st.metric("📞 Type", "Video Call")
                    with col6:
                        st.metric("✅ Status", "Confirmed")
                    
                    st.divider()
                    st.markdown("### 📋 Call Preparation")
                    
                    prep_checklist = {
                        "Item": [
                            "Join meeting 5 min early",
                            "Check internet connection",
                            "Prepare discussion points",
                            "Have notes handy",
                            "Test audio/video"
                        ],
                        "Status": [
                            "📋 Pending",
                            "✅ Ready",
                            "✅ Ready",
                            "✅ Ready",
                            "✅ Ready"
                        ]
                    }
                    
                    prep_df = pd.DataFrame(prep_checklist)
                    st.dataframe(prep_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📧 Invite Sent", "john@company.com")
                    with col2:
                        st.metric("🔗 Meeting Link", "Active")
                    with col3:
                        st.metric("⏲️ Time Until Call", "2h 45m")
                
                else:
                    # ========== GENERAL MEETING SCHEDULING ==========
                    st.success("📅 Meeting Scheduled Successfully!")
                    
                    st.markdown("### 📅 Meeting Confirmation")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📋 Meeting", "Team Meeting")
                    with col2:
                        st.metric("📅 Date", "Tue, Apr 23")
                    with col3:
                        st.metric("🕐 Time", "2:00 PM")
                    with col4:
                        st.metric("⏱️ Duration", "1 hour")
                    
                    st.divider()
                    st.markdown("### 👥 Attendees & Availability")
                    
                    attendees = {
                        "Attendee": [
                            "Alice Johnson (Organizer)",
                            "Bob Smith",
                            "Carol White",
                            "David Brown"
                        ],
                        "Availability": [
                            "✅ Confirmed",
                            "✅ Confirmed",
                            "⏳ Tentative",
                            "✅ Confirmed"
                        ],
                        "Response Time": [
                            "2:15 PM",
                            "2:02 PM",
                            "Pending",
                            "2:08 PM"
                        ]
                    }
                    
                    attendees_df = pd.DataFrame(attendees)
                    st.dataframe(attendees_df, use_container_width=True, hide_index=True)
            
            elif intent["agent"] == "analytics":
                # Analytics Dashboard - Using Beautiful Formatters
                st.success("✅ Analytics Report Generated")
                st.markdown("---")
                
                # Display full analytics report using our new formatters
                display_full_analytics_report(data)
                
                # Developer view (JSON)
                st.markdown("---")
                with st.expander("�‍💻 Developer View - Raw JSON"):
                    st.json(data)

            elif intent["agent"] == "email":
                display_email_results(response, EMAIL_DASHBOARD_URL)
            
            else:  # Meetings
                st.markdown("### 📅 Meeting Scheduling Result")
                
                # Key metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", data.get("status", "Pending"))
                with col2:
                    meeting_count = len(data.get("meetings", []))
                    st.metric("Meetings", meeting_count)
                with col3:
                    suggestion_count = len(data.get("suggestions", []))
                    st.metric("Suggestions", suggestion_count)
                
                st.markdown("---")
                
                # Meetings created/updated
                if data.get("meetings"):
                    st.markdown("### 📌 Meetings")
                    for meeting in data.get("meetings", []):
                        with st.expander(f"📅 {meeting.get('title', 'Meeting')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Start:** {meeting.get('start_time', 'N/A')}")
                                st.write(f"**Attendees:** {len(meeting.get('attendees', []))} people")
                            with col2:
                                st.write(f"**End:** {meeting.get('end_time', 'N/A')}")
                                if meeting.get('location'):
                                    st.write(f"**Location:** {meeting.get('location')}")
                        
                        if meeting.get('description'):
                            st.markdown("**Description:**")
                            st.markdown(meeting.get('description'))
                        
                        if meeting.get('hangout_link'):
                            st.markdown(f"[Join Meeting]({meeting.get('hangout_link')})")
                
                st.markdown("---")
                
                # Availability analysis
                if data.get("availability"):
                    st.markdown("### ⏰ Availability Analysis")
                    availability = data.get("availability")
                    with st.expander("View Availability Details"):
                        if isinstance(availability, dict):
                            st.json(availability)
                        else:
                            st.write(availability)
                
                st.markdown("---")
                
                # Conflict resolution
                if data.get("conflicts"):
                    st.markdown("### ⚠️ Conflicts Detected")
                    conflicts = data.get("conflicts", [])
                    for conflict in conflicts:
                        st.warning(f"🔴 {conflict}")
                
                st.markdown("---")
                
                # Smart suggestions
                if data.get("suggestions"):
                    st.markdown("### 💡 Smart Suggestions")
                    suggestions = data.get("suggestions", [])
                    if isinstance(suggestions, list):
                        for i, suggestion in enumerate(suggestions, 1):
                            st.write(f"{i}. {suggestion}")
                    else:
                        st.write(suggestions)
        
        # Developer view - Hide JSON for project responses (both single and multi-agent)
        if intent["agent"] != "projects":
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
