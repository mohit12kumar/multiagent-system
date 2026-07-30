"""
backend/core/agent_registry.py

Dynamic Agent Registry.
Manages registered NLP and clinical agents with runtime enable/disable flags, priority weights,
and feature flag toggling.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AgentMetadata:
    def __init__(self, name: str, agent_obj: Any, priority: int = 10, enabled: bool = True):
        self.name = name
        self.agent_obj = agent_obj
        self.priority = priority
        self.enabled = enabled

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}

    def register(self, name: str, agent_obj: Any, priority: int = 10, enabled: bool = True):
        self._agents[name] = AgentMetadata(name, agent_obj, priority, enabled)
        logger.info(f"[AgentRegistry] Registered agent '{name}' (priority={priority}, enabled={enabled})")

    def enable(self, name: str):
        if name in self._agents:
            self._agents[name].enabled = True

    def disable(self, name: str):
        if name in self._agents:
            self._agents[name].enabled = False

    def get_active_agents(self) -> List[AgentMetadata]:
        active = [meta for meta in self._agents.values() if meta.enabled]
        active.sort(key=lambda x: x.priority, reverse=True)
        return active

    def get_agent(self, name: str) -> Optional[Any]:
        meta = self._agents.get(name)
        return meta.agent_obj if meta else None

agent_registry = AgentRegistry()
