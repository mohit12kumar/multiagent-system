from typing import List
from src.models.entity import EntityMentionModel
from src.models.pipeline_state import PipelineState
from src.utils.confidence_scoring import calculate_consensus_score
from src.monitoring.logger import logger, set_log_context


class AggregationAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.consensus_threshold = self.config.get("consensus_threshold", 0.60)
        self.weights = self.config.get(
            "weights", {"spacy": 1.0, "hf": 1.5, "ollama": 1.2, "date_time": 2.0})

    def process(self, state: PipelineState) -> PipelineState:
        """
        Gathers all raw extractions, performs span clustering,
        resolves overlaps, and computes consensus confidence scores.
        """
        set_log_context(state.session_id, "aggregation_agent")
        logger.info("Starting aggregation and conflict resolution")

        # 1. Flatten all raw extractions into a single list
        all_mentions: List[EntityMentionModel] = []
        for agent_name, mentions in state.raw_extractions.items():
            for m in mentions:
                all_mentions.append(m)

        if not all_mentions:
            logger.info(
                "No entities extracted from any agent. Skipping aggregation.")
            state.aggregated_entities = []
            state.current_stage = "VALIDATION"
            return state

        # Sort mentions by start offset
        all_mentions.sort(key=lambda x: x.start_char)

        # 2. Group mentions into overlapping clusters
        clusters: List[List[EntityMentionModel]] = []
        for mention in all_mentions:
            placed = False
            for cluster in clusters:
                # Check if this mention overlaps with any mention already in the cluster
                # Overlap condition: start1 < end2 and end1 > start2
                if any(mention.start_char < c_m.end_char and mention.end_char > c_m.start_char for c_m in cluster):
                    cluster.append(mention)
                    placed = True
                    break
            if not placed:
                clusters.append([mention])

        # 3. Resolve overlaps inside each cluster
        resolved_entities: List[EntityMentionModel] = []
        for cluster in clusters:
            # We select a 'winner' mention representing the cluster span
            # To pick: highest confidence * agent weight, then longest span length
            def scoring_key(m: EntityMentionModel):
                agent = m.source_agents[0] if m.source_agents else "spacy"
                weight = self.weights.get(agent, 1.0)
                score = m.confidence * weight
                length = m.end_char - m.start_char
                return (score, length)

            cluster.sort(key=scoring_key, reverse=True)
            winner = cluster[0]  # Highest scoring mention

            # Combine all source agents that contributed to this cluster
            all_sources = set()
            extractions_info = []
            for m in cluster:
                for src in m.source_agents:
                    all_sources.add(src)
                extractions_info.append({
                    "agent": m.source_agents[0] if m.source_agents else "spacy",
                    "confidence": m.confidence
                })

            # Compute consensus confidence
            consensus_conf = calculate_consensus_score(extractions_info)

            # Add resolved entity
            resolved_entities.append(EntityMentionModel(
                text=winner.text,
                type=winner.type,
                start_char=winner.start_char,
                end_char=winner.end_char,
                confidence=consensus_conf,
                source_agents=list(all_sources)
            ))

        # Sort resolved entities back by character offsets
        resolved_entities.sort(key=lambda x: x.start_char)

        # 4. Medication Regimen Grouping
        # Merge close DRUG, DOSAGE, FREQUENCY into one MEDICATION entity.
        final_entities = []
        i = 0
        while i < len(resolved_entities):
            ent = resolved_entities[i]
            if ent.type in ["DRUG", "DOSAGE", "FREQUENCY"]:
                regimen_ents = [ent]
                j = i + 1
                while j < len(resolved_entities):
                    next_ent = resolved_entities[j]
                    if next_ent.type in ["DRUG", "DOSAGE", "FREQUENCY"] and (next_ent.start_char - regimen_ents[-1].end_char) < 40:
                        regimen_ents.append(next_ent)
                        j += 1
                    else:
                        break

                if len(regimen_ents) > 1 and any(e.type == "DRUG" for e in regimen_ents):
                    merged_text = " ".join([e.text for e in regimen_ents])
                    merged_start = regimen_ents[0].start_char
                    merged_end = regimen_ents[-1].end_char
                    merged_conf = sum(
                        e.confidence for e in regimen_ents) / len(regimen_ents)
                    merged_sources = list(
                        set([src for e in regimen_ents for src in e.source_agents]))

                    final_entities.append(EntityMentionModel(
                        text=merged_text,
                        type="DRUG",
                        start_char=merged_start,
                        end_char=merged_end,
                        confidence=merged_conf,
                        source_agents=merged_sources
                    ))
                    i = j
                else:
                    if len(regimen_ents) == 1:
                        final_entities.append(ent)
                        i += 1
                    else:
                        for e in regimen_ents:
                            final_entities.append(e)
                        i = j
            else:
                final_entities.append(ent)
                i += 1

        state.aggregated_entities = final_entities
        state.current_stage = "VALIDATION"

        logger.info(
            f"Aggregation complete. Merged {len(all_mentions)} extractions down to {len(final_entities)} entities.")
        return state
