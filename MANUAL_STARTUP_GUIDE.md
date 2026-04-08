# 🚀 MANUAL STARTUP - 3 Simple Steps

## The Quick Way (Copy-Paste Ready)

You need **4 terminal windows/tabs** running simultaneously.

---

## TERMINAL 1: Support Agent (Port 8000)

```bash
cd ~/Documents/SEM-6/MINI-PROJECT/Customer_support_agent
source .venv/bin/activate
python main.py
```

**✅ You should see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## TERMINAL 2: Document Agent (Port 8001)

```bash
cd ~/Documents/SEM-6/MINI-PROJECT/Document_Review_agent/document_review_agent
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001
```

**✅ You should see:**
```
INFO:     Started server process
INFO:     Application startup complete
```

---

## TERMINAL 3: Meeting Agent (Port 8002) ⭐ THIS ONE IS KEY

```bash
cd ~/Documents/SEM-6/MINI-PROJECT/meeting-calendar-agent
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --port 8002
```

**✅ You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8002
```

---

## TERMINAL 4: Streamlit Dashboard (Port 8501)

```bash
cd ~/Documents/SEM-6/MINI-PROJECT
streamlit run app.py
```

**✅ You should see:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

## ✅ Verify All Running

In a new terminal, run these checks:

```bash
# Check Support Agent
curl http://localhost:8000/health

# Check Document Agent
curl http://localhost:8001/health

# Check Meeting Agent (THE KEY ONE)
curl http://localhost:8002/health

# Check Dashboard
curl http://localhost:8501 | head -20
```

**Expected output for health checks:**
```json
{"status": "ok"}
```

---

## 🔴 If Meeting Agent Connection Fails

### Problem: `Connection refused on port 8002`

**Solution 1: Check if Meeting Agent is running**
```bash
# In a terminal, check if port 8002 is in use
lsof -i :8002

# If nothing shows, the meeting agent isn't running
# Go to TERMINAL 3 above and run the meeting agent command
```

**Solution 2: Kill any process on port 8002**
```bash
# Find process on port 8002
lsof -i :8002

# Kill it (replace PID with actual PID from lsof output)
kill -9 <PID>

# Then restart Terminal 3 with the meeting agent command
```

**Solution 3: Check meeting-calendar-agent directory exists**
```bash
ls -la ~/Documents/SEM-6/MINI-PROJECT/meeting-calendar-agent/
```

Should show:
```
app/
requirements.txt
README.md
tests/
```

---

## 📋 Startup Checklist

- [ ] Terminal 1 running: Support Agent (8000)
- [ ] Terminal 2 running: Document Agent (8001)
- [ ] Terminal 3 running: Meeting Agent (8002) ⭐
- [ ] Terminal 4 running: Streamlit (8501)
- [ ] All health checks pass
- [ ] Dashboard loads at http://localhost:8501
- [ ] No errors in any terminal

---

## 🧪 Test Meeting Agent Integration

Once all 4 services are running:

1. **Open dashboard:** http://localhost:8501
2. **Type in the message box:**
   ```
   Schedule a meeting with the team next Monday at 2 PM
   ```
3. **Click "Submit"**
4. **Look for:**
   - ✅ MCP detects "meetings" agent
   - ✅ Routes to port 8002
   - ✅ Shows meeting details
   - ✅ No connection errors

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused: 8002` | Meeting Agent not running (Terminal 3) |
| `Port 8002 already in use` | `lsof -i :8002` then `kill -9 <PID>` |
| `Module not found` error | Run `pip install -r requirements.txt` in that agent's folder |
| Dashboard shows error | Check all 4 terminals are running |
| Meeting request times out | Check Meeting Agent terminal (3) for errors |

---

## ⚡ Quick Debug

**Check all services at once:**
```bash
for port in 8000 8001 8002; do
  echo "Port $port:"
  curl -s http://localhost:$port/health || echo "NOT RUNNING"
done
```

**Monitor all logs:**
```bash
# In separate terminals, tail each agent's logs
# This helps identify where errors occur
```

---

**Ready? Start the terminals and test! 🎉**
