from typing import List, TypedDict, Optional

class Evidence(TypedDict):
    source: str      # e.g., 'PubMed', 'Local KB'
    citation: str    # e.g., '[PMID 12345] Title (Year)', '[Doc 1] Source: MedQuAD/...'
    text: str        # Abstract or QA pair content

class ResearchState(TypedDict, total=False):
    query: str
    subtasks: List[str]
    covered_subtasks: List[str]
    pubmed_evidence: List[Evidence]
    kb_evidence: List[Evidence]
    draft_answer: str
    verification_notes: str
    verified: Optional[str]      # None | "pending" | "revise" | "pass"
    revision_count: int
    final_report: str
    next: str                    # supervisor's routing decision
