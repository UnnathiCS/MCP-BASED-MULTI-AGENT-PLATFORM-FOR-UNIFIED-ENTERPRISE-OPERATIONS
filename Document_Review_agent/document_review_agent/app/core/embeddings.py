from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text_list):
    return model.encode(text_list, convert_to_tensor=True)
