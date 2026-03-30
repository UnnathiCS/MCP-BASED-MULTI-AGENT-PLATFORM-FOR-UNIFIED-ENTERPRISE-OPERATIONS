from sentence_transformers import util

DOCUMENT_TYPE_TEMPLATES = {
    "contract": "This is a legally binding service agreement between two parties defining obligations, liabilities, termination, and dispute resolution.",
    "policy": "This document defines governance, compliance framework, internal procedures, authority and risk management.",
    "nda": "This agreement protects confidential information exchanged between parties and defines breach handling."
}

def classify_document(doc_embedding, embed_function):
    best_type = None
    best_score = 0
    
    for doc_type, template in DOCUMENT_TYPE_TEMPLATES.items():
        template_emb = embed_function([template])
        score = float(util.cos_sim(doc_embedding, template_emb))
        if score > best_score:
            best_score = score
            best_type = doc_type
            
    return best_type
