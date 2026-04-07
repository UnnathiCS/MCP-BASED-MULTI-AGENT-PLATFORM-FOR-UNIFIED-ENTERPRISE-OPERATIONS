# 🧠 MCP Unified Agent System

**One screen. User types problem. MCP decides which agent. Agent executes. Show result.**

## 🚀 Quick Start (3 Terminals)

### Terminal 1: Support Agent
```bash
cd ~/Documents/SEM-6/MINI-PROJECT/Customer_support_agent
source venv/bin/activate
python main.py
```

### Terminal 2: Document Agent
```bash
cd ~/Documents/SEM-6/MINI-PROJECT/Document_Review_agent/document_review_agent
source venv/bin/activate
python app/main.py
```

### Terminal 3: Dashboard
```bash
cd ~/Documents/SEM-6/MINI-PROJECT
streamlit run app.py
```

**Open:** http://localhost:8501

## 📝 How It Works

### You Type: "My VPN is not working"
```
↓
MCP Analyzes: "This is IT Support issue"
↓
MCP Scores Agents:
  - Customer Support: 0.94 ✅ SELECTED
  - Document Review: 0.15
↓
Routes to: Customer Support Agent (port 8000)
↓
You See:
  ✓ Solution provided
  ✓ MCP's decision reasoning (all 6 factors)
  ✓ Processing timeline (milliseconds)
  ✓ Why other agents weren't selected
```

### You Type: "Review this contract for risks"
```
↓
MCP Analyzes: "This is Document Review task"
↓
MCP Scores Agents:
  - Document Review: 0.98 ✅ SELECTED
  - Customer Support: 0.25
↓
Routes to: Document Review Agent (port 8001)
↓
You Upload PDF (or mention filename)
↓
You See:
  ✓ Risk assessment
  ✓ Clause analysis
  ✓ Recommendations
  ✓ MCP's decision reasoning
  ✓ Processing timeline
```

## 📦 Install Requirements
```bash
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy transformers torch openai-whisper pydantic streamlit requests
```

## 🎯 File Structure
```
app_mcp_unified.py          ← Main dashboard (RUN THIS)
Customer_support_agent/     ← IT support (Terminal 1)
Document_Review_agent/      ← Document analysis (Terminal 2)
```

## 🧠 MCP Decision Engine (What Happens Behind Scenes)

1. **Intent Detection**
   - Analyzes user input for keywords
   - Detects if it's a support issue or document review

2. **Agent Scoring (6 Factors)**
   - Capability Match (Does agent handle this?)
   - Success Rate (How reliable?)
   - Load Factor (How busy?)
   - Specialization (Perfect match?)
   - Policy Compliance (Any restrictions?)
   - User Preference (Used before?)

3. **Decision Making**
   - Scores all agents (0.0 to 1.0)
   - Selects agent with highest score
   - Routes request automatically

4. **Execution**
   - Agent processes request
   - Returns result
   - MCP shows full transparency

## 🔍 What You See in UI

**Left Column:**
- Your problem/task input
- File upload (optional)

**Right Column:**
- Agent Status (Online/Offline)
- How MCP Works (info)
- Settings (show timeline, scoring)

**After Submit:**
- 🧠 MCP Decision Analysis
  - Step 1: What category was detected?
  - Step 2: How were agents scored?
  - Other agents considered (and why not)
- 🎯 Agent Response
  - Solution or Analysis
  - Detailed results
- ⏱️ Processing Timeline
  - Millisecond-by-millisecond breakdown
- 📜 Request History
  - All previous requests

## 💡 Examples to Try

### Support Issues:
- "I can't connect to VPN"
- "My Teams application keeps crashing"
- "I forgot my password"
- "Printer is not working"

### Document Reviews:
- "Review this NDA for risks"
- "Analyze this contract"
- "Check this policy document"
- Upload any PDF and ask for analysis

## 🛠️ Requirements
- Python 3.7+
- fastapi, uvicorn
- streamlit
- requests
- sentence-transformers, faiss-cpu
- torch, transformers
- openai-whisper
- pydantic

## ⚠️ Important
- All 3 services must be running simultaneously
- Ports must be free: 8000, 8001, 8501
- MCP analyzes input and decides which agent to use
- No manual selection needed - automatic routing!

## 🎓 Learn More
- `START_HERE.md` - Quick start guide
- `INTEGRATED_DASHBOARD_GUIDE.md` - Detailed features
- `SYSTEM_VISUAL_OVERVIEW.md` - Visual diagrams

---

**Version:** 2.0.0 (Unified MCP System)
**Status:** ✅ Ready to use