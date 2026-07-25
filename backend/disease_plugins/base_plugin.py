from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseDiseasePlugin(ABC):
    """Abstract Base Class for Dynamic Disease Plugins."""

    @property
    @abstractmethod
    def disease_name(self) -> str:
        pass

    @property
    @abstractmethod
    def icd10_code(self) -> str:
        pass

    @property
    @abstractmethod
    def snomed_code(self) -> str:
        pass

    @abstractmethod
    def calculate_severity(self, symptoms: List[str], labs: List[Any], vitals: List[Any]) -> str:
        pass

    @abstractmethod
    def calculate_stage(self, labs: List[Any], vitals: List[Any]) -> str:
        pass

    @abstractmethod
    def get_guidelines(self) -> List[Dict[str, Any]]:
        pass
