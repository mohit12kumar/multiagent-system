import os
import re
import yaml
from src.models.pipeline_state import PipelineState
from src.monitoring.logger import logger, set_log_context


class ValidationAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.fail_on_invalid_taxonomy = self.config.get(
            "fail_on_invalid_taxonomy", False)
        self.min_length = self.config.get("min_length", 2)
        self.strip_punctuation = self.config.get("strip_punctuation", True)

        # Load taxonomy
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        TAXONOMY_PATH = os.path.join(
            BASE_DIR, "config", "entity_taxonomy.yaml")
        self.taxonomy = {}
        self.mapping = {}

        if os.path.exists(TAXONOMY_PATH):
            try:
                with open(TAXONOMY_PATH, "r") as f:
                    tax_yaml = yaml.safe_load(f)
                    self.taxonomy = tax_yaml.get("taxonomy", {})

                    # Create mapping reverse index
                    for target_type, details in self.taxonomy.items():
                        mappings = details.get("mappings", [])
                        for mapping_src in mappings:
                            self.mapping[mapping_src.upper()] = target_type
            except Exception as e:
                logger.error(f"Failed to load entity taxonomy: {e}")

    def process(self, state: PipelineState) -> PipelineState:
        """
        Applies taxonomy mapping and filters entities against configuration rules.
        """
        set_log_context(state.session_id, "validation_agent")
        logger.info("Starting validation and taxonomy mapping")

        validated = []

        for entity in state.aggregated_entities:
            # 1. Clean entity text if required
            text = entity.text
            if self.strip_punctuation:
                # Strip leading/trailing punctuation characters
                text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text).strip()

            if len(text) < self.min_length:
                logger.warning(
                    f"Skipping entity '{entity.text}': length below minimum limit ({self.min_length})")
                continue

            # 2. Map label to canonical taxonomy
            source_type = entity.type.upper()
            mapped_type = self.mapping.get(source_type, source_type)

            # 3. Apply custom validation constraints from taxonomy rules
            tax_rules = self.taxonomy.get(mapped_type)
            if tax_rules:
                val_config = tax_rules.get("validation", {})

                # Check min/max word count limits
                word_count = len(text.split())
                if "min_words" in val_config and word_count < val_config["min_words"]:
                    logger.warning(
                        f"Entity '{text}' failed min_words validation")
                    continue
                if "max_words" in val_config and word_count > val_config["max_words"]:
                    logger.warning(
                        f"Entity '{text}' failed max_words validation")
                    continue

                # Check regex rules
                if "regex" in val_config:
                    regex_str = val_config["regex"]
                    if not re.match(regex_str, text):
                        logger.warning(
                            f"Entity '{text}' failed regex check: {regex_str}")
                        if self.fail_on_invalid_taxonomy:
                            continue
            else:
                # If the type doesn't exist in our taxonomy, decide whether to skip
                if self.fail_on_invalid_taxonomy:
                    logger.warning(
                        f"Entity '{text}' has type '{source_type}' which is not in taxonomy. Skipping.")
                    continue

            # Add to validated lists
            entity.text = text
            entity.type = mapped_type
            validated.append(entity)

        state.validated_entities = validated
        state.current_stage = "DISAMBIGUATION"

        logger.info(
            f"Validation complete. Retained {len(validated)} of {len(state.aggregated_entities)} entities.")
        return state
