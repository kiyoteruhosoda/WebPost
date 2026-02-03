# infrastructure/scenario/loader_registry.py
from __future__ import annotations

from pathlib import Path
from typing import Dict

from infrastructure.scenario.base_loader import ScenarioLoaderBase, ScenarioLoadError
from infrastructure.scenario.json_loader import JsonScenarioLoader
from infrastructure.scenario.yaml_loader import YamlScenarioLoader


class ScenarioLoaderRegistry:
    def __init__(self) -> None:
        self._loaders: Dict[str, ScenarioLoaderBase] = {
            ".yaml": YamlScenarioLoader(),
            ".yml": YamlScenarioLoader(),
            ".json": JsonScenarioLoader(),
        }

    def get_loader(self, path: Path) -> ScenarioLoaderBase:
        ext = path.suffix.lower()
        loader = self._loaders.get(ext)
        if loader is None:
            raise ScenarioLoadError(f"Unsupported scenario format: {ext}")
        return loader
