# MCP Enterprise Orchestrator 🚀

An Enterprise Multi-Agent AI Orchestration Platform that autonomously coordinates multiple intelligent agents to automate enterprise workflows such as:

- Contract & NDA Review
- IT Support Automation
- HR Employee Onboarding
- Meeting & Calendar Scheduling
- Project Allocation & Management
- Enterprise Analytics & SLA Monitoring

The system uses an MCP (Master Control Program) orchestration layer to dynamically trigger, coordinate, and monitor specialized AI agents in real time.

---

# 🌐 Deployment Link
```text
https://unnathics-mcp-based-multi-agent-platform.streamlit.app/
```



---

# 🌟 Project Vision

Modern enterprises struggle with fragmented workflows spread across departments like HR, Legal, IT, and Project Management.

This project introduces an **AI-Powered Enterprise Operating System** where autonomous agents collaborate together under a centralized MCP orchestration engine.

Instead of manually coordinating across teams, users simply provide a natural language request such as:

```text
"Onboard a new AI Engineer, review contracts, provision access, schedule meetings, and assign project tasks."
```

The MCP automatically:
- understands intent
- activates the required agents
- manages escalation workflows
- performs real enterprise operations
- tracks analytics & SLA metrics

---

# OVERALL ARCHITECTURE:
This is a layered, orchestrator-based microservices architecture:
Key Design Principle: MCP is stateless and horizontally scalable. Each request is independent. Agents only respond to MCP; they never call each other.

<img width="932" height="660" alt="image" src="https://github.com/user-attachments/assets/dfa40a87-a5e1-4cd4-9a43-5e23bb812680" />

# 2. COMPLETE REQUEST LIFECYCLE


USER → FRONTEND
  ↓
[Streamlit dashboard or React UI]
  ↓
POST /api/workflow/submit
  ↓
ORCHESTRATION_API
  ├─ Create workflow record (ID + status: "submitted")
  ├─ Add background task
  └─ Return workflow_id immediately
  ↓
BACKGROUND TASK: orchestrate_workflow(workflow_id, request)
  ├─ classify_request(content)
  │  └─ Keyword-based agent selection
  │     ("contract" → document_review, "password" → it_support, etc.)
  │
  ├─ For each agent:
  │  ├─ Emit AGENT_TRIGGERED event
  │  ├─ Call trigger_agent() → agent_url/api/process
  │  └─ Emit AGENT_COMPLETED event
  │
  └─ Emit WORKFLOW_COMPLETED event
  ↓
FRONTEND (polling or WebSocket)
  ├─ GET /api/workflow/{workflow_id}/status
  ├─ GET /api/workflow/{workflow_id}/events
  └─ Display live event stream
  ↓
[At scale, MCP would be called instead:]
  ├─ ORCHESTRATION_API receives request
  ├─ MCP.process_request(MCPRequest)
  │
  ├─ Step 1: INTENT DETECTION
  │  └─ IntentDetector.detect(text)
  │     ├─ Rule-based matching (keywords)
  │     ├─ Model-based (LLM/NLP)
  │     └─ Semantic fallback (embeddings)
  │
  ├─ Step 2: AGENT REGISTRY LOOKUP
  │  └─ Find agents by detected intent
  │
  ├─ Step 3: CANDIDATE SCORING
  │  └─ Score = 30% intent_match + 25% capability + 20% health
  │            + 15% policy + 5% cost + priority_boost
  │
  ├─ Step 4: POLICY FILTERING
  │  └─ PolicyEngine blocks/allows agents per rules
  │     (compliance, data residency, PII masking)
  │
  ├─ Step 5: PLAN GENERATION
  │  └─ Decide execution mode: sync | async | pipeline
  │
  ├─ Step 6: AGENT INVOCATION (HTTP POST)
  │  └─ Send AgentInvocation with mcp_meta context
  │     {request_id, trace_id, user_id, policies, timeout}
  │
  ├─ Step 7: RESULT AGGREGATION
  │  └─ Consolidate multi-agent responses
  │
  └─ Step 8: RETURN MCPResponse
     {status, decision, result, audit_trail, agent_responses}

FRONTEND receives result
  ├─ Display agent responses
  ├─ Show suggested actions (escalations)
  └─ Handle human approval if needed

  

# 🧠 Core Features

## 🤖 Multi-Agent Architecture
- MCP Core Orchestrator
- Document Review Agent
- IT Support Agent
- HR Onboarding Agent
- Meeting Calendar Agent
- Project Management Agent
- Analytics Agent

---

## 📄 AI Document Review
- Contract classification
- Clause extraction
- Risk analysis
- Semantic similarity search
- Compliance monitoring
- Legal escalation triggers

---

## 🛠 IT Support Automation
- Ticket classification
- Priority prediction
- Voice-enabled support
- Escalation workflows
- SLA monitoring

---

## 👨‍💼 HR Automation
- Employee onboarding
- Team allocation
- Profile generation
- Automated workflow routing

---

## 📅 Meeting Coordination
- Real calendar scheduling
- Natural language date parsing
- Multi-agent collaboration workflows

---

## 📊 Analytics Dashboard
- Live workflow monitoring
- Active agents
- SLA tracking
- Workflow latency
- Escalation analytics
- Enterprise metrics

---

# ⚡ Quick Start Commands

To simplify running the entire MCP Enterprise System, shell scripts are provided.

---

## 🚀 Start All Agents & Services

```bash
bash ~/Documents/SEM-6/MINI-PROJECT/START_ALL_AGENTS.sh
```

This will automatically:
- Start Customer Support Agent
- Start Document Review Agent
- Start MCP Orchestrator
- Start Streamlit Dashboard
- Start React MCP Frontend (if configured)

---

## 🛑 Stop All Running Services

```bash
bash ~/Documents/SEM-6/MINI-PROJECT/STOP_ALL_AGENTS.sh
```

This will terminate:
- FastAPI servers
- Streamlit server
- React frontend
- Background orchestration processes

---

# 📌 Recommended Workflow

## Step 1
Run:

```bash
bash ~/Documents/SEM-6/MINI-PROJECT/START_ALL_AGENTS.sh
```

---

## Step 2
Open:

### Streamlit Dashboard
```text
http://localhost:8501
```

### MCP Frontend UI
```text
http://localhost:3000
```

---

## Step 3
Test enterprise prompts such as:

```text
🚨 EMERGENCY REQUEST 🚨

Immediate team expansion for critical healthcare client crisis

- 3 new senior engineers starting TODAY
- urgent legal contracts need review
- emergency meeting with unathics.btech23@rvu.edu.in on May 23rd 2026
- budget allocation $50,000
- project deadline 48 hours
- need real-time system monitoring
```

---

## Step 4
Watch the MCP orchestrator:
- classify intent
- activate agents
- hand over workflows
- schedule meetings
- analyze contracts
- generate analytics
- visualize orchestration live

---

# 🎬 Demo Workflow

The MCP automatically:

✅ Activates HR onboarding  
✅ Reviews contracts for compliance  
✅ Escalates risky clauses  
✅ Provisions IT access  
✅ Schedules meetings  
✅ Creates project tasks  
✅ Generates analytics dashboard  

---

# 📈 Future Enhancements

- Autonomous Decision Graphs
- LangGraph / CrewAI Integration
- Enterprise RAG Pipelines
- Kubernetes Deployment
- Multi-Cloud Orchestration
- Real-Time Collaboration
- Agent Memory Systems
- Voice-Based Enterprise Control

---

# 🔒 Human-in-the-Loop Governance

The system supports enterprise-grade approval workflows where:

- high-risk legal clauses
- security escalations
- budget approvals

require human authorization before execution.

---

# 📚 Research Inspiration

This project draws inspiration from:
- Agentic AI Systems
- Multi-Agent Enterprise Orchestration
- NLP-based Legal Automation
- AI-driven ITSM Systems
- Autonomous Workflow Platforms

---



# 👨‍💻 Contributors

- Unnathi CS
- Team Members:
  - vaishnavi
  - aditi

---

# 📜 License

This project is developed for academic and enterprise research purposes.

---

# ⭐ Final Note

This project is not just a chatbot.

It is an **Enterprise AI Operating System** capable of autonomous orchestration, intelligent escalation, and real-time multi-agent collaboration.
