# app/core/similarity_engine.py

from sentence_transformers import util
import re

def split_into_sentences(text):
    # Basic sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def get_best_match(clause_embedding, chunk_embeddings, chunks, embed_function):
    """
    Returns:
    - max similarity score
    - most relevant sentence from best chunk
    """

    # Step 1: Find best chunk
    scores = util.cos_sim(clause_embedding, chunk_embeddings)[0]
    max_index = scores.argmax().item()
    max_score = float(scores[max_index])

    best_chunk = chunks[max_index]

    # Step 2: Split chunk into sentences
    sentences = split_into_sentences(best_chunk)

    if not sentences:
        return max_score, best_chunk[:300]

    # Step 3: Embed sentences
    sentence_embeddings = embed_function(sentences)

    # Step 4: Find best sentence
    sentence_scores = util.cos_sim(clause_embedding, sentence_embeddings)[0]
    best_sentence_index = sentence_scores.argmax().item()
    best_sentence = sentences[best_sentence_index]

    return max_score, best_sentence