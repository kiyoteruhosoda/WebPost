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

## エラーハンドリング
- ファイル未検出: CLIは終了コード`1`、HTTPは`404`。
- 形式未対応: CLIは終了コード`1`、HTTPは`400`。
- 実行失敗: `success=false` と `error` に理由を格納。

## ログ仕様
- すべてのログイベントに `type` フィールドを含める。
- ステップ実行時は `step.start` / `step.end` を必ず出力する。
- 相関用に `run_id` と `step_id` を含める。
