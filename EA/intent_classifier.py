"""
Intent classification utilities for better email routing and responses.
"""

import re
from typing import Dict, List, Optional

# Intent keywords mapping
INTENT_KEYWORDS = {
    "technical_support": [
        "error", "bug", "issue", "problem", "not working", "broken", "failed",
        "401", "403", "500", "timeout", "connection", "api", "workflow",
        "execution", "stuck", "slow", "crash", "troubleshoot", "fix"
    ],
    "sales_inquiry": [
        "pricing", "price", "cost", "subscription", "plan", "tier", "trial",
        "demo", "schedule", "purchase", "buy", "quote", "discount", "enterprise",
        "features", "capabilities", "compare"
    ],
    "billing": [
        "invoice", "payment", "billing", "charge", "refund", "credit card",
        "expired", "renewal", "cancel", "upgrade", "downgrade", "receipt"
    ],
    "account_management": [
        "password", "reset", "login", "account", "profile", "settings",
        "api key", "authentication", "2fa", "two factor", "access"
    ],
    "feature_request": [
        "feature", "request", "suggestion", "improvement", "enhancement",
        "add", "new", "wish", "would like"
    ],
    "general_inquiry": [
        "question", "help", "information", "about", "what is", "how does",
        "documentation", "guide", "tutorial", "learn"
    ]
}

def classify_intent(email_content: str, subject: str = "") -> Dict[str, float]:
    """
    Classify email intent based on content and subject.
    
    Args:
        email_content: Email body content
        subject: Email subject line
    
    Returns:
        Dictionary mapping intent types to confidence scores (0-1)
    """
    text = f"{subject} {email_content}".lower()
    
    scores = {}
    total_matches = 0
    
    for intent, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in text)
        scores[intent] = matches
        total_matches += matches
    
    # Normalize scores
    if total_matches > 0:
        scores = {intent: score / total_matches for intent, score in scores.items()}
    else:
        # Default to general inquiry if no matches
        scores["general_inquiry"] = 1.0
    
    return scores

def get_primary_intent(email_content: str, subject: str = "") -> str:
    """
    Get the primary intent classification.
    
    Args:
        email_content: Email body content
        subject: Email subject line
    
    Returns:
        Primary intent string
    """
    scores = classify_intent(email_content, subject)
    return max(scores.items(), key=lambda x: x[1])[0]

def is_spam(email_content: str, subject: str = "") -> bool:
    """
    Determine if email is likely spam.
    
    Args:
        email_content: Email body content
        subject: Email subject line
    
    Returns:
        True if likely spam, False otherwise
    """
    text = f"{subject} {email_content}".lower()
    
    # Spam indicators
    spam_patterns = [
        r"click here.*(?:now|immediately|urgent)",
        r"(?:free|win|prize|congratulations).*(?:click|link|call)",
        r"viagra|cialis|pharmacy",
        r"make money.*(?:fast|easy|guaranteed)",
        r"limited time.*offer",
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if completely unrelated to company
    company_keywords = [
        "companyz", "nexusflow", "nexus flow", "workflow", "automation",
        "api", "integration", "connector", "support", "ticket"
    ]
    
    has_company_keyword = any(keyword in text for keyword in company_keywords)
    
    # If no company keywords and very short, might be spam
    if not has_company_keyword and len(text) < 50:
        return True
    
    return False

def extract_urgency(email_content: str, subject: str = "") -> str:
    """
    Extract urgency level from email.
    
    Args:
        email_content: Email body content
        subject: Email subject line
    
    Returns:
        Urgency level: "high", "medium", or "low"
    """
    text = f"{subject} {email_content}".lower()
    
    high_urgency_keywords = [
        "urgent", "asap", "immediately", "critical", "emergency", "down",
        "broken", "not working", "failed", "error", "outage"
    ]
    
    medium_urgency_keywords = [
        "soon", "quickly", "important", "issue", "problem", "help"
    ]
    
    if any(keyword in text for keyword in high_urgency_keywords):
        return "high"
    elif any(keyword in text for keyword in medium_urgency_keywords):
        return "medium"
    else:
        return "low"

