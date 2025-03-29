# kb_manager.py
import os
import json
import shutil
import datetime
from local_retriever import build_index_from_folder, save_index, load_index

# Define paths (modify as needed).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_FOLDER = os.path.join(BASE_DIR, "../local_kb")
INDEX_FILE = os.path.join(BASE_DIR, "../faiss_index.index")
METADATA_FILE = os.path.join(BASE_DIR, "../kb_documents.json")

def ensure_kb_folder():
    if not os.path.exists(KB_FOLDER):
        os.makedirs(KB_FOLDER)

def load_document_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_document_metadata(metadata):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

def add_file(file_path):
    """
    Copies the file into the KB folder and updates metadata.
    Returns the metadata for the file.
    """
    ensure_kb_folder()
    filename = os.path.basename(file_path)
    dest_path = os.path.join(KB_FOLDER, filename)
    shutil.copy2(file_path, dest_path)
    metadata = load_document_metadata()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata[dest_path] = {"filename": filename, "last_loaded": timestamp}
    save_document_metadata(metadata)
    return metadata[dest_path]

def remove_file(file_path):
    """
    Removes the file from the KB folder and updates metadata.
    """
    metadata = load_document_metadata()
    if file_path in metadata:
        os.remove(file_path)
        del metadata[file_path]
        save_document_metadata(metadata)
        return True
    return False

def rebuild_index():
    """
    Rebuilds the FAISS index from all .txt files in the KB folder.
    Returns the index, chunks, and metadata.
    """
    ensure_kb_folder()
    index, chunks, meta = build_index_from_folder(KB_FOLDER)
    if index is not None:
        save_index(index, INDEX_FILE)
    return index, chunks, meta

def load_existing_index():
    """
    Loads the FAISS index and returns it along with stored chunks and metadata.
    For production, you might store chunks/metadata persistently as well.
    Here we simply rebuild if no persistent storage for chunks exists.
    """
    if os.path.exists(INDEX_FILE):
        index = load_index(INDEX_FILE)
        # For simplicity, rebuild chunks and metadata from the KB folder.
        _, chunks, meta = build_index_from_folder(KB_FOLDER)
        return index, chunks, meta
    else:
        return rebuild_index()
