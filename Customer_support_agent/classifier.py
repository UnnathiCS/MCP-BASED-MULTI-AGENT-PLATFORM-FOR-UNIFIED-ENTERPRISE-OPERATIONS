"""
Simple keyword-based ticket classifier for the Customer Support Agent.

This is intentionally lightweight and rule-based for the demo/academic
use-case. It returns a category string and a suggested default priority
level which the agent can override based on context.
"""

KEYWORDS = {
    "Network": ["vpn", "network", "latency", "connectivity", "outage"],
    "Email": ["email", "outlook", "smtp", "imap", "sendmail"],
    "Access": ["password", "login", "authenticate", "token", "access"],
    "Hardware": ["printer", "laptop", "cpu", "disk", "hardware", "battery"],
    "Security": ["breach", "malware", "virus", "security", "ransomware", "phishing"],
    "General": [""]
}


def classify_ticket(text: str):
    """Return (category, suggested_priority).

    Suggested priority is P1..P4 where P1 is highest.
    This function is intentionally simple — it looks for keyword hits.
    """

    text_lower = text.lower()

    for category, words in KEYWORDS.items():
        for w in words:
            if w and w in text_lower:
                # Map category to a default priority
                if category == "Security":
                    return category, "P1"
                if category == "Network":
                    # outages escalate
                    if "outage" in text_lower or "down" in text_lower:
                        return category, "P1"
                    return category, "P2"
                if category == "Access":
                    return category, "P3"
                if category == "Hardware":
                    return category, "P3"
                if category == "Email":
                    return category, "P3"

    return "General", "P4"
