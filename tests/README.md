# WebPost Tests

このディレクトリにはWebPostプロジェクトの単体テストが含まれています。

## テスト構造

```
tests/
├── domain/              # ドメイン層のテスト
│   ├── test_ids.py         # ScenarioId, RunId, ScenarioVersionのテスト
│   ├── test_run.py         # LastResponse, RunContextのテスト
│   ├── test_steps_base.py  # Step, RetryPolicy, OnErrorRuleのテスト
│   └── test_expr.py        # ExpressionEvaluatorのテスト
├── application/         # アプリケーション層のテスト
│   ├── test_outcome.py     # StepOutcomeのテスト
│   ├── test_http_trace.py  # HttpTrace関連クラスのテスト
│   ├── executor/           # エグゼキューター関連のテスト
│   │   ├── test_handler_registry.py  # HandlerRegistryのテスト
│   │   └── test_step_executor.py     # StepExecutorのテスト
│   └── services/           # サービス層のテスト
│       ├── test_redactor.py          # マスキング機能のテスト
│       ├── test_template_renderer.py # テンプレート描画のテスト
│       ├── test_form_composer.py     # フォーム構成のテスト
│       └── test_execution_deps.py    # 実行時依存関係のテスト
└── infrastructure/      # インフラストラクチャ層のテスト（将来追加予定）
```

## テストの実行

### 必要な依存関係のインストール

```bash
pip install -e ".[test]"
```

### すべてのテストを実行

```bash
pytest tests/
```

### 詳細な出力付きで実行

```bash
pytest tests/ -v
```

### カバレッジレポート付きで実行

```bash
pytest tests/ --cov=application --cov=domain --cov=infrastructure --cov-report=term-missing
```

### HTMLカバレッジレポートの生成

```bash
pytest tests/ --cov=application --cov=domain --cov=infrastructure --cov-report=html
# htmlcov/index.html をブラウザで開く
```

### 特定のテストファイルのみ実行

```bash
pytest tests/domain/test_ids.py
```

### 特定のテストクラスのみ実行

```bash
pytest tests/domain/test_ids.py::TestScenarioId
```

### 特定のテストメソッドのみ実行

```bash
pytest tests/domain/test_ids.py::TestScenarioId::test_create_scenario_id
```

## テストカバレッジ

現在のテストカバレッジ:

- **全体**: 48%
- **コアモジュール**: 90-100%
  - handler_registry.py: 100%
  - step_executor.py: 100%
  - execution_deps.py: 100%
  - form_composer.py: 100%
  - redactor.py: 100%
  - template_renderer.py: 90%
  - http_trace.py: 100%
  - outcome.py: 100%
  - すべてのドメイン層モジュール: 100%

## テストの追加

新しいテストを追加する場合:

1. 対応するディレクトリ構造に従ってテストファイルを作成
2. ファイル名は `test_` で始める
3. テストクラスは `Test` で始める
4. テストメソッドは `test_` で始める
5. pytestのアサーションを使用

### テストの例

```python
import pytest
from domain.ids import ScenarioId

class TestScenarioId:
    def test_create_scenario_id(self):
        scenario_id = ScenarioId(value=1)
        assert scenario_id.value == 1
    
    def test_scenario_id_frozen(self):
        scenario_id = ScenarioId(value=1)
        with pytest.raises(Exception):
            scenario_id.value = 2
```

## CI/CD

テストは継続的インテグレーション（CI）パイプラインで自動的に実行されます。
すべてのプルリクエストはテストが合格する必要があります。

## トラブルシューティング

### テストが失敗する場合

```bash
# より詳細な出力でデバッグ
pytest tests/ -vv --tb=long

# 特定のテストのみデバッグ
pytest tests/path/to/test.py -vv --tb=long
```

### インポートエラーが発生する場合

プロジェクトを編集可能モードでインストールしてください:

```bash
pip install -e .
```
