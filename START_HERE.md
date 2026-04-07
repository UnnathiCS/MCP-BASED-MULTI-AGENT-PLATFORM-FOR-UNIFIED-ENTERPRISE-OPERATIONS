# ⚡ QUICK START - 5 MINUTES TO RUNNING

## ✅ Verification Passed!

All packages, environment, and LangGraph setup are working correctly.

```
✓ All 8 packages installed
✓ GROQ_API_KEY configured  
✓ Imports working
✓ LangGraph graph created
```

---

## 🚀 Start Everything (Easiest Way)

### One Command:
```bash
cd ~/Documents/SEM-6/MINI-PROJECT
./COMPLETE_STARTUP.sh
```

That's it! The script will:
- ✅ Verify everything is set up
- ✅ Start Support Agent (port 8000)
- ✅ Start Document Agent (port 8001)
- ✅ Start Streamlit Dashboard (port 8501)
- ✅ Show you the access URLs

---

## 🧪 Test LangGraph is Working

In a new terminal (after starting services):
```bash
cd ~/Documents/SEM-6/MINI-PROJECT
python3 test_langgraph.py
```

**You should see:**
- ✅ 3 test queries
- ✅ Processing steps including `"decision_with_llm"`
- ✅ LLM reasoning in color
- ✅ Proof that Groq LLM is being invoked

---

## 🌐 Access Your System

Open your browser:
- **Dashboard**: http://localhost:8501
- **Support API**: http://localhost:8000
- **Document API**: http://localhost:8001

---

## 📊 What's Running?

```
LangGraph 4-Node Workflow
├── Node 1: Policy Search (semantic embeddings)
├── Node 2: Sentiment Analysis
├── Node 3: Classification
└── Node 4: ⭐ Groq LLM Decision (FREE - Mixtral 8x7b)
```

---

## 🔍 Verify LLM is Working

**In terminal, test the API:**
```bash
curl -X POST http://localhost:8000/debug/test-langgraph \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"test","message":"My VPN is down"}'
```

**You should see in response:**
```json
{
  "processing_steps": [
    "policy_search",
    "sentiment_analysis",
    "classification",
    "decision_with_llm"  ← ⭐ Proves LLM was used
  ]
}
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `COMPLETE_STARTUP.sh` | Start all services |
| `test_langgraph.py` | Test LLM integration |
| `verify_langgraph_setup.py` | Check setup |
| `Customer_support_agent/.env` | Groq API key |
| `LANGGRAPH_STATUS_COMPLETE.md` | Full status report |
| `LANGGRAPH_EXPLAINED.md` | Architecture details |

---

## ✨ Key Highlights for Faculty

Show them:
1. **Dashboard** → Enter a support query
2. **Expand** → "🔧 LangGraph Workflow" section
3. **Show**:
   - 4-step processing pipeline
   - Agent reasoning chain
   - **"decision_with_llm"** in processing steps
4. **Explain**: Node 4 uses Groq LLM to decide (not just rules)

---

## 🆘 Troubleshooting

**Problem**: Services won't start
```bash
python3 verify_langgraph_setup.py
```
This will tell you exactly what's wrong.

**Problem**: LLM falling back to rules
Check if API key is set:
```bash
cat Customer_support_agent/.env | grep GROQ_API_KEY
```

**Problem**: Port already in use
Find and kill the process:
```bash
lsof -i :8000  # See what's using port 8000
kill -9 <PID>
```

---

## 📚 Full Documentation

For detailed information, see:
- `LANGGRAPH_EXPLAINED.md` - Full architecture explanation
- `LANGGRAPH_STATUS_COMPLETE.md` - Complete status report
- `GROQ_API_SETUP.md` - Groq setup details
- `QUICK_START.md` - Extended quick start

---

## ✅ You're Ready!

```
1. Run: ./COMPLETE_STARTUP.sh
2. Test: python3 test_langgraph.py
3. View: http://localhost:8501
4. Show faculty!
```

**Status: ✅ System Ready**

All LangGraph and Groq integration is complete, verified, and ready for evaluation.

---

*5-minute setup time • ~30 seconds per test • Full system operational*
