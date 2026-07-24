from typing import Dict, Any, List
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class AggregationAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Weights for extraction agents
        self.agent_weights = {
            "scispacy": 1.2,
            "biobert": 1.3,
            "regex": 1.1,
            "local_llm": 1.2,
            "spacy": 1.0
        }

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Aggregation Agent merging extraction outputs for session {state.session_id}")
        raw_extractions = state.raw_extractions

        all_mentions: List[EntityMentionModel] = []
        for agent_name, mentions in raw_extractions.items():
            all_mentions.extend(mentions)

        if not all_mentions:
            state.aggregated_entities = []
            return state

        # Step 1: Group by normalized text & type and compute weighted consensus confidence
        merged_groups: Dict[str, List[EntityMentionModel]] = {}
        for mention in all_mentions:
            key = f"{mention.text.lower().strip()}_{mention.type}"
            if key not in merged_groups:
                merged_groups[key] = []
            merged_groups[key].append(mention)

        aggregated: List[EntityMentionModel] = []
        for key, group in merged_groups.items():
            first = group[0]
            sources = list(set([agent for m in group for agent in m.source_agents]))

            base_score = sum(
                m.confidence * self.agent_weights.get(
                    m.source_agents[0] if m.source_agents else "spacy", 1.0
                ) for m in group
            )
            denominator = sum(
                self.agent_weights.get(
                    m.source_agents[0] if m.source_agents else "spacy", 1.0
                ) for m in group
            )
            raw_conf = base_score / denominator if denominator > 0 else 0.8
            multi_agent_bonus = 0.05 * (len(sources) - 1)
            final_conf = min(0.99, round(raw_conf + multi_agent_bonus, 2))

            aggregated.append(EntityMentionModel(
                text=first.text,
                type=first.type,
                start_char=first.start_char,
                end_char=first.end_char,
                confidence=final_conf,
                source_agents=sources
            ))

        # Step 2: Remove sub-entity duplicates within the same type
        aggregated = self._deduplicate_subentities(aggregated)

        # Step 3: Resolve overlapping spans of different types (cross-type overlap resolution)
        aggregated = self._resolve_cross_type_overlaps(aggregated)

        state.aggregated_entities = aggregated
        logger.info(
            f"Aggregation Agent complete. Merged {len(all_mentions)} extractions "
            f"into {len(aggregated)} unique entities."
        )
        return state

    def _deduplicate_subentities(self, entities: List[EntityMentionModel]) -> List[EntityMentionModel]:
        """
        Remove shorter entities whose text is a substring of a longer entity of the same type.
        Also resolves generic vs specific duplicates by checking post-aggregation (e.g. keeps
        'Type 2 Diabetes' and discards generic 'Diabetes Mellitus' or 'Diabetes').
        """
        by_type: Dict[str, List[EntityMentionModel]] = {}
        for e in entities:
            by_type.setdefault(e.type, []).append(e)

        filtered: List[EntityMentionModel] = []
        for etype, group in by_type.items():
            # Sort longest text first
            group_sorted = sorted(group, key=lambda e: len(e.text), reverse=True)
            kept: List[EntityMentionModel] = []
            for candidate in group_sorted:
                candidate_lower = candidate.text.lower().strip()
                # Substring deduplication
                is_redundant = any(
                    candidate_lower in kept_ent.text.lower().strip()
                    and candidate_lower != kept_ent.text.lower().strip()
                    for kept_ent in kept
                )
                if not is_redundant:
                    kept.append(candidate)

            # Post-processing: Remove generic disease terms if a more specific one is present in kept
            final_kept: List[EntityMentionModel] = []
            for e in kept:
                e_lower = e.text.lower().strip()
                if etype == "DISEASE":
                    # Generic diabetes check
                    if "diabetes" in e_lower and not any(x in e_lower for x in ["type", "t2dm", "t1dm", "gestational"]):
                        has_specific_diabetes = any(
                            "diabetes" in k.text.lower() and any(x in k.text.lower() for x in ["type", "t2dm", "t1dm", "gestational"])
                            for k in kept
                        )
                        if has_specific_diabetes:
                            continue  # discard generic 'diabetes' / 'diabetes mellitus'
                    
                    # Generic hypertension check
                    if e_lower == "hypertension":
                        has_specific_htn = any(
                            "essential hypertension" in k.text.lower() or "pulmonary hypertension" in k.text.lower()
                            for k in kept
                        )
                        if has_specific_htn:
                            continue  # discard generic 'hypertension'

                if etype == "DRUG":
                    # Drug typo normalization
                    drug_synonyms = {
                        "salbutmol": "Salbutamol", "salbutamol": "Salbutamol",
                        "omeprazol": "Omeprazole", "omeprazole": "Omeprazole",
                        "azithromicin": "Azithromycin", "azithromycin": "Azithromycin",
                        "metphormin": "Metformin", "metformin": "Metformin",
                        "atrovastatin": "Atorvastatin", "atorvastatin": "Atorvastatin",
                        "amlodpine": "Amlodipine", "amlodipine": "Amlodipine",
                    }
                    if e_lower in drug_synonyms:
                        e.text = drug_synonyms[e_lower]

                final_kept.append(e)

            filtered.extend(final_kept)

        # Re-sort by original character position to preserve document order
        filtered.sort(key=lambda e: e.start_char)
        return filtered

    def _resolve_cross_type_overlaps(self, entities: List[EntityMentionModel]) -> List[EntityMentionModel]:
        """
        Resolves overlapping entities of different types by keeping the one with higher confidence,
        breaking ties by longer span length.
        """
        if not entities:
            return []

        # Sort by start_char ascending
        entities_sorted = sorted(entities, key=lambda x: x.start_char)

        clusters: List[List[EntityMentionModel]] = []
        for ent in entities_sorted:
            placed = False
            for cluster in clusters:
                # Check if this ent overlaps with any ent already in the cluster
                if any(ent.start_char < c_ent.end_char and ent.end_char > c_ent.start_char for c_ent in cluster):
                    cluster.append(ent)
                    placed = True
                    break
            if not placed:
                clusters.append([ent])

        resolved: List[EntityMentionModel] = []
        for cluster in clusters:
            # Sort cluster to find the winner
            # Winner selection: highest confidence first, then longest text length
            cluster.sort(key=lambda x: (x.confidence, x.end_char - x.start_char), reverse=True)
            resolved.append(cluster[0])

        # Re-sort by start_char to preserve original document order
        resolved.sort(key=lambda x: x.start_char)
        return resolved

