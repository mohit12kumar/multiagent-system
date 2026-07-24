import os
import sys
import shutil
from datasets import load_dataset
from langchain_core.documents import Document
from rich.progress import track
from rich import print

# Add parent directory to path so config can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    print("[bold blue]Starting MedQuAD Knowledge Base Ingestion[/bold blue]")
    
    # Ensure idempotency: Clean up old database directory if it exists
    if os.path.exists(config.CHROMA_DIR):
        print(f"[yellow]Cleaning existing vector database at: {config.CHROMA_DIR}...[/yellow]")
        try:
            shutil.rmtree(config.CHROMA_DIR)
            print("[green]Existing database directory cleared successfully.[/green]")
        except Exception as e:
            print(f"[red]Error clearing database directory: {e}[/red]")
            sys.exit(1)
            
    # Load dataset
    print("[blue]Downloading MedQuAD dataset from Hugging Face...[/blue]")
    try:
        # Load train split of keivalya/MedQuad-MedicalQnADataset
        dataset = load_dataset("keivalya/MedQuad-MedicalQnADataset", split="train")
        print(f"[green]Loaded dataset with {len(dataset)} total rows.[/green]")
    except Exception as e:
        print(f"[red]Error loading dataset from Hugging Face: {e}[/red]")
        sys.exit(1)
        
    # Cap at ~3000 rows for reasonable local build time (as per Build Spec)
    limit = 3000
    rows = list(dataset)[:limit]
    print(f"[blue]Processing and embedding first {len(rows)} Q&A pairs...[/blue]")
    
    # Convert to LangChain Documents
    documents = []
    for row in rows:
        q = row.get("Question", "")
        a = row.get("Answer", "")
        qtype = row.get("qtype", "General")
        
        if not q or not a:
            continue
            
        page_content = f"Q: {q.strip()}\nA: {a.strip()}"
        doc = Document(
            page_content=page_content,
            metadata={"source": f"MedQuAD/{qtype}"}
        )
        documents.append(doc)
        
    print(f"[green]Generated {len(documents)} document objects.[/green]")
    
    # Initialize local embeddings and Chroma client
    print(f"[blue]Initializing embedding model: {config.EMBEDDING_MODEL}...[/blue]")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        
        embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        
        db = Chroma(
            persist_directory=config.CHROMA_DIR,
            embedding_function=embeddings,
            collection_name="medical_kb"
        )
    except Exception as e:
        print(f"[red]Error initializing embeddings/Chroma: {e}[/red]")
        sys.exit(1)
        
    # Embed in batches of ~200
    batch_size = 200
    print("[blue]Beginning ingestion in batches of 200...[/blue]")
    
    try:
        for idx in track(range(0, len(documents), batch_size), description="Ingesting to local Chroma DB"):
            batch = documents[idx : idx + batch_size]
            db.add_documents(batch)
        print("[bold green]Success! Knowledge base successfully ingested and persisted.[/bold green]")
    except Exception as e:
        print(f"[red]Error during document ingestion: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
