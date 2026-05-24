# 🚀 MCP Platform - Deployment Guide

The app now **automatically starts all backends on startup**. Here are deployment options:

---

## **🟢 Option 1: Local Deployment (No Manual Backend Start)**

The app will auto-start backends. Just run:

```bash
streamlit run app.py
```

✅ **All backends will start automatically!**

---

## **🐳 Option 2: Docker Compose (Recommended for Production)**

Deploy all services in containers:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Access the app at:** `http://localhost:8501`

✅ **All backends run in separate containers automatically!**

---

## **☁️ Option 3: Streamlit Cloud (Free)**

1. Push code to GitHub:
```bash
git add .
git commit -m "Add auto-start backend functionality"
git push origin main
```

2. Go to https://share.streamlit.io
3. Click "New app"
4. Select your repository
5. Select `app.py` as main file
6. Deploy!

**Note:** Streamlit Cloud won't run backends automatically. Use Docker option instead.

When backends are not running, the UI uses **demo mode** (sample workflow data) automatically on Streamlit Cloud. Local `streamlit run` always calls real agent APIs.

The app auto-detects Streamlit Community Cloud and other hosts (no bash/lsof messages on the home page).

If detection fails, add to Streamlit Cloud **Secrets** (TOML):

```toml
MCP_DEPLOYMENT_MODE = "deployed"
```

For local development, set `MCP_DEPLOYMENT_MODE=local` to disable demo mode explicitly.

---

## **🚢 Option 4: Railway / Render / Heroku**

Create `Procfile`:

```
web: streamlit run app.py --logger.level=info
```

Or use `docker-compose.yml` with:

```bash
# Railway
railway up

# Render
render deploy

# Heroku
git push heroku main
```

---

## **🔧 Configuration**

The auto-start tries to run backends at these paths:
- Customer_support_agent (port 8000)
- Document_Review_agent/document_review_agent (port 8001)
- meeting-calendar-agent (port 8002)
- HR_Onboarding_agent (port 8003)
- Email_agent (port 8004)
- Project_Management_agent (port 8005)
- Analytics_agent/app (port 8007)

If a service is already running, it will skip it.

---

## **✅ Verification**

Check that backends are running:

```bash
# macOS/Linux
lsof -i :8000 -i :8001 -i :8002 -i :8003 -i :8004 -i :8005 -i :8007 | grep LISTEN

# Windows (PowerShell)
netstat -ano | findstr :8000
```

---

## **🎯 What Changed**

✨ **Auto-Start Feature Added:**
- Backends start automatically when app launches
- No manual terminal commands needed
- Proper cleanup on app exit
- Health check before starting (won't duplicate if already running)

Now your deployed app is **completely independent**! 🎉
