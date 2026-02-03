# infrastructure/secrets/env_secret_provider.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv, dotenv_values


# .envファイルを自動ロード（プロジェクトルートから）
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class EnvSecretProvider:
    """
    環境変数と.envファイルからシークレットを提供する汎用プロバイダ
    
    .envファイルに定義されたすべての変数を読み込み、
    シナリオで ${secrets.変数名} として参照可能にする
    """
    
    def __init__(self):
        # .envファイルから変数を読み込む（環境変数より優先）
        if _env_path.exists():
            self._env_vars = dotenv_values(_env_path)
        else:
            self._env_vars = {}
        
        # 環境変数もマージ（.envファイルの値を優先）
        for key, value in os.environ.items():
            if key not in self._env_vars:
                self._env_vars[key] = value
    
    def get(self) -> Dict[str, Any]:
        """
        すべての環境変数を辞書として返す
        
        Returns:
            環境変数の辞書（キー: 変数名, 値: 変数値）
        """
        return dict(self._env_vars)
