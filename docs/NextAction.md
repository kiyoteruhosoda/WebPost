
# シナリオ TypeCommand リファレンス（全量・改訂版）

（CLI/HTTP 統合・同期実装を正 / 非同期Runは拡張TODO）

## 1. 目的

* シナリオ実行の操作を **CLI/HTTP双方で統一的に定義**する。
* YAML/YML/JSON形式のシナリオを **拡張子に基づいて確実に解決**する。
* 実行結果とエラーを **機械処理可能な形式**で返す。
* 外部サイト（画面遷移・Cookie・HTMLスクレイプ）を前提に、**安全性（secrets保護）と再現性（ログ・メタ記録）**を担保する。

---

## 2. 対象と前提

### 2.1 対象

* シナリオ実行機能の利用者（API/CLI利用者、運用担当、開発者）

### 2.2 前提（実装済み：現行仕様）

* シナリオは `scenarios/` 配下に配置され、拡張子で形式が識別される。
* 形式は `.yaml` / `.yml` / `.json` をサポートする。
* シナリオはステップ列を持つが、本ドキュメントでは **Typeリファレンス側にのみ**ステップ仕様を記載する。
* 実行は **同期**（HTTPは `success/result/error` を即時返却）を正とする。

### 2.3 TODO（未実装想定の将来拡張）

* TODO: **非同期Run（run_id）方式**を正式導入する（監査・長時間実行・ログ参照向き）
* TODO: HTTPに `wait_sec`（上限付き待機）を導入し、非同期と同期の両立を提供する
* TODO: `secret_ref`（SecretProvider参照）方式を導入し、HTTP body で secrets を渡さない運用に寄せる
* TODO: idempotency key による二重実行防止
* TODO: シナリオの保存先をRepository（DB等）に拡張（現状はファイル前提）

---

## 3. コマンド体系（CLI/HTTP）

## 3.1 CLI: `scenario run`（実装済み）

### 形式

```
scenario run --scenario-id <id> [--vars <json>] [--secrets <json>] [--format <yaml|yml|json>]
scenario run --scenario-file <path> [--vars <json>] [--secrets <json>]
```

### パラメータ

| 名前                | 型            |     必須 | 説明                             |
| ----------------- | ------------ | -----: | ------------------------------ |
| `--scenario-id`   | string       | いずれか必須 | `scenarios/` 配下のID検索に使用。       |
| `--scenario-file` | string       | いずれか必須 | 直接ファイルパスを指定。                   |
| `--vars`          | string(JSON) |     任意 | 変数入力。JSON文字列。                  |
| `--secrets`       | string(JSON) |     任意 | シークレット入力。JSON文字列。              |
| `--format`        | string       |     任意 | `--scenario-id` 使用時に拡張子解決を上書き。 |

### 返却

* 終了コード: `0`（成功）、`1`（失敗）
* 標準出力: 実行サマリ、メタ情報、結果（機械処理可能）
* 標準エラー: 失敗時の詳細

### 例

```
scenario run --scenario-id fun_navi_reserve --vars '{"facilityID":"001"}'
scenario run --scenario-file scenarios/sample.json --secrets '{"api_key":"xxx"}'
```

### TODO（CLI拡張）

* TODO: `scenario run start/wait/status/logs` を導入（非同期Runに対応）
* TODO: `--wait` / `--timeout-sec` を導入（内部が非同期でもCLIは同期体験にできる）
* TODO: `--secrets` は標準入力/ファイル経由を推奨し、shell履歴リスクを低減

---

## 3.2 HTTP: 同期実行 `POST /scenarios/{scenario_id}/runs`（実装済み）

### 目的

* シナリオをHTTP経由で実行し、結果をJSONで返す（同期応答）

### パスパラメータ

| 名前            | 型      | 必須 | 説明                           |
| ------------- | ------ | -: | ---------------------------- |
| `scenario_id` | string | 必須 | シナリオID。`scenarios/` から検索される。 |

### リクエストボディ（実装済み）

```json
{
  "vars": {},
  "secrets": {}
}
```

| フィールド     | 型      | 必須 | 説明       |
| --------- | ------ | -: | -------- |
| `vars`    | object | 任意 | 変数入力     |
| `secrets` | object | 任意 | シークレット入力 |

### レスポンス（実装済み）

```json
{
  "success": true,
  "result": {},
  "error": null
}
```

| フィールド     | 型           | 必須 | 説明       |
| --------- | ----------- | -: | -------- |
| `success` | boolean     | 必須 | 実行成功フラグ  |
| `result`  | object/null | 必須 | 実行結果     |
| `error`   | string/null | 必須 | エラーメッセージ |

### ステータスコード（実装済み）

| コード   | 条件                  |
| ----- | ------------------- |
| `200` | 正常応答（successに結果が反映） |
| `404` | シナリオファイルが存在しない      |
| `400` | サポート外の形式            |

---

## 3.3 TODO: HTTP 非同期Run（推奨拡張）

> **Step順序がズレない**ことを仕様として明文化する（Run内は逐次）。
> 非同期は「呼び出し元が待つ/待たない」の違いで、Run内ステップは必ず順次実行。

### TODO: 非同期起動

* TODO: `POST /scenarios/{scenario_id}/runs` → `202 Accepted`

```json
{
  "run_id": "run_20260203_171500_abcd",
  "status": "queued",
  "links": {
    "self": "/runs/run_20260203_171500_abcd",
    "logs": "/runs/run_20260203_171500_abcd/logs"
  }
}
```

### TODO: 状態参照

* TODO: `GET /runs/{run_id}` → status/result/error/timestamps
* TODO: `GET /runs/{run_id}/logs` → ログ一覧

### TODO: wait（同期体験の両立）

* TODO: `POST /scenarios/{scenario_id}/runs?wait_sec=30`

  * 30秒以内に完了 → `200 success/result/error`
  * 30秒を超過 → `202 run_id` を返す

---

## 4. フォーマット解決ルール（実装済み）

* `--scenario-id` またはHTTP経由の場合は、拡張子でローダーを選択する。
* 拡張子の対応:

  * `.yaml` / `.yml` → YAMLローダー
  * `.json` → JSONローダー
* 未対応拡張子は、実行前にフォーマットエラーとする。

### TODO

* TODO: `scenario_id` で複数候補が存在する場合の優先規則（例: `.json`優先）

---

## 5. 実行フロー（共通）

### 5.1 同期（実装済み）

1. シナリオファイルを解決（IDまたはファイルパス）。
2. 拡張子に応じてローダー選択。
3. シナリオをドメインオブジェクトへ変換。
4. 実行依存（logger、secret、http client等）を構築。
5. ステップを順次実行（`enabled=false`はスキップ）。
6. 結果を集約して返却。

### 5.2 TODO: 非同期Run（将来）

* TODO: Runを作成し `queued → running → succeeded/failed` と遷移
* TODO: ワーカーがRunを取り出し、**Run内ステップは必ず配列順に逐次実行**する
* TODO: requests.Session / Context は Runスコープで隔離し、他Runと共有しない

---

## 6. テンプレート（変数参照）仕様

### 6.1 参照

* `${vars.xxx}`: 入力変数
* `${state.xxx}`: 中間状態（抽出結果など）
* `${last.status}` `${last.text}` `${last.url}`: 直前HTTPレスポンス
* `${secrets.xxx}`: シークレット（ログ出力禁止）

### 6.2 展開規約（実装依存部分を含む）

* テンプレート展開は `${...}` を評価し置換する。
* 値が配列/辞書の場合の扱いは、各フィールドの型仕様に従う。

### TODO

* TODO: 未定義参照時の挙動を固定（空文字/例外/そのまま）
* TODO: `${vars.dates[*]}` の配列展開記法を正式仕様化（現状は実装依存）

---

## 7. シナリオDSL（トップレベル）仕様（stepsは記載しない）

> **本章では steps の中身は扱わない**（Typeリファレンス側に集約）。

### 7.1 トップレベル構造

```json
{
  "meta": {
    "id": "fun_navi_reserve",
    "name": "fun-navi-reserve",
    "description": "Login -> Reserve -> Extract reservation number",
    "version": 1,
    "enabled": true
  },
  "inputs": {
    "required": ["mansionGNo", "facilityID", "dates"],
    "optional": ["timeout_sec"]
  },
  "defaults": {
    "http": {
      "base_url": "https://fun-navi.net",
      "timeout_sec": 20,
      "headers": {
        "User-Agent": "ScenarioRunner/1.0"
      }
    }
  },
  "steps": []
}
```

### 7.2 meta

| フィールド         | 型       | 必須 | 説明                           |
| ------------- | ------- | -: | ---------------------------- |
| `id`          | string  | 推奨 | シナリオ識別子（`scenario_id` と一致推奨） |
| `name`        | string  | 任意 | 表示名                          |
| `description` | string  | 任意 | 説明                           |
| `version`     | integer | 任意 | バージョン（運用用）                   |
| `enabled`     | boolean | 任意 | シナリオ全体の実行可否。省略時true          |

### 7.3 inputs（任意）

| フィールド      | 型             | 必須 | 説明     |
| ---------- | ------------- | -: | ------ |
| `required` | array(string) | 任意 | 必須入力キー |
| `optional` | array(string) | 任意 | 任意入力キー |

### 7.4 defaults.http（任意）

| フィールド         | 型       | 必須 | 説明         |
| ------------- | ------- | -: | ---------- |
| `base_url`    | string  | 任意 | 相対URL解決の基点 |
| `timeout_sec` | integer | 任意 | HTTPタイムアウト |
| `headers`     | object  | 任意 | 既定ヘッダ      |

### TODO

* TODO: inputsに基づく実行前バリデーション（不足時はHTTP 400/CLI exit 1）
* TODO: versionの競合制御（Repository運用時）

---

## 8. ログ仕様（実装済み）

* すべてのログイベントに `type` フィールドを含める。
* ステップ実行時は `step.start` / `step.end` を必ず出力する。
* 相関用に `run_id`（同期は省略可だが推奨）と `step_id` を含める。

例:

```
step.start {"type":"step.start","run_id":"...","step_id":"login"}
step.end {"type":"step.end","run_id":"...","step_id":"login","ok":true,"elapsed_ms":120}
```

### TODO

* TODO: 同期実行でも `run_id` を付与してログ相関を統一（将来の非同期化に備える）
* TODO: `http.request/http.response` のログスキーマ標準化（bodyは原則保存しない）

---

## 9. セキュリティ・マスキング（運用要件）

### 実装済み前提（最低限）

* `secrets` はログに出さない（message/fieldsへの展開は禁止）
* 抽出値（予約番号等）は必要に応じてマスク（末尾数桁のみ）

### TODO

* TODO: `${secrets.*}` が log に出た場合の強制エラー（実行停止）を仕様化
* TODO: HTTPの `secrets` を廃止し `secret_ref` に移行（KeyVault等）

---

# 10. シナリオ Type リファレンス（全量）

（ここが “stepsの仕様” の本体。各Typeごとに JSON サンプル付き）

## 10.1 共通フィールド（実装済み）

| フィールド      | 型       | 必須 | 説明                                              |
| ---------- | ------- | -: | ----------------------------------------------- |
| `id`       | string  | 必須 | ステップ識別子                                         |
| `type`     | string  | 必須 | `http` / `scrape` / `assert` / `result` / `log` |
| `enabled`  | boolean | 任意 | 省略時 `true`                                      |
| `retry`    | object  | 任意 | リトライ設定                                          |
| `on_error` | array   | 任意 | エラー時制御                                          |

### retry（実装済み）

| フィールド         | 型              | 必須 | 説明       |
| ------------- | -------------- | -: | -------- |
| `max`         | integer        | 任意 | 最大リトライ回数 |
| `backoff_sec` | array(integer) | 任意 | バックオフ秒数  |

> TODO: backoff配列不足時の扱い（最後を繰り返す等）を固定

### on_error（実装済み）

| フィールド          | 型           | 必須 | 説明                         |
| -------------- | ----------- | -: | -------------------------- |
| `expr`         | string/null | 任意 | 条件式。nullはフォールバック           |
| `action`       | string      | 任意 | `abort` / `retry` / `goto` |
| `goto_step_id` | string      | 任意 | goto時の遷移先                  |

---

## 10.2 Type: `http`（実装済み）

### 目的

* HTTPリクエストを実行し、レスポンスを `last` に保存する。

### 追加フィールド（実装済み）

| フィールド          | 型       | 必須 | 説明                  |
| -------------- | ------- | -: | ------------------- |
| `request`      | object  | 必須 | HTTPリクエスト仕様         |
| `save_as_last` | boolean | 任意 | last保存有無（省略時true想定） |

#### request（実装済み）

| フィールド             | 型                    | 必須 | 説明                                |
| ----------------- | -------------------- | -: | --------------------------------- |
| `method`          | string               | 任意 | 省略時 `GET`                         |
| `url`             | string               | 必須 | 相対/絶対                             |
| `headers`         | object               | 任意 | 既定ヘッダとマージ                         |
| `form_list`       | array([string, any]) | 任意 | フォーム（同名キー複数可・順序保持）                |
| `merge_from_vars` | string               | 任意 | `vars[merge_from_vars]` をフォームにマージ |

#### form_list 規約（重要）

* `form_list` は **順序を保持**する
* 同名キーの複数送信を許容する
* value が list の場合、(key,item) を複製して展開する（joinしない）

**JSON例**

```json
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
}
```

---

## 10.3 Type: `scrape`（実装済み）

### 目的

* HTMLから情報を抽出し、変数領域へ保存する。

### 追加フィールド（実装済み）

| フィールド      | 型       | 必須 | 説明        |
| ---------- | ------- | -: | --------- |
| `command`  | string  | 必須 | スクレイプコマンド |
| `save_as`  | string  | 任意 | 保存キー      |
| `selector` | string  | 任意 | CSSセレクタ   |
| `attr`     | string  | 任意 | 抽出属性      |
| `multiple` | boolean | 任意 | 複数取得      |
| `label`    | string  | 任意 | label系抽出  |

### command例（実装済み前提）

* `hidden_inputs`
* `label_next_td`

**JSON例（hidden_inputs）**

```json
{
  "id": "scrape_login_hidden",
  "type": "scrape",
  "enabled": true,
  "command": "hidden_inputs",
  "save_as": "login_hidden",
  "on_error": [{ "expr": null, "action": "abort" }]
}
```

**JSON例（label_next_td）**

```json
{
  "id": "extract_reservation_no",
  "type": "scrape",
  "enabled": true,
  "command": "label_next_td",
  "label": "予約番号",
  "save_as": "reservationNo",
  "on_error": [{ "expr": null, "action": "abort" }]
}
```

### TODO

* TODO: `save_to`（vars/stateどちらへ保存するか）を仕様化（現状save_asのみだと曖昧化しやすい）
* TODO: `source`（last.text以外）を指定できるようにする

---

## 10.4 Type: `assert`（実装済み）

### 目的

* 条件式の評価で成否を判定する。

### 追加フィールド（実装済み）

| フィールド        | 型             | 必須 | 説明   |
| ------------ | ------------- | -: | ---- |
| `conditions` | array(object) | 必須 | 判定条件 |

#### conditions（実装済み）

| フィールド  | 型      | 必須 | 説明  |
| ------ | ------ | -: | --- |
| `expr` | string | 必須 | 評価式 |

**評価規約（推奨/暗黙）**

* conditions は **全て真（AND）**で成功
* 失敗時は on_error を適用

**JSON例**

```json
{
  "id": "assert_reservation_no",
  "type": "assert",
  "enabled": true,
  "conditions": [
    { "expr": "${last.status}==200" },
    { "expr": "matches(${state.reservationNo}, '^[0-9]{11}$')" }
  ],
  "on_error": [{ "expr": null, "action": "abort" }]
}
```

### TODO

* TODO: OR、失敗メッセージ、fail_fast等の拡張

---

## 10.5 Type: `result`（実装済み）

### 目的

* 実行結果を `result` に格納する（HTTP/CLIの result になる）。

### 追加フィールド（実装済み）

| フィールド    | 型      | 必須 | 説明              |
| -------- | ------ | -: | --------------- |
| `fields` | object | 任意 | 出力キーと値（テンプレート可） |

**JSON例**

```json
{
  "id": "result",
  "type": "result",
  "enabled": true,
  "fields": {
    "reservationNo": "${state.reservationNo}"
  }
}
```

### TODO

* TODO: resultが複数回出た場合の挙動（上書き/マージ/エラー）固定

---

## 10.6 Type: `log`（実装済み）

### 目的

* 実行途中でログを出力する。

### 追加フィールド（実装済み）

| フィールド     | 型      | 必須 | 説明                                  |
| --------- | ------ | -: | ----------------------------------- |
| `message` | string | 必須 | ログ本文（テンプレート可）                       |
| `level`   | string | 任意 | `info` / `debug` / `error`（省略時info） |
| `fields`  | object | 任意 | 付加フィールド                             |

**JSON例**

```json
{
  "id": "log_after_login",
  "type": "log",
  "enabled": true,
  "level": "info",
  "message": "login status=${last.status} url=${last.url}",
  "fields": {
    "step": "login",
    "status": "${last.status}"
  }
}
```

### TODO

* TODO: `${secrets.*}` が message/fields に出たら強制失敗（情報漏洩防止）

---

## 11. エラーハンドリング（実装済み）

* ファイル未検出: CLIは終了コード`1`、HTTPは`404`。
* 形式未対応: CLIは終了コード`1`、HTTPは`400`。
* 実行失敗: `success=false` と `error` に理由を格納。

### TODO

* TODO: `error` の構造化（code/message/step_id/last.status 等）

---

## 12. 付録：非同期導入時の“順序不変”宣言（TODOだが強く推奨）

> ここはあなたの懸念（Step順がズレて壊れる）を仕様で潰すための条項です。

* TODO: **1つのRun内で、ステップは必ず配列順に逐次実行する**（並列実行しない）
* TODO: `requests.Session` は Runスコープで生成し、Run終了で破棄する（Cookie混線防止）
* TODO: `vars/state/last` は Runスコープで隔離し、他Runと共有しない
* TODO: 同一Runを同時に2回実行しない（ロック/状態遷移で防止）

---
