# app/core/risk_engine.py

def calculate_risk(clause_scores, rules, clause_snippets):
    """Calculate risk and also produce a compliance score and coverage map.

    Returns:
        risk_level (str), compliance_index (float), detailed_results (dict),
        compliance_score (float 0-100), coverage (dict clause->symbol)
    """

    detailed_results = {}

    weighted_risk = 0.0
    total_weight = 0.0

    for clause in rules:
        score = clause_scores.get(clause, 0.0)
        weight = rules[clause]["weight"]
        threshold = rules[clause]["threshold"]

        total_weight += weight

        # Determine status with a 'weak' band
        if score >= threshold:
            status = "Present"
            risk_component = 0.0
        else:
            # weak if within 70% of threshold
            if score >= 0.7 * threshold:
                status = "Weak"
                risk_component = weight * 0.5
            else:
                status = "Missing"
                risk_component = weight

        weighted_risk += risk_component

        detailed_results[clause] = {
            "similarity_score": round(score, 3),
            "status": status,
            "weight": weight,
            "snippet": clause_snippets.get(clause, "No relevant content found.")
        }

    # Raw risk ratio
    raw_risk_score = weighted_risk / total_weight if total_weight else 0.0

    # Residual floor so systems never report 0 risk
    residual_floor = 0.02
    adjusted_risk_score = max(raw_risk_score, residual_floor)

    # Risk Level Bands
    if adjusted_risk_score <= 0.25:
        risk_level = "Low"
    elif adjusted_risk_score <= 0.50:
        risk_level = "Moderate"
    elif adjusted_risk_score <= 0.75:
        risk_level = "High"
    else:
        risk_level = "Critical"

    # Compliance Index (inverse, 0.0-1.0)
    compliance_index = round(1 - adjusted_risk_score, 2)

    # Compliance score as percentage of required clause weight present
    present_weight = 0.0
    for clause, info in detailed_results.items():
        if info["status"] == "Present":
            present_weight += info["weight"]
        elif info["status"] == "Weak":
            present_weight += info["weight"] * 0.5

    compliance_score = round((present_weight / total_weight) * 100, 2) if total_weight else 0.0

    # Coverage symbols
    from app.core.clause_rules import coverage_symbols_for_results

    coverage = coverage_symbols_for_results(detailed_results)

    return risk_level, compliance_index, detailed_results, compliance_score, coverage