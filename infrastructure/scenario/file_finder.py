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
        filenames = [
            f"{scenario_id}.yaml",
            f"{scenario_id}.yml",
            f"{scenario_id}.json",
        ]
        
        # Recursively search from the base directory.
        for filename in filenames:
            for file_path in self.base_dir.rglob(filename):
                if file_path.is_file():
                    return file_path
        
        return None
