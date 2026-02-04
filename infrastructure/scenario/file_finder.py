"""Find scenario files by ID."""
from pathlib import Path
from typing import Optional


class ScenarioFileFinder:
    """Search scenario files under the given base directory."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def find_by_id(self, scenario_id: str) -> Optional[Path]:
        """
        Find a scenario file by scenario ID.

        Args:
            scenario_id: Scenario ID (e.g., "fun-navi-reserve")

        Returns:
            The Path if found, otherwise None.
        """
        priority = [".json", ".yaml", ".yml"]
        candidates: list[Path] = []

        # Reason: Define deterministic priority when multiple extensions exist.
        # Impact: .json is selected over YAML variants for the same scenario_id.
        for ext in priority:
            filename = f"{scenario_id}{ext}"
            for file_path in self.base_dir.rglob(filename):
                if file_path.is_file():
                    candidates.append(file_path)

        if not candidates:
            return None

        candidates.sort(key=lambda path: (priority.index(path.suffix), str(path)))
        return candidates[0]
