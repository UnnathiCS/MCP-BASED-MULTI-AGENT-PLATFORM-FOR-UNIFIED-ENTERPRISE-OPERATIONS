# app/core/explainer.py

def generate_explanation(doc_type, risk_level, clause_results):

    return (
        f"This document is classified as a {doc_type}. "
        f"The overall compliance posture is assessed as {risk_level}. "
        f"Clause evaluation has been conducted based on predefined governance standards."
    )