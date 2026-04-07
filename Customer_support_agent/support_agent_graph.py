"""
LangGraph implementation of Support Agent with state visualization.
Replaces the monolithic decide_action() with a multi-step workflow.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any
import logging
from transformers import pipeline
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from policy_store import PolicyStore
from classifier import classify_ticket
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# STATE DEFINITION
# ============================================================================

class SupportAgentState(TypedDict):
    """State object passed through LangGraph workflow"""
    query: str                          # Original user query
    ticket_id: str                      # Ticket identifier
    
    # Step 1: Policy Search Results
    policy_found: Optional[str]
    policy_confidence: float
    
    # Step 2: Sentiment Analysis
    sentiment_label: str                # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score: float
    is_negative: bool
    
    # Step 3: Ticket Classification
    category: str
    suggested_priority: str
    detected_intent: str
    
    # Step 4: Final Decision
    decision: str                       # AUTO_RESOLVE, ESCALATE, HUMAN_REVIEW
    reason: str
    answer: str
    severity: str
    
    # Metadata
    agent_thoughts: str                 # For debugging/logging
    processing_steps: list              # Track which nodes executed

# ============================================================================
# NODE DEFINITIONS
# ============================================================================

def policy_search_node(state: SupportAgentState) -> SupportAgentState:
    """Node 1: Search for matching policies"""
    logger.info(f"[POLICY] Searching policies for: {state['query'][:50]}...")
    
    policy_store = PolicyStore()
    policy, confidence = policy_store.search(state["query"])
    
    state["policy_found"] = policy
    state["policy_confidence"] = confidence
    state["processing_steps"].append("policy_search")
    state["agent_thoughts"] += f"\n✓ Policy search: found={bool(policy)}, conf={confidence:.2f}"
    
    logger.info(f"[POLICY] Result: {policy[:100] if policy else 'None'}...")
    return state


def sentiment_node(state: SupportAgentState) -> SupportAgentState:
    """Node 2: Analyze sentiment of user query"""
    logger.info(f"[SENTIMENT] Analyzing sentiment...")
    
    sentiment_analyzer = pipeline("sentiment-analysis")
    sentiment = sentiment_analyzer(state["query"])[0]
    
    state["sentiment_label"] = sentiment.get("label", "NEUTRAL")
    state["sentiment_score"] = sentiment.get("score", 0.0)
    state["is_negative"] = state["sentiment_label"] == "NEGATIVE"
    state["processing_steps"].append("sentiment_analysis")
    state["agent_thoughts"] += f"\n✓ Sentiment: {state['sentiment_label']} ({state['sentiment_score']:.2f})"
    
    logger.info(f"[SENTIMENT] Result: {state['sentiment_label']}")
    return state


def classification_node(state: SupportAgentState) -> SupportAgentState:
    """Node 3: Classify ticket category and intent"""
    logger.info(f"[CLASSIFY] Classifying ticket...")
    
    # Lightweight classification
    category, suggested_priority = classify_ticket(state["query"])
    state["category"] = category
    state["suggested_priority"] = suggested_priority
    
    # Fine-grained intent detection
    classifier_nli = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )
    LABELS = ["system outage", "vpn issue", "password issue", "software request", "general issue"]
    intent = classifier_nli(state["query"], LABELS)["labels"][0]
    state["detected_intent"] = intent
    
    state["processing_steps"].append("classification")
    state["agent_thoughts"] += f"\n✓ Category: {category}, Intent: {intent}"
    
    logger.info(f"[CLASSIFY] Result: {category}")
    return state


def decision_node(state: SupportAgentState) -> SupportAgentState:
    """Node 4: Make final decision using Groq LLM with context from previous nodes"""
    logger.info(f"[DECISION] Making decision with LLM...")
    
    try:
        # Initialize Groq LLM using model from env or fallback to llama-3.3-70b
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        llm = ChatGroq(
            model=model_name,
            temperature=0.7,
            max_tokens=500,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Build decision prompt with MUCH more context and instruction for LLM to think
        decision_prompt = ChatPromptTemplate.from_template("""
You are an enterprise IT support agent. Analyze this ticket holistically and make an intelligent decision.

**TICKET INFORMATION:**
- User Message: {query}
- Category: {category}
- Intent: {intent}
- User Sentiment: {sentiment} (confidence: {sentiment_score:.2f})
- Relevant IT Policy: {policy_found}
- Policy Match Confidence: {policy_confidence:.2f}

**YOUR TASK:**
Based on ALL the above factors, make an INTELLIGENT decision. Think about:
1. User frustration level (sentiment score)
2. Criticality of issue (category + intent)
3. Whether we have a solution (policy match)
4. Urgency level

**DECISION OPTIONS & GUIDELINES:**
1. AUTO_RESOLVE - Use ONLY if:
   - We have a good policy match (>0.6)
   - AND user is not frustrated
   - AND this is a common issue
   
2. ESCALATE - Use if:
   - User is frustrated/angry
   - OR this is a system outage
   - OR it's a security issue
   - OR we don't have a solution
   
3. HUMAN_REVIEW - Use if:
   - It's unclear or ambiguous
   - OR it needs manager approval
   - OR multiple systems affected

**RESPONSE FORMAT (IMPORTANT - Follow exactly):**
DECISION: [AUTO_RESOLVE or ESCALATE or HUMAN_REVIEW]
REASON: [2-3 sentences explaining your reasoning]
ANSWER: [What you would tell the user - be helpful!]
SEVERITY: [P1 for urgent/outage, P2 for important, P3 for normal, P4 for low]

Now analyze and respond:
        """)
        
        # Create chain
        chain = decision_prompt | llm
        
        # Invoke LLM - THIS IS THE KEY: LLM IS BEING USED HERE
        logger.info(f"[DECISION] Invoking Groq LLM for intelligent decision...")
        response = chain.invoke({
            "query": state["query"],
            "category": state["category"],
            "intent": state["detected_intent"],
            "sentiment": state["sentiment_label"],
            "sentiment_score": state["sentiment_score"],
            "policy_found": state["policy_found"] or "No relevant policy found",
            "policy_confidence": state["policy_confidence"]
        })
        
        # Parse LLM response
        response_text = response.content
        logger.info(f"[DECISION] LLM Response:\n{response_text}")
        
        lines = response_text.strip().split("\n")
        
        for line in lines:
            if line.startswith("DECISION:"):
                state["decision"] = line.replace("DECISION:", "").strip()
            elif line.startswith("REASON:"):
                state["reason"] = line.replace("REASON:", "").strip()
            elif line.startswith("ANSWER:"):
                state["answer"] = line.replace("ANSWER:", "").strip()
            elif line.startswith("SEVERITY:"):
                state["severity"] = line.replace("SEVERITY:", "").strip()
        
        # Verify we got all fields
        if not state["decision"]:
            logger.warning("[DECISION] LLM didn't return DECISION, falling back to rules")
            state = _fallback_decision(state)
        
        state["processing_steps"].append("decision_with_llm")
        state["agent_thoughts"] += f"\n✓ LLM Decision: {state['decision']}\n  Reason: {state['reason']}"
        
        logger.info(f"[DECISION] Result: {state['decision']}")
        
    except Exception as e:
        logger.error(f"[DECISION] LLM Error: {e}. Falling back to rule-based decision.")
        logger.error(f"[DECISION] Error details: {type(e).__name__}: {str(e)}")
        # Fallback to rule-based decision
        state = _fallback_decision(state)
    
    return state


def _fallback_decision(state: SupportAgentState) -> SupportAgentState:
    """Fallback rule-based decision if LLM fails"""
    
    # Rule 1: If policy matches well -> AUTO_RESOLVE
    if state["policy_found"] and state["policy_confidence"] > 0.6:
        state["decision"] = "AUTO_RESOLVE"
        state["reason"] = f"Matched IT policy (confidence {state['policy_confidence']:.2f})"
        state["answer"] = state["policy_found"]
        state["severity"] = state["suggested_priority"]
        return state
    
    # Rule 2: Outage or negative sentiment -> ESCALATE
    if "outage" in state["detected_intent"] or state["is_negative"]:
        state["decision"] = "ESCALATE"
        state["reason"] = "High-priority issue requiring human review"
        state["answer"] = "Your issue has been escalated to senior support team"
        state["severity"] = "P1" if "outage" in state["detected_intent"] else "P2"
        return state
    
    # Rule 3: Default to HUMAN_REVIEW
    state["decision"] = "HUMAN_REVIEW"
    state["reason"] = "Requires expert judgment"
    state["answer"] = "Your ticket has been assigned to a support specialist"
    state["severity"] = state["suggested_priority"]
    
    return state


# ============================================================================
# GRAPH COMPILATION
# ============================================================================

def create_support_agent_graph():
    """Create and compile the LangGraph workflow"""
    
    graph = StateGraph(SupportAgentState)
    
    # Add nodes
    graph.add_node("policy_search", policy_search_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("classify", classification_node)
    graph.add_node("decide", decision_node)
    
    # Add edges (workflow sequence)
    graph.add_edge("policy_search", "sentiment")
    graph.add_edge("sentiment", "classify")
    graph.add_edge("classify", "decide")
    graph.add_edge("decide", END)
    
    # Set entry point
    graph.set_entry_point("policy_search")
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    return compiled_graph


# ============================================================================
# PUBLIC INTERFACE
# ============================================================================

def decide_action_with_graph(query: str, ticket_id: str = "default") -> Dict[str, Any]:
    """
    New interface to replace the old decide_action() function.
    Returns same format but with LangGraph processing.
    """
    
    # Create initial state
    initial_state = SupportAgentState(
        query=query,
        ticket_id=ticket_id,
        policy_found=None,
        policy_confidence=0.0,
        sentiment_label="NEUTRAL",
        sentiment_score=0.0,
        is_negative=False,
        category="",
        suggested_priority="",
        detected_intent="",
        decision="",
        reason="",
        answer="",
        severity="",
        agent_thoughts="LangGraph Processing Flow:\n",
        processing_steps=[]
    )
    
    # Execute graph
    graph = create_support_agent_graph()
    final_state = graph.invoke(initial_state)
    
    # Return in original format (backward compatible)
    return {
        "ticket_id": ticket_id,
        "decision": final_state["decision"],
        "reason": final_state["reason"],
        "answer": final_state["answer"],
        "severity": final_state["severity"],
        "category": final_state["category"],
        "intent": final_state["detected_intent"],
        "sentiment": final_state["sentiment_label"],
        # New: LangGraph metadata
        "processing_steps": final_state["processing_steps"],
        "agent_thoughts": final_state["agent_thoughts"],
        "policy_confidence": final_state["policy_confidence"]
    }


# ============================================================================
# GRAPH VISUALIZATION
# ============================================================================

def get_graph_visualization() -> str:
    """Get ASCII representation of the workflow graph"""
    
    graph_ascii = """
    ╔═════════════════════════════════════════════════════════════════╗
    ║         SUPPORT AGENT - LANGGRAPH WORKFLOW                     ║
    ║         (Multi-step Decision Making with LLM Integration)      ║
    ╚═════════════════════════════════════════════════════════════════╝
    
              ┌─────────────────────────────────┐
              │   START: User Query Received    │
              └──────────────┬──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Policy Search  │ ← Search IT policies
                    │   (Node 1)      │   for matching solutions
                    └────────┬────────┘
                             │
                    ┌────────▼─────────┐
                    │ Sentiment Check  │ ← Analyze user sentiment
                    │  (Node 2)        │   (POSITIVE/NEGATIVE/NEUTRAL)
                    └────────┬─────────┘
                             │
                    ┌────────▼──────────┐
                    │  Classification   │ ← Classify ticket category
                    │   (Node 3)        │   & detect intent
                    └────────┬──────────┘
                             │
                    ┌────────▼────────────────┐
                    │  LLM Decision Making   │ ← Use Groq LLM to decide:
                    │   (Node 4)             │   • AUTO_RESOLVE
                    │   [Groq Mixtral 8x7B]  │   • ESCALATE
                    │                        │   • HUMAN_REVIEW
                    └────────┬───────────────┘
                             │
              ┌──────────────▼──────────────┐
              │  Return Decision & Reason  │
              │  + Severity + Answer        │
              └──────────────┬──────────────┘
                             │
                          ┌──▼──┐
                          │ END │
                          └─────┘
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Key Features:
    ✓ Sequential node execution with state passing
    ✓ Each node adds context for next step
    ✓ LLM-based decision making with fallback rules
    ✓ Observable processing steps tracked
    ✓ Full traceability of agent reasoning
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    return graph_ascii


def get_graph_mermaid() -> str:
    """Get Mermaid diagram code for the workflow"""
    
    mermaid = """graph TD
    A["🔍 Policy Search<br/>(Node 1)"] --> B["😊 Sentiment Analysis<br/>(Node 2)"]
    B --> C["📂 Classification<br/>(Node 3)"]
    C --> D["🤖 LLM Decision<br/>(Node 4)<br/>Groq Mixtral"]
    D --> E["✅ Decision Result<br/>(AUTO_RESOLVE<br/>ESCALATE<br/>HUMAN_REVIEW)"]
    
    style A fill:#e1f5ff
    style B fill:#f3e5f5
    style C fill:#e8f5e9
    style D fill:#fff3e0
    style E fill:#f1f8e9"""
    
    return mermaid
