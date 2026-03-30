# app/services/review_service.py

from app.core.document_loader import extract_text_from_pdf
from app.core.text_chunker import chunk_text
from app.core.embeddings import embed_text
from app.core.similarity_engine import get_best_match
from app.core.classifier import classify_document
from app.core.clause_rules import CLAUSE_RULES
from app.core.risk_engine import calculate_risk
from app.core.explainer import generate_explanation
from app.core.suggestions import generate_suggestions
import requests


async def review_document(file):

    # 1️⃣ Extract text
    text = extract_text_from_pdf(file)

    if not text.strip():
        return {
            "error": "Unable to extract text from document."
        }

    # 2️⃣ Chunk document
    chunks = chunk_text(text)

    # 3️⃣ Generate embeddings
    chunk_embeddings = embed_text(chunks)
    doc_embedding = embed_text([text])[0]

    # 4️⃣ Classify document type
    doc_type = classify_document(doc_embedding, embed_text)

    if doc_type not in CLAUSE_RULES:
        return {
            "document_type": doc_type,
            "message": "No clause rules defined for this document type."
        }

    rules = CLAUSE_RULES[doc_type]

    clause_scores = {}
    clause_snippets = {}

    # 5️⃣ Clause detection
    for clause in rules:
        # embed the clause label/description and find best matching sentence
        clause_embedding = embed_text([clause])[0]

        similarity, best_sentence = get_best_match(
            clause_embedding,
            chunk_embeddings,
            chunks,
            embed_text
        )

        clause_scores[clause] = float(similarity)
        clause_snippets[clause] = best_sentence

    # 6️⃣ Risk calculation (NEW STRUCTURE)
    risk_level, compliance_index, detailed_results, compliance_score, coverage = calculate_risk(
        clause_scores,
        rules,
        clause_snippets
    )

    # NOTE: Collaboration call moved to just before the return (best-effort trigger).

    # 7️⃣ Explanation generation
    explanation = generate_explanation(
        doc_type,
        risk_level,
        detailed_results
    )

    suggestions = generate_suggestions(detailed_results)

    # Agent collaboration: trigger support ticket if high risk
    support_ticket = None
    try:
        if risk_level == "High":
            print("High risk detected → Creating support ticket")
            response = requests.post(
                "http://127.0.0.1:8000/it-support/text",
                json={
                    "ticket_id": "AUTO-RISK",
                    "message": "High risk contract detected. Security review required."
                },
                timeout=5
            )

            # Return the support agent JSON response (best-effort)
            try:
                support_ticket = response.json()
            except Exception:
                support_ticket = {"status": response.status_code, "detail": "Non-JSON response from support agent"}

    except Exception as e:
        print("Support agent call failed:", e)

    return {
        "document_type": doc_type,
        "risk_level": risk_level,
        "compliance_index": compliance_index,
        "compliance_score": compliance_score,
        "coverage": coverage,
        "clause_analysis": detailed_results,
        "explanation": explanation,
        "suggestions": suggestions,
        "support_ticket": support_ticket
    }