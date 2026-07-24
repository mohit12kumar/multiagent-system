from langgraph.graph import StateGraph, END
from state import ResearchState
from agents.nodes import (
    supervisor_node,
    planner_node,
    pubmed_researcher_node,
    kb_researcher_node,
    synthesizer_node,
    verifier_node,
    reporter_node,
)

def route_from_supervisor(state: ResearchState) -> str:
    """Read the routing decision set by the supervisor node and return the destination name."""
    return state.get("next", "end")

def build_graph():
    """Assemble and compile the multi-agent research supervisor state machine."""
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("pubmed_researcher", pubmed_researcher_node)
    workflow.add_node("kb_researcher", kb_researcher_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("reporter", reporter_node)
    
    # The supervisor acts as the central router and starting point
    workflow.set_entry_point("supervisor")
    
    # Configure conditional edges routing out of the supervisor node
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "planner": "planner",
            "pubmed_researcher": "pubmed_researcher",
            "synthesizer": "synthesizer",
            "verifier": "verifier",
            "reporter": "reporter",
            "end": END,
        }
    )
    
    # All nodes except researchers link back to the supervisor to let it decide next steps
    workflow.add_edge("planner", "supervisor")
    
    # Sequential researcher execution flow: pubmed_researcher -> kb_researcher -> supervisor
    workflow.add_edge("pubmed_researcher", "kb_researcher")
    workflow.add_edge("kb_researcher", "supervisor")
    
    workflow.add_edge("synthesizer", "supervisor")
    workflow.add_edge("verifier", "supervisor")
    workflow.add_edge("reporter", "supervisor")
    
    # Compile the graph
    return workflow.compile()
