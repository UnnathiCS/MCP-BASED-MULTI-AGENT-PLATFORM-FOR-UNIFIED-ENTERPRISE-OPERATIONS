import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
import chromadb
from sentence_transformers import SentenceTransformer
from ingest_data import create_vector_db
from intent_classifier import classify_intent, get_primary_intent, is_spam, extract_urgency

# Load environment variables early so GEMINI_API_KEY is available on import
load_dotenv()

DB_PATH = "vector_db_simple"
MODEL_NAME = 'all-MiniLM-L6-v2'
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Models and DB Client 
print("Loading models and vector database...")
# Initialize LLM only if API key is present; otherwise we will use a lightweight fallback
llm = None
if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"[!] Failed to initialize Gemini LLM, falling back to non-LLM mode: {e}")

embedding_model = SentenceTransformer(MODEL_NAME)
db_client = chromadb.PersistentClient(path=DB_PATH)

# Ensure the collection exists; if not, create it from the local knowledge base
try:
    collection = db_client.get_collection("nexusflow_docs")
except Exception:
    print("[i] Vector collection not found. Creating from knowledge base...")
    create_vector_db()
    collection = db_client.get_collection("nexusflow_docs")

print("✅ Agent components ready!")

# Define the RAG Tool 
def search_knowledge_base(query: str) -> str:
    """The function that performs the RAG search."""
    print(f"Searching knowledge base for: '{query}'")
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=3)
    
    if not results['documents'][0]:
        return "No relevant information found in the knowledge base."
        
    context = ""
    for i, doc in enumerate(results['documents'][0]):
        context += f"Relevant Document {i+1}:\n{doc}\n\n"
    return context

# Wrap the function in a LangChain Tool object
knowledge_base_tool = Tool(
    name="search_company_knowledge_base",
    func=search_knowledge_base,
    description="Use this tool to find information about company products (like NexusFlow), pricing, policies, and technical support procedures. Pass the user's full question as the input.",
)
tools = [knowledge_base_tool]

# Create the Agent 
# This prompt guides the agent's reasoning process.

system_prompt = """
You are a professional customer support representative for CompanyZ, a leading enterprise AI solutions provider. Your role is to assist customers with inquiries about CompanyZ products, particularly NexusFlow, our flagship AI workflow automation platform.

IMPORTANT: You will be given the full conversation history. Your response must be based on the ENTIRE thread, focusing on the most recent message to understand the user's latest inquiry.

RESPONSE GUIDELINES:
- Write in a professional, courteous, and helpful tone
- Use proper business email formatting with clear paragraphs
- Address the customer by name if available in the conversation
- Acknowledge their question or concern directly
- Provide clear, actionable information
- Use bullet points or numbered lists when explaining multiple steps or features
- Include relevant links or references when appropriate
- End with a professional closing and offer further assistance

PROCESS TO FOLLOW:

1. Analyze the conversation: First, determine if the latest message is related to CompanyZ, NexusFlow, our products, pricing, technical support, or business inquiries.

2. If the latest message is completely unrelated (e.g., personal spam, marketing from other companies, or random questions like "what time is it?"), your ONLY output should be the single word: SPAM

3. If the latest message is related to the company, you MUST use the 'search_company_knowledge_base' tool to find relevant information.

4. After searching:
   - If the tool finds a specific answer: Synthesize that information into a professional, well-structured email response that:
     * Greets the customer appropriately
     * Directly addresses their question or concern
     * Provides clear, accurate information from the knowledge base
     * Uses proper formatting (paragraphs, lists if needed)
     * Offers additional help or next steps
     * Closes professionally (e.g., "Best regards," "Sincerely,")
   
   - If the tool returns 'No relevant information found': Provide a professional escalation message that:
     * Acknowledges their inquiry
     * Explains that you're escalating to our specialized team
     * Provides contact information: support@companyz.com
     * Assures them of a timely response
     * Maintains a helpful, professional tone

EXAMPLE RESPONSE STRUCTURE:
---
Subject: Re: [Original Subject]

Dear [Customer Name],

Thank you for contacting CompanyZ regarding [their inquiry topic].

[Main response content with clear information, formatted professionally]

[If applicable: Next steps or additional resources]

If you have any further questions, please don't hesitate to reach out. Our support team is here to help.

Best regards,
CompanyZ Support Team
support@companyz.com
---

Remember: Your responses represent CompanyZ professionally. Always be helpful, accurate, and courteous.
"""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{input}"), ("placeholder", "{agent_scratchpad}")]
)

# Create the agent by tying together the LLM, tools, and prompt
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- Define the main function to be called from main.py ---
def _is_related_to_company(text: str) -> bool:
    text_lower = text.lower()
    keywords = ["companyz", "nexusflow", "nexus flow", "pricing", "subscription", "trial"]
    return any(keyword in text_lower for keyword in keywords)


def process_email_with_agent(email_content: str, subject: str = "") -> str:
    """
    Process an email using the agentic setup with enhanced intent classification.
    Falls back to a lightweight rules-based flow if LLM is unavailable.
    
    Args:
        email_content: Full email content or conversation history
        subject: Email subject line (optional, for better intent classification)
    
    Returns:
        Agent response text
    """
    # Pre-classify intent for better routing
    intent_scores = classify_intent(email_content, subject)
    primary_intent = get_primary_intent(email_content, subject)
    urgency = extract_urgency(email_content, subject)
    
    # Check for spam first
    if is_spam(email_content, subject):
        return "SPAM"
    
    # Enhance prompt with intent information
    enhanced_prompt = email_content
    if primary_intent != "general_inquiry":
        enhanced_prompt = f"[Intent: {primary_intent}, Urgency: {urgency}]\n\n{email_content}"
    
    if llm is not None:
        try:
            response = agent_executor.invoke({"input": enhanced_prompt})
            return response['output']
        except Exception as e:
            print(f"[!] LLM processing failed: {e}, falling back to rule-based")
            # Fall through to fallback

    # Fallback behavior without LLM
    kb_result = search_knowledge_base(email_content)
    if kb_result and not kb_result.startswith("No relevant"):
        return kb_result

    if _is_related_to_company(email_content):
        return (
            "We currently do not have information about this in our knowledge base. "
            "Please contact CompanyZ customer care at support@companyz.com for assistance."
        )

    return "SPAM"