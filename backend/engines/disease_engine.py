import os
import importlib
import inspect
from typing import Dict, Any, List
from backend.disease_plugins.base_plugin import BaseDiseasePlugin

class DiseaseEngine:
    """Dynamic Disease Engine with automatic plugin discovery and execution."""

    _PLUGINS_CACHE = {}

    @classmethod
    def load_plugins(cls) -> Dict[str, BaseDiseasePlugin]:
        if cls._PLUGINS_CACHE:
            return cls._PLUGINS_CACHE

        plugins_dir = os.path.join(os.path.dirname(__file__), "..", "disease_plugins")
        for file in os.listdir(plugins_dir):
            if file.endswith("_plugin.py") and file != "base_plugin.py":
                module_name = f"backend.disease_plugins.{file[:-3]}"
                try:
                    mod = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(mod, inspect.isclass):
                        if issubclass(obj, BaseDiseasePlugin) and obj is not BaseDiseasePlugin:
                            instance = obj()
                            cls._PLUGINS_CACHE[instance.disease_name.lower()] = instance
                except Exception:
                    pass

        return cls._PLUGINS_CACHE

    @classmethod
    def evaluate_disease(cls, disease_name: str, symptoms: List[str], labs: List[Any], vitals: List[Any]) -> Dict[str, Any]:
        plugins = cls.load_plugins()
        plugin = plugins.get(disease_name.lower())

        if plugin:
            return {
                "name": plugin.disease_name,
                "icd10": plugin.icd10_code,
                "snomed": plugin.snomed_code,
                "severity": plugin.calculate_severity(symptoms, labs, vitals),
                "stage": plugin.calculate_stage(labs, vitals),
                "guidelines": plugin.get_guidelines(),
                "plugin_executed": True
            }

        return {
            "name": disease_name,
            "icd10": "I99.9",
            "snomed": "404684003",
            "severity": "Moderate",
            "stage": "Standard Stage",
            "guidelines": [],
            "plugin_executed": False
        }
