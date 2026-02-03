# WebPost - シナリオ実行エンジン

design.mdの仕様に沿って実装されたWeb自動化シナリオ実行エンジン。

## 主要機能

### ✅ 実装完了

1. **JSONシナリオDSL**
   - シナリオをJSONで定義
   - ステップの種類: `http`, `scrape`, `assert`, `result`
   - リトライ・エラーハンドリング（retry, goto, abort）
   - **User-Agent**: meta.user_agentで定義、全リクエストに自動設定
   - **Referer**: 前のリクエストURLを自動的に次のリクエストに設定

2. **テンプレート変数展開**
   - `${vars.xxx}`: 入力変数
   - `${state.xxx}`: 中間状態
   - `${secrets.xxx}`: シークレット（`.env`ファイルまたは環境変数から読み込み、ログマスク対応）
   - `${last.status}`, `${last.text}`: 直前のHTTPレスポンス
   - **完全に汎用的**: `.env`に定義した任意の変数を`${secrets.変数名}`で参照可能

3. **配列展開（form_list）**
   - `${vars.dates[*]}` → 複数の同名キー送信に対応
   - 例: `["date", "${vars.dates[*]}"]` → `("date", "2026/02/02"), ("date", "2026/04/13")`

4. **HTTPクライアント**
   - `requests.Session` ベース
   - Cookie自動管理
   - **Referer自動設定**: 前のリクエストのURLを次のリクエストのRefererヘッダーに設定
   - **User-Agent自動設定**: meta.user_agentから取得して全リクエストに適用
   - `application/x-www-form-urlencoded` 対応
   - 同名キーの複数送信対応

5. **スクレイピング**
   - `hidden_inputs`: hidden inputフィールドの一括抽出
   - `css`: CSSセレクタによる抽出
   - `label_next_td`: HTML構造変更に強い抽出方法
     - `<th>ラベル</th>` → 次の`<tr>` → `<td>値</td>`

6. **リトライとエラーハンドリング**
   - ステップ単位のリトライ設定（max, backoff_sec）
   - 条件付きエラーハンドリング（on_error）
   - `goto`: 指定ステップへジャンプ（例: 401 → login_get）
   - `retry`: リトライ実行
   - `abort`: 実行中断

7. **DDD設計**
   - Domain: Scenario, Run, Step, Context
   - Application: Handler (ポリモーフィズム), Executor, Services
   - Infrastructure: HTTP, Logging, Secrets, URL

## ディレクトリ構成

```
application/
  executor/
    handler_registry.py   - ハンドラー登録・ディスパッチ
    step_executor.py      - ステップ実行（retry/goto対応）
  handlers/
    base.py               - ハンドラー基底クラス
    http_handler.py       - HTTPリクエスト処理
    scrape_handler.py     - スクレイピング処理
    assert_handler.py     - アサーション処理
    result_handler.py     - 結果保存処理
  services/
    template_renderer.py  - テンプレート変数展開
    form_composer.py      - form_list生成（配列展開）
    execution_deps.py     - 実行時依存注入
  ports/
    http_client.py        - HTTPクライアントポート
    requests_client.py    - requests実装

domain/
  scenario.py             - シナリオ集約ルート
  run.py                  - Run, RunContext
  steps/
    base.py               - Step基底、RetryPolicy, OnErrorRule
    http.py               - HttpStep
    scrape.py             - ScrapeStep
    assertion.py          - AssertStep
    result.py             - ResultStep

infrastructure/
  scenario/
    json_loader.py        - JSONシナリオローダー
    file_finder.py        - シナリオファイル検索
  http/
    http_artifact_saver.py
  logging/
    console_logger.py
  url/
    base_url_resolver.py

api/
  main.py                 - FastAPI REST APIエンドポイント

scenarios/
  fun_navi_reserve.json   - サンプルシナリオ

scripts/
  run_api.py              - APIサーバー起動スクリプト
  test_api.py             - API動作テストスクリプト
  test_scenario.py        - シナリオテスト実行スクリプト
```

## 使い方

### 環境設定

まず、`.env`ファイルを作成して認証情報を設定します：

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集して実際の認証情報を設定
# FUNNAVI_FULLTIME_ID=your_actual_id
# FUNNAVI_PASSWORD=your_actual_password
```

`.env`ファイルの例：
```
FUNNAVI_FULLTIME_ID=12345678
FUNNAVI_PASSWORD=your_password
```

### REST API サーバー起動

```bash
# APIサーバーを起動
python scripts/run_api.py

# 別のターミナルでAPIをテスト
python scripts/test_api.py
```

APIエンドポイント:
- `GET /` - ヘルスチェック
- `POST /scenarios/{scenario_id}/runs` - シナリオ実行

リクエスト例:
```bash
curl -X POST http://localhost:8000/scenarios/fun-navi-reserve/runs \
  -H "Content-Type: application/json" \
  -d '{
    "vars": {
      "dates": ["", "2026/02/02", "2026/04/13"]
    },
    "secrets": {
      "username": "test_user",
      "password": "test_pass"
    }
  }'
```

レスポンス例:
```json
{
  "success": true,
  "result": {
    "reservationNo": "00003217694"
  }
}
```

### シナリオ実行テスト（スタンドアロン）

```bash
# .envファイルから認証情報を読み込んで実行
python scripts/test_scenario.py scenarios/fun_navi_reserve.json

# モックモードで実行（外部依存なし）
python scripts/test_scenario.py scenarios/fun_navi_reserve.json --mock
```

**注意**: `.env`ファイルに `FUNNAVI_FULLTIME_ID` と `FUNNAVI_PASSWORD` を設定する必要があります。

### シナリオJSON例

`.env`ファイルの設定：
```
# 任意の環境変数を定義可能
FUNNAVI_FULLTIME_ID=your_id
FUNNAVI_PASSWORD=your_password
API_KEY=your_api_key
DATABASE_URL=postgresql://localhost/db
```

シナリオファイル：
```json
{
  "meta": {
    "id": 1,,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "defaults": {
    "http": {
      "base_url": "https://fun-navi.net",
      "timeout_sec": 20,
      "headers": {
        "Accept": "text/html"
      }
      "base_url": "https://fun-navi.net",
      "timeout_sec": 20
    }
  },
  "steps": [
    {
      "id": "login_post",
      "type": "http",
      "request": {
        "method": "POST",
        "url": "/login",
        "form_list": [
          ["fulltimeID", "${secrets.FUNNAVI_FULLTIME_ID}"],
          ["password", "${secrets.FUNNAVI_PASSWORD}"]
        ]
      },
      "retry": { "max": 2, "backoff_sec": [1, 3] },
      "on_error": [
        { "expr": "${last.status}>=500", "action": "retry" },
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "scrape_hidden",
      "type": "scrape",
      "command": "hidden_inputs",
      "save_as": "form_data"
    },
    {
      "id": "submit",
      "type": "http",
      "request": {
        "method": "POST",
        "url": "/submit",
        "merge_from_vars": "form_data",
        "form_list": [
          ["date", "${vars.dates[*]}"]
        ]
      }
    },
    {
      "id": "extract_result",
      "type": "scrape",
      "command": "label_next_td",
      "label": "予約番号",
      "save_as": "reservationNo"
    },
    {
      "id": "result",
      "type": "result",
      "fields": {
        "reservationNo": "${vars.reservationNo}"
      }
    }
  ]
}
```

## 実装の特徴

### 1. 配列展開の仕組み

- **TemplateRenderer**: `${vars.dates[*]}` を `list` のまま返す
- **FormComposer**: `list` の各要素を `(key, item)` に展開
- 結果: `("date", "2026/02/02"), ("date", "2026/04/13")` のように同名キーで複数送信

### 2. label_next_tdスクレイピング

HTML構造変更に強い抽出方法：

```html
<tr><th>予約番号</th></tr>
<tr><td>00003217694</td></tr>
```

1. `<th>` で「予約番号」テキストを含む要素を検索
2. その親 `<tr>` を取得
3. 次の兄弟 `<tr>` を取得
4. その中の `<td>` テキストを抽出

### 3. リトライとgoto

```json
{
  "retry": { "max": 2, "backoff_sec": [1, 3] },
  "on_error": [
    { "expr": "${last.status}==401", "action": "goto", "goto_step_id": "login_get" },
    { "expr": "${last.status}>=500", "action": "retry" },
    { "expr": null, "action": "abort" }
  ]
}
```

- リトライは `max + 1` 回試行（初回 + リトライ回数）
- `on_error` は上から順に評価、マッチした最初のアクションを実行
- `expr: null` は else 節（常にマッチ）

## テスト結果

実際のWebサイト（fun-navi.net）に対してテスト実行し、以下を確認：

✅ JSONシナリオのロード成功  
✅ テンプレート変数展開動作（vars, secrets, last）  
✅ **配列展開が正常動作**（dates配列 → 3つのdateパラメータ）  
✅ HTTPリクエスト実行、Cookie維持  
✅ スクレイピング（hidden_inputs）動作  
✅ **label_next_tdスクレイピングが動作**（予約番号抽出成功）  
✅ アサーション動作  
✅ HTTPトレース・ログ出力  
✅ HTTPアーティファクト保存（tmp/http/）

### モックテスト

外部依存なしで完全にテストできるように、モックHTTPクライアントを実装：

```bash
# モックモードで実行（常に成功）
python scripts/test_scenario.py scenarios/fun_navi_reserve.json --mock

# 実際のWebサイトに対して実行
python scripts/test_scenario.py scenarios/fun_navi_reserve.json
```

モックモードの結果：
```
✅ Scenario execution completed successfully
Result: {
  "reservationNo": "00003217694"
}
```

全8ステップが成功：
1. ✅ login_get - ログインページ取得
2. ✅ scrape_login_hidden - hidden inputs抽出
3. ✅ login_post - ログイン送信
4. ✅ assert_login_success - ログイン成功確認
5. ✅ reserve_post - 予約送信（**配列展開動作確認**）
6. ✅ extract_reservation_no - **label_next_tdで予約番号抽出**
7. ✅ assert_reservation_no - 予約番号形式確認
8. ✅ result - 結果保存

ログ出力例：
```
http.form_composed {
  "form": [
    ["date", ""],
    ["date", "2026/02/02"],
    ["date", "2026/04/13"]
  ]
}
```

## 今後の拡張

- [x] **REST API（FastAPI）** - `/scenarios/{id}/runs` エンドポイント実装済み
- [ ] Run永続化（SQLite/PostgreSQL）
- [ ] 非同期実行（RQ/Redis）
- [ ] Playwright統合（JavaScript対応）
- [ ] idempotency key対応
- [ ] より豊富なアサーション関数
- [ ] ログマスキングの強化

## 関連ドキュメント

- [design.md](design.md) - 設計書
- [AGEND.md](AGEND.md) - アジェンダ
- [docs/API.md](docs/API.md) - REST API ドキュメント
- [docs/SECRETS.md](docs/SECRETS.md) - シークレット管理ガイド
- [docs/HTTP_HEADERS.md](docs/HTTP_HEADERS.md) - HTTPヘッダー自動設定（User-Agent, Referer, Cookie）
