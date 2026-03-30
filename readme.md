install these:
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy transformers torch openai-whisper pydantic

First, run backend:

source venv/bin/activate


terminal-1

cd ~/Documents/SEM-6/MINI-PROJECT/Document_Review_agent/document_review_agent
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --port 8001

terminal-2

cd ~/Documents/SEM-6/MINI-PROJECT/Customer_support_agent
source venv/bin/activate
python3 -m uvicorn main:app --reload --port 8000

terminal - 3
streamlit run app.py

https://www.kaggle.com/datasets/swapniljadhav96/itsm-dataset?resource=download