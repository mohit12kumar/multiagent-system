import os
from typing import List
from src.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class BiobertAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.model_name = self.config.get(
            "model_name", "Almannaa/BioBERT-NER-Diseases")
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.75)
        self.supported_entities = self.config.get(
            "supported_entities", ["DISEASE", "DRUG"])
        self.onnx_model_path = self.config.get("onnx_model_path", "")

        # Auto-detect GPU/CUDA device fallback
        import torch
        self.device = 0 if torch.cuda.is_available() else -1
        if "device" in self.config:
            self.device = self.config["device"]

        self.pipeline = None
        self._initialized = False

    def _initialize_pipeline(self) -> None:
        """Loads HuggingFace pipeline. Attempts ONNX Runtime first if config is set."""
        if self._initialized:
            return

        # 1. Attempt to load using ONNX Runtime via Optimum
        if self.onnx_model_path and os.path.exists(self.onnx_model_path):
            try:
                from optimum.onnxruntime import ORTModelForTokenClassification
                from transformers import AutoTokenizer, pipeline

                logger.info(
                    f"Loading CPU-optimized ONNX model from {self.onnx_model_path}")
                model = ORTModelForTokenClassification.from_pretrained(
                    self.onnx_model_path)
                tokenizer = AutoTokenizer.from_pretrained(self.onnx_model_path)

                self.pipeline = pipeline(
                    "ner",
                    model=model,
                    tokenizer=tokenizer,
                    aggregation_strategy="simple",
                    device=self.device
                )
                self._initialized = True
                logger.info(
                    "Successfully loaded ONNX accelerated BioBERT pipeline")
                return
            except ImportError:
                logger.warning(
                    "Optimum ONNX runtime libraries not found. Falling back to PyTorch.")
            except Exception as e:
                logger.warning(
                    f"Failed to load ONNX model: {e}. Falling back to PyTorch.")

        # 2. PyTorch Fallback
        try:
            from transformers import pipeline
            logger.info(
                f"Loading standard PyTorch BioBERT pipeline: {self.model_name}")
            self.pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy="simple",
                device=self.device
            )
            self._initialized = True
            logger.info("Successfully loaded standard BioBERT pipeline")
        except Exception as e:
            logger.error(f"Failed to initialize BioBERT agent pipeline: {e}")
            self.pipeline = None
            self._initialized = False

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Runs clinical NER extraction on sentences.
        """
        self._initialize_pipeline()
        if not self.pipeline:
            logger.error(
                "BioBERT extraction pipeline is unavailable. Skipping.")
            return []

        extractions = []
        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            try:
                results = self.pipeline(sent_text)
                for res in results:
                    score = float(res.get("score", 1.0))
                    if score < self.confidence_threshold:
                        continue

                    label = res.get("entity_group", "")

                    # BioBERT tags mapping
                    ent_label = "DISEASE"
                    label_upper = label.upper()
                    if "CHEMICAL" in label_upper or "DRUG" in label_upper or "MED" in label_upper:
                        ent_label = "DRUG"

                    if ent_label in self.supported_entities:
                        start_char = sent_start + res.get("start", 0)
                        end_char = sent_start + res.get("end", 0)
                        entity_text = res.get("word", "")

                        extractions.append(EntityMentionModel(
                            text=entity_text,
                            type=ent_label,
                            start_char=start_char,
                            end_char=end_char,
                            confidence=score,
                            source_agents=["biobert"]
                        ))
            except Exception as e:
                logger.error(
                    f"BioBERT extraction failed on sentence: {sent_text}. Error: {e}")

        return extractions
