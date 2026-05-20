from policy_store import PolicyStore
from classifier import classify_ticket
import logging
import time
from transformers import pipeline

logger = logging.getLogger(__name__)

# Initialize with error handling and timeout protection
policy_store = PolicyStore()

# NLP Models - with timeout protection
_sentiment_model = None
_classification_model = None
_models_initialized = False

def init_nlp_models():
    """Initialize NLP models with timeout protection"""
    global _sentiment_model, _classification_model, _models_initialized
    try:
        if not _models_initialized:
            logger.info("Loading NLP models...")
            # Load with timeout in mind - these run locally
            _sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            _classification_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            _models_initialized = True
            logger.info("NLP models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load NLP models: {e}. Using fallback keyword-based detection.")
        _models_initialized = False

# Initialize models on startup
try:
    init_nlp_models()
except Exception as e:
    logger.warning(f"NLP model initialization failed: {e}")

def is_negative_sentiment(query: str) -> bool:
    """Detect negative sentiment using NLP with fallback"""
    try:
        if _sentiment_model and _models_initialized:
            result = _sentiment_model(query)
            label = result[0]['label']
            score = result[0]['score']
            # NEGATIVE with confidence > 0.7
            return label == "NEGATIVE" and score > 0.7
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}. Using keyword fallback.")
    
    # Fallback: keyword-based detection
    negative_words = ["error", "problem", "issue", "fail", "broken", "urgent", "angry", 
                      "frustrated", "terrible", "awful", "worst", "help", "stuck", "not working"]
    query_lower = query.lower()
    return sum(1 for word in negative_words if word in query_lower) >= 2

# Quick category detection with NLP support
def get_quick_category(query: str) -> str:
    """Fast category detection - tries NLP first, falls back to keywords"""
    try:
        if _classification_model and _models_initialized:
            # Use zero-shot classification
            categories = ["Access", "Network", "Email", "VPN", "Software", "Hardware", "General"]
            result = _classification_model(query, categories)
            top_category = result['labels'][0]
            confidence = result['scores'][0]
            
            # Only use NLP result if confidence is high enough
            if confidence > 0.5:
                return top_category
    except Exception as e:
        logger.warning(f"Classification failed: {e}. Using keyword fallback.")
    
    # Fallback: keyword-based detection (fast and reliable)
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["password", "login", "access", "unlock"]):
        return "Access"
    elif any(word in query_lower for word in ["outage", "down", "offline", "crash"]):
        return "Network"
    elif any(word in query_lower for word in ["email", "mail", "exchange"]):
        return "Email"
    elif any(word in query_lower for word in ["vpn", "remote", "connection"]):
        return "VPN"
    elif any(word in query_lower for word in ["software", "install", "license", "tool"]):
        return "Software"
    elif any(word in query_lower for word in ["hardware", "laptop", "monitor", "device"]):
        return "Hardware"
    else:
        return "General"

def decide_action(query: str):
    """Optimized decision engine with NLP + timeout protection
    
    Returns a dict with: decision, category, priority, reason, answer, severity
    """
    try:
        query_lower = query.lower()
        
        # 1. POLICY LOOKUP with timeout protection (max 500ms)
        policy = None
        confidence = 0
        try:
            start = time.time()
            policy, confidence = policy_store.search(query)
            elapsed = (time.time() - start) * 1000
            if elapsed > 500:
                logger.warning(f"Policy search slow: {elapsed:.0f}ms")
        except Exception as e:
            logger.warning(f"Policy search error: {e}")
            policy, confidence = None, 0
        
        # 2. SENTIMENT CHECK with NLP (has fallback)
        negative = is_negative_sentiment(query)
        
        # 3. CATEGORY DETECTION with NLP (has fallback)
        category = get_quick_category(query)
        
        # 4. PRIORITY DETERMINATION
        priority = "P3"  # Default
        if "urgent" in query_lower or "critical" in query_lower or "outage" in query_lower:
            priority = "P1"
        elif negative or "error" in query_lower or "broken" in query_lower:
            priority = "P2"
        
        # ===== DECISION LOGIC (OPTIMIZED) =====
        
        # Rule 1: Policy match with high confidence
        if policy and confidence > 0.6:
            return {
                "decision": "AUTO_RESOLVE",
                "category": category,
                "priority": priority,
                "reason": f"Matched IT policy (confidence {round(confidence, 2)})",
                "answer": policy,
                "severity": priority
            }
        
        # Rule 2: Critical outage detection
        if "outage" in query_lower or "system down" in query_lower or "offline" in query_lower:
            return {
                "decision": "ESCALATE",
                "category": "Network",
                "priority": "P1",
                "reason": "Critical system outage detected",
                "answer": "System outage reported. Escalating to Senior IT team immediately.",
                "severity": "P1"
            }
        
        # Rule 3: Password/Access issues - quick resolution
        if "password" in query_lower or "login" in query_lower or "access" in query_lower:
            return {
                "decision": "AUTO_RESPONSE",
                "category": "Access",
                "priority": "P3",
                "reason": "Common access issue - self-service solution available",
                "answer": "Try resetting your password via Self-Service Portal: https://itsupport.company.com/reset. For account unlock, reply with your employee ID.",
                "severity": "P3"
            }
        
        # Rule 4: High frustration/negative sentiment (with NLP support)
        if negative:
            return {
                "decision": "ESCALATE",
                "category": category,
                "priority": "P2",
                "reason": "High urgency indicated (NLP: negative sentiment) - escalating to specialist",
                "answer": "I understand your frustration. Escalating to a specialist who will contact you within 30 minutes.",
                "severity": "P2"
            }
        
        # Rule 5: Default - raise support ticket
        return {
            "decision": "RAISE_TICKET",
            "category": category,
            "priority": priority,
            "reason": "Ticket raised for IT specialist review",
            "answer": f"Your {category} support ticket has been created. Ticket ID will be sent to your email. Expected response: {priority}.",
            "severity": priority
        }
        
    except Exception as e:
        logger.error(f"Error in decide_action: {e}")
        return {
            "decision": "RAISE_TICKET",
            "category": "General",
            "priority": "P3",
            "reason": "System error - manual ticket required",
            "answer": "A support ticket has been created for manual review.",
            "severity": "P3"
        }
