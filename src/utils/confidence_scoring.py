from typing import List, Dict, Any

# Default agent weights
AGENT_WEIGHTS = {
    "spacy": 1.0,
    "hf": 1.5,
    "ollama": 1.2,
    "date_time": 2.0
}


def calculate_consensus_score(agent_extractions: List[Dict[str, Any]]) -> float:
    """
    Computes a weighted consensus score based on the source agents that extracted the entity.

    agent_extractions: List of dicts, e.g. [{"agent": "spacy", "confidence": 0.7}, ...]
    """
    if not agent_extractions:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for ext in agent_extractions:
        agent = ext.get("agent")
        conf = ext.get("confidence", 0.5)
        weight = AGENT_WEIGHTS.get(agent, 1.0)

        weighted_sum += conf * weight
        total_weight += weight

    base_score = weighted_sum / total_weight if total_weight > 0 else 0.5

    # Apply a boost for consensus (if multiple agents agree)
    unique_agents = len(set(ext.get("agent") for ext in agent_extractions))
    if unique_agents > 1:
        # Boost confidence for agreement: +10% per additional unique agent, capped at 0.98
        boost = 0.10 * (unique_agents - 1)
        return min(0.98, base_score + boost)

    return min(1.0, base_score)
