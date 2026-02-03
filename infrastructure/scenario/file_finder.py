"""シナリオファイルを探索する"""
from pathlib import Path
from typing import Optional


class ScenarioFileFinder:
    """
    指定されたディレクトリからシナリオファイルを検索する
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def find_by_id(self, scenario_id: str) -> Optional[Path]:
        """
        シナリオIDに対応するファイルを検索
        
        Args:
            scenario_id: シナリオID（例: "fun-navi-reserve"）
        
        Returns:
            見つかったファイルのPath、見つからない場合はNone
        """
        filenames = [
            f"{scenario_id}.yaml",
            f"{scenario_id}.yml",
        ]
        
        # base_dirから再帰的に検索
        for filename in filenames:
            for file_path in self.base_dir.rglob(filename):
                if file_path.is_file():
                    return file_path
        
        return None
