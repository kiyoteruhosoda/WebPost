# シナリオコマンド設計書（リファレンス）

## 目的
- シナリオ実行の操作を、CLI/HTTP双方で統一的に定義する。
- YAML/YML/JSON形式のシナリオを、拡張子に基づいて確実に解決する。
- 実行結果とエラーを、機械処理可能な形式で返す。

## 対象と前提
- 対象: シナリオ実行機能の利用者（API/CLIの利用者、運用担当）。
- 前提: シナリオは `scenarios/` 配下に配置され、拡張子で形式が識別される。
- 形式: `.yaml` / `.yml` / `.json` をサポートする。

## コマンド体系

### CLI: `scenario run`
#### 目的
- シナリオをローカルで実行し、結果を標準出力に返す。

#### 形式
```
scenario run --scenario-id <id> [--vars <json>] [--secrets <json>] [--format <yaml|yml|json>]
scenario run --scenario-file <path> [--vars <json>] [--secrets <json>]
```

#### パラメータ
| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `--scenario-id` | string | いずれか必須 | `scenarios/` 配下のID検索に使用。 |
| `--scenario-file` | string | いずれか必須 | 直接ファイルパスを指定する。 |
| `--vars` | string(JSON) | 任意 | 変数入力。JSON文字列。 |
| `--secrets` | string(JSON) | 任意 | シークレット入力。JSON文字列。 |
| `--format` | string | 任意 | `--scenario-id` 使用時に拡張子解決を上書きする。 |

#### 返却
- 終了コード: `0`（成功）、`1`（失敗）
- 標準出力: 実行サマリ、メタ情報、結果を出力
- 標準エラー: 失敗時の詳細情報

#### 例
```
scenario run --scenario-id fun_navi_reserve --vars '{"facilityID":"001"}'
scenario run --scenario-file scenarios/sample.json --secrets '{"api_key":"xxx"}'
```

---

### HTTP: `POST /scenarios/{scenario_id}/runs`
#### 目的
- シナリオをHTTP経由で実行し、結果をJSONで返す。

#### パスパラメータ
| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `scenario_id` | string | 必須 | シナリオID。`scenarios/` から検索される。 |

#### リクエストボディ
```json
{
  "vars": {},
  "secrets": {}
}
```

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `vars` | object | 任意 | 変数入力。 |
| `secrets` | object | 任意 | シークレット入力。 |

#### レスポンス
```json
{
  "success": true,
  "result": {},
  "error": null
}
```

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `success` | boolean | 必須 | 実行成功フラグ。 |
| `result` | object/null | 必須 | 実行結果。 |
| `error` | string/null | 必須 | 失敗時のエラーメッセージ。 |

#### ステータスコード
| コード | 条件 |
|---|---|
| `200` | 正常応答（`success` に結果が反映される） |
| `404` | シナリオファイルが存在しない |
| `400` | サポート外の形式 |

---

## フォーマット解決ルール
- `--scenario-id` またはHTTP経由の場合は、拡張子でローダーを選択する。
- 拡張子の対応:
  - `.yaml` / `.yml` → YAMLローダー
  - `.json` → JSONローダー
- 未対応拡張子は、実行前にフォーマットエラーとする。

## 実行フロー（共通）
1. シナリオファイルを解決（IDまたはファイルパス）。
2. 拡張子に応じてローダー選択。
3. シナリオをドメインオブジェクトへ変換。
4. 実行依存（logger、secret、url resolver）を構築。
5. ステップを順次実行。
6. 結果を集約して返却。

## シナリオTypeリファレンス（全量）
### 共通フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string | 必須 | ステップ識別子。 |
| `type` | string | 必須 | ステップ種別。`http` / `scrape` / `assert` / `result` / `log`。 |
| `enabled` | boolean | 任意 | 実行可否。省略時は`true`。 |
| `retry` | object | 任意 | リトライ設定。 |
| `on_error` | array | 任意 | エラー時の制御ルール。 |

#### `retry` 詳細
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `max` | integer | 任意 | 最大リトライ回数。 |
| `backoff_sec` | array(integer) | 任意 | バックオフ秒数の配列。 |

#### `on_error` 詳細
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `expr` | string | 任意 | 条件式。未指定の場合はフォールバック扱い。 |
| `action` | string | 任意 | `abort` / `retry` / `goto`。 |
| `goto_step_id` | string | 任意 | `action=goto` 時の遷移先。 |

---

### Type: `http`
#### 目的
- HTTPリクエストを実行し、レスポンスを`last`に保存する。

#### 追加フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `request` | object | 必須 | HTTPリクエスト仕様。 |
| `save_as_last` | boolean | 任意 | レスポンスを`last`へ保存するか。 |

#### `request` 詳細
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `method` | string | 任意 | HTTPメソッド。省略時は`GET`。 |
| `url` | string | 必須 | リクエストURL。 |
| `headers` | object | 任意 | HTTPヘッダ。 |
| `form_list` | array([string,string]) | 任意 | フォーム配列。 |
| `merge_from_vars` | string | 任意 | `vars`の辞書をフォームにマージ。 |

---

### Type: `scrape`
#### 目的
- HTMLから情報を抽出し、`vars`または`state`へ保存する。

#### 追加フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `command` | string | 必須 | スクレイプコマンド。 |
| `save_as` | string | 任意 | 保存先キー。 |
| `selector` | string | 任意 | CSSセレクタ。 |
| `attr` | string | 任意 | 抽出属性。 |
| `multiple` | boolean | 任意 | 複数取得の有無。 |
| `label` | string | 任意 | 追加ラベル。 |

---

### Type: `assert`
#### 目的
- 条件式の評価でシナリオの成否を判定する。

#### 追加フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `conditions` | array(object) | 必須 | 判定条件の配列。 |

#### `conditions` 詳細
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `expr` | string | 必須 | 評価式。 |

---

### Type: `result`
#### 目的
- 実行結果を`result`に格納する。

#### 追加フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `fields` | object | 任意 | 出力するキーと値。 |

---

### Type: `log`
#### 目的
- 実行途中でログを出力し、変数や状態を可視化する。

#### 追加フィールド
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `message` | string | 必須 | ログ本文。テンプレート展開に対応。 |
| `level` | string | 任意 | `info` / `debug` / `error`。省略時は`info`。 |
| `fields` | object | 任意 | 付加フィールド。テンプレート展開に対応。 |

## エラーハンドリング
- ファイル未検出: CLIは終了コード`1`、HTTPは`404`。
- 形式未対応: CLIは終了コード`1`、HTTPは`400`。
- 実行失敗: `success=false` と `error` に理由を格納。

## ログ仕様
- すべてのログイベントに `type` フィールドを含める。
- ステップ実行時は `step.start` / `step.end` を必ず出力する。
- 相関用に `run_id` と `step_id` を含める。

### `type` ログ詳細
#### 目的
- ログイベントの種別を機械的に識別するための必須フィールド。

#### 仕様
- 値はイベント名と一致する。
- すべてのログ行に含まれる。
- 既存フィールドと衝突する場合は、イベント名を優先して上書きする。

#### 例
```
step.start {"type":"step.start","run_id":"...","step_id":"login"}
step.end {"type":"step.end","run_id":"...","step_id":"login","ok":true,"elapsed_ms":120}
```
