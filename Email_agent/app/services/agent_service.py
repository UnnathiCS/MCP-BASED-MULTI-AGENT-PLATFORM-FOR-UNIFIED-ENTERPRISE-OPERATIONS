import os
import re
import glob
import csv
import json
import logging

import chromadb
from sentence_transformers import SentenceTransformer
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = str(BASE_DIR / "vector_db_simple")
DATA_PATH = str(BASE_DIR / "knowledge_base") + "/"
MODEL_NAME = 'all-MiniLM-L6-v2'

INTENT_KEYWORDS = {
    "technical_support": ["error", "bug", "issue", "problem", "not working", "broken", "failed",
        "401", "403", "500", "timeout", "connection", "api", "workflow", "execution", "stuck", "slow", "crash", "troubleshoot", "fix"],
    "sales_inquiry": ["pricing", "price", "cost", "subscription", "plan", "tier", "trial",
        "demo", "schedule", "purchase", "buy", "quote", "discount", "enterprise", "features", "capabilities", "compare"],
    "billing": ["invoice", "payment", "billing", "charge", "refund", "credit card",
        "expired", "renewal", "cancel", "upgrade", "downgrade", "receipt"],
    "account_management": ["password", "reset", "login", "account", "profile", "settings",
        "api key", "authentication", "2fa", "two factor", "access"],
    "feature_request": ["feature", "request", "suggestion", "improvement", "enhancement", "add", "new", "wish", "would like"],
    "general_inquiry": ["question", "help", "information", "about", "what is", "how does", "documentation", "guide", "tutorial", "learn"]
}

print("Loading models and vector database...")
llm = None
if GEMINI_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Failed to initialize Gemini LLM: {e}")

embedding_model = SentenceTransformer(MODEL_NAME)
db_client = chromadb.PersistentClient(path=DB_PATH)


def _split_text(text, chunk_size=500, overlap=50):
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            lp = chunk.rfind('.')
            ls = chunk.rfind(' ')
            if lp > chunk_size * 0.7:
                end = start + lp + 1
            elif ls > chunk_size * 0.7:
                end = start + ls
        chunks.append(text[start:end].strip())
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def _create_vector_db():
    import PyPDF2
    documents = []
    for fp in glob.glob(os.path.join(DATA_PATH, "*.txt")):
        with open(fp, 'r', encoding='utf-8') as f:
            documents.append({'content': f.read(), 'source': os.path.basename(fp)})
    for fp in glob.glob(os.path.join(DATA_PATH, "*.pdf")):
        content = ""
        try:
            with open(fp, 'rb') as f:
                for page in PyPDF2.PdfReader(f).pages:
                    content += page.extract_text() or ""
        except Exception:
            pass
        documents.append({'content': content, 'source': os.path.basename(fp)})
    all_chunks, all_metadata = [], []
    for doc in documents:
        chunks = _split_text(doc['content'])
        all_chunks.extend(chunks)
        all_metadata.extend([{'source': doc['source']}] * len(chunks))
    embeddings = embedding_model.encode(all_chunks, show_progress_bar=True)
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection("nexusflow_docs")
    except:
        pass
    col = client.create_collection("nexusflow_docs")
    col.add(documents=all_chunks, embeddings=embeddings.tolist(),
            metadatas=all_metadata, ids=[f"doc_{i}" for i in range(len(all_chunks))])
    return col


try:
    collection = db_client.get_collection("nexusflow_docs")
except Exception:
    print("[i] Vector collection not found. Creating from knowledge base...")
    collection = _create_vector_db()

print("Agent components ready!")


def search_knowledge_base(query: str) -> str:
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=3)
    if not results['documents'][0]:
        return "No relevant information found in the knowledge base."
    return "".join(f"Relevant Document {i+1}:\n{doc}\n\n" for i, doc in enumerate(results['documents'][0]))


knowledge_base_tool = Tool(
    name="search_company_knowledge_base",
    func=search_knowledge_base,
    description="Use this tool to find information about company products (like NexusFlow), pricing, policies, and technical support procedures.",
)

system_prompt = """
You are a professional customer support representative for CompanyZ. Your role is to assist customers with inquiries about CompanyZ products, particularly NexusFlow.

IMPORTANT: You will be given the full conversation history. Focus on the most recent message.

1. If the latest message is completely unrelated to CompanyZ/NexusFlow, output only: SPAM
2. If related, use the 'search_company_knowledge_base' tool to find relevant information.
3. Synthesize the information into a professional email response, or escalate to support@companyz.com if no info found.

Always be helpful, accurate, and courteous.
"""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{input}"), ("placeholder", "{agent_scratchpad}")]
)
agent = create_tool_calling_agent(llm, [knowledge_base_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[knowledge_base_tool], verbose=True)


def classify_intent(email_content: str, subject: str = "") -> dict:
    text = f"{subject} {email_content}".lower()
    scores = {intent: sum(1 for kw in kws if kw in text) for intent, kws in INTENT_KEYWORDS.items()}
    total = sum(scores.values())
    return {intent: score / total for intent, score in scores.items()} if total > 0 else {"general_inquiry": 1.0}


def get_primary_intent(email_content: str, subject: str = "") -> str:
    return max(classify_intent(email_content, subject).items(), key=lambda x: x[1])[0]


def is_spam(email_content: str, subject: str = "") -> bool:
    text = f"{subject} {email_content}".lower()
    spam_patterns = [
        r"click here.*(?:now|immediately|urgent)",
        r"(?:free|win|prize|congratulations).*(?:click|link|call)",
        r"viagra|cialis|pharmacy",
        r"make money.*(?:fast|easy|guaranteed)",
        r"limited time.*offer",
    ]
    if any(re.search(p, text, re.IGNORECASE) for p in spam_patterns):
        return True
    company_keywords = ["companyz", "nexusflow", "nexus flow", "workflow", "automation",
                        "api", "integration", "connector", "support", "ticket"]
    return not any(kw in text for kw in company_keywords) and len(text) < 50


def extract_urgency(email_content: str, subject: str = "") -> str:
    text = f"{subject} {email_content}".lower()
    if any(kw in text for kw in ["urgent", "asap", "immediately", "critical", "emergency", "down", "broken", "not working", "failed", "error", "outage"]):
        return "high"
    if any(kw in text for kw in ["soon", "quickly", "important", "issue", "problem", "help"]):
        return "medium"
    return "low"


def process_email_with_agent(email_content: str, subject: str = "") -> str:
    if is_spam(email_content, subject):
        return "SPAM"
    primary_intent = get_primary_intent(email_content, subject)
    urgency = extract_urgency(email_content, subject)
    enhanced_prompt = email_content
    if primary_intent != "general_inquiry":
        enhanced_prompt = f"[Intent: {primary_intent}, Urgency: {urgency}]\n\n{email_content}"
    if llm is not None:
        try:
            response = agent_executor.invoke({"input": enhanced_prompt})
            return response['output']
        except Exception as e:
            print(f"[!] LLM processing failed: {e}, falling back to rule-based")
    kb_result = search_knowledge_base(email_content)
    if kb_result and not kb_result.startswith("No relevant"):
        cleaned = re.sub(r'^\s*Relevant\s+Document\s+\d+\s*:\s*', '', kb_result, flags=re.IGNORECASE | re.MULTILINE).strip()
        return (f"Thank you for contacting CompanyZ Support.\n\nBased on your inquiry:\n\n{cleaned}\n\n"
                "If the issue continues, please contact support@companyz.com.")
    if any(kw in email_content.lower() for kw in ["companyz", "nexusflow", "pricing", "subscription", "trial"]):
        return "We currently do not have information about this. Please contact support@companyz.com."
    return "SPAM"
