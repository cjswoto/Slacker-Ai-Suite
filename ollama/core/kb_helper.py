# ollama/core/kb_helper.py

import os
from sentence_transformers import SentenceTransformer
import faiss

from ollama.kb.kb_manager import load_existing_index

class KnowledgeBaseHelper:
    def __init__(self):
        self.kb_index, self.kb_chunks, self.kb_metadata = load_existing_index()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.file_filter = None  # If None = search all, otherwise = list of filenames to allow

    def set_file_filter(self, allowed_filenames):
        """
        allowed_filenames: list of filenames (basename) to allow during KB search.
        """
        if allowed_filenames:
            self.file_filter = set(allowed_filenames)
        else:
            self.file_filter = None

    def search_kb(self, query, top_k=3):
        if not self.kb_index or not self.kb_chunks:
            return [], "Local KB not available."

        if self.file_filter:
            # Filter chunks by allowed filenames
            filtered_indices = [
                idx for idx, meta in enumerate(self.kb_metadata)
                if os.path.basename(meta.get("source", "")) in self.file_filter
            ]
            if not filtered_indices:
                return [], "No matching documents in KB filter."

            filtered_chunks = [self.kb_chunks[i] for i in filtered_indices]
            filtered_embeddings = self._encode_chunks(filtered_chunks)

            # Build a temporary FAISS index over the filtered embeddings
            dim = filtered_embeddings.shape[1]
            temp_index = faiss.IndexFlatL2(dim)
            temp_index.add(filtered_embeddings)
            query_vec = self.embedder.encode([query])

            D, I = temp_index.search(query_vec, min(top_k, len(filtered_chunks)))
            selected_chunks = [filtered_chunks[i] for i in I[0]]
        else:
            # Search entire KB
            query_vec = self.embedder.encode([query])
            D, I = self.kb_index.search(query_vec, min(top_k, len(self.kb_chunks)))
            selected_chunks = [self.kb_chunks[i] for i in I[0]]

        preview = "\n".join([
            f"Chunk {i+1}: {chunk.strip()[:100]}..." for i, chunk in enumerate(selected_chunks)
        ])

        return selected_chunks, f"Retrieved {len(selected_chunks)} KB chunks:\n{preview}"

    def _encode_chunks(self, chunks):
        vectors = self.embedder.encode(chunks, convert_to_numpy=True)
        return vectors
