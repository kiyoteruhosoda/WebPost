# Web予約自動化API 設計書（DDD + ポリモーフィズム / requests + 非同期）

## 0. 目的・前提
### 目的
- 時間起動（Job）からAPIを呼び出すと、対象Webサイトにログインし、自動で予約を取得する。
- 予約操作は **JSONシナリオ**（DSL）で定義し、事前に更新して運用する。
- 実行は **非同期** とし、APIは `run_id` を返して後から結果・ログを取得できる。

### 前提
- Runnerは初期は **requests** を使用（JavaScript少なめの画面遷移型）。
- **Cookieは requests.Session により Run単位で維持**する。
- 予約送信は **POST body (application/x-www-form-urlencoded)** で、同名キーの複数送信があり得る（`date` が複数など）。
- 変数入力は **JSON bodyが主**、クエリは上書き用（小さなパラメータのみ）とする。

---

## 1. 用語
- **Scenario**: 予約手順を表すDSL（JSON）。versionとenabledを持つ。
- **Run**: Scenarioの1回の実行単位。run_id、status、result、logsを持つ。
- **Step**: Scenario内の処理単位。`http/scrape/assert/sleep/log/result` 等。
- **Context**: Runの実行時状態（vars/state/lastResponse 等）。
- **Handler**: Step種別ごとの実行ロジック。ポリモーフィズムで差し替え可能。

---

## 2. 目標非機能要件（NFR）
- **安全性**: secrets（ID/パスワード）をシナリオやログに出さない。ログはマスク。
- **拡張性**: Step追加・Runner切替（requests→Playwright）を最小変更で可能にする。
- **再現性**: `scenario_id + scenario_version` を Runに記録し、実行結果の追跡を可能にする。
- **耐障害性**: リトライ・分岐（on_error/goto）をステップ単位で規定。
- **二重実行防止**: idempotency key により同一予約の重複実行を抑止可能にする（任意）。

---

## 3. システム構成（論理）
### 3.1 コンポーネント
- **Presentation（Web API）**: FastAPI。Run開始・参照・ログ参照・シナリオ更新。
- **Application（UseCase）**: Run開始・Run実行・Run参照などユースケース実装。
- **Domain（モデル）**: Scenario/Run/Step/Context/Expression を純粋に表現。
- **Infrastructure（外部I/O）**:
  - HTTP: requests.Session ベースの HttpClient
  - HTML解析: BeautifulSoup（label-based抽出など）
  - Queue: RQ(Redis)
  - Repository: シナリオ保存、Run保存、ログ保存（初期はファイル/SQLiteでも可）

### 3.2 実行フロー（非同期）
1. Jobが `POST /scenarios/{id}/runs` を呼ぶ（varsをbodyで渡す）。
2. APIは Runを作成（status=queued）し、キューに `ExecuteRunUseCase(run_id)` を投入。
3. Workerが Runを取得し、Scenario(version含む)をロード。
4. StepExecutor が Step を順に実行（Handlerへディスパッチ）。
5. 成功: `result`（例：reservationNo）を保存し status=succeeded。
6. 失敗: error を保存し status=failed。

---

## 4. API設計（REST）
### 4.1 Run開始
- **POST** `/scenarios/{scenario_id}/runs`
- Query: 上書き用（任意） `?key=value...`
- Body:
```json
{
  "vars": { "date": "2026-02-10", "toNo": "18", "dates": ["2026/02/02","2026/04/13"] }
}
```
- Response:
```json
{
  "run_id": "run_20260202_090501_8f31",
  "status": "queued",
  "scenario_id": 1,
  "scenario_version": 3,
  "links": {
    "self": "/runs/run_20260202_090501_8f31",
    "logs": "/runs/run_20260202_090501_8f31/logs"
  }
}
```

### 4.2 Run状態取得
- **GET** `/runs/{run_id}`
- Response:
```json
{
  "run_id": "run_...",
  "scenario_id": 1,
  "scenario_version": 3,
  "status": "succeeded",
  "started_at": "2026-02-02T09:05:01+09:00",
  "ended_at": "2026-02-02T09:05:14+09:00",
  "result": { "reservationNo": "00003217694" },
  "error": null
}
```

### 4.3 Runログ取得
- **GET** `/runs/{run_id}/logs`
- Response（例）:
```json
{
  "run_id": "run_...",
  "items": [
    {"ts":"...","step_id":"login_post","level":"INFO","message":"HTTP POST 200"},
    {"ts":"...","step_id":"extract_reservation_no","level":"INFO","message":"reservationNo=********694"}
  ]
}
```

### 4.4 シナリオ取得/更新（運用）
- **GET** `/scenarios/{scenario_id}`
- **PUT** `/scenarios/{scenario_id}`（認証必須）
  - 更新時は `version` をインクリメントする（競合回避）。

---

## 5. DDD設計
### 5.1 Domain（モデル）
#### Aggregates
- **Scenario（集約ルート）**
  - `ScenarioId, version, enabled, meta, steps[]`
  - 不変条件: `version` は単調増加、`steps[].id` はユニーク。
- **Run（集約ルート）**
  - `RunId, scenario_id, scenario_version, status, vars, result, error, logsRef, timestamps`
  - 不変条件: status遷移（queued→running→(succeeded/failed/canceled)）

#### Value Objects
- **RunContext**
  - `vars`: 入力変数（body+queryマージ後）
  - `state`: 途中生成（csrf、reservationNo等）
  - `last`: 直前HTTPレスポンス（status/url/text/headers）
- **RetryPolicy / OnErrorRule**
- **Expression / Condition**
  - `matches, contains, not_contains, ==, >=` 等の安全な評価関数群

#### Ports（Repository/Provider）
- `ScenarioRepository`
- `RunRepository`
- `RunLogRepository`
- `SecretProvider`（secretsを外部保管）
- `Clock`, `IdGenerator`

---

## 6. ポリモーフィズム設計（Step Handler）
### 6.1 Step（ドメイン）種類
- `HttpStep`
- `ScrapeStep`
- `AssertStep`
- `SleepStep`
- `LogStep`
- `ResultStep`

### 6.2 Handler（アプリケーション/インフラ境界）
- `StepHandler`（抽象）
  - `supports(step) -> bool`
  - `handle(step, ctx, deps) -> StepOutcome`
- 具象:
  - `HttpStepHandler`（requests.Session）
  - `ScrapeStepHandler`（BeautifulSoup）
  - `AssertStepHandler`（ExpressionEvaluator）
  - ...

### 6.3 Dispatcher（StepExecutor）
- Step配列を順に走査
- `HandlerRegistry` から対応Handlerを取得し実行
- 失敗時は `retry/on_error` を適用し `goto/retry/abort` を制御

---

## 7. HTTP設計（requests + Cookie）
- Run開始時に `requests.Session()` を生成し、Runの全HTTPステップで共有する。
- Cookieは自動で保持される（Set-Cookie → 次リクエスト）。
- 送信:
  - GET: `session.get(url, headers=..., params=...)`
  - POST: `session.post(url, headers=..., data=form_list)`  
    ※ `data` は **list[tuple]** を標準とし、同名キー複数送信に対応する。

---

## 8. シナリオDSL（JSON）仕様
### 8.1 トップレベル
```json
{
  "meta": { "id": 1, "name": "fun-navi-reserve", "description": "...", "version": 1, "enabled": true },
  "inputs": { "required": ["..."], "optional": ["..."] },
  "defaults": { "http": { "base_url": "https://fun-navi.net", "timeout_sec": 20, "headers": { "User-Agent": "ScenarioRunner/1.0" } } },
  "steps": [ ... ]
}
```

### 8.2 変数参照（テンプレート）
- `${vars.xxx}`: 入力変数
- `${state.xxx}`: 中間状態
- `${last.status}` `${last.text}`: 直前レスポンス
- `${secrets.xxx}`: SecretProvider から取得（ログ出力禁止）

### 8.3 form_list と配列展開
- `form_list`: `[[key, value], ...]`
- `value` が配列展開を表す場合:
  - `${vars.dates[*]}` のように `[*]` を許可し、各要素を同一キーで追加する
  - 例: `["date", "${vars.dates[*]}"]` → `("date", d1), ("date", d2), ...`
- ${...[*]} は list[str] を返す
- form_list の value が list の場合は (key, item) を複製して展開する



### 8.4 Step定義（例：login → reserve → extract reservationNo）
```json
{
  "id": "login_post",
  "type": "http",
  "request": {
    "method": "POST",
    "url": "https://fun-navi.net/FRPC010G_LoginAction.do",
    "form_list": [
      ["screenID","FRPC010G"],
      ["referrer",""],
      ["fulltimeID","${secrets.fulltimeID}"],
      ["password","${secrets.password}"],
      ["loginBTN","ログイン"]
    ]
  },
  "retry": { "max": 2, "backoff_sec": [1,3] }
}
```

```json
{
  "id": "reserve_post",
  "type": "http",
  "request": {
    "method": "POST",
    "url": "https://fun-navi.net/FRPC0400G_RegAction.do",
    "form_list": [
      ["screenID","FRPC0400G"],
      ["mansionGNo","${vars.mansionGNo}"],
      ["facilityID","${vars.facilityID}"],
      ["facilityNo","${vars.facilityNo}"],
      ["appliStart",""],
      ["eventFlg","false"],
      ["eventFacilityNo","0"],
      ["rsvNo","0"],
      ["spEventFlg","false"],
      ["selectDate","${vars.selectDate}"],
      ["toNo","${vars.toNo}"],
      ["roomNo","${vars.roomNo}"],
      ["date",""],
      ["date","${vars.dates[*]}"],
      ["hiddenUserId","${vars.hiddenUserId}"]
    ]
  },
  "on_error": [
    { "expr": "${last.status}==401", "action": "goto", "goto": "login_post" },
    { "expr": "${last.status}>=500", "action": "retry" },
    { "expr": null, "action": "abort" }
  ]
}
```

```json
{
  "id": "extract_reservation_no",
  "type": "scrape",
  "from": "last.text",
  "extract": [
    { "name": "reservationNo", "by": "label_next_td", "label": "予約番号", "required": true, "normalize": "trim" }
  ],
  "save_to": "state"
}
```

```json
{
  "id": "reserve_success",
  "type": "assert",
  "conditions": [
    { "expr": "${last.status}==200" },
    { "expr": "matches(${state.reservationNo}, '^[0-9]{11}$')" }
  ]
}
```


Scenario JSON（例：Fun Navi ログイン→予約→予約番号抽出）
```json
{
  "meta": {
    "id": 1,
    "name": "fun-navi-reserve",
    "description": "Login -> Reserve -> Extract reservation number",
    "version": 1,
    "enabled": true
  },
  "inputs": {
    "required": [
      "mansionGNo",
      "facilityID",
      "facilityNo",
      "selectDate",
      "toNo",
      "roomNo",
      "hiddenUserId",
      "dates"
    ],
    "optional": [
      "appliStart",
      "eventFlg",
      "eventFacilityNo",
      "rsvNo",
      "spEventFlg",
      "timeout_sec"
    ]
  },
  "defaults": {
    "http": {
      "base_url": "https://fun-navi.net",
      "timeout_sec": 20,
      "headers": {
        "User-Agent": "ScenarioRunner/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
      }
    }
  },
  "steps": [
    {
      "id": "login_get",
      "type": "http",
      "enabled": true,
      "request": {
        "method": "GET",
        "url": "/FRPC010G_LoginAction.do",
        "headers": {}
      },
      "retry": { "max": 1, "backoff_sec": [1] },
      "on_error": [
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "scrape_login_hidden",
      "type": "scrape",
      "enabled": true,
      "command": "hidden_inputs",
      "save_as": "login_hidden",
      "on_error": [
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "login_post",
      "type": "http",
      "enabled": true,
      "request": {
        "method": "POST",
        "url": "/FRPC010G_LoginAction.do",
        "merge_from_vars": "login_hidden",
        "form_list": [
          ["screenID", "FRPC010G"],
          ["referrer", ""],
          ["fulltimeID", "${secrets.fulltimeID}"],
          ["password", "${secrets.password}"],
          ["loginBTN", "ログイン"]
        ]
      },
      "retry": { "max": 1, "backoff_sec": [1] },
      "on_error": [
        { "expr": "${last.status}>=500", "action": "retry" },
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "assert_login_success",
      "type": "assert",
      "enabled": true,
      "conditions": [
        { "expr": "${last.status}==200" }
      ],
      "on_error": [
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "reserve_post",
      "type": "http",
      "enabled": true,
      "request": {
        "method": "POST",
        "url": "/FRPC0400G_RegAction.do",
        "form_list": [
          ["screenID", "FRPC0400G"],

          ["mansionGNo", "${vars.mansionGNo}"],
          ["facilityID", "${vars.facilityID}"],
          ["facilityNo", "${vars.facilityNo}"],

          ["appliStart", "${vars.appliStart}"],
          ["eventFlg", "${vars.eventFlg}"],
          ["eventFacilityNo", "${vars.eventFacilityNo}"],
          ["rsvNo", "${vars.rsvNo}"],
          ["spEventFlg", "${vars.spEventFlg}"],

          ["selectDate", "${vars.selectDate}"],
          ["toNo", "${vars.toNo}"],
          ["roomNo", "${vars.roomNo}"],

          ["date", ""],
          ["date", "${vars.dates[*]}"],

          ["hiddenUserId", "${vars.hiddenUserId}"]
        ]
      },
      "retry": { "max": 2, "backoff_sec": [1, 3] },
      "on_error": [
        { "expr": "${last.status}==401", "action": "goto", "goto_step_id": "login_get" },
        { "expr": "${last.status}>=500", "action": "retry" },
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "extract_reservation_no",
      "type": "scrape",
      "enabled": true,
      "command": "label_next_td",
      "label": "予約番号",
      "save_as": "reservationNo",
      "on_error": [
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "assert_reservation_no",
      "type": "assert",
      "enabled": true,
      "conditions": [
        { "expr": "${last.status}==200" },
        { "expr": "matches(${vars.reservationNo}, '^[0-9]{11}$')" }
      ],
      "on_error": [
        { "expr": null, "action": "abort" }
      ]
    },
    {
      "id": "result",
      "type": "result",
      "enabled": true,
      "fields": {
        "reservationNo": "${vars.reservationNo}"
      }
    }
  ]
}

```
1) ${vars.dates[*]} の扱い
TemplateRenderer は list を list のまま返す
FormComposer が ("date", d1), ("date", d2)… に展開する
（join してしまう実装だと壊れます）

2) reserve_post の optional 値
appliStart / eventFlg / ... を入力で省略した場合に空文字にしたいなら、入力側（vars）で空値を渡すか、TemplateRenderer を「未定義は空文字」にしている前提です（あなたの実装は dict.get(...,"") なのでOK）。

---

## 9. スクレイピング設計（label_next_td）
- `label_next_td(label)`:
  1) `th` を全探索し、テキストに `label` を含む要素を見つける
  2) その `th` の親 `tr` の次兄弟 `tr` を取得
  3) その `tr` の `td` テキストを抽出（予約番号など）
- これによりHTMLのclass変更に耐性が高い。

---

## 10. 非同期実行（RQ/Redis）
### 10.1 キュー投入
- `POST /scenarios/{id}/runs` で `enqueue(execute_run, run_id)` を実行

### 10.2 Worker
- `rq worker` でキューを監視し、Runを実行

---

## 11. 永続化（初期案）
最初は開発容易性を優先し、以下いずれかで開始:
- **SQLite**: Run/Log/ScenarioをDB管理（単一ノードで簡単）
- **File**: シナリオはJSONファイル、Run/LogはJSON Lines

本番運用で要求が上がれば以下へ移行:
- **PostgreSQL/MySQL**: Run/Log/ScenarioをRDB化
- **Redis**: 実行状態をキャッシュ（Run参照を高速化）

---

## 12. ディレクトリ構成（推奨）
```
app/
  presentation/
    api.py
    routes/
      runs.py
      scenarios.py
  application/
    usecases/
      start_run.py
      execute_run.py
      get_run.py
    handlers/
      base.py
      http_handler.py
      scrape_handler.py
      assert_handler.py
    ports/
      scenario_repo.py
      run_repo.py
      log_repo.py
      secret_provider.py
      http_client.py
  domain/
    scenario.py
    run.py
    expr.py
    steps/
      base.py
      http.py
      scrape.py
      assertion.py
      sleep.py
      log.py
      result.py
  infrastructure/
    http/
      requests_client.py
    scrape/
      bs4_scraper.py
    repo/
      scenario_file_repo.py
      run_sqlite_repo.py
      log_sqlite_repo.py
    queue/
      rq_client.py
      worker.py
```

---

## 13. ログ・マスキング方針
- `password/fulltimeID` 等の secrets はログに出さない
- 抽出値（予約番号等）は必要に応じて末尾数桁のみ表示（例：`********694`）
- HTTP bodyは原則ログ保存しない（保存する場合は要マスク）














---

## 14. リスクと対策
- **HTML変更**: label-based抽出 + assertで早期検知
- **パラメータ仕様変更**: Scenario version管理、ロールバック可能にする
- **二重予約**: idempotency_key導入（run作成時チェック）
- **アクセス制限**: User-Agent/待機(sleep)/リトライで対策。必要なら将来Playwrightへ。

---

## 15. requirements.txt（別ファイル）
- FastAPI/requests/bs4/RQ/Redis 等を使用（詳細は requirements.txt を参照）

