from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from pathlib import Path

class PolicyStore:
    def __init__(self, policy_file="it_policies.txt"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        # Use absolute path if relative path doesn't exist
        if not os.path.exists(policy_file):
            script_dir = Path(__file__).parent
            policy_file = script_dir / policy_file
        self.policies = self._load_policies(policy_file)
        self.embeddings = self.model.encode(self.policies)
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(np.array(self.embeddings))

    def _load_policies(self, path):
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def search(self, query, threshold=0.55):
        q_vec = self.model.encode([query])
        distances, indices = self.index.search(np.array(q_vec), 1)
        score = 1 / (1 + distances[0][0])

        if score >= threshold:
            return self.policies[indices[0][0]], score

        return None, score
