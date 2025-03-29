# local_retriever.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def build_index_from_folder(kb_path, chunk_size=100, overlap=20, model_name="all-MiniLM-L6-v2"):
    """
    Reads all .txt files in kb_path, chunks their text, creates embeddings,
    and builds a FAISS index along with lists for chunks and metadata.

    :param kb_path: Folder containing text files.
    :param chunk_size: Number of words per chunk.
    :param overlap: Number of overlapping words between chunks.
    :param model_name: Name of the SentenceTransformer model.
    :return: index (FAISS index), chunks (list of text chunks), metadata (list of dicts)
    """
    model = SentenceTransformer(model_name)
    chunks = []
    metadata = []

    # Process each .txt file in the folder.
    for filename in os.listdir(kb_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(kb_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            words = text.split()
            start = 0
            chunk_index = 0
            while start < len(words):
                chunk = " ".join(words[start: start + chunk_size])
                chunks.append(chunk)
                metadata.append({"filename": filename, "chunk_index": chunk_index})
                start += chunk_size - overlap
                chunk_index += 1

    if not chunks:
        # No text found.
        return None, [], []

    # Compute embeddings for all chunks.
    embeddings = model.encode(chunks, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, chunks, metadata


def save_index(index, index_file_path):
    """
    Saves the FAISS index to disk.
    """
    faiss.write_index(index, index_file_path)


def load_index(index_file_path):
    """
    Loads the FAISS index from disk.
    """
    if os.path.exists(index_file_path):
        return faiss.read_index(index_file_path)
    return None


def search_index(query, index, chunks, metadata, top_k=3, model_name="all-MiniLM-L6-v2"):
    """
    Searches the FAISS index for the most relevant chunks given a query.

    :param query: The query string.
    :param index: The FAISS index.
    :param chunks: List of text chunks.
    :param metadata: List of metadata corresponding to each chunk.
    :param top_k: Number of top results to return.
    :param model_name: SentenceTransformer model name.
    :return: List of tuples (chunk, distance, metadata)
    """
    model = SentenceTransformer(model_name)
    query_emb = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_emb, top_k)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        results.append((chunks[idx], dist, metadata[idx]))
    return results
