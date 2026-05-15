import json
import chromadb
from chromadb.utils import embedding_functions
import uuid

# Configuration
JSON_FILE = "a.json"
DB_DIR = "./chroma_db"
COLLECTION_NAME = "shl_assessments"

def build_vector_store():
    print(f"Loading data directly from {JSON_FILE}...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            assessments = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {JSON_FILE}. Make sure it is in the same folder as this script!")
        return

    print(f"Successfully loaded {len(assessments)} assessments from JSON.")

    print("Initializing local ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=DB_DIR)
    
    # Using a fast, local embedding model
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Delete the old scraped collection to ensure a clean slate
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
        
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )

    documents = []
    metadatas = []
    ids = []

    for item in assessments:
        # We extract the rich data provided in your JSON
        name = item.get('name', 'Unknown')
        url = item.get('link', '')
        description = item.get('description', '')
        duration = item.get('duration', 'Variable')
        keys_list = item.get('keys', [])
        keys_str = ", ".join(keys_list) if keys_list else "General"
        
        # Create a highly detailed text chunk for the AI to search against
        doc_text = (
            f"Assessment Name: {name}\n"
            f"Test Categories: {keys_str}\n"
            f"Duration: {duration}\n"
            f"Details: {description}"
        )
        documents.append(doc_text)
        
        # Keep structured data for the final JSON recommendation output
        metadatas.append({
            "name": name,
            "url": url,
            "test_type": keys_str
        })
        ids.append(str(uuid.uuid4()))

    print(f"Generating embeddings and saving to ./chroma_db...")
    
    # Batch add to avoid memory limits
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        
    print("JSON Ingestion complete! Your agent now has a flawless brain.")

if __name__ == "__main__":
    build_vector_store()