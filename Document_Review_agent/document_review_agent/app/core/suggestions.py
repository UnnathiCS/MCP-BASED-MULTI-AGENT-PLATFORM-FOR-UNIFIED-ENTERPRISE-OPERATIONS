# app/core/suggestions.py

SUGGESTION_TEMPLATES = {
    "Data Protection": (
        "The Agreement should include a comprehensive Data Protection clause requiring compliance with applicable laws (e.g., GDPR), clear responsibilities for data controllers/processors, encryption and access controls, and mandatory breach notification timelines."
    ),

    "Termination": (
        "Include express termination rights (for convenience and for cause), termination notice periods, and the effect of termination on outstanding obligations (e.g., data return or deletion)."
    ),

    "Liability": (
        "Specify caps on liability, carve-outs for gross negligence and wilful misconduct, indemnification clauses, and required insurance levels where applicable."
    ),

    "Confidentiality": (
        "Define confidential information, permitted disclosures, duration of obligations, and remedies for breach (injunctive relief, damages)."
    ),

    "Dispute Resolution": (
        "Set governing law, jurisdiction, and preferred dispute resolution mechanisms (mediation/arbitration) including seat, rules, and enforcement approach."
    )
}


def generate_suggestions(clause_results):
    """Return enterprise-style suggestions for clauses that are not Present.

    Only generates suggestions when the clause status is not 'Present'.
    """
    suggestions = {}

    for clause, data in clause_results.items():
        if data.get("status") != "Present":
            suggestions[clause] = SUGGESTION_TEMPLATES.get(
                clause,
                "Consider adding a detailed clause covering this subject."
            )

    return suggestions