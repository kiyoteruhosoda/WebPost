# domain/steps/result.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from domain.steps.base import Step


@dataclass(frozen=True)
class ResultStep(Step):
    """
    実行結果を保存するステップ。
    fields内のテンプレートを展開してRunの最終結果として保存する。
    
    例:
    {
      "id": "result",
      "type": "result",
      "fields": {
        "reservationNo": "${vars.reservationNo}"
      }
    }
    """
    fields: Dict[str, str]
