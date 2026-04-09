import os
import glob
import csv
import json
import PyPDF2
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = "knowledge_base/"
DB_PATH = "vector_db_simple"

def parse_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_pdf(file_path):
    content = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content += page.extract_text() or ""
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
    return content

def parse_csv(file_path):
    """Parse CSV using stdlib to avoid heavy dependencies."""
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            return json.dumps(rows, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error parsing CSV {file_path}: {e}")
        return ""

def load_documents():
    """Load all supported files from knowledge_base folder"""
    documents = []
    # TXT
    txt_files = glob.glob(os.path.join(DATA_PATH, "*.txt"))
    for file_path in txt_files:
        try:
            content = parse_txt(file_path)
            documents.append({'content': content, 'source': os.path.basename(file_path)})
            logger.info(f"Loaded TXT: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error loading TXT {file_path}: {e}")
    # PDF
    pdf_files = glob.glob(os.path.join(DATA_PATH, "*.pdf"))
    for file_path in pdf_files:
        try:
            content = parse_pdf(file_path)
            documents.append({'content': content, 'source': os.path.basename(file_path)})
            logger.info(f"Loaded PDF: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
    # CSV
    csv_files = glob.glob(os.path.join(DATA_PATH, "*.csv"))
    for file_path in csv_files:
        try:
            content = parse_csv(file_path)
            documents.append({'content': content, 'source': os.path.basename(file_path)})
            logger.info(f"Loaded CSV: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
    return documents

def split_text(text, chunk_size=500, overlap=50):
    """Simple text splitting function"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence or word boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_space = chunk.rfind(' ')
            if last_period > chunk_size * 0.7:
                end = start + last_period + 1
            elif last_space > chunk_size * 0.7:
                end = start + last_space
        
        chunks.append(text[start:end].strip())
        start = end - overlap
        
        if start >= len(text):
            break
    
    return chunks

def create_vector_db():
    """Create vector database using minimal dependencies"""
    logger.info("Loading documents...")
    documents = load_documents()
    if not documents:
        logger.error("No documents found!")
        return
    logger.info("Splitting documents into chunks...")
    all_chunks = []
    all_metadata = []
    for doc in documents:
        chunks = split_text(doc['content'])
        all_chunks.extend(chunks)
        all_metadata.extend([{'source': doc['source']}] * len(chunks))
    logger.info(f"Created {len(all_chunks)} chunks")
    logger.info("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Creating embeddings...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    logger.info("Creating ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection("nexusflow_docs")
    except:
        pass
    collection = client.create_collection("nexusflow_docs")
    ids = [f"doc_{i}" for i in range(len(all_chunks))]
    collection.add(
        documents=all_chunks,
        embeddings=embeddings.tolist(),
        metadatas=all_metadata,
        ids=ids
    )
    logger.info("✅ Vector database created successfully!")
    return collection

def test_search():
    """Test the database"""
    logger.info("Testing search...")
    
    # Load model and client
    model = SentenceTransformer('all-MiniLM-L6-v2')
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection("nexusflow_docs")
    
    test_queries = [
        "How much does NexusFlow cost?",
        "What is the free trial period?", 
        "How to fix 401 unauthorized error?",
        "What are the core features?"
    ]
    
    for query in test_queries:
        # Create query embedding
        query_embedding = model.encode([query])
        
        # Search
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        
        print(f"\n❓ Query: '{query}'")
        for i, doc in enumerate(results['documents'][0]):
            print(f"📄 Result {i+1}: {doc[:150]}...")

if __name__ == "__main__":
    try:
        try:
            import sentence_transformers
            import chromadb
        except ImportError:
            logger.info("Installing required packages...")
            os.system("pip install sentence-transformers chromadb")
        
        create_vector_db()
        test_search()
        
        print("\n" + "="*50)
        print("🎉 SUCCESS! Vector database created!")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print("Try: pip install sentence-transformers chromadb")