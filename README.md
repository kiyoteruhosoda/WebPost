# WebPost

YAML/JSONシナリオを実行する Web オートメーション実行基盤です。FastAPI エンドポイント経由の非同期実行と、CLI からの直接実行の両方を提供します。

## 現在の構成（DDD）

- **Domain**: `Scenario` / `Run` / `Step` などのドメインモデルと不変条件。  
- **Application**: ユースケース実行、ステップハンドラー、トレース生成、テンプレート・フォーム組み立てなどのアプリケーションサービス。  
- **Infrastructure**: シナリオローダー、Playwright/HTTP 実装、ロギング、シークレット解決、インメモリ永続化。  
- **Presentation**: FastAPI (`api/main.py`) と `scripts/` の実行スクリプト。

ポリモーフィズムは `application/handlers` と `application/executor/handler_registry.py` を中心に採用しており、ステップ種別ごとの振る舞いを分岐ではなくハンドラー差し替えで拡張できます。

## 主な機能

- YAML / JSON シナリオローディング（`infrastructure/scenario`）
- ステップ実行（`http` / `scrape` / `assert` / `log` / `result` / `browser`）
- リトライ・`on_error`（`retry` / `goto` / `abort`）
- テンプレート展開（`vars` / `state` / `secrets` / `last`）
- `form_list` による同名キー送信・配列展開
- HTTP トレースとトレース拡張（Trace Enricher）
- Idempotency 対応の run API

## ディレクトリ（抜粋）

```text
api/
application/
  executor/
  handlers/
  ports/
  services/
  trace_enrichers/
domain/
infrastructure/
scenarios/
scripts/
tests/
```

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 開発用コマンド

### テスト

```bash
source .venv/bin/activate
pytest -q
```

### API 起動

```bash
source .venv/bin/activate
python scripts/run_api.py
```

## API 利用

### 実行開始

```bash
curl -X POST http://localhost:8000/scenarios/sample-browser/runs \
  -H "Content-Type: application/json" \
  -d '{
    "vars": {},
    "secrets": {}
  }'
```

### 主なエンドポイント

- `GET /` : ヘルスチェック
- `POST /scenarios/{scenario_id}/runs` : 実行開始
- `GET /runs/{run_id}` : 実行状態・結果取得

詳細は `docs/API.md` を参照してください。

## シナリオ作成

- 仕様: `docs/SCENARIO_COMMAND.md`
- 例: `scenarios/simple_test.yaml`, `scenarios/sample_browser.yaml`

### 最小 YAML 例

```yaml
meta:
  id: simple

defaults:
  http:
    base_url: https://example.com

steps:
  - id: get_top
    type: http
    request:
      method: GET
      url: /

  - id: assert_status
    type: assert
    expr: ${last.status} == 200

  - id: output
    type: result
    value:
      ok: true
```

## ドキュメント

- API: `docs/API.md`
- HTTP ヘッダー: `docs/HTTP_HEADERS.md`
- シークレット運用: `docs/SECRETS.md`
- 次アクション: `docs/NextAction.md`
