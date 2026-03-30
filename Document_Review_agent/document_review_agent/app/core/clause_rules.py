# app/core/clause_rules.py

CLAUSE_RULES = {
    "contract": {
        "Data Protection": {
            "weight": 0.25,
            "threshold": 0.45
        },
        "Termination": {
            "weight": 0.20,
            "threshold": 0.45
        },
        "Liability": {
            "weight": 0.25,
            "threshold": 0.50
        },
        "Confidentiality": {
            "weight": 0.15,
            "threshold": 0.50
        },
        "Dispute Resolution": {
            "weight": 0.15,
            "threshold": 0.50
        }
    }
}


def coverage_symbols_for_results(detailed_results: dict):
    """Return a mapping clause -> symbol (✔, ⚠, ✖) based on status.

    Accepts the `detailed_results` structure produced by risk_engine.calculate_risk.
    """
    mapping = {}
    for clause, info in detailed_results.items():
        status = info.get("status", "Missing")
        if status == "Present":
            mapping[clause] = "✔"
        elif status == "Weak":
            mapping[clause] = "⚠"
        else:
            mapping[clause] = "✖"

    return mapping