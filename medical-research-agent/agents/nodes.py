import os
import sys
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

# Add parent directory to path so config and state can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from state import ResearchState, Evidence
from tools.pubmed_tool import pubmed_search
from tools.kb_tool import local_medical_kb_search

# Pydantic schemas for LLM structured outputs
class PlannerOutput(BaseModel):
    subtasks: List[str] = Field(
        description="A list of 2 to 4 concrete sub-questions to address the user's research query."
    )

class VerifierOutput(BaseModel):
    status: str = Field(
        description="The status of fact-checking. Must be either 'pass' or 'revise'."
    )
    notes: str = Field(
        description="Detailed verification feedback. Explain unsupported claims, missing citations, or inaccuracies if status is 'revise'. State reasons if passing."
    )


# 1. Supervisor Node (Deterministic, rule-based)
def supervisor_node(state: ResearchState) -> ResearchState:
    """Read the state and make a routing decision.
    
    This is rule-based and deterministic to avoid routing issues.
    """
    subtasks = state.get("subtasks", [])
    covered = state.get("covered_subtasks", [])
    draft_answer = state.get("draft_answer")
    verified = state.get("verified")
    final_report = state.get("final_report")
    
    # Exact routing logic matching the Build Spec
    if not subtasks:
        next_node = "planner"
    elif len(covered) < len(subtasks):
        next_node = "pubmed_researcher"
    elif not draft_answer or verified == "revise":
        next_node = "synthesizer"
    elif verified is None or verified == "pending":
        next_node = "verifier"
    elif verified == "pass" and not final_report:
        next_node = "reporter"
    else:
        next_node = "end"
        
    return {"next": next_node}


# 2. Planner Node (LLM splits main query)
def planner_node(state: ResearchState) -> ResearchState:
    """Split the user's query into 2 to 4 concrete research subtasks."""
    query = state.get("query", "")
    
    system_prompt = (
        "You are an expert medical research planner.\n"
        "Your task is to split the user's medical research question into 2 to 4 concrete, distinct sub-questions.\n"
        "These sub-questions will be queried against PubMed and local clinical Q&A databases.\n"
        "Return the output as a JSON list of strings matching the required schema."
    )
    
    llm = ChatGroq(model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY, temperature=0.1)
    structured_llm = llm.with_structured_output(PlannerOutput)
    
    response = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Main Medical Query: {query}"}
    ])
    
    return {
        "subtasks": response.subtasks,
        "covered_subtasks": [],
        "pubmed_evidence": [],
        "kb_evidence": [],
        "revision_count": 0
    }


# 3. PubMed Researcher Node
def pubmed_researcher_node(state: ResearchState) -> ResearchState:
    """Call pubmed_search once per uncovered subtask and append evidence."""
    subtasks = state.get("subtasks", [])
    covered = state.get("covered_subtasks", [])
    uncovered = [s for s in subtasks if s not in covered]
    pubmed_evidence = list(state.get("pubmed_evidence", []))
    
    for subtask in uncovered:
        try:
            # Execute pubmed_search tool
            res_str = pubmed_search.invoke(subtask)
        except Exception as e:
            res_str = f"Error: {e}"
            
        if not res_str or "No PubMed results found" in res_str or res_str.startswith("Error"):
            continue
            
        # Parse output formatted as: [PMID ...] Title (Year)\nURL: ...\nAbstract: ...
        articles = res_str.split("\n\n---\n\n")
        for article in articles:
            if not article.strip():
                continue
            lines = article.strip().split("\n")
            citation = lines[0] if len(lines) > 0 else "PubMed Document"
            url = ""
            abstract_lines = []
            
            for line in lines[1:]:
                if line.startswith("URL:"):
                    url = line.replace("URL:", "").strip()
                elif line.startswith("Abstract:"):
                    abstract_lines.append(line.replace("Abstract:", "").strip())
                else:
                    abstract_lines.append(line.strip())
            
            abstract = " ".join(abstract_lines).strip()
            
            pubmed_evidence.append({
                "source": "PubMed",
                "citation": f"{citation} (URL: {url})" if url else citation,
                "text": abstract
            })
            
    return {"pubmed_evidence": pubmed_evidence}


# 4. Local KB Researcher Node
def kb_researcher_node(state: ResearchState) -> ResearchState:
    """Call local_medical_kb_search once per subtask, append evidence, and mark covered."""
    subtasks = state.get("subtasks", [])
    covered = list(state.get("covered_subtasks", []))
    uncovered = [s for s in subtasks if s not in covered]
    kb_evidence = list(state.get("kb_evidence", []))
    
    for subtask in uncovered:
        try:
            # Execute local_medical_kb_search tool
            res_str = local_medical_kb_search.invoke(subtask)
        except Exception as e:
            res_str = f"Error: {e}"
            
        if not res_str or "No matching documents" in res_str or "has not been initialized" in res_str or res_str.startswith("Error"):
            continue
            
        # Parse output formatted as: [Doc i] Source: MedQuAD/...\nContent:\n...
        docs = res_str.split("\n\n---\n\n")
        for doc in docs:
            if not doc.strip():
                continue
            lines = doc.strip().split("\n")
            citation = lines[0] if len(lines) > 0 else "Local KB Document"
            content_lines = []
            
            for line in lines[1:]:
                if line.startswith("Content:"):
                    continue
                content_lines.append(line)
                
            content = "\n".join(content_lines).strip()
            
            kb_evidence.append({
                "source": "Local KB",
                "citation": citation,
                "text": content
            })
            
    # Mark all currently researched subtasks as covered
    new_covered = list(set(covered + uncovered))
    return {
        "kb_evidence": kb_evidence,
        "covered_subtasks": new_covered
    }


# 5. Synthesizer Node
def synthesizer_node(state: ResearchState) -> ResearchState:
    """Merge all collected evidence into a single cited draft answer."""
    query = state.get("query", "")
    pubmed_ev = state.get("pubmed_evidence", [])
    kb_ev = state.get("kb_evidence", [])
    verified = state.get("verified")
    notes = state.get("verification_notes", "")
    prev_draft = state.get("draft_answer", "")
    
    # Construct structured text representation of the evidence
    evidence_str = ""
    evidence_str += "=== PubMed Literature Evidence ===\n"
    for i, ev in enumerate(pubmed_ev, 1):
        evidence_str += f"ID: [PubMed-{i}]\nCitation: {ev['citation']}\nText: {ev['text']}\n\n"
        
    evidence_str += "=== Local Knowledge Base Evidence ===\n"
    for i, ev in enumerate(kb_ev, 1):
        evidence_str += f"ID: [KB-{i}]\nSource: {ev['citation']}\nText: {ev['text']}\n\n"
        
    system_prompt = (
        "You are an expert medical science synthesizer.\n"
        "Your task is to merge the collected clinical evidence to answer the main medical query.\n\n"
        "STRICT REQUIREMENTS:\n"
        "1. GROUNDEDNESS: State ONLY facts directly supported by the provided evidence. Do NOT extrapolate or guess.\n"
        "2. INLINE CITATION: Always cite claims inline using their identifiers, e.g. [PubMed-1] or [KB-2]. Do not combine or invent citations.\n"
        "3. FORMAT: Write in a clear, professional style using headings and bullet points. Omit conversational filler.\n"
        "4. MEDICAL DISCLAIMER: Do NOT offer diagnosis or diagnostic guides. Synthesize scientific literature strictly."
    )
    
    user_prompt = f"Main Question: {query}\n\nEvidence Provided:\n{evidence_str}\n"
    
    # Handle revision request if verifier rejected the previous draft
    if verified == "revise" and prev_draft:
        user_prompt += (
            f"\n--- REVISION NEEDED ---\n"
            f"The previous draft was rejected by the verifier with the following feedback:\n"
            f"\"{notes}\"\n\n"
            f"Previous Draft Answer:\n{prev_draft}\n\n"
            f"Please write a revised draft answer correcting the mentioned issues. Ensure every statement remains 100% grounded."
        )
        
    llm = ChatGroq(model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY, temperature=0.1)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    return {
        "draft_answer": response.content.strip(),
        "verified": "pending"  # Sets verified back to pending to trigger a recheck
    }


# 6. Verifier Node
def verifier_node(state: ResearchState) -> ResearchState:
    """Fact-check the draft against evidence, enforcing a maximum of 2 revisions before failing open."""
    query = state.get("query", "")
    draft = state.get("draft_answer", "")
    pubmed_ev = state.get("pubmed_evidence", [])
    kb_ev = state.get("kb_evidence", [])
    revision_count = state.get("revision_count", 0)
    
    # Fail-open safety check: limit revision cycles to 2 to prevent infinite loops
    if revision_count >= 2:
        return {
            "verified": "pass",
            "verification_notes": f"Verification failed (max revision cycles [2] reached, failing open). Previous notes: {state.get('verification_notes')}"
        }
        
    # Format evidence
    evidence_str = ""
    evidence_str += "=== PubMed Evidence ===\n"
    for i, ev in enumerate(pubmed_ev, 1):
        evidence_str += f"ID: [PubMed-{i}]\nText: {ev['text']}\n\n"
    evidence_str += "=== Local KB Evidence ===\n"
    for i, ev in enumerate(kb_ev, 1):
        evidence_str += f"ID: [KB-{i}]\nText: {ev['text']}\n\n"
        
    system_prompt = (
        "You are a clinical verification agent. Your job is to verify if the draft answer is fully "
        "supported by the evidence. Check for:\n"
        "1. Hallucinations or unsupported medical assertions.\n"
        "2. Proper inline citation format referencing the evidence ID (e.g. [PubMed-1] or [KB-2]).\n\n"
        "If everything matches perfectly, return status 'pass'.\n"
        "If there are errors, unsupported claims, or formatting bugs, return status 'revise' and explain them in the notes.\n"
        "Output structured JSON matching the schema."
    )
    
    user_prompt = (
        f"Main Query: {query}\n\n"
        f"Collected Evidence:\n{evidence_str}\n"
        f"Draft Answer:\n{draft}\n"
    )
    
    try:
        llm = ChatGroq(model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY, temperature=0)
        structured_llm = llm.with_structured_output(VerifierOutput)
        response = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        status = response.status.strip().lower()
        notes = response.notes
    except Exception as e:
        status = "pass"
        notes = f"Verification bypassed due to LLM exception: {str(e)}"
        
    if status == "revise":
        return {
            "verified": "revise",
            "verification_notes": notes,
            "revision_count": revision_count + 1
        }
    else:
        return {
            "verified": "pass",
            "verification_notes": notes
        }


# 7. Reporter Node
def reporter_node(state: ResearchState) -> ResearchState:
    """Format final markdown report with findings, citation index, and mandatory disclaimer."""
    draft = state.get("draft_answer", "")
    pubmed_ev = state.get("pubmed_evidence", [])
    
    # Build unique bibliography citations list
    citations = set()
    for ev in pubmed_ev:
        if ev.get("citation"):
            citations.add(ev["citation"])
    citations_list = sorted(list(citations))
    
    # Format standard report template
    report = []
    report.append("# Medical Research Assistant - Report")
    report.append(f"**Query:** {state.get('query', '')}\n")
    report.append("## Findings & Synthesis")
    report.append(draft)
    report.append("\n## Scientific References (NCBI PubMed)")
    
    if citations_list:
        for idx, citation in enumerate(citations_list, 1):
            report.append(f"{idx}. {citation}")
    else:
        report.append("*No literature citations found in PubMed database.*")
        
    report.append("\n" + "=" * 40)
    report.append(config.MEDICAL_DISCLAIMER)
    
    return {"final_report": "\n".join(report)}
