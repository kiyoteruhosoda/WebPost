# REST API 実装

## エンドポイント

### ヘルスチェック
```bash
GET /
```

レスポンス:
```json
{
  "status": "ok",
  "service": "webpost"
}
```

### シナリオ実行
```bash
POST /scenarios/{scenario_id}/runs
```

リクエストボディ:
```json
{
  "vars": {
    "dates": ["", "2026/02/02", "2026/04/13"]
  },
  "secrets": {
    "username": "test_user",
    "password": "test_pass"
  }
}
```

レスポンス（成功時）:
```json
{
  "success": true,
  "result": {
    "reservationNo": "00003217694"
  }
}
```

レスポンス（失敗時）:
```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

## 使い方

### サーバー起動

```bash
python scripts/run_api.py
```

サーバーは `http://0.0.0.0:8000` で起動します。

### curl での実行例

```bash
# ヘルスチェック
curl http://localhost:8000/

# シナリオ実行
curl -X POST http://localhost:8000/scenarios/fun_navi_reserve/runs \
  -H "Content-Type: application/json" \
  -d '{
    "vars": {"dates": ["", "2026/02/02", "2026/04/13"]},
    "secrets": {"username": "test_user", "password": "test_pass"}
  }'
```

## シナリオファイル検索

- `scenarios/` ディレクトリ内を再帰的に検索
- ファイル名: `{scenario_id}.yaml` または `{scenario_id}.yml`
- 例: `fun_navi_reserve` → `scenarios/fun_navi_reserve.yaml` または `scenarios/subdir/fun_navi_reserve.yml`

## 実装詳細

### ファイル構成

- [api/main.py](../api/main.py) - FastAPI アプリケーション
- [infrastructure/scenario/file_finder.py](../infrastructure/scenario/file_finder.py) - シナリオファイル検索
- [scripts/run_api.py](../scripts/run_api.py) - サーバー起動スクリプト

### 主要機能

1. **シナリオファイル検索**: `ScenarioFileFinder` がscenariosディレクトリを再帰的に検索
2. **YAMLロード**: `YamlScenarioLoader` でシナリオをロード
3. **実行環境構築**: リクエストから `vars` と `secrets` を受け取り、実行コンテキストを構築
4. **ステップ実行**: `StepExecutor` でシナリオを実行
5. **結果返却**: 実行結果をJSON形式で返却

## 開発メモ

### 自動リロード

開発時は `reload=True` で起動しているため、コード変更が自動的に反映されます。

### ログ出力

実行ログは標準出力に出力されます。

### エラーハンドリング

- シナリオファイルが見つからない場合: 404 Not Found
- 実行エラー: 200 OK with `success: false` and `error` message
