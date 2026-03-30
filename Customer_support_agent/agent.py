from transformers import pipeline
from policy_store import PolicyStore
from classifier import classify_ticket

sentiment_analyzer = pipeline("sentiment-analysis")
classifier_nli = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

LABELS = ["system outage", "vpn issue", "password issue", "software request", "general issue"]

policy_store = PolicyStore()


def decide_action(query: str):
    """Decide what to do with an incoming user message.

    Returns a dict with: decision, category, priority, reason, answer, severity
    """

    # Policy lookup
    policy, confidence = policy_store.search(query)

    # Sentiment check
    sentiment = sentiment_analyzer(query)[0]
    negative = sentiment.get("label") == "NEGATIVE"

    # Lightweight keyword classification -> category + suggested priority
    category, suggested_priority = classify_ticket(query)

    # Fine-grained classification via NLI (for intent hints)
    intent = classifier_nli(query, LABELS)["labels"][0]

    # Decision rules (enterprise example):
    # - If policy matches with good confidence -> AUTO_RESOLVE
    if policy and confidence > 0.6:
        return {
            "decision": "AUTO_RESOLVE",
            "category": category,
            "priority": suggested_priority,
            "reason": f"Matched IT policy (confidence {round(confidence,2)})",
            "answer": policy,
            "severity": suggested_priority
        }

    # Security and outage escalations
    if "outage" in intent or "system outage" in intent or "outage" in query.lower():
        return {
            "decision": "ESCALATE",
            "category": "Network",
            "priority": "P1",
            "reason": "Critical system outage detected",
            "answer": None,
            "severity": "P1"
        }

    if "password" in query.lower() or "login" in query.lower():
        return {
            "decision": "AUTO_RESPONSE",
            "category": "Access",
            "priority": "P3",
            "reason": "Password / access guidance provided",
            "answer": "Please try resetting your password via the self-service portal. If that fails, respond to escalate.",
            "severity": "P3"
        }

    if negative:
        return {
            "decision": "ESCALATE",
            "category": category,
            "priority": "P2",
            "reason": "High negative sentiment detected",
            "answer": None,
            "severity": "P2"
        }

    # Default: raise ticket
    return {
        "decision": "RAISE_TICKET",
        "category": category,
        "priority": suggested_priority,
        "reason": "No direct policy match found",
        "answer": None,
        "severity": suggested_priority
    }
