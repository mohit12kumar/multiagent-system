import sys
import os
from langchain_core.tools import tool

# Add parent directory to path so config can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

_vector_store = None

def get_kb_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store
        
    # Check if the database exists and contains files
    if not os.path.exists(config.CHROMA_DIR) or not os.listdir(config.CHROMA_DIR):
        raise FileNotFoundError("Chroma database directory is empty or does not exist.")
        
    # Import locally to keep startup times fast
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    _vector_store = Chroma(
        persist_directory=config.CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="medical_kb"
    )
    return _vector_store

@tool
def local_medical_kb_search(query: str) -> str:
    """Search the local vector database of medical Q&A pairs for relevant evidence.
    
    Args:
        query: The search term or clinical sub-question to query the knowledge base.
    """
    try:
        store = get_kb_store()
        results = store.similarity_search(query, k=4)
        if not results:
            return "No matching documents found in the local knowledge base."
            
        formatted_docs = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown Source")
            content = doc.page_content
            formatted_docs.append(
                f"[Doc {i}] Source: {source}\nContent:\n{content}"
            )
        return "\n\n---\n\n".join(formatted_docs)
        
    except FileNotFoundError:
        return (
            "Error: The local knowledge base has not been initialized yet. "
            "Please run `python ingest.py` first to download the MedQuAD dataset "
            "and build the vector store."
        )
    except Exception as e:
        return f"Error querying the local knowledge base: {str(e)}"
