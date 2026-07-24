import os
import sys
import argparse
import uvicorn
from rich import print
from rich.markdown import Markdown

# Add current directory to path so local files can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from graph import build_graph

def run_cli_query(query: str):
    """Run the multi-agent LangGraph workflow end-to-end for a text query, streaming node steps."""
    if not config.GROQ_API_KEY:
        print("\n[bold red]Error: GROQ_API_KEY is not set.[/bold red]")
        print("Please check your .env file and set a valid API key to proceed.\n")
        return
        
    app_graph = build_graph()
    
    initial_state = {
        "query": query,
        "subtasks": [],
        "covered_subtasks": [],
        "pubmed_evidence": [],
        "kb_evidence": [],
        "draft_answer": "",
        "verification_notes": "",
        "verified": None,
        "revision_count": 0,
        "final_report": "",
        "next": ""
    }
    
    print(f"\n[bold blue]Initiating clinical search workflow for:[/bold blue] '{query}'\n")
    
    state_accum = {}
    try:
        # Stream the LangGraph workflow execution to print node names in real time
        for step_event in app_graph.stream(initial_state, config={"recursion_limit": 50}):
            for node_name, state_update in step_event.items():
                print(f"[dim]Running agent node: {node_name}...[/dim]")
                state_accum.update(state_update)
                
        final_report = state_accum.get("final_report")
        if final_report:
            print("\n" + "=" * 80 + "\n")
            print(Markdown(final_report))
            print("\n" + "=" * 80 + "\n")
        else:
            print("[bold red]Workflow finished but failed to generate a final report.[/bold red]")
    except Exception as e:
        print(f"[bold red]Workflow execution failed: {e}[/bold red]")

def run_interactive_loop():
    """Start an interactive command-line loop for medical queries."""
    print("[bold green]Local Multi-Agent Medical Research Assistant[/bold green]")
    print("Type a clinical question below to start research, or type 'exit' to quit.")
    print("=" * 70)
    
    while True:
        try:
            query = input("\nQuery > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                print("[blue]Goodbye![/blue]")
                break
            run_cli_query(query)
        except (KeyboardInterrupt, EOFError):
            print("\n[blue]Goodbye![/blue]")
            break

def main():
    parser = argparse.ArgumentParser(
        description="Local Multi-Agent Medical Research Assistant CLI & Server"
    )
    parser.add_argument(
        "query", 
        nargs="?", 
        type=str, 
        help="Medical research query to synthesize findings for."
    )
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="Run the FastAPI application server."
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="FastAPI server host binding address."
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="FastAPI server port binding number."
    )
    
    # Process inputs
    args = parser.parse_args()
    
    if args.server:
        print(f"[bold green]Starting FastAPI App on http://{args.host}:{args.port}[/bold green]")
        # Start server using uvicorn (running from current dir)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        uvicorn.run("server:app", host=args.host, port=args.port, reload=True)
    elif args.query:
        run_cli_query(args.query)
    else:
        run_interactive_loop()

if __name__ == "__main__":
    main()
