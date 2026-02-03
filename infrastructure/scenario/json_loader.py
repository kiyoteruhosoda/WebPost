# infrastructure/scenario/json_loader.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.scenario.base_loader import ScenarioLoaderBase


class JsonScenarioLoader(ScenarioLoaderBase):
    def _load_file(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
