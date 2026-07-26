from typing import List, Dict, Any
from backend.models.pipeline_state import PipelineState


class Router:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def route(self, state: PipelineState) -> List[str]:
        """Routes text to active extraction agents."""
        return ["scispacy", "biobert", "regex", "local_llm"]
