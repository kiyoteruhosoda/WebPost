# VS Code Testing Extension の使い方

## セットアップ

VS Codeの設定（`.vscode/settings.json`）で、venv内のPythonインタープリターを使用するように設定済みです：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

## Testing Extensionの使用方法

### 1. テストビューを開く

- サイドバーの **Testing** アイコン（フラスコのアイコン）をクリック
- または `Ctrl+Shift+P` → "Test: Focus on Test Explorer View"

### 2. テストを発見

- Testing ビューの **Refresh Tests** ボタンをクリック
- または `Ctrl+Shift+P` → "Test: Refresh Tests"
- `tests/` ディレクトリ内のすべてのテストファイル（`test_*.py` または `*_test.py`）が自動検出されます

### 3. テストを実行

#### 個別のテスト実行
- Testing ビューでテスト関数の横にある **▶** ボタンをクリック

#### ファイル単位で実行
- テストファイル名の横にある **▶** ボタンをクリック

#### すべてのテスト実行
- Testing ビューの最上部にある **▶▶** ボタンをクリック
- または `Ctrl+Shift+P` → "Test: Run All Tests"

#### エディター内で実行
- テスト関数の上に表示される **▶ Run Test** リンクをクリック

### 4. デバッグモードで実行

- テストの横にある **虫のアイコン** をクリック
- ブレークポイントを設定して詳細なデバッグが可能

### 5. テスト結果の確認

- ✅ 成功: 緑色のチェックマーク
- ❌ 失敗: 赤色のバツマーク
- 🔵 スキップ: 青色の丸
- エラー詳細は各テストをクリックすると表示されます

## pytest の設定

プロジェクトルートに `pytest.ini` または `pyproject.toml` を作成してpytestの動作をカスタマイズできます。

### pytest.ini 例

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### pyproject.toml 例

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"
```

## テストファイルの作成

`tests/` ディレクトリにテストファイルを作成：

```python
# tests/test_example.py
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2

class TestCalculator:
    def test_multiply(self):
        assert 2 * 3 == 6
    
    def test_divide(self):
        assert 10 / 2 == 5
```

## ショートカットキー

- **すべてのテスト実行**: なし（Testing ビューから実行）
- **前回のテストを再実行**: `Ctrl+Shift+P` → "Test: Rerun Last Run"
- **カーソル位置のテスト実行**: `Ctrl+Shift+P` → "Test: Run Test at Cursor"
- **失敗したテストのみ再実行**: `Ctrl+Shift+P` → "Test: Rerun Failed Tests"

## トラブルシューティング

### テストが検出されない場合

1. Python インタープリターが正しく選択されているか確認
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - `.venv/bin/python` を選択

2. pytest がインストールされているか確認
   ```bash
   .venv/bin/python -m pip list | grep pytest
   ```

3. テストファイルの命名規則を確認
   - ファイル名: `test_*.py` または `*_test.py`
   - 関数名: `test_*`
   - クラス名: `Test*`

### テスト実行時にモジュールが見つからない場合

`.vscode/settings.json` の `python.analysis.extraPaths` にプロジェクトルートを追加：

```json
{
  "python.analysis.extraPaths": ["./", "./tests"]
}
```

## 現在のプロジェクト構成

```
/work/project/WebPost/
├── .venv/                    # 仮想環境
│   └── bin/python           # このPythonを使用
├── tests/                    # テストディレクトリ
│   ├── fixtures/            # テスト用フィクスチャ
│   └── mock_http_client.py  # モックHTTPクライアント
├── application/              # アプリケーション層
├── domain/                   # ドメイン層
├── infrastructure/          # インフラ層
└── .vscode/
    └── settings.json        # VS Code設定
```

VS Code Testing Extension は自動的に `.venv/bin/python` を使用してテストを実行します。
